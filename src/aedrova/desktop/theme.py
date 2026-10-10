"""Workroom semantic palette: neutral surfaces, blue action and quiet state hierarchy."""

from dataclasses import dataclass

from PySide6.QtGui import QColor, QPalette


@dataclass(frozen=True)
class Theme:
    name: str
    canvas: str
    bg: str
    rail: str
    sidebar: str
    surface: str
    hover: str
    border: str
    text: str
    secondary: str
    muted: str
    accent: str
    accent_bg: str
    accent_text: str
    primary_text: str
    avatars: tuple[str, ...]


LIGHT = Theme(
    "light",
    "#F5F6F8",
    "#FFFFFF",
    "#F5F6F8",
    "#F5F6F8",
    "#F5F6F8",
    "#EBEBEE",
    "#E4E7EC",
    "#20242C",
    "#414955",
    "#667180",
    "#246BFD",
    "#EDF3FF",
    "#1954D1",
    "#FFFFFF",
    ("#E4E7EC", "#EDEDEF", "#E4E4E7", "#E9E9EC"),
)
DARK = Theme(
    "dark",
    "#0C0C0D",
    "#141415",
    "#0C0C0D",
    "#141415",
    "#1C1C1E",
    "#262628",
    "#333336",
    "#F5F6F8",
    "#CACACF",
    "#A0A0A8",
    "#6C9EFF",
    "#202D45",
    "#A8C6FF",
    "#0C0C0D",
    ("#353537", "#262628", "#38383B", "#323235"),
)


def palette(theme: Theme):
    result = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, theme.bg),
        (QPalette.ColorRole.WindowText, theme.text),
        (QPalette.ColorRole.Base, theme.bg),
        (QPalette.ColorRole.AlternateBase, theme.surface),
        (QPalette.ColorRole.Text, theme.text),
        (QPalette.ColorRole.Button, theme.surface),
        (QPalette.ColorRole.ButtonText, theme.text),
        (QPalette.ColorRole.Highlight, theme.accent_bg),
        (QPalette.ColorRole.HighlightedText, theme.accent_text),
        (QPalette.ColorRole.PlaceholderText, theme.muted),
        (QPalette.ColorRole.ToolTipBase, theme.surface),
        (QPalette.ColorRole.ToolTipText, theme.text),
    ):
        result.setColor(role, QColor(color))
    for role in (
        QPalette.ColorRole.Text,
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.ButtonText,
        QPalette.ColorRole.PlaceholderText,
    ):
        result.setColor(QPalette.ColorGroup.Disabled, role, QColor(theme.muted))
    return result


