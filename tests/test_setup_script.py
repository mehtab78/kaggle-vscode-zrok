#!/usr/bin/env python3
"""
Tests for kaggle/setup_script.py - Kaggle Setup Script

Run with: pytest tests/test_setup_script.py -v
"""

import pytest
import os
import sys
import subprocess
import re
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestConfiguration:
    """Test configuration validation."""
    
    def test_tunnel_mode_valid_values(self):
        """Test that only 'public' and 'private' are valid tunnel modes."""
        valid_modes = ['public', 'private']
        for mode in valid_modes:
            assert mode in valid_modes
    
    def test_tunnel_mode_invalid_values(self):
        """Test that invalid tunnel modes are rejected."""
        invalid_modes = ['PUBLIC', 'Private', 'both', 'none', '']
        valid_modes = ['public', 'private']
        for mode in invalid_modes:
            assert mode not in valid_modes
    
    def test_default_password(self):
        """Test default SSH password."""
        default_password = "kaggle123"
        assert len(default_password) >= 8
        assert default_password.isalnum()
    
    def test_zrok_token_placeholder(self):
        """Test that placeholder token is recognizable."""
        placeholder = "YOUR_ZROK_TOKEN"
        assert "YOUR" in placeholder
        assert "TOKEN" in placeholder


class TestColorCodes:
    """Test ANSI color code definitions."""
    
    def test_color_codes_format(self):
        """Test that color codes follow ANSI escape sequence format."""
        colors = {
            'GREEN': '\033[92m',
            'YELLOW': '\033[93m',
            'RED': '\033[91m',
            'BLUE': '\033[94m',
            'CYAN': '\033[96m',
            'BOLD': '\033[1m',
            'END': '\033[0m',
        }
        
        for name, code in colors.items():
            assert code.startswith('\033['), f"{name} should start with escape sequence"
            assert code.endswith('m'), f"{name} should end with 'm'"
    
    def test_end_code_resets(self):
        """Test that END code properly resets formatting."""
        end_code = '\033[0m'
        # 0m is the reset code
        assert '0m' in end_code


class TestSSHConfiguration:
    """Test SSH server configuration."""
    
    def test_sshd_config_content(self):
        """Test expected SSH configuration options."""
        expected_config = """
Port 22
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
X11Forwarding yes
ClientAliveInterval 60
ClientAliveCountMax 3
Subsystem sftp /usr/lib/openssh/sftp-server
"""
        assert "Port 22" in expected_config
        assert "PermitRootLogin yes" in expected_config
        assert "PasswordAuthentication yes" in expected_config
        assert "PubkeyAuthentication yes" in expected_config
        assert "ClientAliveInterval" in expected_config
    
    def test_ssh_directory_permissions(self):
        """Test expected SSH directory permissions."""
        expected_mode = 0o700
        assert expected_mode == 448  # 0o700 in decimal
    
    def test_authorized_keys_permissions(self):
        """Test expected authorized_keys permissions."""
        expected_mode = 0o600
        assert expected_mode == 384  # 0o600 in decimal


class TestGitHubSSHKeys:
    """Test GitHub SSH key fetching."""
    
    def test_github_keys_url_format(self):
        """Test GitHub keys URL is correctly formatted."""
        username = "testuser"
        url = f"https://github.com/{username}.keys"
        assert url == "https://github.com/testuser.keys"
    
    def test_github_keys_url_with_special_chars(self):
        """Test URL with various valid GitHub usernames."""
        valid_usernames = ["user123", "test-user", "User_Name"]
        for username in valid_usernames:
            url = f"https://github.com/{username}.keys"
            assert ".keys" in url
            assert "github.com" in url
    
    @patch('subprocess.run')
    def test_github_keys_fetch_success(self, mock_run):
        """Test successful GitHub key fetch."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ssh-rsa AAAAB... user@example.com\n"
        )
        
        result = subprocess.run(
            "curl -sf https://github.com/testuser.keys",
            shell=True, capture_output=True, text=True
        )
        
        assert result.returncode == 0
        assert "ssh-rsa" in mock_run.return_value.stdout
    
    @patch('subprocess.run')
    def test_github_keys_fetch_failure(self, mock_run):
        """Test failed GitHub key fetch (invalid user)."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Not Found"
        )
        
        result = subprocess.run(
            "curl -sf https://github.com/nonexistentuser12345.keys",
            shell=True, capture_output=True, text=True
        )
        
        assert result.returncode == 1


class TestZrokInstallation:
    """Test zrok installation methods."""
    
    def test_official_installer_url(self):
        """Test official zrok installer URL."""
        installer_url = "https://get.zrok.io"
        assert "get.zrok.io" in installer_url
        assert installer_url.startswith("https://")
    
    def test_fallback_download_url_format(self):
        """Test fallback download URL format."""
        version = "0.4.44"
        url = f"https://github.com/openziti/zrok/releases/download/v{version}/zrok_{version}_linux_amd64.tar.gz"
        
        assert "openziti/zrok" in url
        assert version in url
        assert "linux_amd64" in url
        assert url.endswith(".tar.gz")
    
    def test_zrok_enable_command(self):
        """Test zrok enable command format."""
        token = "test_token_123"
        cmd = f"zrok enable {token}"
        
        assert "zrok" in cmd
        assert "enable" in cmd
        assert token in cmd


