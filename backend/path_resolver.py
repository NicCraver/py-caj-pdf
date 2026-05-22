from __future__ import annotations

from pathlib import Path


def resolve_output_name(stem: str, used_names: set[str]) -> str:
    candidate = f"{stem}.pdf"
    if candidate not in used_names:
        used_names.add(candidate)
        return candidate

    index = 2
    while True:
        candidate = f"{stem}_{index}.pdf"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        index += 1


def resolve_output_path(output_dir: str, source_path: str, used_names: set[str]) -> str:
    out_root = Path(output_dir).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    stem = Path(source_path).stem
    name = resolve_output_name(stem, used_names)
    return str(out_root / name)
