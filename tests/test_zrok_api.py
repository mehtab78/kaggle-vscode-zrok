#!/usr/bin/env python3
"""
Tests for zrok_api.py - Shared Zrok API Client

Run with: pytest tests/test_zrok_api.py -v
"""

import pytest
import json
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zrok_api import Zrok, ZrokError


class TestZrokInit:
    """Test Zrok initialization."""
    
    def test_valid_token(self):
        """Test initialization with valid token."""
        zrok = Zrok("valid_token_123", "test_env")
        assert zrok.token == "valid_token_123"
        assert zrok.name == "test_env"
    
    def test_placeholder_token_angle_brackets(self):
        """Test that placeholder token with angle brackets raises error."""
        with pytest.raises(ValueError, match="actual zrok token"):
            Zrok("<YOUR_TOKEN>", "test")
    
    def test_empty_token(self):
        """Test that empty token raises error."""
        with pytest.raises(ValueError):
            Zrok("", "test")
    
    def test_none_token(self):
        """Test that None token raises error."""
        with pytest.raises(ValueError):
            Zrok(None, "test")
    
    def test_default_name(self):
        """Test default environment name."""
        zrok = Zrok("token123")
        assert zrok.name == "kaggle"


class TestZrokAPI:
    """Test Zrok API methods."""
    
    @pytest.fixture
    def mock_response(self):
        """Create mock urllib response."""
        def _make_response(data):
            mock = MagicMock()
            mock.read.return_value = json.dumps(data).encode()
            mock.__enter__ = MagicMock(return_value=mock)
            mock.__exit__ = MagicMock(return_value=False)
            return mock
        return _make_response
    
    def test_get_environments(self, mock_response):
        """Test getting environments."""
        response = mock_response({
            "environments": [
                {"environment": {"description": "kaggle_server", "zId": "abc123"}}
            ]
        })
        
        with patch('urllib.request.urlopen', return_value=response):
            zrok = Zrok("test_token", "test")
            envs = zrok.get_environments()
            assert len(envs) == 1
            assert envs[0]["environment"]["description"] == "kaggle_server"
    
    def test_get_environments_empty(self, mock_response):
        """Test getting environments when none exist."""
        response = mock_response({"environments": []})
        
        with patch('urllib.request.urlopen', return_value=response):
            zrok = Zrok("test_token", "test")
            envs = zrok.get_environments()
            assert envs == []
    
    def test_find_env_found(self, mock_response):
        """Test finding an existing environment."""
        response = mock_response({
            "environments": [
                {"environment": {"description": "kaggle_server", "zId": "abc123"}}
            ]
        })
        
        with patch('urllib.request.urlopen', return_value=response):
            zrok = Zrok("test_token", "test")
            env = zrok.find_env("kaggle_server")
            assert env is not None
            assert env["environment"]["zId"] == "abc123"
    
    def test_find_env_case_insensitive(self, mock_response):
        """Test that find_env is case insensitive."""
        response = mock_response({
            "environments": [
                {"environment": {"description": "Kaggle_Server", "zId": "abc123"}}
            ]
        })
        
        with patch('urllib.request.urlopen', return_value=response):
            zrok = Zrok("test_token", "test")
            env = zrok.find_env("kaggle_server")
            assert env is not None
    
    def test_find_env_not_found(self, mock_response):
        """Test finding a non-existent environment."""
        response = mock_response({"environments": []})
        
        with patch('urllib.request.urlopen', return_value=response):
            zrok = Zrok("test_token", "test")
            env = zrok.find_env("nonexistent")
            assert env is None
    
    def test_find_share_token(self, mock_response):
        """Test finding share token from environment."""
        response = mock_response({
            "environments": [{
                "environment": {"description": "kaggle_server", "zId": "abc123"},
                "shares": [{
                    "backendMode": "tcpTunnel",
                    "backendProxyEndpoint": "localhost:22",
                    "shareToken": "share123token"
                }]
            }]
        })
        
        with patch('urllib.request.urlopen', return_value=response):
            zrok = Zrok("test_token", "test")
            token = zrok.find_share_token("kaggle_server")
            assert token == "share123token"
    
    def test_find_share_token_no_shares(self, mock_response):
        """Test finding share token when no shares exist."""
        response = mock_response({
            "environments": [{
                "environment": {"description": "kaggle_server", "zId": "abc123"},
                "shares": []
            }]
        })
        
        with patch('urllib.request.urlopen', return_value=response):
            zrok = Zrok("test_token", "test")
            token = zrok.find_share_token("kaggle_server")
            assert token is None
    
    def test_find_share_token_wrong_port(self, mock_response):
        """Test finding share token with wrong port."""
        response = mock_response({
            "environments": [{
                "environment": {"description": "kaggle_server", "zId": "abc123"},
                "shares": [{
                    "backendMode": "tcpTunnel",
                    "backendProxyEndpoint": "localhost:8080",  # Wrong port
                    "shareToken": "share123token"
                }]
            }]
        })
        
        with patch('urllib.request.urlopen', return_value=response):
            zrok = Zrok("test_token", "test")
            token = zrok.find_share_token("kaggle_server", port=22)
            assert token is None


class TestZrokCLI:
    """Test Zrok CLI-related methods."""
    
    def test_is_installed_true(self):
        """Test is_installed when zrok is available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert Zrok.is_installed() == True
    
    def test_is_installed_false_not_found(self):
        """Test is_installed when zrok is not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            assert Zrok.is_installed() == False
    
    def test_is_installed_false_error(self):
        """Test is_installed when zrok returns error."""
        with patch('subprocess.run') as mock_run:
            from subprocess import CalledProcessError
            mock_run.side_effect = CalledProcessError(1, 'zrok')
            assert Zrok.is_installed() == False


class TestZrokConstants:
    """Test Zrok constants."""
    
    def test_base_url(self):
        """Test BASE_URL is correct."""
        assert Zrok.BASE_URL == "https://api-v1.zrok.io/api/v1"
    
    def test_timeout(self):
        """Test timeout value."""
        assert Zrok.TIMEOUT == 30
    
    def test_max_retries(self):
        """Test max retries value."""
        assert Zrok.MAX_RETRIES == 3
