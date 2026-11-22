"""Permission requests are sequenced, optional, and never prompt before the person asks."""

from aedrova.desktop.permission_cards import PermissionsPage, pending_kinds


class Backend:
    def __init__(self, answers):
        self.answers, self.asked = answers, []

    def permission(self, kind, callback):
        self.asked.append(kind)
        callback(self.answers.get(kind, True))


def page(qtbot, monkeypatch, states, answers=None, assume=()):
    monkeypatch.setattr("aedrova.desktop.motion.reduced", lambda: True)
    backend = Backend(answers or {})
    widget = PermissionsPage(
        backend, state=lambda kind: states.get(kind, "undetermined"), assume=assume
    )
    qtbot.addWidget(widget)
    return widget, backend


def test_opening_the_page_never_prompts(qtbot, monkeypatch):
    widget, backend = page(qtbot, monkeypatch, {})
    assert backend.asked == []
    assert all(row.state == "idle" for row in widget.rows.values())


def test_allow_all_asks_one_at_a_time_in_order_and_ends_granted(qtbot, monkeypatch):
    widget, backend = page(qtbot, monkeypatch, {})
    widget.all.click()
    qtbot.waitUntil(lambda: len(backend.asked) == 3)
    assert backend.asked == ["microphone", "camera", "screen"]
    assert all(row.state == "granted" for row in widget.rows.values())
    assert not widget.all.isVisible()


def test_a_refusal_is_not_an_error_and_other_rows_still_work(qtbot, monkeypatch):
    widget, backend = page(qtbot, monkeypatch, {"camera": "denied"}, answers={"camera": False})
    assert widget.rows["camera"].state == "blocked"  # already refused: points to Settings
    widget.rows["microphone"].action.click()
    qtbot.waitUntil(lambda: widget.rows["microphone"].state == "granted")
    assert backend.asked == ["microphone"]


def test_finished_setups_never_see_the_step():
    assert pending_kinds(lambda kind: "granted") == []
    assert pending_kinds(lambda kind: "undetermined" if kind == "screen" else "granted") == [
        "screen"
    ]


def test_screen_access_that_never_calls_back_still_settles(qtbot, monkeypatch):
    states = {}
    widget, backend = page(qtbot, monkeypatch, states, answers={"screen": False})
    widget.rows["screen"].action.click()
    qtbot.waitUntil(lambda: backend.asked == ["screen"])
    assert widget.rows["screen"].state == "asking"  # the system sheet may still be up
    states["screen"] = "granted"  # the person turned it on
    qtbot.waitUntil(lambda: widget.rows["screen"].state == "granted", timeout=3000)
    assert widget.current is None


def test_screen_access_that_is_never_granted_points_to_settings(qtbot, monkeypatch):
    widget, _ = page(qtbot, monkeypatch, {}, answers={"screen": False})
    widget.rows["screen"].action.click()
    qtbot.waitUntil(lambda: widget.rows["screen"].state == "blocked", timeout=7000)
    assert widget.rows["screen"].action.text() == "Open Settings"
    assert "Screen Recording" in widget.rows["screen"].why.text()


def test_a_late_grant_after_blocked_is_noticed(qtbot, monkeypatch):
    states = {"camera": "denied"}
    widget, _ = page(qtbot, monkeypatch, states)
    assert widget.rows["camera"].state == "blocked"
    states["camera"] = "granted"
    qtbot.waitUntil(lambda: widget.rows["camera"].state == "granted", timeout=3000)


def test_a_camera_that_gives_no_answer_still_ends_as_done_in_setup(qtbot, monkeypatch):
    shared = set()
    monkeypatch.setattr("aedrova.desktop.motion.reduced", lambda: True)
    backend = Backend({"camera": False})
    widget = PermissionsPage(
        backend,
        state=lambda kind: "denied" if kind == "camera" else "undetermined",
        assume=("camera",),
        assumed=shared,
    )
    qtbot.addWidget(widget)
    assert widget.rows["camera"].action.text() == "Allow"  # not a dead "Open Settings"
    widget.rows["camera"].action.click()
    qtbot.waitUntil(lambda: widget.rows["camera"].state == "granted")
    assert shared == {"camera"}
    again = PermissionsPage(
        backend, state=lambda kind: "denied", assume=("camera",), assumed=shared
    )
    qtbot.addWidget(again)
    assert again.rows["camera"].state == "granted"  # still done when you come back
    assert again.rows["screen"].state != "granted"  # nothing else is pretended
