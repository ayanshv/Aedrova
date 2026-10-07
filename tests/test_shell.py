"""User journeys through the local preview; no service accounts or network access."""

from time import perf_counter

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAccessible, QKeySequence
from PySide6.QtTest import QAbstractItemModelTester, QTest
from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QStyleOptionViewItem

from aedrova.desktop.conversation import ConversationModel, MessageView
from aedrova.desktop.state import DemoStore, Message
from aedrova.desktop.theme import DARK, LIGHT
from aedrova.desktop.window import AedrovaWindow


@pytest.fixture
def window(qtbot, tmp_path):
    QApplication.instance().setStyle("Fusion")
    settings = QSettings(str(tmp_path / "appearance.ini"), QSettings.Format.IniFormat)
    widget = AedrovaWindow(settings=settings)
    widget.set_theme("light", persist=False)
    qtbot.addWidget(widget)
    widget.show()
    widget.activateWindow()
    qtbot.waitExposed(widget)
    return widget


def click_item(qtbot, listing, row):
    item = listing.item(row)
    listing.scrollToItem(item)
    qtbot.mouseClick(
        listing.viewport(), Qt.MouseButton.LeftButton, pos=listing.visualItemRect(item).center()
    )


def test_channel_and_workspace_navigation_keeps_separate_drafts(window, qtbot):
    window.composer.editor.setPlainText("Product draft")
    click_item(qtbot, window.channel_list, 2)
    assert window.channel_id == "design"
    assert window.composer.editor.toPlainText() == ""
    window.composer.editor.setPlainText("Design draft")
    qtbot.mouseClick(window.workspace_buttons["orbit"], Qt.MouseButton.LeftButton)
    assert window.workspace_id == "orbit"
    assert window.composer.editor.toPlainText() == ""
    assert "Orbit" in window.windowTitle()
    qtbot.mouseClick(window.workspace_buttons["northstar"], Qt.MouseButton.LeftButton)
    assert window.channel_id == "design"
    assert window.composer.editor.toPlainText() == "Design draft"
    click_item(qtbot, window.channel_list, 1)
    assert window.composer.editor.toPlainText() == "Product draft"


def test_direct_message_navigation(window, qtbot):
    click_item(qtbot, window.dm_list, 0)
    assert window.channel.direct
    assert window.channel.name == "Maya Chen"
    assert window.messages.model().rowCount() == 1
    assert not window.pinned.isVisible()
    assert not window.channel_list.selectedItems()


def test_enter_sends_shift_enter_newline_and_blank_is_ignored(window, qtbot):
    editor = window.composer.editor
    count = len(window.channel.messages)
    editor.setFocus()
    qtbot.keyClicks(editor, "First line")
    qtbot.keyClick(editor, Qt.Key.Key_Return, modifier=Qt.KeyboardModifier.ShiftModifier)
    qtbot.keyClicks(editor, "Second line")
    assert len(window.channel.messages) == count
    qtbot.keyClick(editor, Qt.Key.Key_Return)
    assert len(window.channel.messages) == count + 1
    assert window.channel.messages[-1].body == "First line\nSecond line"
    assert editor.toPlainText() == ""
    assert not window.composer.send.isEnabled()
    editor.setPlainText("   \n ")
    qtbot.keyClick(editor, Qt.Key.Key_Return)
    assert len(window.channel.messages) == count + 1


def test_mention_does_not_fake_agent_execution(window, qtbot):
    count = len(window.channel.messages)
    qtbot.mouseClick(window.composer.mention, Qt.MouseButton.LeftButton)
    qtbot.keyClicks(window.composer.editor, "build this")
    qtbot.mouseClick(window.composer.send, Qt.MouseButton.LeftButton)
    assert len(window.channel.messages) == count + 1
    assert window.channel.messages[-1].author == "You"
    assert "isn’t connected" in window.notice.text()


