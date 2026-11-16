from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from neoneo import NAV, NONE, load_layout, load_option  # noqa: E402

TSV = ROOT / "layout" / "neoneo.tsv"
OPTION_TSV = ROOT / "layout" / "option-de.tsv"


def write_tsv(text: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return Path(f.name)


class LayoutTest(unittest.TestCase):
    def test_reference_rows(self):
        keys = {k.code: k for k in load_layout(TSV)}
        self.assertEqual(keys[18].layers, ("1", "°", "¹", "ª", "₁", "¬"))
        self.assertEqual(keys[0].layers, ("u", "U", "\\", "@home", NONE, "⊂"))
        self.assertEqual(keys[1].layers, ("i", "I", "/", "@left", "ι", "∫"))
        self.assertEqual(keys[49].layers[0], " ")
        self.assertEqual(len(keys), 47)

    def test_keypad_comma_is_a_character(self):
        # HID keypad_comma becomes the JIS keypad key (code 95), which types
        # nothing on a German setup; layer 4 sends "," through map 7 instead.
        keys = {k.code: k for k in load_layout(TSV)}
        self.assertEqual(keys[41].layers[3], ",")
        self.assertNotIn("@kpcomma", NAV)

    def test_unique_codes_and_names(self):
        keys = load_layout(TSV)
        self.assertEqual(len({k.code for k in keys}), len(keys))
        self.assertEqual(len({k.name for k in keys}), len(keys))

    def test_every_nav_known(self):
        for k in load_layout(TSV):
            for v in k.layers:
                if len(v) > 1 and v.startswith("@"):
                    self.assertIn(v, NAV, f"{k.name}: {v}")

    def test_bad_rows_fail(self):
        good = "0\ta\tu\tU\t\\\t@home\t<none>\t⊂\n"
        bad = {
            "seven columns": "0\ta\tu\tU\t\\\t@home\t<none>\n",
            "unknown nav": "0\ta\tu\tU\t\\\t@nowhere\t<none>\t⊂\n",
            "duplicate code": good + "0\ts\ti\tI\t/\t@left\tι\t∫\n",
            "non-int code": "x\ta\tu\tU\t\\\t@home\t<none>\t⊂\n",
        }
        load_layout(write_tsv(good))
        for label, text in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    load_layout(write_tsv(text))

    def test_option_reference(self):
        opt = load_option(OPTION_TSV)
        self.assertEqual(opt["l"], ("@", "ﬂ"))
        self.assertEqual(opt["5"][0], "[")
        self.assertEqual(opt["e"][0], "€")


if __name__ == "__main__":
    unittest.main()
