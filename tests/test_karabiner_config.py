from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from neoneo import ISO_SWAP_DEVICES, karabiner_rules, load_layout  # noqa: E402

SCRIPT = ROOT / "tools" / "karabiner-config.js"
RULES = karabiner_rules(load_layout(ROOT / "layout" / "neoneo.tsv"))
OTHER_RULE = {"description": "Neo2 layer 6", "manipulators": []}


def config(devices: list) -> dict:
    return {
        "global": {"show_in_menu_bar": True},
        "profiles": [
            {"name": "Other", "complex_modifications": {"rules": [
                {"description": "neoneo: Mod3/Mod4 (Caps Lock state)", "manipulators": []}]}},
            {"name": "Default profile", "selected": True, "devices": devices,
             "complex_modifications": {"rules": [OTHER_RULE]}},
        ],
    }


class KarabinerConfigTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.rules = self.dir / "karabiner-neoneo.json"
        self.rules.write_text(json.dumps(RULES), encoding="utf-8")
        self.conf = self.dir / "karabiner.json"

    def run_tool(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["osascript", "-l", "JavaScript", str(SCRIPT), *args],
                              capture_output=True, text=True)

    def install(self, devices: list) -> dict:
        self.conf.write_text(json.dumps(config(devices)), encoding="utf-8")
        result = self.run_tool("install", str(self.rules), str(self.conf))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(self.conf.read_text(encoding="utf-8"))

    def test_install_puts_rules_first_in_selected_profile(self):
        data = self.install([])
        rules = data["profiles"][1]["complex_modifications"]["rules"]
        self.assertEqual(rules, RULES["rules"] + [OTHER_RULE])
        self.assertEqual(data["global"], {"show_in_menu_bar": True})

    def test_install_leaves_other_profiles_alone(self):
        data = self.install([])
        self.assertEqual(data["profiles"][0], config([])["profiles"][0])

    def test_reinstall_replaces_instead_of_duplicating(self):
        self.install([])
        result = self.run_tool("install", str(self.rules), str(self.conf))
        self.assertEqual(result.returncode, 0, result.stderr)
        rules = json.loads(self.conf.read_text())["profiles"][1]["complex_modifications"]["rules"]
        self.assertEqual([r["description"] for r in rules],
                         [r["description"] for r in RULES["rules"]] + [OTHER_RULE["description"]])

    def test_install_turns_off_caps_lock_led_on_swap_devices(self):
        existing = {"identifiers": {"is_keyboard": True, **ISO_SWAP_DEVICES[0]},
                    "simple_modifications": [{"from": {"key_code": "a"}, "to": [{"key_code": "b"}]}]}
        data = self.install([existing])
        devices = data["profiles"][1]["devices"]
        self.assertEqual(len(devices), len(ISO_SWAP_DEVICES))
        for ident in ISO_SWAP_DEVICES:
            entry = [d for d in devices if d["identifiers"]["vendor_id"] == ident["vendor_id"]
                     and d["identifiers"]["product_id"] == ident["product_id"]][0]
            self.assertIs(entry["manipulate_caps_lock_led"], False)
        self.assertEqual(devices[0]["simple_modifications"], existing["simple_modifications"])

    def test_uninstall_removes_rules_from_every_profile(self):
        self.install([])
        result = self.run_tool("uninstall", str(self.conf))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.conf.read_text())
        self.assertEqual(data["profiles"][0]["complex_modifications"]["rules"], [])
        self.assertEqual(data["profiles"][1]["complex_modifications"]["rules"], [OTHER_RULE])

    def test_missing_config_fails(self):
        result = self.run_tool("install", str(self.rules), str(self.dir / "missing.json"))
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
