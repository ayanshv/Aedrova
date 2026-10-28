"""Focused workspace settings: one task per section, backed by existing controls."""

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.dialogs import button, label
from aedrova.desktop.icons import icon


class WorkspaceSettingsView(QWidget):
    def __init__(self):
        super().__init__()
        outer = QGridLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setHorizontalSpacing(20)
        outer.setVerticalSpacing(20)
        outer.setColumnMinimumWidth(0, 44)
        outer.setColumnStretch(1, 1)
        outer.addWidget(label("Workspace settings", "heading"), 0, 1)
        self.workspace_slot = QVBoxLayout()
        self.workspace_slot.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self.workspace_slot, 1, 1)
        self.navigation = QVBoxLayout()
        self.navigation.setContentsMargins(0, 0, 0, 0)
        self.navigation.setSpacing(8)
        nav = QWidget()
        nav.setFixedWidth(44)
        nav.setLayout(self.navigation)
        outer.addWidget(nav, 2, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.sections = QStackedWidget()
        outer.addWidget(self.sections, 2, 1)
        outer.setRowStretch(2, 1)
        self.group = QButtonGroup(self)
        self.pages, self.buttons, self.symbols = {}, {}, []

    def add_section(self, key, title, detail, symbol):
        page = QWidget()
        column = QVBoxLayout(page)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(16)
        column.addWidget(label(title, "title"))
        column.addWidget(label(detail, "muted", wrap=True))
        self.pages[key] = self.sections.addWidget(page)
        control = button("", accessible="People" if key == "people" else title, role="icon")
        control.setToolTip(control.accessibleName())
        control.setFixedSize(44, 44)
        control.setCheckable(True)
        control.setStyleSheet(
            "QPushButton{text-align:center;padding:0;border-radius:10px;}"
            "QPushButton:checked{background:palette(highlight);color:palette(highlighted-text);}"
        )
        control.setIconSize(QSize(20, 20))
        self.symbols.append((control, symbol))
        # Native accessibility can toggle a checkable button without emitting
        # clicked. Keep the selected navigation and visible page in sync.
        control.toggled.connect(lambda checked: self.show_section(key) if checked else None)
        self.group.addButton(control)
        self.buttons[key] = control
        self.navigation.addWidget(control)
        self.refresh_icons()
        if len(self.pages) == 1:
            self.show_section(key)
        return column

    def refresh_icons(self):
        color = self.palette().color(QPalette.ColorRole.Text).name()
        for widget, symbol in self.symbols:
            selected = not isinstance(widget, QLabel) and widget.isChecked()
            artwork = icon(
                symbol,
                self.palette().color(QPalette.ColorRole.HighlightedText).name()
                if selected
                else color,
            )
            if isinstance(widget, QLabel):
                widget.setPixmap(artwork.pixmap(22, 22))
            else:
                widget.setIcon(artwork)

    def changeEvent(self, event):  # noqa: N802
        if event.type() == QEvent.Type.PaletteChange and hasattr(self, "symbols"):
            self.refresh_icons()
        super().changeEvent(event)

    def show_section(self, key):
        self.sections.setCurrentIndex(self.pages[key])
        self.buttons[key].setChecked(True)
        self.refresh_icons()
