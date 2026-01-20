#!/usr/bin/env python3
"""
Zrok utility class for Kaggle VS Code Remote Setup.
"""

import os
import json
import logging
import subprocess
import tarfile
import urllib.request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ZrokError(Exception):
    """Custom exception for Zrok-related errors."""
    pass


class Zrok:
    """Zrok API client for managing environments and tunnels."""
    
    BASE_URL = "https://api-v1.zrok.io/api/v1"
    
    def __init__(self, token: str, name: str = "kaggle_server"):
        if not token or (token.startswith('<') and token.endswith('>')):
            raise ValueError("Please provide your actual zrok token!")
        self.token = token
        self.name = name
    
    def _request(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Make HTTP request to Zrok API."""
        headers = {"x-token": self.token}
        if data:
            headers["Content-Type"] = "application/zrok.v1+json"
        req = urllib.request.Request(
            f"{self.BASE_URL}{endpoint}",
            headers=headers,
            data=json.dumps(data).encode() if data else None,
            method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                return json.loads(body.decode()) if body else {}
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise ZrokError("Invalid or expired token. Get a new one from https://zrok.io")
            raise ZrokError(f"API error: {e.code}")
    
    def get_environments(self) -> list:
        """Get all environments for this account."""
        try:
            return self._request("/overview").get('environments', [])
        except Exception:
            return []
    
    def find_env(self, name: str) -> dict:
        """Find environment by name."""
        for item in self.get_environments():
            if item.get("environment", {}).get("description", "").lower() == name.lower():
                return item
        return None
    
    def find_share_token(self, env_name: str = None, backend_port: int = 22) -> str:
        """Find share token for a specific environment and port."""
        env = self.find_env(env_name or self.name)
        if not env:
            return None
        for share in env.get('shares', []):
            backend = share.get('backendProxyEndpoint', '')
            if f":{backend_port}" in backend or backend == f"localhost:{backend_port}":
                return share.get('token') or share.get('shareToken')
        return None
    
    def delete_env(self, zid: str) -> bool:
        """Delete environment by zId."""
        try:
            self._request("/disable", "POST", {"identity": zid})
            return True
        except Exception:
            return False
    
    def disable(self) -> None:
        """Disable zrok locally and clean up remote environment."""
        subprocess.run(["zrok", "disable"], capture_output=True)
        env = self.find_env(self.name)
        if env:
            zid = env.get('environment', {}).get('zId')
            if zid and self.delete_env(zid):
                logger.info(f"Cleaned up '{self.name}' environment")
    
    def enable(self) -> None:
        """Enable zrok with the configured environment name."""
        # Check if already enabled
        status = subprocess.run(["zrok", "status"], capture_output=True, text=True)
        if "Account Token" in status.stdout and "<<SET>>" in status.stdout:
            logger.info("zrok already enabled locally")
            return
        
        result = subprocess.run(
            ["zrok", "enable", self.token, "-d", self.name],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            if "already enabled" in error_msg.lower():
                logger.info("zrok already enabled")
                return
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                raise ZrokError(
                    "Token expired or invalid!\n"
                    "   → Go to https://zrok.io → Account → Generate new invite token\n"
                    "   → The invite token is ONE-TIME USE only"
                )
            if not error_msg:
                error_msg = "Unknown error - check your token at https://zrok.io"
            raise ZrokError(f"Failed to enable zrok: {error_msg}")
    
    def share(self) -> None:
        """Start private tunnel sharing SSH port."""
        logger.info("Starting zrok tunnel...")
        subprocess.Popen(
            ["zrok", "share", "private", "--backend-mode", "tcpTunnel", "localhost:22"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    @staticmethod
    def is_installed() -> bool:
        """Check if zrok CLI is available."""
        try:
            subprocess.run(["zrok", "version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    @staticmethod
    def install() -> None:
        """Install zrok from GitHub releases."""
        logger.info("Downloading zrok...")
        with urllib.request.urlopen(
            "https://api.github.com/repos/openziti/zrok/releases/latest"
        ) as resp:
            data = json.loads(resp.read())
        url = next(
            (a["browser_download_url"] for a in data["assets"]
             if "linux_amd64.tar.gz" in a["browser_download_url"]),
            None
        )
        if not url:
            raise RuntimeError("Could not find zrok download URL")
        urllib.request.urlretrieve(url, "/tmp/zrok.tar.gz")
        with tarfile.open("/tmp/zrok.tar.gz", "r:gz") as tar:
            tar.extractall("/usr/local/bin/")
        os.remove("/tmp/zrok.tar.gz")
        subprocess.run(["zrok", "version"], check=True)
        logger.info("zrok installed successfully")
