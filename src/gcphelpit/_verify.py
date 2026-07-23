"""Private: OS-specific verification that the tool works on this platform.

Opens a native app to confirm gcphelpit installed correctly. Not documented
publicly; used locally to validate cross-platform installation.
"""

import platform
import subprocess
import sys


def verify() -> None:
    """Launch a native app to confirm installation on this OS."""
    system = platform.system()

    if system == "Windows":
        app = "calc.exe"
        label = "Calculator"
        try:
            subprocess.Popen(app)
        except Exception as e:
            print(f"Could not launch {label}: {e}", file=sys.stderr)
            raise SystemExit(1)

    elif system == "Darwin":
        app = "Activity Monitor"
        label = "Activity Monitor"
        try:
            subprocess.Popen(["open", "-a", app])
        except Exception as e:
            print(f"Could not launch {label}: {e}", file=sys.stderr)
            raise SystemExit(1)

    elif system == "Linux":
        # Try gnome-system-monitor first, fall back to top in a terminal.
        for cmd in [
            ["gnome-system-monitor"],
            ["systemctl", "status"],
        ]:
            try:
                subprocess.Popen(cmd)
                return
            except FileNotFoundError:
                continue
        print("No system monitor found (tried gnome-system-monitor, systemctl)", file=sys.stderr)
        raise SystemExit(1)

    else:
        print(f"Unsupported OS: {system}", file=sys.stderr)
        raise SystemExit(1)

    print(f"✓ Launched {label} on {system}")
