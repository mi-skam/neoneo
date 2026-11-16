from __future__ import annotations

import plistlib
import unittest
from pathlib import Path

PLIST = Path(__file__).resolve().parent.parent / "tools" / "neoneo.capslockdelay.plist"
MATCH = '{"ProductID":0x250,"VendorID":0x5ac}'


class CapsLockDelayAgentTest(unittest.TestCase):
    def test_agent_sets_delay_zero_on_karabiner_virtual_keyboard(self):
        agent = plistlib.loads(PLIST.read_bytes())
        self.assertEqual(agent["Label"], "neoneo.capslockdelay")
        self.assertTrue(agent["RunAtLoad"])
        script = agent["ProgramArguments"][-1]
        self.assertIn(f"--matching '{MATCH}' --set '{{\"CapsLockDelayOverride\":0}}'", script)

    def test_agent_gives_up_after_a_minute(self):
        script = plistlib.loads(PLIST.read_bytes())["ProgramArguments"][-1]
        self.assertIn("seq 30", script)
        self.assertIn("sleep 2", script)


if __name__ == "__main__":
    unittest.main()
