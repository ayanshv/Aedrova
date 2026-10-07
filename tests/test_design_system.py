"""Responsive action and evidence navigation checks for the Workroom redesign."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QVBoxLayout, QWidget

from aedrova.desktop.design_system import FlowActions, MasterDetail
from aedrova.desktop.dialogs import button


def test_actions_wrap_without_clipping_and_dynamic_insert_keeps_order(qtbot):
    panel = QWidget()
    qtbot.addWidget(panel)
    outer = QVBoxLayout(panel)
    actions = FlowActions()
    controls = [
        button(text) for text in ("Review current evidence", "Share exact evidence", "Done")
    ]
    for control in controls:
        actions.addWidget(control)
    start = button("Start build")
    actions.insertWidget(0, start)
    outer.addLayout(actions)
    panel.resize(320, 220)
    panel.show()
    qtbot.wait(30)
    assert actions.itemAt(0).widget() is start
    assert len({control.y() for control in [start, *controls]}) > 1
    for control in [start, *controls]:
        assert panel.rect().contains(control.geometry())
        assert control.width() >= control.minimumSizeHint().width()
    panel.resize(1000, 220)
    qtbot.wait(30)
    assert len({control.y() for control in [start, *controls]}) == 1


def test_master_detail_retains_selection_and_elides_long_titles_after_resize(qtbot):
    listing, editor = QListWidget(), QWidget()
    listing.addItems(["Long source title " * 20, "Second source"])
    listing.setCurrentRow(1)
    panel = MasterDetail(listing, editor)
    qtbot.addWidget(panel)
    panel.resize(1100, 650)
    panel.show()
    qtbot.wait(30)
    assert listing.geometry().right() < editor.geometry().left()
    panel.resize(640, 620)
    qtbot.wait(30)
    assert listing.geometry().bottom() < editor.geometry().top()
    assert listing.currentRow() == 1
    assert listing.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert panel.rect().contains(editor.geometry())


def test_action_labels_show_literal_ampersands_with_readable_accessibility(qtbot):
    control = button("Verify & connect")
    qtbot.addWidget(control)
    assert control.text() == "Verify && connect"
    assert control.accessibleName() == "Verify & connect"
    escaped = button("Review && deliver")
    qtbot.addWidget(escaped)
    assert escaped.text() == "Review && deliver"
    assert escaped.accessibleName() == "Review & deliver"
