#!/bin/bash
#===============================================================================
# Quick Install Script for Debian 12
# Run: curl -sSL https://raw.githubusercontent.com/mehtab78/kaggle-vscode-zrok/main/local/install.sh | sudo bash
#===============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Kaggle VS Code Zrok - Quick Install${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"

# Install git if needed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    apt-get update -qq && apt-get install -y -qq git
fi

# Clone repository
INSTALL_DIR="/opt/kaggle-vscode-zrok"
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR" && git pull -q
else
    echo "Cloning repository..."
    git clone -q https://github.com/mehtab78/kaggle-vscode-zrok.git "$INSTALL_DIR"
fi

# Run setup
cd "$INSTALL_DIR/local"
chmod +x setup_debian12.sh
./setup_debian12.sh

echo -e "\n${GREEN}✅ Installation complete!${NC}"
echo "Repository installed at: $INSTALL_DIR"
# Kaggle VS Code Integration with Zrok

I'll create a complete GitHub repository structure for easily connecting Kaggle notebooks to VS Code using zrok tunneling.

## Repository Structure

```
kaggle-vscode-zrok/
├── README.md
├── kaggle/
│   ├── setup_kaggle.ipynb
│   └── setup_script.py
├── local/
│   ├── connect.sh
│   ├── connect.ps1
│   └── ssh_config_template
├── .vscode/
│   ├── settings.json
│   └── extensions.json
└── requirements.txt
```

## Download the ZIP file

Here's a Python script that creates the ZIP file with all necessary files:

```python
import zipfile
import os

# Create the repository structure
files = {}

# README.md
files['kaggle-vscode-zrok/README.md'] = '''# Kaggle VS Code Integration with Zrok

Connect to Kaggle notebooks remotely using VS Code through zrok tunneling.

## 🚀 Quick Start

### Step 1: Get Zrok Token (One-time setup)
1. Go to [https://zrok.io](https://zrok.io)
2. Sign up for a free account
3. Get your zrok token from the dashboard

### Step 2: Setup on Kaggle
1. Create a new Kaggle notebook
2. Enable GPU/TPU if needed
3. Enable Internet access in notebook settings
4. Copy the contents of `kaggle/setup_kaggle.ipynb` or run `setup_script.py`
5. Replace `YOUR_ZROK_TOKEN` with your actual token
6. Run all cells

### Step 3: Connect from VS Code
1. Install "Remote - SSH" extension in VS Code
2. Copy the SSH command displayed in Kaggle output
3. Add the config to your `~/.ssh/config`
4. Connect using VS Code Remote SSH

## 📁 Repository Structure

```
├── kaggle/
│   ├── setup_kaggle.ipynb    # Jupyter notebook for Kaggle
│   └── setup_script.py       # Python script version
├── local/
│   ├── connect.sh            # Linux/Mac connection helper
│   ├── connect.ps1           # Windows PowerShell helper
│   └── ssh_config_template   # SSH config template
└── .vscode/
    ├── settings.json         # VS Code settings
    └── extensions.json       # Recommended extensions
```

## 🔧 Detailed Instructions

### On Kaggle Notebook:

```python
# Run this in a Kaggle notebook cell
!pip install kaggle-vscode-zrok  # or copy the setup script
```

### Manual Setup:
```python
# Cell 1: Install dependencies
!apt-get update && apt-get install -y openssh-server
!pip install jupyterlab

# Cell 2: Configure SSH
!mkdir -p /root/.ssh
!echo "YOUR_SSH_PUBLIC_KEY" >> /root/.ssh/authorized_keys
!chmod 700 /root/.ssh
!chmod 600 /root/.ssh/authorized_keys
!service ssh start

