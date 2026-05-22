from __future__ import annotations

from pathlib import Path


def scan_caj_files(root_dir: str) -> list[str]:
    root = Path(root_dir).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"入口文件夹不存在: {root}")

    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".caj":
            files.append(path)

    files.sort(key=lambda p: str(p).lower())
    return [str(p) for p in files]
