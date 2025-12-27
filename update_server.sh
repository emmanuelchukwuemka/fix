#!/bin/bash

# MyFigPoint Update Script
# This script updates the deployed MyFigPoint application on the remote server
# without reinstalling all dependencies and services

set -e  # Exit on any error

# Server configuration
SERVER_IP="72.62.4.119"
SSH_USER="root"
SSH_PORT="22"
PROJECT_NAME="myfigpoint"
REMOTE_PROJECT_DIR="/var/www/myfigpoint"
REMOTE_VENV_DIR="/var/www/myfigpoint/venv"

# Local configuration
LOCAL_SSH_KEY="$HOME/.ssh/${PROJECT_NAME}_key"
ARCHIVE_NAME="${PROJECT_NAME}_update.tar.gz"
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

# Create update archive
create_archive() {
    log "Creating update package..."
    
    # Remove existing archive if it exists
    if [ -f "$TEMP_ARCHIVE_PATH" ]; then
        rm -f "$TEMP_ARCHIVE_PATH"
    fi
    
    # Create archive excluding unnecessary files
    tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='venv' \
        --exclude='*.db' --exclude='instance/*.db' --exclude='.env' --exclude='*.log' \
        --exclude='auto_deploy.sh' --exclude='deploy.sh' --exclude='auto_deploy.ps1' --exclude='deploy.ps1' \
        --exclude='update_server.sh' -czf "$TEMP_ARCHIVE_PATH" .
    
    if [ -f "$TEMP_ARCHIVE_PATH" ]; then
        success "Update package created: $TEMP_ARCHIVE_PATH ($(du -h "$TEMP_ARCHIVE_PATH" | cut -f1))"
    else
        error "Failed to create update package"
        exit 1
    fi
}

# Upload files to server
upload_files() {
    log "Uploading files to server..."
    
    # Upload archive
    scp -i "$LOCAL_SSH_KEY" -P $SSH_PORT "$TEMP_ARCHIVE_PATH" "${SSH_USER}@${SERVER_IP}:/tmp/" || {
        error "Failed to upload update package"
        exit 1
    }
    
    success "Files uploaded successfully"
}

# Execute remote update
execute_remote_update() {
    log "Executing remote update..."
    
    # Run remote update commands
    ssh -i "$LOCAL_SSH_KEY" -p $SSH_PORT "${SSH_USER}@${SERVER_IP}" "
        set -e
        
        echo 'Stopping services temporarily...'
        systemctl stop $PROJECT_NAME.service
        
        # Navigate to project directory
        cd $REMOTE_PROJECT_DIR
        
        # Create backup of current version
        echo 'Creating backup of current version...'
        cp -r . /tmp/${PROJECT_NAME}_backup_\$(date +%Y%m%d_%H%M%S)
        
        # Extract update files
        echo 'Extracting update files...'
        tar -xzf /tmp/$ARCHIVE_NAME --exclude='instance/myfigpoint.db' --exclude='.env'
        
        # Clean up archive
        rm -f /tmp/$ARCHIVE_NAME
        
        # Activate virtual environment and install any new dependencies
        echo 'Installing any new dependencies...'
        source $REMOTE_VENV_DIR/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt 2>/dev/null || {
            # If requirements.txt doesn't exist, install the known dependencies
            pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv
        }
        
        # Restart services
        echo 'Restarting services...'
        systemctl daemon-reload
        systemctl start $PROJECT_NAME.service
        
        # Check if the service is running
        if systemctl is-active --quiet $PROJECT_NAME.service; then
            echo 'Services restarted successfully!'
        else
            echo 'Warning: Service may not have started properly. Check with: systemctl status $PROJECT_NAME.service'
        fi
        
        echo 'Update completed successfully!'
    " || {
        error "Remote update failed"
        exit 1
    }
    
    success "Remote update completed"
}

# Cleanup local files
cleanup() {
    log "Cleaning up temporary files..."
    if [ -f "$TEMP_ARCHIVE_PATH" ]; then
        rm -f "$TEMP_ARCHIVE_PATH"
    fi
    success "Cleanup completed"
}

# Main update function
update() {
    log "Starting MyFigPoint update to $SERVER_IP..."
    
    # Test SSH connection
    test_ssh_connection
    
    # Create update archive
    create_archive
    
    # Upload files to server
    upload_files
    
    # Execute remote update
    execute_remote_update
    
    # Cleanup
    cleanup
    
    success "Update finished successfully!"
    echo
    echo -e "${GREEN}Your application should be accessible at: http://$SERVER_IP${NC}"
    echo -e "${GREEN}Admin panel: http://$SERVER_IP/admin/${NC}"
    echo
    echo -e "${YELLOW}Note: The application may take a few seconds to restart after the update.${NC}"
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
    echo -e "${GREEN}    MyFigPoint Update Script             ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    
    # Check requirements
    check_requirements
    
    # Confirm update
    echo -e "${YELLOW}This will update MyFigPoint on $SERVER_IP${NC}"
    echo -e "${YELLOW}Server IP: $SERVER_IP${NC}"
    echo -e "${YELLOW}SSH User: $SSH_USER${NC}"
    echo -e "${YELLOW}Project Directory: $REMOTE_PROJECT_DIR${NC}"
    echo
    
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Update cancelled by user"
        exit 0
    fi
    
    # Perform update
    update
}

# Run main function
main "$@"