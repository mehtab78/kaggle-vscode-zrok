#!/usr/bin/env python3
"""
Shared Zrok API client for Kaggle VS Code Remote.
Used by both server (zrok_server.py) and client (local/connect.py).
"""

import json
import os
import subprocess
import tarfile
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, List, Any

__all__ = ['Zrok', 'ZrokError']


class ZrokError(Exception):
    """Base exception for Zrok operations."""
    pass


class Zrok:
    """
    Zrok API client for managing environments and tunnels.
    
    Features:
    - HTTP API integration for environment management
    - Automatic retry on transient failures
    - Clean environment lifecycle management
    """
    
    BASE_URL = "https://api-v1.zrok.io/api/v1"
    TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    def __init__(self, token: str, name: str = "kaggle"):
        """
        Initialize Zrok client.
        
        Args:
            token: Zrok API token from https://zrok.io
            name: Environment name for identification
        
        Raises:
            ValueError: If token appears to be a placeholder
        """
        if not token or (token.startswith('<') and token.endswith('>')):
            raise ValueError("Please provide your actual zrok token from https://zrok.io")
        self.token = token
        self.name = name
    
    def _request(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """
        Make HTTP request to Zrok API with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., "/overview")
            method: HTTP method
            data: JSON data for POST requests
        
        Returns:
            Parsed JSON response
        
        Raises:
            ZrokError: On API or network failure after retries
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"x-token": self.token}
        
        if data:
            headers["Content-Type"] = "application/zrok.v1+json"
        
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                req = urllib.request.Request(
                    url=url,
                    headers=headers,
                    data=json.dumps(data).encode() if data else None,
                    method=method
                )
                with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                    return json.loads(resp.read().decode()) if resp.read else {}
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    raise ZrokError("Invalid token. Check your zrok API token.")
                elif e.code == 404:
                    return {}
                last_error = e
            except urllib.error.URLError as e:
                last_error = e
            except json.JSONDecodeError:
                return {}
            
            if attempt < self.MAX_RETRIES - 1:
                time.sleep(self.RETRY_DELAY * (attempt + 1))
        
        raise ZrokError(f"API request failed after {self.MAX_RETRIES} attempts: {last_error}")
    
    def get_environments(self) -> List[Dict[str, Any]]:
        """Get all zrok environments for this account."""
        try:
            data = self._request("/overview")
            return data.get('environments', [])
        except ZrokError:
            return []
    
    def find_env(self, name: str) -> Optional[Dict[str, Any]]:
        """Find environment by description/name (case-insensitive)."""
        for item in self.get_environments():
            env_desc = item.get("environment", {}).get("description", "")
            if env_desc.lower() == name.lower():
                return item
        return None
    
    def find_share_token(self, server_name: str = "kaggle_server", port: int = 22) -> Optional[str]:
        """
        Find the SSH tunnel share token from a server environment.
        
        Args:
            server_name: Name of the server environment
            port: Backend port to match (default: 22 for SSH)
        
        Returns:
            Share token string or None if not found
        """
        env = self.find_env(server_name)
        if not env:
            return None
        
        for share in env.get("shares", []):
            backend_mode = share.get("backendMode", "")
            backend_endpoint = share.get("backendProxyEndpoint", "")
            
            if backend_mode == "tcpTunnel" and backend_endpoint == f"localhost:{port}":
                return share.get("shareToken")
        return None
    
    def delete_env(self, zid: str) -> bool:
        """Delete environment by zId."""
        try:
            self._request("/disable", method="POST", data={"identity": zid})
            return True
        except ZrokError:
            return False
    
    def disable(self, cleanup_remote: bool = True) -> None:
        """
        Disable zrok locally and optionally clean up remote environment.
        
        Args:
            cleanup_remote: Also delete the remote environment via API
        """
        # Local disable
        subprocess.run(["zrok", "disable"], capture_output=True)
        
        # Remote cleanup
        if cleanup_remote:
            env = self.find_env(self.name)
            if env:
                zid = env.get('environment', {}).get('zId')
                if zid and self.delete_env(zid):
                    print(f"   ✓ Cleaned up '{self.name}' environment")
    
    def enable(self) -> None:
        """Enable zrok with the configured environment name."""
        result = subprocess.run(
            ["zrok", "enable", self.token, "-d", self.name],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            raise ZrokError(f"Failed to enable zrok: {error_msg}")
    
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
        """
        Install zrok from GitHub releases (Linux amd64 only).
        
        Raises:
            ZrokError: If installation fails
        """
        print("   Downloading zrok...")
        try:
            with urllib.request.urlopen(
                "https://api.github.com/repos/openziti/zrok/releases/latest",
                timeout=30
            ) as resp:
                data = json.loads(resp.read())
            
            url = next(
                (a["browser_download_url"] for a in data.get("assets", [])
                 if "linux_amd64.tar.gz" in a.get("browser_download_url", "")),
                None
            )
            if not url:
                raise ZrokError("Could not find zrok download URL for linux_amd64")
            
            urllib.request.urlretrieve(url, "/tmp/zrok.tar.gz")
            with tarfile.open("/tmp/zrok.tar.gz", "r:gz") as tar:
                tar.extractall("/usr/local/bin/")
            os.remove("/tmp/zrok.tar.gz")
            
            # Verify installation
            result = subprocess.run(["zrok", "version"], capture_output=True, text=True)
            if result.returncode != 0:
                raise ZrokError("zrok installed but failed to run")
            
            print("   ✓ zrok installed")
        except Exception as e:
            raise ZrokError(f"Installation failed: {e}")
