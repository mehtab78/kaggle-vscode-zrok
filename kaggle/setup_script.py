#!/usr/bin/env python3
"""
Kaggle VS Code Remote Setup Script
Run this in a Kaggle notebook to enable remote VS Code access via zrok.
"""

import subprocess
import os
import time
import threading
import urllib.request
import tarfile
import json

# ═══════════════════════════════════════════════════════════════
#                     CONFIGURATION
# ═══════════════════════════════════════════════════════════════

ZROK_TOKEN = "<YOUR_ZROK_TOKEN>"     # Get from https://zrok.io
SSH_PASSWORD = "0"                    # SSH login password
AUTHORIZED_KEYS_URL = ""              # Optional: URL to authorized_keys file

ENV_NAME = "kaggle_server"            # Environment name (must match client)

# ═══════════════════════════════════════════════════════════════
#                     Zrok API Client
# ═══════════════════════════════════════════════════════════════

class Zrok:
    """Abstraction for zrok operations using HTTP API."""
    
    BASE_URL = "https://api-v1.zrok.io/api/v1"
    
    def __init__(self, token: str, name: str):
        if token.startswith('<') and token.endswith('>'):
            raise ValueError("❌ Please provide your actual zrok token!")
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
            print(f"   Cleaned up existing '{self.name}' environment")
    
    def enable(self):
        """Enable zrok with environment name."""
        subprocess.run(["zrok", "enable", self.token, "-d", self.name], check=True)
    
    @staticmethod
    def install():
        """Install zrok from GitHub releases."""
        print("   Downloading zrok...")
        resp = urllib.request.urlopen("https://api.github.com/repos/openziti/zrok/releases/latest")
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
    
    @staticmethod
    def is_installed():
        """Check if zrok is available."""
        try:
            subprocess.run(["zrok", "version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


# ═══════════════════════════════════════════════════════════════
#                     SSH Setup
# ═══════════════════════════════════════════════════════════════

def setup_ssh(password: str, auth_keys_url: str = ""):
    """Configure and start SSH server."""
    # Install openssh
    subprocess.run("apt-get update -qq && apt-get install -y openssh-server > /dev/null 2>&1", 
                   shell=True, check=True)
    
    os.makedirs("/run/sshd", exist_ok=True)
    os.makedirs("/root/.ssh", exist_ok=True)
    os.chmod("/root/.ssh", 0o700)
    
    # Save Kaggle environment variables for SSH sessions
    with open("/kaggle/working/kaggle_env_vars.txt", "w") as f:
        for key, val in os.environ.items():
            if key.startswith(('KAGGLE_', 'CUDA_', 'PATH', 'LD_LIBRARY')):
                f.write(f"{key}={val}\n")
    
    # SSH config
    sshd_config = """Port 22
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
X11Forwarding yes
AllowTcpForwarding yes
ClientAliveInterval 60
ClientAliveCountMax 3
Subsystem sftp /usr/lib/openssh/sftp-server
"""
    with open("/etc/ssh/sshd_config", "w") as f:
        f.write(sshd_config)
    
    # Set password
    subprocess.run(f"echo 'root:{password}' | chpasswd", shell=True, check=True)
    
    # Optional: authorized keys
    if auth_keys_url:
        try:
            urllib.request.urlretrieve(auth_keys_url, "/root/.ssh/authorized_keys")
            os.chmod("/root/.ssh/authorized_keys", 0o600)
            print("   ✓ SSH keys added")
        except Exception as e:
            print(f"   ⚠️ Could not fetch SSH keys: {e}")
    
    # Generate host keys and start
    subprocess.run("ssh-keygen -A", shell=True, capture_output=True)
    subprocess.run("/usr/sbin/sshd", shell=True)


# ═══════════════════════════════════════════════════════════════
#                     Main Setup
# ═══════════════════════════════════════════════════════════════

def setup():
    """Run complete setup."""
    print("=" * 50)
    print("🚀 Kaggle Remote VS Code Setup")
    print("=" * 50)
    
    # 1. Install dependencies
    print("\n[1/4] 📦 Installing dependencies...")
    print("   ✓ openssh-server")
    
    if not Zrok.is_installed():
        Zrok.install()
    else:
        print("   ✓ zrok already installed")
    
    # 2. Setup zrok
    print("\n[2/4] 🌐 Configuring zrok...")
    zrok = Zrok(ZROK_TOKEN, ENV_NAME)
    zrok.disable()
    zrok.enable()
    print("   ✓ zrok enabled")
    
    # 3. Setup SSH
    print("\n[3/4] 🔐 Configuring SSH...")
    setup_ssh(SSH_PASSWORD, AUTHORIZED_KEYS_URL)
    print("   ✓ SSH server running")
    
    # 4. Done
    print("\n[4/4] ✅ Setup complete!")
    print("=" * 50)
    print(f"""
📋 CONNECTION INFO:
   Environment: {ENV_NAME}
   SSH User:    root
   Password:    {SSH_PASSWORD}

🔜 NEXT STEP:
   Run start_tunnel() to start the tunnel.
   Then on your local machine:
   
   python local/connect.py --token YOUR_ZROK_TOKEN
""")
    print("=" * 50)


def start_tunnel():
    """Start zrok tunnel and keep notebook alive."""
    print("🚀 Starting zrok private tunnel...")
    print("=" * 50)
    
    def run_tunnel():
        process = subprocess.Popen(
            ["zrok", "share", "private", "--backend-mode", "tcpTunnel", "localhost:22"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(line, end='')
            if 'token' in line.lower():
                import re
                match = re.search(r'\b([a-z0-9]{12,})\b', line)
                if match:
                    print("\n" + "=" * 50)
                    print("🔒 TUNNEL ACTIVE!")
                    print("=" * 50)
                    print(f"\nShare Token: {match.group(1)}")
                    print(f"Password: {SSH_PASSWORD}")
                    print("\nLocal machine: python local/connect.py --token YOUR_ZROK_TOKEN")
                    print("=" * 50)
    
    thread = threading.Thread(target=run_tunnel, daemon=True)
    thread.start()
    
    print("⏰ Keeping notebook alive... (Press Stop to end)\n")
    start = time.time()
    try:
        while True:
            time.sleep(300)
            elapsed = int(time.time() - start)
            h, m = divmod(elapsed // 60, 60)
            print(f"[{time.strftime('%H:%M:%S')}] Running: {h:02d}h {m:02d}m")
    except KeyboardInterrupt:
        print("\n🛑 Tunnel stopped.")


# ═══════════════════════════════════════════════════════════════
#                     Run
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    setup()
    start_tunnel()
