"""Scoped settings with a stable navigation rail and one focused task per page."""

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.dialogs import button, label
from aedrova.desktop.icons import icon


class WorkspaceSettingsView(QWidget):
    def __init__(self, title="Workspace settings", detail="Changes here affect your team."):
        super().__init__()
        self.setObjectName("SettingsView")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(14)
        outer.addWidget(label(title, "heading"))
        outer.addWidget(label(detail, "muted", wrap=True))
        self.workspace_slot = QVBoxLayout()
        self.workspace_slot.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self.workspace_slot)
        body = QHBoxLayout()
        body.setSpacing(18)
        outer.addLayout(body, 1)
        nav_scroll = QScrollArea()
        nav_scroll.setObjectName("SettingsNavigation")
        nav_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        nav_scroll.setWidgetResizable(True)
        nav_scroll.viewport().setAutoFillBackground(False)
        nav_scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        nav_scroll.setFixedWidth(188)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav = QWidget()
        nav.setObjectName("SettingsSidebar")
        nav.setStyleSheet("QWidget#SettingsSidebar {background:transparent;}")
        self.navigation = QVBoxLayout(nav)
        self.navigation.setContentsMargins(0, 0, 8, 0)
        self.navigation.setSpacing(4)
        self.navigation.addStretch()
        nav_scroll.setWidget(nav)
        body.addWidget(nav_scroll)
        self.sections = QStackedWidget()
        body.addWidget(self.sections, 1)
        self.group = QButtonGroup(self)
        self.pages, self.buttons, self.symbols = {}, {}, []
        self.groups = set()

    def add_section(self, key, title, detail, symbol, *, group=None):
        if group and group not in self.groups:
            heading = label(group, "section")
            heading.setContentsMargins(10, 10 if self.groups else 0, 0, 4)
            self.navigation.insertWidget(self.navigation.count() - 1, heading)
            self.groups.add(group)
        scroll = QScrollArea()
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setStyleSheet("QScrollArea {background:transparent;border:none;}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page = QWidget()
        page.setObjectName("SettingsPage")
        page.setStyleSheet("QWidget#SettingsPage {background:transparent;}")
        column = QVBoxLayout(page)
        column.setContentsMargins(0, 0, 4, 12)
        column.setSpacing(12)
        column.addWidget(label(title, "title"))
        if detail:
            column.addWidget(label(detail, "muted", wrap=True))
        scroll.setWidget(page)
        self.pages[key] = self.sections.addWidget(scroll)
        control = button(title, accessible="People" if key == "people" else title)
        control.setObjectName("SettingsNavButton")
        control.setToolTip(title)
        control.setMinimumHeight(40)
        control.setCheckable(True)
        control.setStyleSheet(
            "QPushButton {text-align:left;padding:8px 10px;border:none;border-radius:9px;"
            "background:transparent;font-size:12px;}"
            "QPushButton:checked {background:palette(highlight);color:palette(highlighted-text);}"
        )
        control.setIconSize(QSize(18, 18))
        self.symbols.append((control, symbol))
        control.toggled.connect(lambda checked: self.show_section(key) if checked else None)
        self.group.addButton(control)
        self.buttons[key] = control
        self.navigation.insertWidget(self.navigation.count() - 1, control)
        self.refresh_icons()
        if len(self.pages) == 1:
            self.show_section(key)
        return column

    def refresh_icons(self):
        for widget, symbol in self.symbols:
            role = (
                QPalette.ColorRole.HighlightedText
                if widget.isChecked()
                else QPalette.ColorRole.Text
            )
            widget.setIcon(icon(symbol, self.palette().color(role).name()))

    def changeEvent(self, event):  # noqa: N802
        if event.type() == QEvent.Type.PaletteChange and hasattr(self, "symbols"):
            self.refresh_icons()
        super().changeEvent(event)

    def show_section(self, key):
        self.sections.setCurrentIndex(self.pages[key])
        self.buttons[key].setChecked(True)
        self.refresh_icons()
