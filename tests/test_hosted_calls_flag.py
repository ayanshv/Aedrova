"""Packaged builds hide hosted calls unless they are deliberately switched on."""

import json

from aedrova.desktop import hosted_calls


def configure(monkeypatch, tmp_path, content):
    folder = tmp_path / "assets"
    folder.mkdir()
    if content is not None:
        (folder / "public-config.json").write_text(json.dumps(content))
    monkeypatch.setattr(hosted_calls, "__file__", str(tmp_path / "hosted_calls.py"))
    monkeypatch.delenv("AEDROVA_HOSTED_CALLS_ENABLED", raising=False)


def test_source_runs_keep_hosted_calls(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, None)
    assert hosted_calls.hosted_calls_enabled() is True


def test_packaged_config_decides(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, {"hosted_calls_enabled": False})
    assert hosted_calls.hosted_calls_enabled() is False
    (tmp_path / "assets/public-config.json").write_text(
        json.dumps({"hosted_calls_enabled": True})
    )
    assert hosted_calls.hosted_calls_enabled() is True


def test_garbled_config_does_not_enable_calls(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path, {"hosted_calls_enabled": "yes"})
    assert hosted_calls.hosted_calls_enabled() is False