def test_pinned_thread_reply_and_draft_are_scoped(window, qtbot):
    qtbot.mouseClick(window.pinned, Qt.MouseButton.LeftButton)
    assert window.thread_id == "p4"
    assert window.thread_panel.isVisible()
    parent = next(m for m in window.channel.messages if m.id == "p4")
    count = len(parent.replies)
    window.thread_composer.editor.setPlainText("Keep sign-in tests.")
    qtbot.keyClick(window.thread_composer.editor, Qt.Key.Key_Return)
    assert len(parent.replies) == count + 1
    assert parent.replies[-1].body == "Keep sign-in tests."
    assert window.thread_messages.model().rowCount() == count + 2
    window.thread_composer.editor.setPlainText("Unsent reply")
    qtbot.mouseClick(window.thread_close, Qt.MouseButton.LeftButton)
    assert not window.thread_panel.isVisible()
    window.open_thread("p1")
    assert window.thread_composer.editor.toPlainText() == ""
    window.open_thread("p4")
    assert window.thread_composer.editor.toPlainText() == "Unsent reply"
    window.switch_workspace("orbit")
    assert not window.thread_id
    assert not window.thread_panel.isVisible()


def test_message_keyboard_activation_and_copy(window, qtbot):
    view = window.messages
    view.setCurrentIndex(view.model().index(0))
    view.setFocus()
    qtbot.keyClick(view, Qt.Key.Key_Return)
    assert window.thread_id == "p1"
    window.close_thread()
    view.copy_current()
    assert QApplication.clipboard().text() == window.channel.messages[0].body


def test_search_dialog_filters_and_navigates_across_workspaces(window, qtbot):
    qtbot.mouseClick(window.search_button, Qt.MouseButton.LeftButton)
    dialog = window.dialog
    qtbot.keyClicks(dialog.search, "orbit")
    assert dialog.results.count() == 2
    qtbot.keyClick(dialog.search, Qt.Key.Key_Down)
    qtbot.keyClick(dialog.search, Qt.Key.Key_Return)
    assert window.workspace_id == "orbit"
    assert window.channel_id == "orbit-design"
    assert not dialog.isVisible()


def test_search_no_matches_and_escape(window, qtbot):
    window.open_switcher()
    dialog = window.dialog
    qtbot.keyClicks(dialog.search, "no-such-channel")
    assert dialog.results.count() == 0
    assert dialog.empty.isVisible()
    qtbot.keyClick(dialog.search, Qt.Key.Key_Return)
    assert dialog.isVisible()
    qtbot.keyClick(dialog.search, Qt.Key.Key_Escape)
    assert not dialog.isVisible()
    assert window.channel_id == "product"


def test_create_workspace_and_channel_with_validation(window, qtbot):
    window.create_local_workspace()
    dialog = window.dialog
    dialog.name.setText("Northstar Labs")
    qtbot.mouseClick(dialog.submit, Qt.MouseButton.LeftButton)
    assert dialog.error.isVisible()
    assert dialog.isVisible()
    dialog.name.setText("New Studio")
    qtbot.mouseClick(dialog.submit, Qt.MouseButton.LeftButton)
    assert window.workspace.name == "New Studio"
    assert window.channel.name == "general"
    assert window.messages.model().rowCount() == 0
    qtbot.mouseClick(window.create_channel_button, Qt.MouseButton.LeftButton)
    dialog = window.dialog
    dialog.name.setText("Launch Planning")
    dialog.topic.setText("Our next release")
    qtbot.mouseClick(dialog.submit, Qt.MouseButton.LeftButton)
    assert window.channel.name == "launch-planning"
    assert window.channel_topic.text() == "Our next release"
    window.composer.editor.setPlainText("Hello, team")
    qtbot.mouseClick(window.composer.send, Qt.MouseButton.LeftButton)
    assert window.message_stack.currentIndex() == 0
    assert window.messages.model().rowCount() == 1


def test_theme_changes_preserve_work_and_saved_preference(window, qtbot):
    window.composer.editor.setPlainText("Keep this draft")
    qtbot.mouseClick(window.theme_button, Qt.MouseButton.LeftButton)
    assert window.theme is DARK
    assert window.settings.value("appearance") == "dark"
    assert window.composer.editor.toPlainText() == "Keep this draft"
    second = AedrovaWindow(settings=window.settings)
    qtbot.addWidget(second)
    assert second.theme is DARK
    window.set_theme("system")
    assert window.settings.value("appearance") == "system"
    assert window.appearance_actions["system"].isChecked()


def test_tabs_open_real_pages_and_sample_documents(window, qtbot):
    for index in range(4):
        qtbot.mouseClick(window.tab_buttons[index], Qt.MouseButton.LeftButton)
        assert window.pages.currentIndex() == index
        assert sum(tab.isChecked() for tab in window.tab_buttons) == 1
    window.select_tab(3)
    window.show_document("Product brief.md")
    editor = window.dialog.findChild(QPlainTextEdit)
    assert editor.isReadOnly()
    assert "Acceptance criteria" in editor.toPlainText()
    window.dialog.accept()
    window.select_tab(2)
    assert any(
        "No builds have run" in child.text()
        for child in window.pages.currentWidget().findChildren(QLabel)
    )


