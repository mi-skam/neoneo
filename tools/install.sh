#!/bin/sh
# Install neoneo for the current user. Run from the unpacked release folder
# (or via `make install`). Uses only tools that ship with macOS.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
layouts="$HOME/Library/Keyboard Layouts"
karabiner_dir="$HOME/.config/karabiner"
karabiner_conf="$karabiner_dir/karabiner.json"
agent="$HOME/Library/LaunchAgents/neoneo.capslockdelay.plist"
support="$HOME/Library/Application Support/neoneo"

if [ ! -f "$karabiner_conf" ]; then
    echo "Karabiner-Elements is not set up yet ($karabiner_conf is missing)." >&2
    echo "Install it, open it once, then run this again." >&2
    exit 1
fi

mkdir -p "$layouts" "$karabiner_dir/assets/complex_modifications" "$HOME/Library/LaunchAgents"

# Keyboard layout. ditto updates an existing bundle in place: removing the
# bundle of the selected layout would crash every app until another layout
# is selected. Files from a downloaded archive carry a quarantine flag that
# can keep macOS from loading the layout, so clear all extended attributes.
ditto "$here/neoneo.bundle" "$layouts/neoneo.bundle"
xattr -cr "$layouts/neoneo.bundle"

# Karabiner: enable the rules in the selected profile (replacing an older
# neoneo version) and keep the asset file for other profiles.
cp "$karabiner_conf" "$karabiner_conf.before-neoneo"
osascript -l JavaScript "$here/karabiner-config.js" install "$here/karabiner-neoneo.json" "$karabiner_conf"
cp "$here/karabiner-neoneo.json" "$karabiner_dir/assets/complex_modifications/neoneo.json"

# List the layout in the enabled input sources so it appears after login.
if ! defaults read com.apple.HIToolbox AppleEnabledInputSources 2>/dev/null \
    | grep -q '"KeyboardLayout Name" = neoneo;'; then
    defaults write com.apple.HIToolbox AppleEnabledInputSources -array-add \
        '<dict><key>InputSourceKind</key><string>Keyboard Layout</string><key>KeyboardLayout ID</key><integer>-24601</integer><key>KeyboardLayout Name</key><string>neoneo</string></dict>'
fi

# Caps Lock delay: launchd starts the helper whenever Karabiner's virtual
# keyboard appears. The agent needs the helper's absolute path.
mkdir -p "$support"
cp "$here/neoneo-capslockdelay" "$support/neoneo-capslockdelay"
chmod 755 "$support/neoneo-capslockdelay"
xattr -c "$support/neoneo-capslockdelay"
sed "s#__HELPER__#$support/neoneo-capslockdelay#" "$here/neoneo.capslockdelay.plist" > "$agent"
launchctl bootout "gui/$(id -u)" "$agent" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$agent"

cat <<EOF
neoneo installed. Log out and in (or restart); neoneo then appears in the
input menu. Previous Karabiner config: $karabiner_conf.before-neoneo
EOF