def stylesheet(t: Theme, *, reduced_transparency=False):
    # QFontDatabase supplies the platform system family (San Francisco on macOS).
    white = t.name == "light"
    capsule = t.bg
    if reduced_transparency:
        capsule = t.surface
    selected = t.accent_bg
    bud_surface = "#FEFDFC" if t.name == "light" else t.surface
    return f"""
    QDialog#Connectors {{ background: {t.bg}; }}
    QDialog#EmbeddedConnectors {{ background: transparent; }}
    QFrame#ConnectorRail {{ background: {t.canvas}; border-right: 1px solid {t.border}; }}
    QWidget#ConnectorGallery {{ background: transparent; }}
    QFrame#ConnectorCard {{ background: {t.bg}; border: 1px solid {t.border};
        border-radius: 12px; }}
    QFrame#ConnectorCard:hover {{ border-color: {t.accent}; }}
    QFrame#ConnectorFeature {{ background: {t.canvas}; border: 1px solid {t.border};
        border-radius: 14px; }}
    QLabel#ConnectorGlyph {{ background: {t.canvas}; border-radius: 9px; color: {t.text}; }}
    QDialog#BudSetup {{ background: {t.canvas}; }}
    QFrame#BudSetupPanel {{ background: {bud_surface};
        border: 1px solid {t.border}; border-radius: 22px; }}
    QWidget#BudSetupPage {{ background: transparent; }}
    QFrame#BudSetupPanel QScrollArea {{ background: transparent; border: none; }}
    QPushButton#BudContinue {{ border-radius: 19px; padding: 10px 24px; min-height: 18px; }}
    QToolButton[budAppearance="true"] {{ border: 1px solid transparent;
        border-radius: 14px; padding: 6px; }}
    QToolButton[budAppearance="true"]:hover {{ background: {t.hover}; }}
    QToolButton[budAppearance="true"]:checked {{ border: 1px solid {t.accent};
        background: {t.accent_bg}; }}
    QToolButton[budAppearance="true"] {{ color: {t.text}; background: transparent;
        font-size: 12px; }}
    QToolButton[budAppearance="true"]:focus {{ border: 1px solid {t.accent}; }}
    QToolButton[budAppearance="true"]:pressed {{ background: {t.border}; }}
    QToolButton[budAppearance="true"]:disabled {{ color: {t.muted}; }}
    QLabel#BudStepDots {{ color: {t.accent}; font-size: 12px; }}

    QWidget {{ color: {t.text}; font-size: 14px; }}
    QFrame#Topbar {{ border-bottom: 1px solid {t.border}; }}
    QFrame#ChannelHeader {{ border-bottom: 1px solid {t.border}; }}
    QWidget#SettingsSection {{ border-bottom: 1px solid {t.border}; }}
    QLabel#AgentIdentity {{ color: {t.accent_text}; background: {t.accent_bg};
        font-size: 10px; padding: 2px 6px; border-radius: 4px; }}
    QMainWindow, QDialog, QStackedWidget#AccountPages, QWidget#AccountPage {{ background: {t.bg}; }}
    QWidget#AccountLoginCard {{ background: {t.bg}; border: none;
        border-radius: 10px; }}
    QComboBox {{ background: {t.bg}; border: 1px solid transparent;
        border-radius: 7px; padding: 10px; min-width: 75px; }}
    QComboBox::drop-down {{ border: none; width: 30px; background: transparent; }}
    QComboBox:focus {{ border-color: {t.accent}; }}
    QComboBox::down-arrow {{ image: none; border: none; width: 0px; height: 0px; }}
    QComboBox QAbstractItemView {{ background: {t.bg}; color: {t.text};
        border: none; border-radius: 7px; padding: 6px;
        selection-background-color: {t.accent_bg}; selection-color: {t.accent_text};
        outline: none; }}
    QFrame#ChoicePopup {{ background: {t.bg}; border: none;
        border-radius: 16px; padding: 0; }}
    QListView#ChoiceList, QListView#ChoiceList:focus {{ border: none; outline: none; }}
    QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 5px 12px;
        border-radius: 8px; }}
    QCheckBox {{ spacing: 9px; padding: 4px 0; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {t.muted};
        border-radius: 5px; background: {t.surface}; }}
    QCheckBox::indicator:checked {{ background: {t.accent}; border-color: {t.accent}; }}
    QProgressBar {{ border: none; border-radius: 3px; background: {t.surface};
        max-height: 6px; min-height: 6px; }}
    QProgressBar::chunk {{ background: {t.accent}; border-radius: 3px; }}
    QTabWidget::pane {{ border: 1px solid {t.border}; border-radius: 8px; }}
    QTabBar::tab {{ background: {t.surface}; padding: 10px 18px; }}
    QTabBar::tab:selected {{ background: {t.accent_bg}; color: {t.accent_text}; }}
    QListWidget[accountList="true"] {{ background: {t.surface};
        border: 1px solid {t.border}; border-radius: 7px; padding: 6px; }}
    QListWidget[accountList="true"]::item {{ padding: 7px; border-radius: 6px; }}
    QListWidget[accountList="true"]::item:selected {{
        background: {t.accent_bg}; color: {t.accent_text}; }}
    QWidget#Chat, QWidget#Thread, QFrame#Rail {{ background: transparent; border: none; }}
    QFrame#Topbar, QFrame#ChannelHeader {{ background: {t.bg}; }}
    QLabel {{ background: transparent; border: none; }}
    QLabel[role='muted'] {{ color: {t.muted}; font-size: 12px; }}
    QLabel#MessageTimestamp {{ color: {t.secondary}; font-size: 11px; }}
    QLabel#ShortcutFooter {{ color: {t.secondary}; font-size: 12px; }}
    QLabel[role='section'] {{ color: {t.muted}; font-size: 11px; font-weight: 500; }}
    QLabel[role='title'] {{ font-size: 18px; font-weight: 600; }}
    QLabel[role='display'] {{ font-size: 30px; font-weight: 600; }}
    QLabel[role='heading'] {{ font-size: 24px; font-weight: 600; }}
    QLabel[role='badge'] {{ color: {t.secondary}; background: {capsule};
        border-radius: 11px; padding: 5px 10px; font-size: 11px; font-weight: 500; }}
    QLabel[role='error'] {{ color: {"#B4232F" if white else "#FF8A92"}; font-size: 12px; }}
    QFrame#Composer {{ background: {capsule}; border: 1px solid {t.border}; border-radius: 14px; }}
    QFrame#Composer[focused='true'] {{ border: 1px solid {t.accent}; }}
    QLabel#ComposerCue {{ color: {t.muted}; font-size: 10px; font-weight: 500; padding-left: 8px; }}
    QPushButton#WorkspaceToolsToggle {{ color: {t.secondary}; font-size: 12px; padding: 7px 8px; }}
    QWidget#WorkspaceTools QPushButton {{ padding: 5px 9px; font-size: 11px; min-height: 22px; }}
    QLabel#SpaceSymbol {{ color: {t.accent}; font-size: 20px; }}
    QFrame#Quiet {{ background: transparent; border-top: 1px solid {t.border}; }}
    QFrame#AudioCallStage {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 10px; }}
    QFrame#AudioParticipant {{ background: {t.bg}; border: 1px solid {t.border};
        border-radius: 10px; }}
    QFrame#AudioParticipant[speaking="true"] {{ border: 1px solid {t.accent}; }}
    QFrame#TeamSection {{ background: transparent; border: none;
        border-radius: 10px; }}
    QSlider::groove:horizontal {{ height: 6px; background: {t.border}; border-radius: 3px; }}
    QSlider::sub-page:horizontal {{ background: {t.accent}; border-radius: 3px; }}
    QSlider::handle:horizontal {{ background: {t.bg}; border: 2px solid {t.accent}; width: 16px;
        margin: -6px 0; border-radius: 9px; }}
    QSlider::handle:horizontal:hover {{ background: {t.accent_bg}; }}
    QSlider::handle:horizontal:focus {{ border: 3px solid {t.accent}; }}
    QSlider::handle:horizontal:disabled {{ border-color: {t.muted}; }}
    QFrame#CallBar {{ background: transparent; border: none;
        border-radius: 10px; }}
    QWidget#Segments {{ background: transparent; border: none;
        border-radius: 7px; }}
    QPushButton {{ background: transparent; border: 1px solid transparent;
        border-radius: 7px; padding: 8px 12px; text-align: left; font-weight: 500; }}
    QPushButton:hover {{ background: {t.hover}; }}
    QPushButton:pressed {{ background: {t.border}; }}
    QPushButton:focus, QLineEdit:focus, QPlainTextEdit:focus, QListView:focus {{
        border: 1px solid {t.accent}; }}
    QPushButton:checked {{ background: {t.accent_bg}; color: {t.accent_text}; }}
    QPushButton:disabled {{ color: {t.muted}; }}
    QPushButton[role='primary'] {{ background: {t.accent}; color: {t.primary_text};
        padding: 9px 18px; border-radius: 8px; font-weight: 600; text-align: center; }}
    QPushButton[role='primary']:hover {{ background: {"#1954D1" if white else "#89B2FF"}; }}
    QPushButton[role='primary']:pressed {{ background: {"#004C99" if white else "#0071E3"}; }}
    QPushButton[role='primary']:disabled {{ background: {t.hover}; color: {t.muted}; }}
    QPushButton[role='outline'] {{ border: 1px solid {t.border}; background: {t.bg}; }}
    QPushButton[role='outline']:hover {{ background: {t.surface}; border-color: {t.muted}; }}
    QPushButton[role='icon'] {{ padding: 0px; text-align: center; }}
    QPushButton[role='workspace'] {{ border-radius: 7px; font-size: 17px;
        font-weight: 600; text-align: center; padding: 0px; }}
    QPushButton[role='workspace']:checked {{ background: {t.text}; color: {t.bg}; }}
    QPushButton[role='tab'] {{ padding: 9px 12px; border-radius: 0px; font-size: 12px;
        color: {t.secondary}; }}
    QPushButton[role='tab']:checked {{ background: transparent; color: {t.accent_text};
        border: none; border-bottom: 2px solid {t.accent}; font-weight: 600; }}
    QPushButton#Pinned {{ background: {t.accent_bg}; color: {t.secondary};
        border: 1px solid {t.border}; border-radius: 8px; padding: 12px 17px; font-size: 12px; }}
    QPushButton#Search {{ background: {t.surface}; color: {t.muted}; border: 1px solid {t.border};
        border-radius: 7px; padding: 8px 16px; font-size: 12px; }}
    QListWidget#Navigation {{ border: none; background: transparent; outline: none; }}
    QListWidget#Navigation::item {{ height: 30px; border-radius: 4px; padding-left: 10px; }}
    QListWidget#Navigation::item:selected {{ background: {selected}; color: {t.accent_text};
        border-left: 2px solid {t.accent}; }}
    QListWidget#Navigation::item:hover {{ background: {t.hover}; }}
    QListView#Messages {{ border: 1px solid transparent; background: transparent; outline: none; }}
    QListWidget#Switcher {{ background: transparent; border: none; }}
    QListWidget#Switcher::item {{ padding: 14px; border-radius: 7px; }}
    QListWidget#Switcher::item:selected {{ background: {t.accent_bg}; color: {t.accent_text}; }}
    QPlainTextEdit {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: 7px;
        padding: 8px; selection-background-color: {t.accent_bg}; }}
    QPlainTextEdit#ComposerEditor, QPlainTextEdit#ComposerEditor:focus {{
        background: transparent; border: 1px solid transparent; }}
    QPlainTextEdit#BuildRequest {{ border: 1px solid {t.border};
        background: {t.surface}; border-radius: 8px; padding: 12px; }}
    QPlainTextEdit#BuildRequest:focus {{ border-color: {t.accent}; }}
    QPlainTextEdit#ProfileBio {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 8px; padding: 12px; color: {t.text}; }}
    QPlainTextEdit#ProfileBio:focus {{ border-color: {t.accent}; }}
    QLineEdit {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: 8px;
        padding: 10px; selection-background-color: {t.accent_bg}; }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 7px; margin: 6px 1px; }}
    QScrollBar::handle:vertical {{ background: {t.border}; min-height: 32px; border-radius: 3px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    QScrollBar:horizontal {{ background: transparent; height: 7px; margin: 1px 6px; }}
    QScrollBar::handle:horizontal {{ background: {t.border}; min-width: 32px; border-radius: 3px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}
    QListWidget#ChatResults {{ background: {t.bg}; border: 1px solid {t.border};
        border-radius: 10px; padding: 10px; outline: none; }}
    QListWidget#ChatResults::item {{ padding: 14px 12px; border: none;
        border-radius: 7px; color: {t.text}; }}
    QListWidget#ChatResults::item:hover {{ background: {t.hover}; }}
    QListWidget#ChatResults::item:selected {{ background: {t.accent_bg}; color: {t.text}; }}
    QListWidget#EmojiGrid {{ background: {t.bg}; border: none; border-radius: 8px;
        outline: none; font-size: 20px; }}
    QListWidget#EmojiGrid::item {{ padding: 0; margin: 2px; border-radius: 8px; }}
    QListWidget#EmojiGrid::item:hover {{ background: {t.hover}; }}
    QListWidget#EmojiGrid::item:selected {{ background: {t.accent_bg}; }}
    QFrame#ReactionBar {{ background: {t.bg}; border: 1px solid {t.border};
        border-radius: 8px; }}
    QFrame#ReactionBar QPushButton {{ border: none; border-radius: 9px;
        background: transparent; padding: 0; margin: 0;
        text-align: center; font-size: 16px; }}
    QFrame#ReactionBar QPushButton:hover {{ background: {t.hover}; }}
    QMenu {{ background: {t.bg}; border: none; padding: 8px; border-radius: 16px; }}
    QMenu::item {{ padding: 10px 24px 10px 12px; border-radius: 8px; }}
    QMenu::separator {{ height: 1px; background: {t.border}; margin: 6px 8px; }}
    QMenu::item:disabled {{ color: {t.muted}; }}
    QMenu::item:selected {{ background: {t.accent_bg}; }}
    QMenu::item:selected:enabled {{ color: {t.accent_text}; }}
    QToolButton:focus {{ border: 1px solid {t.accent}; border-radius: 7px; }}
    QToolButton:disabled, QComboBox:disabled {{ color: {t.muted}; }}
    QComboBox:hover:enabled {{ background: {t.hover}; border-color: transparent; }}
    QLineEdit:hover:enabled {{ border-color: {t.muted}; }}
    QComboBox:focus, QLineEdit:focus {{ border-color: {t.accent}; }}
    QCheckBox:disabled {{ color: {t.muted}; }}
    QCheckBox::indicator:disabled {{ border-color: {t.border}; background: {t.hover}; }}
    QCheckBox::indicator:focus {{ border-color: {t.accent}; }}
    QDialogButtonBox QPushButton {{ text-align: center; min-width: 72px; }}
    QMessageBox {{ min-width: 420px; }}
    QMessageBox QPushButton {{ min-width: 96px; text-align: center; }}
    QDialogButtonBox QPushButton:default {{ background: {t.accent}; color: {t.primary_text}; }}
    QFrame#CallToolbar {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 10px; }}
    QToolButton#CallControl {{ background: transparent; color: {t.text};
        border: 1px solid transparent; border-radius: 7px; padding: 6px 10px;
        font-size: 12px; }}
    QToolButton#CallControl:hover, QToolButton#CallControl:checked {{ background: {t.hover}; }}
    QToolButton#CallControl:focus {{ border-color: {t.accent}; }}
    QToolButton#CallControl:disabled {{ color: {t.muted}; }}
    QToolButton#CallControl[danger='true'] {{ color: {"#B4232F" if white else "#FF8A92"}; }}
    QScrollArea#AgentStream, QWidget#AgentStreamContent,
    QFrame#AgentMessage {{ background: transparent; border: none; }}
    QFrame#AgentTool {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 7px; }}
    QPushButton#AgentDisclosure {{ background: transparent; border: none;
        color: {t.muted}; text-align: left; padding: 0; font-size: 12px; }}
    QPushButton#AgentDisclosure:hover {{ color: {t.text}; }}
    QPushButton#AgentDisclosure:focus {{ border: 1px solid {t.accent}; border-radius: 6px; }}
    QPlainTextEdit#AgentCommandOutput {{ background: transparent; border: none;
        padding: 4px; font-size: 12px; }}
    QToolTip {{ background: {t.surface}; color: {t.text}; border: 1px solid {t.border};
        padding: 6px; }}
    QListWidget#DotList {{ border: none; border-radius: 12px;
        background: {t.surface}; padding: 5px; }}
    QListWidget#DotList::item {{ padding: 8px 10px; border: none; border-radius: 6px; }}
    QListWidget#DotList::item:selected {{ background: {t.accent_bg}; color: {t.accent_text}; }}
    """
