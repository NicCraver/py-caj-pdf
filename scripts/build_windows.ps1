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

Write-Host "==> Inno Setup 安装包"
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    Write-Error "未找到 Inno Setup，请先安装: https://jrsoftware.org/isinfo.php"
}
& $iscc "scripts/installer.iss"

Write-Host "==> 完成: dist\CAJ转PDF\ 与 CAJ-PDF-Windows-Setup.exe"
