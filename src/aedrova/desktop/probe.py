"""Technical spike, not the milestone 2 product dashboard."""

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

from PySide6.QtCore import QAbstractListModel, Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QListView, QVBoxLayout, QWidget


class MessageModel(QAbstractListModel):
    """Virtualized fixture: no QWidget per message and no eagerly generated history."""

    def __init__(self, count: int = 50_000):
        super().__init__()
        self.count = count

    def rowCount(self, parent=None):  # noqa: N802
        return 0 if parent is not None and parent.isValid() else self.count

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and 0 <= index.row() < self.count:
            if role == Qt.ItemDataRole.DisplayRole:
                return f"Teammate · message {index.row() + 1:,}   Discuss → decide → build."
        return None


class ProbeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aedrova · Milestone 1 technical probe")
        self.resize(960, 640)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(QLabel("AEDROVA   /   Desktop feasibility"))
        layout.addWidget(QLabel("50,000 synthetic messages · virtualized list · no network"))
        self.messages = QListView()
        self.messages.setAccessibleName("Synthetic message history")
        self.model = MessageModel()
        self.messages.setModel(self.model)
        self.messages.setUniformItemSizes(True)
        layout.addWidget(self.messages)
        layout.addWidget(
            QLabel("Technical validation only. Product interface starts in milestone 2.")
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-report", type=Path)
    args = parser.parse_args()
    start = perf_counter()
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = ProbeWindow()
    window.show()
    if args.smoke_report:

        def finish():
            window.messages.scrollToBottom()
            app.processEvents()
            args.smoke_report.parent.mkdir(parents=True, exist_ok=True)
            screenshot = args.smoke_report.with_suffix(".png")
            saved = window.grab().save(str(screenshot))
            report = {
                "rows": window.model.rowCount(),
                "last_row_visible": window.messages.verticalScrollBar().value()
                == window.messages.verticalScrollBar().maximum(),
                "elapsed_seconds": round(perf_counter() - start, 3),
                "screenshot_saved": saved,
                "packaged": bool(getattr(sys, "frozen", False)),
                "platform": sys.platform,
            }
            args.smoke_report.write_text(json.dumps(report, indent=2) + "\n")
            app.exit(0 if saved and report["last_row_visible"] else 1)

        QTimer.singleShot(200, finish)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
