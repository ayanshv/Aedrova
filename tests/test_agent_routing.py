from types import SimpleNamespace

import pytest

from aedrova.agents.routing import Candidate, CodingAdapter, Policy, choose
from aedrova.agents.runtime import BuildCancelled


def test_chat_never_launches_agent():
    assert choose("hello", []).provider is None


def test_default_without_evidence():
    rows = [Candidate("codex", True), Candidate("claude_code", True)]
    assert choose("fix bug", rows).provider == "codex"
    assert choose("fix bug", rows, space_default="claude_code").provider == "claude_code"


def test_override_and_no_silent_fallback():
    rows = [Candidate("codex", True), Candidate("claude_code", False)]
    with pytest.raises(ValueError, match="explicitly"):
        choose("fix bug", rows, mode="manual", manual="claude_code")
    assert choose("fix bug", rows, mode="manual", manual="codex").provider == "codex"


def test_unknown_cost_fails_closed_under_budget():
    with pytest.raises(ValueError, match="No eligible"):
        choose("fix bug", [Candidate("codex", True)], remaining_credit=1)


def test_reviewed_evaluations_and_constraints():
    rows = [
        Candidate(
            "codex", True, estimated_cost=2, latency=90, samples=100, successes=50, evaluated=True
        ),
        Candidate(
            "claude_code",
            True,
            estimated_cost=1,
            latency=30,
            samples=100,
            successes=95,
            evaluated=True,
        ),
    ]
    assert choose("fix bug", rows).provider == "claude_code"
    assert choose("fix bug", rows, remaining_credit=1).provider == "claude_code"
    assert (
        choose("fix bug", rows, policy=Policy(default="codex", minimum_samples=200)).provider
        == "codex"
    )


@pytest.mark.parametrize("provider", ["codex", "claude_code"])
def test_adapter_preserves_harness_and_cancellation(provider):
    calls = []
    runner = SimpleNamespace(
        run=lambda *a, **kw: calls.append((a, kw)) or "done", cancel=lambda: calls.append("cancel")
    )
    adapter = CodingAdapter(provider, runner)
    assert adapter.execute("/repo", "task", plan=True) == "done"
    assert calls[0] == ((provider, "/repo", "task"), {"plan": True})
    adapter.cancel()
    assert calls[-1] == "cancel"


def test_errors_are_not_retried_or_replayed():
    def failed(*a, **kw):
        raise BuildCancelled()

    with pytest.raises(BuildCancelled):
        CodingAdapter("codex", SimpleNamespace(run=failed)).execute("/repo", "task", plan=False)


def test_telemetry_excludes_task():
    assert "private secret" not in str(
        choose("fix private secret bug", [Candidate("codex", True)]).record()
    )


def test_routing_telemetry_is_scoped_and_idempotent(tmp_path):
    from aedrova.agents.ledger import RunLedger

    ledger = RunLedger(tmp_path)
    run, _ = ledger.enqueue("alice", "team", "fix bug", {})
    decision = choose("fix bug", [Candidate("codex", True)]).record()
    ledger.record_route(run, "planning", decision, "completed")
    ledger.record_route(run, "planning", decision, "completed")
    assert len(ledger.routing_outcomes("alice", "team")) == 1
    assert ledger.routing_outcomes("bob", "team") == []
    assert ledger.routing_outcomes("alice", "other") == []


def test_offline_evaluation_cannot_execute_or_mutate_policy():
    from aedrova.agents.routing import evaluate

    result = evaluate(
        [{"task": "hello", "expected": None}, {"task": "fix bug", "expected": "codex"}],
        [Candidate("codex", True)],
    )
    assert result["samples"] == result["matched"] == 2


def test_tool_and_latency_limits():
    rows = [
        Candidate("codex", True, tools=False, latency=1),
        Candidate("claude_code", True, latency=20),
    ]
    with pytest.raises(ValueError, match="No eligible"):
        choose("fix bug", rows, maximum_latency=10)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1])
def test_invalid_budget_is_rejected(value):
    with pytest.raises(ValueError):
        choose("fix bug", [Candidate("codex", True)], remaining_credit=value)


def test_reviewed_cohort_requires_exact_category_and_configuration(tmp_path):
    import json

    from aedrova.agents.routing import reviewed_candidates

    path = tmp_path / "cohort.json"
    path.write_text(
        json.dumps({"reviewed": True, "category": "repair", "configuration": "v1", "providers": {}})
    )
    rows = [Candidate("codex", True)]
    assert reviewed_candidates(path, rows, task_category="repair", configuration="v1") == rows
    with pytest.raises(ValueError, match="incompatible"):
        reviewed_candidates(path, rows, task_category="testing", configuration="v1")
