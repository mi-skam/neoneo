"""neoneo: generate a macOS keylayout and Karabiner rules for Neo2 from one TSV."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple

NONE = ""

ESCAPES: Dict[str, str] = {
    "<none>": NONE,
    "<space>": " ",
    "<nbsp>": "\u00a0",
    "<nnbsp>": "\u202f",
    "<shy>": "\u00ad",
}

# Layer-4 navigation names -> Karabiner key_code.
NAV: Dict[str, str] = {
    "@home": "home",
    "@end": "end",
    "@left": "left_arrow",
    "@right": "right_arrow",
    "@up": "up_arrow",
    "@down": "down_arrow",
    "@pgup": "page_up",
    "@pgdn": "page_down",
    "@bksp": "delete_or_backspace",
    "@del": "delete_forward",
    "@ins": "insert",
    "@esc": "escape",
    "@tab": "tab",
    "@ret": "return_or_enter",
    "@undo": "undo",
    **{f"@kp{d}": f"keypad_{d}" for d in range(10)},
    "@kpdot": "keypad_period",
    "@kpcomma": "keypad_comma",
    "@kpplus": "keypad_plus",
    "@kpminus": "keypad_hyphen",
    "@kpmul": "keypad_asterisk",
    "@kpdiv": "keypad_slash",
}


class Key(NamedTuple):
    code: int
    name: str
    layers: Tuple[str, str, str, str, str, str]


def is_nav(value: str) -> bool:
    return value in NAV


def _decode(value: str, where: str) -> str:
    if value in ESCAPES:
        return ESCAPES[value]
    if len(value) > 1 and value.startswith("@") and value not in NAV:
        raise ValueError(f"{where}: unknown navigation name {value!r}")
    if value.startswith("<") and value.endswith(">") and len(value) > 2:
        raise ValueError(f"{where}: unknown escape {value!r}")
    return value


def load_layout(path: Path) -> List[Key]:
    keys: List[Key] = []
    codes = set()
    names = set()
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        where = f"{path}:{n}"
        cols = line.split("\t")
        if len(cols) != 8:
            raise ValueError(f"{where}: expected 8 columns, got {len(cols)}")
        try:
            code = int(cols[0])
        except ValueError:
            raise ValueError(f"{where}: key code {cols[0]!r} is not an integer") from None
        name = cols[1]
        if code in codes:
            raise ValueError(f"{where}: duplicate key code {code}")
        if name in names:
            raise ValueError(f"{where}: duplicate key name {name}")
        codes.add(code)
        names.add(name)
        l1, l2, l3, l4, l5, l6 = (_decode(v, where) for v in cols[2:])
        keys.append(Key(code, name, (l1, l2, l3, l4, l5, l6)))
    return keys
