"""Sculpted assets are packaged locally and usable across every Bud surface."""

from pathlib import Path

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter

from aedrova.desktop.bud_art import LOOKS, appearance, paint_bud, sprite
from aedrova.desktop.dots import shelf_rows


def test_all_six_assets_are_distinct_transparent_and_drawable(qapp):
    keys = []
    for look in LOOKS:
        art = sprite(look)
        assert not art.isNull()
        assert art.toImage().pixelColor(0, 0).alpha() == 0
        keys.append(art.cacheKey())
        frame = QImage(100, 100, QImage.Format.Format_ARGB32)
        frame.fill(0)
        painter = QPainter(frame)
        assert paint_bud(painter, QRectF(0, 0, 100, 100), {"appearance": look})
        painter.end()
        assert any(frame.pixelColor(x, y).alpha() for x in range(100) for y in range(100))
    assert len(set(keys)) == 6
    script = Path("scripts/package_desktop.py").read_text()
    assert "assets/buds" in script


def test_identity_survives_shelf_and_custom_color_cache(qapp):
    row = dict(name="Orbit", role="Finance", appearance="research", color="#8844AA", shape="round")
    config = shelf_rows([row])[0]["config"]
    assert appearance(config) == "research"  # Job does not override a chosen look.
    assert appearance({"role": "Revenue analyst"}) == "finance"
    assert appearance({"shape": "squircle"}) == "designer"
    assert sprite("research", "#8844AA").cacheKey() == sprite("research", "#8844AA").cacheKey()


def test_appearance_rpc_retains_full_configuration():
    from unittest.mock import Mock

    from aedrova.identity.service import IdentityService

    s = IdentityService.__new__(IdentityService)
    s._authenticated = Mock()
    s.client = Mock()
    params = {"p_appearance": "marketing", "p_role": "Launch updates"}
    s.save_bud(params)
    s.client.rpc.assert_called_once_with("save_workspace_bud_appearance", params)
