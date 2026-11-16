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


def expected_rows(
    keys: List[Key],
    option: Dict[str, Tuple[str, str]],
    base: Dict[Tuple[int, str], str],
) -> Dict[int, List[str]]:
    """Key code -> output per map index (same order as STATES)."""
    rows: Dict[int, List[str]] = {}
    for key in keys:
        rows[key.code] = _maps_for(key, option)
        if key.code in ALIASES:
            rows[ALIASES[key.code]] = rows[key.code]
    for code in sorted({c for c, _ in base} - set(rows)):
        rows[code] = [base[(code, s)] for s in STATES]
    return rows


def keylayout_xml(
    keys: List[Key],
    option: Dict[str, Tuple[str, str]],
    base: Dict[Tuple[int, str], str],
) -> str:
    rows = expected_rows(keys, option, base)
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


# macOS only loads layout bundles whose identifier contains ".keyboardlayout."
# (Apple TN2056), and it derives the input source id as <bundle id>.keylayout.<name>
# (KLInfo TISInputSourceID is ignored).
BUNDLE_ID = "xyz.miskam.keyboardlayout.neoneo"
INPUT_SOURCE = BUNDLE_ID + ".keylayout.neoneo"
VERSION = "0.1.2"


def write_bundle(out: Path, xml: str, icns: Path) -> Path:
    """Write out/neoneo.bundle, modelled on the official Neo bundle."""
    import plistlib
    import shutil

    bundle = out / "neoneo.bundle"
    if bundle.exists():
        shutil.rmtree(bundle)  # no stale files from older builds
    res = bundle / "Contents" / "Resources"
    (res / "de.lproj").mkdir(parents=True, exist_ok=True)
    (res / "neoneo.keylayout").write_text(xml, encoding="utf-8")
    shutil.copyfile(icns, res / "neoneo.icns")
    (res / "de.lproj" / "InfoPlist.strings").write_text('"neoneo" = "neoneo";\n', encoding="utf-16")
    info = {
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleName": "neoneo",
        "CFBundleVersion": VERSION,
        "CFBundleShortVersionString": VERSION,
        # No TICapsLockLanguageSwitchCapable: with it set to false, macOS drops the
        # short Caps Lock press that turns Mod3 off, so Caps Lock sticks.
        "KLInfo_neoneo": {
            "TISIntendedLanguage": "de",
            "TISIconIsTemplate": True,
        },
    }
    (bundle / "Contents" / "Info.plist").write_bytes(plistlib.dumps(info))
    return bundle


# Values from docs/quirks.md (mechanism checks, 2026-11-16).
MOD3_KEYS: List[str] = ["caps_lock", "backslash", "non_us_pound"]
MOD4_KEYS: List[str] = ["non_us_backslash", "grave_accent_and_tilde", "right_command"]
# Apple ISO keyboards report the ^ key as non_us_backslash and the < key as
# grave_accent_and_tilde.
ISO_SWAP_DEVICES: List[dict] = [
    {"vendor_id": 1452, "product_id": 835},  # Apple internal
    {"vendor_id": 76, "product_id": 615},  # Apple Magic Keyboard, Bluetooth
]
INPUT_SOURCE_ID = "^" + INPUT_SOURCE.replace(".", "\\.") + "$"
CARET_KEY = "grave_accent_and_tilde"
SWAPPED_CARET_KEY = "non_us_backslash"


def _input_source() -> dict:
    return {"type": "input_source_if", "input_sources": [{"input_source_id": INPUT_SOURCE_ID}]}


def _var(name: str, value: int) -> dict:
    return {"type": "variable_if", "name": name, "value": value}


def _devices(kind: str) -> dict:
    return {"type": kind, "identifiers": ISO_SWAP_DEVICES}


# Which keyboards a modifier key name is that modifier on.
MOD_DEVICE: Dict[str, str] = {
    "non_us_backslash": "device_unless",
    "grave_accent_and_tilde": "device_if",
}


def _manipulator(key: str, conditions: List[dict], **events) -> dict:
    return {
        "type": "basic",
        "from": {"key_code": key, "modifiers": {"optional": ["any"]}},
        "conditions": [_input_source(), *conditions],
        **events,
    }


def _modifier_manipulators(key: str, mine: str, other: str) -> List[dict]:
    device = [_devices(MOD_DEVICE[key])] if key in MOD_DEVICE else []
    owner = dict(
        to=[{"set_variable": {"name": mine, "value": 1}}, {"key_code": "caps_lock"}],
        to_after_key_up=[{"set_variable": {"name": mine, "value": 0}}, {"key_code": "caps_lock"}],
    )
    if key == "caps_lock":
        owner["to_if_alone"] = [{"key_code": "escape"}]
        owner["parameters"] = {"basic.to_if_alone_timeout_milliseconds": 500}
    return [
        _manipulator(key, [_var(mine, 0), _var(other, 0), *device], **owner),
        _manipulator(
            key, [_var(mine, 0), _var(other, 1), *device],
            to=[{"set_variable": {"name": mine, "value": 1}}, {"key_code": "left_option"}],
            to_after_key_up=[{"set_variable": {"name": mine, "value": 0}}],
        ),
        _manipulator(key, [_var(mine, 1), *device], to=[{"key_code": "vk_none"}]),
    ]


