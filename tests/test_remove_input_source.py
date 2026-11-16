from __future__ import annotations

import plistlib
import subprocess
import unittest
import uuid
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "remove-input-source.sh"
GERMAN = {"InputSourceKind": "Keyboard Layout", "KeyboardLayout ID": 3, "KeyboardLayout Name": "German"}
NEONEO = {"InputSourceKind": "Keyboard Layout", "KeyboardLayout ID": -24601, "KeyboardLayout Name": "neoneo"}
PRESS = {"Bundle ID": "com.apple.PressAndHold", "InputSourceKind": "Non Keyboard Input Method"}


class RemoveInputSourceTest(unittest.TestCase):
    """Runs the script against a throwaway preferences domain, never HIToolbox."""

    def setUp(self):
        self.domain = f"neoneo.test.{uuid.uuid4().hex}"
        prefs = {
            "AppleEnabledInputSources": [PRESS, NEONEO, GERMAN],
            "AppleInputSourceHistory": [NEONEO, GERMAN],
            "AppleSelectedInputSources": [PRESS, GERMAN],
            "Unrelated": "keep",
        }
        subprocess.run(["defaults", "import", self.domain, "-"], input=plistlib.dumps(prefs), check=True)

    def tearDown(self):
        subprocess.run(["defaults", "delete", self.domain], check=True, capture_output=True)

    def read(self) -> dict:
        out = subprocess.run(["defaults", "export", self.domain, "-"], check=True, capture_output=True).stdout
        return plistlib.loads(out)

    def run_script(self) -> None:
        subprocess.run(["sh", str(SCRIPT), self.domain, "neoneo"], check=True, capture_output=True)

    def test_removes_layout_from_enabled_and_history_only(self):
        self.run_script()
        prefs = self.read()
        self.assertEqual(prefs["AppleEnabledInputSources"], [PRESS, GERMAN])
        self.assertEqual(prefs["AppleInputSourceHistory"], [GERMAN])
        self.assertEqual(prefs["AppleSelectedInputSources"], [PRESS, GERMAN])
        self.assertEqual(prefs["Unrelated"], "keep")

    def test_second_run_changes_nothing(self):
        self.run_script()
        before = self.read()
        self.run_script()
        self.assertEqual(self.read(), before)


if __name__ == "__main__":
    unittest.main()
