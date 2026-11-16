#!/bin/sh
# Remove what install.sh installed. Safe to run again after a partial run.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
layouts="$HOME/Library/Keyboard Layouts"
karabiner_dir="$HOME/.config/karabiner"
karabiner_conf="$karabiner_dir/karabiner.json"
agent="$HOME/Library/LaunchAgents/neoneo.capslockdelay.plist"

# Removing the selected layout makes every app crash when activated.
if defaults read com.apple.HIToolbox AppleSelectedInputSources 2>/dev/null \
    | grep -q '"KeyboardLayout Name" = neoneo;'; then
    echo "neoneo is the selected input source. Switch to another layout in the" >&2
    echo "input menu first, then run this again." >&2
    exit 1
fi

launchctl bootout "gui/$(id -u)" "$agent" 2>/dev/null || true
rm -f "$agent"

# Karabiner: remove the rules from every profile (device settings stay).
if [ -f "$karabiner_conf" ]; then
    cp "$karabiner_conf" "$karabiner_conf.before-neoneo-uninstall"
    osascript -l JavaScript "$here/karabiner-config.js" uninstall "$karabiner_conf"
fi
rm -f "$karabiner_dir/assets/complex_modifications/neoneo.json"

rm -rf "$layouts/neoneo.bundle"

# Drop neoneo from the enabled input sources and the history.
prefs=$(mktemp)
defaults export com.apple.HIToolbox "$prefs"
for list in AppleEnabledInputSources AppleInputSourceHistory; do
    count=$(plutil -extract "$list" raw "$prefs" 2>/dev/null) || continue
    i=$((count - 1))
    while [ "$i" -ge 0 ]; do
        name=$(plutil -extract "$list.$i.KeyboardLayout Name" raw "$prefs" 2>/dev/null) || name=
        if [ "$name" = neoneo ]; then
            plutil -remove "$list.$i" "$prefs"
        fi
        i=$((i - 1))
    done
done
defaults import com.apple.HIToolbox "$prefs"
rm -f "$prefs"

echo "neoneo removed. Log out and in."
