#!/usr/bin/env python3
"""Fixed version of Zrok class with proper error handling."""

import urllib.request
import os
import sys
import tarfile
import json
import subprocess
import platform

class Zrok:
    def __init__(self, token: str, name: str = None):
        """Initialize Zrok instance with API token and optional environment name.
        
        Args:
            token (str): Zrok API token for authentication
            name (str, optional): Name/description for the zrok environment. Defaults to None.
        """
        if token.startswith('<') and token.endswith('>'):
            raise ValueError("Please provide an actual your zrok token")
        
        self.token = token
        self.name = name
        self.base_url = "https://api-v1.zrok.io/api/v1"

    def get_env(self):
        """Get overview of all zrok environments using HTTP API.

        This method uses HTTP API to retrieve environments even when zrok enable command fails.
        
        Returns:
            list: List of environments
            None: If the API call fails or no environments exist
        """
        req = urllib.request.Request(
            url=f"{self.base_url}/overview",
            headers={"x-token": self.token},
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                status = response.getcode()
                data = response.read().decode('utf-8')
                data = json.loads(data) 

                if status != 200:
                    print(f"Error: {status}")
                    return None
                
                return data.get('environments', [])
        
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            if e.code == 401:
                print("Invalid or expired token. Get a new one from https://zrok.io")
            return None
        except urllib.error.URLError as e:
            print(f"Network Error: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def find_env(self, name: str):
        """Find a specific environment by its name.
        
        Args:
            name (str): Name/description of the environment to find (case-insensitive)
        
        Returns:
            dict: Environment information if found
            None: If no environment matches the given name
        """
        overview = self.get_env()
        
        # BUG FIX: Handle None and empty list
        if overview is None or not overview:
            return None

        for item in overview:
            # BUG FIX: Validate item structure before accessing
            if not item or "environment" not in item:
                continue
                
            env = item["environment"]
            if env.get("description", "").lower() == name.lower():
                return item
            
        return None

    def delete_environment(self, zId: str):
        """Delete a zrok environment by its ID.
        
        Args:
            zId (str): The environment ID to delete
        
        Returns:
            bool: True if the environment was successfully deleted, False otherwise
        """
        headers = {
            "x-token": self.token,
            "Accept": "*/*",
            "Content-Type": "application/zrok.v1+json"
        }
        payload = {
            "identity": zId
        }
        
        data_bytes = json.dumps(payload).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                f"{self.base_url}/disable", 
                headers=headers, 
                data=data_bytes, 
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                status = response.getcode()

                if status != 200:
                    print(f"Failed to delete environment: HTTP {status}")
                    return False

                return True
        
        except urllib.error.HTTPError as e:
            print(f"HTTP Error deleting environment: {e.code}")
            return False
        except urllib.error.URLError as e:
            print(f"Network Error deleting environment: {e.reason}")
            return False
        except Exception as e:
            print(f"Error deleting environment: {e}")
            return False

    def enable(self, name: str = None):
        """Enable zrok with the specified environment name.
        
        This method runs the 'zrok enable' command with the provided token and
        environment name. It will create a new environment if one doesn't exist.
        
        Args:
            name (str, optional): Name/description for the zrok environment.
                                 If not provided, uses the name from initialization.
            
        Raises:
            RuntimeError: If enable command fails
        """
        env_name = name if name is not None else self.name
        if env_name is None:
            raise ValueError("Environment name must be provided either during initialization or when calling enable()")
        
        try:
            result = subprocess.run(
                ["zrok", "enable", self.token, "-d", env_name], 
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            # BUG FIX: Provide helpful error message
            error_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
            if "already enabled" in error_msg.lower():
                print("zrok already enabled")
                return
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                raise RuntimeError(
                    "Token expired or invalid!\n"
                    "Get a new token from https://zrok.io"
                )
            raise RuntimeError(f"Failed to enable zrok: {error_msg}")
        except FileNotFoundError:
            raise RuntimeError("zrok not found. Install it first with Zrok.install()")

    def disable(self, name: str = None):
        """Disable zrok.
        
        This function executes the zrok disable command to delete the environment stored in the local file ~/.zrok/environment.json,
        and additionally removes any environments that could not be deleted through HTTP communication.
        
        Args:
            name (str, optional): Name/description for the zrok environment.
                                If not provided, uses the name from initialization.
        """
        env_name = name if name is not None else self.name

        # Delete the ~/.zrok/environment.json file
        try:
            subprocess.run(["zrok", "disable"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("zrok already disabled")
        except FileNotFoundError:
            print("zrok not found")

        # Delete environment via HTTP communication even if zrok is not enabled
        # BUG FIX: Check if env_name is provided before trying to find it
        if env_name:
            env = self.find_env(env_name)
            if env is not None:
                zid = env.get('environment', {}).get('zId')
                if zid:
                    self.delete_environment(zid)

    @staticmethod
    def install():
        """Install the latest version of zrok.
        
        This method:
        1. Downloads the latest zrok release from GitHub
        2. Extracts the binary to /usr/local/bin/
        3. Verifies the installation
        """
        # Check if running on Windows
        if platform.system() != 'Linux':
            raise Exception("This script only works on Linux. For other operating systems, "
                          "please install zrok manually following the instructions at https://docs.zrok.io/docs/guides/install/")

        print("Downloading latest zrok release")
        
        try:
            # Get latest release info
            response = urllib.request.urlopen(
                "https://api.github.com/repos/openziti/zrok/releases/latest",
                timeout=30
            )
            data = json.loads(response.read())
            
            # Find linux_amd64 tar.gz download URL
            download_url = None
            for asset in data["assets"]:
                if "linux_amd64.tar.gz" in asset["browser_download_url"]:
                    download_url = asset["browser_download_url"]
                    break
            
            if not download_url:
                raise FileNotFoundError("Could not find zrok download URL for linux_amd64")
            
            # Download zrok
            print(f"Downloading from {download_url}")
            urllib.request.urlretrieve(download_url, "zrok.tar.gz")
            
            print("Extracting Zrok")
            with tarfile.open("zrok.tar.gz", "r:gz") as tar:
                tar.extractall("/usr/local/bin/")
            os.remove("zrok.tar.gz")

            # Check if zrok is installed correctly
            if not Zrok.is_installed():
                raise RuntimeError("Failed to verify zrok installation")
            
            print("Successfully installed zrok")
        
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to download zrok: {e.reason}")
        except Exception as e:
            # Clean up on failure
            if os.path.exists("zrok.tar.gz"):
                os.remove("zrok.tar.gz")
            raise RuntimeError(f"Installation failed: {e}")

    @staticmethod
    def is_installed():
        """Check if zrok is installed and accessible.
        
        Returns:
            bool: True if zrok is installed and can be executed, False otherwise
        """
        try:
            subprocess.run(
                ["zrok", "version"], 
                check=True, 
                capture_output=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def is_enabled() -> bool:
        """Check if zrok is enabled.
        
        Returns:
            bool: True if zrok is enabled (Account Token and Ziti Identity are set), False otherwise
        """
        try:
            result = subprocess.run(
                ["zrok", "status"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            # Check if both Account Token and Ziti Identity are set
            return "Account Token  <<SET>>" in result.stdout and "Ziti Identity  <<SET>>" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
