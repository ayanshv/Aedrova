import json
from types import SimpleNamespace
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from aedrova.imports.slack import preview, upload


def export(tmp_path, entries):
    path = tmp_path / "slack.zip"
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, value in entries.items():
            archive.writestr(name, json.dumps(value))
    return path


def test_public_preview_preserves_thread_and_ignores_restricted_folders(tmp_path):
    base = {"type": "message", "ts": "1700000000.000001", "user": "U123", "text": "The launch plan"}
    path = export(
        tmp_path,
        {
            "channels.json": [
                {"id": "C123", "name": "general"},
                {"id": "C234", "name": "shared", "is_ext_shared": True},
                {"id": "C345", "name": "private"},
            ],
            "groups.json": [{"id": "C345", "name": "private"}],
            "users.json": [{"id": "U123", "real_name": "Maya"}],
            "general/2023-11-14.json": [
                base,
                dict(
                    base,
                    ts="1700000000.000002",
                    thread_ts=base["ts"],
                    text="Agreed",
                    reactions=[{"name": "thumbsup", "count": 2}],
                    files=[
                        {"permalink": "https://files.slack.com/example"},
                        {"permalink": "https://files.slack.com.example.org/example"},
                    ],
                ),
            ],
            "shared/2023-11-14.json": [base],
            "private/2023-11-14.json": [base],
            "D123/2023-11-14.json": [base],
        },
    )
    rows, counts, skips = preview(path)
    assert counts == {"general": 2}
    assert skips == 3
    assert rows[0]["author"] == "Maya"
    assert rows[1]["thread_ts"] == rows[0]["source_ts"]
    assert rows[1]["reactions"] == {"thumbsup": 2}
    assert rows[1]["links"] == ["https://files.slack.com/example"]


def test_unsafe_paths_abort_preview(tmp_path):
    with pytest.raises(ValueError, match="invalid or duplicate"):
        preview(export(tmp_path, {"channels.json": [], "../escape.json": []}))


def test_cancelled_upload_resumes_with_same_identifier():
    class Service:
        user = SimpleNamespace(id="owner")
        calls = []

        def rpc(self, name, body):
            if name == "list_slack_imports":
                if not self.calls:
                    return []
                return [{"id": self.calls[0]["p_import"], "next_batch": 1}]
            assert name == "write_slack_history"
            self.calls.append(body)
            return len(body["p_rows"])

    service = Service()
    rows = [{"channel_id": "C123", "source_ts": f"1700000000.{index:06d}"} for index in range(480)]
    with pytest.raises(InterruptedError):
        upload(service, "workspace", rows, lambda: len(service.calls) > 0)
    assert len(service.calls) == 1 and not service.calls[0]["p_finish"]
    upload(service, "workspace", list(reversed(rows)))
    assert len({call["p_import"] for call in service.calls}) == 1
    assert [call["p_batch"] for call in service.calls] == [0, 1, 2]
    assert all(len(call["p_rows"]) <= 200 for call in service.calls)
    assert service.calls[-1]["p_finish"]


def test_slack_citations_are_checked_and_removed_context_is_rejected():
    from aedrova.agents.context import WorkspaceContext, recheck_slack
    from aedrova.agents.retrieval import validate_citations

    citation = "slack:C123:1700000000.000001"
    body = "We approved the onboarding prototype."
    context = WorkspaceContext(
        "workspace",
        "user",
        frozenset(),
        json.dumps(
            {
                "imported_slack_message": {
                    "citation": citation,
                    "channel": "launch",
                    "timestamp": "1700000000.000001",
                    "text": body,
                }
            }
        ),
        0,
        "Aedrova",
        "codex",
    )
    assert validate_citations(context, f"See {citation}.") == [citation]
    service = SimpleNamespace(slack_history=lambda *args: [{"id": citation, "body": body}])
    assert recheck_slack(service, context)
    service.slack_history = lambda *args: []
    with pytest.raises(PermissionError, match="Slack history changed"):
        recheck_slack(service, context)


def test_native_dialog_previews_before_confirming(qtbot, tmp_path):
    from PySide6.QtWidgets import QWidget

    from aedrova.desktop.slack_history import open_slack_history

    parent = QWidget()
    qtbot.addWidget(parent)
    parent.show()
    requests = []

    def rpc(name, params):
        requests.append((name, params))
        if name == "list_slack_imports":
            return []
        return len(params["p_rows"])

    service = SimpleNamespace(user=SimpleNamespace(id="owner"), rpc=rpc)
    path = export(
        tmp_path,
        {
            "channels.json": [{"id": "C123", "name": "general"}],
            "general/2023-11-14.json": [
                {
                    "type": "message",
                    "ts": "1700000000.000001",
                    "text": "Draft is ready",
                }
            ],
        },
    )
    open_slack_history(parent, service, "workspace")
    dialog = parent.slack_history_dialog
    dialog.load_zip(path)
    qtbot.waitUntil(dialog.primary.isEnabled)
    assert dialog.items.count() == 1
    assert not requests
    dialog.primary.click()
    qtbot.waitUntil(lambda: dialog.primary.text() == "View imported history")
    assert requests[-1][1]["p_finish"]
    assert requests[-1][1]["p_workspace"] == "workspace"
    dialog.accept()
    assert not dialog.isVisible()
    open_slack_history(parent, service, "workspace")
    assert parent.slack_history_dialog is not dialog


