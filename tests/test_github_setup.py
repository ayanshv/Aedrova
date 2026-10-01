import hashlib
import io
import stat
import zipfile
from pathlib import Path

import pytest
from test_connected import setup

from aedrova.delivery import installer
from aedrova.desktop.github_setup import GitHubSetup


def archive(binary=b"verified binary", *, linked=False):
    data = io.BytesIO()
    prefix = f"gh_{installer.VERSION}_macOS_arm64"
    with zipfile.ZipFile(data, "w") as output:
        item = zipfile.ZipInfo(prefix + "/bin/gh")
        item.external_attr = ((stat.S_IFLNK if linked else stat.S_IFREG) | 0o755) << 16
        output.writestr(item, binary)
        output.writestr(prefix + "/LICENSE", "MIT license")
        output.writestr("../../unwanted", "not extracted")
    return data.getvalue()


def configure(monkeypatch, data):
    monkeypatch.setattr(installer, "architecture", lambda: "arm64")
    monkeypatch.setitem(installer.CHECKSUMS, "arm64", hashlib.sha256(data).hexdigest())


def test_verified_install_only_writes_exact_members(tmp_path, monkeypatch):
    data = archive()
    configure(monkeypatch, data)
    messages = []
    result = installer.install(root=tmp_path, fetch=lambda *a: data, progress=messages.append)
    assert result.read_bytes() == b"verified binary"
    assert result.stat().st_mode & 0o777 == 0o700
    assert (result.parent / "LICENSE").exists()
    assert not (tmp_path.parent / "unwanted").exists()
    assert {p.name for p in result.parent.iterdir()} == {"gh", "LICENSE"}
    assert messages[-1] == "GitHub CLI is installed."


def test_checksum_failure_never_installs(tmp_path, monkeypatch):
    configure(monkeypatch, archive())
    with pytest.raises(ValueError, match="verification failed"):
        installer.install(root=tmp_path, fetch=lambda *a: b"tampered")
    assert not list(tmp_path.iterdir())


def test_cancelled_download_never_installs(tmp_path, monkeypatch):
    data = archive()
    configure(monkeypatch, data)
    with pytest.raises(InterruptedError):
        installer.install(root=tmp_path, fetch=lambda *a: data, cancelled=lambda: True)
    assert not list(tmp_path.iterdir())


def test_archive_symlink_rejected(tmp_path, monkeypatch):
    data = archive(linked=True)
    configure(monkeypatch, data)
    with pytest.raises(ValueError, match="Invalid GitHub archive"):
        installer.install(root=tmp_path, fetch=lambda *a: data)
    assert not list(tmp_path.iterdir())


def test_installer_never_overwrites_existing_binary(tmp_path, monkeypatch):
    data = archive()
    configure(monkeypatch, data)
    result = installer.install(root=tmp_path, fetch=lambda *a: data)
    with pytest.raises(ValueError, match="already exists"):
        installer.install(root=tmp_path, fetch=lambda *a: data)
    assert result.read_bytes() == b"verified binary"
    assert not list(result.parent.parent.glob(".install-*"))


def test_redirect_rejects_unexpected_or_insecure_host():
    redirect = installer.GitHubRedirect()
    for url in ("https://evil.test/file", "http://github.com/file"):
        with pytest.raises(ValueError, match="unexpected host"):
            redirect.redirect_request(None, None, 302, "", {}, url)


def test_setup_install_button_and_completion(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    installed = []

    def find():
        if not installed:
            raise ValueError("missing")
        return "/verified/gh"

    monkeypatch.setattr("aedrova.desktop.github_setup.gh_path", find)
    monkeypatch.setattr(
        "aedrova.desktop.github_setup.install",
        lambda **kwargs: installed.append(True) or Path("/verified/gh"),
    )
    dialog = GitHubSetup(window)
    qtbot.addWidget(dialog)
    assert dialog.install_button.isEnabled()
    assert not dialog.continue_button.isEnabled()
    dialog.install_button.click()
    qtbot.waitUntil(lambda: dialog.job is None)
    assert dialog.login_button.isEnabled() and dialog.continue_button.isEnabled()
    dialog.continue_button.click()
    assert window.settings.value("githubHelperOnboarded", type=bool)


def test_setup_download_failure_allows_retry(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)

    def missing():
        raise ValueError("missing")

    def failure(**kwargs):
        raise ValueError("Download verification failed")

    monkeypatch.setattr("aedrova.desktop.github_setup.gh_path", missing)
    monkeypatch.setattr("aedrova.desktop.github_setup.install", failure)
    dialog = GitHubSetup(window)
    qtbot.addWidget(dialog)
    dialog.install_button.click()
    qtbot.waitUntil(lambda: dialog.job is None)
    assert "verification failed" in dialog.status.text()
    assert dialog.install_button.isEnabled() and not dialog.login_button.isEnabled()


def test_login_failure_does_not_expose_process_output(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    monkeypatch.setattr("aedrova.desktop.github_setup.gh_path", lambda: "/missing/executable")
    dialog = GitHubSetup(window)
    qtbot.addWidget(dialog)
    dialog.login()
    qtbot.waitUntil(lambda: dialog.process is None)
    assert "did not complete" in dialog.status.text()
    assert not dialog.code.text() and not dialog.output
    assert dialog.login_button.isEnabled()


@pytest.mark.parametrize(
    "message",
    [
        "First copy your one-time code: ABCD-1234",
        "One-time code (ABCD-1234) copied to clipboard",
    ],
)
def test_login_code_is_parsed_and_signout_cancels(qtbot, tmp_path, monkeypatch, message):
    window, _ = setup(qtbot, tmp_path)
    helper = tmp_path / "fake-gh"
    helper.write_text(f"#!/bin/sh\nprintf '{message}\\n'\nexec /bin/sleep 20\n")
    helper.chmod(0o700)
    monkeypatch.setattr("aedrova.desktop.github_setup.gh_path", lambda: str(helper))
    dialog = GitHubSetup(window)
    qtbot.addWidget(dialog)
    dialog.login()
    qtbot.waitUntil(lambda: dialog.code.text() == "ABCD-1234")
    window.account_dialog.session_closed.emit()
    qtbot.waitUntil(lambda: dialog.process is None)
    assert dialog.cancelled.is_set()
    assert not dialog.code.text() and not dialog.output


def test_first_dashboard_offers_setup_once(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    calls = []
    monkeypatch.setattr("aedrova.desktop.github_setup.open_github_setup", lambda w: calls.append(w))
    window.settings.setValue("githubHelperOnboarded", False)
    window.open_dashboard()
    qtbot.waitUntil(lambda: len(calls) == 1)
    window.open_dashboard()
    qtbot.wait(30)
    assert len(calls) == 1
