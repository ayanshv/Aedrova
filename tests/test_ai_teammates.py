"""Identity, native mentions, permission revocation and actual task routing."""

from copy import deepcopy

import pytest
from PySide6.QtCore import Qt
from test_background_builds import configured
from test_connected import setup

from aedrova.agents.runtime import LocalRunner
from aedrova.desktop.ai_teammates import Character, TeammatesDialog
from aedrova.desktop.conversation import Composer
from aedrova.desktop.execution import execution_queue
from aedrova.teammates.model import prompt, resolve, validate


def connect_test_tools(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        "aedrova.connectors.service.Vault", lambda: SimpleNamespace(get=lambda *_: "test-token")
    )

    def fetch(url, headers):
        if "/issues?" in url:
            return []
        if url.endswith("/readme"):
            return {}
        return {"full_name": "owner/repo", "description": "Test project"}

    monkeypatch.setattr("aedrova.connectors.service.get_json", fetch)


def profile(role="engineering"):
    return {
        "id": "specialist",
        "workspace_id": "w",
        "version": 1,
        "paused": False,
        "config": {
            "name": "Pixel",
            "role": role,
            "shape": "round",
            "color": "#4388F5",
            "personality": "concise",
            "reporting": "milestones",
            "effort": "quick",
            "importance": "normal",
            "responsibilities": "Help the team with scoped work.",
            "connections": [{"tool": "github", "resource": "owner/repo"}],
        },
    }


def test_profile_settings_never_expand_authority():
    row = profile()
    assert validate(row["config"])
    row["config"]["importance"] = "critical"
    assert "not authority" in prompt(row["config"])
    row["config"]["name"] = "bad name"
    with pytest.raises(ValueError):
        validate(row["config"])


def test_mentions_are_anchored_and_names_dont_match_email_or_longer_names():
    row = profile()
    assert resolve("@Pixel inspect sources", [row]) == (row, "inspect sources")
    assert resolve("<@ai:specialist|Pixel> inspect sources", [row]) == (row, "inspect sources")
    row["config"]["name"] = "Orbit"
    assert resolve("<@ai:specialist|Pixel> inspect sources", [row]) == (row, "inspect sources")
    row["config"]["name"] = "Pixel"
    for text in ("email@Pixel", "@Pixelate hello", "text @Pixel hello"):
        assert resolve(text, [row]) is None


def test_specialist_autocomplete_keeps_persistent_actor_token(qtbot):
    composer = Composer()
    qtbot.addWidget(composer)
    composer.ai_teammates = [profile()]
    composer.show()
    composer.editor.setFocus()
    qtbot.keyClicks(composer.editor, "@pix")
    qtbot.keyClick(composer.editor, Qt.Key.Key_Tab)
    assert composer.editor.toPlainText() == "@Pixel "
    assert composer.mention_tokens["Pixel"] == "<@ai:specialist|Pixel>"


def test_real_analysis_mode_uses_read_only_phase_and_named_result(qtbot, tmp_path, monkeypatch):
    connect_test_tools(monkeypatch)
    window, service, source = configured(qtbot, tmp_path, monkeypatch)
    row = profile("research")
    window.account_dialog.snapshot["ai_teammates"] = [row]
    service.snapshot = lambda: deepcopy(window.account_dialog.snapshot)
    service.ai_teammates = lambda _: {"items": [row], "setup_required": False}
    runs = []

    def run(self, provider, project, text, *, plan):
        runs.append(plan)
        assert "Do not edit files" in text and "AI teammate Pixel" in text
        assert self.timeout == 300
        return "The team requested hello.py. [message:requirement]"

    monkeypatch.setattr(LocalRunner, "run", run)
    assert window.start_agent_request("@Pixel summarize the agreed requirement")
    dialog = window.build_dialog
    qtbot.waitUntil(lambda: dialog.successful_build, timeout=10000)
    assert runs == [True] and not dialog.background_transition
    assert not list(source.iterdir())
    assert "requested hello.py" in window.agent_feed.toPlainText()
    assert window.agent_feed.author_name == "Pixel"
    assert not dialog.review_button.isEnabled()