def test_upload_reports_progress_in_batches_and_skips_saved_ones():
    class Service:
        user = SimpleNamespace(id="owner")
        calls = []

        def rpc(self, name, body):
            if name == "list_slack_imports":
                return []
            self.calls.append(body)
            return len(body["p_rows"])

    service, seen = Service(), []
    rows = [{"channel_id": "C123", "source_ts": f"1700000000.{i:06d}"} for i in range(450)]
    upload(service, "workspace", rows, progress=lambda sent, total: seen.append((sent, total)))
    assert seen[0] == (0, 3) and seen[-1] == (3, 3)
    assert [s for s, _ in seen] == sorted(s for s, _ in seen)


def test_panel_shows_a_plain_message_for_a_bad_zip(qtbot, tmp_path):
    from aedrova.desktop.slack_history import SlackImportPanel

    panel = SlackImportPanel(SimpleNamespace(user=SimpleNamespace(id="owner")), "workspace")
    qtbot.addWidget(panel)
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip")
    panel.load_zip(bad)
    qtbot.waitUntil(lambda: not panel.busy)
    assert "valid Slack" in panel.status.text()
    assert not panel.primary.isEnabled() and panel.items.isHidden()


def message(ts="1700000000.000001", **fields):
    return {"type": "message", "ts": ts, "user": "U1", "text": "hello", **fields}


def test_hostile_or_broken_archives_are_refused_with_plain_messages(tmp_path, monkeypatch):
    from aedrova.imports import slack

    plain = {"channels.json": [{"id": "C1", "name": "general"}]}
    path = export(tmp_path, plain | {"general/2023-11-14.json": [message()]})
    monkeypatch.setattr(slack, "MAX_ZIP", 10)
    with pytest.raises(ValueError, match="smaller than 32 MB"):
        preview(path)
    monkeypatch.undo()
    monkeypatch.setattr(slack, "MAX_EXPANDED", 10)
    with pytest.raises(ValueError, match="exceeds the import limits"):
        preview(path)
    monkeypatch.undo()
    monkeypatch.setattr(slack, "MAX_ROWS", 1)
    many = export(
        tmp_path,
        plain
        | {
            "general/2023-11-14.json": [
                message(),
                message("1700000001.000001"),
                message("1700000002.000001"),
            ]
        },
    )
    with pytest.raises(ValueError, match="over 50,000"):
        preview(many)
    monkeypatch.undo()
    missing = tmp_path / "missing.zip"
    with ZipFile(missing, "w") as archive:
        archive.writestr("general/2023-11-14.json", "[]")
    with pytest.raises(ValueError, match="public-channel manifest"):
        preview(missing)
    garbage = tmp_path / "garbage.zip"
    garbage.write_bytes(b"PK not really")
    with pytest.raises(ValueError, match="valid Slack"):
        preview(garbage)
    broken = tmp_path / "broken.zip"
    with ZipFile(broken, "w") as archive:
        archive.writestr("channels.json", "{not json")
    with pytest.raises(ValueError, match="valid Slack"):
        preview(broken)
    twins = export(
        tmp_path,
        {"channels.json": [{"id": "C1", "name": "a"}, {"id": "C1", "name": "b"}]},
    )
    with pytest.raises(ValueError, match="duplicate channel"):
        preview(twins)


def test_only_real_messages_in_public_channels_come_through(tmp_path):
    path = export(
        tmp_path,
        {
            "channels.json": [
                {"id": "C1", "name": "general"},
                {"id": "C2", "name": "partner", "shared_team_ids": ["T1", "T2"]},
                {"id": "C3", "name": "secret", "is_private": True},
            ],
            "users.json": [{"id": "U1", "real_name": "Maya"}],
            "general/2023-11-14.json": [
                message(text="keep \x00this"),
                message("1700000001.000001", subtype="channel_join"),
                message("1700000002.000001", subtype="message_deleted"),
                message("1700000003.000001", hidden=True),
                message("not-a-timestamp"),
                message("1700000004.000001", text="   "),
                message("1700000005.000001", user="B1", text="bot says hi"),
            ],
            "partner/2023-11-14.json": [message()],
            "secret/2023-11-14.json": [message()],
        },
    )
    rows, counts, skipped = preview(path)
    assert counts == {"general": 2} and skipped == 2
    assert [row["body"] for row in rows] == ["keep this", "bot says hi"]
    assert rows[1]["author"] == "B1"  # attribution only: no account is created or linked


