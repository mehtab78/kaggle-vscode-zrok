#!/usr/bin/env python3
"""
Kaggle VS Code Connection Helper
Connects to Kaggle via zrok private tunnel automatically.
"""

import subprocess
import sys
import os
import json
import argparse
import time
import signal
import urllib.request
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#                     Zrok API Client
# ═══════════════════════════════════════════════════════════════

class Zrok:
    """Abstraction for zrok operations using HTTP API."""
    
    BASE_URL = "https://api-v1.zrok.io/api/v1"
    
    def __init__(self, token: str, name: str = "kaggle_client"):
        self.token = token
        self.name = name
    
    def get_environments(self):
        """Get all zrok environments via HTTP API."""
        req = urllib.request.Request(
            url=f"{self.BASE_URL}/overview",
            headers={"x-token": self.token}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        return data.get('environments', [])
    
    def find_env(self, name: str):
        """Find environment by name."""
        for item in self.get_environments():
            if item["environment"]["description"].lower() == name.lower():
                return item
        return None
    
    def find_share_token(self, server_name: str = "kaggle_server", port: int = 22):
        """Find SSH tunnel share token from server environment."""
        env = self.find_env(server_name)
        if not env:
            return None
        
        for share in env.get("shares", []):
            if (share.get("backendMode") == "tcpTunnel" and 
                share.get("backendProxyEndpoint") == f"localhost:{port}"):
                return share.get("shareToken")
        return None
    
    def delete_env(self, zid: str):
        """Delete environment by zId."""
        req = urllib.request.Request(
            url=f"{self.BASE_URL}/disable",
            headers={"x-token": self.token, "Content-Type": "application/zrok.v1+json"},
            data=json.dumps({"identity": zid}).encode(),
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            return resp.getcode() == 200
    
    def disable(self):
        """Disable zrok locally and clean up remote environment."""
        subprocess.run(["zrok", "disable"], capture_output=True)
        env = self.find_env(self.name)
        if env:
            self.delete_env(env['environment']['zId'])
    
    def enable(self):
        """Enable zrok with environment name."""
        subprocess.run(["zrok", "enable", self.token, "-d", self.name], check=True)
    
    @staticmethod
    def is_installed():
        """Check if zrok is available."""
        try:
            subprocess.run(["zrok", "version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


# ═══════════════════════════════════════════════════════════════
#                     Connection Helpers
# ═══════════════════════════════════════════════════════════════

CONFIG_FILE = Path.home() / ".kaggle_vscode_config.json"
SSH_CONFIG = Path.home() / ".ssh" / "config"
ZROK_PID_FILE = Path.home() / ".kaggle_zrok_access.pid"

def load_config():
    """Load saved configuration."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(config):
    """Save configuration."""
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    CONFIG_FILE.chmod(0o600)

def update_ssh_config(host_name: str = "kaggle", port: int = 9191):
    """Update SSH config for localhost connection."""
    SSH_CONFIG.parent.mkdir(mode=0o700, exist_ok=True)
    
    entry = f"""
Host {host_name}
    HostName 127.0.0.1
    User root
    Port {port}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
"""
    
    existing = SSH_CONFIG.read_text() if SSH_CONFIG.exists() else ""
    
    # Remove existing entry
    if f"Host {host_name}" in existing:
        lines = existing.split('\n')
        new_lines = []
        skip = False
        for line in lines:
            if line.strip() == f"Host {host_name}":
                skip = True
                continue
            if skip and line.strip().startswith('Host '):
                skip = False
            if not skip:
                new_lines.append(line)
        existing = '\n'.join(new_lines)
    
    SSH_CONFIG.write_text(existing.rstrip() + entry)
    SSH_CONFIG.chmod(0o600)
    print(f"✓ SSH config updated for '{host_name}'")

def stop_zrok_access():
    """Stop any running zrok access process."""
    if ZROK_PID_FILE.exists():
        try:
            pid = int(ZROK_PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"✓ Stopped zrok access (PID: {pid})")
        except (ProcessLookupError, ValueError):
            pass
        ZROK_PID_FILE.unlink(missing_ok=True)
    subprocess.run(['pkill', '-f', 'zrok access'], capture_output=True)

def start_zrok_access(share_token: str, port: int = 9191):
    """Start zrok access private."""
    stop_zrok_access()
    
    process = subprocess.Popen(
        ['zrok', 'access', 'private', '--bind', f'127.0.0.1:{port}', share_token],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    ZROK_PID_FILE.write_text(str(process.pid))
    print(f"✓ zrok access started (PID: {process.pid})")
    time.sleep(3)
    return process


# ═══════════════════════════════════════════════════════════════
#                     Main
# ═══════════════════════════════════════════════════════════════

def main(args):
    if not Zrok.is_installed():
        print("❌ zrok not installed. Install from https://docs.zrok.io/docs/guides/install/")
        sys.exit(1)
    
    zrok = Zrok(args.token, args.name)
    
    # Clean up and enable local zrok
    print("🔄 Setting up zrok...")
    zrok.disable()
    zrok.enable()
    print("✓ zrok enabled")
    
    # Find server's share token via API
    print(f"\n🔍 Looking for '{args.server_name}' environment...")
    share_token = zrok.find_share_token(args.server_name)
    
    if not share_token:
        print(f"❌ Could not find SSH tunnel in '{args.server_name}'")
        print("   Make sure the Kaggle notebook is running Cell 2.")
        sys.exit(1)
    
    print(f"✓ Found share token: {share_token}")
    
    # Start zrok access
    print(f"\n🚀 Starting tunnel on port {args.port}...")
    start_zrok_access(share_token, args.port)
    
    # Update SSH config
    update_ssh_config(args.name, args.port)
    
    # Launch VS Code
    if not args.no_vscode:
        print(f"\n💻 Launching VS Code...")
        subprocess.Popen(
            ['code', '--remote', f'ssh-remote+{args.name}', args.workspace],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"✓ VS Code launched")
        time.sleep(3)
    
    print(f"""
{'='*50}
🎉 CONNECTED!
{'='*50}

SSH:     ssh {args.name}
         ssh root@localhost -p {args.port}

VS Code: code --remote ssh-remote+{args.name} {args.workspace}

Press Ctrl+C to disconnect.
{'='*50}
""")
    
    # Keep running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Disconnecting...")
        stop_zrok_access()
        print("Goodbye! 👋")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Connect to Kaggle via zrok')
    parser.add_argument('--token', '-t', type=str, help='Your zrok API token')
    parser.add_argument('--name', default='kaggle_client', help='Local environment name (default: kaggle_client)')
    parser.add_argument('--server-name', default='kaggle_server', help='Server environment name (default: kaggle_server)')
    parser.add_argument('--port', type=int, default=9191, help='Local port (default: 9191)')
    parser.add_argument('--no-vscode', action='store_true', help='Skip VS Code launch')
    parser.add_argument('--workspace', default='/kaggle/working', help='Remote workspace path')
    parser.add_argument('--stop', action='store_true', help='Stop zrok access and exit')
    
    args = parser.parse_args()
    
    if args.stop:
        stop_zrok_access()
        sys.exit(0)
    
    if not args.token:
        # Try loading from config
        config = load_config()
        if 'token' in config:
            args.token = config['token']
        else:
            args.token = input("Enter your zrok API token: ").strip()
            if args.token:
                config['token'] = args.token
                save_config(config)
    
    if not args.token:
        print("❌ Token required")
        sys.exit(1)
    
    try:
        main(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
