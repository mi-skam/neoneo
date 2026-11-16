# neoneo

The [Neo2](https://www.neo-layout.org/) keyboard layout for macOS, rebuilt so
Option, Command and Control behave as on every other macOS layout. It is a
generated keylayout plus a small set of Karabiner-Elements rules; Mod3 and Mod4
reach the keylayout through the Caps Lock state.

**Version 0.1.** Layers 1–6 on ISO keyboards. Not yet: dead keys (typed as plain
characters), Shift lock, Mod4 lock.

## Install

Needs Python 3.9+, the Xcode command line tools (for `swift`) and
[Karabiner-Elements](https://karabiner-elements.pqrs.org/).

```sh
make test       # run the tests
make install    # build and install the layout, the Karabiner rules and a login agent
```

Then:

1. Log out and in. **neoneo** appears in the input menu with an "nn" icon
   (System Settings > Keyboard > Input Sources lists it under German).
2. Karabiner-Elements > Settings > Complex Modifications > Add predefined rule >
   **neoneo**: enable both rules (Default profile).
3. Select neoneo. Check: Caps Lock + the key printed `A` types `\`, and Caps Lock
   is off again after you let go.

`make verify` compares the installed layout with the source table.
`make uninstall` switches to Apple's German layout, then removes everything
`make install` added; remove the Karabiner rules in Karabiner afterwards.

### Recommended settings

- **Caps Lock LED:** Karabiner-Elements > Settings > Devices > each keyboard >
  turn off "Manipulate caps lock LED", or the LED lights up while Mod3 is held.
- **Caps Lock symbol:** macOS shows a ⇪ symbol near the cursor while Mod3 is
  held. `defaults write kCFPreferencesAnyApplication TSMLanguageIndicatorEnabled 0`
  hides it (system-wide; it also hides the input-source popup).
- **Caps Lock delay:** handled by the login agent `neoneo.capslockdelay` that
  `make install` adds. After a Karabiner restart without logging out, run
  `launchctl kickstart -k gui/$(id -u)/neoneo.capslockdelay`.

## Modifiers

| Modifier | Keys                                     | Layers                         |
| -------- | ---------------------------------------- | ------------------------------ |
| Shift    | Shift                                    | 2                              |
| Mod3     | Caps Lock (tap = Escape), `#` right of Ä | 3; with Shift 5                |
| Mod4     | `<` left of Y, Right Command             | 4; with Mod3 6                 |
| Option   | Option                                   | Apple German Option characters |
| ⌘, Ctrl  | Command, Control                         | follow Neo letters             |

## The hidden switch

1. A macOS keylayout only knows Shift, Option, Caps Lock, Command and Control.
2. Karabiner turns the Caps Lock *state* on while Mod3 or Mod4 is held.
3. The keylayout puts layer 3 on Caps, layer 5 on Caps+Shift, layer 6 on Caps+Option.
4. Mod3+Mod4 adds a held Option; Mod4 alone gets per-key Karabiner rules (layer 4).
5. So layers 3, 5 and 6 need no per-key Karabiner rules at all.

## Known limitations

- Apps that match shortcuts by physical key position instead of the layout
  (some Electron/Chromium apps and terminal programs) keep their shortcuts on
  the QWERTZ keys. Seen: hrdx.
- Measured keyboards: Apple internal and Magic Keyboard (both swap the `^` and
  `<` key codes; handled). Other ISO keyboards are expected to work but are not
  measured yet.
- The input source id is `xyz.miskam.keyboardlayout.neoneo.keylayout.neoneo`:
  macOS derives it from the bundle id and ignores a custom one.

## Files

- `layout/neoneo.tsv`: the source of truth, one row per key with its six layers.
- `neoneo.py`: generates `build/neoneo.bundle` and `build/karabiner-neoneo.json`.
- `layout/apple-german.tsv`, `layout/option-de.tsv`: Apple German, for Option
  and for keys outside the Neo table.
- `layout/neoneo.icns`: the menu bar icon (`make icon` redraws it).
- [Design](docs/superpowers/specs/2026-11-16-neoneo-design.md),
  [macOS quirks and hand-checked results](docs/quirks.md).
