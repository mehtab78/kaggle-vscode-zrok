#!/usr/bin/env python3
"""
Kaggle VS Code Connection Helper
A Python-based SSH connection manager for connecting to Kaggle via zrok tunnel.
Optimized for Debian 12 / Linux systems.
"""

import subprocess
import sys
import os
import json
import argparse
from pathlib import Path

# Configuration file path
CONFIG_FILE = Path.home() / ".kaggle_vscode_config.json"

def load_config():
    """Load saved configuration."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save configuration for future use."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)  # Secure the config file

def check_dependencies():
    """Check if required dependencies are installed."""
    deps = {
        'ssh': 'openssh-client',
        'sshpass': 'sshpass'
    }
    
    missing = []
    for cmd, pkg in deps.items():
        result = subprocess.run(['which', cmd], capture_output=True)
        if result.returncode != 0:
            missing.append(pkg)
    
    if missing:
        print("❌ Missing dependencies. Install with:")
        print(f"   sudo apt install {' '.join(missing)}")
        return False
    return True

def update_ssh_config(hostname, alias="kaggle"):
    """Update ~/.ssh/config with Kaggle connection."""
    ssh_dir = Path.home() / ".ssh"
    ssh_config = ssh_dir / "config"
    
    # Ensure .ssh directory exists
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    
    # SSH config entry
    entry = f"""
# Kaggle Remote Connection (auto-generated)
Host {alias}
    HostName {hostname}
    User root
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3
    LogLevel ERROR
"""
    
    # Read existing config
    existing = ""
    if ssh_config.exists():
        existing = ssh_config.read_text()
    
    # Remove old Kaggle entry if exists
    lines = existing.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if line.strip().startswith(f'Host {alias}'):
            skip = True
            continue
        if skip and line.strip().startswith('Host '):
            skip = False
        if not skip and not line.strip().startswith('# Kaggle Remote Connection'):
            new_lines.append(line)
    
    # Add new entry
    new_config = '\n'.join(new_lines).strip() + entry
    
    # Write config
    ssh_config.write_text(new_config)
    ssh_config.chmod(0o600)
    
    print(f"✅ SSH config updated for '{alias}'")

def connect_ssh(hostname, password=None, use_key=False):
    """Connect to Kaggle via SSH."""
    if use_key:
        # Key-based authentication
        cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', 
               f'root@{hostname}']
    elif password:
        # Password-based authentication with sshpass
        cmd = ['sshpass', '-p', password, 'ssh', '-o', 'StrictHostKeyChecking=no', 
               '-o', 'UserKnownHostsFile=/dev/null', f'root@{hostname}']
    else:
        # Interactive password prompt
        cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null',
               f'root@{hostname}']
    
    print(f"\n🔗 Connecting to {hostname}...")
    subprocess.run(cmd)

def open_vscode(hostname):
    """Open VS Code with Remote SSH."""
    # Check if code command exists
    result = subprocess.run(['which', 'code'], capture_output=True)
    if result.returncode != 0:
        print("❌ VS Code 'code' command not found.")
        print("   Install VS Code and add to PATH, or connect manually.")
        return False
    
    print(f"🚀 Opening VS Code Remote SSH to {hostname}...")
    subprocess.run(['code', '--remote', f'ssh-remote+root@{hostname}', '/kaggle/working'])
    return True

def list_saved():
    """List saved connections."""
    config = load_config()
    if not config.get('connections'):
        print("No saved connections.")
        return
    
    print("\n📋 Saved Connections:")
    print("-" * 40)
    for name, data in config.get('connections', {}).items():
        print(f"  {name}: {data.get('hostname', 'N/A')}")

def interactive_menu():
    """Show interactive menu."""
    print("\n" + "=" * 50)
    print("  🐍 Kaggle VS Code Connection Helper")
    print("     Optimized for Debian 12")
    print("=" * 50)
    
    config = load_config()
    last_hostname = config.get('last_hostname', '')
    last_password = config.get('last_password', 'kaggle123')
    
    print("\nOptions:")
    print("  1. Connect via SSH")
    print("  2. Open in VS Code")
    print("  3. Update SSH config")
    print("  4. List saved connections")
    print("  5. Exit")
    
    choice = input("\nSelect option [1-5]: ").strip()
    
    if choice == '1' or choice == '2':
        if last_hostname:
            hostname = input(f"Enter zrok hostname [{last_hostname}]: ").strip() or last_hostname
        else:
            hostname = input("Enter zrok hostname (e.g., abc123.share.zrok.io): ").strip()
        
        if not hostname:
            print("❌ Hostname required!")
            return
        
        password = input(f"Enter password [{last_password}]: ").strip() or last_password
        
        # Save for next time
        config['last_hostname'] = hostname
        config['last_password'] = password
        save_config(config)
        
        if choice == '1':
            connect_ssh(hostname, password)
        else:
            update_ssh_config(hostname)
            open_vscode(hostname)
            
    elif choice == '3':
        hostname = input("Enter zrok hostname: ").strip()
        alias = input("Enter alias [kaggle]: ").strip() or "kaggle"
        if hostname:
            update_ssh_config(hostname, alias)
        else:
            print("❌ Hostname required!")
            
    elif choice == '4':
        list_saved()
        
    elif choice == '5':
        print("Goodbye! 👋")
        sys.exit(0)
    else:
        print("Invalid option!")

def main():
    parser = argparse.ArgumentParser(
        description='Kaggle VS Code Connection Helper for Debian 12',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Interactive mode
  %(prog)s -H abc123.share.zrok.io   # Connect directly
  %(prog)s -H abc123.share.zrok.io --vscode  # Open in VS Code
  %(prog)s --setup-ssh abc123.share.zrok.io  # Update SSH config only
        """
    )
    
    parser.add_argument('-H', '--hostname', help='Zrok tunnel hostname')
    parser.add_argument('-p', '--password', default='kaggle123', help='SSH password (default: kaggle123)')
    parser.add_argument('-k', '--key', action='store_true', help='Use SSH key authentication')
    parser.add_argument('--vscode', action='store_true', help='Open in VS Code instead of terminal')
    parser.add_argument('--setup-ssh', metavar='HOSTNAME', help='Update SSH config only')
    parser.add_argument('--list', action='store_true', help='List saved connections')
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Handle specific commands
    if args.list:
        list_saved()
        return
    
    if args.setup_ssh:
        update_ssh_config(args.setup_ssh)
        return
    
    # Direct connection mode
    if args.hostname:
        # Save hostname
        config = load_config()
        config['last_hostname'] = args.hostname
        save_config(config)
        
        if args.vscode:
            update_ssh_config(args.hostname)
            open_vscode(args.hostname)
        else:
            connect_ssh(args.hostname, args.password if not args.key else None, args.key)
        return
    
    # Interactive mode
    while True:
        try:
            interactive_menu()
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break

if __name__ == "__main__":
    main()