def test_engineering_keeps_plan_build_and_isolated_checkout(qtbot, tmp_path, monkeypatch):
    connect_test_tools(monkeypatch)
    window, service, source = configured(qtbot, tmp_path, monkeypatch)
    row = profile()
    window.account_dialog.snapshot["ai_teammates"] = [row]
    service.snapshot = lambda: deepcopy(window.account_dialog.snapshot)
    service.ai_teammates = lambda _: {"items": [row], "setup_required": False}
    runs = []

    def run(self, provider, project, text, *, plan):
        runs.append(plan)
        if plan:
            return "Implement hello.py. [message:requirement]"
        (project / "hello.py").write_text("hello=True\n")
        return "Implemented hello.py."

    monkeypatch.setattr(LocalRunner, "run", run)
    assert execution_queue(window).submit("Build hello", teammate=row)
    dialog = window.build_dialog
    qtbot.waitUntil(lambda: dialog.successful_build, timeout=10000)
    assert runs == [True, False]
    assert (dialog.project / "hello.py").exists() and not (source / "hello.py").exists()


def test_revoked_teammate_cancels_and_clears_running_context(qtbot, tmp_path, monkeypatch):
    window, service, source = configured(qtbot, tmp_path, monkeypatch)
    row = profile()
    window.account_dialog.snapshot["ai_teammates"] = [row]
    service.snapshot = lambda: deepcopy(window.account_dialog.snapshot)
    service.ai_teammates = lambda _: {"items": [], "setup_required": False}
    called = []
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **k: called.append(True))
    execution_queue(window).submit("Build hello", teammate=row)
    dialog = window.build_dialog
    qtbot.waitUntil(lambda: not dialog.pending, timeout=10000)
    assert not called
    snapshot = deepcopy(window.account_dialog.snapshot)
    snapshot["ai_teammates"] = []
    dialog.verify_access(snapshot)
    assert dialog.invalidated and dialog.context is None


def test_editor_missing_migration_and_character_do_not_call_provider(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.ai_teammates = lambda _: {"items": [], "setup_required": True}
    dialog = TeammatesDialog(window)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    assert "SQL migration" in dialog.status.text()
    assert not dialog.save.isEnabled()
    assert isinstance(dialog.character, Character)
    dialog.reject()
    assert dialog.closed and not dialog.rows


@pytest.mark.parametrize("role", ["engineering", "research"])
def test_saved_specialist_review_retains_identity_and_analysis_cannot_publish(
    qtbot, tmp_path, monkeypatch, role
):
    from aedrova.desktop.builds import BuildDialog
    from aedrova.desktop.execution import scope
    from aedrova.desktop.projects import binding

    window, service, source = configured(qtbot, tmp_path, monkeypatch)
    row = profile(role)
    window.account_dialog.snapshot["ai_teammates"] = [row]
    service.snapshot = lambda: deepcopy(window.account_dialog.snapshot)
    queue = execution_queue(window)
    queue.timer.stop()
    settings = scope(binding(window))
    settings["ai_teammate"] = row
    run, _ = queue.ledger.enqueue("u", "w", "Saved specialist", settings)
    queue.ledger.update(run, "completed", project=source)
    queue.ledger.save_channels(run, {"c"})
    queue.show_history()
    opened = []
    monkeypatch.setattr(BuildDialog, "open_review", lambda self: opened.append(self))
    queue.dialog.review_result()
    assert len(opened) == (1 if role == "engineering" else 0)
    if opened:
        assert opened[0].teammate == row
        opened[0].invalidate()
    row["paused"] = True
    queue.dialog.review_result()
    assert len(opened) == (1 if role == "engineering" else 0)
