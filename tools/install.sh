#!/bin/sh
# Install neoneo for the current user. Run from the unpacked release folder
# (or via `make install`). Uses only tools that ship with macOS.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
layouts="$HOME/Library/Keyboard Layouts"
karabiner="$HOME/.config/karabiner/assets/complex_modifications"
agent="$HOME/Library/LaunchAgents/neoneo.capslockdelay.plist"

mkdir -p "$layouts" "$karabiner" "$HOME/Library/LaunchAgents"

# Keyboard layout. ditto updates an existing bundle in place: removing the
# bundle of the selected layout would crash every app until another layout
# is selected. Files from a downloaded archive carry a quarantine flag that
# can keep macOS from loading the layout, so clear all extended attributes.
ditto "$here/neoneo.bundle" "$layouts/neoneo.bundle"
xattr -cr "$layouts/neoneo.bundle"

# Karabiner rules (enabled by hand in Karabiner's settings).
cp "$here/karabiner-neoneo.json" "$karabiner/neoneo.json"

# List the layout in the enabled input sources so it appears after login.
if ! defaults read com.apple.HIToolbox AppleEnabledInputSources 2>/dev/null \
    | grep -q '"KeyboardLayout Name" = neoneo;'; then
    defaults write com.apple.HIToolbox AppleEnabledInputSources -array-add \
        '<dict><key>InputSourceKind</key><string>Keyboard Layout</string><key>KeyboardLayout ID</key><integer>-24601</integer><key>KeyboardLayout Name</key><string>neoneo</string></dict>'
fi

# Login agent: turn off the Caps Lock delay of Karabiner's virtual keyboard.
cp "$here/neoneo.capslockdelay.plist" "$agent"
xattr -c "$agent"
launchctl bootout "gui/$(id -u)" "$agent" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$agent"

cat <<'EOF'
neoneo installed.
1. Log out and in (or restart). neoneo appears in the input menu.
2. Karabiner-Elements > Settings > Complex Modifications > Add predefined rule
   > neoneo: enable both rules. After reinstalling a new version, remove both
   neoneo rules there and add them again: Karabiner keeps its own copy.
EOF
