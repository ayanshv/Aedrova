from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from aedrova.desktop.controls import AppDialog
from aedrova.desktop.materials import SpringButton, system_font


def label(text, role="", *, wrap=False):
    from aedrova.desktop.design_system import TYPE

    widget = QLabel(text)
    if role in ("display", "heading", "title"):
        widget.setFont(system_font(TYPE[role], QFont.Weight.DemiBold))
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap or role in ("heading", "title"))
    if widget.wordWrap() and role not in ("heading", "title"):
        widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
    if role:
        widget.setProperty("role", role)
    return widget


def button(text, accessible="", role=""):
    import re

    visible = re.sub(r"(?<!&)&(?!&)", "&&", text)
    widget = SpringButton(visible)
    widget.setAccessibleName(accessible or text.replace("&&", "&"))
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if role == "icon" and accessible:
        widget.setToolTip(accessible)
    if role:
        widget.setProperty("role", role)
    from aedrova.desktop.icons import SYMBOLS, assign

    if text in SYMBOLS:
        assign(widget, SYMBOLS[text])
        widget.setText("")
        widget.setToolTip(accessible or SYMBOLS[text].replace("_", " ").title())
    return widget


def apple_sign_in_button():
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QIcon

    from aedrova.desktop.brand import ASSETS

    control = button("Sign in with Apple")
    control.setIcon(QIcon(str(ASSETS / "apple.svg")))
    control.setIconSize(QSize(18, 18))
    control.setMinimumHeight(44)
    control.setStyleSheet(
        "QPushButton {background:white;color:black;border:1px solid #d0d0d0;"
        "border-radius:10px;font-weight:500;text-align:center;} "
        "QPushButton:hover {background:#f5f5f5;} "
        "QPushButton:pressed {background:#e5e5e5;} "
        "QPushButton:focus {border-color:#246bfd;} "
        "QPushButton:disabled {background:#ededed;color:#676767;}"
    )
    return control


def icon_button(name, title, *, primary=False):
    """Compact action with a visible glyph, tooltip and full accessible label."""
    from PySide6.QtCore import QSize

    from aedrova.desktop.icons import assign

    control = button("", accessible=title, role="primary" if primary else "icon")
    control.setObjectName("WorkspaceAction")
    control.setFixedSize(44, 44)
    assign(control, name)
    control.setIconSize(QSize(20, 20))
    control.setToolTip(title)
    return control


def row_button(name, title):
    """A labeled sidebar row: glyph, plain words, the full row is the target."""
    from PySide6.QtCore import QSize

    from aedrova.desktop.icons import assign

    control = button(title, accessible=title)
    control.setObjectName("SidebarRow")
    control.setMinimumHeight(34)
    control.setCursor(Qt.CursorShape.PointingHandCursor)
    assign(control, name)
    control.setIconSize(QSize(16, 16))
    control.setToolTip(title)
    return control


class CreateDialog(AppDialog):
    def __init__(self, parent, *, workspace, create):
        super().__init__(parent)
        self.create = create
        self.result_object = None
        self.setWindowTitle("Create workspace" if workspace else "Create channel")
        self.setModal(True)
        self.resize(480, 400 if workspace else 480)
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 30, 32, 30)
        layout.setSpacing(14)
        layout.addWidget(label(self.windowTitle(), "title"))
        layout.addWidget(
            label(
                "Make room for your next idea." if workspace else "Give this conversation a home.",
                "muted",
            )
        )
        self.name = QLineEdit()
        self.name.setMaxLength(32)
        self.name.setPlaceholderText("e.g. Northstar Labs" if workspace else "e.g. launch-planning")
        self.name.setAccessibleName("Workspace name" if workspace else "Channel name")
        caption = label("Name")
        caption.setBuddy(self.name)
        layout.addWidget(caption)
        layout.addWidget(self.name)
        self.topic = QLineEdit()
        self.topic.setMaxLength(120)
        self.topic.setPlaceholderText("What is this channel for?")
        self.topic.setAccessibleName("Channel topic")
        if not workspace:
            topic_label = label("Topic · optional")
            topic_label.setBuddy(self.topic)
            layout.addWidget(topic_label)
            layout.addWidget(self.topic)
        else:
            self.topic.hide()
        layout.addWidget(
            label(
                "Demo workspace. It resets when you close the app.", "muted", wrap=True
            )
        )
        self.error = label("", "error", wrap=True)
        self.error.hide()
        layout.addWidget(self.error)
        actions = QHBoxLayout()
        actions.addStretch()
        cancel = button("Cancel")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        self.submit = button("Create workspace" if workspace else "Create channel", role="primary")
        self.submit.setDefault(True)
        self.submit.clicked.connect(self.save)
        actions.addWidget(self.submit)
        layout.addLayout(actions)

    def save(self):
        try:
            self.result_object = self.create(self.name.text(), self.topic.text())
        except ValueError as exc:
            self.error.setText(str(exc))
            self.error.show()
            self.name.setFocus()
            return
        self.accept()


