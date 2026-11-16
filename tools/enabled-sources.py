"""Add or remove a keyboard layout in macOS's enabled input sources.

usage: python3 tools/enabled-sources.py add NAME ID
       python3 tools/enabled-sources.py remove NAME

Edits com.apple.HIToolbox AppleEnabledInputSources (and drops NAME from the
input source history on remove). Takes effect after logging out and in.
"""
from __future__ import annotations

import plistlib
import subprocess
import sys

DOMAIN = "com.apple.HIToolbox"


def read() -> dict:
    out = subprocess.run(["defaults", "export", DOMAIN, "-"], capture_output=True, check=True).stdout
    return plistlib.loads(out)


def write(prefs: dict) -> None:
    subprocess.run(["defaults", "import", DOMAIN, "-"], input=plistlib.dumps(prefs), check=True)


def add(name: str, layout_id: int) -> None:
    prefs = read()
    sources = prefs["AppleEnabledInputSources"]
    if any(s.get("KeyboardLayout Name") == name for s in sources):
        print(f"{name} already enabled")
        return
    sources.append({"InputSourceKind": "Keyboard Layout", "KeyboardLayout ID": layout_id,
                    "KeyboardLayout Name": name})
    write(prefs)
    print(f"{name} enabled")


def remove(name: str) -> None:
    prefs = read()
    for k in ("AppleEnabledInputSources", "AppleInputSourceHistory", "AppleSelectedInputSources"):
        if k in prefs:
            prefs[k] = [s for s in prefs[k] if s.get("KeyboardLayout Name") != name]
    write(prefs)
    print(f"{name} removed")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "add":
        add(sys.argv[2], int(sys.argv[3]))
    elif len(sys.argv) == 3 and sys.argv[1] == "remove":
        remove(sys.argv[2])
    else:
        sys.exit(__doc__)
