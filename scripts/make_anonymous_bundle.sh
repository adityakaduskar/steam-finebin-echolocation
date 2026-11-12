#!/bin/bash
# Build an anonymised copy of the repository for double-blind review: paper/supplementary_anonymous.zip
# (tracked files of HEAD only; user name, home paths and repository names replaced; author-facing notes removed).
set -euo pipefail; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; OUT=$ROOT/paper/supplementary_anonymous.zip; T=$(mktemp -d)
git -C "$ROOT" archive --format=tar --prefix=echolocation_supplement/ HEAD | tar -x -C "$T"; D=$T/echolocation_supplement
rm -f "$D/NOTICE" "$D/paper/README.md" "$D/paper/main.pdf" "$D/scripts/make_anonymous_bundle.sh"; rm -rf "$D/habitat_audio/videos"
grep -rIlE "adityakaduskar|steam-finebin-echolocation|echoengine|gmail" "$D" | while read -r f; do
  sed -i -E 's/adityakaduskar@gmail\.com/anonymous@example.org/g; s/adityakaduskar/anonymous/g; s/steam-finebin-echolocation/anonymous-repository/g; s/echoengine/other-project/g' "$f"; done
left=$(grep -rIlE "adityakaduskar|steam-finebin|gmail" "$D" | wc -l); [ "$left" = 0 ] || { echo "identifying strings remain in $left files"; exit 1; }
(cd "$T" && zip -qr "$OUT" echolocation_supplement); rm -rf "$T"; ls -la "$OUT" | awk '{print $5" bytes -> "$9}'
