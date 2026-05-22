#!/usr/bin/env bash
# 在 macOS 上通过 GitHub Actions 拉取 Windows 安装包（含 ARM 设备可用的 x64 兼容包）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT="${1:-CAJ-PDF-Windows-Setup.exe}"

echo "==> 触发 GitHub Actions Build 工作流"
gh workflow run Build --ref "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"

echo "==> 等待最新运行完成"
run_id="$(gh run list --workflow=Build --limit 1 --json databaseId --jq '.[0].databaseId')"
gh run watch "$run_id"

echo "==> 下载 Windows 安装包"
tmpdir="$(mktemp -d)"
gh run download "$run_id" -n CAJ-PDF-Windows-Setup.exe -D "$tmpdir"
src="$tmpdir/CAJ-PDF-Windows-Setup.exe/CAJ-PDF-Windows-Setup.exe"
if [[ ! -f "$src" ]]; then
  src="$tmpdir/CAJ-PDF-Windows-Setup.exe"
fi
cp "$src" "$ROOT/$OUT"
rm -rf "$tmpdir"
ls -lh "$ROOT/$OUT"
echo "==> 完成: $ROOT/$OUT"
