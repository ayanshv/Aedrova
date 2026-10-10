"""Reference-led Bud configuration: a quiet native setup panel, one decision at a time."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.ai_teammates import Character
from aedrova.desktop.bud_art import LABELS, LOOKS, sprite
from aedrova.desktop.controls import ChoiceBox
from aedrova.desktop.dialogs import button, label
from aedrova.dots.roles import ROLES

COLORS = [
    ("Original", "#4388F5"),
    ("Iris", "#8275E6"),
    ("Midnight", "#303035"),
    ("Moonstone", "#A4ABB6"),
    ("Ocean", "#48A9AF"),
    ("Peach", "#E8A575"),
    ("Rose", "#D981A3"),
    ("Moss", "#7D9A78"),
]


class BudLineup(QWidget):
    """The actual bundled characters, without mock participants or fake connection states."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(142)
        self.setAccessibleName("Builder, Designer, Marketing, Finance, Research and Product Buds")

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        side = min(96, self.width() / 5.1)
        step = side * 0.82
        left = (self.width() - (5 * step + side)) / 2
        for index, look in enumerate(LOOKS):
            art = sprite(look)
            painter.drawPixmap(
                QRectF(
                    left + index * step,
                    (self.height() - side) / 2 + (side * 0.10 if index >= 3 else 0),
                    side,
                    side,
                ),
                art,
                QRectF(art.rect()),
            )


