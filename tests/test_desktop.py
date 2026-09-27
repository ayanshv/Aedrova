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
