$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> 构建前端"
Set-Location frontend
npm install
npm run build
Set-Location $Root

Write-Host "==> 安装 Python 依赖"
python -m pip install -e . pyinstaller

Write-Host "==> PyInstaller 打包"
pyinstaller scripts/caj-pdf.spec --noconfirm

Write-Host "==> 完成: dist\CAJ转PDF\"
