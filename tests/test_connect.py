#!/usr/bin/env python3
"""
Tests for local/connect.py - Kaggle VS Code Connection Helper

Run with: pytest tests/test_connect.py -v
"""

import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add local directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "local"))

from connect import (
    Zrok,
    load_config,
    save_config,
    update_ssh_config,
    CONFIG_FILE,
    SSH_CONFIG,
)


class TestZrok:
    """Test Zrok API client class."""
    
    def test_init(self):
        """Test Zrok initialization."""
        zrok = Zrok("test_token", "test_env")
        assert zrok.token == "test_token"
        assert zrok.name == "test_env"
    
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
    
    def test_find_share_token(self):
        """Test finding share token from environment."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "environments": [{
                "environment": {"description": "kaggle_server", "zId": "abc123"},
                "shares": [{
                    "backendMode": "tcpTunnel",
                    "backendProxyEndpoint": "localhost:22",
                    "shareToken": "share123"
                }]
            }]
        }).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            zrok = Zrok("test_token", "test")
            token = zrok.find_share_token("kaggle_server")
            assert token == "share123"


class TestConfig:
    """Test configuration load/save functions."""
    
    def test_load_config_empty(self, tmp_path, monkeypatch):
        """Test loading config when file doesn't exist."""
        fake_config = tmp_path / ".kaggle_vscode_config.json"
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        config = load_config()
        assert config == {}
    
    def test_load_config_with_data(self, tmp_path, monkeypatch):
        """Test loading config with existing data."""
        fake_config = tmp_path / ".kaggle_vscode_config.json"
        test_data = {"token": "test_token_123"}
        fake_config.write_text(json.dumps(test_data))
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        config = load_config()
        assert config == test_data
    
    def test_save_config(self, tmp_path, monkeypatch):
        """Test saving configuration."""
        fake_config = tmp_path / ".kaggle_vscode_config.json"
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        test_data = {"token": "new_token_456"}
        save_config(test_data)
        
        assert fake_config.exists()
        loaded = json.loads(fake_config.read_text())
        assert loaded == test_data
    
    def test_save_config_permissions(self, tmp_path, monkeypatch):
        """Test that saved config has restricted permissions."""
        fake_config = tmp_path / ".kaggle_vscode_config.json"
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        save_config({"test": "data"})
        
        mode = fake_config.stat().st_mode & 0o777
        assert mode == 0o600


class TestSSHConfig:
    """Test SSH config update function."""
    
    def test_update_ssh_config_creates_entry(self, tmp_path, monkeypatch):
        """Test that SSH config entry is created."""
        ssh_dir = tmp_path / ".ssh"
        ssh_config = ssh_dir / "config"
        
        monkeypatch.setattr('connect.SSH_CONFIG', ssh_config)
        
        update_ssh_config("kaggle_client", port=9191)
        
        assert ssh_config.exists()
        content = ssh_config.read_text()
        assert "Host kaggle_client" in content
        assert "HostName 127.0.0.1" in content
        assert "User root" in content
        assert "Port 9191" in content
    
    def test_update_ssh_config_replaces_existing(self, tmp_path, monkeypatch):
        """Test that existing entry is replaced."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        ssh_config = ssh_dir / "config"
        
        existing = """Host kaggle_client
    HostName 127.0.0.1
    User root
    Port 8080

Host other
    HostName other.example.com
"""
        ssh_config.write_text(existing)
        
        monkeypatch.setattr('connect.SSH_CONFIG', ssh_config)
        
        update_ssh_config("kaggle_client", port=9191)
        
        content = ssh_config.read_text()
        assert "Port 8080" not in content
        assert "Port 9191" in content
        assert "Host other" in content  # Other hosts preserved
    
    def test_update_ssh_config_permissions(self, tmp_path, monkeypatch):
        """Test that SSH config has correct permissions."""
        ssh_dir = tmp_path / ".ssh"
        ssh_config = ssh_dir / "config"
        
        monkeypatch.setattr('connect.SSH_CONFIG', ssh_config)
        
        update_ssh_config("test", port=9191)
        
        mode = ssh_config.stat().st_mode & 0o777
        assert mode == 0o600
