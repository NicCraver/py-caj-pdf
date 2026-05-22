from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from backend.converter import convert_caj_to_pdf
from backend.history import HistoryStore
from backend.path_resolver import resolve_output_path


class QueueState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ProgressSnapshot:
    state: QueueState = QueueState.IDLE
    batch_id: int | None = None
    input_dir: str = ""
    output_dir: str = ""
    total: int = 0
    completed: int = 0
    success_count: int = 0
    failed_count: int = 0
    current_file: str = ""
    logs: list[dict[str, str]] = field(default_factory=list)
    failed_files: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "batch_id": self.batch_id,
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "total": self.total,
            "completed": self.completed,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "current_file": self.current_file,
            "progress_percent": round(self.completed / self.total * 100, 1)
            if self.total
            else 0,
            "logs": self.logs[-200:],
            "failed_files": self.failed_files,
        }


class QueueManager:
    def __init__(self, history: HistoryStore) -> None:
        self.history = history
        self._lock = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_requested = False
        self._thread: threading.Thread | None = None
        self._progress = ProgressSnapshot()
        self._on_update: Callable[[], None] | None = None

    def set_update_callback(self, callback: Callable[[], None]) -> None:
        self._on_update = callback

    def _notify(self) -> None:
        if self._on_update:
            self._on_update()

    def get_progress(self) -> dict[str, Any]:
        with self._lock:
            return self._progress.to_dict()

    def is_busy(self) -> bool:
        with self._lock:
            return self._progress.state in (QueueState.RUNNING, QueueState.PAUSED)

    def start(self, input_dir: str, output_dir: str, files: list[str]) -> dict[str, Any]:
        if self.is_busy():
            return {"ok": False, "error": "已有转换任务在进行中"}

        if not files:
            return {"ok": False, "error": "未找到 CAJ 文件"}

        self._stop_requested = False
        self._pause_event.set()
        batch_id = self.history.create_batch(input_dir, output_dir, len(files))

        with self._lock:
            self._progress = ProgressSnapshot(
                state=QueueState.RUNNING,
                batch_id=batch_id,
                input_dir=input_dir,
                output_dir=output_dir,
                total=len(files),
            )

        self._thread = threading.Thread(
            target=self._run,
            args=(batch_id, input_dir, output_dir, files),
            daemon=True,
        )
        self._thread.start()
        self._notify()
        return {"ok": True, "batch_id": batch_id, "total": len(files)}

    def pause(self) -> dict[str, Any]:
        with self._lock:
            if self._progress.state != QueueState.RUNNING:
                return {"ok": False, "error": "当前没有运行中的任务"}
            self._progress.state = QueueState.PAUSED
        self._pause_event.clear()
        self._notify()
        return {"ok": True}

    def resume(self) -> dict[str, Any]:
        with self._lock:
            if self._progress.state != QueueState.PAUSED:
                return {"ok": False, "error": "任务未处于暂停状态"}
            self._progress.state = QueueState.RUNNING
        self._pause_event.set()
        self._notify()
        return {"ok": True}

    def cancel(self) -> dict[str, Any]:
        if not self.is_busy():
            return {"ok": False, "error": "没有可取消的任务"}
        self._stop_requested = True
        self._pause_event.set()
        self._notify()
        return {"ok": True}

    def _append_log(self, level: str, message: str, filename: str = "") -> None:
        with self._lock:
            self._progress.logs.append(
                {"level": level, "message": message, "filename": filename}
            )

    def _run(
        self, batch_id: int, input_dir: str, output_dir: str, files: list[str]
    ) -> None:
        used_names: set[str] = set()
        success_count = 0
        failed_count = 0
        final_status = "completed"

        try:
            for source in files:
                if self._stop_requested:
                    final_status = "cancelled"
                    break

                self._pause_event.wait()

                filename = source.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
                with self._lock:
                    self._progress.current_file = filename

                output_path = resolve_output_path(output_dir, source, used_names)
                output_name = output_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]

                result = convert_caj_to_pdf(source, output_path)

                with self._lock:
                    self._progress.completed += 1

                if result.success:
                    success_count += 1
                    self.history.add_item(
                        batch_id, source, output_name, "success"
                    )
                    self._append_log(
                        "success", f"✓ {filename} → {output_name}", filename
                    )
                else:
                    failed_count += 1
                    err = result.error or "未知错误"
                    self.history.add_item(
                        batch_id, source, output_name, "failed", err
                    )
                    with self._lock:
                        self._progress.failed_files.append(
                            {"source": source, "filename": filename, "error": err}
                        )
                    self._append_log("error", f"✗ {filename}  {err}", filename)

                self._notify()
                time.sleep(0.05)
        finally:
            self.history.finish_batch(
                batch_id, success_count, failed_count, final_status
            )
            with self._lock:
                if final_status == "cancelled":
                    self._progress.state = QueueState.CANCELLED
                else:
                    self._progress.state = QueueState.COMPLETED
                self._progress.success_count = success_count
                self._progress.failed_count = failed_count
                self._progress.current_file = ""
            self._notify()