def build_setup(d, window):
    d.setWindowTitle("Aedrova · Configure your Buds")
    d.setObjectName("BudSetup")
    d.setMinimumSize(600, 650)
    d.resize(820, 800)
    outer = QVBoxLayout(d)
    outer.setContentsMargins(32, 22, 32, 22)
    toolbar = QHBoxLayout()
    toolbar.addWidget(label("Aedrova / Buds", "muted"))
    toolbar.addStretch()
    d.new = button("New Bud")
    d.new.clicked.connect(d.new_dot)
    toolbar.addWidget(d.new)
    outer.addLayout(toolbar)
    d.list = QListWidget(d)
    d.list.setProperty("accountList", True)
    d.list.setAccessibleName("Your workspace Buds")
    d.list.setMaximumHeight(54)
    d.list.currentRowChanged.connect(d.select)
    outer.addWidget(d.list)
    panel = QFrame(d)
    panel.setObjectName("BudSetupPanel")
    d.setup_panel = panel
    panel.setMinimumWidth(500)
    panel.setMaximumWidth(560)
    outer.addWidget(panel, 1, Qt.AlignmentFlag.AlignHCenter)
    column = QVBoxLayout(panel)
    column.setContentsMargins(34, 24, 34, 24)
    column.setSpacing(10)
    navigation = QHBoxLayout()
    d.progress = label("1 / 6", "muted")
    navigation.addWidget(d.progress)
    navigation.addStretch()
    d.exit_button = button("Finish later")
    d.exit_button.clicked.connect(d.accept)
    navigation.addWidget(d.exit_button)
    column.addLayout(navigation)
    d.back = button("‹  Back")
    d.back.clicked.connect(lambda: d.show_step(max(0, d.pages.currentIndex() - 1)))
    column.addWidget(d.back, alignment=Qt.AlignmentFlag.AlignLeft)
    d.pages = QStackedWidget(panel)
    column.addWidget(d.pages, 1)
    d.character = Character(parent=panel, reduced_motion=window.reduced_motion)
    d.summary = label("A little teammate. A useful connection.", "muted", wrap=True)
    d.summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
    d.capabilities = label("", "muted", wrap=True)
    d.status = label("Loading your workspace…", "muted", wrap=True)
    d.status.setTextFormat(Qt.TextFormat.PlainText)
    d.status.setObjectName("BudSetupStatus")
    d.character_layouts = {}

    def page(title, subtitle, *, centered=False):
        area = QScrollArea(panel)
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget(area)
        body.setObjectName("BudSetupPage")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(2, 16, 2, 8)
        layout.setSpacing(14)
        heading = label(title, "heading", wrap=True)
        note = label(subtitle, "muted", wrap=True)
        if centered:
            heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
            note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        layout.addWidget(note)
        area.setWidget(body)
        d.pages.addWidget(area)
        return layout

    welcome = page(
        "Set up your Buds",
        "Your team, plus AI.\nA few thoughtful choices. A teammate that feels yours.",
        centered=True,
    )
    welcome.addStretch(1)
    welcome.addWidget(BudLineup(panel))
    welcome.addWidget(d.summary)
    welcome.addStretch(2)

    looks = page("Pick your Bud’s look", "Same useful teammate. A personality you can recognize.")
    preview = QVBoxLayout()
    looks.addLayout(preview)
    d.character_layouts[1] = preview
    d.color, d.shape, d.appearance = ChoiceBox(d), ChoiceBox(d), ChoiceBox(d)
    for control in (d.color, d.shape, d.appearance):
        control.hide()
    for title, value in COLORS:
        d.color.addItem(title, value)
    for title, value in [("Planet", "round"), ("Moon", "squircle"), ("Ringed", "cloud")]:
        d.shape.addItem(title, value)
    d.appearance.addItem("Match role", "auto")
    for title, value in zip(LABELS, LOOKS, strict=True):
        d.appearance.addItem(title, value)
    grid = QGridLayout()
    grid.setSpacing(8)
    d.appearance_buttons, d.planet_buttons = [], []
    for index, (title, value) in enumerate(zip(LABELS, LOOKS, strict=True)):
        tile = QToolButton(panel)
        tile.setText(title)
        tile.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        tile.setCursor(Qt.CursorShape.PointingHandCursor)
        tile.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        tile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tile.setCheckable(True)
        tile.setProperty("budAppearance", True)
        tile.setIcon(QIcon(sprite(value)))
        tile.setIconSize(QSize(52, 52))
        tile.setMinimumHeight(86)
        tile.setAccessibleName("Choose " + title + " appearance")
        tile.clicked.connect(lambda checked=False, v=value: choose_look(d, v))
        grid.addWidget(tile, index // 3, index % 3)
        d.appearance_buttons.append((tile, value))
    looks.addLayout(grid)
    looks.addStretch()

    identity = page("Make it yours", "Give your Bud a name and choose its color.")
    custom = QHBoxLayout()
    custom.setSpacing(22)
    artwork = QVBoxLayout()
    custom.addLayout(artwork, 1)
    d.character_layouts[2] = artwork
    fields = QVBoxLayout()
    custom.addLayout(fields, 2)
    d.name = QLineEdit("Orbit", panel)
    d.name.setMaxLength(32)
    d.name.setAccessibleName("Bud name")
    fields.addWidget(label("Bud name", "muted"))
    fields.addWidget(d.name)
    fields.addSpacing(10)
    fields.addWidget(label("Color", "muted"))
    swatches = QGridLayout()
    swatches.setSpacing(8)
    d.swatch_buttons = []
    for index, (title, value) in enumerate(COLORS):
        swatch = button("")
        swatch.setFixedSize(28, 28)
        swatch.setToolTip(title)
        swatch.setAccessibleName("Bud color " + title)
        swatch.clicked.connect(
            lambda checked=False, v=value: d.color.setCurrentIndex(d.color.findData(v))
        )
        swatches.addWidget(swatch, index // 4, index % 4)
        d.swatch_buttons.append((swatch, value))
    fields.addLayout(swatches)
    custom_color = button("Custom color…")
    custom_color.clicked.connect(d.custom_color)
    d.custom_color_button = custom_color
    fields.addWidget(custom_color)
    identity.addStretch(1)
    identity.addLayout(custom)
    identity.addWidget(label("Use its name with @ in your conversation.", "muted", wrap=True))
    identity.addStretch(2)

    purpose = page("Give it a purpose", "What would make this Bud useful to your team?")
    role_preview = QVBoxLayout()
    purpose.addLayout(role_preview)
    d.character_layouts[3] = role_preview
    d.job_role = ChoiceBox(panel)
    d.job_role.setAccessibleName("Bud specialty")
    for key, (title, _, _) in ROLES.items():
        d.job_role.addItem(title, key)
    purpose.addWidget(label("Specialty", "muted"))
    purpose.addWidget(d.job_role)
    d.role = QLineEdit(panel)
    d.role.setMaxLength(240)
    d.role.setPlaceholderText("e.g. Help us stay on top of engineering")
    d.role.setAccessibleName("Bud role or purpose")
    d.instructions = QPlainTextEdit(panel)
    d.instructions.setPlaceholderText("Focus on open pull requests and explain changes concisely.")
    d.instructions.setAccessibleName("Bud instructions")
    d.instructions.setFixedHeight(100)
    purpose.addWidget(label("Role or purpose", "muted"))
    purpose.addWidget(d.role)
    purpose.addWidget(label("A little guidance · optional", "muted"))
    purpose.addWidget(d.instructions)
    purpose.addStretch()

    # Keep profile fields as state holders for existing save/version semantics.
    # The user-facing tool step is the shared connector gallery, mounted inline.
    tools = QWidget(panel)
    d.tools_layout = QVBoxLayout(tools)
    d.tools_layout.setContentsMargins(0, 12, 0, 0)
    d.pages.addWidget(tools)
    d.embedded_connectors = None
    d.provider = ChoiceBox(panel)
    d.provider.setAccessibleName("Bud connected tool")
    d.provider.currentIndexChanged.connect(d.provider_changed)
    d.resource = QLineEdit(panel)
    d.resource.setAccessibleName("Bud tool resource")
    d.recommendations = label("", "muted", wrap=True)
    d.connection_hint = label("", "muted", wrap=True)
    d.connect = button("Connect GitHub", role="primary")
    d.connect.clicked.connect(d.authorize)
    d.connector_gallery = button("Browse connectors →")
    d.connector_gallery.clicked.connect(d.open_connectors)
    d.save = button("Save changes")
    d.save.clicked.connect(d.save_dot)
    d.disconnect = button("Disconnect my access")
    d.disconnect.clicked.connect(d.disconnect_dot)
    for control in (
        d.provider,
        d.resource,
        d.recommendations,
        d.capabilities,
        d.connection_hint,
        d.connect,
        d.connector_gallery,
        d.save,
        d.disconnect,
    ):
        control.hide()

    ready = page(
        "Meet your Bud", "A familiar face. Your tools. Right in your conversation.", centered=True
    )
    ready.addStretch(1)
    final_art = QVBoxLayout()
    ready.addLayout(final_art)
    d.character_layouts[5] = final_art
    d.ready_copy = label("", "title", wrap=True)
    d.ready_copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ready.addWidget(d.ready_copy)
    note = label(
        "Mention its name to bring your connected context into the work.", "muted", wrap=True
    )
    note.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ready.addWidget(note)
    ready.addStretch(2)
    column.addWidget(d.status)
    d.dots = label("", "muted")
    d.dots.setObjectName("BudStepDots")
    d.dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
    column.addWidget(d.dots)
    d.next = button("Let’s set up your Bud →", role="primary")
    d.next.setObjectName("BudContinue")
    d.next.setMinimumWidth(260)
    d.next.clicked.connect(d.continue_setup)
    column.addWidget(d.next, alignment=Qt.AlignmentFlag.AlignHCenter)
    d.remove = button("Remove Bud")
    d.remove.clicked.connect(d.remove_dot)
    outer.addWidget(d.remove, alignment=Qt.AlignmentFlag.AlignHCenter)
    d.job_role.currentIndexChanged.connect(d.role_changed)
    for field in (d.name, d.role):
        field.textChanged.connect(d.preview)
    for control in (d.color, d.shape, d.appearance):
        control.currentIndexChanged.connect(d.preview)
    # Do not composite the entire page: descendant SpringButtons have their own
    # scale effects, which Cocoa can omit inside a parent opacity effect.
    d.opacity = QGraphicsOpacityEffect(d.character)
    d.character.setGraphicsEffect(d.opacity)
    d.transition = QPropertyAnimation(d.opacity, b"opacity", d)
    d.transition.setDuration(160)
    d.transition.setEasingCurve(QEasingCurve.Type.OutCubic)
    d.after_refresh = None
    d.show_step(0)


def choose_look(dialog, look):
    """A visual specialty selection also selects its actual role and tool recommendations."""
    dialog.appearance.setCurrentIndex(dialog.appearance.findData(look))
    dialog.job_role.setCurrentIndex(dialog.job_role.findData(look))
