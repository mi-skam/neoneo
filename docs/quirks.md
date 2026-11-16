# macOS quirks

How neoneo meets each macOS quirk, and what was observed by hand. Hand-checked
results are recorded here, separate from the automated tests.

## Install format

- **Bundle identifier must contain `.keyboardlayout.`** (Apple TN2056). Bundles
  with `com.mi-skam.keylayout.…` or `xyz.miskam.keylayout.…` were ignored
  silently after logout and restart, in `~/Library` and `/Library` alike, with
  nothing in the logs. `xyz.miskam.keyboardlayout.neoneo` loads (2026-11-16).
- **The input source id is derived:** `<bundle id>.keylayout.<name>`, here
  `xyz.miskam.keyboardlayout.neoneo.keylayout.neoneo`. KLInfo
  `TISInputSourceID` is ignored (the official Neo bundle shows the same).
- **Template icon:** `TISIconIsTemplate` in KLInfo makes the "nn" icon follow
  the menu bar colour.
- **Do not set `TICapsLockLanguageSwitchCapable = false`.** With it, Caps Lock
  stayed on after every Mod3 press: macOS dropped Karabiner's short Caps Lock
  press on release, and one more tap was needed to clear it. Removing the key
  fixed it (operator, 2026-11-16).
- A standalone `.keylayout` loads too (id `org.unknown.keylayout.<name>`, no
  template icon); v0.1 used it until the bundle id was fixed.
- Bundles are only picked up at login; `TISRegisterInputSource` registers a
  standalone `.keylayout` at once but not a bundle.
- The layout must also be in `com.apple.HIToolbox AppleEnabledInputSources`;
  `make install` adds it.
- **Never delete the selected layout's files.** Every app then crashes when
  activated (`_TSMSetInputSourceSelected` on a NULL id) until another layout is
  selected. `make uninstall` selects Apple's German layout first.

The Karabiner rules match the input source ID exactly. With a wrong ID they
silently do nothing, while plain Caps Lock still gives layer 3 from the layout
alone, so a quick Caps test can pass for the wrong reason.

"Use Caps Lock to switch to and from ABC" is only offered when a non-Latin
input method is enabled. With only Latin layouts it does not appear and is
inactive. Adding such a method later may turn it on and break Mod3.

## Mechanism checks (2026-11-16)

Checked with a four-key test layout (Neo `u i a 1` on QWERTZ `a s d 1`) before
the generator was written. Candidate modifier keys: Mod3 = `caps_lock`,
`non_us_pound`, `backslash`; Mod4 = `non_us_backslash`,
`grave_accent_and_tilde`, `right_command`.

| # | Check | Expected | Result |
|---|-------|----------|--------|
| 1 | Fast typing Mod3+u, Mod3+i, Mod3+a | `\ / {` every time, no uppercase, no delay | ok |
| 2 | Hold Mod3+i | `/` repeats | ok |
| 3 | Shift+Mod3+i | `ι` | ok |
| 4 | Mod3+Mod4+i, press both orders, release both orders | `∫`; Caps Lock off afterwards | ok in all four orders. With i held through the release: Mod4 released first gives `/` (layer 3), Mod3 released first gives `⁄` (Option-only map, not layer 4) |
| 5 | Hold Mod3+Mod4, release Mod3 first, type i, then Mod4+i again | note what appears | i tapped after releasing Mod3 moves the cursor one character left (plain layer 4, no extra Option) |
| 6 | Mod4+i / Shift+Mod4+i / Mod4+1 | cursor left / selects left / `ª` | ok |
| 7 | Tap Caps Lock | Escape; Caps state off afterwards | ok |
| 8 | Caps Lock LED and on-screen Caps indicator on Mod3 | seen or not | seen: the LED and the on-screen Caps indicator light up while Mod3 is held |
| 9 | ⌘ + the `a` key (QWERTZ `d`) in TextEdit, also with Mod3 held | select all | ok, also with Mod3 held |
| 10 | Ctrl + the `a` key in Terminal | cursor to line start | ok |
| 11 | Option + the `u` key | German Option+U (umlaut dead key: nothing) | ok (nothing appears) |
| 12 | Both Mod3 keys held, release in either order | no Caps Lock left on | ok |

