from __future__ import annotations

import sys


def configure_app_identity(name: str) -> None:
    """Set bundle/process identity before pywebview loads on macOS."""
    if sys.platform != "darwin":
        return

    try:
        from Foundation import NSBundle

        bundle = NSBundle.mainBundle()
        if bundle:
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            if info is not None:
                info["CFBundleName"] = name
                info["CFBundleDisplayName"] = name
    except Exception:  # noqa: BLE001
        pass

    try:
        from AppKit import NSProcessInfo

        NSProcessInfo.processInfo().setProcessName_(name)
    except Exception:  # noqa: BLE001
        pass


def sync_pywebview_bundle_name(name: str) -> None:
    """Keep pywebview Cocoa backend in sync with the configured app name."""
    if sys.platform != "darwin":
        return

    try:
        from webview.platforms import cocoa

        if getattr(cocoa, "info", None) is not None:
            cocoa.info["CFBundleName"] = name
            cocoa.info["CFBundleDisplayName"] = name
    except Exception:  # noqa: BLE001
        pass


def fix_macos_menu_name(name: str) -> None:
    """Update the application menu title shown in the macOS menu bar."""
    if sys.platform != "darwin":
        return

    try:
        from AppKit import NSApplication

        app = NSApplication.sharedApplication()
        main_menu = app.mainMenu()
        if main_menu and main_menu.numberOfItems() > 0:
            app_menu_item = main_menu.itemAtIndex_(0)
            if app_menu_item is not None:
                app_menu_item.setTitle_(name)
    except Exception:  # noqa: BLE001
        pass
