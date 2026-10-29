"""Two-account staging acceptance with synthetic data and no paid inference.

Reuses the same two in-memory Google sessions for connector readiness, model
preflight, verified uploads and private Bud history. Does not grant connector
access, initiate checkout, record audio or enable meetings. Not a launch approval.
"""

import argparse
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from check_staging_bud_privacy import AccountChooser, expect_denied
from check_staging_media import denied
from run_staging import validate

from aedrova.agents.managed import ManagedClient
from aedrova.identity.oauth import google_sign_in
from aedrova.identity.service import Connection


def check_bud_capacity(owner, workspace, created, record):
    capacity = owner.bud_capacity(workspace)
    assert capacity and capacity["plan"] == "free" and capacity["limit"] == 1
    assert capacity["used"] == 0 and capacity["remaining"] == 1
    record("hosted_bud_capacity_rpc_free_default")
    forks = [owner.fork_for_context(), owner.fork_for_context()]
    barrier = Barrier(2)

    def create(index):
        from postgrest.exceptions import APIError

        service = forks[index]
        try:
            barrier.wait(timeout=15)
            return service.save_bud(
                {
                    "p_id": None,
                    "p_workspace": workspace,
                    "p_version": 0,
                    "p_provider": "github",
                    "p_resource": "acceptance/cap-" + str(index),
                    "p_name": "Capacity " + str(index),
                    "p_color": "#4388F5",
                    "p_shape": "round",
                    "p_role": "Builder",
                    "p_instructions": "",
                    "p_appearance": "builder",
                }
            )
        except APIError as error:
            if error.code == "54000":
                return None
            raise
        finally:
            service.close_context()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(create, i) for i in range(2)]
        for future in futures:
            value = future.result()
            if value:
                created.append(value)
    assert len(created) == 1, "Concurrent creation exceeded capacity"
    assert owner.bud_capacity(workspace)["used"] == 1
    record("hosted_concurrent_bud_creation_one_slot_only")
    for row in created:
        owner.remove_dot(row["id"], workspace, row["version"])
    created.clear()
    assert owner.bud_capacity(workspace)["remaining"] == 1
    record("hosted_bud_deletion_frees_capacity")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    config = validate(json.loads(args.config.read_text()))
    os.environ["AEDROVA_MANAGED_ORIGIN"] = config["managed_origin"]
    report = {
        "environment": "staging",
        "started_at": datetime.now(UTC).isoformat(),
        "status": "awaiting_first_sign_in",
        "checks": {},
        "limitations": [
            "No actual inference or provider spending",
            "Connector configuration is not a fresh OAuth grant/resource-read test",
            "No microphone, camera, two-device meeting or native onboarding test",
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    accounts, workspace, bud, member = [], None, None, None
    capacity_buds, original_profiles = [], []
    messages = []

    def save():
        args.report.write_text(json.dumps(report, indent=2))

    def record(name):
        report["checks"][name] = "passed"
        save()
        print("PASS " + name, flush=True)

    save()
    try:
        owner = AccountChooser(
            Connection(config["supabase_url"], config["supabase_publishable_key"])
        )
        accounts.append(owner)
        print("FIRST_ACCOUNT_REQUIRED: sign into the primary staging test account.", flush=True)
        google_sign_in(owner, timeout=900)
        report["status"] = "running_owner_checks"
        save()
        token = owner.client.auth.get_session().access_token
        client = ManagedClient(config["managed_origin"], token)
        catalog = client.request("/api/buds/connectors", timeout=90)
        report["connector_configuration"] = [
            {
                "id": item.get("id", item.get("key", item.get("provider", "unknown"))),
                "available": bool(item.get("available")),
                "oauth_available": bool(item.get("oauth_available")),
                "oauth_supported": bool(item.get("oauth_supported")),
                "managed_available": bool(item.get("managed_available")),
            }
            for item in catalog["providers"]
        ]
        record("authenticated_connector_catalog")
        workspace = owner.rpc("create_workspace", {"p_name": "Acceptance " + uuid4().hex[:6]})
        check_bud_capacity(owner, workspace, capacity_buds, record)
        owner.rpc(
            "set_agent_preferences",
            {"p_workspace": workspace, "p_nickname": "Aedrova", "p_provider": "auto"},
        )
        rows = (
            owner.client.table("workspace_agent_preferences")
            .select("provider")
            .eq("workspace_id", workspace)
            .execute()
            .data
        )
        assert rows == [{"provider": "auto"}]
        record("hosted_auto_preference_save_and_readback")
        balance = client.balance(workspace)
        report["new_workspace_ai_status"] = balance.get("status")
        report["new_workspace_ai_funded"] = bool(balance.get("available", 0) > 0)
        for row in owner.client.table("workspaces").select("id").limit(20).execute().data:
            candidate = client.balance(row["id"])
            if isinstance(candidate.get("coding_providers"), list):
                report["managed_provider_count"] = len(candidate["coding_providers"])
                report["managed_credit_available"] = bool(candidate.get("available", 0) > 0)
                record("authenticated_provider_preflight")
                break
        channel = owner.rpc(
            "create_channel",
            {"p_workspace": workspace, "p_name": "private-probe", "p_private": True},
        )
        parent, attachment = str(uuid4()), str(uuid4())
        owner.rpc(
            "send_message", {"p_id": parent, "p_channel": channel, "p_body": "Synthetic acceptance"}
        )
        messages.append(parent)
        with tempfile.TemporaryDirectory(prefix="aedrova-acceptance-") as directory:
            path = Path(directory) / "synthetic.txt"
            payload = b"Synthetic staging acceptance; no customer data.\n"
            path.write_bytes(payload)
            messages.append(owner.upload_attachment(attachment, channel, path, parent=parent))
            assert owner.download_attachment(attachment) == payload
            record("server_verified_private_upload_and_download")
            for cancel_at in (2, 3):
                calls = [0]

                def cancelled(calls=calls, cancel_at=cancel_at):
                    calls[0] += 1
                    return calls[0] == cancel_at

                abandoned = str(uuid4())
                assert (
                    owner.upload_attachment(abandoned, channel, path, cancelled=cancelled) is None
                )
                assert (
                    not owner.client.table("attachments")
                    .select("id")
                    .eq("id", abandoned)
                    .execute()
                    .data
                )
                record("upload_cancellation_boundary_" + str(cancel_at))
        bud = owner.save_bud(
            {
                "p_id": None,
                "p_workspace": workspace,
                "p_version": 0,
                "p_provider": "github",
                "p_resource": "aedrova-fixtures/not-connected",
                "p_name": "Privacy Probe",
                "p_color": "#4388F5",
                "p_shape": "round",
                "p_role": "Builder",
                "p_instructions": "Synthetic acceptance only.",
                "p_appearance": "builder",
            }
        )
        message = {"p_id": str(uuid4()), "p_bud": bud["id"], "p_body": "Synthetic owner message"}
        owner.rpc("append_bud_message", message)
        owner.rpc("append_bud_message", message)
        assert len(owner.rpc("bud_conversation", {"p_bud": bud["id"]})) == 1
        record("owner_bud_history_and_retry_idempotency")
        other = AccountChooser(
            Connection(config["supabase_url"], config["supabase_publishable_key"])
        )
        accounts.append(other)
        report["status"] = "awaiting_second_sign_in"
        save()
        print(
            "SECOND_ACCOUNT_REQUIRED: select a DIFFERENT registered staging test account.",
            flush=True,
        )
        google_sign_in(other, timeout=900)
        assert owner.user.id != other.user.id, "Distinct staging accounts required"
        record("distinct_authenticated_accounts")
        denied(lambda: other.download_attachment(attachment))
        expect_denied(lambda: other.rpc("bud_conversation", {"p_bud": bud["id"]}))
        record("foreign_workspace_file_and_bud_denied")
        invitation = owner.rpc(
            "create_invitation",
            {"p_workspace": workspace, "p_email": other.user.email, "p_role": "member"},
        )
        other.rpc("accept_invitation", {"p_token": invitation})
        member = str(other.user.id)
        for account in (owner, other):
            profile = account.my_profile()
            original_profiles.append((account, profile))
        owner.rpc(
            "chat_action",
            {"p_action": "profile", "p_data": {"status": "Acceptance", "availability": "online"}},
        )
        other.rpc(
            "chat_action",
            {"p_action": "profile", "p_data": {"status": "Acceptance", "availability": "away"}},
        )
        people = owner.chat_inventory(workspace, section="people")["people"]
        assert next(p for p in people if p["user_id"] == member)["availability"] == "away"
        record("hosted_owner_sees_teammate_away")
        people = other.chat_inventory(workspace, section="people")["people"]
        assert (
            next(p for p in people if p["user_id"] == str(owner.user.id))["availability"]
            == "online"
        )
        record("hosted_teammate_sees_owner_online")
        owner.rpc(
            "chat_action",
            {"p_action": "profile", "p_data": {"status": "Acceptance", "availability": "busy"}},
        )
        people = other.chat_inventory(workspace, section="people")["people"]
        assert (
            next(p for p in people if p["user_id"] == str(owner.user.id))["availability"] == "busy"
        )
        record("hosted_teammate_sees_do_not_disturb")
        denied(lambda: other.download_attachment(attachment))
        assert other.rpc("bud_conversation", {"p_bud": bud["id"]}) == []
        expect_denied(
            lambda: other.rpc(
                "append_bud_message",
                {
                    "p_id": str(uuid4()),
                    "p_bud": bud["id"],
                    "p_body": "Denied reply",
                    "p_reply_to": message["p_id"],
                },
            )
        )
        record("member_private_file_history_and_reply_isolated")
        other.rpc(
            "append_bud_message",
            {"p_id": str(uuid4()), "p_bud": bud["id"], "p_body": "Synthetic member message"},
        )
        assert len(other.rpc("bud_conversation", {"p_bud": bud["id"]})) == 1
        assert len(owner.rpc("bud_conversation", {"p_bud": bud["id"]})) == 1
        record("private_bud_history_isolated_both_directions")
        owner.rpc("remove_member", {"p_workspace": workspace, "p_user": member})
        member = None
        expect_denied(lambda: other.rpc("bud_conversation", {"p_bud": bud["id"]}))
        denied(lambda: other.download_attachment(attachment))
        record("revoked_member_file_and_bud_denied")
        report["status"] = "automated_authenticated_checks_passed"
    except Exception as error:
        report["status"] = "incomplete"
        report["error_type"] = type(error).__name__
        print("INCOMPLETE " + type(error).__name__ + "; no credentials logged.", flush=True)
    finally:
        for account, profile in original_profiles:
            try:
                account.rpc(
                    "chat_action",
                    {
                        "p_action": "profile",
                        "p_data": {
                            "status": profile.get("status", ""),
                            "availability": profile.get("availability", "online"),
                        },
                    },
                )
            except Exception as error:
                report["profile_restore_error_type"] = type(error).__name__
                report["status"] = "incomplete"
        if workspace and accounts[0].user:
            try:
                for row in capacity_buds:
                    accounts[0].remove_dot(row["id"], workspace, row["version"])
                if member:
                    accounts[0].rpc("remove_member", {"p_workspace": workspace, "p_user": member})
                for identifier in reversed(messages):
                    if identifier:
                        accounts[0].rpc("unsend_message", {"p_message": identifier})
                if bud:
                    accounts[0].remove_dot(bud["id"], workspace, bud["version"])
                accounts[0].rpc(
                    "set_workspace_archived", {"p_workspace": workspace, "p_archived": True}
                )
                record("synthetic_fixtures_removed_workspace_archived")
            except Exception as error:
                report["cleanup_error_type"] = type(error).__name__
                report["status"] = "incomplete"
        for account in accounts:
            if account.user:
                try:
                    account.sign_out()
                    denied(lambda account=account: account.download_attachment(str(uuid4())))
                except Exception as error:
                    report["signout_error_type"] = type(error).__name__
                    report["status"] = "incomplete"
        save()
    return 0 if report["status"] == "automated_authenticated_checks_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
