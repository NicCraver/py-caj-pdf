#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 构建前端"
(cd frontend && npm install && npm run build)

echo "==> 安装 Python 依赖"
python3 -m pip install -e . pyinstaller

echo "==> PyInstaller 打包"
pyinstaller scripts/caj-pdf.spec --noconfirm

echo "==> 完成: dist/CAJ转PDF.app (macOS) 或 dist/CAJ转PDF/ (Windows)"
