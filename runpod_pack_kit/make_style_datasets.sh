#!/usr/bin/env bash
# Split /workspace/sa3_beats into 4 style datasets (symlinks — no copies) by caption content.
set -euo pipefail
SRC="${SRC:-/workspace/sa3_beats}"
mk() { local name="$1" pat="$2" dst="/workspace/sa3_${1}"
  mkdir -p "$dst"
  find "$SRC" -name '*.txt' -print0 | xargs -0 grep -liE "$pat" | while read -r f; do
    base="${f%.txt}"
    ln -sf "$f" "$dst/"
    for ext in wav flac mp3 ogg aif aiff m4a; do [ -f "$base.$ext" ] && ln -sf "$base.$ext" "$dst/"; done
  done
  echo "sa3_${name}: $(find "$dst" -name '*.txt' | wc -l) clips  (pattern: $pat)"
}
mk boombap 'boom bap|dusty vinyl.*(mellow|warm)'
mk trap    '\btrap\b'
mk drill   '\bdrill\b'
mk lofi    '\blofi\b|mellow, laid back'
