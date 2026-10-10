"""Normal OAuth, synthetic teammate CRUD/RLS checks; never stores credentials."""

import json
import traceback
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from check_hosted_build_reviews import denied

from aedrova.identity.oauth import google_sign_in
from aedrova.identity.service import Connection, IdentityService

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "work/m17f1/hosted-teammate-check.json"


def probe(owner, member, report):
    assert owner.user.id != member.user.id
    workspace = owner.rpc(
        "onboard_workspace",
        {
            "p_name": "AI teammate validation " + uuid4().hex[:6],
            "p_nickname": "Aedrova",
            "p_provider": "codex",
        },
    )
    report["workspace"] = workspace
    identifier = str(uuid4())
    config = {
        "name": "Pixel",
        "role": "research",
        "shape": "round",
        "color": "#4388F5",
        "personality": "concise",
        "reporting": "quiet",
        "effort": "quick",
        "importance": "normal",
        "responsibilities": "Summarize synthetic approved requirements.",
    }
    params = {"p_id": identifier, "p_workspace": workspace, "p_version": 0, "p_config": config}
    joined = False
    version = 0
    try:
        assert owner.save_ai_teammate(params) == 1
        version = 1
        assert owner.save_ai_teammate(params) == 1
        assert owner.ai_teammates(workspace)["items"][0]["config"] == config
        assert member.ai_teammates(workspace)["items"] == []
        denied(lambda: member.save_ai_teammate(params))
        report["persistence_retry_outsider_isolation"] = "passed"
        denied(lambda: owner.save_ai_teammate(dict(params, p_id=str(uuid4()))), "23505")
        denied(
            lambda: owner.rpc(
                "set_agent_preferences",
                {"p_workspace": workspace, "p_nickname": "pixel", "p_provider": "codex"},
            ),
            "22023",
        )
        report["unique_actor_names"] = "passed"
        invite = owner.rpc(
            "create_invitation",
            {"p_workspace": workspace, "p_email": member.user.email, "p_role": "member"},
        )
        member.rpc("accept_invitation", {"p_token": invite})
        joined = True
        assert member.ai_teammates(workspace)["items"][0]["id"] == identifier
        denied(lambda: member.save_ai_teammate(dict(params, p_version=1)))
        denied(lambda: member.remove_ai_teammate(identifier, 1))
        denied(
            lambda: (
                member.client.table("ai_teammates")
                .update({"paused": True})
                .eq("id", identifier)
                .execute()
            )
        )
        report["member_reads_owner_admin_writes_only"] = "passed"
        assert owner.save_ai_teammate(dict(params, p_version=1, p_paused=True)) == 2
        version = 2
        assert member.ai_teammates(workspace)["items"][0]["paused"]
        denied(lambda: owner.save_ai_teammate(dict(params, p_version=1)), "PT409")
        renamed = deepcopy(config)
        renamed["name"] = "Orbit"
        assert (
            owner.save_ai_teammate(dict(params, p_version=2, p_config=renamed, p_paused=False)) == 3
        )
        version = 3
        live = member.ai_teammates(workspace)["items"][0]
        assert live["id"] == identifier and live["version"] == 3 and not live["paused"]
        assert live["config"]["name"] == "Orbit"
        from aedrova.teammates.model import resolve

        assert resolve(f"<@ai:{identifier}|Pixel> summarize", [live]) == (live, "summarize")
        report["pause_stale_edit_rename_stable_mentions"] = "passed"
        owner.rpc("remove_member", {"p_workspace": workspace, "p_user": str(member.user.id)})
        joined = False
        assert member.ai_teammates(workspace)["items"] == []
        assert owner.ai_teammates(workspace)["items"][0]["id"] == identifier
        denied(lambda: member.save_ai_teammate(dict(params, p_version=3)))
        report["revocation_while_profile_exists"] = "passed"
        owner.remove_ai_teammate(identifier, version)
        version = 0
        assert owner.ai_teammates(workspace)["items"] == []
        denied(lambda: owner.save_ai_teammate(params))
        report["deletion_no_identity_resurrection"] = "passed"
        report["status"] = "passed"
    finally:
        if joined:
            owner.rpc("remove_member", {"p_workspace": workspace, "p_user": str(member.user.id)})
        if version:
            owner.remove_ai_teammate(identifier, version)


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
        stage = "hosted teammate acceptance"
        probe(*accounts, report)
        print(
            "PASS hosted teammate persistence, lifecycle and two-account privacy.",
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
