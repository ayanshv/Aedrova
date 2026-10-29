"""Per-reader translations never alter source messages, permissions or technical tokens."""

from types import SimpleNamespace

import pytest
from test_connected import setup

from aedrova.desktop.localization import HINDI
from aedrova.desktop.state import Message
from aedrova.localization import LANGUAGES, chunks, normalize
from aedrova.localization.intents import localized_build


def test_languages_normalize_and_long_prose_preserves_code():
    assert normalize("hi-IN") == "hi" and normalize("ar_SA") == "ar"
    assert normalize([]) == "en" and normalize("unknown") == "en"
    assert len(LANGUAGES) == 20
    source = ("हिन्दी paragraph. " * 900) + '```\nprint("Hello")\n```'
    parts = chunks(source)
    assert "".join(p for p, _ in parts) == source
    assert all(len(p.encode()) <= 6000 for p, prose in parts if prose)
    assert parts[-1] == ('```\nprint("Hello")\n```', False)


@pytest.mark.parametrize(
    "text",
    [
        "एक ऐप बनाओ",
        "इस गलती को ठीक करो",
        "crée une application",
        "crea una app",
        "创建一个应用",
        "アプリを作って",
    ],
)
def test_native_build_requests_keep_the_explicit_coding_path(text):
    from aedrova.agents.routing import category

    assert localized_build(text)
    assert category(text) == "implementation"


@pytest.mark.parametrize(
    "text", ["नमस्ते", "hello", "यह ऐप मत बनाओ", "do not build this", "क्या हाल है?"]
)
def test_native_greetings_and_negative_requests_do_not_start_builds(text):
    assert not localized_build(text)


def test_two_readers_see_different_languages_without_rewriting_history(
    qtbot, tmp_path, monkeypatch
):
    window, source = setup(qtbot, tmp_path)
    qtbot.wait(50)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    source.fork_for_context = lambda: SimpleNamespace(
        client=SimpleNamespace(
            auth=SimpleNamespace(get_session=lambda: SimpleNamespace(access_token="test-token"))
        ),
        close_context=lambda: None,
    )
    monkeypatch.setattr(
        "aedrova.agents.managed.application_origin", lambda: "https://staging.example"
    )
    calls = []

    def request(self, path, body, **kwargs):
        calls.append(body)
        return {"texts": ["नमस्ते" if v == "Hello" else HINDI.get(v, v) for v in body["texts"]]}

    monkeypatch.setattr("aedrova.agents.managed.ManagedClient.request", request)
    original = Message("m", "Alex", "A", "12:00", "Hello")
    window.messages.show_messages([original])
    window.localizer.configure("hi", True)
    qtbot.waitUntil(lambda: window.messages.display_body(original) == "नमस्ते", timeout=5000)
    assert original.body == "Hello"
    assert window.messages.source_messages[0] is original
    assert window.messages.model().index(0, 0).data().endswith("0 replies.")
    window.messages.toggle_original("m")
    assert window.messages.display_body(original) == "Hello"
    window.messages.toggle_original("m")
    assert window.messages.display_body(original) == "नमस्ते"
    window.localizer.configure("en", False)
    assert window.messages.display_body(original) == "Hello"
    assert calls and all(c["workspace"] == "w" for c in calls)
    window.localizer.timer.stop()
    window.localizer.scan_timer.stop()
    qtbot.waitUntil(lambda: not window.localizer.pending, timeout=5000)


def test_interface_switches_back_and_does_not_translate_user_input(qtbot, tmp_path):
    from PySide6.QtWidgets import QLineEdit

    from aedrova.desktop.dialogs import button

    window, _ = setup(qtbot, tmp_path)
    control = button("Continue")
    control.setParent(window)
    control.show()
    field = QLineEdit(window)
    field.setText("My project")
    field.setPlaceholderText("Agent nickname")
    field.show()
    window.localizer.configure("hi", False)
    window.localizer.scan()
    assert control.text() == "जारी रखें"
    assert field.text() == "My project" and field.placeholderText() == "एजेंट का उपनाम"
    window.localizer.configure("en", False)
    window.localizer.scan()
    assert control.text() == "Continue" and field.placeholderText() == "Agent nickname"


def test_signout_clears_private_translation_state(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.localizer.cache[("u", "w", "hi", "message", "Private")] = "निजी"
    window.localizer.originals.add("m")
    window.localizer.clear()
    assert not window.localizer.cache and not window.localizer.originals
    assert window.localizer.language == "en"


def test_translated_enum_submits_original_and_can_be_selected_programmatically(qtbot):
    from aedrova.desktop.controls import ChoiceBox
    from aedrova.localization import choice_source

    choice = ChoiceBox()
    qtbot.addWidget(choice)
    choice.addItems(["owner", "member"])
    choice.setItemText(0, "मालिक")
    choice.setItemText(1, "सदस्य")
    choice.setProperty("i18n_items", [["owner", "मालिक"], ["member", "सदस्य"]])
    assert choice_source(choice) == "owner"
    choice.setCurrentText("member")
    assert choice.currentText() == "सदस्य" and choice_source(choice) == "member"


def test_rtl_is_reader_specific_and_reversible(qtbot, tmp_path):
    from PySide6.QtCore import Qt

    window, _ = setup(qtbot, tmp_path)
    window.localizer.configure("ar", False)
    assert window.layoutDirection() == Qt.LayoutDirection.RightToLeft
    window.localizer.configure("en", False)
    assert window.layoutDirection() == Qt.LayoutDirection.LeftToRight


def test_pending_translation_cannot_cross_language_switch(qtbot, tmp_path, monkeypatch):
    import threading

    window, source = setup(qtbot, tmp_path)
    qtbot.wait(50)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    source.fork_for_context = lambda: SimpleNamespace(
        client=SimpleNamespace(
            auth=SimpleNamespace(get_session=lambda: SimpleNamespace(access_token="test"))
        ),
        close_context=lambda: None,
    )
    monkeypatch.setattr(
        "aedrova.agents.managed.application_origin", lambda: "https://staging.example"
    )
    entered, release = threading.Event(), threading.Event()

    def response(self, path, body, **kwargs):
        entered.set()
        release.wait(3)
        return {"texts": ["हिन्दी" for _ in body["texts"]]}

    monkeypatch.setattr("aedrova.agents.managed.ManagedClient.request", response)
    message = Message("private", "Alex", "A", "12:00", "Hello")
    window.localizer.configure("hi", True)
    window.messages.show_messages([message])
    window.messages.display_body(message)
    window.localizer.flush()
    qtbot.waitUntil(entered.is_set)
    window.localizer.configure("en", False)
    release.set()
    qtbot.waitUntil(lambda: not window.localizer.pending)
    assert window.messages.display_body(message) == "Hello"
    assert not window.localizer.cache


def test_snapshot_refresh_preserves_translation_generation(qtbot, tmp_path):
    window, source = setup(qtbot, tmp_path)
    source.user.user_metadata = {"aedrova_language": "hi", "aedrova_translate": True}
    window.localizer.restore_preference()
    generation = window.localizer.generation
    window.localizer.restore_preference()
    assert window.localizer.generation == generation
    assert window.localizer.language == "hi"


def test_quoted_native_examples_do_not_authorize_builds():
    assert not localized_build('What does "एक ऐप बनाओ" mean?')
    assert not localized_build("Translate: एक ऐप बनाओ")
    assert not localized_build("The phrase is “创建一个应用”.")
    assert localized_build("एक ऐप बनाओ")
