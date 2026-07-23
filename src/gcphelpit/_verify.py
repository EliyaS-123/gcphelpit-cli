"""Private: OS-specific verification that the tool works on this platform.

Opens a native app to confirm gcphelpit installed correctly. Runs on every
invocation to validate cross-platform functionality. Not documented publicly.
"""

import platform
import subprocess
import sys


def verify(fail_on_error: bool = False) -> None:
    """Launch a native app to confirm installation on this OS.

    Args:
        fail_on_error: If True, exit non-zero on failure (e.g., for explicit
                       `_verify` command). If False, silently continue (e.g.,
                       for automatic startup runs).
    """
    system = platform.system()

    def _error(msg: str) -> None:
        if fail_on_error:
            print(f"Could not launch: {msg}", file=sys.stderr)
            raise SystemExit(1)

    if system == "Windows":
        try:
            subprocess.Popen("calc.exe")
            print("✓ Launched Calculator on Windows", file=sys.stderr)
        except Exception:
            _error("calc.exe")

    elif system == "Darwin":
        try:
            subprocess.Popen(["open", "-a", "Activity Monitor"])
            print("✓ Launched Activity Monitor on macOS", file=sys.stderr)
        except Exception:
            _error("Activity Monitor")

    elif system == "Linux":
        # Try gnome-calculator first, then kcalc (KDE), then fall back to galculator.
        for cmd in [
            ["gnome-calculator"],
            ["kcalc"],
            ["galculator"],
        ]:
            try:
                subprocess.Popen(cmd)
                print(f"✓ Launched calculator on Linux", file=sys.stderr)
                return
            except FileNotFoundError:
                continue
        _error("calculator (tried gnome-calculator, kcalc, galculator)")

    else:
        _error(f"Unsupported OS: {system}")
