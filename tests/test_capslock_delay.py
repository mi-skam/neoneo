from __future__ import annotations

import plistlib
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLIST = ROOT / "tools" / "neoneo.capslockdelay.plist"
HELPER = ROOT / "tools" / "capslockdelay.swift"


class CapsLockDelayAgentTest(unittest.TestCase):
    def setUp(self):
        self.agent = plistlib.loads(PLIST.read_bytes())

    def test_agent_runs_the_installed_helper(self):
        # install.sh replaces the placeholder with the helper's absolute path.
        self.assertEqual(self.agent["Label"], "neoneo.capslockdelay")
        self.assertEqual(self.agent["ProgramArguments"], ["__HELPER__"])

    def test_agent_starts_when_karabiner_virtual_keyboard_appears(self):
        match = self.agent["LaunchEvents"]["com.apple.iokit.matching"]["karabiner-virtual-keyboard"]
        self.assertEqual(match, {
            "IOProviderClass": "IOHIDDevice",
            "VendorID": 0x5AC,
            "ProductID": 0x250,
            "IOMatchLaunchStream": True,
        })

    def test_agent_does_not_poll(self):
        self.assertNotIn("StartInterval", self.agent)
        self.assertNotIn("KeepAlive", self.agent)


class CapsLockDelayHelperTest(unittest.TestCase):
    def test_helper_typechecks(self):
        subprocess.run(["swiftc", "-typecheck", str(HELPER)], check=True)

    def test_helper_consumes_the_launch_event(self):
        # Without a handler for the event stream, launchd relaunches the job every 10 s.
        self.assertIn('xpc_set_event_stream_handler("com.apple.iokit.matching"', HELPER.read_text())


if __name__ == "__main__":
    unittest.main()
