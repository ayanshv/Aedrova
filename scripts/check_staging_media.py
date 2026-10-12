"""Real OAuth and synthetic private media acceptance, restricted to staging.

Run with the public staging profile. Tokens remain in memory. The second OAuth
login must use a distinct test account. No audio capture or AI calls are made.
"""

import argparse
import json
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from run_staging import validate

from aedrova.identity.oauth import google_sign_in
from aedrova.identity.service import Connection, IdentityService


class SecondAccount(IdentityService):
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


def denied(operation):
    try:
        operation()
    except PermissionError:
        return
    raise AssertionError("Private attachment access was not denied")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    config = validate(json.loads(args.config.read_text()))
    os.environ["AEDROVA_MANAGED_ORIGIN"] = config["managed_origin"]
    report = {"environment": "staging", "checks": {}, "status": "running"}
    accounts, messages = [], []
    workspace = None

    def record(name):
        report["checks"][name] = "passed"
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))
        print("PASS " + name, flush=True)

    try:
        owner = IdentityService(
            Connection(config["supabase_url"], config["supabase_publishable_key"])
        )
        accounts.append(owner)
        print("Sign in to the first staging test account.", flush=True)
        google_sign_in(owner, timeout=900)
        workspace = owner.rpc("create_workspace", {"p_name": "Media acceptance " + uuid4().hex[:6]})
        channel = owner.rpc(
            "create_channel",
            {"p_workspace": workspace, "p_name": "private-media", "p_private": True},
        )
        parent = str(uuid4())
        owner.rpc("send_message", {"p_id": parent, "p_channel": channel, "p_body": "Media probe"})
        messages.append(parent)
        with tempfile.TemporaryDirectory(prefix="aedrova-staging-probe-") as directory:
            path = Path(directory) / "synthetic.txt"
            data = b"Non-sensitive staging media acceptance fixture.\n"
            path.write_bytes(data)
            identifier = str(uuid4())
            message = owner.upload_attachment(identifier, channel, path, parent=parent)
            messages.append(message)
            rows = (
                owner.client.table("messages").select("parent_id").eq("id", message).execute().data
            )
            assert rows == [{"parent_id": parent}]
            assert owner.download_attachment(identifier) == data
            record("private_channel_thread_publication_and_verified_download")
            for cancel_at in (2, 3):
                checks = [0]

                def cancelled(checks=checks, cancel_at=cancel_at):
                    checks[0] += 1
                    return checks[0] == cancel_at

                abandoned = str(uuid4())
                result = owner.upload_attachment(abandoned, channel, path, cancelled=cancelled)
                assert result is None
                assert (
                    not owner.client.table("attachments")
                    .select("id")
                    .eq("id", abandoned)
                    .execute()
                    .data
                )
                record("cancel_" + ("after_reservation" if cancel_at == 2 else "after_storage"))
        print("SECOND_ACCOUNT_REQUIRED: use a DIFFERENT staging Google test account.", flush=True)
        other = SecondAccount(
            Connection(config["supabase_url"], config["supabase_publishable_key"])
        )
        accounts.append(other)
        google_sign_in(other, timeout=900)
        assert owner.user.id != other.user.id, "Distinct test accounts required"
        denied(lambda: other.download_attachment(identifier))
        record("foreign_workspace_attachment_denied")
        invitation = owner.rpc(
            "create_invitation",
            {"p_workspace": workspace, "p_email": other.user.email, "p_role": "member"},
        )
        other.rpc("accept_invitation", {"p_token": invitation})
        denied(lambda: other.download_attachment(identifier))
        record("workspace_member_private_channel_attachment_denied")
        owner.rpc("remove_member", {"p_workspace": workspace, "p_user": str(other.user.id)})
        record("test_member_removed")
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "incomplete"
        report["error_type"] = type(error).__name__
        print("INCOMPLETE " + type(error).__name__ + "; no credentials logged.", flush=True)
    finally:
        if workspace and accounts[0].user:
            try:
                for message in reversed(messages):
                    accounts[0].rpc("unsend_message", {"p_message": message})
                accounts[0].rpc(
                    "set_workspace_archived", {"p_workspace": workspace, "p_archived": True}
                )
                record("synthetic_messages_unsent_workspace_archived")
            except Exception as error:
                report["cleanup_error_type"] = type(error).__name__
        for account in accounts:
            if account.user:
                try:
                    account.sign_out()
                    denied(lambda account=account: account.download_attachment(str(uuid4())))
                    record("signed_out_session_media_denied")
                except Exception as error:
                    report["signout_error_type"] = type(error).__name__
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
