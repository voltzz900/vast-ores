#!/bin/sh
# Rebuilds Vast Ores and Vast Depths from config.json and installs them into Horizon.
# Content mods: no game rebuild, just restart Horizon.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
mods="$HOME/Library/Application Support/horizon/horizon-mods"
python3 -I "$here/tools/build_content.py" "$here/build"
for mod in vastores vastdepths; do
  rm -rf "$mods/$mod"
  cp -R "$here/build/$mod" "$mods/$mod"
done
echo "Installed. Restart Horizon; only new chunks get new ore settings."