def test_compact_thread_replaces_chat_without_losing_draft(window, qtbot):
    window.composer.editor.setPlainText("Main draft")
    window.resize(900, 680)
    qtbot.waitUntil(lambda: window.width() == 900)
    window.open_pinned()
    assert not window.chat_column.isVisible()
    assert window.thread_panel.isVisible()
    qtbot.waitUntil(lambda: window.thread_composer.width() >= 300)
    window.resize(1440, 940)
    qtbot.waitUntil(window.chat_column.isVisible)
    assert window.thread_panel.isVisible()
    window.close_thread()
    assert window.composer.editor.toPlainText() == "Main draft"


def test_accessible_names_and_model_text(window):
    for control in (
        window.search_button,
        window.composer.editor,
        window.composer.send,
        window.channel_list,
        window.messages,
        window.create_workspace_button,
    ):
        interface = QAccessible.queryAccessibleInterface(control)
        assert interface is not None
        assert interface.text(QAccessible.Text.Name)
    index = window.messages.model().index(0)
    accessible = index.data(Qt.ItemDataRole.AccessibleTextRole)
    assert "Alex Morgan" in accessible and "three steps" in accessible


def test_input_limit_and_plain_text_are_preserved(window, qtbot):
    window.composer.editor.setPlainText("x" * 10_001)
    assert not window.composer.send.isEnabled()
    count = len(window.channel.messages)
    qtbot.keyClick(window.composer.editor, Qt.Key.Key_Return)
    assert len(window.channel.messages) == count
    text = '<script>alert("hello")</script> & **literal text**'
    window.composer.editor.setPlainText(text)
    qtbot.mouseClick(window.composer.send, Qt.MouseButton.LeftButton)
    doc = window.messages.delegate.document(window.channel.messages[-1], 500)
    assert window.channel.messages[-1].body == text
    assert doc.toPlainText() == '<script>alert("hello")</script> & literal text'


def test_variable_height_history_model_and_rendering(qtbot):
    view = MessageView()
    qtbot.addWidget(view)
    view.resize(700, 650)
    messages = [
        Message(
            str(i),
            "Teammate",
            "TM",
            "10:00",
            ("A line that needs wrapping. " * (1 + i % 8)),
            attachment="reference.md" if i % 10 == 0 else "",
        )
        for i in range(2_000)
    ]
    start = perf_counter()
    view.show_messages(messages)
    tester = QAbstractItemModelTester(
        view.model(),
        QAbstractItemModelTester.FailureReportingMode.Warning,
    )
    assert tester.model() is view.model()
    view.show()
    qtbot.waitExposed(view)
    view.scrollTo(view.model().index(1999))
    qtbot.waitUntil(
        lambda: view.viewport().rect().intersects(view.visualRect(view.model().index(1999))),
        timeout=5000,
    )
    option = QStyleOptionViewItem()
    tall = view.delegate.sizeHint(option, view.model().index(7)).height()
    short = view.delegate.sizeHint(option, view.model().index(1)).height()
    assert tall > short
    assert len(view.delegate.documents) <= 512
    assert not view.grab().isNull()
    assert perf_counter() - start < 8


def test_model_insert_and_accessibility_roles(qtbot):
    model = ConversationModel()
    tester = QAbstractItemModelTester(model, QAbstractItemModelTester.FailureReportingMode.Warning)
    model.append(Message("x", "You", "AV", "12:00", "A real local message"))
    assert tester.model().rowCount() == 1
    assert model.index(0).data(Qt.ItemDataRole.AccessibleTextRole).startswith("You")


@pytest.mark.parametrize("theme", [LIGHT, DARK])
def test_text_contrast_in_both_appearances(theme):
    def luminance(color):
        values = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        values = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(values, (0.2126, 0.7152, 0.0722), strict=True))

    for foreground, background in (
        (theme.text, theme.bg),
        (theme.secondary, theme.bg),
        (theme.muted, theme.sidebar),
        (theme.accent_text, theme.accent_bg),
    ):
        light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
        assert (light + 0.05) / (dark + 0.05) >= 4.5


