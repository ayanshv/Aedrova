"""Switching channels shows known messages at once and starts that channel's sync right away."""

import threading

from test_connected import row, setup, snapshot


def two_channels():
    state = snapshot()
    state["channels"].append({"id": "d", "workspace_id": "w", "name": "design", "private": False})
    return state


def ready(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.snapshot = two_channels
    window.account_dialog.loaded(two_channels())
    service.message_page = lambda channel, **kw: (
        [] if kw.get("after") else [dict(row(f"m-{channel}"), channel_id=channel, body=channel)]
    )
    window.connected.refresh()
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    return window, service


def test_a_channel_seen_before_renders_immediately_on_switch(qtbot, tmp_path):
    window, _ = ready(qtbot, tmp_path)
    window.connected.cache["d"] = {"m-d": dict(row("m-d"), channel_id="d", body="Design notes")}
    window.switch_channel("d")
    assert [m.body for m in window.channel.messages] == ["Design notes"]
    assert [m.body for m in window.messages.conversation_model.messages] == ["Design notes"]


def test_switching_stops_the_previous_channels_sync_so_the_new_one_starts(qtbot, tmp_path):
    window, _ = ready(qtbot, tmp_path)
    window.connected.sync_interrupt.clear()
    window.account_dialog.busy = True  # a sync for the old channel is still running
    window.switch_channel("d")
    assert window.connected.sync_interrupt.is_set()
    window.account_dialog.busy = False


def test_the_new_channel_is_fetched_after_a_switch(qtbot, tmp_path):
    window, service = ready(qtbot, tmp_path)
    asked = []
    original = service.message_page

    def page(channel, **kw):
        asked.append(channel)
        return original(channel, **kw)

    service.message_page = page
    window.switch_channel("d")
    qtbot.waitUntil(lambda: "d" in asked)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert [m.body for m in window.channel.messages] == ["d"]


def test_starting_a_direct_message_says_so_at_once_and_clears_when_it_opens(
    qtbot, tmp_path, monkeypatch
):
    window, service = ready(qtbot, tmp_path)
    state = two_channels()
    state["directory"] = [
        {"workspace_id": "w", "user_id": "p2", "display_name": "Priya Shah"},
        {"workspace_id": "w", "user_id": "u", "display_name": "Me"},
    ]
    state["members"].append({"workspace_id": "w", "user_id": "p2", "role": "member"})
    window.connected.account.snapshot = state
    service.snapshot = lambda: state
    release = threading.Event()

    def start(name, params):
        release.wait(5)  # the server is slow to answer
        return "d"

    service.rpc = start
    monkeypatch.setattr(
        "aedrova.desktop.connected.choose_conversation", lambda *_: ("person", "p2")
    )
    window.connected.start_dm()
    assert "Priya Shah" in window.notice.text() and window.notice.isVisible()
    skeleton = window.connected._loading_skeleton
    assert skeleton.isVisible()  # feedback shows before the conversation exists
    release.set()
    qtbot.waitUntil(lambda: not skeleton.isVisible(), timeout=8000)
    assert "Opening your conversation" not in window.notice.text() or window.notice.isHidden()
