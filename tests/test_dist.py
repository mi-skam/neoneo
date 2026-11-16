from __future__ import annotations

import os
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from neoneo import VERSION, dist  # noqa: E402


class DistTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp())
        cls.folder = dist(cls.out)

    def test_folder_name_carries_version(self):
        self.assertEqual(self.folder, self.out / f"neoneo-{VERSION}")

    def test_contents(self):
        names = sorted(p.name for p in self.folder.iterdir())
        self.assertEqual(names, [
            "README.md", "install.sh", "karabiner-neoneo.json",
            "neoneo.bundle", "neoneo.capslockdelay.plist", "uninstall.sh",
        ])
        info = plistlib.loads((self.folder / "neoneo.bundle" / "Contents" / "Info.plist").read_bytes())
        self.assertEqual(info["CFBundleVersion"], VERSION)

    def test_scripts_executable_and_valid_sh(self):
        for name in ("install.sh", "uninstall.sh"):
            with self.subTest(name):
                path = self.folder / name
                self.assertTrue(os.access(path, os.X_OK))
                subprocess.run(["sh", "-n", str(path)], check=True)

    def test_install_clears_quarantine_and_enables_source(self):
        text = (self.folder / "install.sh").read_text()
        self.assertIn("xattr -cr", text)
        self.assertIn("AppleEnabledInputSources", text)
        self.assertIn("launchctl bootstrap", text)

    def test_uninstall_refuses_while_neoneo_selected(self):
        text = (self.folder / "uninstall.sh").read_text()
        self.assertIn("AppleSelectedInputSources", text)


class VersionTest(unittest.TestCase):
    def test_version_command_prints_version(self):
        out = subprocess.run([sys.executable, str(ROOT / "neoneo.py"), "version"],
                             check=True, capture_output=True, text=True).stdout
        self.assertEqual(out, VERSION + "\n")


if __name__ == "__main__":
    unittest.main()
