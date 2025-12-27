#!/bin/bash

# MyFigPoint Automated Deployment Script
# This script deploys the MyFigPoint application to a remote server
# without requiring password input during the process

set -e  # Exit on any error

# Server configuration
SERVER_IP="72.62.4.119"
SSH_USER="root"
SSH_PORT="22"
PROJECT_NAME="myfigpoint"
REMOTE_PROJECT_DIR="/var/www/myfigpoint"
REMOTE_VENV_DIR="/var/www/myfigpoint/venv"
GUNICORN_PORT="8000"

# Local configuration
LOCAL_SSH_KEY="$HOME/.ssh/${PROJECT_NAME}_key"
ARCHIVE_NAME="${PROJECT_NAME}.tar.gz"
TEMP_ARCHIVE_PATH="/tmp/${ARCHIVE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Windows (Git Bash) or Linux/Mac
is_windows() {
    [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]
}

# Setup SSH key authentication
setup_ssh_key() {
    log "Setting up SSH key authentication..."
    
    # Generate SSH key if it doesn't exist
    if [ ! -f "$LOCAL_SSH_KEY" ]; then
        log "Generating new SSH key for deployment..."
        ssh-keygen -t rsa -b 4096 -f "$LOCAL_SSH_KEY" -N "" -C "deployment@myfigpoint"
        success "SSH key generated at $LOCAL_SSH_KEY"
    else
        log "Using existing SSH key at $LOCAL_SSH_KEY"
    fi
    
    # Ensure proper permissions
    chmod 600 "$LOCAL_SSH_KEY"
    chmod 644 "${LOCAL_SSH_KEY}.pub"
    
    # Copy public key to server using sshpass to avoid interactive password prompt
    log "Copying SSH public key to server..."
    
    # Try to copy the key using sshpass if available
    if command -v sshpass >/dev/null 2>&1; then
        log "Using sshpass for non-interactive authentication..."
        sshpass -p "Myfigpoint23." ssh-copy-id -i "${LOCAL_SSH_KEY}.pub" -p $SSH_PORT "${SSH_USER}@${SERVER_IP}" 2>/dev/null || {
            warning "sshpass method failed, falling back to manual key setup..."
            # Manual key setup
            PUBLIC_KEY=$(cat "${LOCAL_SSH_KEY}.pub")
            ssh -o StrictHostKeyChecking=no -p $SSH_PORT "${SSH_USER}@${SERVER_IP}" \
                "mkdir -p ~/.ssh && echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys" 2>/dev/null || {
                error "Failed to set up SSH key authentication. Please ensure passwordless SSH is configured."
                exit 1
            }
        }
    else
        # Manual key setup
        PUBLIC_KEY=$(cat "${LOCAL_SSH_KEY}.pub")
        ssh -o StrictHostKeyChecking=no -p $SSH_PORT "${SSH_USER}@${SERVER_IP}" \
            "mkdir -p ~/.ssh && echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys" 2>/dev/null || {
            warning "Manual key setup failed. You may need to enter the password once for initial setup."
            ssh-copy-id -i "${LOCAL_SSH_KEY}.pub" -p $SSH_PORT "${SSH_USER}@${SERVER_IP}" || {
                error "Failed to set up SSH key authentication."
                exit 1
            }
        }
    fi
    
    success "SSH key authentication configured"
}

# Test SSH connection
test_ssh_connection() {
    log "Testing SSH connection..."
    if ssh -i "$LOCAL_SSH_KEY" -p $SSH_PORT -o BatchMode=yes -o ConnectTimeout=10 "${SSH_USER}@${SERVER_IP}" exit 2>/dev/null; then
        success "SSH connection successful"
    else
        error "SSH connection failed. Please check your SSH configuration."
        exit 1
    fi
}

