#!/usr/bin/env python3
"""
Kaggle VS Code Connection Helper
A Python-based SSH connection manager for connecting to Kaggle via zrok tunnel.
Supports both PUBLIC and PRIVATE tunnels.
Optimized for Debian 12 / Linux systems.
"""

import subprocess
import sys
import os
import json
import argparse
import time
import signal
import threading
from pathlib import Path

# Configuration file path
CONFIG_FILE = Path.home() / ".kaggle_vscode_config.json"
ZROK_PID_FILE = Path.home() / ".kaggle_zrok_access.pid"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

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
    os.chmod(CONFIG_FILE, 0o600)

def check_dependencies(include_zrok=False):
    """Check if required dependencies are installed."""
    deps = {
        'ssh': 'openssh-client',
        'sshpass': 'sshpass'
    }
    
    if include_zrok:
        deps['zrok'] = 'zrok (install from https://zrok.io)'
    
    missing = []
    for cmd, pkg in deps.items():
        result = subprocess.run(['which', cmd], capture_output=True)
        if result.returncode != 0:
            missing.append(pkg)
    
    if missing:
        print_error("Missing dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        if 'zrok' not in str(missing):
            print(f"\n   Install with: sudo apt install {' '.join([p for p in missing if 'zrok' not in p])}")
        return False
    return True

def update_ssh_config(hostname, port=22, alias="kaggle"):
    """Update ~/.ssh/config with Kaggle connection."""
    ssh_dir = Path.home() / ".ssh"
    ssh_config = ssh_dir / "config"
    
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    
    entry = f"""
# Kaggle Remote Connection (auto-generated)
Host {alias}
    HostName {hostname}
    User root
    Port {port}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3
    LogLevel ERROR
"""
    
    existing = ""
    if ssh_config.exists():
        existing = ssh_config.read_text()
    
    # Remove old entry
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
    
    new_config = '\n'.join(new_lines).strip() + entry
    ssh_config.write_text(new_config)
    ssh_config.chmod(0o600)
    
    print_success(f"SSH config updated for '{alias}'")

def connect_ssh(hostname, port=22, password=None, use_key=False):
    """Connect to Kaggle via SSH."""
    if use_key:
        cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null',
               '-p', str(port), f'root@{hostname}']
    elif password:
        cmd = ['sshpass', '-p', password, 'ssh', '-o', 'StrictHostKeyChecking=no',
               '-o', 'UserKnownHostsFile=/dev/null', '-p', str(port), f'root@{hostname}']
    else:
        cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null',
               '-p', str(port), f'root@{hostname}']
    
    print(f"\n{Colors.BLUE}🔗 Connecting to {hostname}:{port}...{Colors.END}")
    subprocess.run(cmd)

def open_vscode(hostname, port=22, remote_path="/kaggle/working"):
    """Open VS Code with Remote SSH."""
    result = subprocess.run(['which', 'code'], capture_output=True)
    if result.returncode != 0:
        print_error("VS Code 'code' command not found.")
        print_info("Install VS Code and add to PATH, or connect manually.")
        return False
    
    if port != 22:
        # For non-standard ports, update SSH config first
        update_ssh_config(hostname, port, "kaggle-temp")
        remote_uri = f'ssh-remote+kaggle-temp'
    else:
        remote_uri = f'ssh-remote+root@{hostname}'
    
    print_info(f"Opening VS Code Remote SSH to {hostname}:{port}...")
    subprocess.run(['code', '--remote', remote_uri, remote_path])
    return True

