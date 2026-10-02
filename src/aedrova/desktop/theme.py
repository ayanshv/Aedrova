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
    QComboBox {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 12px; padding: 10px; min-width: 75px; }}
    QComboBox::drop-down {{ border: none; width: 30px; background: transparent; }}
    QComboBox:focus {{ border-color: {t.accent}; }}
    QComboBox::down-arrow {{ image: none; border: none; width: 0px; height: 0px; }}
    QComboBox QAbstractItemView {{ background: {t.surface}; color: {t.text};
        border: 1px solid {t.border}; border-radius: 12px; padding: 6px;
        selection-background-color: {t.accent_bg}; selection-color: {t.accent_text};
        outline: none; }}
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
    QLabel[role='error'] {{ color: {t.accent_text}; font-size: 12px; }}
    QFrame#Composer {{ background: {capsule}; border: 1px solid {t.border}; border-radius: 22px; }}
    QFrame#Composer[focused='true'] {{ border: 1px solid {t.accent}; }}
    QFrame#Quiet {{ background: transparent; border-top: 1px solid {t.border}; }}
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
    QPushButton[role='primary']:hover {{ background: {t.accent}; }}
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
    QLineEdit {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: 14px;
        padding: 12px; selection-background-color: {t.accent_bg}; }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 7px; margin: 6px 1px; }}
    QScrollBar::handle:vertical {{ background: {t.border}; min-height: 32px; border-radius: 3px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    QMenu {{ background: {t.bg}; border: 1px solid {t.border}; padding: 7px; border-radius: 12px; }}
    QMenu::item {{ padding: 10px 24px 10px 12px; border-radius: 8px; }}
    QMenu::separator {{ height: 1px; background: {t.border}; margin: 6px 8px; }}
    QMenu::item:disabled {{ color: {t.muted}; }}
    QMenu::item:selected {{ background: {t.accent_bg}; }}
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
