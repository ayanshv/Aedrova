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
        def request(self, path, body=None, **kwargs):
            if path == "/api/buds/connectors":
                return {
                    "providers": [
                        dict(
                            id=key,
                            name=name,
                            group=group,
                            description=description,
                            resource_hint=hint,
                            available=True,
                        )
                        for key, name, group, description, hint in [
                            (
                                "github",
                                "GitHub",
                                "Code & delivery",
                                "Repository context",
                                "owner/repository",
                            ),
                            ("figma", "Figma", "Design & knowledge", "Design context", "file key"),
                            ("notion", "Notion", "Design & knowledge", "Shared notes", "page UUID"),
                        ]
                    ]
                }
            if path == "/api/buds/connections":
                rows[0]["connections"] = [
                    dict(
                        id="grant-1",
                        provider=body["provider"],
                        resource=body["resource"],
                        status="Connected",
                        version="grant-1",
                    )
                ]
                rows[0]["status"] = "Connected"
                return {"connected": True}
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
    monkeypatch.setattr("aedrova.desktop.bud_connectors.client", lambda service: API())
    from aedrova.desktop.bud_connectors import ConnectorsDialog

    monkeypatch.setattr(
        ConnectorsDialog,
        "run",
        lambda self, operation, completed, **kwargs: completed(operation(service)),
    )
    monkeypatch.setattr(
        DotDialog, "run", lambda self, operation, completed, **kwargs: completed(operation(service))
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
    assert "connector card" in dialog.status.text()
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
    assert "Each account authorizes its own access" in dialog.recommendations.text()
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
        "product": ("Notion — coming next", "PostHog"),
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


def test_connector_step_is_inline_gallery_and_draft_connects_without_extra_window(editor, qtbot):
    from PySide6.QtWidgets import QFrame

    dialog, rows, saved, window = editor
    dialog.show_step(4)
    gallery = dialog.embedded_connectors
    assert not gallery.isWindow()
    assert gallery.parentWidget() is dialog.pages.widget(4)
    assert not dialog.provider.isVisible() and not dialog.resource.isVisible()
    assert not dialog.recommendations.isVisible()
    assert gallery.filter.currentData() == "builder"
    assert len(gallery.findChildren(QFrame, "ConnectorCard")) == 1
    qtbot.wait(40)
    assert gallery.columns == 3
    assert gallery.gallery.horizontalScrollBar().maximum() == 0
    gallery.open_provider(gallery.providers[0])
    gallery.resource.setText("team/project")
    gallery.credential.setText("private-fixture-token")
    gallery.connect_tool()
    assert len(saved) == 1
    assert rows[0]["connections"][0]["resource"] == "team/project"
    assert gallery.credential.text() == ""
    assert dialog.pages.currentIndex() == 4
    dialog.next.click()
    assert dialog.pages.currentIndex() == 5
    dialog.back.click()
    assert gallery.bud.currentData() == rows[0]["id"]
    gallery.credential.setText("never-retain-this")
    dialog.reject()
    assert gallery.credential.text() == ""


def test_new_bud_clears_previous_connector_target(editor):
    dialog, rows, saved, _ = editor
    dialog.resource.setText("team/project")
    dialog.save_dot()
    gallery = dialog.embedded_connectors
    assert gallery.bud.currentData() == rows[0]["id"]
    dialog.new_dot()
    dialog.show_step(4)
    assert gallery.bud.currentData() is None
    assert gallery.row().get("connections") == []


def test_connector_saves_changed_profile_before_authorizing_current_version(editor):
    dialog, rows, saved, _ = editor
    dialog.resource.setText("team/project")
    dialog.save_dot()
    dialog.name.setText("Renamed Bud")
    dialog.show_step(4)
    gallery = dialog.embedded_connectors
    gallery.open_provider(gallery.providers[0])
    gallery.resource.setText("team/project")
    gallery.credential.setText("private-fixture-token")
    gallery.connect_tool()
    assert len(saved) == 2
    assert rows[0]["name"] == "Renamed Bud"
    assert rows[0]["status"] == "Connected"
    assert not dialog.has_changes()
    dialog.next.click()
    assert dialog.pages.currentIndex() == 5


def test_pending_inline_connection_prevents_changing_bud_or_advancing(editor):
    dialog, _, _, _ = editor
    dialog.show_step(4)
    gallery = dialog.embedded_connectors
    gallery.pending = True
    gallery.update_controls()
    assert not dialog.back.isEnabled()
    assert not dialog.next.isEnabled()
    assert not dialog.new.isEnabled()
    assert not dialog.list.isEnabled()
    gallery.pending = False
    gallery.update_controls()
    assert dialog.back.isEnabled() and dialog.next.isEnabled()


def test_inline_oauth_saves_draft_opens_same_service_and_updates_real_connection(
    editor, monkeypatch
):
    dialog, rows, saved, window = editor
    dialog.show_step(4)
    gallery = dialog.embedded_connectors
    provider = {
        **gallery.providers[0],
        "oauth_available": True,
        "oauth_supported": True,
        "permissions": "Read-only repository",
    }
    gallery.open_provider(provider)
    gallery.resource.setText("team/project")
    origin, state = "http://127.0.0.1:8090", "a" * 43
    monkeypatch.setattr("aedrova.desktop.bud_connectors.connector_origin", lambda: origin)
    opened = []
    monkeypatch.setattr(
        "aedrova.desktop.bud_connectors.QDesktopServices.openUrl",
        lambda url: opened.append(url.toString()) or True,
    )
    original = __import__("aedrova.desktop.bud_connectors", fromlist=["client"]).client
    calls = []

    class API:
        def request(self, path, body=None, **kwargs):
            calls.append((path, body))
            if path == "/api/buds/oauth/start":
                return {"url": origin + "/buds/authorize/" + state, "state": state}
            if path.startswith("/api/buds/oauth/status?"):
                rows[0]["status"] = "Connected"
                rows[0]["connections"] = [
                    dict(id="grant", provider="github", resource="team/project", status="Connected")
                ]
                return {"status": "connected", "connection": "grant"}
            return original(None).request(path, body, **kwargs)

    monkeypatch.setattr("aedrova.desktop.bud_connectors.client", lambda _: API())
    gallery.connect_oauth()
    assert len(saved) == 1 and opened == [origin + "/buds/authorize/" + state]
    assert gallery.oauth_timer.isActive() and gallery.oauth_state == state
    assert "credential" not in calls[0][1] and calls[0][1]["dot"] == rows[0]["id"]
    gallery.poll_oauth()
    assert not gallery.oauth_timer.isActive() and not gallery.oauth_state
    assert dialog.current()["status"] == "Connected"
    assert window.composer.dots[0]["status"] == "Connected"
    dialog.next.click()
    assert dialog.pages.currentIndex() == 5


def test_oauth_rejects_external_redirect_and_stops_polling_when_closed(editor, monkeypatch):
    dialog, _, _, _ = editor
    dialog.resource.setText("team/project")
    dialog.save_dot()
    gallery = dialog.embedded_connectors
    gallery.open_provider(
        {
            **gallery.providers[0],
            "oauth_available": True,
            "oauth_supported": True,
            "permissions": "Read-only repository",
        }
    )
    gallery.resource.setText("team/project")
    monkeypatch.setattr(
        "aedrova.desktop.bud_connectors.connector_origin", lambda: "http://127.0.0.1:8090"
    )

    class API:
        def request(self, *_args, **_kwargs):
            return {"url": "https://evil.test/authorize", "state": "a" * 43}

    monkeypatch.setattr("aedrova.desktop.bud_connectors.client", lambda _: API())
    gallery.connect_oauth()
    assert "invalid authorization link" in gallery.status.text()
    assert not gallery.oauth_state
    gallery.oauth_state = "a" * 43
    gallery.oauth_timer.start()
    dialog.reject()
    assert not gallery.oauth_timer.isActive() and not gallery.oauth_state


def test_look_selection_sets_specialty_and_recommendations(editor):
    dialog, _, _, _ = editor
    for tile, specialty in dialog.appearance_buttons:
        tile.click()
        assert dialog.appearance.currentData() == specialty
        assert dialog.job_role.currentData() == specialty
        assert dialog.recommendations.text().startswith(specialty.title() + " tools")
    assert not any("Match" in tile.text() for tile, _ in dialog.appearance_buttons)


def test_required_bud_setup_cannot_be_accepted_without_verified_connection(editor):
    dialog, rows, saved, window = editor
    dialog.required = True
    dialog.accept()
    assert dialog.isVisible()
    assert "connect one tool" in dialog.status.text()
    assert not rows


def test_required_setup_finishes_only_after_verified_tool_and_final_stage(editor):
    dialog, rows, _, _ = editor
    dialog.required = True
    dialog.show_step(4)
    gallery = dialog.embedded_connectors
    gallery.open_provider(gallery.providers[0])
    gallery.resource.setText("team/project")
    gallery.credential.setText("private-fixture-token")
    gallery.connect_tool()
    assert rows[0]["status"] == "Connected"
    dialog.accept()
    assert dialog.isVisible()  # A connected grant cannot skip the final handoff.
    dialog.next.click()
    assert dialog.pages.currentIndex() == 5
    for status in ("Needs authorization", "Disconnected", "Permission issue", "Error"):
        dialog.current()["status"] = status
        dialog.accept()
        assert dialog.isVisible()
    dialog.current()["status"] = "Connected"
    dialog.name.setText("Changed after authorization")
    dialog.accept()
    assert dialog.isVisible()  # Old grants cannot authorize changed Bud settings.
    dialog.name.setText(rows[0]["name"])
    dialog.accept()
    assert not dialog.isVisible()
    assert dialog.result() == dialog.DialogCode.Accepted