Keyboards (Karabiner-EventViewer, `key_code` names; read with plain Deutsch
selected, because with the test layout active EventViewer shows the rules' output,
so all three keys appear as `caps_lock`):

| Keyboard | key left of 1 | key left of Y | key right of Ä |
|----------|---------------|---------------|----------------|
| Apple internal (1452/835) | `non_us_backslash` (swapped) | `grave_accent_and_tilde` (swapped) | `backslash` |
| Apple Magic Keyboard, Bluetooth (76/615) | `non_us_backslash` (swapped) | `grave_accent_and_tilde` (swapped) | `backslash` |
| Logitech (1133/50475) | | | |
| PC (1130/49304) | | | |

Outcome: all 12 checks pass, so the Caps Lock state approach stays (no
Option+Control fallback).

- Mod3 = `caps_lock` and the key right of Ä, which both Apple keyboards report
  as `backslash`.
- Mod4 = the key left of Y and `right_command`. Apple keyboards report the key
  left of Y as `grave_accent_and_tilde`, standard ISO as `non_us_backslash`.
- 10/50 swap devices: 1452/835 (Apple internal), 76/615 (Magic Keyboard).
  Apply the swap as a per-device simple modification: complex manipulators do
  not feed into each other, so a swap written as a complex rule would never
  reach the Mod4 rule.
- Logitech (1133/50475) and PC (1130/49304): not measured, not connected on
  2026-11-16. Measure before relying on them.

Trap: System Settings > Keyboard > Modifier Keys sets Caps Lock to "No Action"
on the internal keyboard (1452/835). Karabiner bypasses this while running;
without Karabiner, Caps Lock does nothing on that keyboard.

## Full layout v0.1

Installed with `make install` (`neoneo.bundle`, input source ID
`xyz.miskam.keyboardlayout.neoneo.keylayout.neoneo`, added to
`AppleEnabledInputSources`), then log out and in and enable both "neoneo"
rules in Karabiner.

`make verify` (automated, 2026-11-16, bundle install): ok, all 128 key codes ×
10 states match the TSV. Menu bar shows the "nn" template icon (operator).

Hand checks on the full layout (repeat the mechanism checks with the real keys):
done, pass (operator, 2026-11-16), after the fixes below.

Caps Lock delay (found 2026-11-16 on the full layout): a fast Mod3+key
sometimes typed the layer-1 character. Cause: macOS delays Caps Lock on
Apple-vendor keyboards, and Karabiner's virtual keyboard reports Apple's vendor
id (0x5ac/0x250), so the Caps state came on after the next key. Fix:
`CapsLockDelayOverride = 0` on the virtual keyboard via `hidutil`; the value is
lost on reboot and Karabiner restart, so `make install` adds the login agent
`neoneo.capslockdelay`, which sets it at login. After the fix: no more literal
characters (operator). After a Karabiner restart without logout, rerun it with
`launchctl kickstart -k gui/$(id -u)/neoneo.capslockdelay`.

Caps Lock LED: off while Mod3 is held after turning off "Manipulate caps lock
LED" per keyboard in Karabiner > Settings > Devices (operator, 2026-11-16).
The on-screen Caps Lock symbol (shown with the internal keyboard) is hidden by
`defaults write kCFPreferencesAnyApplication TSMLanguageIndicatorEnabled 0`
(operator, 2026-11-16). System-wide: it also hides the input-source popup.
Undo: `defaults delete kCFPreferencesAnyApplication TSMLanguageIndicatorEnabled`.

Apps that read key codes instead of the layout for shortcuts (no per-app
remaps in v0.1; listed here per the spec):

| App | Observed | Cause |
|-----|----------|-------|
| hrdx | Ctrl+B fires on the key printed `b` (Neo `z`), not on the Neo `b` key | Ctrl shortcuts matched by physical key position (key code 11), as with the old Neo2 setup |
