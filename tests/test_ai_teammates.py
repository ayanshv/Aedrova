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


def test_legacy_mentions_no_longer_route_autonomous_specialists(qtbot, tmp_path, monkeypatch):
    window, service, source = configured(qtbot, tmp_path, monkeypatch)
    window.account_dialog.snapshot["ai_teammates"] = [profile("research")]
    called = []
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **k: called.append(True))
    assert not window.start_agent_request("@Pixel summarize the agreed requirement")
    assert not called and not list(source.iterdir())


def test_legacy_queue_is_paused_for_explicit_migration(qtbot, tmp_path, monkeypatch):
    from aedrova.desktop.execution import scope
    from aedrova.desktop.projects import binding

    window, service, source = configured(qtbot, tmp_path, monkeypatch)
    queue = execution_queue(window)
    saved = scope(binding(window))
    saved["ai_teammate"] = profile()
    run, _ = queue.ledger.enqueue("u", "w", "Build hello", saved)
    called = []
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **k: called.append(True))
    queue.tick()
    assert next(r for r in queue.ledger.rows("u", "w") if r["id"] == run)["state"] == "paused"
    assert not called and not list(source.iterdir())


def test_central_builder_remains_available_without_dots(qtbot, tmp_path, monkeypatch):
    window, service, source = configured(qtbot, tmp_path, monkeypatch)
    window.account_dialog.snapshot["dots"] = []
    runs = []

    def run(self, provider, project, text, *, plan):
        runs.append(plan)
        if plan:
            return "Implement hello.py. [message:requirement]"
        (project / "hello.py").write_text("hello=True\n")
        return "Implemented hello.py."

    monkeypatch.setattr(LocalRunner, "run", run)
    assert window.start_agent_request("@Aedrova build hello")
    dialog = window.build_dialog
    qtbot.waitUntil(lambda: dialog.successful_build, timeout=10000)
    assert runs == [True, False]
    assert (dialog.project / "hello.py").exists() and not (source / "hello.py").exists()


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