def test_a_channel_opens_as_a_read_only_copy_with_its_messages(qtbot):
    from PySide6.QtWidgets import QWidget

    from aedrova.desktop.slack_history import open_slack_history

    parent = QWidget()
    qtbot.addWidget(parent)
    parent.show()
    pages = []
    rows = [
        {
            "id": "slack:C1:1700000000.000001",
            "author": "Maya",
            "body": "Launch plan is set",
            "source_ts": "1700000000.000001",
            "thread_ts": None,
            "links": [],
            "reactions": {"tada": 2},
        },
        {
            "id": "slack:C1:1700000100.000001",
            "author": "Sam",
            "body": "<b>Agreed</b>",
            "source_ts": "1700000100.000001",
            "thread_ts": "1700000000.000001",
            "links": [],
            "reactions": {},
        },
    ]

    def messages(workspace, channel, before=None, limit=100):
        pages.append((workspace, channel, before, limit))
        return rows

    service = SimpleNamespace(user=SimpleNamespace(id="u"), slack_channel_messages=messages)
    open_slack_history(
        parent,
        service,
        "w",
        mode="channel",
        channel={"channel_id": "C1", "channel_name": "launch"},
    )
    dialog = parent.slack_history_dialog
    qtbot.waitUntil(lambda: bool(dialog.log.toPlainText()), timeout=3000)
    text = dialog.log.toPlainText()
    assert dialog.windowTitle() == "#launch" and pages == [("w", "C1", None, 100)]
    assert "Maya · Nov 14, 2023 22:13 UTC" in text and "Launch plan is set" in text
    assert "Reply · Sam" in text and "<b>Agreed</b>" in text  # shown as text, never interpreted
    assert ":tada: 2" in text and not dialog.earlier.isVisible()
    assert dialog.log.isReadOnly() and dialog.items.isHidden()
    dialog.accept()


def test_the_sidebar_lists_imported_channels_and_opens_one(qtbot, tmp_path):
    import sys

    sys.path.insert(0, "tests")
    from test_connected import setup

    window, service = setup(qtbot, tmp_path)
    service.slack_channels = lambda workspace: [
        {"channel_id": "C1", "channel_name": "general", "message_count": 120},
        {"channel_id": "C2", "channel_name": "launch", "message_count": 8},
    ]
    service.slack_channel_messages = lambda *a, **k: []
    window.slack_archive.refresh(force=True)
    qtbot.waitUntil(lambda: window.slack_archive.list.count() == 2, timeout=3000)
    assert window.slack_archive.isVisible()
    assert window.slack_archive.list.item(0).text().endswith("general")
    window.slack_archive.open_channel(window.slack_archive.list.item(1))
    assert window.slack_history_dialog.windowTitle() == "#launch"
    window.slack_history_dialog.accept()
    service.slack_channels = lambda workspace: []
    window.slack_archive.refresh(force=True)
    qtbot.waitUntil(lambda: window.slack_archive.isHidden(), timeout=3000)
    window.connected.timer.stop()


def test_instructions_are_numbered_explicit_and_open_slacks_guide(qtbot):
    from aedrova.desktop.slack_steps import EXPORT_HELP, IN_AEDROVA, IN_SLACK, ExportSteps

    opened = []
    steps = ExportSteps(open_url=lambda url: opened.append(url.toString()))
    qtbot.addWidget(steps)
    assert len(steps.steps) == len(IN_SLACK) + len(IN_AEDROVA) == 8
    text = " ".join(step.text.text() for step in steps.steps)
    for must_say in (
        "Workspace settings",
        "Export tab",
        "Start export",
        "Download",
        ".zip",
        "Import history",
        "Untick",
    ):
        assert must_say in text
    assert not steps.guide.icon().isNull()  # the Slack mark
    steps.guide.click()
    assert opened == [EXPORT_HELP]


def test_the_slack_mark_renders_in_its_four_colours(qtbot):
    from aedrova.desktop.slack_logo import slack_pixmap

    image = slack_pixmap(64).toImage()
    colours = {image.pixelColor(x, y).name() for x in range(0, 128, 4) for y in range(0, 128, 4)}
    assert {"#35c5f0", "#2eb67d", "#ecb22e", "#de1c59"} <= colours


def test_setup_uses_three_short_lines_and_the_settings_dialog_keeps_all_eight(qtbot):
    from aedrova.desktop.slack_steps import QUICK, QuickSteps

    quick = QuickSteps(open_url=lambda url: None)
    qtbot.addWidget(quick)
    assert len(quick.steps) == len(QUICK) == 3
    assert all(len(step.text.text().split()) <= 16 for step in quick.steps)
