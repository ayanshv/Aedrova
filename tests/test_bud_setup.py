"""Bud drafts work before OAuth; connection and authorization remain real gates."""

from copy import deepcopy

import pytest
from PySide6.QtCore import Qt
from test_connected import setup

from aedrova.desktop.dots import DotDialog


@pytest.fixture
def editor(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    rows, saved = [], []
    providers = [
        dict(
            id="github",
            name="GitHub",
            available=False,
            configurable=True,
            permissions="Read-only repository",
        )
    ]

    class API:
        def request(self, path):
            return (
                {"providers": providers}
                if path.endswith("providers")
                else {"items": deepcopy(rows)}
            )

    def save(parameters):
        saved.append(parameters)
        item = dict(
            id="bud-1",
            workspace_id="w",
            version=parameters["p_version"] + 1,
            status="Needs authorization",
            last_sync=0,
            tools={"changes": "Recent commits"},
            permissions="Read-only repository",
        )
        item.update(
            {
                key: parameters["p_" + key]
                for key in [
                    "name",
                    "provider",
                    "resource",
                    "shape",
                    "color",
                    "role",
                    "instructions",
                    "appearance",
                ]
            }
        )
        rows[:] = [item]
        return item

    service.save_bud = save
    monkeypatch.setattr("aedrova.desktop.dots.client", lambda service: API())
    monkeypatch.setattr(
        DotDialog, "run", lambda self, operation, completed: completed(operation(service))
    )
    dialog = DotDialog(window)
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog, rows, saved, window


def test_six_stages_save_without_oauth_and_never_fake_ready(editor, qtbot):
    dialog, rows, saved, window = editor
    assert dialog.pages.currentIndex() == 0
    dialog.next.click()
    assert dialog.pages.currentIndex() == 1
    dialog.name.setText("Orbit")
    dialog.role.setText("Engineering updates")
    dialog.instructions.setPlainText("Focus on open pull requests.")
    dialog.shape.setCurrentIndex(dialog.shape.findData("cloud"))
    dialog.color.addItem("Custom", "#334455")
    dialog.color.setCurrentIndex(dialog.color.findData("#334455"))
    for stage in [2, 3, 4]:
        dialog.next.click()
        assert dialog.pages.currentIndex() == stage
    dialog.resource.setText("team/project")
    assert dialog.save.isEnabled() and not dialog.connect.isEnabled()
    dialog.next.click()
    assert saved[0]["p_role"] == "Builder · Engineering updates"
    assert saved[0]["p_shape"] == "cloud"
    assert dialog.current()["id"] == "bud-1"
    assert dialog.pages.currentIndex() == 4
    dialog.next.click()
    assert len(saved) == 1
    assert "Connect its tool" in dialog.status.text()
    assert dialog.pages.currentIndex() == 4
    rows[0]["status"] = "Connected"
    dialog.refresh()
    dialog.show_step(4)
    dialog.next.click()
    assert dialog.pages.currentIndex() == 5
    dialog.next.click()
    assert window.composer.editor.toPlainText().endswith("@Orbit ")
    assert window.composer.mention_tokens["Orbit"] == "<@dot:bud-1|Orbit>"
    assert not dialog.isVisible()


def test_validation_and_member_cannot_save(editor):
    dialog, rows, saved, window = editor
    dialog.name.setText("Orbit")
    dialog.resource.setText("https://github.com/team/project")
    dialog.save_dot()
    assert not saved and "repository identifier" in dialog.status.text()
    dialog.resource.setText("team/project")
    window.account_dialog.snapshot["members"][0]["role"] = "member"
    dialog.save_dot()
    assert not saved and "owners or admins" in dialog.status.text()


def test_choices_preview_and_no_extra_top_level_widgets(editor, qtbot):
    dialog, _, _, _ = editor
    dialog.show_step(1)
    tile, shape = dialog.appearance_buttons[-2]
    tile.click()
    assert dialog.character.config["appearance"] == shape
    for control in [dialog.color, dialog.shape, dialog.character]:
        assert not control.isWindow()
    qtbot.keyClick(dialog.exit_button, Qt.Key.Key_Space)
    assert not dialog.isVisible()


@pytest.mark.parametrize("has_notes", [False, True])
def test_missing_bud_migration_preserves_notes_or_uses_safe_fallback(has_notes):
    from unittest.mock import Mock

    from aedrova.identity.service import IdentityService

    class MissingRPC(Exception):
        code = "PGRST202"

    service = IdentityService.__new__(IdentityService)
    service._authenticated = Mock()
    service.client = Mock()
    service.client.rpc.return_value.execute.side_effect = MissingRPC()
    service.save_dot = Mock(return_value={"id": "legacy"})
    params = {"p_name": "Orbit", "p_role": "Engineering" if has_notes else "", "p_instructions": ""}
    if has_notes:
        with pytest.raises(ValueError, match="202610070002_bud_profiles.sql"):
            service.save_bud(params)
        service.save_dot.assert_not_called()
    else:
        assert service.save_bud(params)["id"] == "legacy"
        service.save_dot.assert_called_once_with({"p_name": "Orbit"})


def test_back_navigation_preserves_configuration_and_reduced_motion(editor):
    dialog, _, _, window = editor
    window.reduced_motion = True
    dialog.show_step(2)
    dialog.name.setText("Scout")
    dialog.next.click()
    dialog.role.setText("Research")
    dialog.back.click()
    assert dialog.name.text() == "Scout"
    assert dialog.role.text() == "Research"
    assert dialog.opacity.opacity() == 1
    dialog.name.clear()
    dialog.next.click()
    assert dialog.pages.currentIndex() == 2
    assert "name" in dialog.status.text()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_color_controls_render_after_transition_and_change_preview(editor, qtbot, theme):
    from PySide6.QtGui import QColor

    dialog, _, _, window = editor
    window.set_theme(theme)
    dialog.show_step(1)
    dialog.show_step(2)
    qtbot.wait(220)
    assert dialog.pages.graphicsEffect() is None
    assert dialog.custom_color_button.isVisible()
    for tile, value in dialog.swatch_buttons:
        assert tile.isVisible() and tile.width() == 28
        # Render the real widget; an empty control fails even when its hit area exists.
        drawn = tile.grab().toImage()
        sample = drawn.pixelColor(drawn.width() // 2, drawn.height() // 2)
        expected = QColor(value)
        assert abs(sample.red() - expected.red()) < 15
        assert abs(sample.green() - expected.green()) < 15
        assert abs(sample.blue() - expected.blue()) < 15
    tile, value = dialog.swatch_buttons[-1]
    tile.click()
    assert dialog.color.currentData() == value
    assert dialog.character.config["color"] == value


def test_role_presets_persist_independently_of_appearance(editor):
    dialog, rows, saved, _ = editor
    dialog.appearance.setCurrentIndex(dialog.appearance.findData("marketing"))
    dialog.job_role.setCurrentIndex(dialog.job_role.findData("designer"))
    dialog.role.setText("Review our designs")
    dialog.resource.setText("team/project")
    assert "Figma — coming next" in dialog.recommendations.text()
    assert "Notion — coming next" in dialog.recommendations.text()
    assert "one external connection" in dialog.recommendations.text()
    dialog.save_dot()
    assert saved[-1]["p_role"] == "Designer · Review our designs"
    assert saved[-1]["p_appearance"] == "marketing"
    assert dialog.job_role.currentData() == "designer"
    assert dialog.role.text() == "Review our designs"
    assert not dialog.has_changes()


def test_every_specialty_has_curated_tools_without_fake_access(editor):
    dialog, _, _, _ = editor
    expected = {
        "builder": ("GitHub — owner setup required", "Supabase — coming next"),
        "designer": ("Figma — coming next", "Notion — coming next"),
        "marketing": ("Instagram — coming next", "TikTok — coming next"),
        "finance": ("Stripe — coming next", "QuickBooks"),
        "research": ("AI model — uses workspace AI access", "Web search — coming next"),
        "product": ("Notion — coming next", "Linear — coming next"),
    }
    for specialty, phrases in expected.items():
        dialog.job_role.setCurrentIndex(dialog.job_role.findData(specialty))
        for phrase in phrases:
            assert phrase in dialog.recommendations.text()
        assert not dialog.connect.isEnabled()
        dialog.role.setText("x" * 240)
        dialog.resource.setText("team/project")
        dialog.save_dot()
        assert "240 characters" in dialog.status.text()


def test_legacy_long_purpose_survives_role_picker(editor):
    dialog, rows, _, _ = editor
    dialog.resource.setText("team/project")
    dialog.save_dot()
    rows[0]["role"] = "x" * 240
    dialog.refresh()
    assert dialog.role.text() == rows[0]["role"]
    assert dialog.configured_role() == rows[0]["role"]
    assert not dialog.has_changes()
