#!/usr/bin/env python3
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
            match = re.search(r'([a-z0-9]+\.share\.zrok\.io)', line)
            if match:
                hostname = match.group(1)
                print("\n" + "="*60)
                print("🎉 CONNECTION SUCCESSFUL!")
                print("="*60)
                print(f"\nTo connect via VS Code:")
                print(f"1. Install 'Remote - SSH' extension")
                print(f"2. Add to ~/.ssh/config:")
                print(f"\n   Host kaggle")
                print(f"       HostName {hostname}")
                print(f"       User root")
                print(f"       Port 22")
                print(f"\n3. Or use SSH command:")
                print(f"   ssh root@{hostname}")
                print(f"\n   Password: {SSH_PASSWORD}")
                print("="*60 + "\n")

def keep_alive():
    """Keep the notebook alive."""
    print("\n⏰ Keeping notebook alive...")
    print("Press Ctrl+C to stop.\n")
    while True:
        time.sleep(60)
        print(f"Still running... {time.strftime('%H:%M:%S')}")

def main():
    """Main setup function."""
    print("="*60)
    print("🚀 Kaggle VS Code Remote Setup")
    print("="*60 + "\n")
    
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
