# MyFigPoint Automated Deployment Script for Windows
# This script deploys the MyFigPoint application to a remote Linux server
# without requiring password input during the process

param(
    [string]$ServerIP = "72.62.4.119",
    [string]$Username = "root",
    [int]$SSHPort = 22
)

# Configuration
$ProjectName = "myfigpoint"
$RemoteProjectDir = "/var/www/myfigpoint"
$RemoteVenvDir = "/var/www/myfigpoint/venv"
$GunicornPort = "8000"
$KeyName = "${ProjectName}_key"
$ArchiveName = "${ProjectName}.tar.gz"

# Paths
$KeyPath = "$env:USERPROFILE\.ssh\$KeyName"
$PublicKeyPath = "$KeyPath.pub"
$ArchivePath = "$env:TEMP\$ArchiveName"
$TempScript = "$env:TEMP\deploy_script.sh"

# Colors
$Host.UI.RawUI.ForegroundColor = "White"

function Write-Log {
    param([string]$Message, [string]$Color = "Gray")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Log $Message "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-Log $Message "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-Log $Message "Red"
}

# Check if required tools are available
function Check-Requirements {
    Write-Log "Checking requirements..."
    
    $missingTools = @()
    
    # Check for required tools
    $tools = @("ssh", "scp", "ssh-keygen", "tar")
    
    foreach ($tool in $tools) {
        if (!(Get-Command $tool -ErrorAction SilentlyContinue)) {
            $missingTools += $tool
        }
    }
    
    if ($missingTools.Count -gt 0) {
        Write-Error "Missing required tools: $($missingTools -join ', ')"
        Write-Error "Please install these tools and try again."
        exit 1
    }
    
    Write-Success "All requirements met"
}

# Setup SSH key authentication
function Setup-SSHKey {
    Write-Log "Setting up SSH key authentication..."
    
    # Generate SSH key if it doesn't exist
    if (!(Test-Path "$KeyPath")) {
        Write-Log "Generating new SSH key for deployment..."
        & ssh-keygen -t rsa -b 4096 -f "$KeyPath" -N "" -C "deployment@myfigpoint"
        Write-Success "SSH key generated at $KeyPath"
    } else {
        Write-Log "Using existing SSH key at $KeyPath"
    }
    
    # Wait a moment for key generation
    Start-Sleep -Seconds 2
    
    # Copy SSH key to server
    Write-Log "Copying SSH public key to server..."
    
    if (Test-Path $PublicKeyPath) {
        $KeyContent = Get-Content $PublicKeyPath
        # Try to set up key authentication
        try {
            ssh -o StrictHostKeyChecking=no -p $SSHPort ${Username}@${ServerIP} "mkdir -p ~/.ssh; echo '$KeyContent' >> ~/.ssh/authorized_keys; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys" 2>$null
            Write-Success "SSH key copied to server"
        } catch {
            Write-Warning "Automatic key setup failed. You may need to enter the password once for initial setup."
            ssh-copy-id -i $PublicKeyPath -p $SSHPort ${Username}@${ServerIP}
        }
    } else {
        Write-Error "Public key not found at $PublicKeyPath"
        exit 1
    }
}

# Test SSH connection
function Test-SSHConnection {
    Write-Log "Testing SSH connection..."
    try {
        $result = ssh -i $KeyPath -p $SSHPort -o BatchMode=yes -o ConnectTimeout=10 ${Username}@${ServerIP} "exit" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "SSH connection successful"
        } else {
            Write-Error "SSH connection failed. Please check your SSH configuration."
            exit 1
        }
    } catch {
        Write-Error "SSH connection failed. Please check your SSH configuration."
        exit 1
    }
}

# Create deployment archive
function Create-Archive {
    Write-Log "Creating deployment package..."
    
    # Remove existing archive if it exists
    if (Test-Path $ArchivePath) {
        Remove-Item $ArchivePath -Force
    }
    
    # Create tar.gz archive excluding unnecessary files
    tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='venv' --exclude='*.db' --exclude='instance/*.db' --exclude='.env' --exclude='*.log' --exclude='auto_deploy.sh' --exclude='auto_deploy.ps1' -czf $ArchivePath .
    
    if (Test-Path $ArchivePath) {
        $size = (Get-Item $ArchivePath).Length / 1MB
        Write-Success "Deployment package created: $ArchivePath ($('{0:F2} MB' -f $size))"
    } else {
        Write-Error "Failed to create deployment package"
        exit 1
    }
}

# Upload files to server
function Upload-Files {
    Write-Log "Uploading files to server..."
    
    # Upload archive
    scp -i $KeyPath -P $SSHPort $ArchivePath ${Username}@${ServerIP}:/tmp/
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upload deployment package"
        exit 1
    }
    
    Write-Success "Files uploaded successfully"
}

