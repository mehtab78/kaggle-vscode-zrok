#!/usr/bin/env python3
"""
Local machine client for connecting to Kaggle via zrok tunnel.
Works on Windows, Linux, and macOS.
"""

import os
import subprocess
import time
import argparse
import platform
from pathlib import Path
from utils import Zrok


def get_ssh_config_path():
    """Get the SSH config file path for the current platform."""
    if platform.system() == "Windows":
        return Path.home() / ".ssh" / "config"
    else:
        return Path(os.path.expanduser("~/.ssh/config"))


def update_ssh_config(name, port=9191):
    """Update SSH config for the tunnel connection."""
    config_path = get_ssh_config_path()
    config_path.parent.mkdir(mode=0o700, exist_ok=True)
    
    entry = f"""
Host {name}
    HostName 127.0.0.1
    User root
    Port {port}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
"""
    
    # Read existing config
    existing = config_path.read_text() if config_path.exists() else ""
    
    # Check if entry already exists
    if f"Host {name}" not in existing:
        config_path.write_text(existing.rstrip() + "\n" + entry)
        print(f"✓ SSH config updated for '{name}'")
    else:
        print(f"✓ SSH config already contains '{name}' entry")
    
    # Set permissions (on Unix)
    if platform.system() != "Windows":
        config_path.chmod(0o600)


def start_zrok_access(share_token, port=9191):
    """Start zrok access process."""
    print(f"Starting zrok tunnel on port {port}...")
    
    # Use platform-appropriate method to start process
    if platform.system() == "Windows":
        # On Windows, use cmd /k to keep window open
        process = subprocess.Popen(
            ["cmd", "/k", f"zrok access private --bind 127.0.0.1:{port} {share_token}"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # On Unix, just start in background
        process = subprocess.Popen(
            ["zrok", "access", "private", "--bind", f"127.0.0.1:{port}", share_token],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    # Wait for tunnel to establish
    time.sleep(5)
    return process


def launch_vscode(name, workspace):
    """Launch VS Code with remote SSH."""
    try:
        subprocess.Popen(
            ["code", "--remote", f"ssh-remote+{name}", workspace],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ VS Code launched")
    except FileNotFoundError:
        print("⚠ VS Code 'code' command not found")
        print(f"  Connect manually: code --remote ssh-remote+{name} {workspace}")


def main(args):
    """Main connection logic."""
    zrok = Zrok(args.token, args.name)
    
    # Check zrok installation
    if not Zrok.is_installed():
        print("Installing zrok...")
        Zrok.install()

    # Setup local zrok
    print("Setting up zrok environment...")
    zrok.disable()
    zrok.enable()

    # Find server tunnel
    print(f"Looking for '{args.server_name}' environment...")
    env = zrok.find_env(args.server_name)
    if env is None:
        print(f"❌ {args.server_name} environment not found. Is the notebook running?")
        return 1

    # Find share token
    share_token = None
    for share in env.get("shares", []):
        if (share.get("backendMode") == "tcpTunnel" and
            share.get("backendProxyEndpoint") == f"localhost:{args.port}"):
            share_token = share.get("shareToken")
            break

    if not share_token:
        print(f"❌ SSH tunnel not found in {args.server_name} environment")
        return 1

    print(f"✓ Found tunnel: {share_token[:16]}...")

    # Start zrok access
    start_zrok_access(share_token, args.local_port)

    # Update SSH config
    update_ssh_config(args.name, args.local_port)

    # Launch VS Code
    if not args.no_vscode:
        print("Launching VS Code...")
        launch_vscode(args.name, args.workspace)
        time.sleep(2)

    # Print connection info
    print(f"""
{'='*60}
🎉 CONNECTED!
{'='*60}

SSH:     ssh {args.name}
         ssh root@localhost -p {args.local_port}

VS Code: code --remote ssh-remote+{args.name} {args.workspace}

{'='*60}
""")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Connect to Kaggle via zrok tunnel')
    parser.add_argument('--token', type=str, help='zrok API token')
    parser.add_argument('--name', type=str, default='kaggle_client', 
                        help='Local environment name (default: kaggle_client)')
    parser.add_argument('--server-name', type=str, default='kaggle_server', 
                        help='Server environment name (default: kaggle_server)')
    parser.add_argument('--port', type=int, default=22, 
                        help='Remote SSH port (default: 22)')
    parser.add_argument('--local-port', type=int, default=9191, 
                        help='Local port for tunnel (default: 9191)')
    parser.add_argument('--no-vscode', action='store_true', 
                        help='Skip VS Code launch')
    parser.add_argument('--workspace', type=str, default='/kaggle/working', 
                        help='Remote workspace path')
    args = parser.parse_args()

    if not args.token:
        args.token = input("Enter your zrok API token: ")
    
    try:
        exit(main(args))
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
        exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")
        exit(1)
