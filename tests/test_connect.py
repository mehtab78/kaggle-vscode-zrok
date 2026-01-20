#!/usr/bin/env python3
"""
Tests for local/connect.py - Kaggle VS Code Connection Client

Run with: pytest tests/test_connect.py -v
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "local"))

from connect import (
    Zrok,
    ZrokError,
    load_config,
    save_config,
    update_ssh_config,
    CONFIG_FILE,
    SSH_CONFIG,
)


class TestZrokClient:
    """Test embedded Zrok client in connect.py."""
    
    def test_init(self):
        """Test Zrok initialization."""
        zrok = Zrok("test_token", "test_env")
        assert zrok.token == "test_token"
        assert zrok.name == "test_env"
    
    def test_init_empty_token(self):
        """Test that empty token raises error."""
        with pytest.raises(ValueError):
            Zrok("", "test")
    
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


class TestConfig:
    """Test configuration functions."""
    
    def test_load_config_empty(self, tmp_path, monkeypatch):
        """Test loading config when file doesn't exist."""
        fake_config = tmp_path / ".kaggle_zrok_config.json"
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        config = load_config()
        assert config == {}
    
    def test_load_config_with_data(self, tmp_path, monkeypatch):
        """Test loading config with existing data."""
        fake_config = tmp_path / ".kaggle_zrok_config.json"
        test_data = {"token": "test_token_123"}
        fake_config.write_text(json.dumps(test_data))
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        config = load_config()
        assert config == test_data
    
    def test_load_config_invalid_json(self, tmp_path, monkeypatch):
        """Test loading config with invalid JSON."""
        fake_config = tmp_path / ".kaggle_zrok_config.json"
        fake_config.write_text("not valid json")
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        config = load_config()
        assert config == {}
    
    def test_save_config(self, tmp_path, monkeypatch):
        """Test saving configuration."""
        fake_config = tmp_path / ".kaggle_zrok_config.json"
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        test_data = {"token": "new_token_456"}
        save_config(test_data)
        
        assert fake_config.exists()
        loaded = json.loads(fake_config.read_text())
        assert loaded == test_data
    
    def test_save_config_permissions(self, tmp_path, monkeypatch):
        """Test that saved config has restricted permissions."""
        fake_config = tmp_path / ".kaggle_zrok_config.json"
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        save_config({"test": "data"})
        
        mode = fake_config.stat().st_mode & 0o777
        assert mode == 0o600


class TestSSHConfig:
    """Test SSH config functions."""
    
    def test_update_ssh_config_creates_entry(self, tmp_path, monkeypatch):
        """Test that SSH config entry is created."""
        ssh_dir = tmp_path / ".ssh"
        ssh_config = ssh_dir / "config"
        monkeypatch.setattr('connect.SSH_CONFIG', ssh_config)
        
        update_ssh_config("kaggle", port=9191)
        
        assert ssh_config.exists()
        content = ssh_config.read_text()
        assert "Host kaggle" in content
        assert "HostName 127.0.0.1" in content
        assert "User root" in content
        assert "Port 9191" in content
    
    def test_update_ssh_config_replaces_existing(self, tmp_path, monkeypatch):
        """Test that existing entry is replaced."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        ssh_config = ssh_dir / "config"
        
        existing = """Host kaggle
    HostName 127.0.0.1
    User root
    Port 8080

Host other
    HostName other.example.com
"""
        ssh_config.write_text(existing)
        monkeypatch.setattr('connect.SSH_CONFIG', ssh_config)
        
        update_ssh_config("kaggle", port=9191)
        
        content = ssh_config.read_text()
        assert "Port 8080" not in content
        assert "Port 9191" in content
        assert "Host other" in content  # Other hosts preserved
    
    def test_update_ssh_config_permissions(self, tmp_path, monkeypatch):
        """Test that SSH config has correct permissions."""
        ssh_config = tmp_path / ".ssh" / "config"
        monkeypatch.setattr('connect.SSH_CONFIG', ssh_config)
        
        update_ssh_config("test", port=9191)
        
        mode = ssh_config.stat().st_mode & 0o777
        assert mode == 0o600
    
    def test_update_ssh_config_creates_directory(self, tmp_path, monkeypatch):
        """Test that .ssh directory is created if missing."""
        ssh_config = tmp_path / ".ssh" / "config"
        monkeypatch.setattr('connect.SSH_CONFIG', ssh_config)
        
        # Directory doesn't exist yet
        assert not ssh_config.parent.exists()
        
        update_ssh_config("test", port=9191)
        
        assert ssh_config.parent.exists()
        assert ssh_config.exists()
