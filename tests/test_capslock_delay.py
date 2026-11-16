from __future__ import annotations

import plistlib
import unittest
from pathlib import Path

PLIST = Path(__file__).resolve().parent.parent / "tools" / "neoneo.capslockdelay.plist"
MATCH = '{"ProductID":0x250,"VendorID":0x5ac}'


class CapsLockDelayAgentTest(unittest.TestCase):
    def setUp(self):
        self.agent = plistlib.loads(PLIST.read_bytes())

    def test_agent_sets_delay_zero_on_karabiner_virtual_keyboard(self):
        self.assertEqual(self.agent["Label"], "neoneo.capslockdelay")
        self.assertEqual(self.agent["ProgramArguments"], [
            "/usr/bin/hidutil", "property", "--matching", MATCH,
            "--set", '{"CapsLockDelayOverride":0}',
        ])

    def test_agent_runs_at_login_and_every_30_seconds(self):
        # A Karabiner restart recreates the virtual keyboard without the setting;
        # the timer restores it within 30 s. (An IOKit-matching launch event would
        # relaunch a non-XPC job every 10 s, so a plain timer is simpler.)
        self.assertTrue(self.agent["RunAtLoad"])
        self.assertEqual(self.agent["StartInterval"], 30)

    def test_agent_output_discarded(self):
        self.assertEqual(self.agent["StandardOutPath"], "/dev/null")


if __name__ == "__main__":
    unittest.main()
