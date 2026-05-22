from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass

from backend.config import conversion_runtime, mutool_path, setup_caj2pdf_path


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


def _patch_cajparser_mutool() -> None:
    import cajparser  # type: ignore[import-untyped]

    tool = mutool_path()

    def mutool_check_output(args, *a, **kw):
        if args and args[0] == "mutool":
            args = [tool, *args[1:]]
        return subprocess.check_output(args, *a, **kw)

    cajparser.check_output = mutool_check_output


def convert_caj_to_pdf(source_path: str, output_path: str) -> ConversionResult:
    setup_caj2pdf_path()
    ok, mutool_msg = check_mutool_available()
    if not ok:
        return ConversionResult(success=False, error=mutool_msg)

    source = os.path.abspath(source_path)
    output = os.path.abspath(output_path)

    try:
        from cajparser import CAJParser  # type: ignore[import-untyped]
    except ImportError as exc:
        return ConversionResult(success=False, error=f"无法加载 caj2pdf: {exc}")

    _patch_cajparser_mutool()

    try:
        with conversion_runtime():
            parser = CAJParser(source)
            format_type = getattr(parser, "format", None)
            parser.convert(output)
        if not os.path.isfile(output):
            return ConversionResult(
                success=False,
                error="转换完成但未生成 PDF 文件",
                format_type=format_type,
            )
        return ConversionResult(
            success=True,
            output_path=output,
            format_type=format_type,
        )
    except Exception as exc:  # noqa: BLE001 — caj2pdf raises varied errors
        return ConversionResult(
            success=False,
            error=str(exc) or exc.__class__.__name__,
            format_type=locals().get("format_type"),
        )
