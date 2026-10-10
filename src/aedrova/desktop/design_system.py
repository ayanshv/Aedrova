"""Aedrova Workroom: quiet surfaces, precise type and responsive native primitives."""

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QBoxLayout, QLayout, QSizePolicy, QVBoxLayout, QWidget

SPACE = (4, 8, 12, 16, 24, 32, 48)
TYPE = {"display": 30, "heading": 24, "title": 18, "body": 14, "muted": 12, "section": 11}
RADIUS = {"control": 7, "panel": 10, "menu": 16}
MOTION = {"press": 90, "hover": 120, "transition": 180}


class FlowActions(QLayout):
    """Action rows wrap at narrow widths; no button is compressed or clipped."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(8)

    def addItem(self, item):
        self.items.append(item)

    def insertWidget(self, index, widget):
        self.addWidget(widget)
        item = self.items.pop()
        self.items.insert(max(0, min(index, len(self.items))), item)
        self.invalidate()

    def addStretch(self, *args):
        pass

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index):
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.arrange(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.arrange(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.items:
            if not item.isEmpty():
                size = size.expandedTo(item.minimumSize())
        return size

    def arrange(self, rect, measure):
        x, y, height = rect.x(), rect.y(), 0
        for item in self.items:
            if item.isEmpty():
                continue
            size = item.sizeHint().expandedTo(item.minimumSize())
            size.setWidth(min(size.width(), max(1, rect.width())))
            if x > rect.x() and x + size.width() > rect.right() + 1:
                x, y, height = rect.x(), y + height + self.spacing(), 0
            if not measure:
                item.setGeometry(QRect(QPoint(x, y), size))
            x += size.width() + self.spacing()
            height = max(height, size.height())
        return y + height - rect.y()


class MasterDetail(QWidget):
    """A persistent list beside an editor, stacked on compact desktop windows."""

    def __init__(self, listing, editor, parent=None):
        super().__init__(parent)
        self.listing, self.editor = listing, editor
        self.row = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(24)
        self.row.addWidget(listing)
        self.row.addWidget(editor, 1)
        self.setMinimumWidth(0)

    def resizeEvent(self, event):
        compact = self.width() < 900
        self.row.setDirection(
            QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight
        )
        self.listing.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.listing.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.listing.setMinimumWidth(0 if compact else 224)
        self.listing.setMaximumWidth(16777215 if compact else 256)
        self.listing.setMaximumHeight(132 if compact else 16777215)
        self.listing.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        super().resizeEvent(event)


def section(parent_layout, title, description=""):
    from aedrova.desktop.dialogs import label

    container = QWidget()
    container.setObjectName("SettingsSection")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 16, 0, 20)
    layout.setSpacing(12)
    layout.addWidget(label(title, "title"))
    if description:
        layout.addWidget(label(description, "muted", wrap=True))
    parent_layout.addWidget(container)
    return layout
