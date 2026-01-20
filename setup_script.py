#!/usr/bin/env python3
"""
Kaggle-side setup script for VS Code + zrok.

- Installs zrok if missing
- Configures and starts SSH server
- Enables zrok environment and starts private share
"""

from __future__ import annotations

import argparse
import logging
import os
import secrets
import string
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional

from utils import Zrok, ZrokError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def generate_random_password(length: int = 16) -> str:
    """Generate a secure random password."""
    if length < 8:
        raise ValueError("Password length must be at least 8")
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def ensure_ssh_installed() -> None:
    """Ensure sshd is available (best-effort)."""
    if shutil_which("sshd"):
        logger.info("SSH server already installed")
        return
    
    logger.info("Installing openssh-server...")
    try:
        _run(["apt-get", "update", "-y"], check=True)
        _run(["apt-get", "install", "-y", "openssh-server"], check=True)
        logger.info("SSH server installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install openssh-server: {e}")
        raise RuntimeError(
            "SSH installation failed. This tool requires openssh-server. "
            "Please install it manually or run in an environment with SSH support."
        )


def shutil_which(cmd: str) -> Optional[str]:
    from shutil import which

    return which(cmd)


def configure_ssh(password: str, authorized_keys_url: str = "") -> None:
    """Configure sshd with password and/or keys."""
    os.makedirs("/var/run/sshd", exist_ok=True)

    # Set root password
    try:
        proc = subprocess.Popen(["chpasswd"], stdin=subprocess.PIPE, text=True)
        proc.communicate(f"root:{password}\n")
        if proc.returncode != 0:
            raise RuntimeError("Failed to set password")
        logger.info("Root password configured")
    except Exception as e:
        logger.error(f"Password configuration failed: {e}")
        raise

    # Update sshd_config
    config_path = Path("/etc/ssh/sshd_config")
    config = config_path.read_text() if config_path.exists() else ""

    def set_option(text: str, key: str, value: str) -> str:
        lines = text.splitlines()
        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}") or line.strip().startswith(f"#{key}"):
                new_lines.append(f"{key} {value}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"{key} {value}")
        return "\n".join(new_lines) + "\n"

    config = set_option(config, "PermitRootLogin", "yes")
    config = set_option(config, "PasswordAuthentication", "yes")
    config = set_option(config, "PubkeyAuthentication", "yes")
    config_path.write_text(config)

    # Authorized keys
    if authorized_keys_url:
        try:
            ssh_dir = Path("/root/.ssh")
            ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            key_data = urllib.request.urlopen(authorized_keys_url, timeout=15).read().decode()
            auth_keys = ssh_dir / "authorized_keys"
            auth_keys.write_text(key_data)
            auth_keys.chmod(0o600)
            logger.info("Authorized keys installed")
        except Exception as e:
            logger.error(f"Failed to install authorized keys: {e}")
            raise

    # Start/restart sshd
    try:
        if shutil_which("service"):
            _run(["service", "ssh", "restart"], check=True)
            logger.info("SSH service restarted")
        elif shutil_which("sshd"):
            _run(["/usr/sbin/sshd"], check=True)
            logger.info("SSH daemon started")
        else:
            raise RuntimeError("No SSH service manager found")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start SSH service: {e}")
        raise


def setup_zrok(token: str, env_name: str) -> None:
    """Enable zrok and share SSH tunnel."""
    zrok = Zrok(token, env_name)
    zrok.disable()
    zrok.enable()
    zrok.share()


def main() -> int:
    parser = argparse.ArgumentParser(description="Kaggle zrok SSH setup")
    parser.add_argument("--token", required=True, help="Zrok API token")
    parser.add_argument("--password", default="0", help="SSH password (0 = random)")
    parser.add_argument("--authorized_keys_url", default="", help="URL to authorized_keys file")
    parser.add_argument("--env-name", default="kaggle_server", help="Zrok environment name")
    parser.add_argument("--hide-password", action="store_true", help="Don't display password in output")
    args = parser.parse_args()

    if not Zrok.is_installed():
        logger.info("zrok not found, installing...")
        Zrok.install()

    password = args.password
    if password == "0" or password.strip() == "":
        password = generate_random_password()

    try:
        ensure_ssh_installed()
        configure_ssh(password, args.authorized_keys_url)
    except Exception as e:
        logger.error(f"SSH setup failed: {e}")
        return 1

    try:
        setup_zrok(args.token, args.env_name)
    except ZrokError as exc:
        logger.error(f"Zrok setup failed: {exc}")
        return 1

    # Success message
    print("\n" + "=" * 60)
    logger.info("Kaggle SSH + zrok is ready")
    if not args.hide_password:
        print(f"SSH password: {password}")
    else:
        print("SSH password: [hidden - use --authorized_keys_url or save it]")
    print(f"Zrok environment: {args.env_name}")
    if args.authorized_keys_url:
        print("Auth keys: enabled")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
