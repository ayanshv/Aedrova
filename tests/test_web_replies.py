import pytest

from aedrova.agents.replies import WEB_INSTRUCTION, reply_request, wants_web
from aedrova.desktop.agent_components import StepChecklist


class Access:
    provider, model = "codex", "gpt-5.3-codex"
    limits = {"output_tokens": 2000}


@pytest.mark.parametrize(
    "question",
    [
        "@Aedrova summary soysee.com",
        "summarize https://example.org/pricing please",
        "what does www.stripe.com offer",
        "search the web for the best pasta recipe",
        "give me the latest news about OpenAI",
        "can you google this error",
    ],
)
def test_websites_and_explicit_web_requests_turn_search_on(question):
    assert wants_web(question)


@pytest.mark.parametrize(
    "question",
    [
        "what did we decide about onboarding",
        "draft a welcome message for the team",
        "summarize the last meeting",
        "fix the bug in checkout.py",
        "hello",
    ],
)
def test_ordinary_questions_stay_tool_free(question):
    assert not wants_web(question)


def test_the_request_carries_hosted_search_only_when_asked():
    _, plain = reply_request(Access, "hi")
    assert plain["tools"] == [] and WEB_INSTRUCTION not in plain["instructions"]
    path, searching = reply_request(Access, "summary soysee.com", web=True)
    assert path == "/responses" and searching["tools"] == [{"type": "web_search"}]
    assert "untrusted data" in searching["instructions"]
    assert "no live web" not in searching["instructions"].lower()


def test_the_progress_rows_say_the_web_was_used(qtbot):
    steps = StepChecklist()
    qtbot.addWidget(steps)
    steps.observe("Gathered 12 messages for context")
    steps.observe("Writing a response using the web…")
    assert steps.find("respond")["label"] == "Replying from 12 messages of context and the live web"
    only_web = StepChecklist()
    qtbot.addWidget(only_web)
    only_web.observe("Writing a response using the web…")
    assert only_web.find("respond")["label"] == "Replying from the live web"