# Cell 3: Install and setup zrok
!wget https://github.com/openziti/zrok/releases/latest/download/zrok_linux_amd64.tar.gz
!tar -xzf zrok_linux_amd64.tar.gz
!./zrok enable YOUR_ZROK_TOKEN
!./zrok share private --backend-mode tcpTunnel localhost:22 &
```

## ⚠️ Important Notes

- Kaggle notebooks have a 12-hour runtime limit
- GPU sessions may have shorter limits
- Save your work frequently
- The connection will break when the notebook times out

## 🔐 Security

- Use SSH key authentication (recommended)
- Never share your zrok token
- The tunnel is private by default

## 📝 License

MIT License
'''

# Kaggle Setup Notebook (as Python script for the .ipynb content)
files['kaggle-vscode-zrok/kaggle/setup_kaggle.ipynb'] = '''{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Kaggle VS Code Remote Setup\\n",
    "Run all cells to set up remote VS Code connection via zrok"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Configuration - EDIT THESE VALUES\\n",
    "ZROK_TOKEN = \\"YOUR_ZROK_TOKEN\\"  # Get from https://zrok.io\\n",
    "SSH_PASSWORD = \\"kaggle123\\"  # Set your SSH password\\n",
    "SSH_PUBLIC_KEY = \\"\\"  # Optional: Your SSH public key for key-based auth"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Cell 1: Install system dependencies\\n",
    "!apt-get update -qq\\n",
    "!apt-get install -y -qq openssh-server > /dev/null 2>&1\\n",
    "print(\\"✅ SSH server installed\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Cell 2: Configure SSH\\n",
    "import subprocess\\n",
    "\\n",
    "# Set root password\\n",
    "subprocess.run(f\\"echo 'root:{SSH_PASSWORD}' | chpasswd\\", shell=True)\\n",
    "\\n",
    "# Configure SSH to allow root login\\n",
    "!sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config\\n",
    "!sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config\\n",
    "\\n",
    "# Add SSH public key if provided\\n",
    "if SSH_PUBLIC_KEY:\\n",
    "    !mkdir -p /root/.ssh\\n",
    "    !echo \\"{SSH_PUBLIC_KEY}\\" >> /root/.ssh/authorized_keys\\n",
    "    !chmod 700 /root/.ssh\\n",
    "    !chmod 600 /root/.ssh/authorized_keys\\n",
    "    print(\\"✅ SSH key added\\")\\n",
    "\\n",
    "# Start SSH service\\n",
    "!service ssh start\\n",
    "print(\\"✅ SSH server started\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Cell 3: Install zrok\\n",
    "!wget -q https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_linux_amd64.tar.gz\\n",
    "!tar -xzf zrok_0.4.44_linux_amd64.tar.gz\\n",
    "!chmod +x zrok\\n",
    "!mv zrok /usr/local/bin/\\n",
    "print(\\"✅ zrok installed\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Cell 4: Enable zrok with your token\\n",
    "!zrok enable {ZROK_TOKEN}\\n",
    "print(\\"✅ zrok enabled\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Cell 5: Start zrok tunnel (this will display connection info)\\n",
    "import subprocess\\n",
    "import threading\\n",
    "import time\\n",
    "import re\\n",
    "\\n",
    "def run_zrok():\\n",
    "    process = subprocess.Popen(\\n",
    "        ['zrok', 'share', 'public', '--backend-mode', 'tcpTunnel', 'localhost:22'],\\n",
    "        stdout=subprocess.PIPE,\\n",
    "        stderr=subprocess.STDOUT,\\n",
    "        text=True\\n",
    "    )\\n",
    "    for line in process.stdout:\\n",
    "        print(line, end='')\\n",
    "        if 'https://' in line:\\n",
    "            url = re.search(r'https://[\\\\w.-]+', line)\\n",
    "            if url:\\n",
    "                print(f\\"\\\\n\\" + \\"=\\"*60)\\n",
    "                print(\\"🎉 CONNECTION INFO:\\")\\n",
    "                print(f\\"=\\"*60)\\n",
    "                print(f\\"Tunnel URL: {url.group()}\\")\\n",
    "                print(f\\"SSH Command: ssh root@{url.group().replace('https://', '')} -p 22\\")\\n",
    "                print(f\\"Password: {SSH_PASSWORD}\\")\\n",
    "                print(\\"=\\"*60 + \\"\\\\n\\")\\n",
    "\\n",
    "thread = threading.Thread(target=run_zrok, daemon=True)\\n",
    "thread.start()\\n",
    "print(\\"🚀 Starting zrok tunnel... Please wait for connection info.\\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Cell 6: Keep notebook alive\\n",
    "import time\\n",
    "print(\\"⏰ Keeping notebook alive. Don't close this tab!\\")\\n",
    "print(\\"Press Ctrl+C to stop.\\")\\n",
    "\\n",
    "while True:\\n",
    "    time.sleep(60)\\n",
    "    print(f\\"Still running... {time.strftime('%H:%M:%S')}\\")"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.10.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}'''

# Setup Script (Python version)
files['kaggle-vscode-zrok/kaggle/setup_script.py'] = '''#!/usr/bin/env python3
"""
Kaggle VS Code Remote Setup Script
Run this script in a Kaggle notebook to set up remote VS Code connection.
"""

import subprocess
import os
import time
import threading
import re

# ============================================
# CONFIGURATION - EDIT THESE VALUES
# ============================================
ZROK_TOKEN = "YOUR_ZROK_TOKEN"  # Get from https://zrok.io
SSH_PASSWORD = "kaggle123"       # Set your SSH password
SSH_PUBLIC_KEY = ""              # Optional: Your SSH public key

# ============================================
# DO NOT EDIT BELOW THIS LINE
# ============================================

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running: {cmd}")
        print(result.stderr)
    return result

def setup_ssh():
    """Install and configure SSH server."""
    print("📦 Installing SSH server...")
    run_command("apt-get update -qq")
    run_command("apt-get install -y -qq openssh-server")
    
    print("🔧 Configuring SSH...")
    # Set root password
    run_command(f"echo 'root:{SSH_PASSWORD}' | chpasswd")
    
    # Configure SSH
    run_command("sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config")
    run_command("sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config")
    
    # Add SSH public key if provided
    if SSH_PUBLIC_KEY:
        run_command("mkdir -p /root/.ssh")
        run_command(f"echo '{SSH_PUBLIC_KEY}' >> /root/.ssh/authorized_keys")
        run_command("chmod 700 /root/.ssh")
        run_command("chmod 600 /root/.ssh/authorized_keys")
        print("✅ SSH key added")
    
    # Start SSH service
    run_command("service ssh start")
    print("✅ SSH server started")

def install_zrok():
    """Download and install zrok."""
    print("📦 Installing zrok...")
    run_command("wget -q https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_linux_amd64.tar.gz")
    run_command("tar -xzf zrok_0.4.44_linux_amd64.tar.gz")
    run_command("chmod +x zrok")
    run_command("mv zrok /usr/local/bin/")
    print("✅ zrok installed")

def enable_zrok():
    """Enable zrok with the provided token."""
    print("🔑 Enabling zrok...")
    result = run_command(f"zrok enable {ZROK_TOKEN}")
    if result.returncode == 0:
        print("✅ zrok enabled")
    else:
        print("❌ Failed to enable zrok. Check your token.")
        return False
    return True

def start_tunnel():
    """Start the zrok tunnel."""
    print("🚀 Starting zrok tunnel...")
    
    process = subprocess.Popen(
        ['zrok', 'share', 'public', '--backend-mode', 'tcpTunnel', 'localhost:22'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    for line in process.stdout:
        print(line, end='')
        if 'zrok.io' in line.lower() or 'share token' in line.lower():
            match = re.search(r'([a-z0-9]+\\.share\\.zrok\\.io)', line)
            if match:
                hostname = match.group(1)
                print("\\n" + "="*60)
                print("🎉 CONNECTION SUCCESSFUL!")
                print("="*60)
                print(f"\\nTo connect via VS Code:")
                print(f"1. Install 'Remote - SSH' extension")
                print(f"2. Add to ~/.ssh/config:")
                print(f"\\n   Host kaggle")
                print(f"       HostName {hostname}")
                print(f"       User root")
                print(f"       Port 22")
                print(f"\\n3. Or use SSH command:")
                print(f"   ssh root@{hostname}")
                print(f"\\n   Password: {SSH_PASSWORD}")
                print("="*60 + "\\n")

def keep_alive():
    """Keep the notebook alive."""
    print("\\n⏰ Keeping notebook alive...")
    print("Press Ctrl+C to stop.\\n")
    while True:
        time.sleep(60)
        print(f"Still running... {time.strftime('%H:%M:%S')}")

def main():
    """Main setup function."""
    print("="*60)
    print("🚀 Kaggle VS Code Remote Setup")
    print("="*60 + "\\n")
    
    if ZROK_TOKEN == "YOUR_ZROK_TOKEN":
        print("❌ ERROR: Please set your ZROK_TOKEN!")
        print("Get one at https://zrok.io")
        return
    
    setup_ssh()
    install_zrok()
    
    if enable_zrok():
        # Start tunnel in a thread
        tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
        tunnel_thread.start()
        
        # Wait a bit for tunnel to start
        time.sleep(5)
        
        # Keep notebook alive
        keep_alive()

if __name__ == "__main__":
    main()
'''

# Local connect script for Linux/Mac
files['kaggle-vscode-zrok/local/connect.sh'] = '''#!/bin/bash
# Kaggle VS Code Connection Helper for Linux/Mac

echo "=========================================="
echo "  Kaggle VS Code Connection Helper"
echo "=========================================="

# Check if ssh is installed
if ! command -v ssh &> /dev/null; then
    echo "Error: SSH is not installed"
    exit 1
fi

# Prompt for connection details
read -p "Enter zrok hostname (e.g., abc123.share.zrok.io): " HOSTNAME
read -p "Enter password [kaggle123]: " PASSWORD
PASSWORD=${PASSWORD:-kaggle123}

echo ""
echo "Connecting to Kaggle..."
echo "Password: $PASSWORD"
echo ""

ssh root@$HOSTNAME
'''

# Local connect script for Windows
files['kaggle-vscode-zrok/local/connect.ps1'] = '''# Kaggle VS Code Connection Helper for Windows PowerShell

Write-Host "=========================================="
Write-Host "  Kaggle VS Code Connection Helper"
Write-Host "=========================================="

# Prompt for connection details
$Hostname = Read-Host "Enter zrok hostname (e.g., abc123.share.zrok.io)"
$Password = Read-Host "Enter password (default: kaggle123)"
if ([string]::IsNullOrEmpty($Password)) {
    $Password = "kaggle123"
}

Write-Host ""
Write-Host "Connecting to Kaggle..."
Write-Host "Password: $Password"
Write-Host ""

ssh root@$Hostname
'''

# SSH config template
files['kaggle-vscode-zrok/local/ssh_config_template'] = '''# Add this to ~/.ssh/config

# Kaggle Remote Connection
Host kaggle
    HostName YOUR_ZROK_HOSTNAME.share.zrok.io
    User root
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

# Alternative with specific settings
Host kaggle-gpu
    HostName YOUR_ZROK_HOSTNAME.share.zrok.io
    User root
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3
'''

# VS Code settings
files['kaggle-vscode-zrok/.vscode/settings.json'] = '''{
    "remote.SSH.remotePlatform": {
        "kaggle": "linux"
    },
    "remote.SSH.connectTimeout": 60,
    "remote.SSH.defaultExtensions": [
        "ms-python.python",
        "ms-toolsai.jupyter"
    ],
    "remote.SSH.showLoginTerminal": true,
    "python.defaultInterpreterPath": "/opt/conda/bin/python"
}
'''

# VS Code extensions
files['kaggle-vscode-zrok/.vscode/extensions.json'] = '''{
    "recommendations": [
        "ms-vscode-remote.remote-ssh",
        "ms-vscode-remote.remote-ssh-edit",
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-toolsai.jupyter",
        "ms-toolsai.jupyter-keymap",
        "ms-toolsai.jupyter-renderers"
    ]
}
'''

# Requirements
files['kaggle-vscode-zrok/requirements.txt'] = '''# Local development requirements (optional)
paramiko>=2.7.0
'''

# .gitignore
files['kaggle-vscode-zrok/.gitignore'] = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/

# IDE
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Secrets
*.pem
*.key
zrok_token.txt
'''

# Create ZIP file
with zipfile.ZipFile('kaggle-vscode-zrok.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for filepath, content in files.items():
        zipf.writestr(filepath, content)

print("✅ Created kaggle-vscode-zrok.zip successfully!")
print("\nContents:")
for filepath in sorted(files.keys()):
    print(f"  📄 {filepath}")
```

## Quick Start Guide

### Step 1: Get Zrok Token
1. Go to [https://zrok.io](https://zrok.io)
2. Create a free account
3. Copy your token from the dashboard

### Step 2: On Kaggle
```python
# Run this in a Kaggle notebook cell

# Configuration
ZROK_TOKEN = "your_token_here"
SSH_PASSWORD = "kaggle123"

# Install dependencies
!apt-get update -qq && apt-get install -y -qq openssh-server

# Configure SSH
!echo "root:$SSH_PASSWORD" | chpasswd
!sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
!sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
!service ssh start

# Install zrok
!wget -q https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_linux_amd64.tar.gz
!tar -xzf zrok_0.4.44_linux_amd64.tar.gz && chmod +x zrok && mv zrok /usr/local/bin/

# Enable and start tunnel
!zrok enable $ZROK_TOKEN
!zrok share public --backend-mode tcpTunnel localhost:22
```

### Step 3: Connect from VS Code
1. Install **Remote - SSH** extension
2. Press `F1` → "Remote-SSH: Connect to Host"
3. Enter: `root@YOUR_HOSTNAME.share.zrok.io`
4. Enter password when prompted

Would you like me to run the Python script to generate the actual ZIP file, or do you need any modifications to the setup?