#!/usr/bin/env python3
"""
Kaggle-side zrok server setup script.
Run this on Kaggle notebooks to enable SSH access via zrok tunnel.
"""

import subprocess
import argparse
import string
import random
from utils import Zrok


def generate_random_password(length=16):
    """Generate a secure random password."""
    characters = string.ascii_letters + string.digits + "!@#$%^*()-_=+{}[]<>.,?"
    return ''.join(random.choices(characters, k=length))

def main(args):
    """Main setup function for Kaggle SSH + zrok."""
    zrok = Zrok(args.token, args.name)
    
    # Install zrok if not available
    if not Zrok.is_installed():
        print("Installing zrok...")
        Zrok.install()

    # Clean up any previous environment and enable fresh
    print("Setting up zrok environment...")
    zrok.disable()
    zrok.enable()
    
    # Setup SSH server
    print("Setting up SSH server...")
    if args.authorized_keys_url:
        subprocess.run(["bash", "setup_ssh.sh", args.authorized_keys_url], check=True)
    else:
        subprocess.run(["bash", "setup_ssh.sh"], check=True)

    # Configure SSH password
    if args.password is not None:
        password = args.password
    else:
        password = generate_random_password()
    
    print(f"Setting password for root user: {password}")
    subprocess.run(f"echo 'root:{password}' | sudo chpasswd", shell=True, check=True)
    
    # Start zrok share (this is the critical missing piece!)
    print("Starting zrok tunnel...")
    subprocess.Popen(
        ["zrok", "share", "private", "--backend-mode", "tcpTunnel", "localhost:22"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Print success message
    print("\n" + "="*60)
    print("✓ Kaggle SSH + zrok setup complete!")
    print(f"SSH password: {password}")
    print(f"Zrok environment: {args.name}")
    if args.authorized_keys_url:
        print("Authorized keys: enabled")
    print("="*60)
    print("\nRun the client script on your local machine to connect.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Kaggle SSH connection setup with zrok')
    parser.add_argument('--token', type=str, help='zrok API token')
    parser.add_argument('--name', type=str, default='kaggle_server', 
                        help='Environment name to create (default: kaggle_server)')
    parser.add_argument('--authorized_keys_url', type=str, 
                        help='URL to authorized_keys file (optional)')
    parser.add_argument('--password', type=str, 
                        help='Password for root user (if not provided, a random password will be generated)')
    args = parser.parse_args()

    if not args.token:
        args.token = input("Enter your zrok API token: ")
    
    try:
        main(args)
    except Exception as e:
        print(f"Error: {e}")
        input("An error occurred. Press Enter to exit...")