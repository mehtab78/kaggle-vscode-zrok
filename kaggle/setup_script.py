#!/usr/bin/env python3
"""
Kaggle VS Code Remote Setup Script
Run this script in a Kaggle notebook to set up remote VS Code connection.
Supports both PUBLIC and PRIVATE zrok tunnels.
"""

import subprocess
import os
import sys
import time
import threading
import re
import signal

# ╔═══════════════════════════════════════════════════════════════╗
# ║                    CONFIGURATION                              ║
# ║               ⚠️  EDIT THESE VALUES  ⚠️                        ║
# ╚═══════════════════════════════════════════════════════════════╝

ZROK_TOKEN = "YOUR_ZROK_TOKEN"       # Get from https://zrok.io
SSH_PASSWORD = "kaggle123"            # SSH login password
GITHUB_USERNAME = ""                  # Optional: GitHub username for SSH key auth

# Tunnel mode: "public" or "private"
# - PUBLIC:  Direct SSH access (ssh root@hostname.share.zrok.io)
#            No zrok needed on client. Easier but less secure.
# - PRIVATE: Requires `zrok access private <token>` on client
#            More secure, requires zrok on client machine.
TUNNEL_MODE = "public"

# ╔═══════════════════════════════════════════════════════════════╗
# ║                    DO NOT EDIT BELOW                          ║
# ╚═══════════════════════════════════════════════════════════════╝

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def run_command(cmd, show=False, check=False):
    """Run a shell command and return the result."""
    if show:
        print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print_error(f"Command failed: {cmd}")
        print(result.stderr)
    return result

def setup_ssh():
    """Install and configure SSH server."""
    print_info("Installing SSH server...")
    run_command("apt-get update -qq")
    run_command("apt-get install -y -qq openssh-server > /dev/null 2>&1")
    
    # Create required directories
    os.makedirs("/run/sshd", exist_ok=True)
    os.makedirs("/root/.ssh", exist_ok=True)
    os.chmod("/root/.ssh", 0o700)
    
    # Write optimized SSH config
    sshd_config = """
Port 22
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
X11Forwarding yes
ClientAliveInterval 60
ClientAliveCountMax 3
Subsystem sftp /usr/lib/openssh/sftp-server
"""
    with open("/etc/ssh/sshd_config", "w") as f:
        f.write(sshd_config)
    
    # Set root password
    run_command(f"echo 'root:{SSH_PASSWORD}' | chpasswd")
    
    # Add GitHub SSH keys if provided
    if GITHUB_USERNAME:
        print_info(f"Adding SSH keys from GitHub: {GITHUB_USERNAME}")
        result = run_command(f"curl -sf https://github.com/{GITHUB_USERNAME}.keys")
        if result.returncode == 0 and result.stdout.strip():
            with open("/root/.ssh/authorized_keys", "a") as f:
                f.write(result.stdout)
            os.chmod("/root/.ssh/authorized_keys", 0o600)
            print_success("SSH keys added from GitHub")
        else:
            print_warning(f"Could not fetch SSH keys for {GITHUB_USERNAME}")
    
    # Generate host keys and start SSH
    run_command("ssh-keygen -A 2>/dev/null")
    run_command("/usr/sbin/sshd")
    print_success("SSH server configured and running")

def install_zrok():
    """Install zrok using official installer."""
    print_info("Installing zrok...")
    result = run_command("curl -sSf https://get.zrok.io | bash", check=False)
    if result.returncode != 0:
        # Fallback to manual download
        print_warning("Official installer failed, trying manual download...")
        run_command("wget -q https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_linux_amd64.tar.gz")
        run_command("tar -xzf zrok_0.4.44_linux_amd64.tar.gz")
        run_command("chmod +x zrok && mv zrok /usr/local/bin/")
    print_success("zrok installed")

def enable_zrok():
    """Enable zrok with the provided token."""
    print_info("Enabling zrok...")
    # Disable first in case already enabled
    run_command("zrok disable 2>/dev/null")
    result = run_command(f"zrok enable {ZROK_TOKEN} 2>&1")
    if "enabled" in result.stdout.lower() or result.returncode == 0:
        print_success("zrok enabled")
        return True
    else:
        print_error("Failed to enable zrok. Check your token.")
        print(result.stdout)
        print(result.stderr)
        return False

