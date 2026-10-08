from time import perf_counter

from PySide6.QtCore import QModelIndex
from PySide6.QtTest import QAbstractItemModelTester

from aedrova.desktop.probe import MessageModel, ProbeWindow


def test_message_model_contract(qtbot):
    model = MessageModel()
    tester = QAbstractItemModelTester(
        model,
        QAbstractItemModelTester.FailureReportingMode.Warning,
    )
    assert tester.model() is model
    assert model.rowCount() == 50_000
    assert model.rowCount(model.index(0)) == 0
    assert model.data(QModelIndex()) is None
    assert "50,000" in model.data(model.index(49_999))


def test_large_history_renders_and_scrolls(qtbot):
    start = perf_counter()
    window = ProbeWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    window.messages.scrollToBottom()
    qtbot.waitUntil(
        lambda: (
            window.messages.verticalScrollBar().value()
            == window.messages.verticalScrollBar().maximum()
        ),
    )
    assert not window.grab().isNull()
    assert perf_counter() - start < 5, "50k-row probe exceeded generous local smoke threshold"


def test_resizing_shell_never_spawns_participant_label_window(qtbot, tmp_path):
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from aedrova.desktop.window import AedrovaWindow

    window = AedrovaWindow(
        settings=QSettings(str(tmp_path / "launch.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(window)
    window.members_label.setText("Your team")
    for width in (1440, 960, 1200):
        window.resize(width, 800)
        window.show()
        QApplication.processEvents()
        assert window.members_label.parentWidget() is window.header
        assert not window.members_label.isWindow()
        assert not window.members_label.isVisible()
        assert window.members_label not in QApplication.topLevelWidgets()
    window.hide()
    window.show_account()
    qtbot.addWidget(window.account_dialog)
    QApplication.processEvents()
    assert not window.members_label.isVisible()
    assert window.members_label not in QApplication.topLevelWidgets()
