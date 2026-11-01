"""First-use orchestration, interruption, account changes and responsive UI."""

import copy
import json
from threading import Event
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSettings

from aedrova.desktop.projects import binding_key
from aedrova.desktop.window import AedrovaWindow


class Service:
    def __init__(self):
        self.user = SimpleNamespace(id="new-user")
        self.state = {}
        self.calls = []
        self.items = []

    def rpc(self, name, params):
        self.calls.append((name, params))
        if name == "get_first_use_progress":
            return copy.deepcopy(self.state)
        if name == "save_first_use_progress":
            assert params["p_revision"] == self.state.get("revision", 0)
            self.state.update(draft=params["p_draft"], stage=params["p_stage"])
        elif name == "create_first_use_space":
            assert params["p_allow_ai"]
            self.state.update(workspace_id="new-space", stage=2, ai_reviewed_at="reviewed")
        elif name == "activate_first_use_buds":
            for role in params["p_roles"]:
                self.state.setdefault("buds", {})[role] = "bud-" + role
                if not any(row["id"] == "bud-" + role for row in self.items):
                    self.items.append({"id": "bud-" + role})
        elif name == "invite_first_use_teammate":
            email = params["p_email"]
            self.state.setdefault("invitations", {})[email] = "invite"
            self.state["revision"] = self.state.get("revision", 0) + 1
            return {"progress": copy.deepcopy(self.state), "email": email, "code": "one-use"}
        elif name == "complete_first_use":
            self.state.update(completed_at="complete", first_message_id="message")
            self.state["draft"]["goal"] = params["p_goal"]
        else:
            raise AssertionError(name)
        self.state["revision"] = self.state.get("revision", 0) + 1
        return copy.deepcopy(self.state)

    def bud_capacity(self, workspace):
        return {"used": len(self.items), "limit": 1, "remaining": 1 - len(self.items)}

    def dots(self, workspace):
        return {"items": self.items}

    def snapshot(self):
        return {"workspaces": [{"id": "new-space", "name": "My team"}], "invitations": []}


