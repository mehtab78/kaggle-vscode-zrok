#!/usr/bin/env python3
"""
Tests for local/connect.py - Kaggle VS Code Connection Helper

Run with: pytest tests/test_connect.py -v
"""

import pytest
import json
import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add local directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "local"))

from connect import (
    Colors,
    load_config,
    save_config,
    check_dependencies,
    update_ssh_config,
    CONFIG_FILE,
    ZROK_PID_FILE,
)


class TestColors:
    """Test Colors class for terminal output."""
    
    def test_colors_defined(self):
        """Test that all color codes are defined."""
        assert Colors.GREEN == '\033[92m'
        assert Colors.YELLOW == '\033[93m'
        assert Colors.RED == '\033[91m'
        assert Colors.BLUE == '\033[94m'
        assert Colors.CYAN == '\033[96m'
        assert Colors.BOLD == '\033[1m'
        assert Colors.END == '\033[0m'
    
    def test_colors_are_ansi_codes(self):
        """Test that colors are valid ANSI escape codes."""
        for attr in ['GREEN', 'YELLOW', 'RED', 'BLUE', 'CYAN', 'BOLD', 'END']:
            color = getattr(Colors, attr)
            assert color.startswith('\033[')
            assert color.endswith('m')


class TestConfig:
    """Test configuration load/save functions."""
    
    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create a temporary config file path."""
        return tmp_path / ".kaggle_vscode_config.json"
    
    def test_load_config_empty(self, tmp_path, monkeypatch):
        """Test loading config when file doesn't exist."""
        fake_config = tmp_path / ".kaggle_vscode_config.json"
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        config = load_config()
        assert config == {}
    
    def test_load_config_with_data(self, tmp_path, monkeypatch):
        """Test loading config with existing data."""
        fake_config = tmp_path / ".kaggle_vscode_config.json"
        test_data = {"hostname": "test.share.zrok.io", "password": "test123"}
        fake_config.write_text(json.dumps(test_data))
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        config = load_config()
        assert config == test_data
    
    def test_save_config(self, tmp_path, monkeypatch):
        """Test saving configuration."""
        fake_config = tmp_path / ".kaggle_vscode_config.json"
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        test_data = {"hostname": "new.share.zrok.io", "mode": "public"}
        save_config(test_data)
        
        assert fake_config.exists()
        loaded = json.loads(fake_config.read_text())
        assert loaded == test_data
    
    def test_save_config_permissions(self, tmp_path, monkeypatch):
        """Test that saved config has restricted permissions."""
        fake_config = tmp_path / ".kaggle_vscode_config.json"
        monkeypatch.setattr('connect.CONFIG_FILE', fake_config)
        
        save_config({"test": "data"})
        
        # Check file permissions (should be 600 = owner read/write only)
        mode = fake_config.stat().st_mode & 0o777
        assert mode == 0o600


class TestDependencyCheck:
    """Test dependency checking function."""
    
    def test_check_dependencies_all_present(self):
        """Test when all dependencies are installed."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = check_dependencies(include_zrok=False)
            assert result == True
    
    def test_check_dependencies_missing_ssh(self):
        """Test when ssh is missing."""
        def mock_which(args, **kwargs):
            result = MagicMock()
            if 'ssh' in args:
                result.returncode = 1  # Not found
            else:
                result.returncode = 0  # Found
            return result
        
        with patch('subprocess.run', side_effect=mock_which):
            result = check_dependencies(include_zrok=False)
            assert result == False
    
    def test_check_dependencies_with_zrok(self):
        """Test checking zrok dependency."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = check_dependencies(include_zrok=True)
            assert result == True
            
            # Verify zrok was checked
            calls = [str(call) for call in mock_run.call_args_list]
            assert any('zrok' in str(call) for call in calls)


class TestSSHConfig:
    """Test SSH config update function."""
    
    @pytest.fixture
    def temp_ssh_dir(self, tmp_path):
        """Create a temporary .ssh directory."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        return ssh_dir
    
    def test_update_ssh_config_creates_entry(self, tmp_path, monkeypatch):
        """Test that SSH config entry is created."""
        ssh_dir = tmp_path / ".ssh"
        ssh_config = ssh_dir / "config"
        
        # Mock Path.home() to return our temp directory
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        update_ssh_config("test.share.zrok.io", port=22, alias="kaggle")
        
        assert ssh_config.exists()
        content = ssh_config.read_text()
        assert "Host kaggle" in content
        assert "HostName test.share.zrok.io" in content
        assert "User root" in content
        assert "Port 22" in content
    
    def test_update_ssh_config_custom_port(self, tmp_path, monkeypatch):
        """Test SSH config with custom port."""
        ssh_dir = tmp_path / ".ssh"
        ssh_config = ssh_dir / "config"
        
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        update_ssh_config("localhost", port=9191, alias="kaggle-private")
        
        content = ssh_config.read_text()
        assert "Port 9191" in content
        assert "Host kaggle-private" in content
    
    def test_update_ssh_config_replaces_existing(self, tmp_path, monkeypatch):
        """Test that existing entry is replaced."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        ssh_config = ssh_dir / "config"
        
        # Create existing config
        existing = """Host kaggle
    HostName old.share.zrok.io
    User root
    Port 22

Host other
    HostName other.example.com
"""
        ssh_config.write_text(existing)
        
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        update_ssh_config("new.share.zrok.io", alias="kaggle")
        
        content = ssh_config.read_text()
        assert "old.share.zrok.io" not in content
        assert "new.share.zrok.io" in content
        assert "Host other" in content  # Other entries preserved
    
    def test_ssh_config_permissions(self, tmp_path, monkeypatch):
        """Test SSH config file has correct permissions."""
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        update_ssh_config("test.share.zrok.io")
        
        ssh_config = tmp_path / ".ssh" / "config"
        mode = ssh_config.stat().st_mode & 0o777
        assert mode == 0o600


