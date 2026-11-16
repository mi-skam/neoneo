#!/bin/sh
# Remove a keyboard layout from the enabled input sources and the history.
#
# usage: sh remove-input-source.sh DOMAIN NAME   (uninstall.sh: com.apple.HIToolbox neoneo)
#
# Writes back only the lists that change, one key at a time, instead of
# re-importing the whole domain, so other settings are never touched.
set -eu

domain=$1
name=$2
prefs=$(mktemp)
trap 'rm -f "$prefs"' EXIT

defaults export "$domain" "$prefs"
for list in AppleEnabledInputSources AppleInputSourceHistory; do
    count=$(plutil -extract "$list" raw "$prefs" 2>/dev/null) || continue
    changed=no
    i=$((count - 1))
    while [ "$i" -ge 0 ]; do
        entry=$(plutil -extract "$list.$i.KeyboardLayout Name" raw "$prefs" 2>/dev/null) || entry=
        if [ "$entry" = "$name" ]; then
            plutil -remove "$list.$i" "$prefs"
            changed=yes
        fi
        i=$((i - 1))
    done
    if [ "$changed" = yes ]; then
        defaults write "$domain" "$list" "$(plutil -extract "$list" xml1 -o - "$prefs")"
    fi
done
