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
