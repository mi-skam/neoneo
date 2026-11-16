# neoneo

The [Neo2](https://www.neo-layout.org/) keyboard layout for macOS, rebuilt so
Option, Command and Control behave as on every other macOS layout. It is a
generated keylayout plus a small set of Karabiner-Elements rules; Mod3 and Mod4
reach the keylayout through the Caps Lock state.

**Version 0.1.1.** Layers 1–6 on ISO keyboards. Not yet: dead keys (typed as plain
characters), Shift lock, Mod4 lock.

## Install

Needs [Karabiner-Elements](https://karabiner-elements.pqrs.org/), opened at
least once.

1. Download `neoneo-<version>.zip` from the
   [releases](../../releases), unpack it, and in Terminal run:
   ```sh
   sh ~/Downloads/neoneo-0.1.1/install.sh
   ```
2. Log out and in, or restart. **neoneo** appears in the input menu with an
   "nn" icon (System Settings > Keyboard > Input Sources lists it under German).
3. Select neoneo. Check: Caps Lock + the key printed `A` types `\`, and Caps Lock
   is off again after you let go.

`install.sh` sets up, for the current user only:

- the layout in `~/Library/Keyboard Layouts` and in the enabled input sources;
- the two neoneo rules, first in Karabiner's selected profile, and "Manipulate
  caps lock LED" off for the Apple keyboards, so the LED stays dark on Mod3.
  It saves the previous `karabiner.json` as `karabiner.json.before-neoneo`;
- a small helper, `~/Library/Application Support/neoneo/neoneo-capslockdelay`,
  that keeps macOS's Caps Lock delay off for Karabiner's virtual keyboard
  (without it a fast Mod3+key sometimes types the layer-1 character). launchd
  starts it only when that keyboard appears (login, Karabiner restart or
  update); it applies the setting and exits. Nothing runs in between.

**Updating:** run the new version's `install.sh`, then log out and in. It
replaces the old neoneo rules in Karabiner.

**Removing:** switch to another layout in the input menu, then run
`sh uninstall.sh` from the release folder. It refuses while neoneo is
selected, because removing the selected layout crashes apps. It removes the
neoneo rules from every Karabiner profile; device settings such as the LED stay.

### From source

Needs Python 3.9+ and the Xcode command line tools (for `swift`).

```sh
make test       # run the tests
make install    # build the release folder and run its install.sh
make verify     # compare the installed layout with the source table
make uninstall  # run uninstall.sh
make dist       # build/neoneo-<version>.zip, as published by CI
```

Releases: set `VERSION` in `neoneo.py`, commit, tag `v<VERSION>` and push the
tag. GitHub Actions runs the tests and publishes the zip.

### Optional

- **Caps Lock symbol:** macOS shows a ⇪ symbol near the cursor while Mod3 is
  held. `defaults write kCFPreferencesAnyApplication TSMLanguageIndicatorEnabled 0`
  hides it (system-wide; it also hides the input-source popup).
- **Other keyboards:** the LED setting is only changed for the measured Apple
  keyboards; for others, Karabiner-Elements > Settings > Devices > the keyboard
  > turn off "Manipulate caps lock LED".

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
- Releasing Mod3 and Mod4 in a rolling order (the first-pressed one first)
  can give one wrong character until the other key is released.
- The input source id is `xyz.miskam.keyboardlayout.neoneo.keylayout.neoneo`:
  macOS derives it from the bundle id and ignores a custom one.

## Files

- `layout/neoneo.tsv`: the source of truth, one row per key with its six layers.
- `neoneo.py`: generates `build/neoneo.bundle` and `build/karabiner-neoneo.json`.
- `layout/apple-german.tsv`, `layout/option-de.tsv`: Apple German, for Option
  and for keys outside the Neo table.
- `layout/neoneo.icns`: the menu bar icon (`make icon` redraws it).
- `tools/install.sh`, `tools/uninstall.sh`, `tools/karabiner-config.js`: the
  install scripts shipped in the release.
- `tools/capslockdelay.swift`, `tools/neoneo.capslockdelay.plist`: the Caps
  Lock delay helper and its launch agent (`make helper` builds it).
- `.github/workflows/release.yml`: tests on every push; the release on a tag.
- [Design](docs/superpowers/specs/2026-11-16-neoneo-design.md),
  [macOS quirks and hand-checked results](docs/quirks.md).
