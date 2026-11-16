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


def load_option(path: Path) -> Dict[str, Tuple[str, str]]:
    table: Dict[str, Tuple[str, str]] = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        where = f"{path}:{n}"
        cols = line.split("\t")
        if len(cols) != 3:
            raise ValueError(f"{where}: expected 3 columns, got {len(cols)}")
        char, option, shift_option = (_decode(v, where) for v in cols)
        if char in table:
            raise ValueError(f"{where}: duplicate character {char!r}")
        table[char] = (option, shift_option)
    return table


# Apple German dump states, in keylayout map-index order (see the plan's map table).
STATES = [
    "none", "shift", "command", "control", "caps",
    "caps+shift", "caps+option", "caps+shift+option", "option", "shift+option",
]

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

# Apple ISO keyboards send the ^ key as code 10, others as code 50; the other
# code is the < key, which Karabiner owns as Mod4. Emit the ^ row at both.
ALIASES: Dict[int, int] = {10: 50}


def load_base(path: Path) -> Dict[Tuple[int, str], str]:
    """Read a dump-layout.swift TSV: (key code, state) -> output."""
    base: Dict[Tuple[int, str], str] = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        cols = line.split("\t")
        if len(cols) != 3:
            raise ValueError(f"{path}:{n}: expected 3 columns, got {len(cols)}")
        base[(int(cols[0]), cols[1])] = "".join(chr(int(p, 16)) for p in cols[2].split("U+") if p)
    return base


def _control(l1: str) -> str:
    if len(l1) == 1 and "a" <= l1 <= "z":
        return chr(ord(l1) - ord("a") + 1)
    return l1


def _maps_for(key: Key, option: Dict[str, Tuple[str, str]]) -> List[str]:
    l1, l2, l3, l4, l5, l6 = key.layers
    opt, shift_opt = option.get(l1, (NONE, NONE))
    return [
        l1, l2, l1, _control(l1), l3, l5, l6,
        NONE if is_nav(l4) else l4,
        opt, shift_opt,
    ]


def _xml_escape(s: str) -> str:
    return "".join(
        f"&#x{ord(c):04X};" if ord(c) < 0x20 or ord(c) == 0x7F or c in "<>&\"'" else c
        for c in s
    )


def keylayout_xml(
    keys: List[Key],
    option: Dict[str, Tuple[str, str]],
    base: Dict[Tuple[int, str], str],
) -> str:
    rows: Dict[int, List[str]] = {}
    for key in keys:
        rows[key.code] = _maps_for(key, option)
        if key.code in ALIASES:
            rows[ALIASES[key.code]] = rows[key.code]
    for code in sorted({c for c, _ in base} - set(rows)):
        rows[code] = [base[(code, s)] for s in STATES]
    maxout = max(len(v.encode("utf-16-le")) // 2 for r in rows.values() for v in r)
    lines = [
        '<?xml version="1.1" encoding="UTF-8"?>',
        '<!DOCTYPE keyboard SYSTEM "file://localhost/System/Library/DTDs/KeyboardLayout.dtd">',
        f'<keyboard group="126" id="-24601" name="neoneo" maxout="{max(maxout, 1)}">',
        "  <layouts>",
        '    <layout first="0" last="255" mapSet="ANSI" modifiers="Modifiers"/>',
        "  </layouts>",
        '  <modifierMap id="Modifiers" defaultIndex="0">',
    ]
    for i, mods in enumerate(MODIFIERS):
        lines.append(f'    <keyMapSelect mapIndex="{i}"><modifier keys="{mods}"/></keyMapSelect>')
    lines += ["  </modifierMap>", '  <keyMapSet id="ANSI">']
    for i in range(len(MODIFIERS)):
        lines.append(f'    <keyMap index="{i}">')
        for code in sorted(rows):
            lines.append(f'      <key code="{code}" output="{_xml_escape(rows[code][i])}"/>')
        lines.append("    </keyMap>")
    lines += ["  </keyMapSet>", "</keyboard>", ""]
    return "\n".join(lines)


def write_keylayout(out: Path, xml: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    path = out / "neoneo.keylayout"
    path.write_text(xml, encoding="utf-8")
    return path
