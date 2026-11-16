# neoneo: design

Date: 2026-11-16. Status: draft for approval.

## Intent

neoneo is the Neo2 layout for macOS, rebuilt so it
behaves like any other macOS keyboard layout. Today's setup (the official
`Deutsch (Neo 2).keylayout` plus 72 hand-written Karabiner rules in
`~/.config/home-manager/macos/karabiner.json`) has these quirks:

- Option is spent on Neo layer 3, so Option and Option+Shift shortcuts and the
  usual macOS Option behaviour are gone (Zed needed a workaround for it).
- Shortcuts follow two rules: ⌘ uses Neo letters, Ctrl uses QWERTZ positions,
  so the same key means different letters depending on the modifier.
- macOS layouts know only Shift, Option, Caps Lock, Command, Control; Neo needs
  two more modifiers (Mod3, Mod4).

The task now is in `~/Work/neoneo`: the mechanism
proven, the source of truth and generator in place, tests, docs. Not a
finished, polished layout.

## Goals

- Option, Command, Control behave as on every macOS layout. Option keeps the
  standard Apple German Option characters.
- ⌘ and Ctrl both follow Neo letters (⌘C = the key that types `c` in Neo),
  like Dvorak/Colemak on macOS.
- Neo layers 1–6 with the standard Neo modifier keys:
  Mod3 = Caps Lock and the ISO key right of Ä (`#`, macOS key code 42);
  Mod4 = the ISO key left of Y (`<`) and Right Command (the AltGr position on
  Mac keyboards). Right Option stays Option.
- Lean and fast: one data file is the source of truth; a generator emits both
  the keylayout and the Karabiner rules; as few Karabiner manipulators as
  possible on the typing path.

## Non-goals (for v0.1)

