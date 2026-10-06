"""Apple-inspired semantic palette: 60% base, 30% material, <=10% accent emphasis."""

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
    "#F5F5F7",
    "#FFFFFF",
    "#F5F5F7",
    "#F5F5F7",
    "#F5F5F7",
    "#EBEBEE",
    "#E8E8EB",
    "#1D1D1F",
    "#424247",
    "#68686E",
    "#0066CC",
    "#EAF2FF",
    "#0058B0",
    "#FFFFFF",
    ("#E8E8EB", "#EDEDEF", "#E4E4E7", "#E9E9EC"),
)
DARK = Theme(
    "dark",
    "#000000",
    "#1C1C1E",
    "#000000",
    "#1C1C1E",
    "#242426",
    "#303033",
    "#343437",
    "#F5F5F7",
    "#D0D0D5",
    "#A0A0A8",
    "#0A84FF",
    "#11273F",
    "#85BEFF",
    "#000000",
    ("#353537", "#303033", "#38383B", "#323235"),
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
    capsule = "rgba(255,255,255,185)" if white else "rgba(255,255,255,16)"
    if reduced_transparency:
        capsule = t.surface
    selected = "#FFFFFF" if white else "#444448"
    return f"""
    QWidget {{ color: {t.text}; font-size: 14px; }}
    QMainWindow, QDialog, QStackedWidget#AccountPages, QWidget#AccountPage {{ background: {t.bg}; }}
    QComboBox {{ background: {t.bg}; border: 1px solid transparent;
        border-radius: 12px; padding: 10px; min-width: 75px; }}
    QComboBox::drop-down {{ border: none; width: 30px; background: transparent; }}
    QComboBox:focus {{ border-color: {t.accent}; }}
    QComboBox::down-arrow {{ image: none; border: none; width: 0px; height: 0px; }}
    QComboBox QAbstractItemView {{ background: {t.bg}; color: {t.text};
        border: none; border-radius: 12px; padding: 6px;
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
    QTabWidget::pane {{ border: 1px solid {t.border}; border-radius: 14px; }}
    QTabBar::tab {{ background: {t.surface}; padding: 10px 18px; }}
    QTabBar::tab:selected {{ background: {t.accent_bg}; color: {t.accent_text}; }}
    QListWidget[accountList="true"] {{ background: {t.surface};
        border: 1px solid {t.border}; border-radius: 12px; padding: 6px; }}
    QListWidget[accountList="true"]::item {{ padding: 7px; border-radius: 6px; }}
    QListWidget[accountList="true"]::item:selected {{
        background: {t.accent_bg}; color: {t.accent_text}; }}
    QWidget#Chat, QWidget#Thread, QFrame#Rail, QFrame#Topbar,
    QFrame#ChannelHeader {{ background: transparent; border: none; }}
    QLabel {{ background: transparent; border: none; }}
    QLabel[role='muted'] {{ color: {t.muted}; font-size: 12px; }}
    QLabel[role='section'] {{ color: {t.muted}; font-size: 10px; font-weight: 500; }}
    QLabel[role='title'] {{ font-size: 20px; font-weight: 600; }}
    QLabel[role='display'] {{ font-size: 34px; font-weight: 600; }}
    QLabel[role='heading'] {{ font-size: 32px; font-weight: 600; }}
    QLabel[role='badge'] {{ color: {t.secondary}; background: {capsule};
        border-radius: 11px; padding: 5px 10px; font-size: 10px; font-weight: 500; }}
    QLabel[role='error'] {{ color: {"#B4232F" if white else "#FF8A92"}; font-size: 12px; }}
    QFrame#Composer {{ background: {capsule}; border: 1px solid {t.border}; border-radius: 22px; }}
    QFrame#Composer[focused='true'] {{ border: 1px solid {t.accent}; }}
    QFrame#Quiet {{ background: transparent; border-top: 1px solid {t.border}; }}
    QFrame#AudioCallStage {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 24px; }}
    QFrame#AudioParticipant {{ background: {t.bg}; border: 1px solid {t.border};
        border-radius: 20px; }}
    QFrame#AudioParticipant[speaking="true"] {{ border: 1px solid {t.accent}; }}
    QFrame#CallBar {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 18px; }}
    QWidget#Segments {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 17px; }}
    QPushButton {{ background: transparent; border: 1px solid transparent;
        border-radius: 12px; padding: 8px 12px; text-align: left; font-weight: 500; }}
    QPushButton:hover {{ background: {t.hover}; }}
    QPushButton:pressed {{ background: {t.border}; }}
    QPushButton:focus, QLineEdit:focus, QPlainTextEdit:focus, QListView:focus {{
        border: 1px solid {t.accent}; }}
    QPushButton:checked {{ background: {t.accent_bg}; color: {t.accent_text}; }}
    QPushButton:disabled {{ color: {t.muted}; }}
    QPushButton[role='primary'] {{ background: {t.accent}; color: {t.primary_text};
        padding: 9px 18px; border-radius: 16px; font-weight: 600; text-align: center; }}
    QPushButton[role='primary']:hover {{ background: {"#0058B0" if white else "#389CFF"}; }}
    QPushButton[role='primary']:pressed {{ background: {"#004C99" if white else "#0071E3"}; }}
    QPushButton[role='primary']:disabled {{ background: {t.hover}; color: {t.muted}; }}
    QPushButton[role='outline'] {{ border: 1px solid {t.border}; background: {capsule}; }}
    QPushButton[role='icon'] {{ padding: 0px; text-align: center; }}
    QPushButton[role='workspace'] {{ border-radius: 17px; font-size: 17px;
        font-weight: 600; text-align: center; padding: 0px; }}
    QPushButton[role='workspace']:checked {{ background: {t.text}; color: {t.bg}; }}
    QPushButton[role='tab'] {{ padding: 7px 15px; border-radius: 12px; font-size: 12px;
        color: {t.secondary}; }}
    QPushButton[role='tab']:checked {{ background: {selected}; color: {t.text};
        border: 1px solid {t.border}; font-weight: 600; }}
    QPushButton#Pinned {{ background: {capsule}; color: {t.secondary};
        border: 1px solid {t.border}; border-radius: 15px; padding: 12px 17px; font-size: 12px; }}
    QPushButton#Search {{ background: {capsule}; color: {t.muted}; border: 1px solid {t.border};
        border-radius: 17px; padding: 8px 16px; font-size: 12px; }}
    QListWidget#Navigation {{ border: none; background: transparent; outline: none; }}
    QListWidget#Navigation::item {{ height: 39px; border-radius: 12px; padding-left: 13px; }}
    QListWidget#Navigation::item:selected {{ background: {selected}; color: {t.text}; }}
    QListWidget#Navigation::item:hover {{ background: {t.hover}; }}
    QListView#Messages {{ border: 1px solid transparent; background: transparent; outline: none; }}
    QListWidget#Switcher {{ background: transparent; border: none; }}
    QListWidget#Switcher::item {{ padding: 14px; border-radius: 12px; }}
    QListWidget#Switcher::item:selected {{ background: {t.accent_bg}; color: {t.accent_text}; }}
    QPlainTextEdit {{ background: transparent; border: 1px solid transparent;
        padding: 8px; selection-background-color: {t.accent_bg}; }}
    QPlainTextEdit#ComposerEditor:focus {{ border: 1px solid transparent; }}
    QPlainTextEdit#BuildRequest {{ border: 1px solid {t.border};
        background: {t.surface}; border-radius: 14px; padding: 12px; }}
    QPlainTextEdit#BuildRequest:focus {{ border-color: {t.accent}; }}
    QPlainTextEdit#ProfileBio {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 14px; padding: 12px; color: {t.text}; }}
    QPlainTextEdit#ProfileBio:focus {{ border-color: {t.accent}; }}
    QLineEdit {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: 14px;
        padding: 12px; selection-background-color: {t.accent_bg}; }}
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
        border-radius: 18px; padding: 10px; outline: none; }}
    QListWidget#ChatResults::item {{ padding: 14px 12px; border: none;
        border-radius: 12px; color: {t.text}; }}
    QListWidget#ChatResults::item:hover {{ background: {t.hover}; }}
    QListWidget#ChatResults::item:selected {{ background: {t.accent_bg}; color: {t.text}; }}
    QListWidget#EmojiGrid {{ background: {t.bg}; border: none; border-radius: 14px;
        outline: none; font-size: 20px; }}
    QListWidget#EmojiGrid::item {{ padding: 0; margin: 2px; border-radius: 8px; }}
    QListWidget#EmojiGrid::item:hover {{ background: {t.hover}; }}
    QListWidget#EmojiGrid::item:selected {{ background: {t.accent_bg}; }}
    QFrame#ReactionBar {{ background: {t.bg}; border: 1px solid {t.border};
        border-radius: 14px; }}
    QFrame#ReactionBar QPushButton {{ border: none; border-radius: 9px;
        background: transparent; padding: 0; }}
    QFrame#ReactionBar QPushButton:hover {{ background: {t.hover}; }}
    QMenu {{ background: {t.bg}; border: none; padding: 8px; border-radius: 16px; }}
    QMenu::item {{ padding: 10px 24px 10px 12px; border-radius: 8px; }}
    QMenu::separator {{ height: 1px; background: {t.border}; margin: 6px 8px; }}
    QMenu::item:disabled {{ color: {t.muted}; }}
    QMenu::item:selected {{ background: {t.accent_bg}; }}
    QMenu::item:selected:enabled {{ color: {t.accent_text}; }}
    QToolButton:focus {{ border: 1px solid {t.accent}; border-radius: 12px; }}
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
        border-radius: 20px; }}
    QToolButton#CallControl {{ background: transparent; color: {t.text};
        border: 1px solid transparent; border-radius: 12px; padding: 6px 10px;
        font-size: 12px; }}
    QToolButton#CallControl:hover, QToolButton#CallControl:checked {{ background: {t.hover}; }}
    QToolButton#CallControl:focus {{ border-color: {t.accent}; }}
    QToolButton#CallControl:disabled {{ color: {t.muted}; }}
    QToolButton#CallControl[danger='true'] {{ color: {"#B4232F" if white else "#FF8A92"}; }}
    QScrollArea#AgentStream, QWidget#AgentStreamContent,
    QFrame#AgentMessage {{ background: transparent; border: none; }}
    QFrame#AgentTool {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 12px; }}
    QPushButton#AgentDisclosure {{ background: transparent; border: none;
        color: {t.muted}; text-align: left; padding: 0; font-size: 12px; }}
    QPushButton#AgentDisclosure:hover {{ color: {t.text}; }}
    QPushButton#AgentDisclosure:focus {{ border: 1px solid {t.accent}; border-radius: 6px; }}
    QPlainTextEdit#AgentCommandOutput {{ background: transparent; border: none;
        padding: 4px; font-size: 12px; }}
    QToolTip {{ background: {t.surface}; color: {t.text}; border: 1px solid {t.border};
        padding: 6px; }}
    """
