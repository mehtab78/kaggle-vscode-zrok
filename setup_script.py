#!/usr/bin/env python3
"""
Kaggle VS Code Remote Setup - Server Script

Usage:
    python3 setup_script.py --token "YOUR_ZROK_TOKEN" --password "0"
    python3 setup_script.py --token "TOKEN" --authorized_keys_url "URL"
"""

import subprocess
import argparse
import string
import random
from utils import Zrok, ZrokError


def generate_random_password(length=16):
    """Generate a random password."""
    characters = string.ascii_letters + string.digits + "!@#$%^*()-_=+{}[]<>.,?"
    return ''.join(random.choices(characters, k=length))


def main(args):
    print("=" * 55)
    print("🚀 Kaggle Remote VS Code Setup")
    print("=" * 55)
    
    # Step 1: Install zrok if needed
    print("\n[1/4] 📦 Installing dependencies...")
    if not Zrok.is_installed():
        Zrok.install()
    else:
        print("   ✓ zrok already installed")
    
    # Step 2: Configure zrok
    print("\n[2/4] 🌐 Configuring zrok...")
    zrok = Zrok(args.token, args.name)
    zrok.disable()
    zrok.enable()
    print("   ✓ zrok enabled")
    
    # Step 3: Setup SSH server
    print("\n[3/4] 🔐 Configuring SSH...")
    if args.authorized_keys_url:
        subprocess.run(["bash", "setup_ssh.sh", args.authorized_keys_url], check=True)
    else:
        subprocess.run(["bash", "setup_ssh.sh"], check=True)
    
    # Set password
    password = args.password if args.password else generate_random_password()
    subprocess.run(f"echo 'root:{password}' | sudo chpasswd", shell=True, check=True)
    print(f"   ✓ SSH server running (password: {password})")
    
    # Step 4: Start tunnel
    print("\n[4/4] 🚀 Starting tunnel...")
    zrok.share()
    
    # Get share token for connection info
    import time
    time.sleep(3)  # Wait for tunnel to establish
    share_token = zrok.find_share_token()
    
    print("\n" + "=" * 55)
    print("🔒 TUNNEL ACTIVE!")
    print("=" * 55)
    if share_token:
        print(f"""
Share Token: {share_token}
Password:    {password}

On your local machine:
  python local/connect.py --token YOUR_ZROK_TOKEN

Or manually:
  1. zrok access private {share_token}
  2. ssh root@localhost -p 9191
""")
    else:
        print(f"""
Password: {password}

Check 'zrok status' for share token, then on local machine:
  python local/connect.py --token YOUR_ZROK_TOKEN
""")
    print("=" * 55)
    
    # Keep alive
    print("\n⏰ Keeping notebook alive... (Press Ctrl+C to stop)")
    try:
        while True:
            time.sleep(300)
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Kaggle SSH connection setup')
    parser.add_argument('--token', '-t', type=str, help='zrok invite token')
    parser.add_argument('--name', type=str, default='kaggle_server', 
                        help='Environment name (default: kaggle_server)')
    parser.add_argument('--authorized_keys_url', '-k', type=str, 
                        help='URL to authorized_keys file')
    parser.add_argument('--password', '-p', type=str, 
                        help='Password for root (default: random)')
    args = parser.parse_args()

    if not args.token:
        args.token = input("Enter your zrok invite token: ")
    
    try:
        main(args)
    except (ZrokError, ValueError) as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
