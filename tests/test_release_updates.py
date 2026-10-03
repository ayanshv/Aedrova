"""Read-only checks never accept preview, mismatched or malformed releases."""

import pytest

from aedrova.delivery.releases import check_release, validate_release, version_tuple


def release(**changes):
    return {
        "version": "0.1.1",
        "public_release": True,
        "architecture": "arm64",
        "minimum_macos": "14.0",
        "sha256": "a" * 64,
        **changes,
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"public_release": False},
        {"version": "javascript:alert(1)"},
        {"architecture": "x86_64"},
        {"sha256": "bad"},
        {"minimum_macos": ""},
    ],
)
def test_invalid_release_rejected(changes):
    with pytest.raises(ValueError):
        validate_release(release(**changes), machine="arm64", macos="15.0")


def test_version_comparison_and_mac_compatibility():
    assert version_tuple("0.1.10") > version_tuple("0.1.2")
    assert validate_release(release(), machine="arm64", macos="14.0")["version"] == "0.1.1"
    with pytest.raises(ValueError, match="newer macOS"):
        validate_release(release(), machine="arm64", macos="13.6")


def test_untrusted_update_origins_do_not_make_network_requests():
    with pytest.raises(ValueError, match="verified"):
        check_release("http://untrusted.example")


@pytest.mark.parametrize("value", [[], None, "invalid", 7])
def test_invalid_metadata_shape(value):
    with pytest.raises(ValueError, match="invalid"):
        validate_release(value)


@pytest.mark.parametrize(
    "origin",
    [
        "https://user:secret@example.com",
        "https://example.com/path",
        "https://example.com?token=secret",
        "https:///",
    ],
)
def test_update_origin_cannot_contain_credentials_or_paths(origin):
    with pytest.raises(ValueError, match="verified"):
        check_release(origin)
