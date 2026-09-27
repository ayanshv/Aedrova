from collections.abc import AsyncIterator
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from uuid import UUID

from pydantic import Field

from aedrova.domain.contracts import ContextPackage, Record


class AgentRequest(Record):
    build_id: UUID
    context: ContextPackage
    checkout: Path
    max_cost_usd: float = Field(gt=0, allow_inf_nan=False)
    timeout_seconds: int = Field(gt=0, le=3600)


class EventKind(StrEnum):
    STARTED = "started"
    PROGRESS = "progress"
    APPROVAL_REQUIRED = "approval_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentEvent(Record):
    build_id: UUID
    sequence: int = Field(ge=0)
    kind: EventKind
    message: str


class AgentProvider(Protocol):
    """Adapters emit ordered events; never hold push/merge/deploy credentials.

    A production worker supplies OS isolation. An SDK permission callback alone
    is not a sandbox. Durable event storage and cancellation are worker duties.
    """

    def run(self, request: AgentRequest) -> AsyncIterator[AgentEvent]: ...

    async def cancel(self, build_id: UUID) -> None: ...
