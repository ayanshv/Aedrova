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
REPORT = ROOT / "work/m16/hosted-build-review-check.json"


def denied(action, code="42501"):
    try:
        action()
    except Exception as error:
        if getattr(error, "code", None) == code:
            return
        raise
    raise AssertionError("Unauthorized or stale operation accepted")


def probe(owner, member, report):
    import subprocess
    import sys
    from tempfile import TemporaryDirectory

    from aedrova.agents.checkout import prepare
    from aedrova.agents.context import WorkspaceContext
    from aedrova.delivery.evidence import command_result, manifest, project_fingerprint
    from aedrova.delivery.files import make_review
    from aedrova.memory.model import snapshot_record

    assert owner.user.id != member.user.id, "Choose two different accounts"
    workspace = owner.rpc(
        "onboard_workspace",
        {
            "p_name": "Build review validation " + uuid4().hex[:6],
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
        {"p_workspace": workspace, "p_name": "private-evidence", "p_private": True},
    )
    source, memory, build, private_build, decision = [str(uuid4()) for _ in range(5)]
    joined = False
    try:
        owner.rpc(
            "send_message",
            {
                "p_id": source,
                "p_channel": channel,
                "p_body": "M16 synthetic acceptance: addition returns the sum.",
            },
        )
        owner.save_memory(
            {
                "p_id": memory,
                "p_workspace": workspace,
                "p_channel": channel,
                "p_version": 0,
                "p_kind": "requirement",
                "p_title": "Synthetic addition requirement",
                "p_body": "Adding 2 and 3 returns 5.",
                "p_state": "approved",
                "p_sources": [owner.memory_source("message", source)],
            }
        )
        channels = frozenset({channel})
        record = snapshot_record(owner.memory_context(workspace), workspace, channels)
        context = WorkspaceContext(
            workspace, str(owner.user.id), channels, json.dumps(record), 1, "Aedrova", "codex"
        )
        with TemporaryDirectory(prefix="aedrova-m16-hosted-") as temp:
            root = Path(temp)
            original = root / "source"
            original.mkdir()
            (original / "addition.py").write_text("def add(a,b):\n    return a-b\n")
            project = prepare(original, root / "builds")
            (project / "addition.py").write_text("def add(a,b):\n    return a+b\n")
            checked = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from addition import add; assert add(2,3)==5; print('1 assertion passed')",
                ],
                cwd=project,
                capture_output=True,
                text=True,
            )
            assert checked.returncode == 0
            receipt = command_result("python: check addition", checked.stdout, checked.returncode)
            receipt["project_fingerprint"] = project_fingerprint(project)
            value = manifest(
                context, "Synthetic M16: correct addition", "codex", make_review(project), [receipt]
            )
        value["acceptance_criteria"] = ["Adding 2 and 3 returns 5."]
        value["requirements"][0].update(
            assessment="reviewer_verified", files=["addition.py"], checks=[receipt["id"]]
        )
        params = {
            "p_id": build,
            "p_workspace": workspace,
            "p_channel": channel,
            "p_sources": [channel],
            "p_version": 0,
            "p_evidence": value,
        }
        print("Checking actual diff/check persistence and safe retries…", flush=True)
        assert owner.save_build_review(params) == 1
        assert owner.save_build_review(params) == 1
        assert owner.client.table("messages").select("id").eq("id", build).execute().data
        denied(lambda: member.build_reviews(workspace))
        private_params = dict(params, p_id=private_build, p_sources=[channel, private])
        owner.save_build_review(private_params)
        report["actual_local_diff_check_persistence_retries"] = "passed"
        invite = owner.rpc(
            "create_invitation",
            {"p_workspace": workspace, "p_email": member.user.email, "p_role": "member"},
        )
        member.rpc("accept_invitation", {"p_token": invite})
        joined = True
        visible = member.build_reviews(workspace)["items"]
        assert len(visible) == 1 and visible[0]["id"] == build and visible[0]["current"]
        assert visible[0]["evidence"]["files"][0]["path"] == "addition.py"
        assert visible[0]["evidence"]["checks"][0]["exit_code"] == 0
        denied(
            lambda: (
                member.client.table("build_reviews")
                .update({"version": 99})
                .eq("id", build)
                .execute()
            )
        )
        denied(lambda: member.save_build_review(dict(params, p_version=1)))
        review = {
            "p_id": decision,
            "p_build": build,
            "p_version": 1,
            "p_decision": "approved",
            "p_note": "Synthetic acceptance: inspected the diff and actual assertion result.",
        }
        assert member.decide_build_review(review) == decision
        assert member.decide_build_review(review) == decision
        assert len(owner.build_review_decisions(build)) == 1
        denied(
            lambda: member.decide_build_review(
                dict(review, p_id=str(uuid4()), p_build=private_build)
            )
        )
        report["peer_review_private_isolation_direct_write_denial"] = "passed"
        print("Checking stale versions, changed sources and withdrawal…", flush=True)
        changed = dict(value, acceptance_criteria=["Sum remains correct."])
        assert owner.save_build_review(dict(params, p_version=1, p_evidence=changed)) == 2
        denied(lambda: member.decide_build_review(dict(review, p_id=str(uuid4()))), "PT409")
        owner.rpc(
            "chat_action",
            {
                "p_action": "edit",
                "p_data": {
                    "message": source,
                    "body": "M16 synthetic acceptance: subtraction now required.",
                },
            },
        )
        assert member.build_reviews(workspace)["items"][0]["current"] is False
        denied(
            lambda: member.decide_build_review(dict(review, p_id=str(uuid4()), p_version=2)),
            "PT409",
        )
        denied(lambda: owner.save_build_review(dict(params, p_version=2)), "PT409")
        owner.rpc("remove_member", {"p_workspace": workspace, "p_user": str(member.user.id)})
        joined = False
        assert len(owner.build_reviews(workspace)["items"]) == 2
        denied(lambda: member.build_reviews(workspace))
        assert member.build_review_decisions(build) == []
        assert (
            member.client.table("build_reviews")
            .select("id")
            .eq("workspace_id", workspace)
            .execute()
            .data
            == []
        )
        report["revocation_with_evidence_still_present"] = "passed"
        invite = owner.rpc(
            "create_invitation",
            {"p_workspace": workspace, "p_email": member.user.email, "p_role": "member"},
        )
        member.rpc("accept_invitation", {"p_token": invite})
        joined = True
        owner.rpc("unsend_message", {"p_message": source})
        assert owner.build_reviews(workspace)["items"] == []
        assert member.build_review_decisions(build) == []
        report["version_conflicts_source_staleness_withdrawal_cleanup"] = "passed"
    finally:
        if joined:
            owner.rpc("remove_member", {"p_workspace": workspace, "p_user": str(member.user.id)})
    assert (
        member.client.table("build_reviews")
        .select("id")
        .eq("workspace_id", workspace)
        .execute()
        .data
        == []
    )
    report["membership_revocation"] = "passed"
    report["real_github_pr"] = "deferred external acceptance; no publication performed"
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
        stage = "hosted build review acceptance"
        probe(*accounts, report)
        print(
            "PASS hosted build reviews, real local evidence, peer decisions "
            "and two-account privacy.",
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
            error_code=getattr(error, "code", None),
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