def _layer4_manipulator(key: Key, name: str, extra: List[dict]) -> dict:
    l4 = key.layers[3]
    # Non-nav keys, including <none>, go through keylayout map 7 (caps+shift+option),
    # which holds the layer-4 characters; without a rule Mod4's caps state would
    # type layer 3.
    to = [{"key_code": NAV[l4]}] if is_nav(l4) else [
        {"key_code": name, "modifiers": ["left_shift", "left_option"]}]
    return _manipulator(name, [_var("neoneo_mod4", 1), _var("neoneo_mod3", 0), *extra], to=to)


def karabiner_rules(keys: List[Key]) -> dict:
    mods: List[dict] = []
    for k in MOD3_KEYS:
        mods += _modifier_manipulators(k, "neoneo_mod3", "neoneo_mod4")
    for k in MOD4_KEYS:
        mods += _modifier_manipulators(k, "neoneo_mod4", "neoneo_mod3")
    layer4: List[dict] = []
    for key in keys:
        if key.name == CARET_KEY:
            layer4.append(_layer4_manipulator(key, CARET_KEY, [_devices("device_unless")]))
            layer4.append(_layer4_manipulator(key, SWAPPED_CARET_KEY, [_devices("device_if")]))
        else:
            layer4.append(_layer4_manipulator(key, key.name, []))
    return {
        "title": "neoneo",
        "rules": [
            {"description": "neoneo: Mod3/Mod4 (Caps Lock state)", "manipulators": mods},
            {"description": "neoneo: layer 4", "manipulators": layer4},
        ],
    }


def verify(dump: Path, rows: Dict[int, List[str]]) -> List[str]:
    """Compare a dump of the installed layout with the expected rows."""
    got = load_base(dump)
    problems: List[str] = []
    for code, outs in sorted(rows.items()):
        for state, want in zip(STATES, outs):
            if (code, state) not in got:
                problems.append(f"{code}\t{state}\tmissing from dump")
            elif got[(code, state)] != want:
                problems.append(f"{code}\t{state}\twant {want!r}, got {got[(code, state)]!r}")
    return problems


def _sources() -> Tuple[List[Key], Dict[str, Tuple[str, str]], Dict[Tuple[int, str], str]]:
    layout = ROOT / "layout"
    return (load_layout(layout / "neoneo.tsv"), load_option(layout / "option-de.tsv"),
            load_base(layout / "apple-german.tsv"))


def build(out: Path) -> None:
    import json

    keys, option, base = _sources()
    xml = keylayout_xml(keys, option, base)
    write_bundle(out, xml, ROOT / "layout" / "neoneo.icns")
    (out / "karabiner-neoneo.json").write_text(
        json.dumps(karabiner_rules(keys), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dist(out: Path, helper: Path) -> Path:
    """Assemble the release folder out/neoneo-<VERSION> from scratch.

    helper is the compiled neoneo-capslockdelay (built by `make helper`)."""
    import shutil

    folder = out / f"neoneo-{VERSION}"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    build(folder)
    shutil.copyfile(ROOT / "tools" / "neoneo.capslockdelay.plist", folder / "neoneo.capslockdelay.plist")
    shutil.copyfile(ROOT / "README.md", folder / "README.md")
    shutil.copyfile(ROOT / "tools" / "karabiner-config.js", folder / "karabiner-config.js")
    shutil.copyfile(helper, folder / "neoneo-capslockdelay")
    (folder / "neoneo-capslockdelay").chmod(0o755)
    for script in ("install.sh", "uninstall.sh", "remove-input-source.sh"):
        shutil.copyfile(ROOT / "tools" / script, folder / script)
        (folder / script).chmod(0o755)
    return folder


ROOT = Path(__file__).resolve().parent


def main(argv: List[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="neoneo.py")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="write neoneo.bundle and karabiner-neoneo.json")
    b.add_argument("--out", type=Path, required=True)
    d = sub.add_parser("dist", help="assemble the release folder neoneo-<version>")
    d.add_argument("--out", type=Path, required=True)
    d.add_argument("--helper", type=Path, required=True)
    v = sub.add_parser("verify", help="compare a dump-layout.swift dump with the TSV")
    v.add_argument("dump", type=Path)
    sub.add_parser("version", help="print the version")
    args = parser.parse_args(argv)
    if args.command == "build":
        build(args.out)
        return 0
    if args.command == "dist":
        print(dist(args.out, args.helper))
        return 0
    if args.command == "version":
        print(VERSION)
        return 0
    problems = verify(args.dump, expected_rows(*_sources()))
    for p in problems:
        print(p)
    if problems:
        print(f"{len(problems)} mismatches")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
