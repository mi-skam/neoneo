from __future__ import annotations

import plistlib
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from neoneo import Key, keylayout_xml, load_base, load_layout, load_option, write_bundle  # noqa: E402

KEYS = load_layout(ROOT / "layout" / "neoneo.tsv")
OPTION = load_option(ROOT / "layout" / "option-de.tsv")
BASE = load_base(ROOT / "layout" / "apple-german.tsv")

MODIFIERS = [
    "",
    "anyShift",
    "command anyShift? caps? anyOption? anyControl?",
    "anyControl anyShift? caps? anyOption?",
    "caps",
    "caps anyShift",
    "caps anyOption",
    "caps anyShift anyOption",
    "anyOption",
    "anyShift anyOption",
]


def parse_keylayout(text: str) -> ET.Element:
    """Python's XML parser rejects control-character references; swap them out."""
    def sub(m: re.Match) -> str:
        n = int(m.group(1), 16)
        return f"CTRL{n:04X}" if n < 0x20 or n == 0x7F else m.group(0)
    text = re.sub(r"&#x([0-9A-Fa-f]+);", sub, text).replace('version="1.1"', 'version="1.0"')
    return ET.fromstring(text)


def outputs(root: ET.Element, index: int) -> dict:
    km = root.find(f"./keyMapSet/keyMap[@index='{index}']")
    out = {}
    for k in km.findall("key"):
        v = k.get("output")
        out[int(k.get("code"))] = re.sub(r"CTRL([0-9A-F]{4})", lambda m: chr(int(m.group(1), 16)), v)
    return out


ROOT_EL = parse_keylayout(keylayout_xml(KEYS, OPTION, BASE))


class KeylayoutTest(unittest.TestCase):
    def test_maps_order(self):
        selects = ROOT_EL.findall("./modifierMap/keyMapSelect")
        self.assertEqual([int(s.get("mapIndex")) for s in selects], list(range(10)))
        self.assertEqual([s.find("modifier").get("keys") for s in selects], MODIFIERS)

    def test_header(self):
        self.assertEqual(ROOT_EL.get("name"), "neoneo")
        self.assertEqual(ROOT_EL.get("id"), "-24601")
        self.assertEqual(ROOT_EL.get("group"), "126")

    def test_layers(self):
        self.assertEqual(outputs(ROOT_EL, 4)[1], "/")
        self.assertEqual(outputs(ROOT_EL, 5)[1], "ι")
        self.assertEqual(outputs(ROOT_EL, 6)[1], "∫")
        self.assertEqual(outputs(ROOT_EL, 7)[18], "ª")
        self.assertEqual(outputs(ROOT_EL, 7)[1], "")

    def test_command_and_control_follow_neo(self):
        self.assertEqual(outputs(ROOT_EL, 2)[1], "i")
        self.assertEqual(outputs(ROOT_EL, 3)[2], "\x01")
        self.assertEqual(outputs(ROOT_EL, 3)[18], "1")

    def test_option_by_neo_letter(self):
        code_l = next(k.code for k in KEYS if k.layers[0] == "l")
        self.assertEqual(outputs(ROOT_EL, 8)[code_l], "@")
        self.assertEqual(outputs(ROOT_EL, 9)[code_l], "ﬂ")

    def test_escaping(self):
        key = Key(0, "a", ("<", "&", '"', "\x01", "'", ">"))
        root = parse_keylayout(keylayout_xml([key], {}, {}))
        self.assertEqual([outputs(root, i)[0] for i in (0, 1, 4, 5, 6)], ["<", "&", '"', "'", ">"])
        self.assertEqual(outputs(root, 7)[0], "\x01")

    def test_none_is_empty_output(self):
        codes = {k.code for k in KEYS}
        for i in range(10):
            with self.subTest(map=i):
                self.assertLessEqual(codes, set(outputs(ROOT_EL, i)))
        self.assertEqual(outputs(ROOT_EL, 5)[0], "")

    def test_caret_key_on_both_iso_codes(self):
        for i in range(10):
            self.assertEqual(outputs(ROOT_EL, i)[10], outputs(ROOT_EL, i)[50])
        self.assertEqual(outputs(ROOT_EL, 0)[50], "^")

    def test_other_keys_from_apple_german(self):
        self.assertEqual(outputs(ROOT_EL, 0)[36], "\r")
        self.assertEqual(outputs(ROOT_EL, 0)[123], BASE[(123, "none")])

    def test_write_bundle_drops_stale_files(self):
        out = Path(tempfile.mkdtemp())
        icns = out / "in.icns"
        icns.write_bytes(b"icns")
        stale = out / "neoneo.bundle" / "Contents" / "Resources" / "old.keylayout"
        stale.parent.mkdir(parents=True)
        stale.write_text("old", encoding="utf-8")
        write_bundle(out, "<keyboard/>", icns)
        self.assertFalse(stale.exists())

    def test_write_bundle(self):
        out = Path(tempfile.mkdtemp())
        icns = out / "in.icns"
        icns.write_bytes(b"icns")
        bundle = write_bundle(out, "<keyboard/>", icns)
        self.assertEqual(bundle, out / "neoneo.bundle")
        res = bundle / "Contents" / "Resources"
        self.assertEqual((res / "neoneo.keylayout").read_text(encoding="utf-8"), "<keyboard/>")
        self.assertEqual((res / "neoneo.icns").read_bytes(), b"icns")
        self.assertTrue((res / "de.lproj" / "InfoPlist.strings").exists())
        info = plistlib.loads((bundle / "Contents" / "Info.plist").read_bytes())
        # macOS only loads layout bundles whose identifier contains ".keyboardlayout."
        # (Apple TN2056); the spike's and the first v0.1 bundle were ignored without it.
        self.assertEqual(info["CFBundleIdentifier"], "xyz.miskam.keyboardlayout.neoneo")
        # macOS ignores KLInfo TISInputSourceID and derives the input source id as
        # <bundle id>.keylayout.<name>, so the bundle does not set one.
        self.assertEqual(info["KLInfo_neoneo"], {
            "TISIntendedLanguage": "de",
            "TISIconIsTemplate": True,
        })

if __name__ == "__main__":
    unittest.main()
