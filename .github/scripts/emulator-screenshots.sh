#!/usr/bin/env bash
# Installs the APK on the running emulator and saves screenshots of the main screens.
set -euo pipefail
out=docs/screenshots
mkdir -p "$out"
pkg=pl.modako.grzyby
adb install -r apk/*.apk
shot() { sleep "$2"; adb exec-out screencap -p > "$out/$1.png"; echo "saved $1"; }

adb shell am start -n "$pkg/.MainActivity"
# First start downloads the forest map (~9 MB) and the forecast.
shot 1-mapa 75
# Screen size, used to scroll the forest card.
size=$(adb shell wm size | grep -o '[0-9]*x[0-9]*' | tail -1); w=${size%x*}; h=${size#*x}
adb shell am start -a android.intent.action.VIEW -d "grzyby://cell/881e2cdad7fffff" "$pkg"
shot 2-karta-lasu 8
adb shell input swipe $((w/2)) $((h*3/4)) $((w/2)) $((h/4)) 400
shot 3-karta-lasu-dol 3
adb shell am start -a android.intent.action.VIEW -d "grzyby://info" "$pkg"
shot 4-informacje 6
adb logcat -d -s ReactNativeJS:V ReactNative:V AndroidRuntime:E > "$out/logcat.txt" || true  # uploaded as artifact, not committed