def test_local_state_is_not_shared_between_app_instances():
    first, second = DemoStore(), DemoStore()
    first.send("northstar", "product", "Only in the first instance")
    assert len(first.channel("northstar", "product").messages) == 6
    assert len(second.channel("northstar", "product").messages) == 5


def test_keyboard_shortcuts_and_focus(window, qtbot):
    # Activate Qt's test window without stealing focus from the user's foreground app.
    with pytest.warns(DeprecationWarning, match="setActiveWindow"):
        QApplication.setActiveWindow(window)
    qtbot.waitUntil(window.isActiveWindow)
    QTest.keySequence(window, QKeySequence("Ctrl+K"))
    qtbot.waitUntil(lambda: window.dialog is not None and window.dialog.isVisible())
    qtbot.keyClicks(window.dialog.search, "engineering")
    qtbot.keyClick(window.dialog.search, Qt.Key.Key_Return)
    assert window.channel_id == "engineering"
    # Activate Qt's test window without stealing focus from the user's foreground app.
    with pytest.warns(DeprecationWarning, match="setActiveWindow"):
        QApplication.setActiveWindow(window)
    qtbot.waitUntil(window.isActiveWindow)
    QTest.keySequence(window, QKeySequence("Ctrl+3"))
    assert window.pages.currentIndex() == 2
    QTest.keySequence(window, QKeySequence("Ctrl+1"))
    assert window.pages.currentIndex() == 0
    QTest.keySequence(window, QKeySequence("Ctrl+Shift+L"))
    assert window.theme is DARK
    window.composer.editor.setFocus()
    qtbot.keyClick(window.composer.editor, Qt.Key.Key_Tab)
    assert not window.composer.editor.hasFocus()
    window.switch_channel("product")
    window.open_pinned()
    qtbot.keyClick(window.thread_composer.editor, Qt.Key.Key_Escape)
    assert not window.thread_panel.isVisible()


def test_many_workspaces_keep_window_usable(window, qtbot):
    for i in range(20):
        workspace = window.store.add_workspace(f"Workspace {i}")
    window.switch_workspace(workspace.id)
    window.resize(900, 680)
    qtbot.waitUntil(lambda: window.width() == 900)
    assert window.height() <= 680
    assert window.create_workspace_button.isVisible()
    assert window.create_workspace_button.geometry().bottom() <= window.height()


def test_selected_workspace_keeps_visible_background_after_theme_changes(window, qtbot):
    for theme in ("dark", "light"):
        window.set_theme(theme)
        control = window.workspace_buttons[window.workspace_id]
        image = control.grab().toImage()
        scale = image.devicePixelRatio()
        assert image.pixelColor(int(5 * scale), int(22 * scale)).name() == window.theme.text.lower()


def test_spring_motion_reacts_without_moving_layout(window, qtbot):
    from PySide6.QtCore import QEvent

    control = window.search_button
    original = control.geometry()
    QApplication.sendEvent(control, QEvent(QEvent.Type.Enter))
    qtbot.waitUntil(lambda: control.motion.effect.get_scale() > 1.01)
    assert control.geometry() == original
    qtbot.mousePress(control, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: control.motion.effect.get_scale() < 0.99)
    # Release outside the control: test the physical spring without opening a dialog.
    from PySide6.QtCore import QPoint

    qtbot.mouseRelease(control, Qt.MouseButton.LeftButton, pos=QPoint(-10, -10))
    QApplication.sendEvent(control, QEvent(QEvent.Type.Leave))
    qtbot.waitUntil(lambda: abs(control.motion.effect.get_scale() - 1.0) < 0.001)
    assert control.geometry() == original


def test_reduce_motion_and_transparency_are_functional_and_saved(window, qtbot):
    from PySide6.QtCore import QEvent

    from aedrova.desktop.materials import GlassFrame

    window.reduce_motion_action.trigger()
    window.reduce_transparency_action.trigger()
    QApplication.sendEvent(window.search_button, QEvent(QEvent.Type.Enter))
    assert window.search_button.motion.effect.get_scale() == 1.0
    assert not window.search_button.motion.enabled
    assert all(panel.reduced_transparency for panel in window.findChildren(GlassFrame))
    image = window.backdrop.texture()
    assert image.pixelColor(3, image.height() - 4).name() == window.theme.canvas.lower()
    assert window.settings.value("reduceMotion", type=bool)
    assert window.settings.value("reduceTransparency", type=bool)
    second = AedrovaWindow(settings=window.settings)
    qtbot.addWidget(second)
    assert second.reduced_motion and second.reduced_transparency