# Execute remote deployment
function Execute-RemoteDeployment {
    Write-Log "Executing remote deployment..."
    
    $RemoteCommands = @"
#!/bin/bash
set -e

# Update package list
echo 'Updating system packages...'
apt-get update -y

# Install required packages
echo 'Installing required packages...'
apt-get install -y python3 python3-pip python3-venv nginx sqlite3 supervisor openssl

# Create project directory
echo 'Creating project directory...'
mkdir -p $RemoteProjectDir

# Navigate to project directory
cd $RemoteProjectDir

# Extract files
echo 'Extracting project files...'
tar -xzf /tmp/$ArchiveName

# Clean up archive
rm -f /tmp/$ArchiveName

# Create virtual environment
echo 'Setting up Python virtual environment...'
python3 -m venv $RemoteVenvDir
source $RemoteVenvDir/bin/activate

# Install Python dependencies
echo 'Installing Python dependencies...'
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv

# Create environment file
echo 'Setting up environment variables...'
cat > $RemoteProjectDir/.env << ENV_END
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///$RemoteProjectDir/instance/myfigpoint.db
FLASK_APP=app.py
FLASK_ENV=production
ENV_END

# Create instance directory
echo 'Creating instance directory...'
mkdir -p $RemoteProjectDir/instance

# Initialize database
echo 'Initializing database...'
export $(cat $RemoteProjectDir/.env | xargs)
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
echo 'Seeding database...'
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

# Create Gunicorn service
echo 'Setting up Gunicorn service...'
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
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE_END

# Configure Nginx
echo 'Configuring Nginx...'
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
echo 'Enabling site...'
ln -sf /etc/nginx/sites-available/$ProjectName /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Start services
echo 'Starting services...'
systemctl daemon-reload
systemctl restart nginx
systemctl enable nginx
systemctl start $ProjectName.service
systemctl enable $ProjectName.service

echo 'Deployment completed successfully!'
"@

    # Save commands to temporary file with Unix line endings
    $RemoteCommands = $RemoteCommands -replace "`r", ""
    $RemoteCommands | Out-File -FilePath $TempScript -Encoding UTF8
    
    # Upload and execute the script
    scp -i $KeyPath -P $SSHPort $TempScript ${Username}@${ServerIP}:/tmp/deploy_script.sh
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upload deployment script"
        exit 1
    }
    
    ssh -i $KeyPath -p $SSHPort ${Username}@${ServerIP} "chmod +x /tmp/deploy_script.sh; bash /tmp/deploy_script.sh"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Remote deployment failed"
        exit 1
    }
    
    Write-Success "Remote deployment completed"
}

# Cleanup local files
function Cleanup {
    Write-Log "Cleaning up temporary files..."
    
    if (Test-Path $ArchivePath) {
        Remove-Item $ArchivePath -Force
    }
    
    if (Test-Path $TempScript) {
        Remove-Item $TempScript -Force
    }
    
    Write-Success "Cleanup completed"
}

# Main deployment function
function Deploy {
    Write-Log "Starting MyFigPoint deployment to $ServerIP..."
    
    # Setup SSH key authentication
    Setup-SSHKey
    
    # Test SSH connection
    Test-SSHConnection
    
    # Create deployment archive
    Create-Archive
    
    # Upload files to server
    Upload-Files
    
    # Execute remote deployment
    Execute-RemoteDeployment
    
    # Cleanup
    Cleanup
    
    Write-Success "Deployment finished successfully!"
    Write-Host ""
    Write-Host "Your application should be accessible at: http://$ServerIP" -ForegroundColor Green
    Write-Host "Admin panel: http://$ServerIP/admin/" -ForegroundColor Green
    Write-Host ""
    Write-Host "Admin credentials:" -ForegroundColor Yellow
    Write-Host "Email: admin@myfigpoint.com" -ForegroundColor Yellow
    Write-Host "Password: MyFigPoint2025" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "SSH private key saved to: $KeyPath" -ForegroundColor Blue
    Write-Host "To SSH into your server: ssh -i $KeyPath -p $SSHPort $Username@$ServerIP" -ForegroundColor Blue
}

# Main execution
function Main {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  MyFigPoint Automated Deployment Script " -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Check requirements
    Check-Requirements
    
    # Confirm deployment
    Write-Host "This will deploy MyFigPoint to $ServerIP" -ForegroundColor Yellow
    Write-Host "Server IP: $ServerIP" -ForegroundColor Yellow
    Write-Host "SSH User: $Username" -ForegroundColor Yellow
    Write-Host "Project Directory: $RemoteProjectDir" -ForegroundColor Yellow
    Write-Host ""
    
    $confirmation = Read-Host "Do you want to continue? (y/N)"
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-Log "Deployment cancelled by user"
        exit 0
    }
    
    # Perform deployment
    Deploy
}

# Run main function
Main