def start_public_tunnel():
    """Start a PUBLIC zrok tunnel (direct SSH access)."""
    print_header("🌐 Starting PUBLIC Tunnel")
    print_info("Mode: Direct SSH access (no zrok needed on client)")
    
    process = subprocess.Popen(
        ['zrok', 'share', 'public', '--backend-mode', 'tcpTunnel', 'localhost:22'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    hostname_found = False
    for line in process.stdout:
        print(line, end='')
        
        # Parse the hostname from output
        if not hostname_found and 'zrok.io' in line.lower():
            match = re.search(r'https://([a-z0-9]+\.share\.zrok\.io)', line)
            if not match:
                match = re.search(r'([a-z0-9]+\.share\.zrok\.io)', line)
            if match:
                hostname = match.group(1)
                hostname_found = True
                print_connection_info_public(hostname)

def start_private_tunnel():
    """Start a PRIVATE zrok tunnel (requires zrok on client)."""
    print_header("🔒 Starting PRIVATE Tunnel")
    print_info("Mode: Secure tunnel (requires zrok on client)")
    
    process = subprocess.Popen(
        ['zrok', 'share', 'private', '--backend-mode', 'tcpTunnel', 'localhost:22'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    share_token_found = False
    for line in process.stdout:
        print(line, end='')
        
        # Parse the share token from output
        if not share_token_found and 'share token' in line.lower():
            match = re.search(r'share token[:\s]+([a-z0-9]+)', line.lower())
            if match:
                share_token = match.group(1)
                share_token_found = True
                print_connection_info_private(share_token)

def print_connection_info_public(hostname):
    """Print connection info for PUBLIC tunnel."""
    print("\n")
    print_header("🎉 PUBLIC TUNNEL ACTIVE!")
    print(f"""
{Colors.BOLD}📋 CONNECTION INFO:{Colors.END}
   
   Hostname:  {Colors.CYAN}{hostname}{Colors.END}
   User:      root
   Password:  {SSH_PASSWORD}

{Colors.BOLD}🔗 CONNECT VIA SSH:{Colors.END}
   ssh root@{hostname}

{Colors.BOLD}💻 CONNECT VIA VS CODE:{Colors.END}
   1. Install 'Remote - SSH' extension
   2. Press F1 → "Remote-SSH: Connect to Host"
   3. Enter: root@{hostname}
   
   Or run: code --remote ssh-remote+root@{hostname} /kaggle/working

{Colors.BOLD}🐧 DEBIAN 12 QUICK CONNECT:{Colors.END}
   python3 connect.py -H {hostname}
   python3 connect.py -H {hostname} --vscode
""")
    print("=" * 60)

def print_connection_info_private(share_token):
    """Print connection info for PRIVATE tunnel."""
    print("\n")
    print_header("🔒 PRIVATE TUNNEL ACTIVE!")
    print(f"""
{Colors.BOLD}📋 CONNECTION INFO:{Colors.END}
   
   Share Token:  {Colors.CYAN}{share_token}{Colors.END}
   User:         root
   Password:     {SSH_PASSWORD}

{Colors.BOLD}🔗 ON YOUR LOCAL MACHINE:{Colors.END}

   Step 1: Start zrok access (in one terminal)
   $ zrok access private {share_token}
   
   Step 2: Connect via SSH (in another terminal)
   $ ssh root@localhost -p 9191

{Colors.BOLD}💻 VS CODE CONNECTION:{Colors.END}
   After running 'zrok access private':
   1. Add to ~/.ssh/config:
      Host kaggle
          HostName localhost
          Port 9191
          User root
   2. Connect via Remote-SSH to 'kaggle'

{Colors.BOLD}🐧 DEBIAN 12 QUICK CONNECT:{Colors.END}
   python3 connect.py --private {share_token}
""")
    print("=" * 60)

def keep_alive():
    """Keep the notebook alive with status updates."""
    print_info("Keeping notebook alive... (Press Ctrl+C to stop)")
    start_time = time.time()
    
    try:
        while True:
            time.sleep(300)  # 5 minutes
            elapsed = int(time.time() - start_time)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"[{time.strftime('%H:%M:%S')}] Running for {hours:02d}:{minutes:02d}:{seconds:02d}")
    except KeyboardInterrupt:
        print("\n")
        print_warning("Tunnel stopped by user")

def main():
    """Main setup function."""
    print_header("🚀 Kaggle VS Code Remote Setup")
    print(f"   Tunnel Mode: {Colors.BOLD}{TUNNEL_MODE.upper()}{Colors.END}")
    
    # Validate configuration
    if ZROK_TOKEN == "YOUR_ZROK_TOKEN":
        print_error("Please set your ZROK_TOKEN!")
        print_info("Get one at https://zrok.io")
        return
    
    if TUNNEL_MODE not in ["public", "private"]:
        print_error("TUNNEL_MODE must be 'public' or 'private'")
        return
    
    # Setup steps
    print("\n[1/4] Setting up SSH server...")
    setup_ssh()
    
    print("\n[2/4] Installing zrok...")
    install_zrok()
    
    print("\n[3/4] Enabling zrok...")
    if not enable_zrok():
        return
    
    print("\n[4/4] Starting tunnel...")
    
    # Start tunnel in a thread
    if TUNNEL_MODE == "public":
        tunnel_func = start_public_tunnel
    else:
        tunnel_func = start_private_tunnel
    
    tunnel_thread = threading.Thread(target=tunnel_func, daemon=True)
    tunnel_thread.start()
    
    # Wait for tunnel to start
    time.sleep(3)
    
    # Keep notebook alive
    keep_alive()

if __name__ == "__main__":
    main()
