from __future__ import annotations

import json
from typing import Any

import webview

from backend.converter import check_mutool_available
from backend.history import HistoryStore
from backend.queue_manager import QueueManager
from backend.scanner import scan_caj_files


class Api:
    def __init__(self, window: webview.Window | None = None) -> None:
        self.window = window
        self.history = HistoryStore()
        self.history.mark_interrupted_batches()
        self.queue = QueueManager(self.history)
        self.queue.set_update_callback(self._push_progress)

    def _push_progress(self) -> None:
        if self.window is None:
            return
        payload = json.dumps(self.queue.get_progress(), ensure_ascii=False)
        try:
            self.window.evaluate_js(
                f"window.__onProgressUpdate && window.__onProgressUpdate({payload})"
            )
        except Exception:  # noqa: BLE001 — window may be closing
            pass

    def get_app_info(self) -> dict[str, Any]:
        ok, mutool = check_mutool_available()
        return {
            "name": "CAJ转PDF",
            "version": "0.1.0",
            "mutool_ok": ok,
            "mutool_path": mutool if ok else "",
        }

    def get_settings(self) -> dict[str, str]:
        return {
            "theme": self.history.get_setting("theme", "system"),
            "last_input_dir": self.history.get_setting("last_input_dir", ""),
            "last_output_dir": self.history.get_setting("last_output_dir", ""),
        }

    def set_theme(self, theme: str) -> dict[str, bool]:
        if theme not in ("light", "dark", "system"):
            theme = "system"
        self.history.set_setting("theme", theme)
        return {"ok": True}

    def select_folder(self, kind: str = "input") -> dict[str, Any]:
        if self.window is None:
            return {"ok": False, "error": "窗口未就绪"}
        if self.queue.is_busy():
            return {"ok": False, "error": "转换进行中，无法更改文件夹"}

        title = "选择入口文件夹" if kind == "input" else "选择出口文件夹"
        result = self.window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=self.history.get_setting(
                f"last_{kind}_dir" if kind in ("input", "output") else "last_input_dir",
                "",
            ),
        )
        if not result:
            return {"ok": False, "cancelled": True}

        path = result[0] if isinstance(result, (list, tuple)) else result
        key = f"last_{kind}_dir"
        self.history.set_setting(key, path)
        return {"ok": True, "path": path}

    def scan_input(self, input_dir: str) -> dict[str, Any]:
        try:
            files = scan_caj_files(input_dir)
            return {"ok": True, "count": len(files), "files": files[:20]}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    def start_conversion(self, input_dir: str, output_dir: str) -> dict[str, Any]:
        if not input_dir or not output_dir:
            return {"ok": False, "error": "请先选择入口和出口文件夹"}
        try:
            files = scan_caj_files(input_dir)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

        self.history.set_setting("last_input_dir", input_dir)
        self.history.set_setting("last_output_dir", output_dir)
        return self.queue.start(input_dir, output_dir, files)

    def pause_conversion(self) -> dict[str, Any]:
        return self.queue.pause()

    def resume_conversion(self) -> dict[str, Any]:
        return self.queue.resume()

    def cancel_conversion(self) -> dict[str, Any]:
        return self.queue.cancel()

    def get_progress(self) -> dict[str, Any]:
        return self.queue.get_progress()

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.history.list_batches(limit)

    def get_history_detail(self, batch_id: int) -> dict[str, Any]:
        batches = self.history.list_batches(500)
        batch = next((b for b in batches if b["id"] == batch_id), None)
        if not batch:
            return {"ok": False, "error": "批次不存在"}
        items = self.history.get_batch_items(batch_id)
        return {"ok": True, "batch": batch, "items": items}