def journey(qtbot, tmp_path):
    window = AedrovaWindow(
        settings=QSettings(str(tmp_path / "first.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(window)
    window.show_first_use()
    flow = window.first_use_journey
    service = Service()
    window.account_dialog.service = service
    window.account_dialog.snapshot = {"workspaces": []}
    flow.owner = service.user.id
    flow.sign_in.hide()
    flow.space_form.show()
    flow.show_stage(1, animated=False)
    return window, flow, service


def settled(qtbot, flow, stage):
    qtbot.waitUntil(lambda: not flow.pending and flow.stage == stage, timeout=5000)


def create(qtbot, flow):
    flow.space_name.setText("My team")
    flow.ai_consent.setChecked(True)
    flow.advance()
    settled(qtbot, flow, 2)


def test_new_user_saves_real_setup_and_enters_workspace_without_ai_run(
    qtbot, tmp_path, monkeypatch
):
    window, flow, service = journey(qtbot, tmp_path)
    flow.space_name.setText("My team")
    flow.advance()
    assert not service.calls and "Review" in flow.status.text()
    create(qtbot, flow)
    assert flow.state["workspace_id"] == "new-space"
    assert not flow.automatic.isEnabled()
    flow.skip_stage()
    settled(qtbot, flow, 3)
    flow.bud_choices["research"].setChecked(True)
    flow.advance()
    settled(qtbot, flow, 4)
    flow.team_email.setText("teammate@company.test")
    flow.invite_teammate()
    qtbot.waitUntil(lambda: not flow.pending)
    assert flow.local_codes == {"teammate@company.test": "one-use"}
    assert "one-use" not in window.settings.value(flow.local_key())
    flow.skip_stage()
    settled(qtbot, flow, 5)
    flow.goal.setPlainText("Build a shared research library")
    entered = []
    monkeypatch.setattr(flow.account, "loaded", lambda value: entered.append(value))
    monkeypatch.setattr(flow.account, "open_dashboard", lambda: entered.append("dashboard"))
    flow.advance()
    qtbot.waitUntil(lambda: flow.closed)
    assert entered[-1] == "dashboard" and not flow.isVisible()
    assert service.state["draft"]["goal"] == "Build a shared research library"
    config = json.loads(window.settings.value(binding_key("new-user", "new-space")))
    assert config["provider"] == "auto" and not config["background_build"]
    assert [n for n, _ in service.calls].count("create_first_use_space") == 1
    assert [n for n, _ in service.calls].count("complete_first_use") == 1
    assert window.settings.value(flow.local_key()) is None


def test_interrupted_progress_restores_local_folder_and_reviewed_authority(qtbot, tmp_path):
    window, flow, _ = journey(qtbot, tmp_path)
    create(qtbot, flow)
    project = tmp_path / "project"
    project.mkdir()
    flow.project_folder = str(project)
    flow.goal.setPlainText("The draft objective")
    flow.stage = 5
    flow.save_local()
    saved = copy.deepcopy(flow.state)
    flow.goal.clear()
    # Restore the saved file, as if the process had restarted without more edits.
    window.settings.setValue(
        flow.local_key(),
        json.dumps(
            {
                "revision": saved["revision"],
                "stage": 5,
                "draft": {**saved["draft"], "goal": "The draft objective"},
                "project_folder": str(project),
            }
        ),
    )
    flow.restore(saved)
    assert flow.stage == 5 and flow.goal.toPlainText() == "The draft objective"
    assert flow.project_folder == str(project)
    assert flow.ai_consent.isChecked() and not flow.automatic.isEnabled()


def test_malformed_local_stage_and_draft_do_not_break_recovery(qtbot, tmp_path):
    window, flow, _ = journey(qtbot, tmp_path)
    window.settings.setValue(
        flow.local_key(), json.dumps({"revision": 0, "stage": {}, "draft": []})
    )
    flow.restore({})
    assert flow.stage == 1 and flow.space_name.text() == ""


def test_existing_users_are_not_forced_through_first_use(qtbot, tmp_path):
    window, flow, _ = journey(qtbot, tmp_path)
    flow.account.snapshot = {"workspaces": [{"id": "existing", "name": "Existing"}]}
    flow.restore({})
    assert flow.closed and window.account_dialog.isVisible()
    assert flow.account.pages.currentIndex() == 4


def test_changed_account_cannot_receive_inflight_result(qtbot, tmp_path):
    _, flow, service = journey(qtbot, tmp_path)
    release = Event()
    started = Event()
    results = []

    def operation(_):
        started.set()
        release.wait(3)
        return {"private": "first account"}

    flow.run(operation, results.append)
    qtbot.waitUntil(started.is_set)
    service.user = SimpleNamespace(id="another-user")
    release.set()
    qtbot.waitUntil(lambda: not flow.pending)
    assert not results and "account changed" in flow.status.text()


def test_bud_allowance_excludes_deleted_and_limits_draft_selection(qtbot, tmp_path):
    _, flow, _ = journey(qtbot, tmp_path)
    flow.state = {"buds": {"research": "deleted"}}
    for choice in flow.bud_choices.values():
        choice.setChecked(True)
    flow.capacity_loaded({"capacity": {"used": 0, "limit": 1, "remaining": 1}, "items": []})
    assert sum(c.isChecked() for c in flow.bud_choices.values()) == 1
    assert not flow.bud_choices["research"].active


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_all_stages_fit_viewport_and_reduced_motion_stops_timers(qtbot, tmp_path, width, height):
    _, flow, _ = journey(qtbot, tmp_path)
    flow.reduced = True
    flow.owner = None
    flow.resize(width, height)
    flow.show()
    for stage in range(6):
        flow.show_stage(stage, animated=False)
        qtbot.wait(20)
        assert flow.stack.width() <= width
        assert flow.pages[stage].width() <= flow.stack.width()
        assert flow.primary.isVisible() and flow.primary.height() >= 44
        assert flow.stack.widget(stage).horizontalScrollBar().maximum() == 0
    assert not flow.opening_scene.timer.isActive()


def test_embedded_connector_creates_bud_only_after_explicit_connect(qtbot, tmp_path, monkeypatch):
    from aedrova.desktop import bud_connectors

    _, flow, service = journey(qtbot, tmp_path)
    flow.reduced = True
    flow.space_name.setText("My team")
    service.state = {"workspace_id": "new-space", "revision": 2, "draft": flow.draft(), "buds": {}}
    flow.state = copy.deepcopy(service.state)
    service.fork_for_context = lambda: service
    service.close_context = lambda: None
    calls = []
    provider = {
        "id": "github",
        "name": "GitHub",
        "group": "Code & delivery",
        "description": "Repository changes",
        "resource_hint": "owner/repository",
        "available": True,
        "oauth_available": True,
    }

    class API:
        def request(self, path, body=None):
            calls.append((path, body))
            if path == "/api/buds/connectors":
                return {
                    "providers": [provider, {**provider, "id": "figma", "oauth_available": False}]
                }
            if path.startswith("/api/dots?"):
                return {
                    "items": [
                        {
                            **row,
                            "workspace_id": "new-space",
                            "version": 1,
                            "status": "Needs authorization",
                            "last_sync": 0,
                            "name": "Builder",
                            "role": "Builder",
                            "provider": "github",
                            "resource": "selection/pending",
                            "connections": [],
                        }
                        for row in service.items
                    ]
                }
            if path == "/api/buds/oauth/start":
                return {
                    "state": "s" * 48,
                    "url": "https://staging.example/buds/authorize/" + "s" * 48,
                }
            raise AssertionError(path)

    monkeypatch.setattr(bud_connectors, "client", lambda _: API())
    monkeypatch.setattr(bud_connectors, "connector_origin", lambda: "https://staging.example")
    monkeypatch.setattr(bud_connectors.QDesktopServices, "openUrl", lambda _: True)
    flow.show_stage(2, animated=False)
    gallery = flow.connector_gallery
    qtbot.waitUntil(lambda: not gallery.pending and not gallery.job)
    assert [p["id"] for p in gallery.providers] == ["github"]
    assert not any(name == "activate_first_use_buds" for name, _ in service.calls)
    assert gallery.cards[0].isEnabled()
    gallery.open_provider(gallery.providers[0])
    assert gallery.oauth.isEnabled()
    gallery.oauth.click()
    qtbot.waitUntil(lambda: bool(gallery.oauth_state), timeout=5000)
    assert [name for name, _ in service.calls].count("activate_first_use_buds") == 1
    assert calls[-1][1]["dot"] == "bud-builder"
    assert flow.stage == 2
    flow.reject()
    assert not gallery.oauth_timer.isActive()


def test_ui_handoff_failure_keeps_completed_progress_retryable(qtbot, tmp_path, monkeypatch):
    _, flow, _ = journey(qtbot, tmp_path)
    monkeypatch.setattr(flow, "enter_space", lambda _: (_ for _ in ()).throw(OSError("disk")))
    flow.state = {"completed_at": "done", "workspace_id": "new-space"}
    flow.restore(flow.state)
    qtbot.waitUntil(lambda: not flow.pending)
    assert not flow.closed and not flow.retry.isHidden()
    assert "saved" in flow.status.text()
