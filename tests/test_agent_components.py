"""Live task list, approval and question cards, and the working indicator."""

from test_connected import setup

from aedrova.desktop.agent_components import (
    ApprovalCard,
    FourDots,
    PromptCard,
    StepChecklist,
)


def test_chat_flow_fills_in_without_inventing_progress(qtbot):
    steps = StepChecklist()
    qtbot.addWidget(steps)
    steps.observe("Checking workspace access…")
    assert steps.states() == [
        ("access", "running"),
        ("context", "pending"),
        ("respond", "pending"),
    ]
    steps.observe("Writing a response…")
    # Context never ran for this request, so it is dropped rather than shown as done.
    assert steps.states() == [("access", "done"), ("respond", "running")]
    steps.finish()
    assert steps.states() == [("access", "done"), ("respond", "done")]


def test_build_flow_tracks_commands_edits_and_failed_checks(qtbot):
    steps = StepChecklist()
    qtbot.addWidget(steps)
    steps.observe("Preparing an independent local Git copy…")
    steps.observe("Running: ls src")
    assert steps.states()[0] == ("copy", "running")
    steps.observe("Plan ready · starting background build…")
    assert dict(steps.states())["plan"] == "done"  # planning ran between the two updates
    steps.observe("Files changed: []")
    assert dict(steps.states())["build"] == "running"
    steps.observe("Running: python -m pytest -q")
    assert dict(steps.states())["checks"] == "running"
    steps.observe("$ python -m pytest -q\n1 failed\nExit code: 1")
    check = steps.find("checks")["commands"][0]
    assert check["state"] == "failed"
    steps.finish(ok=False)
    assert dict(steps.states())["checks"] == "failed"


def test_four_dots_swap_positions_and_stop_when_hidden(qtbot):
    dots = FourDots()
    qtbot.addWidget(dots)
    dots.show()
    assert dots.timer.isActive()
    before = list(dots.slots)
    for _ in range(40):
        dots.advance()
    assert sorted(dots.slots) == [0, 1, 2, 3] and dots.slots != before
    dots.hide()
    assert not dots.timer.isActive()


def test_approval_card_waits_then_reports_one_decision(qtbot):
    card = ApprovalCard("Bash", {"command": "python build.py", "reason": "Needed to build"})
    qtbot.addWidget(card)
    seen = []
    card.decided.connect(seen.append)
    assert seen == []
    card.allow.click()
    card.deny.click()  # a second click cannot change the outcome
    card.resolve(False)
    assert seen == [True] and not card.allow.isVisible()


def test_prompt_card_requires_answers_and_sends_once(qtbot):
    question = {
        "title": "Which database?",
        "fields": [
            {
                "label": "Database",
                "type": "single",
                "options": ["Postgres", "SQLite"],
                "required": True,
            },
            {"label": "Notes", "type": "text", "required": False},
            {
                "label": "Extras",
                "type": "multiple",
                "options": ["Auth", "Billing"],
                "required": False,
            },
        ],
    }
    card = PromptCard(question)
    qtbot.addWidget(card)
    sent = []
    card.submitted.connect(sent.append)
    card.send_button.click()
    assert sent == [] and "required" in card.note.text()
    postgres, sqlite = card.inputs[0][2]
    postgres.click()
    sqlite.click()
    assert sqlite.isChecked() and not postgres.isChecked()
    card.inputs[2][2][1].click()
    card.send_button.click()
    card.send_button.click()
    assert sent == [
        [
            {"label": "Database", "answer": "SQLite"},
            {"label": "Notes", "answer": ""},
            {"label": "Extras", "answer": ["Billing"]},
        ]
    ]


