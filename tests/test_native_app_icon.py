"""Do not replace the system-selected adaptive Dock icon with Qt's static ICNS."""

import pytest

from aedrova.desktop import brand


@pytest.mark.parametrize("platform", ["darwin", "win32", "linux"])
def test_only_native_macos_catalog_defers_to_system(tmp_path, monkeypatch, qtbot, platform):
    contents = tmp_path / "Aedrova.app/Contents"
    resources = contents / "Resources"
    resources.mkdir(parents=True)
    monkeypatch.setattr(brand.sys, "platform", platform)
    monkeypatch.setattr(brand.sys, "executable", str(contents / "MacOS/Aedrova"))
    assert not brand.app_icon().isNull()  # Missing catalog retains the legacy icon.
    (resources / "Assets.car").write_bytes(b"fixture")
    assert brand.app_icon().isNull() == (platform == "darwin")
