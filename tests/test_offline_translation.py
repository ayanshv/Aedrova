"""Offline admission, preservation and two concurrent real UI reader scopes."""

from unittest.mock import Mock

import pytest

from aedrova.localization import offline


def test_missing_pack_never_uses_network_or_cloud(monkeypatch, tmp_path):
    monkeypatch.setenv("AEDROVA_TRANSLATION_MODELS", str(tmp_path))
    cloud = Mock(side_effect=AssertionError("Cloud must not be called"))
    monkeypatch.setattr("aedrova.agents.managed.ManagedClient.request", cloud)
    monkeypatch.setattr("httpx.Client.request", cloud)
    result = offline.batch([("Hello", False)], "hi")
    assert result == {"texts": ["Hello"], "unavailable": [0]}
    cloud.assert_not_called()


def test_technical_spans_and_source_prompt_are_preserved(monkeypatch):
    seen = []

    class Tokenizer:
        def encode(self, text, out_type):
            seen.append(text)
            return [text]

        def decode(self, tokens):
            return tokens[0]

    class Engine:
        def translate_batch(self, tokens, **kwargs):
            from types import SimpleNamespace

            return [SimpleNamespace(hypotheses=[["हिन्दी"]])]

    monkeypatch.setattr(offline, "_engine", lambda *args: (Engine(), Tokenizer()))
    source = "Hello @Aedrova https://aedrova.com `print(1)` **world**\n```\nsecret = 1\n```"
    result = offline.translate(source, "hi", interface=True)
    for token in ("@Aedrova", "https://aedrova.com", "`print(1)`", "**", "```\nsecret = 1\n```"):
        assert token in result
    assert not any("secret" in text or "print" in text or "https" in text for text in seen)
    assert source.startswith("Hello")


def test_language_data_must_match_pinned_hash(monkeypatch, tmp_path):
    monkeypatch.setenv("AEDROVA_TRANSLATION_MODELS", str(tmp_path / "models"))
    data = tmp_path / "bad.argosmodel"
    data.write_bytes(b"bad")
    with pytest.raises(ValueError, match="verification"):
        offline.install_archive(data, {"bytes": 3, "sha256": "0" * 64})
    assert not (tmp_path / "models").exists()


def test_hindi_prompts_detect_without_rewriting_and_unsupported_keeps_original():
    assert offline.source_language("कृपया @Aedrova यह ऐप बनाओ") == "hi"
    assert offline.source_language("Hello @Aedrova") == "en"
    assert offline.batch([("Hello", False)], "ja")["texts"] == ["Hello"]


def test_simultaneous_readers_do_not_share_display_or_prompt_state(qtbot, tmp_path, monkeypatch):
    from test_connected import setup

    from aedrova.desktop.state import Message

    def local(items, target):
        return {
            "texts": [
                ({"Hello": "नमस्ते"} if target == "hi" else {"नमस्ते": "Hello"}).get(text, text)
                for text, _ in items
            ]
        }

    monkeypatch.setattr(offline, "batch", local)
    first, _ = setup(qtbot, tmp_path / "first")
    second, _ = setup(qtbot, tmp_path / "second")
    qtbot.waitUntil(lambda: not first.account_dialog.busy and not second.account_dialog.busy)
    first.localizer.account_id = "english-reader"
    second.localizer.account_id = "hindi-reader"
    first.localizer.configure("en", True)
    second.localizer.configure("hi", True)
    english = Message("en", "Alex", "A", "12:00", "Hello")
    hindi = Message("hi", "Alex", "A", "12:01", "नमस्ते")
    for window in (first, second):
        window.channel.messages = [english, hindi]
        window.messages.show_messages([english, hindi])
    qtbot.waitUntil(lambda: first.messages.display_body(hindi) == "Hello")
    qtbot.waitUntil(lambda: second.messages.display_body(english) == "नमस्ते")
    assert first.messages.display_body(english) == "Hello"
    assert second.messages.display_body(hindi) == "नमस्ते"
    second.messages.toggle_original("en")
    assert second.messages.display_body(english) == "Hello"
    assert first.messages.display_body(hindi) == "Hello"
    prompt = "कृपया @Aedrova यह ऐप बनाओ"
    second.composer.editor.setPlainText(prompt)
    second.localizer.scan()
    assert second.composer.submission_text() == prompt
    assert (english.body, hindi.body) == ("Hello", "नमस्ते")
    assert all(k[0] == "english-reader" for k in first.localizer.cache)
    assert all(k[0] == "hindi-reader" for k in second.localizer.cache)


def test_context_markers_preserve_mentions_without_exposing_technical_spans(monkeypatch):
    from types import SimpleNamespace

    class Tokenizer:
        def encode(self, text, out_type):
            return [text]

        def decode(self, tokens):
            return tokens[0]

    class Engine:
        def translate_batch(self, tokens, **kwargs):
            assert tokens[0] == ["कृपया ZXQ0QXZ सारांश दें।"]
            return [SimpleNamespace(hypotheses=[["Please summarize for ZXQ0QXZ."]])]

    monkeypatch.setattr(offline, "_engine", lambda *args: (Engine(), Tokenizer()))
    assert offline.translate("कृपया @Aedrova सारांश दें।", "en") == "Please summarize for @Aedrova."
