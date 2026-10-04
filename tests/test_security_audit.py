"""M13 credential and loopback boundary regressions; synthetic credentials only."""

from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from test_builds import service

from aedrova.agents.checkout import prepare
from aedrova.agents.context import gather
from aedrova.delivery.preview import StaticPreview
from aedrova.security.credentials import credential_rules


@pytest.mark.parametrize(
    "prefix,rule",
    [
        ("sk-proj-", "provider-secret"),
        ("sk-ant-", "provider-secret"),
        ("sb_secret_", "supabase-secret"),
        ("sk_live_", "stripe-secret"),
        ("rk_test_", "stripe-secret"),
        ("whsec_", "stripe-secret"),
        ("ghp_", "github-token"),
        ("GOCSPX-", "google-client-secret"),
    ],
)
def test_snapshot_refuses_hardcoded_credentials_without_echo(tmp_path, prefix, rule):
    secret = prefix + "x" * 40
    source = tmp_path / "source"
    source.mkdir()
    (source / "config.py").write_text("key = " + repr(secret))
    assert rule in credential_rules(secret.encode())
    with pytest.raises(ValueError) as error:
        prepare(source, tmp_path / "builds")
    assert secret not in str(error.value)
    assert all(
        secret.encode() not in p.read_bytes()
        for p in (tmp_path / "builds").rglob("*")
        if p.is_file()
    )


def test_credential_files_are_not_copied(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "main.py").write_text("print('hello')")
    for name in (".aws/credentials", ".ssh/config", ".npmrc", ".netrc", "auth.json"):
        file = source / name
        file.parent.mkdir(exist_ok=True)
        file.write_text("synthetic protected content")
    project = prepare(source, tmp_path / "builds")
    assert (project / "main.py").exists()
    assert not (project / ".aws").exists()
    assert not (project / ".ssh").exists()
    assert not (project / "auth.json").exists()


def test_chat_credential_never_enters_provider_context():
    source = service()
    secret = "whsec_" + "x" * 40
    source.context_page = lambda channel, **kwargs: [
        {"id": "m", "channel_id": channel, "sequence": 1, "body": secret}
    ]
    with pytest.raises(ValueError) as error:
        gather(source, "w")
    assert secret not in str(error.value)


@pytest.mark.parametrize("method", ["GET", "HEAD"])
@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "attacker.example"},
        {"Origin": "https://attacker.example"},
    ],
)
def test_preview_rejects_foreign_host_and_origin(tmp_path, method, headers):
    (tmp_path / "index.html").write_text("private preview")
    preview = StaticPreview(tmp_path)
    try:
        with pytest.raises(HTTPError) as error:
            urlopen(Request(preview.url, headers=headers, method=method))
        assert error.value.code == 403
        assert b"private preview" not in error.value.read()
    finally:
        preview.close()
