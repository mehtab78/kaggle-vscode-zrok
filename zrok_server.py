#!/usr/bin/env python3
"""
Kaggle VS Code Remote Setup - Server Script

Usage:
    python3 zrok_server.py --token "YOUR_ZROK_TOKEN" --password "0"
    python3 zrok_server.py --token "TOKEN" --authorized_keys_url "URL"

Run this on Kaggle to set up SSH server and zrok tunnel.
"""

import os
import subprocess
import urllib.request
import argparse
import threading
import time
import re
import sys

# Import shared Zrok client (or use embedded version if not available)
try:
    from zrok_api import Zrok, ZrokError
except ImportError:
    # Embedded minimal version for standalone use
    import json
    import tarfile
    
    class ZrokError(Exception):
        pass
    
    class Zrok:
        BASE_URL = "https://api-v1.zrok.io/api/v1"
        
        def __init__(self, token: str, name: str = "kaggle_server"):
            if not token or (token.startswith('<') and token.endswith('>')):
                raise ValueError("Please provide your actual zrok token!")
            self.token = token
            self.name = name
        
        def _request(self, endpoint, method="GET", data=None):
            headers = {"x-token": self.token}
            if data:
                headers["Content-Type"] = "application/zrok.v1+json"
            req = urllib.request.Request(
                f"{self.BASE_URL}{endpoint}", headers=headers,
                data=json.dumps(data).encode() if data else None, method=method
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                return json.loads(body.decode()) if body else {}
        
        def get_environments(self):
            try:
                return self._request("/overview").get('environments', [])
            except Exception:
                return []
        
        def find_env(self, name):
            for item in self.get_environments():
                if item.get("environment", {}).get("description", "").lower() == name.lower():
                    return item
            return None
        
        def delete_env(self, zid):
            try:
                self._request("/disable", "POST", {"identity": zid})
                return True
            except Exception:
                return False
        
        def disable(self):
            subprocess.run(["zrok", "disable"], capture_output=True)
            env = self.find_env(self.name)
            if env:
                zid = env.get('environment', {}).get('zId')
                if zid and self.delete_env(zid):
                    print(f"   ✓ Cleaned up '{self.name}' environment")
        
        def enable(self):
            # Check if already enabled
            status = subprocess.run(["zrok", "status"], capture_output=True, text=True)
            if "Account Token" in status.stdout and "<<SET>>" in status.stdout:
                print("   ✓ zrok already enabled locally")
                return
            
            result = subprocess.run(["zrok", "enable", self.token, "-d", self.name], 
                                    capture_output=True, text=True)
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                # Check for common errors
                if "already enabled" in error_msg.lower():
                    print("   ✓ zrok already enabled")
                    return
                if not error_msg:
                    error_msg = "Unknown error - check your token at https://zrok.io"
                raise ZrokError(f"Failed to enable zrok: {error_msg}")
        
        @staticmethod
        def is_installed():
            try:
                subprocess.run(["zrok", "version"], capture_output=True, check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False
        
        @staticmethod
        def install():
            print("   Downloading zrok...")
            with urllib.request.urlopen(
                "https://api.github.com/repos/openziti/zrok/releases/latest"
            ) as resp:
                data = json.loads(resp.read())
            url = next((a["browser_download_url"] for a in data["assets"] 
                        if "linux_amd64.tar.gz" in a["browser_download_url"]), None)
            if not url:
                raise RuntimeError("Could not find zrok download URL")
            urllib.request.urlretrieve(url, "/tmp/zrok.tar.gz")
            with tarfile.open("/tmp/zrok.tar.gz", "r:gz") as tar:
                tar.extractall("/usr/local/bin/")
            os.remove("/tmp/zrok.tar.gz")
            subprocess.run(["zrok", "version"], check=True)
            print("   ✓ zrok installed")


# ═══════════════════════════════════════════════════════════════
#                     SSH Setup
# ═══════════════════════════════════════════════════════════════

SSHD_CONFIG = """Port 22
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
X11Forwarding yes
AllowTcpForwarding yes
ClientAliveInterval 60
ClientAliveCountMax 3
Subsystem sftp /usr/lib/openssh/sftp-server
"""

def setup_ssh(password: str, authorized_keys_url: str = "") -> bool:
    """
    Configure and start SSH server.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Install openssh-server
        subprocess.run(
            "apt-get update -qq && apt-get install -y openssh-server > /dev/null 2>&1",
            shell=True, check=True, timeout=120
        )
        
        # Create directories
        os.makedirs("/run/sshd", exist_ok=True)
        os.makedirs("/root/.ssh", mode=0o700, exist_ok=True)
        
        # Save environment variables for SSH sessions
        env_file = "/kaggle/working/kaggle_env_vars.txt"
        with open(env_file, "w") as f:
            for key, val in os.environ.items():
                if key.startswith(('KAGGLE_', 'CUDA_', 'PATH', 'LD_LIBRARY')):
                    f.write(f"export {key}=\"{val}\"\n")
        
        # Write SSH config
        with open("/etc/ssh/sshd_config", "w") as f:
            f.write(SSHD_CONFIG)
        
        # Set password
        subprocess.run(f"echo 'root:{password}' | chpasswd", shell=True, check=True)
        
        # Add authorized keys if URL provided
        if authorized_keys_url:
            try:
                urllib.request.urlretrieve(authorized_keys_url, "/root/.ssh/authorized_keys")
                os.chmod("/root/.ssh/authorized_keys", 0o600)
                print("   ✓ SSH keys added")
            except Exception as e:
                print(f"   ⚠ Could not fetch SSH keys: {e}")
        
        # Generate host keys and start SSH
        subprocess.run("ssh-keygen -A 2>/dev/null", shell=True)
        subprocess.run("/usr/sbin/sshd", shell=True, check=True)
        
        return True
    except Exception as e:
        print(f"   ✗ SSH setup failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
#                     Tunnel Management
# ═══════════════════════════════════════════════════════════════

class TunnelManager:
    """Manages zrok tunnel lifecycle."""
    
    def __init__(self, password: str):
        self.password = password
        self.process = None
        self.share_token = None
        self._running = False
    
    def start(self) -> None:
        """Start the tunnel in a background thread."""
        self._running = True
        thread = threading.Thread(target=self._run_tunnel, daemon=True)
        thread.start()
    
    def _run_tunnel(self) -> None:
        """Run zrok share and capture output."""
        self.process = subprocess.Popen(
            ["zrok", "share", "private", "--backend-mode", "tcpTunnel", "localhost:22"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in self.process.stdout:
            if not self._running:
                break
            print(line, end='')
            
            # Parse share token from output
            if 'token' in line.lower() and not self.share_token:
                match = re.search(r'\b([a-z0-9]{12,})\b', line)
                if match:
                    self.share_token = match.group(1)
                    self._print_connection_info()
    
    def _print_connection_info(self) -> None:
        """Print connection instructions."""
        print("\n" + "=" * 55)
        print("🔒 TUNNEL ACTIVE!")
        print("=" * 55)
        print(f"""
Share Token: {self.share_token}
Password:    {self.password}

On your local machine:
  python local/connect.py --token YOUR_ZROK_TOKEN

Or manually:
  1. zrok access private {self.share_token}
  2. ssh root@localhost -p 9191
""")
        print("=" * 55)
    
    def stop(self) -> None:
        """Stop the tunnel."""
        self._running = False
        if self.process:
            self.process.terminate()


def keep_alive() -> None:
    """Keep the notebook running with periodic status updates."""
    print("⏰ Keeping notebook alive... (Press Ctrl+C to stop)\n")
    start = time.time()
    
    try:
        while True:
            time.sleep(300)  # 5 minutes
            elapsed = int(time.time() - start)
            hours, mins = divmod(elapsed // 60, 60)
            print(f"[{time.strftime('%H:%M:%S')}] Running: {hours:02d}h {mins:02d}m")
    except KeyboardInterrupt:
        print("\n🛑 Tunnel stopped.")


# ═══════════════════════════════════════════════════════════════
#                     Main Entry Point
# ═══════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Kaggle VS Code Remote Setup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 zrok_server.py --token "abc123" --password "mypass"
  python3 zrok_server.py -t "abc123" -k "https://github.com/user.keys"
        """
    )
    parser.add_argument('--token', '-t', required=True, 
                        help='Your zrok API token (from https://zrok.io)')
    parser.add_argument('--password', '-p', default='0', 
                        help='SSH password (default: 0)')
    parser.add_argument('--authorized_keys_url', '-k', default='', 
                        help='URL to authorized_keys file for key-based auth')
    parser.add_argument('--env-name', default='kaggle_server', 
                        help='Zrok environment name (default: kaggle_server)')
    
    args = parser.parse_args()
    
    print("=" * 55)
    print("🚀 Kaggle Remote VS Code Setup")
    print("=" * 55)
    
    try:
        # Step 1: Install dependencies
        print("\n[1/4] 📦 Installing dependencies...")
        
        if not Zrok.is_installed():
            Zrok.install()
        else:
            print("   ✓ zrok already installed")
        
        # Step 2: Configure zrok
        print("\n[2/4] 🌐 Configuring zrok...")
        zrok = Zrok(args.token, args.env_name)
        zrok.disable()
        zrok.enable()
        print("   ✓ zrok enabled")
        
        # Step 3: Setup SSH
        print("\n[3/4] 🔐 Configuring SSH...")
        if not setup_ssh(args.password, args.authorized_keys_url):
            return 1
        print("   ✓ SSH server running")
        
        # Step 4: Start tunnel
        print("\n[4/4] 🚀 Starting tunnel...")
        tunnel = TunnelManager(args.password)
        tunnel.start()
        
        # Keep alive
        keep_alive()
        tunnel.stop()
        
        return 0
        
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        return 1
    except ZrokError as e:
        print(f"\n❌ Zrok error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
