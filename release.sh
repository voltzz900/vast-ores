#!/bin/sh
# Builds Vast Ores and Vast Depths and packs each as the .hmod the Horizon registry takes, into dist/.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
python3 -I "$here/tools/build_content.py" "$here/build"
mkdir -p "$here/dist"
for mod in vastores vastdepths; do
  version="$(sed -n 's/^version = "\(.*\)"/\1/p' "$here/build/$mod/horizon-mod.toml")"
  file="$here/dist/$mod-$version.hmod"
  rm -f "$file"
  # The MIT notice goes with every copy.
  cp "$here/LICENSE" "$here/build/$mod/LICENSE"
  (cd "$here/build/$mod" && zip -q -X -r -9 "$file" .)
  echo "$file  $(shasum -a 256 "$file" | cut -d' ' -f1)"
done
