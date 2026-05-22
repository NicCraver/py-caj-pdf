# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

root = Path(SPECPATH).parent.parent
icon_macos = root / "resources" / "icon.icns"
icon_windows = root / "resources" / "icon.ico"

datas = [
    (str(root / "frontend" / "dist"), "frontend/dist"),
    (str(root / "backend" / "vendor" / "caj2pdf"), "backend/vendor/caj2pdf"),
]
resources_bin = root / "resources" / "bin"
if resources_bin.is_dir():
    datas.append((str(resources_bin), "resources/bin"))

a = Analysis(
    [str(root / 'backend' / 'main.py')],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=["cajparser", "PyPDF2", "imagesize"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CAJ转PDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_windows) if sys.platform == "win32" and icon_windows.is_file() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CAJ转PDF',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='CAJ转PDF.app',
        icon=str(icon_macos) if icon_macos.is_file() else None,
        bundle_identifier='com.cajpdf.desktop',
    )
