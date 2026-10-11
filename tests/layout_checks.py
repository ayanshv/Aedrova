"""Wait for Qt's queued layout pass and report genuine compact-width overflow."""

from PySide6.QtWidgets import QHBoxLayout, QWidget


def no_horizontal_overflow(qtbot, scroll):
    try:
        qtbot.waitUntil(lambda: scroll.horizontalScrollBar().maximum() == 0, timeout=1500)
    except Exception:
        body = scroll.widget()
        print(
            "viewport/content/minimum",
            scroll.viewport().width(),
            body.width(),
            body.minimumSizeHint().width(),
        )
        for row in body.findChildren(QHBoxLayout):
            print("row minimum", row.minimumSize().width())
        for control in body.findChildren(QWidget):
            if control.minimumSizeHint().width() > 150:
                print(
                    type(control).__name__,
                    control.objectName(),
                    getattr(control, "text", lambda: "")()[:120],
                    control.width(),
                    control.minimumSizeHint().width(),
                )
        raise