# Create deployment archive
create_archive() {
    log "Creating deployment package..."
    
    # Remove existing archive if it exists
    if [ -f "$TEMP_ARCHIVE_PATH" ]; then
        rm -f "$TEMP_ARCHIVE_PATH"
    fi
    
    # Create archive excluding unnecessary files
    tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='venv' \
        --exclude='*.db' --exclude='instance/*.db' --exclude='.env' --exclude='*.log' \
        --exclude='auto_deploy.sh' --exclude='deploy.ps1' -czf "$TEMP_ARCHIVE_PATH" .
    
    if [ -f "$TEMP_ARCHIVE_PATH" ]; then
        success "Deployment package created: $TEMP_ARCHIVE_PATH ($(du -h "$TEMP_ARCHIVE_PATH" | cut -f1))"
    else
        error "Failed to create deployment package"
        exit 1
    fi
}

# Upload files to server
upload_files() {
    log "Uploading files to server..."
    
    # Upload archive
    scp -i "$LOCAL_SSH_KEY" -P $SSH_PORT "$TEMP_ARCHIVE_PATH" "${SSH_USER}@${SERVER_IP}:/tmp/" || {
        error "Failed to upload deployment package"
        exit 1
    }
    
    success "Files uploaded successfully"
}

# Execute remote deployment
execute_remote_deployment() {
    log "Executing remote deployment..."
    
    # Run remote deployment commands
    ssh -i "$LOCAL_SSH_KEY" -p $SSH_PORT "${SSH_USER}@${SERVER_IP}" "
        set -e
        
        # Update package list
        echo 'Updating system packages...'
        apt-get update -y
        
        # Install required packages
        echo 'Installing required packages...'
        apt-get install -y python3 python3-pip python3-venv nginx sqlite3 supervisor openssl
        
        # Create project directory
        echo 'Creating project directory...'
        mkdir -p $REMOTE_PROJECT_DIR
        
        # Navigate to project directory
        cd $REMOTE_PROJECT_DIR
        
        # Extract files
        echo 'Extracting project files...'
        tar -xzf /tmp/$ARCHIVE_NAME
        
        # Clean up archive
        rm -f /tmp/$ARCHIVE_NAME
        
        # Create virtual environment
        echo 'Setting up Python virtual environment...'
        python3 -m venv $REMOTE_VENV_DIR
        source $REMOTE_VENV_DIR/bin/activate
        
        # Install Python dependencies
        echo 'Installing Python dependencies...'
        pip install --upgrade pip
        pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv
        
        # Create environment file
        echo 'Setting up environment variables...'
        cat > $REMOTE_PROJECT_DIR/.env << ENV_END
SECRET_KEY=\$(openssl rand -hex 32)
JWT_SECRET_KEY=\$(openssl rand -hex 32)
DATABASE_URL=sqlite:///$REMOTE_PROJECT_DIR/instance/myfigpoint.db
FLASK_APP=app.py
FLASK_ENV=production
ENV_END
        
        # Create instance directory
        echo 'Creating instance directory...'
        mkdir -p $REMOTE_PROJECT_DIR/instance
        
        # Initialize database
        echo 'Initializing database...'
        export \$(cat $REMOTE_PROJECT_DIR/.env | xargs)
        source $REMOTE_VENV_DIR/bin/activate
        python -c \"
import sys
sys.path.append('$REMOTE_PROJECT_DIR')
from backend.app import create_app
from backend.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
print('Database initialized successfully')
\"
        
        # Seed database
        echo 'Seeding database...'
        python -c \"
import sys
sys.path.append('$REMOTE_PROJECT_DIR')
try:
    from backend.seed import seed_database
    seed_database()
    print('Database seeded successfully')
except Exception as e:
    print(f'Database seeding skipped: {e}')
\"
        
        # Create Gunicorn service
        echo 'Setting up Gunicorn service...'
        cat > /etc/systemd/system/$PROJECT_NAME.service << SERVICE_END
[Unit]
Description=Gunicorn instance to serve MyFigPoint
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=$REMOTE_PROJECT_DIR
EnvironmentFile=$REMOTE_PROJECT_DIR/.env
ExecStart=$REMOTE_VENV_DIR/bin/gunicorn --workers 3 --bind 0.0.0.0:$GUNICORN_PORT --timeout 120 app:app
ExecReload=/bin/kill -s HUP \\\\$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE_END
        
        # Configure Nginx
        echo 'Configuring Nginx...'
        cat > /etc/nginx/sites-available/$PROJECT_NAME << NGINX_END
server {
    listen 80;
    server_name $SERVER_IP;

    location / {
        proxy_pass http://localhost:$GUNICORN_PORT;
        proxy_set_header Host \\\\$host;
        proxy_set_header X-Real-IP \\\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\\$scheme;
    }
    
    location /static/ {
        alias $REMOTE_PROJECT_DIR/assets/;
    }
    
    client_max_body_size 16M;
}
NGINX_END
        
        # Enable site
        echo 'Enabling site...'
        ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        
        # Start services
        echo 'Starting services...'
        systemctl daemon-reload
        systemctl restart nginx
        systemctl enable nginx
        systemctl start $PROJECT_NAME.service
        systemctl enable $PROJECT_NAME.service
        
        echo 'Deployment completed successfully!'
    " || {
        error "Remote deployment failed"
        exit 1
    }
    
    success "Remote deployment completed"
}

