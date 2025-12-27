# MyFigPoint Update Process

This document describes how to update the deployed MyFigPoint application on the server at 72.62.4.119 with your latest code changes.

## Prerequisites

Before updating the server, ensure you have:

1. SSH access to the server at 72.62.4.119
2. SSH key authentication set up (the update script will use `~/.ssh/myfigpoint_key`)
3. The latest code changes committed locally
4. Required tools: `ssh`, `scp`, `ssh-keygen`, `tar`

## Update Process

### Option 1: Using the Update Script (Recommended)

#### For Linux/Mac or Git Bash users:
```bash
chmod +x update_server.sh
./update_server.sh
```

#### For PowerShell users:
```powershell
.\update_server.ps1
```

### Option 2: Manual Update Process

1. Stop the running service:
   ```bash
   ssh root@72.62.4.119 "systemctl stop myfigpoint.service"
   ```

2. Create an archive of your local code:
   ```bash
   tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='venv' \
       --exclude='*.db' --exclude='instance/*.db' --exclude='.env' --exclude='*.log' \
       --exclude='auto_deploy.sh' --exclude='deploy.sh' --exclude='auto_deploy.ps1' --exclude='deploy.ps1' \
       --exclude='update_server.sh' --exclude='update_server.ps1' -czf myfigpoint_update.tar.gz .
   ```

3. Upload the archive to the server:
   ```bash
   scp myfigpoint_update.tar.gz root@72.62.4.119:/tmp/
   ```

4. Extract and update on the server:
   ```bash
   ssh root@72.62.4.119 "
     cd /var/www/myfigpoint
     # Create backup
     cp -r . /tmp/myfigpoint_backup_$(date +%Y%m%d_%H%M%S)
     # Extract update
     tar -xzf /tmp/myfigpoint_update.tar.gz --exclude='instance/myfigpoint.db' --exclude='.env'
     # Install any new dependencies
     source /var/www/myfigpoint/venv/bin/activate
     pip install -r requirements.txt 2>/dev/null || pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv
     # Restart service
     systemctl daemon-reload
     systemctl start myfigpoint.service
   "
   ```

5. Clean up:
   ```bash
   ssh root@72.62.4.119 "rm /tmp/myfigpoint_update.tar.gz"
   ```

## What the Update Script Does

1. Creates an archive of your local code, excluding unnecessary files
2. Uploads the archive to the server
3. Stops the running service temporarily
4. Creates a backup of the current version
5. Extracts the updated files
6. Installs any new dependencies
7. Restarts the service
8. Cleans up temporary files

## Troubleshooting

### If SSH key authentication fails:
- Ensure your SSH key is properly set up: `ssh -i ~/.ssh/myfigpoint_key root@72.62.4.119`
- If needed, copy your public key manually: `ssh-copy-id -i ~/.ssh/myfigpoint_key.pub root@72.62.4.119`

### If the service doesn't restart properly:
- Check service status: `ssh root@72.62.4.119 "systemctl status myfigpoint.service"`
- Check service logs: `ssh root@72.62.4.119 "journalctl -u myfigpoint.service -f"`

### If there are dependency issues:
- Manually install dependencies: `ssh root@72.62.4.119 "source /var/www/myfigpoint/venv/bin/activate && pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv"`

## Rollback Process

If the update causes issues and you need to rollback:

1. Connect to the server: `ssh root@72.62.4.119`
2. Find your backup: `ls -la /tmp/myfigpoint_backup_*`
3. Restore the backup:
   ```bash
   systemctl stop myfigpoint.service
   rm -rf /var/www/myfigpoint/*
   cp -r /tmp/myfigpoint_backup_[timestamp]/* /var/www/myfigpoint/
   systemctl start myfigpoint.service
   ```

## Best Practices

- Always test your changes locally before updating the server
- Make sure to commit all your changes before running the update
- Check the application after the update to ensure everything works
- Keep a copy of the previous version in case of issues
- Update during low-traffic periods when possible