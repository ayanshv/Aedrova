"""Role advice is non-authoritative; local physics and named mentions preserve identity."""

from copy import deepcopy
from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt
from test_ai_teammates import profile
from test_connected import setup

from aedrova.desktop.choice_slider import ChoiceSlider
from aedrova.desktop.teammate_habitat import Habitat
from aedrova.teammates.advisor import advise, parse_advice, role_prompt
from aedrova.teammates.model import prompt, validate


def test_free_role_uses_real_provider_only_on_request_and_suggestions_are_allowlisted(tmp_path):
    seen = []

    class Runner:
        def run(self, provider, project, text, *, plan):
            seen.append((provider, project, text, plan))
            assert set(p.name for p in project.iterdir()) == {"README.md", ".git"}
            assert "workspace-context" not in text
            return (
                '{"summary":"Turn customer feedback into requirements.",'
                '"tools":["workspace_search","figma","shell_unrestricted","figma"]}'
            )

    result = advise("A product researcher", "codex", Runner())
    assert result["tools"] == ["workspace_search", "figma"]
    assert seen[0][3] is True
    assert not seen[0][1].exists()
    for bad in ("", "x" * 241):
        with pytest.raises(ValueError):
            role_prompt(bad)
    with pytest.raises(ValueError):
        parse_advice('{"summary":"Okay","tools":"all"}')


def test_custom_role_does_not_change_execution_authority():
    config = profile("research")["config"]
    config["role_label"] = "Financial analyst for our team"
    config["suggested_tools"] = ["finance"]
    validate(config)
    instructions = prompt(config)
    assert "Financial analyst" in instructions and "Do not edit files" in instructions
    config["role_label"] = "x" * 241
    with pytest.raises(ValueError):
        validate(config)


def test_slider_is_keyboard_accessible_and_retains_semantic_values(qtbot):
    slider = ChoiceSlider()
    qtbot.addWidget(slider)
    slider.addItem("Quiet", "quiet")
    slider.addItem("Milestones", "milestones")
    slider.addItem("Detailed", "detailed")
    slider.show()
    slider.slider.setFocus()
    qtbot.keyClick(slider.slider, Qt.Key.Key_Right)
    assert slider.currentData() == "milestones"
    assert slider.slider.accessibleDescription() == "Milestones"
    assert slider.findData("detailed") == 2


def rows(n):
    result = []
    for i in range(n):
        r = deepcopy(profile())
        r["id"] = "orb-" + str(i)
        r["config"]["name"] = "Pixel" + str(i)
        result.append(r)
    return result


def test_twelve_marbles_settle_without_respawning_and_hidden_timer_stops(qtbot):
    window = SimpleNamespace(reduced_motion=False)
    habitat = Habitat(window)
    qtbot.addWidget(habitat)
    habitat.resize(178, 250)
    habitat.show()
    profiles = rows(12)
    habitat.sync(profiles, "w")
    habitat.timer.stop()
    for _ in range(900):
        habitat.step(1 / 60)
    identity = habitat.marbles["orb-0"]
    import math

    marbles = list(habitat.marbles.values())
    assert (
        min(
            math.hypot(a.x - b.x, a.y - b.y)
            for i, a in enumerate(marbles)
            for b in marbles[i + 1 :]
        )
        > 45
    )  # The visible orb silhouettes do not intersect.
    assert all(
        0 <= m.x <= habitat.width() - 56 and -1 <= m.y <= habitat.height() - 56
        for m in habitat.marbles.values()
    )
    profiles[0]["config"]["name"] = "Renamed"
    habitat.sync(profiles, "w")
    assert habitat.marbles["orb-0"] is identity
    assert identity.widget.accessibleName().endswith("Renamed")
    habitat.hide()
    assert not habitat.timer.isActive()
    habitat.sync([], "other-workspace")
    assert not habitat.marbles


def test_reduced_motion_is_still_and_click_inserts_identity_without_running(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    window.reduced_motion = True
    section = window.ai_team_section
    section.sync(rows(3), "w")
    assert not section.habitat.timer.isActive()
    called = []
    window.start_agent_request = lambda *_: called.append(True)
    row = rows(3)[1]
    section.mention(row)
    assert window.composer.editor.toPlainText() == "@Pixel1 "
    assert window.composer.mention_tokens["Pixel1"] == "<@ai:orb-1|Pixel1>"
    assert not called
    row["paused"] = True
    section.mention(row)
    assert window.composer.editor.toPlainText() == "@Pixel1 "
