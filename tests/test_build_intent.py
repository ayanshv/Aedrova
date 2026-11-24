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


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            'create a project folder in my documents folder called "Soysee" and add a page',
            ("Soysee", "documents"),
        ),
        ("make a folder named Notes on my desktop", ("Notes", "desktop")),
        ("create a project folder called Soy See, then build a UI", ("Soy See", "documents")),
        ("create a folder called Work in my home folder", ("Work", "home")),
        ("build me a calculator", None),
        ("what is a folder called", None),
        ("create a folder called ../escape", None),
    ],
)
def test_a_named_project_folder_is_understood(text, expected):
    from aedrova.agents.intent import requested_project

    assert requested_project(text) == expected


def test_named_project_is_created_in_documents_and_connected(qtbot, tmp_path):
    from aedrova.desktop.projects import use_named_project

    window, _ = setup(qtbot, tmp_path)
    (tmp_path / "Documents").mkdir()
    save_binding(window, {"folder": str(tmp_path / "old-project"), "provider": "codex"})
    folder = use_named_project(window, "Soysee", "documents", home=tmp_path)
    assert folder == tmp_path / "Documents" / "Soysee" and folder.is_dir()
    assert binding(window)["folder"] == str(folder)
    assert use_named_project(window, "Soysee", "documents", home=tmp_path) == folder  # reuse


def test_asking_for_a_named_project_moves_the_build_there(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    (tmp_path / "Documents").mkdir()
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda cls: tmp_path))
    save_binding(window, {"folder": str(tmp_path / "other"), "provider": "codex"})
    started = []
    monkeypatch.setattr(
        "aedrova.desktop.builds.start_background_build",
        lambda win, request, **options: started.append(request) or True,
    )
    window.send_message(
        '@Aedrova create a project folder in my documents folder called "Soysee" '
        "and create the basic MVP UI"
    )
    assert binding(window)["folder"] == str(tmp_path / "Documents" / "Soysee")
    assert (tmp_path / "Documents" / "Soysee").is_dir() and len(started) == 1


def test_what_is_left_after_the_folder_clause_decides_between_direct_and_build():
    from aedrova.agents.intent import (
        only_makes_a_folder,
        wants_folder_opened,
        without_folder_request,
    )

    assert only_makes_a_folder("create a folder called Test Calc in my Documents folder.")
    assert only_makes_a_folder("create a folder called Notes on my desktop and open it in finder")
    assert wants_folder_opened("create a folder called Notes and open it in finder")
    mixed = (
        'ok, now create a project folder in my documents folder called "Soysee" '
        "and create the basic MVP UI. Then open locally on my computer."
    )
    assert not only_makes_a_folder(mixed)
    assert without_folder_request(mixed).startswith("create the basic MVP UI")
    assert not only_makes_a_folder("create a folder called X and tell me a joke")


def test_a_folder_only_request_is_answered_directly_with_no_build(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    (tmp_path / "Documents").mkdir()
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda cls: tmp_path))
    started, answers = [], []
    monkeypatch.setattr(
        "aedrova.desktop.builds.start_background_build",
        lambda *a, **k: started.append(a) or True,
    )
    monkeypatch.setattr(
        "aedrova.desktop.builds.open_build", lambda *a, **k: started.append(a) or True
    )
    window.connected.complete_agent_reply = lambda *args, **kw: answers.append(args[2])
    window.send_message("@Aedrova create a folder called Test Calc in my Documents folder.")
    qtbot.waitUntil(lambda: bool(answers), timeout=2000)
    assert not started
    assert (tmp_path / "Documents" / "Test Calc").is_dir()
    assert "Test Calc" in answers[0] and str(tmp_path / "Documents" / "Test Calc") in answers[0]
    assert binding(window)["folder"] == str(tmp_path / "Documents" / "Test Calc")


def test_a_mixed_request_tells_the_builder_the_folder_already_exists(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    (tmp_path / "Documents").mkdir()
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda cls: tmp_path))
    started = []
    monkeypatch.setattr(
        "aedrova.desktop.builds.start_background_build",
        lambda win, request, **options: started.append(request) or True,
    )
    window.send_message(
        '@Aedrova create a project folder in my documents folder called "Soysee" '
        "and create the basic MVP UI"
    )
    assert len(started) == 1
    assert "already exists" in started[0] and "do not try to create it" in started[0]
    assert "create the basic MVP UI" in started[0]
