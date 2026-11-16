from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from neoneo import STATES, expected_rows, load_base, load_layout, load_option, verify  # noqa: E402

LAYOUT = ROOT / "layout"
ROWS = expected_rows(load_layout(LAYOUT / "neoneo.tsv"), load_option(LAYOUT / "option-de.tsv"),
                     load_base(LAYOUT / "apple-german.tsv"))


def dump_text(rows: dict) -> str:
    lines = []
    for code, outs in sorted(rows.items()):
        for state, out in zip(STATES, outs):
            lines.append(f"{code}\t{state}\t" + "".join(f"U+{ord(c):04X}" for c in out))
    return "\n".join(lines) + "\n"


def write(text: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return Path(f.name)


class VerifyTest(unittest.TestCase):
    def test_verify_accepts_matching_dump(self):
        self.assertEqual(verify(write(dump_text(ROWS)), ROWS), [])

    def test_verify_detects_mismatch(self):
        bad = {code: list(outs) for code, outs in ROWS.items()}
        bad[1][STATES.index("caps")] = "x"
        problems = verify(write(dump_text(bad)), ROWS)
        self.assertEqual(len(problems), 1)
        self.assertIn("1\tcaps", problems[0])

    def test_verify_detects_missing_key(self):
        short = {code: outs for code, outs in ROWS.items() if code != 1}
        self.assertTrue(verify(write(dump_text(short)), ROWS))


if __name__ == "__main__":
    unittest.main()
