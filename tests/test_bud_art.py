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
    assert appearance(config) == "research"
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


def test_blink_closes_eyes_without_squashing_body(qapp):
    from aedrova.desktop.bud_art import blinking_sprite

    for look in LOOKS:
        open_eye, closed_eye = sprite(look).toImage(), blinking_sprite(look).toImage()
        assert open_eye != closed_eye
        assert open_eye.size() == closed_eye.size()
        assert open_eye.pixelColor(100, 100) == closed_eye.pixelColor(100, 100)


def test_custom_colors_keep_full_resolution_and_exact_edge_opacity(qapp):
    from aedrova.desktop.bud_art import atlas_image

    atlas = atlas_image()
    for index, look in enumerate(LOOKS):
        width, height = atlas.width() // 3, atlas.height() // 2
        source = atlas.copy(index % 3 * width, index // 3 * height, width, height)
        recolored = sprite(look, "#ED5749").toImage()
        assert recolored.size() == source.size()
        source_rgba = source.convertToFormat(QImage.Format.Format_RGBA8888)
        tinted_rgba = recolored.convertToFormat(QImage.Format.Format_RGBA8888)
        source_alpha = bytes(source_rgba.constBits())[3::4]
        tinted_alpha = bytes(tinted_rgba.constBits())[3::4]
        assert source_alpha == tinted_alpha


def test_extreme_colors_retain_shading_and_protect_accessories(qapp):
    source = sprite("builder").toImage()
    for color in ("#000000", "#FFFFFF"):
        tinted = sprite("builder", color).toImage()
        shades = {tinted.pixelColor(x, 430).red() for x in range(120, 420)}
        assert len(shades) > 12
        assert tinted.pixelColor(260, 150) == source.pixelColor(260, 150)
        assert tinted.pixelColor(270, 340) == source.pixelColor(270, 340)
    from aedrova.desktop.bud_art import BASE_COLORS

    designer = sprite("designer").toImage()
    custom_designer = sprite("designer", "#ED5749").toImage()
    assert designer.pixelColor(443, 150) == custom_designer.pixelColor(443, 150)
    original_research = sprite("research", BASE_COLORS[LOOKS.index("research")]).toImage()
    custom_research = sprite("research", "#ED5749").toImage()
    assert custom_research.pixelColor(365, 174) == original_research.pixelColor(365, 174)


def test_custom_color_blink_preserves_resolution_and_body_texture(qapp):
    from aedrova.desktop.bud_art import blinking_sprite

    open_eye = sprite("product", "#8844AA").toImage()
    closed_eye = blinking_sprite("product", "#8844AA").toImage()
    assert open_eye.size() == closed_eye.size() == sprite("product").size()
    assert open_eye != closed_eye
    assert open_eye.pixelColor(250, 410) == closed_eye.pixelColor(250, 410)
