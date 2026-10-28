"""Creation requires an explicit, scoped AI setup; recovery never duplicates a Space."""

import json

import pytest
from test_account import dialog, setup_service
from test_connected import setup
from test_dots import dot

from aedrova.desktop.projects import binding_key, save_binding


def review(widget, *, automatic=False):
    widget.begin_onboarding()
    widget.onboarding_workspace.setText("New team")
    widget.advance_onboarding()
    widget.provider_continue.click()
    widget.onboarding_workflow.setCurrentIndex(widget.onboarding_workflow.findData(automatic))
    widget.onboarding_ack.setChecked(True)


def test_creation_is_blocked_until_ai_review_and_changes_revoke_consent(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    calls = setup_service(widget)
    widget.onboarding_workspace.setText("New team")
    widget.complete_onboarding()
    assert not calls and widget.onboarding_steps.currentIndex() == widget.ai_review_step
    assert not widget.finish_onboarding.isEnabled()
    widget.onboarding_ack.setChecked(True)
    widget.onboarding_provider.setCurrentIndex(1)
    assert not widget.onboarding_ack.isChecked() and not widget.finish_onboarding.isEnabled()
    widget.onboarding_ack.setChecked(True)
    widget.onboarding_workflow.setCurrentIndex(1)
    assert not widget.onboarding_ack.isChecked()


def test_compact_review_scrolls_instead_of_compressing_controls(qtbot, tmp_path):
    from PySide6.QtWidgets import QScrollArea

    widget = dialog(qtbot, tmp_path)
    review(widget)
    widget.resize(600, 540)
    widget.show()
    qtbot.wait(50)
    scroll = widget.pages.currentWidget()
    assert isinstance(scroll, QScrollArea)
    scroll.ensureWidgetVisible(widget.finish_onboarding)
    assert scroll.verticalScrollBar().maximum() > 0
    assert widget.finish_onboarding.height() >= 48
    assert widget.onboarding_permission.height() >= widget.onboarding_permission.sizeHint().height()


@pytest.mark.parametrize("automatic", [True, False])
def test_creation_saves_real_execution_preferences_per_account_workspace(
    qtbot, tmp_path, automatic
):
    widget = dialog(qtbot, tmp_path)
    calls = setup_service(widget)
    review(widget, automatic=automatic)
    widget.finish_onboarding.click()
    qtbot.waitUntil(lambda: not widget.busy)
    data = json.loads(widget.settings.value(binding_key("user", "new")))
    assert data["background_build"] is data["auto_plan"] is automatic
    assert data["provider"] == "auto" and data["ai_setup_version"] == 1
    assert data["model_policy"] in {"managed", "provider_default"}
    assert not data["ai_setup_pending"] and "folder" not in data
    assert widget.settings.value(binding_key("another-user", "new")) is None
    assert len(calls) == 1


def test_subspace_gets_selected_identity_and_retries_setup_without_recreating(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    calls = setup_service(widget)
    original = widget.service.rpc
    failed = []

    def rpc(name, params):
        if name == "set_agent_preferences" and not failed:
            failed.append(True)
            raise RuntimeError("private diagnostic")
        return original(name, params)

    widget.service.rpc = rpc
    review(widget, automatic=True)
    widget.space_parent.addItem("Subspace of parent", "parent")
    widget.space_parent.setCurrentIndex(widget.space_parent.findData("parent"))
    widget.onboarding_nickname.setText("Atlas")
    widget.finish_onboarding.click()
    qtbot.waitUntil(lambda: not widget.busy)
    assert widget.creation_workspace == "new"
    pending = json.loads(widget.settings.value(binding_key("user", "new")))
    assert pending["ai_setup_pending"] and not pending["background_build"]
    assert widget.onboarding_steps.currentIndex() == widget.ai_review_step
    widget.finish_onboarding.click()
    qtbot.waitUntil(lambda: not widget.busy)
    assert [n for n, _ in calls].count("create_subspace") == 1
    assert calls[-1] == (
        "set_agent_preferences",
        {"p_workspace": "new", "p_nickname": "Atlas", "p_provider": "auto"},
    )
    complete = json.loads(widget.settings.value(binding_key("user", "new")))
    assert not complete["ai_setup_pending"] and complete["background_build"]
    assert widget.onboarding_steps.currentIndex() == 2


def test_dashboard_closes_before_activation_can_start_another_request(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    setup_service(widget)
    widget.loaded(widget.service.snapshot())
    observed = []

    def activating():
        observed.append(widget.isVisible())
        widget.busy = True

    widget.dashboard_requested.connect(activating)
    widget.open_dashboard()
    assert observed == [False] and not widget.isVisible()
    widget.busy = False


def test_pending_setup_cannot_be_bypassed_by_dashboard_after_reopen(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    setup_service(widget)
    widget.loaded(widget.service.snapshot())
    widget.settings.setValue(
        binding_key("user", "new"),
        json.dumps(
            {
                "ai_setup_pending": True,
                "provider": "codex",
                "agent_nickname": "Atlas",
                "background_build": False,
            }
        ),
    )
    calls = []
    widget.dashboard_requested.connect(lambda: calls.append(True))
    widget.open_dashboard()
    assert not calls and widget.isVisible()
    assert widget.creation_workspace == "new" and not widget.onboarding_ack.isChecked()


@pytest.mark.parametrize("bud", [None, "Bud"])
def test_manual_workflow_opens_review_without_background_execution(
    qtbot, tmp_path, monkeypatch, bud
):
    window, _ = setup(qtbot, tmp_path)
    row = dot("Bud") if bud else None
    window.account_dialog.snapshot["dots"] = [row] if row else []
    save_binding(
        window,
        {"provider": "codex", "background_build": False, "auto_plan": False, "ai_setup_version": 1},
    )
    opened = []
    monkeypatch.setattr(
        "aedrova.desktop.builds.open_build",
        lambda w, task, **kw: opened.append((task, kw.get("bud"))) or True,
    )
    monkeypatch.setattr(
        "aedrova.desktop.builds.start_background_build",
        lambda *a, **k: pytest.fail("Manual workflow must not execute"),
    )
    assert window.start_agent_request("@" + (bud or "Aedrova") + " build a page")
    assert len(opened) == 1 and opened[0][1] == row
