"""Deterministic, opt-in coding routing. No model calls or task text telemetry."""

import math
import re
from dataclasses import asdict, dataclass

PROVIDERS = ("codex", "claude_code")


@dataclass(frozen=True)
class Candidate:
    provider: str
    available: bool
    tools: bool = True
    estimated_cost: float | None = None
    latency: float | None = None
    samples: int = 0
    successes: int = 0
    # Evaluations must be reviewed offline, not learned from unvalidated live traffic.
    evaluated: bool = False


@dataclass(frozen=True)
class Policy:
    default: str = "codex"
    minimum_samples: int = 30
    cost_weight: float = 0.2
    latency_weight: float = 0.2
    quality_weight: float = 0.6

    def __post_init__(self):
        if self.default not in PROVIDERS or self.minimum_samples < 1:
            raise ValueError("Invalid routing policy")
        for weight in (self.cost_weight, self.latency_weight, self.quality_weight):
            if not math.isfinite(weight) or weight < 0:
                raise ValueError("Invalid routing weight")


@dataclass(frozen=True)
class Decision:
    provider: str | None
    category: str
    reason: str
    policy_version: str = "1"

    def record(self):
        return asdict(self)


def category(task):
    if not isinstance(task, str) or not task.strip() or len(task) > 20000:
        raise ValueError("Development requests require 1–20,000 characters")
    for name, pattern in (
        ("repair", r"\b(fix|debug|repair|regression|bug)\b"),
        ("testing", r"\b(tests?|coverage|pytest)\b"),
        ("refactor", r"\b(refactor|migrate|restructure)\b"),
        ("implementation", r"\b(build|implement|create|code|deploy|repository)\b"),
    ):
        if re.search(pattern, task, re.I):
            return name
    return "conversation"


def choose(
    task,
    candidates,
    *,
    mode="auto",
    manual=None,
    space_default=None,
    remaining_credit=None,
    maximum_latency=None,
    policy=None,
):
    policy = policy or Policy()
    kind = category(task)
    if mode not in {"auto", "manual", "space_default"}:
        raise ValueError("Invalid routing mode")
    if remaining_credit is not None and (
        not math.isfinite(remaining_credit) or remaining_credit < 0
    ):
        raise ValueError("Invalid remaining credit")
    rows = {}
    for candidate in candidates:
        if candidate.provider not in PROVIDERS or candidate.provider in rows:
            raise ValueError("Invalid or duplicate provider")
        if candidate.samples < 0 or not 0 <= candidate.successes <= candidate.samples:
            raise ValueError("Invalid evaluation")
        for number in (candidate.estimated_cost, candidate.latency):
            if number is not None and (not math.isfinite(number) or number < 0):
                raise ValueError("Invalid estimate")
        rows[candidate.provider] = candidate
    explicit = manual if mode == "manual" else space_default if mode == "space_default" else None
    if explicit is not None and explicit not in PROVIDERS:
        raise ValueError("Invalid provider preference")
    if mode != "auto" and explicit is None:
        raise ValueError("A provider must be selected")
    if kind == "conversation":
        return Decision(None, kind, "Use the conversation path; no coding agent is needed.")

    def eligible(row):
        return (
            row.available
            and row.tools
            and (
                remaining_credit is None
                or (row.estimated_cost is not None and row.estimated_cost <= remaining_credit)
            )
            and (
                maximum_latency is None
                or (row.latency is not None and row.latency <= maximum_latency)
            )
        )

    available = {key: row for key, row in rows.items() if eligible(row)}
    if explicit:
        if explicit not in available:
            raise ValueError(
                "Selected provider unavailable or outside limits. "
                "Choose another provider explicitly before retrying."
            )
        return Decision(explicit, kind, "Explicit provider preference respected.")
    if not available:
        raise ValueError("No eligible coding provider. Check access and limits.")
    default = space_default or policy.default
    if default not in PROVIDERS:
        raise ValueError("Invalid Space default")
    # Compare only complete, approved, sufficiently sampled evaluations for this category.
    measured = all(
        row.evaluated
        and row.samples >= policy.minimum_samples
        and row.latency is not None
        and row.estimated_cost is not None
        for row in available.values()
    )
    if measured and len(available) > 1:
        costs = max(1e-9, max(r.estimated_cost for r in available.values()))
        times = max(1e-9, max(r.latency for r in available.values()))

        def score(row):
            # Wilson lower bound penalizes uncertain quality estimates.
            n, z = row.samples, 1.96
            rate = row.successes / n
            quality = (
                rate + z * z / (2 * n) - z * math.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n))
            ) / (1 + z * z / n)
            return (
                policy.quality_weight * quality
                - policy.cost_weight * row.estimated_cost / costs
                - policy.latency_weight * row.latency / times
            )

        selected = max(available, key=lambda key: (score(available[key]), key == default))
        return Decision(selected, kind, "Selected from reviewed comparable evaluation metrics.")
    selected = default if default in available else sorted(available)[0]
    return Decision(selected, kind, "Insufficient comparable evidence; using an eligible default.")


class CodingAdapter:
    """Delegate to the proven harness, retaining events, permissions and cancellation."""

    def __init__(self, provider, runner):
        if provider not in PROVIDERS:
            raise ValueError("Unsupported coding provider")
        self.provider, self.runner = provider, runner

    def execute(self, project, prompt, *, plan):
        # Runtime checks cancellation, bounds lifetime and enforces tool approval.
        return self.runner.run(self.provider, project, prompt, plan=plan)

    def cancel(self):
        self.runner.cancel()


def runtime_candidates():
    from aedrova.agents.runtime import executable

    result = []
    for provider, binary in (("codex", "codex"), ("claude_code", "claude")):
        try:
            executable(binary)
            installed = True
        except ValueError:
            installed = False
        # Installation is only a preflight; live login and budget are verified by existing runtime.
        result.append(Candidate(provider, installed))
    return result


def evaluate(cases, candidates, *, policy=None):
    """Offline synthetic routing evaluation; never starts agents or updates live policy."""
    results = []
    for case in cases:
        decision = choose(case["task"], candidates, policy=policy)
        results.append(
            {
                "category": decision.category,
                "provider": decision.provider,
                "matches_expected": decision.provider == case["expected"],
            }
        )
    return {
        "samples": len(results),
        "matched": sum(r["matches_expected"] for r in results),
        "results": results,
    }
