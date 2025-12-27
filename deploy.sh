#!/bin/bash

# MyFigPoint Deployment Script
# This script deploys the MyFigPoint application to a remote server
# without requiring password input during the process

set -e  # Exit on any error

# Server configuration
SERVER_IP="72.62.4.119"
SSH_USER="root"
PROJECT_NAME="myfigpoint"
REMOTE_PROJECT_DIR="/var/www/myfigpoint"
REMOTE_VENV_DIR="/var/www/myfigpoint/venv"
GUNICORN_PORT="8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting MyFigPoint deployment...${NC}"

# Check if SSH key exists, if not generate one
if [ ! -f ~/.ssh/id_rsa_myfigpoint ]; then
    echo -e "${YELLOW}Generating new SSH key for deployment...${NC}"
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_myfigpoint -N ""
fi

# Copy SSH key to server (will prompt for password only once)
echo -e "${YELLOW}Setting up SSH key authentication...${NC}"
ssh-copy-id -i ~/.ssh/id_rsa_myfigpoint.pub ${SSH_USER}@${SERVER_IP}

# Create deployment archive
echo -e "${YELLOW}Creating deployment package...${NC}"
tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='venv' --exclude='*.db' --exclude='instance/*' -czf /tmp/${PROJECT_NAME}.tar.gz .

# Upload files to server
echo -e "${YELLOW}Uploading files to server...${NC}"
scp -i ~/.ssh/id_rsa_myfigpoint /tmp/${PROJECT_NAME}.tar.gz ${SSH_USER}@${SERVER_IP}:/tmp/

# Execute remote deployment commands
echo -e "${YELLOW}Executing remote deployment...${NC}"
ssh -i ~/.ssh/id_rsa_myfigpoint ${SSH_USER}@${SERVER_IP} << EOF
    set -e
    
    echo "Updating system packages..."
    apt-get update
    
    echo "Installing required packages..."
    apt-get install -y python3 python3-pip python3-venv nginx supervisor sqlite3
    
    echo "Creating project directory..."
    mkdir -p ${REMOTE_PROJECT_DIR}
    
    echo "Extracting project files..."
    cd ${REMOTE_PROJECT_DIR}
    tar -xzf /tmp/${PROJECT_NAME}.tar.gz
    
    echo "Setting up Python virtual environment..."
    python3 -m venv ${REMOTE_VENV_DIR}
    source ${REMOTE_VENV_DIR}/bin/activate
    
    echo "Installing Python dependencies..."
    pip install --upgrade pip
    pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv
    
    echo "Setting up environment variables..."
    cat > ${REMOTE_PROJECT_DIR}/.env << ENV_END
SECRET_KEY=\$(openssl rand -hex 32)
JWT_SECRET_KEY=\$(openssl rand -hex 32)
DATABASE_URL=sqlite:///${REMOTE_PROJECT_DIR}/instance/myfigpoint.db
FLASK_APP=app.py
FLASK_ENV=production
ENV_END
    
    echo "Creating instance directory..."
    mkdir -p ${REMOTE_PROJECT_DIR}/instance
    
    echo "Initializing database..."
    export \$(cat ${REMOTE_PROJECT_DIR}/.env | xargs)
    cd ${REMOTE_PROJECT_DIR}
    source ${REMOTE_VENV_DIR}/bin/activate
    python -c "
import sys
sys.path.append('${REMOTE_PROJECT_DIR}')
from backend.app import create_app
from backend.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
print('Database initialized successfully')
"
    
    echo "Seeding database..."
    python -c "
import sys
sys.path.append('${REMOTE_PROJECT_DIR}')
try:
    from backend.seed import seed_database
    seed_database()
    print('Database seeded successfully')
except Exception as e:
    print(f'Database seeding skipped: {e}')
"
    
    echo "Setting up Gunicorn service..."
    cat > /etc/systemd/system/${PROJECT_NAME}.service << SERVICE_END
[Unit]
Description=Gunicorn instance to serve MyFigPoint
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=${REMOTE_PROJECT_DIR}
EnvironmentFile=${REMOTE_PROJECT_DIR}/.env
ExecStart=${REMOTE_VENV_DIR}/bin/gunicorn --workers 3 --bind 0.0.0.0:${GUNICORN_PORT} --timeout 120 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE_END
    
    echo "Setting up Nginx configuration..."
    cat > /etc/nginx/sites-available/${PROJECT_NAME} << NGINX_END
server {
    listen 80;
    server_name ${SERVER_IP};

    location / {
        proxy_pass http://localhost:${GUNICORN_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias ${REMOTE_PROJECT_DIR}/assets/;
    }
    
    client_max_body_size 16M;
}
NGINX_END
    
    echo "Enabling site..."
    ln -sf /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    echo "Starting services..."
    systemctl daemon-reload
    systemctl restart nginx
    systemctl enable nginx
    systemctl start ${PROJECT_NAME}.service
    systemctl enable ${PROJECT_NAME}.service
    
    echo "Deployment completed successfully!"
EOF

echo -e "${GREEN}Deployment finished!${NC}"
echo -e "${GREEN}Your application should be accessible at: http://${SERVER_IP}${NC}"
echo -e "${YELLOW}Admin credentials:${NC}"
echo -e "${YELLOW}Email: admin@myfigpoint.com${NC}"
echo -e "${YELLOW}Password: MyFigPoint2025${NC}"
echo -e "${YELLOW}SSH key saved to: ~/.ssh/id_rsa_myfigpoint${NC}"