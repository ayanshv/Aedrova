from threading import Event

from test_connected import setup

from aedrova.desktop.connected import with_reaction


def ready(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    window.account_dialog.hide()
    window.connected.refresh()
    qtbot.waitUntil(
        lambda: not window.account_dialog.busy and "m" in window.connected.cache.get("c", {})
    )
    window.connected.timer.stop()
    return window, service


def test_reaction_is_visible_before_slow_request_finishes_and_rapid_toggle_wins(qtbot, tmp_path):
    window, service = ready(qtbot, tmp_path)
    entered, release = Event(), Event()
    server = {"mine": False}
    writes = []

    def rpc(name, params):
        if name == "set_message_reaction":
            writes.append(params["p_present"])
            entered.set()
            assert release.wait(5)
            server["mine"] = params["p_present"]

    service.rpc = rpc
    service.message_interactions = lambda ids: [
        {
            "id": "m",
            "reactions": [{"emoji": "👍", "count": 1, "mine": True}] if server["mine"] else [],
        }
    ]
    try:
        window.react_message("m", "👍", True)
        assert window.channel.messages[0].reactions == [{"emoji": "👍", "count": 1, "mine": True}]
        qtbot.waitUntil(entered.is_set)
        window.react_message("m", "👍", False)
        assert not window.channel.messages[0].reactions
        # Old polling data must not override the latest local intention.
        rows = list(window.connected.cache["c"].values())
        window.connected.apply(window.account_dialog.snapshot, rows, "w", "c")
        assert not window.channel.messages[0].reactions
    finally:
        release.set()
    qtbot.waitUntil(lambda: not window.connected.reaction_edits)
    assert writes == [True, False]
    assert not window.channel.messages[0].reactions


def test_failure_rolls_back_only_reaction_and_keeps_chat(qtbot, tmp_path):
    window, service = ready(qtbot, tmp_path)
    entered, release = Event(), Event()

    def rpc(name, params):
        if name == "set_message_reaction":
            entered.set()
            release.wait(5)
            raise PermissionError("Not allowed")

    service.rpc = rpc
    try:
        window.react_message("m", "🎉", True)
        assert window.channel.messages[0].reactions[0]["mine"]
        qtbot.waitUntil(entered.is_set)
    finally:
        release.set()
    qtbot.waitUntil(lambda: not window.connected.reaction_edits)
    assert window.channel.messages[0].body == "Hello"
    assert not window.channel.messages[0].reactions
    assert "Reaction could not be confirmed" in window.notice.text()


def test_overlay_preserves_other_members_counts_without_mutation():
    row = {"id": "m", "reactions": [{"emoji": "👍", "count": 3, "mine": False}]}
    added = with_reaction(row, "👍", True)
    assert added["reactions"][0]["count"] == 4
    assert with_reaction(added, "👍", True)["reactions"][0]["count"] == 4
    assert with_reaction(added, "👍", False)["reactions"][0]["count"] == 3
    assert row["reactions"][0]["count"] == 3 and not row["reactions"][0]["mine"]


def test_unsent_and_signout_drop_optimistic_reactions(qtbot, tmp_path):
    window, service = ready(qtbot, tmp_path)
    window.account_dialog.busy = True
    window.react_message("m", "❤️", True)
    assert window.connected.reaction_edits
    window.connected.disconnect()
    assert not window.connected.reaction_edits and not window.connected.reaction_jobs
    assert (
        with_reaction({"id": "m", "unsent_at": "now", "reactions": []}, "❤️", True)["reactions"]
        == []
    )
    window.account_dialog.busy = False


def test_queued_clicks_coalesce_and_reactions_precede_background_work(qtbot, tmp_path):
    window, service = ready(qtbot, tmp_path)
    writes = []
    service.rpc = lambda name, params: (
        writes.append(params["p_present"]) if name == "set_message_reaction" else None
    )
    window.account_dialog.busy = True
    window.connected.enqueue(("avatar", "photo"), lambda: b"", lambda _: None)
    for present in (True, False, True, False):
        window.react_message("m", "👍", present)
    assert len(window.connected.queue) == 2
    assert window.connected.queue[0][0][0] == "reaction"
    assert not window.channel.messages[0].reactions
    window.account_dialog.busy = False
    window.connected.refresh()
    qtbot.waitUntil(lambda: not window.connected.reaction_edits)
    assert writes == [False]
