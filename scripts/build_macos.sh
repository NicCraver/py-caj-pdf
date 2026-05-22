#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 构建前端"
(cd frontend && npm install && npm run build)

echo "==> 安装 Python 依赖"
if [[ ! -d "$ROOT/.venv" ]]; then
  python3 -m venv "$ROOT/.venv"
fi
# shellcheck source=/dev/null
source "$ROOT/.venv/bin/activate"
python -m pip install -e . pyinstaller

echo "==> PyInstaller 打包"
pyinstaller scripts/caj-pdf.spec --noconfirm

echo "==> 创建 DMG"
hdiutil create -volname "CAJ 转 PDF" -srcfolder "dist/CAJ转PDF.app" -ov -format UDZO "CAJ-PDF-macOS.dmg"

echo "==> 完成: dist/CAJ转PDF.app, CAJ-PDF-macOS.dmg"
