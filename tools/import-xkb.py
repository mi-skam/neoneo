"""One-off import of Neo2 from xkeyboard-config into layout/neoneo.tsv.

usage: python3 tools/import-xkb.py SYMBOLS_DE KEYSYMDEF_H OUT_TSV

Neo layers 1..6 come from xkb levels 1, 2, 3, 5, 4, 7 (level 6 is Neo's
pseudo layer). Dead keys become their spacing characters; dead keys without
a spacing form become <none>. Navigation and keypad keysyms become @names.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# xkb key -> (macOS key code, Karabiner key_code name)
KEYS: Dict[str, Tuple[int, str]] = {
    "TLDE": (10, "grave_accent_and_tilde"),
    **{f"AE{i:02d}": (c, n) for i, (c, n) in enumerate(zip(
        [18, 19, 20, 21, 23, 22, 26, 28, 25, 29, 27, 24],
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "hyphen", "equal_sign"]), 1)},
    **{f"AD{i:02d}": (c, n) for i, (c, n) in enumerate(zip(
        [12, 13, 14, 15, 17, 16, 32, 34, 31, 35, 33, 30],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "open_bracket", "close_bracket"]), 1)},
    **{f"AC{i:02d}": (c, n) for i, (c, n) in enumerate(zip(
        [0, 1, 2, 3, 5, 4, 38, 40, 37, 41, 39],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l", "semicolon", "quote"]), 1)},
    **{f"AB{i:02d}": (c, n) for i, (c, n) in enumerate(zip(
        [6, 7, 8, 9, 11, 45, 46, 43, 47, 44],
        ["z", "x", "c", "v", "b", "n", "m", "comma", "period", "slash"]), 1)},
    "SPCE": (49, "spacebar"),
}

LEVELS = (1, 2, 3, 5, 4, 7)

NAV_KEYSYMS: Dict[str, str] = {
    "Home": "@home", "End": "@end", "Left": "@left", "Right": "@right",
    "Up": "@up", "Down": "@down", "Prior": "@pgup", "Next": "@pgdn",
    "BackSpace": "@bksp", "Delete": "@del", "Insert": "@ins",
    "Escape": "@esc", "Tab": "@tab", "Return": "@ret", "Undo": "@undo",
    **{f"KP_{d}": f"@kp{d}" for d in range(10)},
    "KP_Decimal": "@kpdot", "KP_Separator": "@kpcomma", "KP_Add": "@kpplus",
    "KP_Subtract": "@kpminus", "KP_Multiply": "@kpmul", "KP_Divide": "@kpdiv",
}

DEAD: Dict[str, str] = {
    "dead_circumflex": "^", "dead_caron": "ˇ", "dead_abovedot": "˙",
    "dead_grave": "`", "dead_cedilla": "¸", "dead_abovering": "˚",
    "dead_dasia": "῾", "dead_diaeresis": "¨", "dead_macron": "¯",
    "dead_acute": "´", "dead_tilde": "˜", "dead_psili": "᾿",
    "dead_doubleacute": "˝", "dead_breve": "˘",
    "dead_belowdot": "<none>", "dead_stroke": "<none>",
}

SPECIAL: Dict[str, str] = {
    "NoSymbol": "<none>", "space": "<space>", "nobreakspace": "<nbsp>",
}


def keysym_table(keysymdef: Path) -> Dict[str, str]:
    # Aliases carry no U+ comment, so resolve every name through its keysym value.
    by_value: Dict[str, str] = {}
    value_of: Dict[str, str] = {}
    pat = re.compile(r"^#define XK_(\w+)\s+(0x[0-9a-fA-F]+)(.*)$")
    for line in keysymdef.read_text(encoding="latin-1").splitlines():
        m = pat.match(line)
        if not m:
            continue
        name, value, rest = m.groups()
        value_of.setdefault(name, value)
        u = re.search(r"U\+([0-9A-Fa-f]{4,6})", rest)
        if u and value not in by_value:
            by_value[value] = chr(int(u.group(1), 16))
    return {n: by_value[v] for n, v in value_of.items() if v in by_value}


INVISIBLE: Dict[str, str] = {"\u202f": "<nnbsp>", "\u00a0": "<nbsp>", "\u00ad": "<shy>"}


def to_value(sym: str, table: Dict[str, str]) -> str:
    if sym in SPECIAL:
        return SPECIAL[sym]
    if sym in NAV_KEYSYMS:
        return NAV_KEYSYMS[sym]
    if sym in DEAD:
        return DEAD[sym]
    if re.fullmatch(r"U[0-9A-Fa-f]{4,6}", sym):
        ch = chr(int(sym[1:], 16))
        return {" ": "<nnbsp>", " ": "<nbsp>"}.get(ch, ch)
    if sym in table:
        return INVISIBLE.get(table[sym], table[sym])
    raise ValueError(f"unknown keysym {sym!r}")


def neo_base(symbols: str) -> Dict[str, List[str]]:
    m = re.search(r'xkb_symbols "neo_base" \{(.*?)\n\};', symbols, re.S)
    if not m:
        raise ValueError("neo_base section not found")
    rows: Dict[str, List[str]] = {}
    for key, body in re.findall(r"key\s*<(\w+)>\s*\{\s*\[([^\]]*)\]", m.group(1)):
        rows[key] = [s.strip() for s in body.split(",")]
    return rows


def main(symbols_de: str, keysymdef_h: str, out_tsv: str) -> None:
    table = keysym_table(Path(keysymdef_h))
    rows = neo_base(Path(symbols_de).read_text(encoding="utf-8"))
    lines = ["# code\tname\tL1\tL2\tL3\tL4\tL5\tL6",
             "# Imported once from xkeyboard-config symbols/de neo_base; edited by hand since."]
    for xkb, (code, name) in sorted(KEYS.items(), key=lambda kv: kv[1][0]):
        syms = rows[xkb]
        values = [to_value(syms[level - 1], table) for level in LEVELS]
        lines.append("\t".join([str(code), name, *values]))
    Path(out_tsv).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
