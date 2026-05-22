from pathlib import Path

import pytest

from backend.path_resolver import resolve_output_name, resolve_output_path
from backend.scanner import scan_caj_files


def test_resolve_output_name_unique():
    used: set[str] = set()
    assert resolve_output_name("论文", used) == "论文.pdf"
    assert resolve_output_name("论文", used) == "论文_2.pdf"
    assert resolve_output_name("论文", used) == "论文_3.pdf"


def test_resolve_output_path(tmp_path: Path):
    used: set[str] = set()
    out = resolve_output_path(str(tmp_path), "/fake/dir/a.caj", used)
    assert out.endswith("a.pdf")
    out2 = resolve_output_path(str(tmp_path), "/fake/dir/sub/a.caj", used)
    assert out2.endswith("a_2.pdf")


def test_scan_caj_files(tmp_path: Path):
    (tmp_path / "a.caj").write_text("fake")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.CAJ").write_text("fake")
    (sub / "c.txt").write_text("skip")

    files = scan_caj_files(str(tmp_path))
    assert len(files) == 2
    names = {Path(f).name.lower() for f in files}
    assert names == {"a.caj", "b.caj"}
