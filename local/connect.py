#!/usr/bin/env python3
"""
Kaggle VS Code Connection Client

Usage:
    python connect.py --token YOUR_ZROK_TOKEN
    python connect.py --token YOUR_ZROK_TOKEN --no-vscode
    python connect.py --stop

Auto-discovers Kaggle tunnel and connects via VS Code.
"""

import subprocess
import sys
import os
import json
import argparse
import time
import signal
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import Zrok, ZrokError


# ═══════════════════════════════════════════════════════════════
#                     Configuration & SSH
# ═══════════════════════════════════════════════════════════════

CONFIG_FILE = Path.home() / ".kaggle_zrok_config.json"
SSH_CONFIG = Path.home() / ".ssh" / "config"
PID_FILE = Path.home() / ".kaggle_zrok_access.pid"


def load_config() -> dict:
    """Load saved configuration."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save configuration securely."""
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    CONFIG_FILE.chmod(0o600)


def update_ssh_config(host: str = "kaggle", port: int = 9191) -> None:
    """Update SSH config for the tunnel connection."""
    SSH_CONFIG.parent.mkdir(mode=0o700, exist_ok=True)
    
    entry = f"""
Host {host}
    HostName 127.0.0.1
    User root
    Port {port}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
"""
    
    # Read existing config
    existing = SSH_CONFIG.read_text() if SSH_CONFIG.exists() else ""
    
    # Remove existing entry for this host
    if f"Host {host}" in existing:
        lines = existing.split('\n')
        new_lines, skip = [], False
        for line in lines:
            if line.strip() == f"Host {host}":
                skip = True
                continue
            if skip and line.strip().startswith('Host '):
                skip = False
            if not skip:
                new_lines.append(line)
        existing = '\n'.join(new_lines)
    
    SSH_CONFIG.write_text(existing.rstrip() + entry)
    SSH_CONFIG.chmod(0o600)
    print(f"✓ SSH config updated for '{host}'")


# ═══════════════════════════════════════════════════════════════
#                     Tunnel Management
# ═══════════════════════════════════════════════════════════════

def stop_tunnel() -> None:
    """Stop any running zrok access process."""
    stopped = False
    
    # Kill by PID file
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            stopped = True
            print(f"✓ Stopped zrok access (PID: {pid})")
        except (ProcessLookupError, ValueError, OSError):
            pass
        PID_FILE.unlink(missing_ok=True)
    
    # Also kill any stray processes
    subprocess.run(['pkill', '-f', 'zrok access'], capture_output=True)
    
    if not stopped:
        print("✓ No tunnel running")


def start_tunnel(share_token: str, port: int = 9191) -> subprocess.Popen:
    """Start zrok access private tunnel."""
    stop_tunnel()
    
    process = subprocess.Popen(
        ['zrok', 'access', 'private', '--bind', f'127.0.0.1:{port}', share_token],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    PID_FILE.write_text(str(process.pid))
    print(f"✓ Tunnel started (PID: {process.pid})")
    
    # Wait for tunnel to establish
    time.sleep(3)
    return process


def launch_vscode(host: str, workspace: str) -> None:
    """Launch VS Code with remote SSH."""
    try:
        subprocess.Popen(
            ['code', '--remote', f'ssh-remote+{host}', workspace],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ VS Code launched")
    except FileNotFoundError:
        print("⚠ VS Code 'code' command not found")
        print(f"  Connect manually: code --remote ssh-remote+{host} {workspace}")


# ═══════════════════════════════════════════════════════════════
#                     Main Entry Point
# ═══════════════════════════════════════════════════════════════

def connect(args) -> int:
    """Main connection logic."""
    
    # Check zrok installation
    if not Zrok.is_installed():
        print("❌ zrok not installed")
        print("   Install from: https://docs.zrok.io/docs/guides/install/")
        return 1
    
    zrok = Zrok(args.token, args.name)
    
    # Setup local zrok
    print("🔄 Setting up zrok...")
    try:
        zrok.disable()
        zrok.enable()
        print("✓ zrok enabled")
    except ZrokError as e:
        print(f"❌ Failed to enable zrok: {e}")
        return 1
    
    # Auto-discover server tunnel
    print(f"\n🔍 Looking for '{args.server_name}' environment...")
    share_token = zrok.find_share_token(args.server_name)
    
    if not share_token:
        print(f"❌ Could not find SSH tunnel in '{args.server_name}'")
        print("   Make sure the Kaggle notebook is running zrok_server.py")
        return 1
    
    print(f"✓ Found tunnel: {share_token[:16]}...")
    
    # Start local tunnel
    print(f"\n🚀 Starting tunnel on port {args.port}...")
    start_tunnel(share_token, args.port)
    
    # Update SSH config
    update_ssh_config(args.name, args.port)
    
    # Launch VS Code
    if not args.no_vscode:
        print(f"\n💻 Launching VS Code...")
        launch_vscode(args.name, args.workspace)
        time.sleep(2)
    
    # Print connection info
    print(f"""
{'='*55}
🎉 CONNECTED!
{'='*55}

SSH:     ssh {args.name}
         ssh root@localhost -p {args.port}

VS Code: code --remote ssh-remote+{args.name} {args.workspace}

Press Ctrl+C to disconnect.
{'='*55}
""")
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Disconnecting...")
        stop_tunnel()
        print("Goodbye! 👋")
    
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Connect to Kaggle via zrok tunnel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python connect.py --token abc123xyz
  python connect.py -t abc123xyz --no-vscode
  python connect.py --stop
        """
    )
    parser.add_argument('--token', '-t', help='Your zrok API token')
    parser.add_argument('--name', default='kaggle_client', 
                        help='Local environment name (default: kaggle_client)')
    parser.add_argument('--server-name', default='kaggle_server', 
                        help='Server environment name (default: kaggle_server)')
    parser.add_argument('--port', type=int, default=9191, 
                        help='Local port (default: 9191)')
    parser.add_argument('--no-vscode', action='store_true', 
                        help='Skip VS Code launch')
    parser.add_argument('--workspace', default='/kaggle/working', 
                        help='Remote workspace path')
    parser.add_argument('--stop', action='store_true', 
                        help='Stop tunnel and exit')
    
    args = parser.parse_args()
    
    # Handle stop command
    if args.stop:
        stop_tunnel()
        return 0
    
    # Get token from args, config, or prompt
    if not args.token:
        config = load_config()
        if 'token' in config:
            args.token = config['token']
            print(f"Using saved token")
        else:
            args.token = input("Enter your zrok API token: ").strip()
            if args.token:
                save_config({'token': args.token})
                print("Token saved for future use")
    
    if not args.token:
        print("❌ Token required")
        return 1
    
    try:
        return connect(args)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
        stop_tunnel()
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
