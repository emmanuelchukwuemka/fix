# MyFigPoint Deployment Script for Windows
# This script deploys the MyFigPoint application to a remote Linux server
# without requiring password input during the process

param(
    [string]$ServerIP = "72.62.4.119",
    [string]$Username = "root"
)

# Configuration
$ProjectName = "myfigpoint"
$RemoteProjectDir = "/var/www/myfigpoint"
$RemoteVenvDir = "/var/www/myfigpoint/venv"
$GunicornPort = "8000"
$KeyName = "myfigpoint_deploy_key"

Write-Host "Starting MyFigPoint deployment..." -ForegroundColor Green

# Check if SSH key exists, if not generate one
$KeyPath = "$env:USERPROFILE\.ssh\$KeyName"
$PublicKeyPath = "$KeyPath.pub"

if (-not (Test-Path "$KeyPath")) {
    Write-Host "Generating new SSH key for deployment..." -ForegroundColor Yellow
    # Use ssh-keygen with proper parameters
    ssh-keygen -t rsa -b 4096 -f $KeyPath -N "" -C "deployment@myfigpoint"
}

# Wait a moment for key generation
Start-Sleep -Seconds 2

# Copy SSH key to server (will prompt for password only once)
Write-Host "Setting up SSH key authentication..." -ForegroundColor Yellow
if (Test-Path $PublicKeyPath) {
    $KeyContent = Get-Content $PublicKeyPath
    ssh ${Username}@${ServerIP} "mkdir -p ~/.ssh; echo '$KeyContent' >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys"
} else {
    Write-Host "Error: Public key not found at $PublicKeyPath" -ForegroundColor Red
    exit 1
}

# Create deployment archive
Write-Host "Creating deployment package..." -ForegroundColor Yellow
$ArchivePath = "$env:TEMP\$ProjectName.tar.gz"
# Remove existing archive if it exists
if (Test-Path $ArchivePath) {
    Remove-Item $ArchivePath
}

# Create tar.gz archive excluding unnecessary files
tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='venv' --exclude='*.db' --exclude='instance/*' -czf $ArchivePath .

# Upload files to server
Write-Host "Uploading files to server..." -ForegroundColor Yellow
scp -i $KeyPath $ArchivePath ${Username}@${ServerIP}:/tmp/

# Execute remote deployment commands
Write-Host "Executing remote deployment..." -ForegroundColor Yellow
$RemoteCommands = @"
#!/bin/bash
set -e

# Fix line endings
sed -i 's/\r$//' \$0

# Update package list
dpkg --configure -a
apt-get update -y

# Install required packages
apt-get install -y python3 python3-pip python3-venv nginx sqlite3 supervisor openssl

# Create project directory
mkdir -p $RemoteProjectDir

cd $RemoteProjectDir

# Extract project files
tar -xzf /tmp/$ProjectName.tar.gz

# Set up Python virtual environment
python3 -m venv $RemoteVenvDir
source $RemoteVenvDir/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv

# Set up environment variables
cat > $RemoteProjectDir/.env << ENV_END
SECRET_KEY=`openssl rand -hex 32`
JWT_SECRET_KEY=`openssl rand -hex 32`
DATABASE_URL=sqlite:///$RemoteProjectDir/instance/myfigpoint.db
FLASK_APP=app.py
FLASK_ENV=production
ENV_END

# Create instance directory
mkdir -p $RemoteProjectDir/instance

# Initialize database
export `cat $RemoteProjectDir/.env | xargs`
source $RemoteVenvDir/bin/activate
python -c "
import sys
sys.path.append('$RemoteProjectDir')
from backend.app import create_app
from backend.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
print('Database initialized successfully')
"

# Seed database
python -c "
import sys
sys.path.append('$RemoteProjectDir')
try:
    from backend.seed import seed_database
    seed_database()
    print('Database seeded successfully')
except Exception as e:
    print(f'Database seeding skipped: {e}')
"

# Set up Gunicorn service
cat > /etc/systemd/system/$ProjectName.service << SERVICE_END
[Unit]
Description=Gunicorn instance to serve MyFigPoint
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=$RemoteProjectDir
EnvironmentFile=$RemoteProjectDir/.env
ExecStart=$RemoteVenvDir/bin/gunicorn --workers 3 --bind 0.0.0.0:$GunicornPort --timeout 120 app:app
ExecReload=/bin/kill -s HUP \\$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE_END

# Set up Nginx configuration
cat > /etc/nginx/sites-available/$ProjectName << NGINX_END
server {
    listen 80;
    server_name $ServerIP;

    location / {
        proxy_pass http://localhost:$GunicornPort;
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
    }
    
    location /static/ {
        alias $RemoteProjectDir/assets/;
    }
    
    client_max_body_size 16M;
}
NGINX_END

# Enable site
ln -sf /etc/nginx/sites-available/$ProjectName /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Start services
systemctl daemon-reload
systemctl restart nginx
systemctl enable nginx
systemctl start $ProjectName.service
systemctl enable $ProjectName.service

echo "Deployment completed successfully!"
"@

# Save commands to temporary file with Unix line endings
$TempScript = "$env:TEMP\deploy_script.sh"
$RemoteCommands | Out-File -FilePath $TempScript -Encoding UTF8

# Convert to Unix line endings
(Get-Content $TempScript) | ForEach-Object {$_.TrimEnd()} | Set-Content $TempScript -Encoding UTF8

# Upload and execute the script
scp -i $KeyPath $TempScript ${Username}@${ServerIP}:/tmp/deploy_script.sh
ssh -i $KeyPath ${Username}@${ServerIP} "chmod +x /tmp/deploy_script.sh; bash /tmp/deploy_script.sh"

Write-Host "Deployment finished!" -ForegroundColor Green
Write-Host "Your application should be accessible at: http://$ServerIP" -ForegroundColor Green
Write-Host "Admin credentials:" -ForegroundColor Yellow
Write-Host "Email: admin@myfigpoint.com" -ForegroundColor Yellow
Write-Host "Password: MyFigPoint2025" -ForegroundColor Yellow
Write-Host "SSH private key saved to: $KeyPath" -ForegroundColor Yellow