#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/resources/macos/CAJ转PDF.app"
ICON_SRC="$ROOT/resources/icon.icns"
ICON_DST="$APP/Contents/Resources/icon.icns"

echo "==> 构建前端"
(cd "$ROOT/frontend" && npm run build)

chmod +x "$APP/Contents/MacOS/CAJ转PDF"

if [[ -f "$ICON_SRC" ]]; then
  mkdir -p "$APP/Contents/Resources"
  cp "$ICON_SRC" "$ICON_DST"
fi

open "$APP"
