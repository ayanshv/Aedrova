"""Launch the milestone 2 local desktop preview."""

import argparse
import json
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication

from aedrova.desktop.brand import app_icon
from aedrova.desktop.window import AedrovaWindow


def main():
    parser = argparse.ArgumentParser(description="Aedrova desktop · local preview")
    parser.add_argument("--theme", choices=("light", "dark", "system"))
    parser.add_argument("--smoke-report", type=Path)
    parser.add_argument("--settings-file", type=Path)
    parser.add_argument("--thread", action="store_true")
    parser.add_argument("--demo", action="store_true", help="Open the local sample chat preview")
    parser.add_argument("--account", action="store_true", help="Open account and workspace setup")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=940)
    args = parser.parse_args()
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("Aedrova")
    app.setOrganizationName("Aedrova")
    app.setStyle("Fusion")
    app.setWindowIcon(app_icon())
    settings = (
        QSettings(str(args.settings_file), QSettings.Format.IniFormat)
        if args.settings_file
        else None
    )
    window = AedrovaWindow(settings=settings)
    if args.theme:
        window.set_theme(args.theme, persist=False)
    window.resize(args.width, args.height)
    account_first = args.account or (not args.demo and not args.smoke_report)
    if not account_first:
        window.show()
    if args.thread:
        window.open_pinned()
    if account_first:
        window.show_account()
    if args.smoke_report:

        def capture():
            args.smoke_report.parent.mkdir(parents=True, exist_ok=True)
            target = window.account_dialog if args.account else window
            saved = target.grab().save(str(args.smoke_report.with_suffix(".png")))
            result = {
                "milestone": 3 if args.account else 2,
                "account_screen": args.account,
                "packaged": bool(getattr(sys, "frozen", False)),
                "theme": window.theme.name,
                "workspace": window.workspace.name,
                "channel": window.channel.name,
                "messages": window.messages.model().rowCount(),
                "tabs": window.pages.count(),
                "thread_open": bool(window.thread_id),
                "width": window.width(),
                "height": window.height(),
                "screenshot_saved": saved,
                "network_services": "not connected; local preview",
            }
            args.smoke_report.write_text(json.dumps(result, indent=2) + "\n")
            app.exit(0 if saved else 1)

        QTimer.singleShot(500, capture)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
