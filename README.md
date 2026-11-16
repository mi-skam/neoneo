# neoneo

The Neo2 keyboard layout for macOS, rebuilt so Option, Command and Control
behave as on every macOS layout. A generated keylayout plus a small set of
Karabiner-Elements rules; Mod3 and Mod4 are signalled through the Caps Lock
state. Version 0.1: no dead keys, no Shift lock or Mod4 lock, ISO keyboards only.

## Install

Needs Python 3.9+, the Xcode command line tools (for `swift`) and
Karabiner-Elements.

```sh
make test       # run the tests
make install    # build, copy the layout and the Karabiner rules, enable the input source
```

Then log out and in, select **neoneo** in the input menu, and enable both
"neoneo" rules in Karabiner-Elements > Complex Modifications (Default
profile). `make verify` checks the installed layout against the source table.
`make uninstall` removes it again.

`make install` also adds a login agent that turns off macOS's Caps Lock delay
for Karabiner's virtual keyboard; without it a fast Mod3+key sometimes types
the layer-1 character (see [quirks](docs/quirks.md)).

## Modifiers

| Modifier | Keys                                        | Layers         |
| -------- | ------------------------------------------- | -------------- |
| Shift    | Shift                                       | 2              |
| Mod3     | Caps Lock (tap = Escape), `#` right of Ä    | 3; +Shift = 5  |
| Mod4     | `<` left of Y, Right Command                | 4; +Mod3 = 6   |
| Option   | Option                                      | Apple German Option characters |
| ⌘, Ctrl  | Command, Control                            | follow Neo letters |

## The hidden switch

1. A macOS keylayout only knows Shift, Option, Caps Lock, Command and Control.
2. Karabiner turns the Caps Lock *state* on while Mod3 or Mod4 is held.
3. The keylayout puts layer 3 on Caps, layer 5 on Caps+Shift, layer 6 on Caps+Option.
4. Mod3+Mod4 adds a held Option; Mod4 alone gets per-key Karabiner rules (layer 4).
5. So layers 3, 5 and 6 need no per-key Karabiner rules at all.

## Files

- `layout/neoneo.tsv`: the source of truth, one row per key with its six layers.
- `neoneo.py`: generates `build/neoneo.keylayout` and `build/karabiner-neoneo.json`.
- `layout/apple-german.tsv`, `layout/option-de.tsv`: Apple German, for Option
  and for keys outside the Neo table.
- [Design](docs/superpowers/specs/2026-11-16-neoneo-design.md),
  [macOS quirks and hand-checked results](docs/quirks.md).
