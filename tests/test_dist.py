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

HELPER_BYTES = b"\xcf\xfa\xed\xfe fake helper"


class DistTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp())
        helper = cls.out / "helper-in"
        helper.write_bytes(HELPER_BYTES)
        cls.folder = dist(cls.out, helper)

    def test_folder_name_carries_version(self):
        self.assertEqual(self.folder, self.out / f"neoneo-{VERSION}")

    def test_contents(self):
        names = sorted(p.name for p in self.folder.iterdir())
        self.assertEqual(names, [
            "README.md", "install.sh", "karabiner-config.js", "karabiner-neoneo.json",
            "neoneo-capslockdelay", "neoneo.bundle", "neoneo.capslockdelay.plist",
            "remove-input-source.sh", "uninstall.sh",
        ])
        info = plistlib.loads((self.folder / "neoneo.bundle" / "Contents" / "Info.plist").read_bytes())
        self.assertEqual(info["CFBundleVersion"], VERSION)

    def test_helper_shipped_executable(self):
        helper = self.folder / "neoneo-capslockdelay"
        self.assertEqual(helper.read_bytes(), HELPER_BYTES)
        self.assertTrue(os.access(helper, os.X_OK))

    def test_install_points_agent_at_installed_helper(self):
        text = (self.folder / "install.sh").read_text()
        self.assertIn("__HELPER__", text)
        self.assertIn("Application Support/neoneo", text)

    def test_scripts_executable_and_valid_sh(self):
        for name in ("install.sh", "uninstall.sh", "remove-input-source.sh"):
            with self.subTest(name):
                path = self.folder / name
                self.assertTrue(os.access(path, os.X_OK))
                subprocess.run(["sh", "-n", str(path)], check=True)

    def test_install_clears_quarantine_and_enables_source(self):
        text = (self.folder / "install.sh").read_text()
        self.assertIn("xattr -cr", text)
        self.assertIn("AppleEnabledInputSources", text)
        self.assertIn("launchctl bootstrap", text)

    def test_install_writes_karabiner_config(self):
        text = (self.folder / "install.sh").read_text()
        self.assertIn('karabiner-config.js" install', text)

    def test_uninstall_refuses_while_neoneo_selected(self):
        text = (self.folder / "uninstall.sh").read_text()
        self.assertIn("AppleSelectedInputSources", text)

    def test_uninstall_edits_only_the_input_source_lists(self):
        text = (self.folder / "uninstall.sh").read_text()
        self.assertIn('remove-input-source.sh" com.apple.HIToolbox neoneo', text)
        self.assertNotIn("defaults import", text)

    def test_uninstall_removes_karabiner_rules(self):
        text = (self.folder / "uninstall.sh").read_text()
        self.assertIn('karabiner-config.js" uninstall', text)


class VersionTest(unittest.TestCase):
    def test_version_command_prints_version(self):
        out = subprocess.run([sys.executable, str(ROOT / "neoneo.py"), "version"],
                             check=True, capture_output=True, text=True).stdout
        self.assertEqual(out, VERSION + "\n")


if __name__ == "__main__":
    unittest.main()