class SwitcherDialog(AppDialog):
    chosen = Signal(str, str)

    def __init__(self, parent, store):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Jump to a conversation")
        self.setModal(True)
        self.resize(560, 430)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find a channel, person, or workspace…")
        self.search.setAccessibleName("Search channels and workspaces")
        self.search.installEventFilter(self)
        layout.addWidget(self.search)
        self.results = QListWidget()
        self.results.setObjectName("Switcher")
        self.results.setAccessibleName("Conversation search results")
        layout.addWidget(self.results)
        self.empty = label("No conversations match your search.", "muted")
        layout.addWidget(self.empty)
        layout.addWidget(label("↑ ↓ to navigate     ↵ to open     esc to close", "muted"))
        self.search.textChanged.connect(self.filter)
        self.search.returnPressed.connect(self.choose_current)
        self.results.itemActivated.connect(lambda _: self.choose_current())
        self.results.itemClicked.connect(lambda _: self.choose_current())
        self.filter("")

    def filter(self, query):
        self.results.clear()
        query = query.strip().casefold()
        for workspace in self.store.workspaces:
            for channel in workspace.channels:
                prefix = "" if channel.direct else "# "
                text = f"{prefix}{channel.name}   /   {workspace.name}"
                if query in text.casefold():
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, (workspace.id, channel.id))
                    self.results.addItem(item)
        self.empty.setVisible(self.results.count() == 0)
        if self.results.count():
            self.results.setCurrentRow(0)

    def choose_current(self):
        item = self.results.currentItem()
        if item:
            self.chosen.emit(*item.data(Qt.ItemDataRole.UserRole))
            self.accept()

    def eventFilter(self, watched, event):  # noqa: N802
        if watched is self.search and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                delta = 1 if event.key() == Qt.Key.Key_Down else -1
                row = min(max(0, self.results.currentRow() + delta), self.results.count() - 1)
                self.results.setCurrentRow(row)
                return True
        return super().eventFilter(watched, event)


def trailing_chevron(control):
    """A drawn disclosure chevron after the text, in place of a typed glyph."""
    from PySide6.QtCore import QSize

    from aedrova.desktop.icons import assign

    assign(control, "chevron")
    control.setIconSize(QSize(14, 14))
    control.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    # Right-to-left layout mirrors alignment, so this keeps the words at the left edge.
    control.setStyleSheet(control.styleSheet() + " text-align: right;")
    return control


class InsetRow(QPushButton):
    """One row of an inset group: glyph, title with a line of detail, and a chevron."""

    def __init__(self, symbol, title, detail=""):
        super().__init__()
        from PySide6.QtCore import QSize
        from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

        from aedrova.desktop.icons import icon

        self.setObjectName("InsetRow")
        self.symbol = symbol
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(title)
        self.setAccessibleDescription(detail)
        self.setMinimumHeight(56 if detail else 46)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 8, 14, 8)
        row.setSpacing(12)
        self.glyph = QLabel()
        self.glyph.setFixedSize(QSize(20, 20))
        color = self.palette().windowText().color().name()
        self.glyph.setPixmap(icon(symbol, color).pixmap(20, 20))
        self.glyph.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(self.glyph)
        text = QVBoxLayout()
        text.setSpacing(1)
        self.title = QLabel(title)
        self.title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text.addWidget(self.title)
        self.detail = QLabel(detail)
        self.detail.setProperty("role", "muted")
        self.detail.setWordWrap(True)
        self.detail.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.detail.setVisible(bool(detail))
        text.addWidget(self.detail)
        row.addLayout(text, 1)
        self.chevron = QLabel()
        self.chevron.setFixedSize(QSize(16, 16))
        self.chevron.setPixmap(icon("chevron_right", self.muted_color()).pixmap(16, 16))
        self.chevron.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(self.chevron)

    def changeEvent(self, event):  # noqa: N802
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.Type.PaletteChange and hasattr(self, "symbol"):
            from aedrova.desktop.icons import icon

            color = self.palette().windowText().color().name()
            self.glyph.setPixmap(icon(self.symbol, color).pixmap(20, 20))
            self.chevron.setPixmap(icon("chevron_right", self.muted_color()).pixmap(16, 16))
        super().changeEvent(event)

    def muted_color(self):
        from PySide6.QtGui import QPalette

        return self.palette().color(QPalette.ColorRole.PlaceholderText).name()

    def set_detail(self, text):
        self.detail.setText(text)
        self.detail.setVisible(bool(text))
        self.setAccessibleDescription(text)


def inset_group(rows):
    """Rows in one rounded group with hairline separators, like Apple's grouped lists."""
    from PySide6.QtWidgets import QFrame, QVBoxLayout

    group = QFrame()
    group.setObjectName("InsetGroup")
    column = QVBoxLayout(group)
    column.setContentsMargins(0, 0, 0, 0)
    column.setSpacing(0)
    for index, row in enumerate(rows):
        if index:
            line = QFrame()
            line.setObjectName("InsetSeparator")
            line.setFixedHeight(1)
            column.addWidget(line)
        column.addWidget(row)
    return group
