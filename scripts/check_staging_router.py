"""Staging-only authenticated routing acceptance; no inference or provider spending."""

import json
from pathlib import Path
from uuid import uuid4

from run_staging import validate

from aedrova.agents.managed import ManagedClient
from aedrova.identity.oauth import google_sign_in
from aedrova.identity.service import Connection, IdentityService


def main():
    root = Path(__file__).resolve().parents[1]
    config = validate(json.loads((root / "work/staging/public-config.json").read_text()))
    service = IdentityService(
        Connection(config["supabase_url"], config["supabase_publishable_key"])
    )
    report = {"environment": "staging", "checks": {}, "status": "incomplete"}
    workspace = None
    try:
        print("STAGING_GOOGLE_SIGN_IN_REQUIRED", flush=True)
        google_sign_in(service, timeout=900)
        workspace = service.rpc(
            "create_workspace", {"p_name": "Router acceptance " + uuid4().hex[:6]}
        )
        service.rpc(
            "set_agent_preferences",
            {"p_workspace": workspace, "p_nickname": "Aedrova", "p_provider": "auto"},
        )
        rows = (
            service.client.table("workspace_agent_preferences")
            .select("provider")
            .eq("workspace_id", workspace)
            .execute()
            .data
        )
        assert rows and rows[0]["provider"] == "auto"
        report["checks"]["migration_and_authorized_auto_save"] = "passed"
        token = service.client.auth.get_session().access_token
        balance = ManagedClient(config["managed_origin"], token).balance(workspace)
        assert isinstance(balance.get("coding_providers"), list)
        report["checks"]["authenticated_managed_preflight"] = "passed"
        report["checks"]["provider_count"] = len(balance["coding_providers"])
        report["checks"]["credit_available"] = bool(balance.get("available", 0) > 0)
        report["status"] = "passed"
        print("PASS migration and authenticated preflight (no inference)", flush=True)
    except Exception as error:
        report["error_type"] = type(error).__name__
        print("Acceptance incomplete: " + type(error).__name__, flush=True)
    finally:
        if workspace:
            try:
                service.rpc(
                    "set_workspace_archived", {"p_workspace": workspace, "p_archived": True}
                )
            except Exception:
                report["cleanup"] = "archive_required"
        if service.user:
            service.sign_out()
        (root / "work/staging/router-acceptance.json").write_text(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
