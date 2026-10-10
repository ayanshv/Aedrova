"""Two normal Google sign-ins and synthetic Product Memory acceptance checks.

Creates one named test workspace. Uses only user tokens in memory, never admin
credentials. The second account is invited only to synthetic test data, then
removed. Reports contain checks/IDs only; tokens and exception contents are hidden.
"""

import json
import traceback
from pathlib import Path
from uuid import uuid4

from aedrova.identity.oauth import google_sign_in
from aedrova.identity.service import Connection, IdentityService

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "work/m15/hosted-memory-check.json"


def denied(action, code="42501"):
    try:
        action()
    except Exception as error:
        if getattr(error, "code", None) == code:
            return
        raise
    raise AssertionError("Unauthorized or stale operation accepted")


def probe(owner, member, report):
    assert owner.user.id != member.user.id, "Choose two different accounts"
    workspace = owner.rpc(
        "onboard_workspace",
        {
            "p_name": "Product memory validation " + uuid4().hex[:6],
            "p_nickname": "Aedrova",
            "p_provider": "codex",
        },
    )
    report["workspace"] = workspace
    channel = (
        owner.client.table("channels")
        .select("id")
        .eq("workspace_id", workspace)
        .execute()
        .data[0]["id"]
    )
    private = owner.rpc(
        "create_channel",
        {
            "p_workspace": workspace,
            "p_name": "private-memory-check",
            "p_private": True,
        },
    )
    identifiers = [str(uuid4()) for _ in range(5)]
    message, private_message, entry, private_entry, replacement = identifiers
    owner.rpc(
        "send_message",
        {
            "p_id": message,
            "p_channel": channel,
            "p_body": "M15 synthetic test: export timestamps in UTC.",
        },
    )
    owner.rpc(
        "send_message",
        {
            "p_id": private_message,
            "p_channel": private,
            "p_body": "M15 synthetic private test: preserve private source access.",
        },
    )

    def params(identifier, scope, source, version=0, state="proposal"):
        return {
            "p_id": identifier,
            "p_workspace": workspace,
            "p_channel": scope,
            "p_version": version,
            "p_kind": "constraint",
            "p_title": "Synthetic M15 check",
            "p_body": "Test fixture only: timestamp export requirement.",
            "p_state": state,
            "p_sources": [owner.memory_source("message", source)],
        }

    proposal = params(entry, channel, message)
    owner.save_memory(proposal)
    rows = owner.memory_list(workspace)["items"]
    assert len(rows) == 1 and rows[0]["state"] == "proposal" and rows[0]["fresh"]
    report["proposal_persistence"] = "passed"
    print("Checking approval save and history…", flush=True)
    approved = params(entry, channel, message, 1, "approved")
    owner.save_memory(approved)
    assert len(owner.memory_history(entry)) == 2
    print("Checking stale version rejection…", flush=True)
    denied(lambda: owner.save_memory(approved), "PT409")
    print("Approval and stale edit checks passed.", flush=True)
    report["approval_history_optimistic_edits"] = "passed"
    print("Checking private entry and outsider access…", flush=True)
    owner.save_memory(params(private_entry, private, private_message, state="approved"))
    denied(lambda: member.memory_list(workspace))
    invite = owner.rpc(
        "create_invitation",
        {
            "p_workspace": workspace,
            "p_email": member.user.email,
            "p_role": "member",
        },
    )
    print("Joining second account to synthetic workspace…", flush=True)
    member.rpc("accept_invitation", {"p_token": invite})
    try:
        assert member.memory_list(workspace)["total"] == 1
        assert len(member.memory_history(entry)) == 2
        assert member.memory_history(private_entry) == []
        assert member.memory_source("message", private_message) is None
        denied(lambda: member.save_memory(params(str(uuid4()), private, private_message)))
        denied(
            lambda: (
                member.client.table("product_memory")
                .update({"body": "Unauthorized direct write"})
                .eq("id", entry)
                .execute()
            )
        )
        print("Two-account privacy checks passed.", flush=True)
        report["shared_visibility_private_isolation_direct_write_denial"] = "passed"
        owner.rpc(
            "chat_action",
            {
                "p_action": "edit",
                "p_data": {
                    "message": message,
                    "body": "M15 synthetic test: export timestamps with local offsets.",
                },
            },
        )
        assert member.memory_list(workspace)["items"][0]["fresh"] is False
        stale = dict(approved, p_version=2)
        denied(lambda: owner.save_memory(stale), "PT409")
        print("Edited source checks passed.", flush=True)
        report["edited_evidence_staleness"] = "passed"
        updated = params(entry, channel, message, 2, "approved")
        owner.save_memory(updated)
        assert member.memory_list(workspace)["items"][0]["fresh"] is True
        replacement_params = params(replacement, channel, message, state="approved")
        replacement_params.update(p_supersedes=entry, p_supersedes_version=3)
        owner.save_memory(replacement_params)
        assert owner.memory_list(workspace, active=True)["total"] == 2
        assert len(owner.memory_history(entry)) == 4
        owner.save_memory(params(replacement, channel, message, 1, "retired"))
        assert member.memory_list(workspace, active=True)["total"] == 0
        report["replacement_retirement_active_context"] = "passed"
        owner.rpc("unsend_message", {"p_message": message})
        assert member.memory_list(workspace)["total"] == 0
        assert member.memory_history(entry) == []
        assert member.memory_history(replacement) == []
        report["unsent_source_purges_entries_and_history"] = "passed"
    finally:
        owner.rpc("remove_member", {"p_workspace": workspace, "p_user": str(member.user.id)})
    denied(lambda: member.memory_list(workspace))
    assert member.memory_history(private_entry) == []
    report["membership_revocation"] = "passed"
    report["status"] = "passed"


def main():
    accounts = []
    report = {
        "status": "incomplete",
        "data": "synthetic test fixtures only",
        "live_provider_build": "not tested",
    }
    stage = "public configuration"
    try:
        config = json.loads(
            (
                ROOT
                / "dist/Aedrova.app/Contents/Resources/aedrova/desktop/assets/public-config.json"
            ).read_text()
        )
        connection = Connection(config["supabase_url"], config["supabase_publishable_key"])
        for title in ("personal account", "school account"):
            stage = "Google sign-in: " + title
            print("Sign in with " + title + " in the opened browser.", flush=True)
            account = IdentityService(connection)
            accounts.append(account)
            google_sign_in(account, timeout=300)
            print("Authenticated. Credentials remain in memory.", flush=True)
        stage = "hosted memory acceptance"
        probe(*accounts, report)
        print(
            "PASS hosted Product Memory persistence, lifecycle, freshness and two-account privacy.",
            flush=True,
        )
    except Exception as error:
        own = [
            frame
            for frame in traceback.extract_tb(error.__traceback__)
            if frame.filename == __file__
        ]
        report.update(
            status="failed",
            stage=stage,
            error_type=type(error).__name__,
            line=own[-1].lineno if own else None,
        )
        print(
            f"FAIL {stage} ({type(error).__name__}, line {report['line']}). No credentials logged.",
            flush=True,
        )
        raise SystemExit(1) from None
    finally:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2))
        for account in accounts:
            if account._transport:
                account._transport.close()


if __name__ == "__main__":
    main()
