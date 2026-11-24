"""A request to build software starts a real build in the person's project, not pasted code."""

import pytest
from test_connected import setup

from aedrova.agents.intent import wants_build
from aedrova.desktop.projects import binding, ensure_project, project_slug, save_binding

BUILD_REQUESTS = [
    "Can you build a python only calculator locally?",
    "could you make me a todo app",
    "i want a calculator in python",
    "write a script that renames files",
    "please create a landing page",
    "I need you to fix the login bug",
    "let's add dark mode to the settings page",
    "make a python calculator",
    "set up a react project",
    "hey can you build a cli tool",
    "I want you to implement the export feature",
    "go ahead and refactor the parser",
    "can you write a function that parses dates",
]
CONVERSATION = [
    "can you explain how the build works",
    "what did we decide about the launch",
    "write an email to the team",
    "make a summary of the meeting",
    "create a plan for next week",
    "can you summarize the repo",
    "how do I build a calculator",
    "add me to the channel",
    "please don't build anything yet",
    "what is a calculator",
    "I want a coffee",
    "can you fix my typo in this sentence",
    "tell me about the project",
    "who wrote the script",
    "show me how to build a bot",
]


@pytest.mark.parametrize("text", BUILD_REQUESTS)
def test_requests_to_build_software_are_builds(text):
    assert wants_build(text)


@pytest.mark.parametrize("text", CONVERSATION)
def test_questions_and_everyday_writing_stay_replies(text):
    assert not wants_build(text)


def test_code_in_a_message_does_not_confuse_the_intent():
    assert not wants_build("what does `build the app` mean in this log")
    assert wants_build("can you build a tool that reads ```{ a: 1 }``` and prints it")


def test_project_names_come_from_the_request():
    assert project_slug("Can you build a python only calculator locally?") == "python-calculator"
    assert project_slug("!!!") == "new-project"


def test_first_build_gets_a_fresh_project_and_never_replaces_an_existing_one(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    root = tmp_path / "projects"
    first = ensure_project(window, "build a python calculator", root)
    assert first == root / "python-calculator" and first.is_dir() and not any(first.iterdir())
    saved = binding(window)
    assert saved["folder"] == str(first) and saved["background_build"] is True
    assert ensure_project(window, "build another thing", root) is None  # already connected
    assert binding(window)["folder"] == str(first)
    save_binding(window, {})
    second = ensure_project(window, "build a python calculator", root)
    assert second == root / "python-calculator-2"


def test_asking_for_a_calculator_without_a_project_starts_a_build(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    monkeypatch.setattr("aedrova.desktop.projects.projects_root", lambda: tmp_path / "made")
    started = []
    monkeypatch.setattr(
        "aedrova.desktop.builds.start_background_build",
        lambda win, request, **options: started.append(request) or True,
    )
    window.send_message("@Aedrova can you build a python only calculator locally?")
    assert len(started) == 1 and "calculator" in started[0]
    folder = binding(window)["folder"]
    assert folder.startswith(str(tmp_path / "made")) and binding(window)["background_build"]
    assert "new project folder" in window.notice.text()


def test_a_plain_question_to_the_agent_is_still_answered_not_built(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    started, analysed = [], []
    monkeypatch.setattr(
        "aedrova.desktop.builds.start_background_build",
        lambda *a, **k: started.append(a) or True,
    )
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.start_analysis",
        lambda win, request, **k: analysed.append(request) or True,
    )
    window.send_message("@Aedrova what did we decide about the launch?")
    assert not started and len(analysed) == 1
    assert not binding(window).get("folder")


def test_an_explicit_manual_workflow_choice_is_never_overridden(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    save_binding(window, {"provider": "codex", "background_build": False})
    folder = ensure_project(window, "build a page", tmp_path / "projects")
    assert folder and binding(window)["folder"] == str(folder)
    assert binding(window)["background_build"] is False
