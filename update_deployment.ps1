# MyFigPoint Deployment Update Script

Write-Host "========================================" -ForegroundColor Green
Write-Host "MyFigPoint Deployment Update Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Configuration
$ServerIP = "72.62.4.119"
$Username = "root"
$ProjectName = "myfigpoint"
$RemoteProjectDir = "/var/www/myfigpoint"
$RemoteVenvDir = "/var/www/myfigpoint/venv"
$ArchiveName = "${ProjectName}_update.tar.gz"

Write-Host "Updating MyFigPoint deployment at $ServerIP" -ForegroundColor Yellow
Write-Host ""

# Create temporary archive
Write-Host "Creating deployment archive..." -ForegroundColor Cyan
$excludeList = @(
    "*.pyc",
    "__pycache__",
    ".git",
    "venv",
    "*.db",
    "instance/*.db",
    ".env",
    "*.log",
    "auto_deploy.sh",
    "deploy.sh",
    "auto_deploy.ps1",
    "deploy.ps1",
    "update_server.sh",
    "update_server.ps1",
    "UPDATE_PROCESS.md",
    "update_deployment.ps1",
    "update_deployment.bat"
)

$excludeArgs = $excludeList | ForEach-Object { "--exclude='$_'" }
$excludeString = $excludeArgs -join " "

$command = "tar $excludeString -czf $ArchiveName ."
Write-Host "Executing: $command" -ForegroundColor Gray
$result = Invoke-Expression $command

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error creating archive" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Archive created successfully" -ForegroundColor Green
Write-Host ""

# Upload archive to server
Write-Host "Uploading archive to server..." -ForegroundColor Cyan
Write-Host "Please enter password when prompted: Mathscrusader123." -ForegroundColor Yellow
$uploadCommand = "scp -P 22 $ArchiveName ${Username}@${ServerIP}:/tmp/"
Write-Host "Executing: $uploadCommand" -ForegroundColor Gray
$result = Invoke-Expression $uploadCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error uploading archive" -ForegroundColor Red
    if (Test-Path $ArchiveName) {
        Remove-Item $ArchiveName
    }
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Upload completed" -ForegroundColor Green
Write-Host ""

# Execute update commands on remote server
Write-Host "Updating server..." -ForegroundColor Cyan
$updateScript = "#!/bin/bash`n" +
"set -e`n`n" +
"echo 'Stopping services temporarily...'`n" +
"systemctl stop $ProjectName.service 2>/dev/null || true`n`n" +
"# Navigate to project directory`n" +
"cd $RemoteProjectDir`n`n" +
"# Create backup of current version`n" +
"echo 'Creating backup of current version...'`n" +
"cp -r . /tmp/${ProjectName}_backup_\$(date +%%Y%%m%%d_%%H%%M%%S)`n`n" +
"# Extract update files`n" +
"echo 'Extracting update files...'`n" +
"tar -xzf /tmp/$ArchiveName --exclude='instance/myfigpoint.db' --exclude='.env'`n`n" +
"# Clean up archive`n" +
"rm -f /tmp/$ArchiveName`n`n" +
"# Activate virtual environment and install any new dependencies`n" +
"echo 'Installing any new dependencies...'`n" +
"source $RemoteVenvDir/bin/activate`n" +
"pip install --upgrade pip`n" +
"if [ -f `"requirements.txt`" ]; then`n" +
"    pip install -r requirements.txt`n" +
"else`n" +
"    pip install --break-system-packages flask flask-sqlalchemy flask-bcrypt flask-jwt-extended flask-cors gunicorn python-dotenv`n" +
"fi`n`n" +
"# Restart services`n" +
"echo 'Restarting services...'`n" +
"systemctl daemon-reload`n" +
"systemctl start $ProjectName.service`n`n" +
"# Check if the service is running`n" +
"if systemctl is-active --quiet $ProjectName.service; then`n" +
"    echo 'Services restarted successfully!'`n" +
"else`n" +
"    echo 'Warning: Service may not have started properly. Check with: systemctl status $ProjectName.service'`n" +
"fi`n`n" +
"echo 'Update completed successfully!'"

# Save the update script to a temporary file with Unix line endings
$tempScriptPath = "$env:TEMP\update_script.sh"
$updateScript | Out-File -FilePath $tempScriptPath -Encoding ASCII

# Upload the script to the server
$scriptUploadCommand = "scp -P 22 $tempScriptPath ${Username}@${ServerIP}:/tmp/update_script.sh"
Write-Host "Uploading update script..." -ForegroundColor Gray
$result = Invoke-Expression $scriptUploadCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error uploading update script" -ForegroundColor Red
    if (Test-Path $ArchiveName) {
        Remove-Item $ArchiveName
    }
    if (Test-Path $tempScriptPath) {
        Remove-Item $tempScriptPath
    }
    Read-Host "Press Enter to exit"
    exit 1
}

# Execute the update script on the server
$executeCommand = "ssh -p 22 ${Username}@${ServerIP} `"chmod +x /tmp/update_script.sh; bash /tmp/update_script.sh`""
Write-Host "Executing update on server..." -ForegroundColor Gray
$result = Invoke-Expression $executeCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error during remote update" -ForegroundColor Red
    if (Test-Path $ArchiveName) {
        Remove-Item $ArchiveName
    }
    if (Test-Path $tempScriptPath) {
        Remove-Item $tempScriptPath
    }
    Read-Host "Press Enter to exit"
    exit 1
}

# Clean up local files
if (Test-Path $ArchiveName) {
    Remove-Item $ArchiveName
}
if (Test-Path $tempScriptPath) {
    Remove-Item $tempScriptPath
}

Write-Host ""
Write-Host "Deployment update completed successfully!" -ForegroundColor Green
Write-Host "Your application should be accessible at: http://$ServerIP" -ForegroundColor Green
Write-Host "Admin panel: http://$ServerIP/admin/" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to exit"