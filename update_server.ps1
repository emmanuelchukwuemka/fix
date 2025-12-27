# MyFigPoint Update Script for Windows
# This script updates the deployed MyFigPoint application on the remote server
# without reinstalling all dependencies and services

param(
    [string]$ServerIP = "72.62.4.119",
    [string]$Username = "root",
    [int]$SSHPort = 22
)

# Configuration
$ProjectName = "myfigpoint"
$RemoteProjectDir = "/var/www/myfigpoint"
$RemoteVenvDir = "/var/www/myfigpoint/venv"
$KeyName = "${ProjectName}_key"
$ArchiveName = "${ProjectName}_update.tar.gz"

# Paths
$KeyPath = "$env:USERPROFILE\.ssh\$KeyName"
$PublicKeyPath = "$KeyPath.pub"
$ArchivePath = "$env:TEMP\$ArchiveName"
$TempScript = "$env:TEMP\update_script.sh"

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

# Create update archive
function Create-Archive {
    Write-Log "Creating update package..."
    
    # Remove existing archive if it exists
    if (Test-Path $ArchivePath) {
        Remove-Item $ArchivePath -Force
    }
    
    # Create tar.gz archive excluding unnecessary files
    tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='venv' --exclude='*.db' --exclude='instance/*.db' --exclude='.env' --exclude='*.log' --exclude='auto_deploy.sh' --exclude='deploy.sh' --exclude='auto_deploy.ps1' --exclude='deploy.ps1' --exclude='update_server.sh' --exclude='update_server.ps1' -czf $ArchivePath .
    
    if (Test-Path $ArchivePath) {
        $size = (Get-Item $ArchivePath).Length / 1MB
        Write-Success "Update package created: $ArchivePath ($('{0:F2} MB' -f $size))"
    } else {
        Write-Error "Failed to create update package"
        exit 1
    }
}

# Upload files to server
function Upload-Files {
    Write-Log "Uploading files to server..."
    
    # Upload archive
    scp -i $KeyPath -P $SSHPort $ArchivePath ${Username}@${ServerIP}:/tmp/
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upload update package"
        exit 1
    }
    
    Write-Success "Files uploaded successfully"
}

# Execute remote update
function Execute-RemoteUpdate {
    Write-Log "Executing remote update..."
    
    $RemoteCommands = @"
#!/bin/bash
set -e

echo 'Stopping services temporarily...'
systemctl stop $ProjectName.service

# Navigate to project directory
cd $RemoteProjectDir

# Create backup of current version
echo 'Creating backup of current version...'
cp -r . /tmp/${ProjectName}_backup_\$(date +%Y%m%d_%H%M%S)

# Extract update files
echo 'Extracting update files...'
tar -xzf /tmp/$ArchiveName --exclude='instance/myfigpoint.db' --exclude='.env'

# Clean up archive
rm -f /tmp/$ArchiveName

# Activate virtual environment and install any new dependencies
echo 'Installing any new dependencies...'
source $RemoteVenvDir/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv
fi

# Restart services
echo 'Restarting services...'
systemctl daemon-reload
systemctl start $ProjectName.service

# Check if the service is running
if systemctl is-active --quiet $ProjectName.service; then
    echo 'Services restarted successfully!'
else
    echo 'Warning: Service may not have started properly. Check with: systemctl status $ProjectName.service'
fi

echo 'Update completed successfully!'
"@

    # Save commands to temporary file with Unix line endings
    $RemoteCommands = $RemoteCommands -replace "`r", ""
    $RemoteCommands | Out-File -FilePath $TempScript -Encoding UTF8
    
    # Upload and execute the script
    scp -i $KeyPath -P $SSHPort $TempScript ${Username}@${ServerIP}:/tmp/update_script.sh
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upload update script"
        exit 1
    }
    
    ssh -i $KeyPath -p $SSHPort ${Username}@${ServerIP} "chmod +x /tmp/update_script.sh; bash /tmp/update_script.sh"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Remote update failed"
        exit 1
    }
    
    Write-Success "Remote update completed"
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

# Main update function
function Update-Project {
    Write-Log "Starting MyFigPoint update to $ServerIP..."
    
    # Test SSH connection
    Test-SSHConnection
    
    # Create update archive
    Create-Archive
    
    # Upload files to server
    Upload-Files
    
    # Execute remote update
    Execute-RemoteUpdate
    
    # Cleanup
    Cleanup
    
    Write-Success "Update finished successfully!"
    Write-Host ""
    Write-Host "Your application should be accessible at: http://$ServerIP" -ForegroundColor Green
    Write-Host "Admin panel: http://$ServerIP/admin/" -ForegroundColor Green
    Write-Host ""
    Write-Host "Note: The application may take a few seconds to restart after the update." -ForegroundColor Yellow
}

# Main execution
function Main {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "    MyFigPoint Update Script             " -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Check requirements
    Check-Requirements
    
    # Confirm update
    Write-Host "This will update MyFigPoint on $ServerIP" -ForegroundColor Yellow
    Write-Host "Server IP: $ServerIP" -ForegroundColor Yellow
    Write-Host "SSH User: $Username" -ForegroundColor Yellow
    Write-Host "Project Directory: $RemoteProjectDir" -ForegroundColor Yellow
    Write-Host ""
    
    $confirmation = Read-Host "Do you want to continue? (y/N)"
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-Log "Update cancelled by user"
        exit 0
    }
    
    # Perform update
    Update-Project
}

# Run main function
Main