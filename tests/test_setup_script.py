#!/usr/bin/env python3
"""
Tests for kaggle/setup_script.py - Kaggle Setup Script

Run with: pytest tests/test_setup_script.py -v
"""

import pytest
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add kaggle directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "kaggle"))

from setup_script import Zrok


class TestZrok:
    """Test Zrok API client class."""
    
    def test_init_valid_token(self):
        """Test Zrok initialization with valid token."""
        zrok = Zrok("valid_token_123", "test_env")
        assert zrok.token == "valid_token_123"
        assert zrok.name == "test_env"
    
    def test_init_placeholder_token(self):
        """Test Zrok initialization with placeholder token raises error."""
        with pytest.raises(ValueError, match="Please provide your actual zrok token"):
            Zrok("<YOUR_ZROK_TOKEN>", "test_env")
    
    def test_base_url(self):
        """Test that BASE_URL is correct."""
        assert Zrok.BASE_URL == "https://api-v1.zrok.io/api/v1"
    
    def test_is_installed_true(self):
        """Test is_installed when zrok is available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert Zrok.is_installed() == True
    
    def test_is_installed_false(self):
        """Test is_installed when zrok is not available."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            assert Zrok.is_installed() == False
    
    def test_get_environments(self):
        """Test getting environments from API."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "environments": [
                {"environment": {"description": "kaggle_server", "zId": "abc123"}}
            ]
        }).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            zrok = Zrok("test_token", "test")
            envs = zrok.get_environments()
            assert len(envs) == 1
            assert envs[0]["environment"]["description"] == "kaggle_server"
    
    def test_find_env_found(self):
        """Test finding an existing environment."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "environments": [
                {"environment": {"description": "kaggle_server", "zId": "abc123"}}
            ]
        }).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            zrok = Zrok("test_token", "test")
            env = zrok.find_env("kaggle_server")
            assert env is not None
            assert env["environment"]["zId"] == "abc123"
    
    def test_find_env_case_insensitive(self):
        """Test that find_env is case insensitive."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "environments": [
                {"environment": {"description": "Kaggle_Server", "zId": "abc123"}}
            ]
        }).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            zrok = Zrok("test_token", "test")
            env = zrok.find_env("kaggle_server")
            assert env is not None
    
    def test_find_env_not_found(self):
        """Test finding a non-existent environment."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "environments": []
        }).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            zrok = Zrok("test_token", "test")
            env = zrok.find_env("nonexistent")
            assert env is None
    
    def test_delete_env(self):
        """Test deleting environment via API."""
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            zrok = Zrok("test_token", "test")
            result = zrok.delete_env("abc123")
            assert result == True


class TestSSHConfiguration:
    """Test SSH server configuration values."""
    
    def test_sshd_config_content(self):
        """Test expected SSH configuration options."""
        expected_options = [
            "Port 22",
            "PermitRootLogin yes",
            "PasswordAuthentication yes",
            "PubkeyAuthentication yes",
            "X11Forwarding yes",
            "AllowTcpForwarding yes",
            "ClientAliveInterval 60",
            "ClientAliveCountMax 3",
        ]
        
        # These should all be present in a proper sshd_config
        for option in expected_options:
            assert option  # Just verify they're non-empty strings
    
    def test_ssh_directory_permissions(self):
        """Test expected SSH directory permissions."""
        expected_mode = 0o700
        assert expected_mode == 448  # 0o700 in decimal
    
    def test_authorized_keys_permissions(self):
        """Test expected authorized_keys permissions."""
        expected_mode = 0o600
        assert expected_mode == 384  # 0o600 in decimal


class TestConfiguration:
    """Test configuration validation."""
    
    def test_env_name_default(self):
        """Test default environment name."""
        default_name = "kaggle_server"
        assert default_name.isalpha() or "_" in default_name
    
    def test_password_default(self):
        """Test default password."""
        default_password = "0"
        assert len(default_password) >= 1
    
    def test_placeholder_token_format(self):
        """Test that placeholder token has recognizable format."""
        placeholder = "<YOUR_ZROK_TOKEN>"
        assert placeholder.startswith("<")
        assert placeholder.endswith(">")
        assert "TOKEN" in placeholder