- Dead keys (Neo's `^ ` ´` keys and their layers): next step after v0.1
- They are emitted as plain characters until then. (My call.)
- Shift lock (both Shifts) and Mod4 lock. (My call, next step.)
- home-manager/Nix integration, a flake, other layouts (3l, Bone, …).
- ANSI keyboards (no `<` key); ISO only.

## Anti-goals

- Anything that makes typing feel laggy, drops or reorders keys, or breaks key
  repeat.
- Karabiner shelling out (`shell_command`, osascript) to type characters.
- Changing the existing `neo2` profile or the official Neo bundle; neoneo
  installs side by side.

## Constraints

- A keylayout maps (key code, modifier state) to output. It distinguishes only
  shift, option, caps lock, command, control; it does not see left/right.
- Karabiner cannot type arbitrary Unicode; it sends key codes and modifiers
  that the active keylayout turns into characters.
- New or changed keylayouts in `~/Library/Keyboard Layouts` are picked up after
  logging out and in.
- Apple ISO keyboards report the `^` key and the `<` key with swapped key codes
  (10/50) relative to other ISO keyboards; the existing config swaps them in
  Karabiner.

## Approach

**One data file + generator** (chosen). A table lists each physical key with
its six Neo layers; a Python script generates the `.keylayout` bundle and
the Karabiner rules; tests check the invariants. Changing a character is a
one-line edit and both outputs follow.


## Mechanism: the hidden switch

Karabiner signals Mod3/Mod4 to the keylayout through modifier states nobody
types by hand. The physical Caps Lock key is Mod3, so the Caps Lock *state* is
free to serve as the switch:

| Held (physical) | Karabiner sets         | Keylayout map selected                         | Layer |
| --------------- | ---------------------- | ---------------------------------------------- | ----- |
| —               | —                      | none                                           | 1     |
| Shift           | —                      | anyShift                                       | 2     |
| Mod3            | caps on                | caps                                           | 3     |
| Mod4            | caps on; per-key rules | nav: key codes; chars: caps+anyShift+anyOption | 4     |
| Shift+Mod3      | caps on                | caps+anyShift                                  | 5     |
| Mod3+Mod4       | caps on + Option held  | caps+anyOption                                 | 6     |
| Option (±Shift) | —                      | anyOption (Apple German)                       | —     |
| ⌘ / Ctrl (any)  | —                      | command / control: Neo letters                 | —     |

Consequences:

- Layers 3, 5 and 6 need **no per-key Karabiner rules**: keys pass through,
  the keylayout picks the character from the caps state. Only the modifier
  keys (≈6 manipulators) and layer 4 (≈30: navigation keys as key codes,
  digits as keypad codes, the rest as key + Shift+Option with caps on) are
  Karabiner rules.
- The command and control maps are written with `caps?` so a held Mod3 never
  changes what a shortcut means.
- All Karabiner rules are conditioned on the neoneo input source being active,
  so other layouts are untouched.

The mechanism must be proven first (see Spike). Open risks it must answer:
Caps Lock delay or races when Karabiner toggles the state (does the next key
already see caps on?), the macOS Caps Lock indicator popping up near the
cursor on every Mod3 press, the LED flicker (`manipulate_caps_lock_led`), key
repeat while Mod3 is held, and the Apple ISO 10/50 swap. Fallback if the caps
state does not work: map Mod3 to a held Option+Control pair in the keylayout
(costs Ctrl+Option shortcuts; decided with the operator then).

## Project layout

```
~/Work/neoneo/
  README.md            what it is, install, the hidden switch in five lines
  makefile            build, test, install, uninstall, spike-install
  layout/neoneo.tsv    source of truth (below)
  neoneo.py            generator, Python 3 stdlib only, one file
  tests/test_neoneo.py unittest
  spike/               hand-written minimal keylayout + Karabiner rule (3 keys)
  docs/quirks.md       the macOS quirks and how neoneo handles each
  docs/superpowers/specs/  this design
  build/               generated, git-ignored
```

- `layout/neoneo.tsv`: one row per physical key, tab-separated:
  macOS key code, a name, then layers 1–6. Characters are literal; a few
  escapes for invisibles (`<space>`, `<nbsp>`, `<tab>`). Layer-4 navigation
  entries are names (`@left`, `@pgup`, `@kp7`, `@bksp`, …) that the generator
  turns into Karabiner key codes. A `-` means "no character".
  Initial content is imported once from xkeyboard-config's `symbols/de`
  (`neo_base`) by a one-off script kept in `tools/import-xkb.py`, then checked
  against https://www.neo-layout.org/; from then on the TSV is edited by hand.
- `neoneo.py build` writes `build/neoneo.bundle` (Info.plist, keylayout, icon
  optional) and `build/karabiner-neoneo.json` (one complex-modification file).
  The Option map is copied from Apple's German layout mapping, kept as a
  second table `layout/option-de.tsv`. Fails hard on unknown names, missing
  layers or duplicate key codes.
- `make install` copies the bundle to `~/Library/Keyboard Layouts/` and the
  JSON to `~/.config/karabiner/assets/complex_modifications/`, then says to
  log out/in and enable the rule in Karabiner. `make uninstall` reverses it.

## Tests (stdlib unittest, run by `make test`)

- TSV: every row has six layers, unique key codes, every `@name` known.
- Generated keylayout parses as XML and has the maps in the table above.
- ⌘ and Ctrl maps: each letter key outputs its Neo layer-1 letter
  (control map: the matching control character).
- Layer-4 rules exist only for layer-4 entries; layers 3/5/6 produce no
  per-key rules; every rule carries the input-source condition.
- Golden-file test for a handful of keys in both outputs.

What tests cannot show: real typing in apps. That is the spike and manual
acceptance, reported separately.

## Spike (first build step)

A throwaway keylayout with three keys (layers 1/3/5/6 only) plus the Karabiner
modifier rules, installed beside everything else. Check in TextEdit, Terminal,
Zed: Mod3 characters appear without delay at fast typing, repeat works,
⌘C/⌘V/Ctrl+A follow Neo letters, Option+L gives `@`, no Caps Lock indicator
or a way to silence it, ISO key swap on the Apple and the Logitech keyboard.
Results go into `docs/quirks.md`; the generator is built only after the spike
passes, or after the fallback is chosen.

## Settled after the builder check

- **Caps Lock: tap = Escape, hold = Mod3** (operator's decision, as in the
  current setup). Mod3 switches the caps state on at key-down (no added
  latency for layer 3); a tap without another key in between switches it off
  again and sends Escape. The spike must show this causes no visible flicker,
  indicator pop-up or stuck caps state; if it cannot, tap = Escape is dropped
  and the operator is told.

- **Option follows Neo letters** (my call, consistent with ⌘/Ctrl and with
  Apple's Dvorak): Option + the key that types `l` gives `@`.
  `layout/option-de.tsv` is keyed by the layer-1 character, not the key code.
  Keys whose layer-1 character has no Apple German Option entry output
  nothing with Option.
- **Keyboards** (my call): all three in the live Karabiner config, the Apple
  (1452/835), the Logitech (1133/50475, Right Option disabled there) and the
  PC keyboard (1130/49304, Command/Option swapped as simple modifications, so
  its AltGr arrives as `right_command` = Mod4, which is Neo's position). The
  spike records which of them report 10/50 swapped; the swap becomes a
  per-device rule only where needed.
- **Karabiner placement** (my call): the live `~/.config/karabiner/karabiner.json`
  is authoritative (a regular file, not written by home-manager). neoneo's
  rule goes into the selected Default profile next to the Neo2 rules; every
  rule is conditioned on neoneo's input source, the Neo2 rules on the Neo
  bundle ids, so they never both fire. `just install` copies the asset file;
  enabling it in Karabiner's UI is a manual step. Bundle id
  `com.mi-skam.keylayout.neoneo`, outside the `org.sil.ukelele…neo` regex.
- **Layer-4 navigation passes modifiers through** (my call, Neo standard):
  Shift/Option/⌘ + Mod4 + navigation key = Shift/Option/⌘ + that key.
  Layer 6 is signalled by a Karabiner-held Option only while both Mod3 and
  Mod4 variables are set; navigation rules match on `mod4 = 1, mod3 = 0`.
- **Acceptance apps** (my call): TextEdit, Terminal, Zed, a Chromium browser.
  If an app reads key codes instead of the keylayout for shortcuts, it is
  recorded in `docs/quirks.md`; per-key ⌘/Ctrl remaps are not added in the
  starting project.

## Left to the builder

Exact keylayout `id`/group numbers, bundle identifiers (`com.mi-skam.neoneo`
is fine), icon, TSV escape set, Karabiner rule naming, file layout of tests.
