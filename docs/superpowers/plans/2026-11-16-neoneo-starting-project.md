# neoneo starting project Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A working neoneo starting project in `~/Work/neoneo`: the Caps-state mechanism proven by a spike, one TSV as source of truth, and a generator that emits a macOS keylayout bundle and a Karabiner rule file.

**Architecture:** `layout/neoneo.tsv` lists every typing key with its six Neo layers. `neoneo.py` (Python 3 stdlib, one file) turns it plus `layout/option-de.tsv` into `build/neoneo.bundle` and `build/karabiner-neoneo.json`. Karabiner only handles the modifier keys and layer 4; the keylayout selects layers 3/5/6 from the Caps Lock state that Karabiner sets while Mod3/Mod4 are held.

**Tech Stack:** Python ≥3.9 stdlib (`unittest`, `xml.etree`, `plistlib`, `json`), Swift script (Xcode toolchain) for reading installed layouts, `just`, Karabiner-Elements, Nix only to fetch xkeyboard-config/xorgproto for the one-off import.

**Spec:** `docs/superpowers/specs/2026-11-16-neoneo-design.md`

## Global Constraints

- Python 3.9 compatible (the system `python3` is Xcode's 3.9): no `match`, use `from __future__ import annotations`.
- No third-party Python packages. Fail hard: raise on any unknown name, missing layer, duplicate key code; no defaults for required data.
- Input source id and bundle id: `com.mi-skam.keylayout.neoneo` (spike: `com.mi-skam.keylayout.neoneo-spike`). Layout name `neoneo`.
- Karabiner variables: `neoneo_mod3`, `neoneo_mod4`. Every manipulator carries `{"type": "input_source_if", "input_sources": [{"input_source_id": "^com\\.mi-skam\\.keylayout\\.neoneo$"}]}`.
- Mod3 keys: Caps Lock (tap = Escape, hold = Mod3) and the ISO key right of Ä. Mod4 keys: ISO key left of Y and `right_command`. Right Option stays Option.
- ⌘, Ctrl and Option follow Neo layer-1 letters.
- Dead keys emitted as their spacing characters; no Shift lock / Mod4 lock; ISO only.
- Never touch the official Neo bundle, the existing Neo2 Karabiner rules or `~/.config/home-manager`.
- `build/` is git-ignored. Commit after every task with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Keylayout modifier maps (decided here, used by Tasks 1 and 4)

`keyMapSelect` order = map index; first match wins.

| index | `modifier keys=`                              | content                          |
|-------|-----------------------------------------------|----------------------------------|
| 0     | `""`                                          | L1                               |
| 1     | `"anyShift"`                                  | L2                               |
| 2     | `"command anyShift? caps? anyOption? anyControl?"` | L1 (shortcuts by Neo letter) |
| 3     | `"anyControl anyShift? caps? anyOption?"`     | L1 letters a–z → U+0001–U+001A; other keys L1 |
| 4     | `"caps"`                                      | L3                               |
| 5     | `"caps anyShift"`                             | L5                               |
| 6     | `"caps anyOption"`                            | L6                               |
| 7     | `"caps anyShift anyOption"`                   | L4 characters (`@` entries → no output) |
| 8     | `"anyOption"`                                 | Option char of the key's L1 char |
| 9     | `"anyShift anyOption"`                        | Shift-Option char of the key's L1 char |

## Karabiner modifier manipulators (decided here, used by Tasks 1 and 5)

The key whose press turned Caps Lock on also turns it off on its release ("owner"); a second modifier never toggles Caps Lock. This makes a stuck Caps state impossible regardless of release order.

For each Mod3 key `k` (and symmetric for Mod4 with the variables swapped):

1. `k` down, `neoneo_mod3 = 0` and `neoneo_mod4 = 0` → `to: [set neoneo_mod3=1, caps_lock]`, `to_after_key_up: [set neoneo_mod3=0, caps_lock]` (owner).
2. `k` down, `neoneo_mod3 = 0` and `neoneo_mod4 = 1` → `to: [set neoneo_mod3=1, left_option]` (held while `k` is held), `to_after_key_up: [set neoneo_mod3=0]` (layer 6).
3. `k` down, `neoneo_mod3 = 1` → `to: [{"key_code": "vk_none"}]` (second Mod3 key is a no-op).

Caps Lock key only: variant 1 adds `to_if_alone: [escape]` and `parameters: {"basic.to_if_alone_timeout_milliseconds": 500}`. All `from` use `"modifiers": {"optional": ["any"]}`.

Layer-4 rules: condition `neoneo_mod4 = 1` and `neoneo_mod3 = 0`; `from` with `optional: ["any"]`. `@name` entries → `to: [{"key_code": NAV[name]}]`; character entries → `to: [{"key_code": <same key>, "modifiers": ["left_shift", "left_option"]}]`.

## Review Focus

- Mod3 and Mod4 released in either order → Caps Lock ends off. Test in Task 5: every manipulator that emits `caps_lock` in `to` emits it in `to_after_key_up` too, and no other manipulator emits `caps_lock`.
- Both Mod3 keys held together → no second toggle. Test in Task 5: the owner manipulator for each Mod3 key requires `neoneo_mod3 = 0`.
- ⌘ held together with Mod3 → shortcut letter unchanged. Test in Task 4: map 2 comes before map 4 and has `caps?`.
- Characters that need escaping (`<`, `>`, `&`, `"`, control characters) → valid keylayout. Test in Task 4: round-trip of those outputs.
- A layer marked `<none>` → the key has `output=""` in that map, not a missing `<key>`. Test in Task 4.

---

### Task 1: Scaffold, layout dump tool, spike

**Files:**
- Create: `.gitignore` (`build/`), `justfile`, `README.md` (stub: one paragraph + "see docs"), `tools/dump-layout.swift`, `spike/neoneo-spike.keylayout`, `spike/Info.plist`, `spike/karabiner-neoneo-spike.json`, `docs/quirks.md`

**Interfaces:**
- Produces: `swift tools/dump-layout.swift <input-source-id>` prints TSV lines `keycode<TAB>modifiers<TAB>output` for key codes 0–127 and modifier sets `none shift option shift+option caps caps+shift caps+option caps+shift+option command control`, output as `U+XXXX` sequences (empty if none). Uses `TISCreateInputSourceList` filtered by `kTISPropertyInputSourceID`, `kTISPropertyUnicodeKeyLayoutData`, `UCKeyTranslate` with `kUCKeyTranslateNoDeadKeysBit`. Exits non-zero if the id is not found.
- Produces: `justfile` recipes `test` (`python3 -m unittest discover -s tests -v`), `spike-install`, `spike-uninstall`, `dump id`.

- [ ] **Step 1:** Write `tools/dump-layout.swift`. Verify: `swift tools/dump-layout.swift com.apple.keylayout.German | awk -F'\t' '$1==37 && $2=="option"'` prints `37	option	U+0040` (Option+L = @).
- [ ] **Step 2:** Write the spike keylayout by hand: keys 0, 1, 2, 18 only, all ten maps from the table above, values from the TSV reference rows (code 0 = `u U \ @home <none> ⊂`, code 1 = `i I / @left ι ∫`, code 2 = `a A { @down α ∀`, code 18 = `1 ° ¹ ª ₁ ¬`; Option maps from the German dump for `u i a 1`). `spike/Info.plist` with `TISInputSourceID` = `com.mi-skam.keylayout.neoneo-spike`.
- [ ] **Step 3:** Write `spike/karabiner-neoneo-spike.json` with the modifier manipulators above (input source condition on the spike id) plus layer-4 rules for code 0 (`home`), code 1 (`left_arrow`), code 18 (`1` + shift+option). Mod3 keys: `caps_lock`, `non_us_pound`, `backslash`; Mod4 keys: `non_us_backslash`, `grave_accent_and_tilde`, `right_command` (all candidates; the spike narrows them). Verify: `python3 -m json.tool spike/karabiner-neoneo-spike.json >/dev/null`.
- [ ] **Step 4:** `just spike-install`: copy bundle to `~/Library/Keyboard Layouts/neoneo-spike.bundle`, JSON to `~/.config/karabiner/assets/complex_modifications/`. Then `swift tools/dump-layout.swift com.mi-skam.keylayout.neoneo-spike` after the operator logs out/in and adds the input source; check codes 0/1/2/18 against Step 2.
- [ ] **Step 5 (operator):** Enable the spike rule in Karabiner (Default profile), switch to the spike input source, run the checklist and record each result in `docs/quirks.md`:
  - fast typing of Mod3+u/i/a: `\ / {` every time, no uppercase leak, no delay
  - holding Mod3+i: `/` repeats
  - Shift+Mod3+i: `ι`; Mod3+Mod4+i (both orders, release both orders): `∫`, Caps Lock afterwards off
  - Mod4+i: cursor left; Shift+Mod4+i: selects; Mod4+1: `ª`
  - Caps tap: Escape, Caps state afterwards off; LED and Caps indicator pop-up: seen or not
  - ⌘ + the `a` key: select all (in TextEdit) also with Mod3 held; Ctrl + the `a` key in Terminal: line start; Option + the `u` key: what German Option+U gives
  - Karabiner-EventViewer on each keyboard (Apple 1452/835, Logitech 1133/50475, PC 1130/49304): names of the key left of 1, the key left of Y, the key right of Ä
- [ ] **Step 6:** Gate. If any check fails, stop and report to the operator with the quirks.md entry (fallback per spec: Option+Control pair). If all pass, record the confirmed Mod3/Mod4 key names and the swap devices in `docs/quirks.md`, `just spike-uninstall`, commit.

```bash
git add .gitignore justfile README.md tools/dump-layout.swift spike docs/quirks.md
git commit -m "spike: prove the Caps-state layer switch"
```

### Task 2: Import Neo2 into the TSV and load it

**Files:**
- Create: `tools/import-xkb.py`, `layout/neoneo.tsv`, `neoneo.py`, `tests/test_layout.py`

**Interfaces:**
- Produces in `neoneo.py`: `Key = NamedTuple("Key", [("code", int), ("name", str), ("layers", Tuple[str, str, str, str, str, str])])`; `NONE = ""`; `load_layout(path: Path) -> List[Key]` (decodes escapes, raises `ValueError` naming the line); `NAV: Dict[str, str]` (`@name` → Karabiner key_code); `is_nav(value: str) -> bool`.
- TSV format: `#` lines are comments; columns `code name L1 L2 L3 L4 L5 L6`, tab-separated; `name` = Karabiner `from.key_code`. Escapes: `<none>`, `<space>`, `<nbsp>`, `<nnbsp>`. `NAV` keys: `@home @end @left @right @up @down @pgup @pgdn @bksp @del @ins @esc @tab @ret @undo @kp0`…`@kp9 @kpdot @kpcomma @kpplus @kpminus @kpmul @kpdiv`. (`@undo` → `undo`, `@ins` → `insert`; rest the obvious `keypad_*`/arrow names.)
- `tools/import-xkb.py SYMBOLS_DE KEYSYMDEF_H OUT_TSV`: reads `xkb_symbols "neo_base"` from `SYMBOLS_DE`, keysym names → characters via the `/* U+XXXX … */` comments in `keysymdef.h` and `Uxxxx` names, `dead_*` → spacing character, `KP_*`/navigation keysyms → `@names`. xkb key → (code, name) table: AE01–AE10 → 18 19 20 21 23 22 26 28 25 29 / `1`…`0`; AE11 27 `hyphen`; AE12 24 `equal_sign`; AD01–AD12 → 12 13 14 15 17 16 32 34 31 35 33 30 / `q w e r t y u i o p open_bracket close_bracket`; AC01–AC11 → 0 1 2 3 5 4 38 40 37 41 39 / `a s d f g h j k l semicolon quote`; AB01–AB10 → 6 7 8 9 11 45 46 43 47 44 / `z x c v b n m comma period slash`; SPCE 49 `spacebar`; TLDE 10 `grave_accent_and_tilde` (adjust name per Task 1 findings). BKSL and LSGT are modifiers, not rows.
- xkb level → Neo layer mapping is whatever makes the reference rows below pass (expected: Neo L1..L6 ← xkb levels 1,2,3,5,4,7).

- [ ] **Step 1: failing tests** in `tests/test_layout.py`:

```python
def test_reference_rows(self):
    keys = {k.code: k for k in load_layout(TSV)}
    self.assertEqual(keys[18].layers, ("1", "°", "¹", "ª", "₁", "¬"))
    self.assertEqual(keys[0].layers, ("u", "U", "\\", "@home", NONE, "⊂"))
    self.assertEqual(keys[1].layers, ("i", "I", "/", "@left", "ι", "∫"))
    self.assertEqual(keys[49].layers[0], " ")
    self.assertEqual(len(keys), 47)
def test_unique_codes_and_names(self): ...
def test_every_nav_known(self): every layer value starting with "@" is in NAV
def test_bad_rows_fail(self):  # temp files: 7 columns, unknown @name, duplicate code, non-int code → ValueError
```

- [ ] **Step 2:** `just test` → FAIL (no module/TSV).
- [ ] **Step 3:** Implement `load_layout`, `NAV`, `is_nav`; write the importer; fetch sources with `nix build --no-link --print-out-paths nixpkgs#xkeyboard_config nixpkgs#xorg.xorgproto`, run the importer, check five rows by eye against https://www.neo-layout.org/ (layer 4 navigation block, Greek on layer 5).
- [ ] **Step 4:** `just test` → PASS.
- [ ] **Step 5:** Commit `tools/import-xkb.py layout/neoneo.tsv neoneo.py tests/test_layout.py` — "feat: Neo2 source table and loader".

### Task 3: Apple German Option table

**Files:**
- Create: `tools/option-table.py`, `layout/option-de.tsv`; Modify: `neoneo.py`; Test: `tests/test_layout.py`

**Interfaces:**
- `tools/option-table.py DUMP_TSV OUT_TSV`: from `dump-layout.swift com.apple.keylayout.German` output, write `char<TAB>option<TAB>shift_option` keyed by the German layer-1 (`none`) character, same escapes as neoneo.tsv.
- `load_option(path: Path) -> Dict[str, Tuple[str, str]]`.

- [ ] **Step 1: failing test** `test_option_reference`: `opt = load_option(OPTION_TSV)`; `opt["l"] == ("@", "ﬂ")`, `opt["5"][0] == "["`, `opt["e"][0] == "€"`.
- [ ] **Step 2:** run → FAIL. **Step 3:** implement, generate the TSV. **Step 4:** run → PASS (if a reference value differs, the dump is right; fix the test value from the dump and note it). **Step 5:** commit — "feat: Apple German Option table".

### Task 4: Keylayout and bundle

**Files:**
- Modify: `neoneo.py`; Test: `tests/test_keylayout.py`

**Interfaces:**
- `keylayout_xml(keys: List[Key], option: Dict[str, Tuple[str, str]]) -> str`: maps per the table above; `<keyboard group="126" id="-24601" name="neoneo" maxout="1">`; one `<layout first="0" last="255" mapSet="ANSI" modifiers="Modifiers"/>`; every key in every map has a `<key code= output=>` (empty for `<none>` and for `@` entries); non-printing and `<>&"'` written as `&#xXXXX;`.
- `write_bundle(out: Path, xml: str) -> Path`: `out/neoneo.bundle/Contents/{Info.plist, Resources/neoneo.keylayout}`; Info.plist via `plistlib` with `CFBundleIdentifier`, `CFBundleName` `neoneo`, `CFBundleVersion` `1`, `KLInfo_neoneo: {TISInputSourceID, TISIntendedLanguage: "de"}`.
- Test helper `parse_keylayout(text) -> Element` replaces `&#x…;` control references before `ET.fromstring` (Python rejects them).

- [ ] **Step 1: failing tests:** `test_maps_order` (ten `keyMapSelect`, modifier strings exactly as the table); `test_layers` (map 4 code 1 = `/`, map 5 code 1 = `ι`, map 6 code 1 = `∫`, map 7 code 18 = `ª`, map 7 code 1 = ``); `test_command_and_control_follow_neo` (map 2 code 1 = `i`, map 3 code 2 = `\x01`, map 3 code 18 = `1`); `test_option_by_neo_letter` (map 8 for the key whose L1 is `l` = `@`); `test_escaping` (synthetic Key with `<`, `&`, `"`, `\x01` round-trips); `test_none_is_empty_output` (every map has all 47 codes); `test_bundle_plist` (TISInputSourceID).
- [ ] **Step 2:** run → FAIL. **Step 3:** implement. **Step 4:** run → PASS. **Step 5:** commit — "feat: generate the neoneo keylayout bundle".

### Task 5: Karabiner rules

**Files:**
- Modify: `neoneo.py`; Test: `tests/test_karabiner.py`

**Interfaces:**
- Constants `MOD3_KEYS: List[str]`, `MOD4_KEYS: List[str]`, `ISO_SWAP_DEVICES: List[dict]` with values from `docs/quirks.md` (Task 1).
- `karabiner_rules(keys: List[Key]) -> dict`: `{"title": "neoneo", "rules": [modifiers_rule, layer4_rule]}` plus a swap rule (device_if per `ISO_SWAP_DEVICES`) only if that list is non-empty.

- [ ] **Step 1: failing tests:** `test_caps_toggle_paired` and `test_second_mod3_noop` (Review Focus); `test_caps_tap_escape` (Caps owner has `to_if_alone` escape, timeout 500); `test_layer6_holds_option` (variant 2 `to` contains `left_option`); `test_layer4_only` (one layer-4 manipulator per key with a non-`<none>` L4; nav → `NAV` key code, chars → same key + `["left_shift","left_option"]`; conditions `neoneo_mod4=1`, `neoneo_mod3=0`); `test_every_manipulator_has_input_source`; `test_manipulator_count` (layer-4 rule ≤ 47, modifier rule = 3 × (len(MOD3_KEYS)+len(MOD4_KEYS))).
- [ ] **Step 2:** run → FAIL. **Step 3:** implement; `python3 neoneo.py build [--out build]` writes the bundle and `build/karabiner-neoneo.json`. **Step 4:** run → PASS; `python3 neoneo.py build` succeeds. **Step 5:** commit — "feat: generate the neoneo Karabiner rules".

### Task 6: Install, verify, docs

**Files:**
- Modify: `justfile`, `README.md`, `docs/quirks.md`

- [ ] **Step 1:** `justfile` recipes `build`, `install` (build, copy bundle to `~/Library/Keyboard Layouts/`, JSON to `~/.config/karabiner/assets/complex_modifications/`, print: log out/in, add input source, enable rule), `uninstall`, `verify` (dump the installed `com.mi-skam.keylayout.neoneo` and compare with the TSV via `python3 neoneo.py verify DUMP`, non-zero on any mismatch).
- [ ] **Step 2:** Add `verify` subcommand: compares dump lines for maps none/shift/caps/caps+shift/caps+option/command/option against the generated expectations; test `test_verify_detects_mismatch` with a synthetic dump.
- [ ] **Step 3:** `README.md`: what, install, the modifier table, the hidden switch in five lines, link to the spec and quirks.
- [ ] **Step 4 (operator):** `just install`, log out/in, `just verify` → "ok"; repeat the Task 1 checklist on the full layout; record results in `docs/quirks.md`, kept separate from test results.
- [ ] **Step 5:** commit — "feat: install and verify neoneo".