# Cleanup local files
cleanup() {
    log "Cleaning up temporary files..."
    if [ -f "$TEMP_ARCHIVE_PATH" ]; then
        rm -f "$TEMP_ARCHIVE_PATH"
    fi
    success "Cleanup completed"
}

# Main deployment function
deploy() {
    log "Starting MyFigPoint deployment to $SERVER_IP..."
    
    # Setup SSH key authentication
    setup_ssh_key
    
    # Test SSH connection
    test_ssh_connection
    
    # Create deployment archive
    create_archive
    
    # Upload files to server
    upload_files
    
    # Execute remote deployment
    execute_remote_deployment
    
    # Cleanup
    cleanup
    
    success "Deployment finished successfully!"
    echo
    echo -e "${GREEN}Your application should be accessible at: http://$SERVER_IP${NC}"
    echo -e "${GREEN}Admin panel: http://$SERVER_IP/admin/${NC}"
    echo
    echo -e "${YELLOW}Admin credentials:${NC}"
    echo -e "${YELLOW}Email: admin@myfigpoint.com${NC}"
    echo -e "${YELLOW}Password: MyFigPoint2025${NC}"
    echo
    echo -e "${BLUE}SSH key saved to: $LOCAL_SSH_KEY${NC}"
    echo -e "${BLUE}To SSH into your server: ssh -i $LOCAL_SSH_KEY -p $SSH_PORT $SSH_USER@$SERVER_IP${NC}"
}

# Check if required tools are available
check_requirements() {
    log "Checking requirements..."
    
    local missing_tools=()
    
    # Check for required tools
    for tool in ssh scp ssh-keygen tar; do
        if ! command -v $tool >/dev/null 2>&1; then
            missing_tools+=($tool)
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        error "Missing required tools: ${missing_tools[*]}"
        error "Please install these tools and try again."
        exit 1
    fi
    
    success "All requirements met"
}

# Main execution
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  MyFigPoint Automated Deployment Script ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    
    # Check requirements
    check_requirements
    
    # Confirm deployment
    echo -e "${YELLOW}This will deploy MyFigPoint to $SERVER_IP${NC}"
    echo -e "${YELLOW}Server IP: $SERVER_IP${NC}"
    echo -e "${YELLOW}SSH User: $SSH_USER${NC}"
    echo -e "${YELLOW}Project Directory: $REMOTE_PROJECT_DIR${NC}"
    echo
    
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Deployment cancelled by user"
        exit 0
    fi
    
    # Perform deployment
    deploy
}

# Run main function
main "$@"