from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "CAJ转PDF"
APP_VERSION = "0.1.0"


def _app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


ROOT_DIR = _app_root()
BACKEND_DIR = ROOT_DIR / "backend" if not getattr(sys, "frozen", False) else ROOT_DIR
VENDOR_CAJ2PDF = (
    ROOT_DIR / "backend" / "vendor" / "caj2pdf"
    if (ROOT_DIR / "backend" / "vendor" / "caj2pdf").is_dir()
    else ROOT_DIR / "vendor" / "caj2pdf"
)
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
RESOURCES_DIR = ROOT_DIR / "resources"

DATA_DIR = Path.home() / ".caj-pdf-desktop"
DB_PATH = DATA_DIR / "history.db"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def setup_caj2pdf_path() -> None:
    vendor = str(VENDOR_CAJ2PDF)
    if vendor not in sys.path:
        sys.path.insert(0, vendor)


def resource_bin_dir() -> Path | None:
    """Platform-specific bundled binaries (mutool, native libs)."""
    if sys.platform == "win32":
        sub = "win64"
    elif sys.platform == "darwin":
        sub = "macos-universal"
    else:
        sub = "linux64"
    path = RESOURCES_DIR / "bin" / sub
    return path if path.is_dir() else None


def mutool_path() -> str:
    bundled = resource_bin_dir()
    if bundled:
        name = "mutool.exe" if sys.platform == "win32" else "mutool"
        candidate = bundled / name
        if candidate.is_file():
            return str(candidate)
    return "mutool"


def lib_env() -> dict[str, str]:
    env = os.environ.copy()
    bundled = resource_bin_dir()
    if bundled:
        lib_dir = bundled / "lib"
        if lib_dir.is_dir():
            key = "PATH" if sys.platform == "win32" else "DYLD_LIBRARY_PATH"
            existing = env.get(key, "")
            env[key] = f"{lib_dir}{os.pathsep}{existing}" if existing else str(lib_dir)
    vendor_lib = VENDOR_CAJ2PDF / "lib"
    if vendor_lib.is_dir():
        if sys.platform == "win32":
            key = "PATH"
        elif sys.platform == "darwin":
            key = "DYLD_LIBRARY_PATH"
        else:
            key = "LD_LIBRARY_PATH"
        existing = env.get(key, "")
        env[key] = f"{vendor_lib}{os.pathsep}{existing}" if existing else str(vendor_lib)
    return env
