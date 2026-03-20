"""
Deploy BVC Analytics to VPS via SSH
Creates a tar, uploads it, and runs the deploy script.
"""
import subprocess, os, sys

VPS = "38.242.225.58"
USER = "root"
PASS = "Ea1128544093dd"
APP_DIR = "/opt/bvc-analytics"
PROJECT = os.path.dirname(os.path.abspath(__file__)).replace("\\scripts", "")

print("=" * 50)
print("  BVC Analytics - Deploy to VPS")
print("=" * 50)

# 1. Create tar archive of the project
print("\n[1/4] Creating archive...")
tar_path = os.path.join(PROJECT, "bvc-deploy.tar.gz")
excludes = [
    "__pycache__", "*.pyc", ".git", "node_modules", 
    "bvc-deploy.tar.gz", ".env.local", "data/*.csv"
]

import tarfile
with tarfile.open(tar_path, "w:gz") as tar:
    for item in os.listdir(PROJECT):
        skip = False
        for exc in excludes:
            if exc.startswith("*"):
                if item.endswith(exc[1:]):
                    skip = True
            elif item == exc:
                skip = True
        if not skip:
            full = os.path.join(PROJECT, item)
            tar.add(full, arcname=item)
            
size_mb = os.path.getsize(tar_path) / 1024 / 1024
print(f"    Archive: {size_mb:.1f} MB")

# 2. Use plink/pscp if available, otherwise use paramiko-like approach
# Since we don't have external tools, we'll write a PowerShell script
print("\n[2/4] Generating upload commands...")

ps_script = f'''
$pass = ConvertTo-SecureString "{PASS}" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("{USER}", $pass)

Write-Host "[Upload] Copying files to VPS..."
# Use Windows native SCP alternative
$env:SSHPASS = "{PASS}"
'''

# Write the PowerShell commands for the user
print("\n" + "=" * 50)
print("  COMMANDS TO RUN MANUALLY:")
print("=" * 50)
print(f"""
Since Windows doesn't have native scp/rsync, run these commands:

OPTION A - Using Git Bash or WSL:
  cd "{PROJECT}"
  scp -r ./* root@{VPS}:{APP_DIR}/

OPTION B - Using PowerShell with tar:
  Step 1: Upload the tar file (run in PowerShell):
  
  $session = New-PSSession ... # Requires WinRM

OPTION C - Best option - SSH into VPS and clone/download:
  1. SSH into VPS:
     ssh root@{VPS}
     Password: {PASS}
  
  2. On the VPS run:
     mkdir -p {APP_DIR}
     cd {APP_DIR}
     
  3. Then from your local PC, use scp:
     scp bvc-deploy.tar.gz root@{VPS}:{APP_DIR}/
     
  4. On the VPS:
     cd {APP_DIR}
     tar xzf bvc-deploy.tar.gz
     bash deploy.sh

The tar file is ready at: {tar_path}
""")
