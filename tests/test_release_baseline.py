"""The deferred startup dashboard must not remain in release navigation."""

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMenu

from aedrova.desktop.window import AedrovaWindow


def test_pulse_is_not_exposed_and_primary_navigation_survives(qtbot, tmp_path):
    window = AedrovaWindow(settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    assert window.pages.count() == 4
    assert not hasattr(window, "pulse_page")
    assert not hasattr(window, "open_pulse")
    for menu in window.menuBar().findChildren(QMenu):
        assert all("Pulse" not in action.text() for action in menu.actions())
    for i in range(4):
        window.select_tab(i)
        assert window.pages.currentIndex() == i
    window.set_theme("dark", persist=False)
    window.set_theme("light", persist=False)


def test_staging_launcher_rejects_production_fallback_and_private_keys():
    import importlib.util
    from pathlib import Path

    import pytest

    spec = importlib.util.spec_from_file_location(
        "staging_launcher", Path(__file__).parents[1] / "scripts/run_staging.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    validate = module.validate

    config = {
        "environment": "staging",
        "supabase_url": "https://stage-example.supabase.co",
        "supabase_publishable_key": "sb_publishable_fixturepublickey",
        "managed_origin": "https://stage-example.onrender.com",
        "connector_origin": "https://stage-connectors.onrender.com",
    }
    assert validate(config) == config
    for change in (
        {"supabase_url": "https://cpelagtufyocepnqcqqd.supabase.co"},
        {"managed_origin": "https://aedrova.com"},
        {"connector_origin": "https://aedrova-connectors.onrender.com"},
        {"supabase_publishable_key": "sb_secret_fixture"},
        {"environment": "production"},
        {"private_secret": "not-allowed"},
    ):
        with pytest.raises(ValueError):
            validate(config | change)
