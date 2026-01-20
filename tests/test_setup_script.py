"""Tests for setup_script.py functions."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_script import (
    generate_random_password,
    shutil_which,
    configure_ssh,
)


class TestPasswordGeneration(unittest.TestCase):
    """Test password generation functions."""

    def test_generate_random_password_default_length(self):
        """Test default password length is 16."""
        password = generate_random_password()
        self.assertEqual(len(password), 16)

    def test_generate_random_password_custom_length(self):
        """Test custom password length."""
        password = generate_random_password(24)
        self.assertEqual(len(password), 24)

    def test_generate_random_password_minimum_length(self):
        """Test minimum password length is 8."""
        password = generate_random_password(8)
        self.assertEqual(len(password), 8)

    def test_generate_random_password_too_short_raises(self):
        """Test that password length < 8 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            generate_random_password(7)
        self.assertIn("at least 8", str(context.exception))

    def test_generate_random_password_randomness(self):
        """Test that passwords are random (not identical)."""
        password1 = generate_random_password()
        password2 = generate_random_password()
        self.assertNotEqual(password1, password2)

    def test_generate_random_password_character_set(self):
        """Test password contains only letters and digits."""
        password = generate_random_password(100)
        self.assertTrue(all(c.isalnum() for c in password))


class TestShutilWhich(unittest.TestCase):
    """Test shutil_which wrapper function."""

    @patch('shutil.which')
    def test_shutil_which_found(self, mock_which):
        """Test command is found."""
        mock_which.return_value = "/usr/bin/ssh"
        result = shutil_which("ssh")
        self.assertEqual(result, "/usr/bin/ssh")

    @patch('shutil.which')
    def test_shutil_which_not_found(self, mock_which):
        """Test command not found returns None."""
        mock_which.return_value = None
        result = shutil_which("nonexistent")
        self.assertIsNone(result)


class TestConfigureSSH(unittest.TestCase):
    """Test SSH configuration functions."""

    @patch('setup_script.subprocess.Popen')
    @patch('setup_script.os.makedirs')
    @patch('setup_script.Path')
    @patch('setup_script.shutil_which')
    @patch('setup_script._run')
    def test_configure_ssh_password_only(
        self, mock_run, mock_which, mock_path, mock_makedirs, mock_popen
    ):
        """Test SSH configuration with password only."""
        # Setup mocks
        mock_which.return_value = "/usr/sbin/service"
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc
        
        mock_config_path = MagicMock()
        mock_config_path.exists.return_value = True
        mock_config_path.read_text.return_value = "PermitRootLogin no\n"
        mock_path.return_value = mock_config_path

        # Call function
        configure_ssh("test_password")

        # Verify password was set
        mock_popen.assert_called_once_with(
            ["chpasswd"], stdin=unittest.mock.ANY, text=True
        )
        mock_proc.communicate.assert_called_once_with("root:test_password\n")

        # Verify SSH service was started
        mock_run.assert_called()

    @patch('setup_script.subprocess.Popen')
    @patch('setup_script.os.makedirs')
    @patch('setup_script.Path')
    @patch('setup_script.shutil_which')
    @patch('setup_script._run')
    def test_configure_ssh_password_failure(
        self, mock_run, mock_which, mock_path, mock_makedirs, mock_popen
    ):
        """Test SSH configuration handles password failure."""
        # Setup mocks
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc

        # Should raise RuntimeError
        with self.assertRaises(RuntimeError) as context:
            configure_ssh("test_password")
        self.assertIn("Failed to set password", str(context.exception))

    @patch('setup_script.urllib.request.urlopen')
    @patch('setup_script.subprocess.Popen')
    @patch('setup_script.os.makedirs')
    @patch('setup_script.Path')
    @patch('setup_script.shutil_which')
    @patch('setup_script._run')
    def test_configure_ssh_with_authorized_keys(
        self, mock_run, mock_which, mock_path_class, 
        mock_makedirs, mock_popen, mock_urlopen
    ):
        """Test SSH configuration with authorized keys URL."""
        # Setup mocks
        mock_which.return_value = "/usr/sbin/service"
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        # Mock config file
        mock_config_path = MagicMock()
        mock_config_path.exists.return_value = True
        mock_config_path.read_text.return_value = ""
        
        # Mock authorized_keys handling
        mock_ssh_dir = MagicMock()
        mock_auth_keys = MagicMock()
        
        def path_side_effect(path_str):
            if path_str == "/etc/ssh/sshd_config":
                return mock_config_path
            elif path_str == "/root/.ssh":
                return mock_ssh_dir
            return MagicMock()
        
        mock_path_class.side_effect = path_side_effect
        
        # Mock SSH dir behavior
        mock_ssh_dir.__truediv__ = lambda self, x: mock_auth_keys
        
        # Mock URL response
        mock_response = MagicMock()
        mock_response.read.return_value = b"ssh-rsa AAAAB3... user@host"
        mock_response.decode.return_value = "ssh-rsa AAAAB3... user@host"
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = lambda self, *args: None
        mock_urlopen.return_value = mock_response

        # Call function
        configure_ssh("test_password", "https://example.com/keys")

        # Verify authorized keys were processed
        mock_urlopen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
