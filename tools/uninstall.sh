#!/bin/sh
# Remove what install.sh installed. Safe to run again after a partial run.
set -eu

layouts="$HOME/Library/Keyboard Layouts"
karabiner="$HOME/.config/karabiner/assets/complex_modifications"
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
rm -f "$karabiner/neoneo.json"
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

cat <<'EOF'
neoneo removed. Remove the two neoneo rules in Karabiner-Elements >
Settings > Complex Modifications, then log out and in.
EOF
