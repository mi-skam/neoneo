from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from neoneo import (  # noqa: E402
    ISO_SWAP_DEVICES, MOD3_KEYS, MOD4_KEYS, NAV, is_nav, karabiner_rules, load_layout,
)

KEYS = load_layout(ROOT / "layout" / "neoneo.tsv")
RULES = karabiner_rules(KEYS)
MODS, LAYER4 = RULES["rules"]
INPUT_SOURCE = {"type": "input_source_if",
                "input_sources": [{"input_source_id": "^org\\.unknown\\.keylayout\\.neoneo$"}]}


def var(name: str, value: int) -> dict:
    return {"type": "variable_if", "name": name, "value": value}


def emits_caps(events: list) -> bool:
    return any(e.get("key_code") == "caps_lock" for e in events)


def from_key(m: dict) -> str:
    return m["from"]["key_code"]


class KarabinerTest(unittest.TestCase):
    def test_caps_toggle_paired(self):
        for m in MODS["manipulators"] + LAYER4["manipulators"]:
            if emits_caps(m.get("to", [])):
                self.assertTrue(emits_caps(m["to_after_key_up"]), from_key(m))
            else:
                self.assertFalse(emits_caps(m.get("to_after_key_up", [])), from_key(m))
        for m in LAYER4["manipulators"]:
            self.assertFalse(emits_caps(m["to"]))

    def test_second_mod3_noop(self):
        for k in MOD3_KEYS:
            ms = [m for m in MODS["manipulators"] if from_key(m) == k]
            owner = [m for m in ms if emits_caps(m["to"])]
            self.assertEqual(len(owner), 1, k)
            self.assertIn(var("neoneo_mod3", 0), owner[0]["conditions"])
            self.assertIn(var("neoneo_mod4", 0), owner[0]["conditions"])
            noop = [m for m in ms if var("neoneo_mod3", 1) in m["conditions"]]
            self.assertEqual([n["to"] for n in noop], [[{"key_code": "vk_none"}]], k)

    def test_caps_tap_escape(self):
        owner = [m for m in MODS["manipulators"] if from_key(m) == "caps_lock" and emits_caps(m["to"])][0]
        self.assertEqual(owner["to_if_alone"], [{"key_code": "escape"}])
        self.assertEqual(owner["parameters"], {"basic.to_if_alone_timeout_milliseconds": 500})
        others = [m for m in MODS["manipulators"] if m is not owner]
        self.assertFalse(any("to_if_alone" in m for m in others))

    def test_layer6_holds_option(self):
        for k in MOD3_KEYS:
            m = [m for m in MODS["manipulators"]
                 if from_key(m) == k and var("neoneo_mod4", 1) in m["conditions"]][0]
            self.assertIn({"key_code": "left_option"}, m["to"])
            self.assertEqual(m["to_after_key_up"], [{"set_variable": {"name": "neoneo_mod3", "value": 0}}])

    def test_layer4(self):
        by_from = {}
        for m in LAYER4["manipulators"]:
            self.assertIn(var("neoneo_mod4", 1), m["conditions"])
            self.assertIn(var("neoneo_mod3", 0), m["conditions"])
            self.assertEqual(m["from"]["modifiers"], {"optional": ["any"]})
            by_from.setdefault(from_key(m), []).append(m)
        for key in KEYS:
            m = by_from[key.name][0]
            l4 = key.layers[3]
            if is_nav(l4):
                self.assertEqual(m["to"], [{"key_code": NAV[l4]}], key.name)
            else:
                self.assertEqual(m["to"], [{"key_code": key.name, "modifiers": ["left_shift", "left_option"]}],
                                 key.name)

    def test_swap_devices(self):
        devices = {"identifiers": ISO_SWAP_DEVICES}
        mod4 = {from_key(m): m for m in MODS["manipulators"] if from_key(m) in MOD4_KEYS}
        self.assertIn({"type": "device_unless", **devices}, mod4["non_us_backslash"]["conditions"])
        self.assertIn({"type": "device_if", **devices}, mod4["grave_accent_and_tilde"]["conditions"])
        caret = [m for m in LAYER4["manipulators"] if m["to"][0].get("key_code") in
                 ("grave_accent_and_tilde", "non_us_backslash")]
        pairs = {(from_key(m), m["conditions"][-1]["type"]) for m in caret}
        self.assertEqual(pairs, {("grave_accent_and_tilde", "device_unless"),
                                 ("non_us_backslash", "device_if")})
        for m in caret:
            self.assertEqual(m["to"][0]["key_code"], from_key(m))

    def test_every_manipulator_has_input_source(self):
        for m in MODS["manipulators"] + LAYER4["manipulators"]:
            self.assertEqual(m["conditions"][0], INPUT_SOURCE)
            self.assertEqual(m["type"], "basic")
            self.assertEqual(m["from"]["modifiers"], {"optional": ["any"]})

    def test_manipulator_count(self):
        self.assertEqual(len(MODS["manipulators"]), 3 * (len(MOD3_KEYS) + len(MOD4_KEYS)))
        self.assertEqual(len(LAYER4["manipulators"]), len(KEYS) + 1)  # + the swapped ^ key

    def test_title(self):
        self.assertEqual(RULES["title"], "neoneo")
        self.assertEqual(len(RULES["rules"]), 2)


if __name__ == "__main__":
    unittest.main()