def test_stream_shows_checklist_cards_and_keeps_a_summary(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    feed = window.agent_feed
    feed.set_status("Aedrova", "Checking workspace access…")
    feed.set_status("Aedrova", "Finding relevant context")
    assert feed.status_row.checklist.isVisible() or feed.status_row.checklist.steps
    card = feed.add_approval("Write", {"file_path": "hello.py"})
    assert feed.cards() == [card]
    feed.resolve_cards()
    assert card.resolved
    feed.set_status("Aedrova", "Writing a response…")
    feed.finish_with_result("All done.")
    assert feed.reply_row.step_summary is not None
    assert "steps completed" in feed.reply_row.step_summary.title


def test_agent_headings_render_as_quiet_bold_lead_ins(qtbot):
    from aedrova.desktop.conversation import markdown_html

    html = markdown_html("## Changes\n- one\n- two\n\n# Checks\nAll passed.", agent=True)
    assert "<h1" not in html and "<h2" not in html
    assert "Changes" in html and "All passed." in html


def test_every_agent_prompt_asks_for_scannable_replies_without_titles():
    from aedrova.agents.runtime import RESPONSE_STYLE

    assert "Do not use headings or titles" in RESPONSE_STYLE
    assert "complete" in RESPONSE_STYLE and "senior engineer" in RESPONSE_STYLE


def test_context_step_reports_how_much_was_actually_read(qtbot):
    steps = StepChecklist()
    qtbot.addWidget(steps)
    steps.observe("Checking workspace access…")
    steps.observe("Reading #general…")
    steps.observe("Gathered 142 messages for context")
    assert steps.find("context")["label"] == "Read 142 messages"


class FakeReview:
    def __init__(self, count):
        from types import SimpleNamespace

        change = SimpleNamespace(line_counts=lambda: (10, 2), path="a.py")
        self.changes = tuple(change for _ in range(count))
        self.source = "/work/project"


def delivery_fixture(qtbot, review_count=2):
    from types import SimpleNamespace

    from PySide6.QtCore import QObject, Signal

    from aedrova.desktop.agent_components import DeliveryCard

    class Dialog(QObject):
        state = Signal(str, object)

        def __init__(self):
            super().__init__()
            self.review = None
            self.calls = []
            self.scope = SimpleNamespace(text=lambda: "PRIVATE\nRepository: team/app")
            self.studio = SimpleNamespace(open_review=lambda: self.calls.append("open"))

        def apply(self, *, confirmed=False):
            self.calls.append(("apply", confirmed))

        def prepare(self):
            self.calls.append("prepare")

        def publish(self, *, confirmed=False):
            self.calls.append(("publish", confirmed))

        def open_project_connection(self):
            self.calls.append("connect")

    dialog = Dialog()
    card = DeliveryCard(dialog)
    qtbot.addWidget(card)
    card.show()
    dialog.review = FakeReview(review_count)
    dialog.state.emit("loaded", dialog.review)
    return dialog, card


def test_delivery_card_applies_only_after_its_own_confirmation(qtbot):
    dialog, card = delivery_fixture(qtbot)
    assert "2 files changed" in card.headline.text() and "+20" in card.headline.text()
    assert card.apply_button.isVisible() and card.pr_button.isVisible()
    card.apply_button.click()
    assert dialog.calls == []  # a single click never changes the project
    assert "/work/project" in card.detail.text() and card.confirm_button.isVisible()
    card.cancel_button.click()
    assert dialog.calls == [] and card.apply_button.isVisible()
    card.apply_button.click()
    card.confirm_button.click()
    assert dialog.calls == [("apply", True)]
    dialog.state.emit("applied", "/recovery")
    assert not card.apply_button.isVisible() and "Applied" in card.headline.text()


def test_pull_request_needs_a_prepared_scope_then_a_separate_confirmation(qtbot):
    dialog, card = delivery_fixture(qtbot)
    card.pr_button.click()
    assert dialog.calls == ["prepare"]
    dialog.state.emit("prepared", object())
    assert "team/app" in card.detail.text()
    assert dialog.calls == ["prepare"]  # nothing is published yet
    card.confirm_button.click()
    assert dialog.calls == ["prepare", ("publish", True)]
    dialog.state.emit("published", {"message": "Draft PR created", "url": "https://github.com/t/a/pull/1"})
    assert card.link_button.isVisible() and not card.pr_button.isVisible()


def test_pull_request_without_a_repository_offers_to_connect_one(qtbot):
    dialog, card = delivery_fixture(qtbot)
    card.pr_button.click()
    dialog.state.emit("needs_repository", None)
    card.confirm_button.click()
    assert dialog.calls == ["prepare", "connect"]


def test_empty_build_shows_no_delivery_actions(qtbot):
    _, card = delivery_fixture(qtbot, review_count=0)
    assert "no changes" in card.headline.text() and not card.apply_button.isVisible()


def test_message_times_read_like_a_person_wrote_them(qtbot):
    from datetime import datetime

    from aedrova.desktop.conversation import human_time

    now = datetime(2026, 11, 22, 15, 0)
    assert "2026" not in human_time("2026-11-22 05:00", now)
    assert human_time("2026-11-21 05:00", now).startswith("Yesterday ")
    assert human_time("2026-11-19 05:00", now).startswith("Thu ")
    assert human_time("2026-09-27 05:00", now).startswith("Sep 27, ")
    assert human_time("2025-09-27 05:00", now).startswith("Sep 27 2025, ")
    assert human_time("not a time") == "not a time"
