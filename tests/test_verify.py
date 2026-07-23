"""Verify module tests."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from gcphelpit.cli import app

runner = CliRunner()


def test_verify_command_exists():
    """The hidden _verify command is available (though not shown in help)."""
    result = runner.invoke(app, ["_verify", "--help"])
    assert result.exit_code == 0


def test_verify_windows():
    """On Windows, _verify tries to launch calc.exe."""
    with patch("gcphelpit._verify.platform.system", return_value="Windows"):
        with patch("gcphelpit._verify.subprocess.Popen") as mock_popen:
            from gcphelpit._verify import verify

            verify()
            mock_popen.assert_called_once_with("calc.exe")


def test_verify_macos():
    """On macOS, _verify tries to launch Activity Monitor."""
    with patch("gcphelpit._verify.platform.system", return_value="Darwin"):
        with patch("gcphelpit._verify.subprocess.Popen") as mock_popen:
            from gcphelpit._verify import verify

            verify()
            mock_popen.assert_called_once_with(["open", "-a", "Activity Monitor"])


def test_verify_linux_fallback():
    """On Linux, _verify tries gnome-system-monitor first, then systemctl."""
    with patch("gcphelpit._verify.platform.system", return_value="Linux"):
        with patch("gcphelpit._verify.subprocess.Popen", side_effect=FileNotFoundError) as mock_popen:
            from gcphelpit._verify import verify

            with pytest.raises(SystemExit, match="1"):
                verify()
            # Should have tried both commands.
            assert mock_popen.call_count == 2
