
import paramiko
import os
import sys
import time

# Configuration
HOST = '72.62.4.119'
USERNAME = 'root'
PASSWORD = 'Mathscrusader123.'
PORT = 22
REMOTE_DIR = '/var/www/myfigpoint'
APP_PORT = 8000

def create_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD)
        print("Connected successfully.")
        return client
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

def run_command(client, command, ignore_error=False):
    print(f"Running: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    
    if out:
        print(f"Output:\n{out}")
    if err:
        print(f"Error:\n{err}")
        
    if exit_status != 0 and not ignore_error:
        print(f"Command failed with status {exit_status}")
        # specific check: if we try to kill a process that doesn't exist, it's fine
        if "kill" in command or "rm" in command:
            pass 
        else:
            raise Exception(f"Command failed: {command}")
    
    return out

def upload_files(client):
    sftp = client.open_sftp()
    
    # Create remote directory if it doesn't exist
    try:
        sftp.stat(REMOTE_DIR)
    except FileNotFoundError:
        print(f"Creating remote directory {REMOTE_DIR}")
        run_command(client, f"mkdir -p {REMOTE_DIR}")
    
    # Define files/folders to exclude
    excludes = {
        '.git', '__pycache__', '.env', 'instance', 'deploy.py', 
        'myfigpoint.db', 'venv', '.pytest_cache', '.vscode', '.idea'
    }
    
    print("Uploading files...")
    
    # Walk through local directory
    local_path = os.getcwd()
    
    for root, dirs, files in os.walk(local_path):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in excludes]
        
        # Get relative path
        rel_path = os.path.relpath(root, local_path)
        if rel_path == '.':
            remote_path = REMOTE_DIR
        else:
            remote_path = os.path.join(REMOTE_DIR, rel_path).replace('\\', '/')
            
        # Create remote directory
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            sftp.mkdir(remote_path)
            
        for file in files:
            if file in excludes or file.endswith('.pyc') or file.endswith('.git'):
                continue
                
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_path, file).replace('\\', '/')
            
            print(f"Uploading {file} to {remote_file}...")
            sftp.put(local_file, remote_file)
            
    sftp.close()
    print("Upload complete.")

def deploy():
    client = create_client()
    
    try:
        # 1. Clean Slate: Remove database
        print("\n--- CLEANING SLATE ---")
        run_command(client, f"rm -rf {REMOTE_DIR}/instance/myfigpoint.db", ignore_error=True)
        # Ensure instance dir exists
        run_command(client, f"mkdir -p {REMOTE_DIR}/instance")
        
        # 2. Upload Files
        print("\n--- UPLOADING FILES ---")
        upload_files(client)
        
        # 3. Install Dependencies
        print("\n--- INSTALLING DEPENDENCIES ---")
        # Ensure pip is installed
        run_command(client, "apt-get update && apt-get install -y python3-pip python3-venv", ignore_error=True)
        
        # Create virtual env if not exists
        venv_path = f"{REMOTE_DIR}/venv"
        run_command(client, f"python3 -m venv {venv_path}", ignore_error=True)
        
        # Install requirements
        run_command(client, f"{venv_path}/bin/pip install --upgrade pip")
        run_command(client, f"{venv_path}/bin/pip install -r {REMOTE_DIR}/requirements.txt")
        
        # 4. Stop existing process on port 8000
        print(f"\n--- STOPPING PORT {APP_PORT} ---")
        # Find PID using port 8000 and kill it
        run_command(client, f"fuser -k {APP_PORT}/tcp", ignore_error=True)
        
        # 5. Start Application
        print(f"\n--- STARTING APPLICATION ON PORT {APP_PORT} ---")
        # We use nohup to keep it running after we disconnect
        # Binding to 0.0.0.0:8000
        start_cmd = f"cd {REMOTE_DIR} && nohup {venv_path}/bin/gunicorn --bind 0.0.0.0:{APP_PORT} app:app > app.log 2>&1 &"
        run_command(client, start_cmd)
        
        # 6. Verify
        print("\n--- VERIFYING ---")
        time.sleep(5) # Wait for startup
        run_command(client, f"lsof -i :{APP_PORT}")
        
        print("\nDeployment Successful!")
        print(f"Live at http://{HOST}:{APP_PORT}")
        
    except Exception as e:
        print(f"\nDEPLOYMENT FAILED: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    deploy()