def test_bento_reflows_and_document_tile_opens(window, qtbot):
    from aedrova.desktop.materials import AdaptiveBento, DocumentTile

    window.select_tab(1)
    grid = window.pages.currentWidget().findChild(AdaptiveBento)
    qtbot.waitUntil(lambda: grid.columns == 2)
    window.resize(900, 680)
    qtbot.waitUntil(lambda: grid.columns == 1)
    scroll = window.pages.currentWidget()
    assert scroll.horizontalScrollBar().maximum() == 0
    window.resize(1440, 940)
    qtbot.waitUntil(lambda: grid.columns == 2)
    tile = grid.findChild(DocumentTile)
    qtbot.mouseClick(tile, Qt.MouseButton.LeftButton)
    assert window.dialog.isVisible()
    assert window.dialog.windowTitle() == "Design principles.md"


@pytest.mark.parametrize("theme_name", ["light", "dark"])
def test_accent_is_a_small_fraction_of_the_rendered_workspace(window, qtbot, theme_name):
    window.set_theme(theme_name)
    image = window.grab().toImage()
    accented = total = 0
    # Coarse screenshot sampling: strongly chromatic blue, not antialiased neutral text.
    for y in range(0, image.height(), 12):
        for x in range(0, image.width(), 12):
            color = image.pixelColor(x, y)
            total += 1
            accented += color.blue() - color.red() > 45 and color.blue() - color.green() > 15
    assert accented / total < 0.10


def test_brand_artwork_icon_and_reduced_motion(window, qtbot):
    from aedrova.desktop.brand import BrandMark, app_icon, brand_image

    artwork = brand_image()
    assert not artwork.isNull()
    assert artwork.hasAlphaChannel()
    assert artwork.width() < 450  # Transparent source margins do not shrink the mark.
    assert not app_icon().pixmap(128, 128).isNull()
    marks = window.findChildren(BrandMark)
    assert len(marks) == 2  # Header and chat; the old branding footer became the AI team shelf.
    mark = marks[0]
    mark.animate(1.0)
    qtbot.waitUntil(lambda: mark.get_lift() > 0.5)
    window.set_reduced_motion(True)
    assert mark.get_lift() == 0
    mark.animate(1.0)
    qtbot.wait(50)
    assert mark.get_lift() == 0
    window.show_about()
    assert window.dialog.findChild(BrandMark).reduced_motion
    window.dialog.accept()


def test_composer_grows_and_returns_to_compact_height(window, qtbot):
    composer = window.composer
    composer.editor.setPlainText("A thoughtful draft\n" * 12)
    qtbot.waitUntil(lambda: composer.editor.height() > 67)
    assert composer.editor.height() <= 134
    composer.clear()
    qtbot.waitUntil(lambda: composer.editor.height() == 67)


def test_mention_separates_from_previous_word_and_handles_emoji(window):
    from PySide6.QtGui import QTextCursor

    composer = window.composer
    composer.editor.setPlainText("Build this 🚀")
    composer.editor.moveCursor(QTextCursor.MoveOperation.End)
    composer.insert_mention()
    assert composer.editor.toPlainText() == "Build this 🚀 @Aedrova "


def test_desktop_workspace_actions_use_connected_account(window):
    intents = []
    window.show_account = lambda intent=None: intents.append(intent)
    window.create_workspace_button.click()
    window.invite_teammates_button.click()
    assert intents == ["create", "invite"]


def test_invitation_exit_opens_hidden_chat_dashboard(window, qtbot):
    window.hide()
    window.show_account()
    account = window.account_dialog
    account.pages.setCurrentIndex(2)
    account.onboarding_steps.setCurrentIndex(3)
    account.generated_code.setText("private-invite")
    account.invite_dashboard.click()
    assert window.isVisible()
    assert not account.isVisible()
    assert window.tab_buttons[0].isChecked()
    assert account.generated_code.text() == ""
    # Reopening account preserves the same session-owning dialog instance.
    window.show_account()
    assert window.account_dialog is account


def test_workspace_home_dashboard_action(window):
    window.hide()
    window.show_account()
    window.account_dialog.pages.setCurrentIndex(4)
    window.account_dialog.home_dashboard.click()
    assert window.isVisible()
    assert not window.account_dialog.isVisible()
