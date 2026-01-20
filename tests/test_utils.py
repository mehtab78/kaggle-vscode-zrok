"""Tests for utils.py - Zrok utility class."""

import pytest
from unittest.mock import patch, MagicMock
import subprocess


class TestZrokInit:
    """Test Zrok class initialization."""
    
    def test_valid_token(self):
        from utils import Zrok
        zrok = Zrok("valid_token_123")
        assert zrok.token == "valid_token_123"
        assert zrok.name == "kaggle_server"
    
    def test_custom_name(self):
        from utils import Zrok
        zrok = Zrok("token", "custom_env")
        assert zrok.name == "custom_env"
    
    def test_placeholder_token_raises(self):
        from utils import Zrok
        with pytest.raises(ValueError, match="actual zrok token"):
            Zrok("<YOUR_TOKEN>")
    
    def test_empty_token_raises(self):
        from utils import Zrok
        with pytest.raises(ValueError):
            Zrok("")
    
    def test_none_token_raises(self):
        from utils import Zrok
        with pytest.raises(ValueError):
            Zrok(None)


class TestZrokAPI:
    """Test Zrok API methods."""
    
    @patch('utils.urllib.request.urlopen')
    def test_get_environments(self, mock_urlopen):
        from utils import Zrok
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"environments": [{"environment": {"description": "test"}}]}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        zrok = Zrok("token")
        envs = zrok.get_environments()
        assert len(envs) == 1
    
    @patch('utils.urllib.request.urlopen')
    def test_find_env_found(self, mock_urlopen):
        from utils import Zrok
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"environments": [{"environment": {"description": "kaggle_server", "zId": "abc123"}}]}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        zrok = Zrok("token")
        env = zrok.find_env("kaggle_server")
        assert env is not None
        assert env["environment"]["zId"] == "abc123"
    
    def test_find_env_not_found(self):
        from utils import Zrok
        with patch.object(Zrok, 'get_environments', return_value=[]):
            zrok = Zrok("token")
            env = zrok.find_env("nonexistent")
            assert env is None
    
    def test_find_env_handles_none_environments(self):
        """Test that find_env handles None return gracefully."""
        from utils import Zrok
        with patch.object(Zrok, 'get_environments', return_value=None):
            zrok = Zrok("token")
            env = zrok.find_env("test")
            assert env is None
    
    def test_get_environments_handles_api_errors(self):
        """Test that get_environments returns empty list on API errors."""
        from utils import Zrok, ZrokError
        with patch.object(Zrok, '_request', side_effect=ZrokError("API error")):
            zrok = Zrok("token")
            envs = zrok.get_environments()
            assert envs == []
    
    @patch('utils.urllib.request.urlopen')
    def test_find_share_token(self, mock_urlopen):
        from utils import Zrok
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"environments": [{"environment": {"description": "kaggle_server"}, "shares": [{"token": "share123", "backendProxyEndpoint": "localhost:22"}]}]}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        zrok = Zrok("token")
        token = zrok.find_share_token()
        assert token == "share123"


class TestZrokCLI:
    """Test Zrok CLI wrapper methods."""
    
    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        from utils import Zrok
        mock_run.return_value = MagicMock(returncode=0)
        assert Zrok.is_installed() is True
    
    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        from utils import Zrok
        mock_run.side_effect = FileNotFoundError()
        assert Zrok.is_installed() is False
    
    @patch('subprocess.run')
    def test_enable_already_enabled(self, mock_run):
        from utils import Zrok
        # First call is zrok status
        status_result = MagicMock()
        status_result.stdout = "Account Token  <<SET>>"
        # Mock returns status check
        mock_run.return_value = status_result
        
        zrok = Zrok("token")
        zrok.enable()  # Should not raise
    
    @patch('subprocess.run')
    @patch('subprocess.Popen')
    def test_share(self, mock_popen, mock_run):
        from utils import Zrok
        zrok = Zrok("token")
        zrok.share()
        mock_popen.assert_called_once()


class TestSetupScript:
    """Test setup_script.py functions."""
    
    def test_generate_random_password(self):
        from setup_script import generate_random_password
        pwd1 = generate_random_password()
        pwd2 = generate_random_password()
        assert len(pwd1) == 16
        assert pwd1 != pwd2  # Should be random
    
    def test_generate_random_password_custom_length(self):
        from setup_script import generate_random_password
        pwd = generate_random_password(32)
        assert len(pwd) == 32
