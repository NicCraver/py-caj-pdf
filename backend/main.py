from __future__ import annotations

import sys


def main() -> None:
    from backend.config import APP_NAME, FRONTEND_DIST, app_icon_path, ensure_data_dir
    from backend.macos_app import (
        configure_app_identity,
        fix_macos_menu_name,
        sync_pywebview_bundle_name,
    )

    configure_app_identity(APP_NAME)
    ensure_data_dir()

    import webview

    sync_pywebview_bundle_name(APP_NAME)

    dist = FRONTEND_DIST
    if not dist.is_dir():
        print(f"前端未构建，请先运行: cd frontend && npm install && npm run build")
        print(f"期望路径: {dist}")
        sys.exit(1)

    from backend.api import Api

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
    icon = app_icon_path()
    webview.start(
        func=lambda: fix_macos_menu_name(APP_NAME),
        debug=False,
        icon=str(icon) if icon else None,
    )


if __name__ == "__main__":
    main()
