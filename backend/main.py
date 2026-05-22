from __future__ import annotations

import sys

import webview

from backend.api import Api
from backend.config import APP_NAME, FRONTEND_DIST, ensure_data_dir


def main() -> None:
    ensure_data_dir()
    dist = FRONTEND_DIST
    if not dist.is_dir():
        print(f"前端未构建，请先运行: cd frontend && npm install && npm run build")
        print(f"期望路径: {dist}")
        sys.exit(1)

    api = Api()
    window = webview.create_window(
        title=APP_NAME,
        url=str(dist / "index.html"),
        width=960,
        height=720,
        min_size=(800, 600),
        js_api=api,
    )
    api.window = window
    webview.start(debug=False)


if __name__ == "__main__":
    main()