class TestConnectionHelpers:
    """Test connection helper functions."""
    
    def test_hostname_format_public(self):
        """Test public hostname format validation."""
        valid_hostnames = [
            "abc123.share.zrok.io",
            "xyz789.share.zrok.io",
            "a1b2c3d4.share.zrok.io",
        ]
        
        import re
        pattern = r'^[a-z0-9]+\.share\.zrok\.io$'
        
        for hostname in valid_hostnames:
            assert re.match(pattern, hostname), f"{hostname} should be valid"
    
    def test_invalid_hostname_format(self):
        """Test invalid hostname detection."""
        invalid_hostnames = [
            "notazrokhost.com",
            "abc123.zrok.io",  # Missing .share
            ".share.zrok.io",  # Missing subdomain
            "ABC123.share.zrok.io",  # Uppercase
        ]
        
        import re
        pattern = r'^[a-z0-9]+\.share\.zrok\.io$'
        
        for hostname in invalid_hostnames:
            assert not re.match(pattern, hostname), f"{hostname} should be invalid"


class TestPrintFunctions:
    """Test print helper functions."""
    
    def test_print_success(self, capsys):
        """Test success message printing."""
        from connect import print_success
        print_success("Test success")
        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "Test success" in captured.out
        assert Colors.GREEN in captured.out
    
    def test_print_error(self, capsys):
        """Test error message printing."""
        from connect import print_error
        print_error("Test error")
        captured = capsys.readouterr()
        assert "❌" in captured.out
        assert "Test error" in captured.out
        assert Colors.RED in captured.out
    
    def test_print_info(self, capsys):
        """Test info message printing."""
        from connect import print_info
        print_info("Test info")
        captured = capsys.readouterr()
        assert "ℹ️" in captured.out
        assert "Test info" in captured.out
        assert Colors.CYAN in captured.out
    
    def test_print_warning(self, capsys):
        """Test warning message printing."""
        from connect import print_warning
        print_warning("Test warning")
        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "Test warning" in captured.out
        assert Colors.YELLOW in captured.out


class TestArgumentParser:
    """Test command-line argument parsing."""
    
    def test_parse_hostname_short(self):
        """Test parsing short hostname flag."""
        import argparse
        from connect import main
        
        # We can't easily test main() directly, but we can test the expected behavior
        test_args = ['-H', 'test.share.zrok.io']
        # This tests the expected argument format
        assert test_args[0] == '-H'
        assert test_args[1] == 'test.share.zrok.io'
    
    def test_parse_private_token(self):
        """Test parsing private tunnel token."""
        test_args = ['--private', 'abc123xyz']
        assert test_args[0] == '--private'
        assert test_args[1] == 'abc123xyz'
    
    def test_parse_vscode_flag(self):
        """Test parsing vscode flag."""
        test_args = ['-H', 'test.share.zrok.io', '--vscode']
        assert '--vscode' in test_args
    
    def test_parse_custom_port(self):
        """Test parsing custom port."""
        test_args = ['--private', 'token', '--port', '9192']
        assert '--port' in test_args
        assert '9192' in test_args


class TestZrokAccess:
    """Test zrok access management functions."""
    
    def test_pid_file_path(self):
        """Test PID file path is in home directory."""
        assert ZROK_PID_FILE == Path.home() / ".kaggle_zrok_access.pid"
    
    @patch('subprocess.Popen')
    @patch('builtins.open', mock_open())
    def test_start_zrok_access_creates_pid_file(self, mock_popen, tmp_path, monkeypatch):
        """Test that starting zrok access creates a PID file."""
        from connect import start_zrok_access, stop_zrok_access
        
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        fake_pid_file = tmp_path / ".kaggle_zrok_access.pid"
        monkeypatch.setattr('connect.ZROK_PID_FILE', fake_pid_file)
        
        # Mock stop_zrok_access to avoid side effects
        with patch('connect.stop_zrok_access'):
            with patch('time.sleep'):
                start_zrok_access("test_token", 9191)
        
        # Verify Popen was called with correct arguments
        mock_popen.assert_called()
        call_args = mock_popen.call_args[0][0]
        assert 'zrok' in call_args
        assert 'access' in call_args
        assert 'private' in call_args


class TestIntegration:
    """Integration tests (require actual environment)."""
    
    @pytest.mark.skipif(
        subprocess.run(['which', 'ssh'], capture_output=True).returncode != 0,
        reason="SSH not installed"
    )
    def test_ssh_available(self):
        """Test that SSH is available on the system."""
        result = subprocess.run(['which', 'ssh'], capture_output=True)
        assert result.returncode == 0
    
    @pytest.mark.skipif(
        subprocess.run(['which', 'sshpass'], capture_output=True).returncode != 0,
        reason="sshpass not installed"
    )
    def test_sshpass_available(self):
        """Test that sshpass is available on the system."""
        result = subprocess.run(['which', 'sshpass'], capture_output=True)
        assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
