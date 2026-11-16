"""A small, opt-in introduction to the iPhone companion."""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from aedrova.desktop.brand import ASSETS, BrandLockup
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label


def companion_section():
    section = QFrame()
    column = QVBoxLayout(section)
    column.setContentsMargins(0, 8, 0, 0)
    column.setSpacing(6)
    column.addWidget(label("Take Aedrova with you", "heading"))
    column.addWidget(
        label("Keep up with team chat and Agent replies on your phone.", "muted", wrap=True)
    )
    stores = QHBoxLayout()
    stores.setSpacing(6)
    for asset, title in (("apple.svg", "App Store"), ("google-play.svg", "Google Play")):
        mark = QLabel()
        mark.setFixedSize(24, 24)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setStyleSheet("background: white; border-radius: 6px;")
        mark.setPixmap(QIcon(str(ASSETS / asset)).pixmap(16, 16))
        stores.addWidget(mark)
        stores.addWidget(label(title, "muted"))
        stores.addSpacing(8)
    stores.addStretch()
    column.addLayout(stores)
    column.addWidget(label("Coming soon", "muted"))
    action = button("Get release updates", role="outline")
    action.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aedrova.com/waitlist")))
    column.addWidget(action, alignment=Qt.AlignmentFlag.AlignLeft)
    return section


def show_iphone_companion(window):
    existing = getattr(window, "iphone_companion", None)
    if existing:
        existing.show()
        existing.raise_()
        existing.activateWindow()
        return
    dialog = AppDialog(window)
    dialog.setWindowTitle("Aedrova for iPhone")
    dialog.setMinimumWidth(420)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(36, 38, 36, 32)
    layout.setSpacing(14)
    center = Qt.AlignmentFlag.AlignHCenter
    layout.addWidget(BrandLockup(28, 17), alignment=center)
    title = label("Aedrova for iPhone", "heading", wrap=True)
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title)
    detail = label(
        "Keep up with team chats and Agent replies when you’re away from your desk.",
        "muted",
        wrap=True,
    )
    detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
    detail.setMinimumWidth(300)
    layout.addWidget(detail)
    availability = label("Coming to iPhone", "muted")
    layout.addWidget(availability, alignment=center)
    action = button("Get release updates", role="primary")
    action.setMinimumHeight(44)
    action.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aedrova.com/waitlist")))
    layout.addWidget(action, alignment=center)
    window.iphone_companion = dialog
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
