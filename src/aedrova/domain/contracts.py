"""Milestone 1 contracts. Persistence and service enforcement arrive in later milestones."""

from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Record(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"


class Membership(Record):
    workspace_id: UUID
    user_id: UUID
    role: Role
    active: bool = True


class ChannelPolicy(Record):
    workspace_id: UUID
    channel_id: UUID
    readers: frozenset[UUID]
    builders: frozenset[UUID] = frozenset()
    ai_enabled: bool = False

    @model_validator(mode="after")
    def builders_can_read(self) -> Self:
        if not self.builders <= self.readers:
            raise ValueError("Channel builders must also be readers")
        return self


def can_invoke(member: Membership, channel: ChannelPolicy) -> bool:
    return (
        member.active
        and member.workspace_id == channel.workspace_id
        and member.user_id in channel.builders
        and channel.ai_enabled
    )


class SourceKind(StrEnum):
    MESSAGE = "message"
    DECISION = "decision"
    DOCUMENT = "document"
    REPOSITORY = "repository"
    TRANSCRIPT = "transcript"


class ContextSource(Record):
    source_id: UUID
    workspace_id: UUID
    project_id: UUID
    kind: SourceKind
    revision: int = Field(ge=1)
    text: str = Field(min_length=1)
    readers: frozenset[UUID]
    ai_allowed: bool = False
    deleted: bool = False
    superseded: bool = False
    updated_at: AwareDatetime


def select_context(
    sources: tuple[ContextSource, ...],
    *,
    member: Membership,
    destination: ChannelPolicy,
    project_id: UUID,
) -> tuple[ContextSource, ...]:
    """Fail closed; caller must supply CURRENT ACLs, not cached client assertions.

    Restrict to sources visible to every destination reader. This conservative
    policy prevents private context leaking through a public agent response.
    """
    if not can_invoke(member, destination):
        raise PermissionError("Member cannot invoke AI in this destination")
    return tuple(
        source
        for source in sources
        if source.workspace_id == member.workspace_id
        and source.project_id == project_id
        and source.ai_allowed
        and not source.deleted
        and not source.superseded
        and destination.readers <= source.readers
    )


class ContextPackage(Record):
    workspace_id: UUID
    project_id: UUID
    requested_by: UUID
    destination_id: UUID
    request: str = Field(min_length=1)
    acceptance_criteria: tuple[str, ...] = Field(min_length=1)
    sources: tuple[ContextSource, ...]
    created_at: AwareDatetime

    @model_validator(mode="after")
    def validate_sources(self) -> Self:
        for source in self.sources:
            if (source.workspace_id, source.project_id) != (self.workspace_id, self.project_id):
                raise ValueError("Context package cannot mix workspaces or projects")
            if not source.ai_allowed or source.deleted or source.superseded:
                raise ValueError("Context package contains an ineligible source")
            if self.requested_by not in source.readers:
                raise ValueError("Requester cannot read this source")
        return self


class BuildState(StrEnum):
    REQUESTED = "requested"
    PLANNING = "planning"
    AWAITING_PLAN = "awaiting_plan"
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TRANSITIONS = {
    BuildState.REQUESTED: {BuildState.PLANNING, BuildState.CANCELLED},
    BuildState.PLANNING: {BuildState.AWAITING_PLAN, BuildState.FAILED, BuildState.CANCELLED},
    BuildState.AWAITING_PLAN: {BuildState.QUEUED, BuildState.CANCELLED},
    BuildState.QUEUED: {BuildState.RUNNING, BuildState.FAILED, BuildState.CANCELLED},
    BuildState.RUNNING: {BuildState.AWAITING_REVIEW, BuildState.FAILED, BuildState.CANCELLED},
    BuildState.AWAITING_REVIEW: {
        BuildState.SUCCEEDED,
        BuildState.RUNNING,
        BuildState.CANCELLED,
    },
    BuildState.SUCCEEDED: set(),
    BuildState.FAILED: set(),
    BuildState.CANCELLED: set(),
}


def transition(current: BuildState, target: BuildState) -> BuildState:
    """Validate graph only; authorization and atomic persistence are service duties."""
    if target not in TRANSITIONS[current]:
        raise ValueError(f"Invalid build transition: {current} -> {target}")
    return target


class ExternalAction(StrEnum):
    PUSH = "push"
    MERGE = "merge"
    DEPLOY = "deploy"


class ActionScope(Record):
    workspace_id: UUID
    build_id: UUID
    action: ExternalAction
    repository: str = Field(min_length=1)
    target: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    artifact_digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    def fingerprint(self) -> str:
        return sha256(self.model_dump_json().encode()).hexdigest()


class Approval(Record):
    approval_id: UUID
    scope: ActionScope
    approved_by: UUID
    expires_at: AwareDatetime
    revoked: bool = False

    def permits(self, scope: ActionScope, *, actor: Membership, now: datetime) -> bool:
        if now.tzinfo is None:
            raise ValueError("Approval checks require timezone-aware timestamps")
        return (
            not self.revoked
            and now < self.expires_at
            and actor.active
            and actor.workspace_id == scope.workspace_id
            and actor.user_id == self.approved_by
            and actor.role in {Role.OWNER, Role.ADMIN}
            and self.scope.fingerprint() == scope.fingerprint()
        )
