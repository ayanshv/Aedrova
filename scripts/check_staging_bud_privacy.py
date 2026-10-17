"""Live two-account Bud privacy acceptance in a disposable staging workspace.

Uses ordinary Google OAuth, no admin/provider keys, AI inference or connector grants.
Creates only synthetic messages; soft-removes its Bud and archives its workspace.
Tokens stay in memory and reports contain check names only. Never run in production.
"""

import argparse
import json
from pathlib import Path
from uuid import uuid4

from postgrest.exceptions import APIError
from run_staging import validate

from aedrova.identity.oauth import google_sign_in
from aedrova.identity.service import Connection, IdentityService


class AccountChooser(IdentityService):
    def google_authorization_url(self, redirect):
        return self.client.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {
                    "redirect_to": redirect,
                    "scopes": "openid email profile",
                    "query_params": {"prompt": "select_account"},
                },
            }
        ).url


def expect_denied(operation):
    try:
        operation()
    except APIError as error:
        if error.code == "42501":
            return
        raise AssertionError("Expected authorization rejection, not another failure") from None
    raise AssertionError("Private operation was accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    config = validate(json.loads(args.config.read_text()))
    report = {"environment": "staging", "status": "running", "checks": {}}
    accounts, workspace, bud, member = [], None, None, None

    def record(name):
        report["checks"][name] = "passed"
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))
        print("PASS " + name, flush=True)

    try:
        owner = AccountChooser(
            Connection(config["supabase_url"], config["supabase_publishable_key"])
        )
        accounts.append(owner)
        print("FIRST_ACCOUNT_REQUIRED", flush=True)
        google_sign_in(owner, timeout=900)
        workspace = owner.rpc(
            "create_workspace", {"p_name": "Bud privacy acceptance " + uuid4().hex[:6]}
        )
        bud = owner.save_bud(
            {
                "p_id": None,
                "p_workspace": workspace,
                "p_version": 0,
                "p_provider": "github",
                "p_resource": "aedrova-fixtures/never-connected",
                "p_name": "Privacy Probe",
                "p_color": "#4388F5",
                "p_shape": "round",
                "p_role": "Builder",
                "p_instructions": "Disposable acceptance fixture.",
                "p_appearance": "builder",
            }
        )
        channel_rows = (
            owner.client.table("channels").select("id").eq("workspace_id", workspace).execute().data
        )
        channels = [r["id"] for r in channel_rows]
        before = (
            owner.client.table("messages").select("id").in_("channel_id", channels).execute().data
        )
        message = {
            "p_id": str(uuid4()),
            "p_bud": bud["id"],
            "p_body": "Synthetic private owner message",
        }
        owner.rpc("append_bud_message", message)
        owner.rpc("append_bud_message", message)
        history = owner.rpc("bud_conversation", {"p_bud": bud["id"]})
        assert len(history) == 1 and history[0]["id"] == message["p_id"]
        record("owner_history_and_idempotent_retry")
        other = AccountChooser(
            Connection(config["supabase_url"], config["supabase_publishable_key"])
        )
        accounts.append(other)
        print("SECOND_DISTINCT_ACCOUNT_REQUIRED", flush=True)
        google_sign_in(other, timeout=900)
        assert owner.user.id != other.user.id, "Two distinct staging accounts required"
        record("distinct_authenticated_accounts")
        expect_denied(lambda: other.rpc("bud_conversation", {"p_bud": bud["id"]}))
        expect_denied(
            lambda: other.rpc(
                "append_bud_message",
                {
                    "p_id": str(uuid4()),
                    "p_bud": bud["id"],
                    "p_body": "Must be denied",
                },
            )
        )
        record("outsider_history_and_write_denied")
        invitation = owner.rpc(
            "create_invitation",
            {
                "p_workspace": workspace,
                "p_email": other.user.email,
                "p_role": "member",
            },
        )
        other.rpc("accept_invitation", {"p_token": invitation})
        member = str(other.user.id)
        assert other.rpc("bud_conversation", {"p_bud": bud["id"]}) == []
        assert (
            other.client.table("bud_messages").select("id").eq("id", message["p_id"]).execute().data
            == []
        )
        expect_denied(
            lambda: other.rpc(
                "append_bud_message",
                {
                    "p_id": str(uuid4()),
                    "p_bud": bud["id"],
                    "p_body": "Must be denied",
                    "p_reply_to": message["p_id"],
                },
            )
        )
        record("same_workspace_private_history_and_reply_isolated")
        other_message = {
            "p_id": str(uuid4()),
            "p_bud": bud["id"],
            "p_body": "Synthetic private member message",
        }
        other.rpc("append_bud_message", other_message)
        assert len(other.rpc("bud_conversation", {"p_bud": bud["id"]})) == 1
        assert (
            owner.client.table("bud_messages")
            .select("id")
            .eq("id", other_message["p_id"])
            .execute()
            .data
            == []
        )
        assert len(owner.rpc("bud_conversation", {"p_bud": bud["id"]})) == 1
        record("member_own_history_and_reverse_isolation")
        after = (
            owner.client.table("messages").select("id").in_("channel_id", channels).execute().data
        )
        assert sorted(row["id"] for row in before) == sorted(row["id"] for row in after)
        record("no_private_messages_in_shared_channels")
        owner.rpc("remove_member", {"p_workspace": workspace, "p_user": member})
        member = None
        expect_denied(lambda: other.rpc("bud_conversation", {"p_bud": bud["id"]}))
        record("removed_member_history_denied")
        report["status"] = "passed"
    except Exception as error:
        report["status"], report["error_type"] = "incomplete", type(error).__name__
        print("INCOMPLETE " + type(error).__name__ + "; no credentials logged.", flush=True)
    finally:
        if workspace and accounts[0].user:
            try:
                if member:
                    accounts[0].rpc("remove_member", {"p_workspace": workspace, "p_user": member})
                if bud:
                    accounts[0].remove_dot(bud["id"], workspace, bud["version"])
                accounts[0].rpc(
                    "set_workspace_archived", {"p_workspace": workspace, "p_archived": True}
                )
                record("synthetic_bud_soft_removed_and_workspace_archived")
            except Exception as error:
                report["cleanup_error_type"] = type(error).__name__
                report["status"] = "incomplete"
        for account in accounts:
            if account.user:
                try:
                    account.sign_out()
                except Exception as error:
                    report["signout_error_type"] = type(error).__name__
                    report["status"] = "incomplete"
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
