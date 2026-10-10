"""Baseline release gate catches credential formats without printing values."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "release_check", ROOT / "scripts/check_release_secrets.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_release_scan_flags_environment_and_secret_without_disclosing_value(tmp_path):
    path = tmp_path / ".env.production"
    secret = "GOCSPX-" + "a" * 30
    path.write_text(secret)
    findings = module.inspect_paths([path])
    assert (str(path), "environment-file") in findings
    assert (str(path), "google-client-secret") in findings
    assert secret not in str(findings)


def test_publishable_configuration_is_not_a_secret(tmp_path):
    path = tmp_path / "public-config.json"
    path.write_text('{"supabase_publishable_key": "sb_publishable_example1234567890"}')
    assert module.inspect_paths([path]) == []


def test_legacy_service_role_jwt_is_rejected(tmp_path):
    import base64
    import json

    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').decode().rstrip("=")
    payload = (
        base64.urlsafe_b64encode(json.dumps({"role": "service_role"}).encode()).decode().rstrip("=")
    )
    path = tmp_path / "public-config.json"
    path.write_text(header + "." + payload + ".signature")
    assert (str(path), "supabase-service-role-jwt") in module.inspect_paths([path])
