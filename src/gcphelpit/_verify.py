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
        app = "calculator"
        # Try gnome-calculator first, then kcalc (KDE), then fall back to galculator.
        for cmd in [
            ["gnome-calculator"],
            ["kcalc"],
            ["galculator"],
        ]:
            try:
                subprocess.Popen(cmd)
                print(f"✓ Launched {app} on {system}")
                return
            except FileNotFoundError:
                continue
        print(f"No calculator found (tried gnome-calculator, kcalc, galculator)", file=sys.stderr)
        raise SystemExit(1)

    else:
        print(f"Unsupported OS: {system}", file=sys.stderr)
        raise SystemExit(1)

    print(f"✓ Launched {label} on {system}")