def start_zrok_access(share_token, local_port=9191):
    """Start zrok access private for a share token."""
    print_info(f"Starting zrok access for token: {share_token}")
    print_info(f"Local port: {local_port}")
    
    # Kill any existing zrok access process
    stop_zrok_access()
    
    # Start zrok access in background
    process = subprocess.Popen(
        ['zrok', 'access', 'private', '--bind', f'127.0.0.1:{local_port}', share_token],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Save PID
    with open(ZROK_PID_FILE, 'w') as f:
        f.write(str(process.pid))
    
    print_success(f"zrok access started (PID: {process.pid})")
    print_info("Waiting for tunnel to establish...")
    time.sleep(3)
    
    return process

def stop_zrok_access():
    """Stop any running zrok access process."""
    if ZROK_PID_FILE.exists():
        try:
            pid = int(ZROK_PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print_info(f"Stopped zrok access (PID: {pid})")
        except (ProcessLookupError, ValueError):
            pass
        ZROK_PID_FILE.unlink(missing_ok=True)
    
    # Also kill any stray zrok access processes
    subprocess.run(['pkill', '-f', 'zrok access'], capture_output=True)

def connect_private(share_token, password=None, use_key=False, vscode=False, local_port=9191):
    """Connect via private tunnel."""
    if not check_dependencies(include_zrok=True):
        return
    
    print(f"\n{Colors.BOLD}🔒 Private Tunnel Connection{Colors.END}")
    print(f"   Share Token: {share_token}")
    print(f"   Local Port:  {local_port}")
    
    # Start zrok access in background thread
    zrok_process = start_zrok_access(share_token, local_port)
    
    try:
        if vscode:
            update_ssh_config("localhost", local_port, "kaggle")
            open_vscode("localhost", local_port)
        else:
            connect_ssh("localhost", local_port, password, use_key)
    finally:
        # Stop zrok access when done
        stop_zrok_access()

def connect_public(hostname, password=None, use_key=False, vscode=False):
    """Connect via public tunnel."""
    if not check_dependencies():
        return
    
    print(f"\n{Colors.BOLD}🌐 Public Tunnel Connection{Colors.END}")
    print(f"   Hostname: {hostname}")
    
    # Save for next time
    config = load_config()
    config['last_hostname'] = hostname
    config['last_mode'] = 'public'
    save_config(config)
    
    if vscode:
        update_ssh_config(hostname)
        open_vscode(hostname)
    else:
        connect_ssh(hostname, 22, password, use_key)

def interactive_menu():
    """Show interactive menu."""
    print(f"\n{Colors.BLUE}{'='*55}{Colors.END}")
    print(f"{Colors.BOLD}  🐍 Kaggle VS Code Connection Helper{Colors.END}")
    print(f"{Colors.CYAN}     Supports PUBLIC and PRIVATE tunnels{Colors.END}")
    print(f"{Colors.BLUE}{'='*55}{Colors.END}")
    
    config = load_config()
    last_hostname = config.get('last_hostname', '')
    last_token = config.get('last_token', '')
    last_password = config.get('last_password', 'kaggle123')
    last_mode = config.get('last_mode', 'public')
    
    print(f"\n{Colors.BOLD}Connection Mode:{Colors.END}")
    print("  1. PUBLIC  - Direct SSH (hostname.share.zrok.io)")
    print("  2. PRIVATE - Via zrok access (share token)")
    print("  3. Exit")
    
    mode = input(f"\nSelect mode [1-3] (last: {last_mode}): ").strip() or ('1' if last_mode == 'public' else '2')
    
    if mode == '3':
        print("Goodbye! 👋")
        sys.exit(0)
    
    if mode == '1':
        # Public mode
        if last_hostname and last_mode == 'public':
            hostname = input(f"Enter hostname [{last_hostname}]: ").strip() or last_hostname
        else:
            hostname = input("Enter hostname (e.g., abc123.share.zrok.io): ").strip()
        
        if not hostname:
            print_error("Hostname required!")
            return
            
    elif mode == '2':
        # Private mode
        if last_token and last_mode == 'private':
            share_token = input(f"Enter share token [{last_token}]: ").strip() or last_token
        else:
            share_token = input("Enter share token: ").strip()
        
        if not share_token:
            print_error("Share token required!")
            return
        
        config['last_token'] = share_token
        config['last_mode'] = 'private'
    else:
        print_error("Invalid option!")
        return
    
    password = input(f"Enter password [{last_password}]: ").strip() or last_password
    config['last_password'] = password
    save_config(config)
    
    print(f"\n{Colors.BOLD}Connect via:{Colors.END}")
    print("  1. SSH terminal")
    print("  2. VS Code")
    
    connect_type = input("\nSelect [1-2]: ").strip() or '1'
    vscode = connect_type == '2'
    
    if mode == '1':
        connect_public(hostname, password, vscode=vscode)
    else:
        connect_private(share_token, password, vscode=vscode)

def main():
    parser = argparse.ArgumentParser(
        description='Kaggle VS Code Connection Helper - Supports PUBLIC and PRIVATE tunnels',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.BOLD}Examples:{Colors.END}

  {Colors.CYAN}# Interactive mode{Colors.END}
  %(prog)s

  {Colors.CYAN}# PUBLIC tunnel (direct SSH){Colors.END}
  %(prog)s -H abc123.share.zrok.io
  %(prog)s -H abc123.share.zrok.io --vscode
  %(prog)s -H abc123.share.zrok.io -k  # Use SSH key

  {Colors.CYAN}# PRIVATE tunnel (via zrok access){Colors.END}
  %(prog)s --private abc123xyz
  %(prog)s --private abc123xyz --vscode
  %(prog)s --private abc123xyz --port 9191

  {Colors.CYAN}# Other commands{Colors.END}
  %(prog)s --setup-ssh hostname.share.zrok.io
  %(prog)s --stop  # Stop zrok access process
        """
    )
    
    # Public tunnel options
    parser.add_argument('-H', '--hostname', help='Public tunnel hostname (e.g., abc123.share.zrok.io)')
    
    # Private tunnel options
    parser.add_argument('--private', metavar='TOKEN', help='Private tunnel share token')
    parser.add_argument('--port', type=int, default=9191, help='Local port for private tunnel (default: 9191)')
    
    # Common options
    parser.add_argument('-p', '--password', default='kaggle123', help='SSH password (default: kaggle123)')
    parser.add_argument('-k', '--key', action='store_true', help='Use SSH key authentication')
    parser.add_argument('--vscode', action='store_true', help='Open in VS Code')
    parser.add_argument('--setup-ssh', metavar='HOSTNAME', help='Update SSH config only')
    parser.add_argument('--stop', action='store_true', help='Stop zrok access process')
    parser.add_argument('--list', action='store_true', help='List saved configuration')
    
    args = parser.parse_args()
    
    # Handle specific commands
    if args.stop:
        stop_zrok_access()
        return
    
    if args.list:
        config = load_config()
        print(f"\n{Colors.BOLD}Saved Configuration:{Colors.END}")
        print(json.dumps(config, indent=2))
        return
    
    if args.setup_ssh:
        update_ssh_config(args.setup_ssh)
        return
    
    # Private tunnel mode
    if args.private:
        if not check_dependencies(include_zrok=True):
            sys.exit(1)
        connect_private(
            args.private,
            args.password if not args.key else None,
            args.key,
            args.vscode,
            args.port
        )
        return
    
    # Public tunnel mode
    if args.hostname:
        if not check_dependencies():
            sys.exit(1)
        connect_public(
            args.hostname,
            args.password if not args.key else None,
            args.key,
            args.vscode
        )
        return
    
    # Interactive mode
    while True:
        try:
            interactive_menu()
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            stop_zrok_access()
            break

if __name__ == "__main__":
    main()