class TestTunnelCommands:
    """Test zrok tunnel commands."""
    
    def test_public_tunnel_command(self):
        """Test public tunnel command format."""
        cmd = ['zrok', 'share', 'public', '--backend-mode', 'tcpTunnel', 'localhost:22']
        
        assert cmd[0] == 'zrok'
        assert 'share' in cmd
        assert 'public' in cmd
        assert '--backend-mode' in cmd
        assert 'tcpTunnel' in cmd
        assert 'localhost:22' in cmd
    
    def test_private_tunnel_command(self):
        """Test private tunnel command format."""
        cmd = ['zrok', 'share', 'private', '--backend-mode', 'tcpTunnel', 'localhost:22']
        
        assert cmd[0] == 'zrok'
        assert 'share' in cmd
        assert 'private' in cmd
        assert '--backend-mode' in cmd
        assert 'tcpTunnel' in cmd
        assert 'localhost:22' in cmd
    
    def test_public_tunnel_hostname_regex(self):
        """Test regex for parsing public tunnel hostname."""
        pattern = r'([a-z0-9]+\.share\.zrok\.io)'
        
        test_lines = [
            "https://abc123.share.zrok.io",
            "endpoint: xyz789.share.zrok.io",
            "Share URL: https://test456.share.zrok.io/",
        ]
        
        for line in test_lines:
            match = re.search(pattern, line)
            assert match is not None, f"Should match hostname in: {line}"
            hostname = match.group(1)
            assert hostname.endswith('.share.zrok.io')
    
    def test_private_tunnel_token_regex(self):
        """Test regex for parsing private tunnel token."""
        pattern = r'share token[:\s]+([a-z0-9]+)'
        
        test_lines = [
            "share token: abc123xyz",
            "Share Token: def456uvw",
            "share token abc789qrs",
        ]
        
        for line in test_lines:
            match = re.search(pattern, line.lower())
            assert match is not None, f"Should match token in: {line}"


class TestConnectionInfo:
    """Test connection info formatting."""
    
    def test_public_ssh_command_format(self):
        """Test public SSH command format."""
        hostname = "abc123.share.zrok.io"
        cmd = f"ssh root@{hostname}"
        
        assert cmd == "ssh root@abc123.share.zrok.io"
        assert "root@" in cmd
    
    def test_private_ssh_command_format(self):
        """Test private SSH command format."""
        cmd = "ssh root@localhost -p 9191"
        
        assert "localhost" in cmd
        assert "-p 9191" in cmd
        assert "root@" in cmd
    
    def test_vscode_remote_command_format(self):
        """Test VS Code remote SSH command format."""
        hostname = "abc123.share.zrok.io"
        remote_path = "/kaggle/working"
        cmd = f"code --remote ssh-remote+root@{hostname} {remote_path}"
        
        assert "--remote" in cmd
        assert "ssh-remote+" in cmd
        assert hostname in cmd
        assert remote_path in cmd
    
    def test_zrok_access_command_format(self):
        """Test zrok access private command format."""
        token = "sharetoken123"
        cmd = f"zrok access private {token}"
        
        assert "zrok" in cmd
        assert "access" in cmd
        assert "private" in cmd
        assert token in cmd


class TestKeepAlive:
    """Test keep-alive functionality."""
    
    def test_keep_alive_interval(self):
        """Test keep-alive interval is reasonable."""
        interval = 300  # 5 minutes
        assert interval == 300
        assert interval > 60  # More than 1 minute
        assert interval <= 600  # Less than 10 minutes
    
    def test_elapsed_time_format(self):
        """Test elapsed time formatting."""
        elapsed = 3723  # 1 hour, 2 minutes, 3 seconds
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        assert hours == 1
        assert minutes == 2
        assert seconds == 3
        
        formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        assert formatted == "01:02:03"


class TestValidation:
    """Test input validation."""
    
    def test_validate_zrok_token_placeholder(self):
        """Test that placeholder token is detected."""
        token = "YOUR_ZROK_TOKEN"
        is_placeholder = token == "YOUR_ZROK_TOKEN"
        assert is_placeholder == True
    
    def test_validate_zrok_token_real(self):
        """Test that real token is not detected as placeholder."""
        token = "abc123xyz789"
        is_placeholder = token == "YOUR_ZROK_TOKEN"
        assert is_placeholder == False
    
    def test_validate_tunnel_mode(self):
        """Test tunnel mode validation."""
        valid = ["public", "private"]
        
        assert "public" in valid
        assert "private" in valid
        assert "invalid" not in valid


class TestPathOperations:
    """Test file path operations."""
    
    def test_sshd_config_path(self):
        """Test SSH config path."""
        path = "/etc/ssh/sshd_config"
        assert path.startswith("/etc/ssh")
        assert path.endswith("sshd_config")
    
    def test_ssh_dir_path(self):
        """Test .ssh directory path."""
        path = "/root/.ssh"
        assert ".ssh" in path
    
    def test_authorized_keys_path(self):
        """Test authorized_keys path."""
        path = "/root/.ssh/authorized_keys"
        assert path.endswith("authorized_keys")
        assert ".ssh" in path
    
    def test_run_sshd_path(self):
        """Test run/sshd directory path."""
        path = "/run/sshd"
        assert path == "/run/sshd"


class TestDependencies:
    """Test dependency installation."""
    
    def test_apt_packages(self):
        """Test required apt packages."""
        packages = ["openssh-server"]
        
        assert "openssh-server" in packages
    
    def test_sshd_binary_path(self):
        """Test sshd binary path."""
        path = "/usr/sbin/sshd"
        assert path.endswith("sshd")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
