@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MyFigPoint Deployment Update Script
echo ========================================
echo.

REM Configuration
set SERVER_IP=72.62.4.119
set USERNAME=root
set PROJECT_NAME=myfigpoint
set REMOTE_PROJECT_DIR=/var/www/myfigpoint
set REMOTE_VENV_DIR=/var/www/myfigpoint/venv

echo Updating MyFigPoint deployment at %SERVER_IP%
echo.

REM Create temporary archive
echo Creating deployment archive...
tar --exclude="*.pyc" --exclude="__pycache__" --exclude=".git" --exclude="venv" ^
    --exclude="*.db" --exclude="instance/*.db" --exclude=".env" --exclude="*.log" ^
    --exclude="auto_deploy.sh" --exclude="deploy.sh" --exclude="auto_deploy.ps1" --exclude="deploy.ps1" ^
    --exclude="update_server.sh" --exclude="update_server.ps1" --exclude="UPDATE_PROCESS.md" ^
    -czf ..\%PROJECT_NAME%_update.tar.gz .

if errorlevel 1 (
    echo Error creating archive
    pause
    exit /b 1
)

echo Archive created successfully
echo.

REM Upload archive to server using plink
echo Uploading archive to server...
echo Please enter password: Mathscrusader123.
pscp -scp -P 22 ..\%PROJECT_NAME%_update.tar.gz %USERNAME%@%SERVER_IP%:/tmp/
if errorlevel 1 (
    echo Error uploading archive
    del ..\%PROJECT_NAME%_update.tar.gz
    pause
    exit /b 1
)

echo Upload completed
echo.

REM Execute update commands on remote server
echo Updating server...
plink -ssh -P 22 %USERNAME%@%SERVER_IP% -m - << EOF
    set -e
    
    echo 'Stopping services temporarily...'
    systemctl stop %PROJECT_NAME%.service 2>/dev/null || true
    
    # Navigate to project directory
    cd %REMOTE_PROJECT_DIR%
    
    # Create backup of current version
    echo 'Creating backup of current version...'
    cp -r . /tmp/%PROJECT_NAME%_backup_$(date +%%Y%%m%%d_%%H%%M%%S)
    
    # Extract update files
    echo 'Extracting update files...'
    tar -xzf /tmp/%PROJECT_NAME%_update.tar.gz --exclude='instance/myfigpoint.db' --exclude='.env'
    
    # Clean up archive
    rm -f /tmp/%PROJECT_NAME%_update.tar.gz
    
    # Activate virtual environment and install any new dependencies
    echo 'Installing any new dependencies...'
    source %REMOTE_VENV_DIR%/bin/activate
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv
    fi
    
    # Restart services
    echo 'Restarting services...'
    systemctl daemon-reload
    systemctl start %PROJECT_NAME%.service
    
    # Check if the service is running
    if systemctl is-active --quiet %PROJECT_NAME%.service; then
        echo 'Services restarted successfully!'
    else
        echo 'Warning: Service may not have started properly. Check with: systemctl status %PROJECT_NAME%.service'
    fi
    
    echo 'Update completed successfully!'
EOF

if errorlevel 1 (
    echo Error during remote update
    del ..\%PROJECT_NAME%_update.tar.gz
    pause
    exit /b 1
)

REM Clean up local archive
if exist "..\%PROJECT_NAME%_update.tar.gz" (
    del "..\%PROJECT_NAME%_update.tar.gz"
)

echo.
echo Deployment update completed successfully!
echo Your application should be accessible at: http://%SERVER_IP%
echo Admin panel: http://%SERVER_IP%/admin/
echo.
echo Press any key to exit...
pause > nul