#!/usr/bin/env bash
# Render tools/og-image.svg to site/og.png (1200x630) for link previews. Needs a Chromium binary.
set -euo pipefail
chrome=${CHROME:-$HOME/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome}
"$chrome" --headless --disable-gpu --hide-scrollbars --window-size=1200,630 \
  --screenshot="$(pwd)/site/og.png" "file://$(pwd)/tools/og-image.svg"
