"""Growing a window expands content without pulling related form controls apart."""

import pytest
from test_workspace_archive import account


@pytest.mark.parametrize("section", ["agent", "account"])
def test_short_forms_keep_related_actions_close_when_resized(qtbot, tmp_path, section):
    dialog, _ = account(qtbot, tmp_path)
    dialog.pages.setCurrentIndex(1)
    view = dialog.workspace_settings
    view.show_section(section)
    for height in (850, 1150):
        dialog.resize(900, height)
        qtbot.wait(30)
        if section == "agent":
            preceding, action = dialog.agent_provider, dialog.save_agent
        else:
            preceding = dialog.invite_code
            action = next(
                b
                for b in view.sections.currentWidget().findChildren(type(dialog.home_dashboard))
                if b.accessibleName() == "Back to workspace"
            )
        gap = action.geometry().top() - preceding.geometry().bottom()
        assert 0 < gap <= 48


def test_workspace_picker_stays_one_group_at_large_sizes(qtbot, tmp_path):
    dialog, _ = account(qtbot, tmp_path)
    dialog.archived_workspaces.addItem("Older workspace", "old")
    dialog.archived_section.show()
    for height in (780, 1150):
        dialog.resize(900, height)
        qtbot.wait(30)
        active_y = dialog.home_workspaces.mapTo(dialog, dialog.home_workspaces.rect().topLeft()).y()
        archive_y = dialog.archived_workspaces.mapTo(
            dialog, dialog.archived_workspaces.rect().topLeft()
        ).y()
        assert 100 <= archive_y - active_y <= 200
        assert dialog.home_workspaces.width() <= 720


@pytest.mark.parametrize(
    "section,attribute",
    [("channels", "channels"), ("people", "members"), ("invitations", "invitations")],
)
def test_settings_lists_use_extra_window_height(qtbot, tmp_path, section, attribute):
    dialog, _ = account(qtbot, tmp_path)
    dialog.pages.setCurrentIndex(1)
    dialog.workspace_settings.show_section(section)
    if section == "invitations":
        dialog.invitations.addItem("teammate@example.com · member")
        dialog.invitations.show()
    dialog.resize(900, 850)
    qtbot.wait(30)
    before = getattr(dialog, attribute).height()
    dialog.resize(900, 1150)
    qtbot.wait(30)
    assert getattr(dialog, attribute).height() >= before + 200
