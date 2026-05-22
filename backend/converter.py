from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

from backend.config import lib_env, mutool_path, setup_caj2pdf_path


@dataclass
class ConversionResult:
    success: bool
    output_path: str | None = None
    error: str | None = None
    format_type: str | None = None


def check_mutool_available() -> tuple[bool, str]:
    path = mutool_path()
    if path != "mutool" and os.path.isfile(path):
        return True, path
    found = shutil.which("mutool")
    if found:
        return True, found
    return False, "未找到 mutool。请安装 MuPDF（macOS: brew install mupdf）或确保安装包内置 mutool。"


def convert_caj_to_pdf(source_path: str, output_path: str) -> ConversionResult:
    setup_caj2pdf_path()
    ok, mutool_msg = check_mutool_available()
    if not ok:
        return ConversionResult(success=False, error=mutool_msg)

    env = lib_env()
    if mutool_msg != "mutool":
        bin_dir = os.path.dirname(mutool_msg)
        path_key = "PATH"
        env[path_key] = f"{bin_dir}{os.pathsep}{env.get(path_key, '')}"

    try:
        from cajparser import CAJParser  # type: ignore[import-untyped]
    except ImportError as exc:
        return ConversionResult(success=False, error=f"无法加载 caj2pdf: {exc}")

    try:
        parser = CAJParser(source_path)
        format_type = getattr(parser, "format", None)
        parser.convert(output_path)
        if not os.path.isfile(output_path):
            return ConversionResult(
                success=False,
                error="转换完成但未生成 PDF 文件",
                format_type=format_type,
            )
        return ConversionResult(
            success=True,
            output_path=output_path,
            format_type=format_type,
        )
    except Exception as exc:  # noqa: BLE001 — caj2pdf raises varied errors
        return ConversionResult(
            success=False,
            error=str(exc) or exc.__class__.__name__,
            format_type=locals().get("format_type"),
        )
