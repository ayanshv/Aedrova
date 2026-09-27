from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aedrova.domain.contracts import (
    ActionScope,
    Approval,
    BuildState,
    ChannelPolicy,
    ContextPackage,
    ContextSource,
    ExternalAction,
    Membership,
    Role,
    SourceKind,
    can_invoke,
    select_context,
    transition,
)


@pytest.fixture
def scenario():
    user, teammate, workspace, project = (uuid4() for _ in range(4))
    member = Membership(workspace_id=workspace, user_id=user, role=Role.ADMIN)
    channel = ChannelPolicy(
        workspace_id=workspace,
        channel_id=uuid4(),
        readers={user, teammate},
        builders={user},
        ai_enabled=True,
    )
    source = ContextSource(
        source_id=uuid4(),
        workspace_id=workspace,
        project_id=project,
        kind=SourceKind.DECISION,
        revision=1,
        text="Build the three-step onboarding",
        readers={user, teammate},
        ai_allowed=True,
        updated_at=datetime.now(UTC),
    )
    return member, channel, source


def test_context_is_visible_to_requester_and_entire_destination(scenario):
    member, channel, source = scenario
    private = source.model_copy(update={"source_id": uuid4(), "readers": {member.user_id}})
    selected = select_context(
        (source, private),
        member=member,
        destination=channel,
        project_id=source.project_id,
    )
    assert selected == (source,)


@pytest.mark.parametrize(
    "change",
    [
        {"workspace_id": uuid4()},
        {"project_id": uuid4()},
        {"deleted": True},
        {"superseded": True},
        {"ai_allowed": False},
        {"readers": frozenset()},
    ],
)
def test_context_excludes_ineligible_sources(scenario, change):
    member, channel, source = scenario
    assert (
        select_context(
            (source.model_copy(update=change),),
            member=member,
            destination=channel,
            project_id=source.project_id,
        )
        == ()
    )


@pytest.mark.parametrize(
    "member_change,channel_change",
    [
        ({"active": False}, {}),
        ({"workspace_id": uuid4()}, {}),
        ({}, {"ai_enabled": False}),
        ({}, {"builders": frozenset()}),
    ],
)
def test_invocation_fails_closed(scenario, member_change, channel_change):
    member, channel, source = scenario
    member = member.model_copy(update=member_change)
    channel = channel.model_copy(update=channel_change)
    assert not can_invoke(member, channel)
    with pytest.raises(PermissionError):
        select_context((source,), member=member, destination=channel, project_id=source.project_id)


def test_builders_must_be_readers(scenario):
    _, channel, _ = scenario
    with pytest.raises(ValidationError):
        ChannelPolicy(**(channel.model_dump() | {"builders": {uuid4()}}))


def test_context_cannot_cross_tenants(scenario):
    member, channel, source = scenario
    with pytest.raises(ValidationError):
        ContextPackage(
            workspace_id=uuid4(),
            project_id=source.project_id,
            requested_by=member.user_id,
            destination_id=channel.channel_id,
            request="Build onboarding",
            acceptance_criteria=("Three steps",),
            sources=(source,),
            created_at=datetime.now(UTC),
        )


def test_build_lifecycle_and_terminal_states():
    path = [
        BuildState.REQUESTED,
        BuildState.PLANNING,
        BuildState.AWAITING_PLAN,
        BuildState.QUEUED,
        BuildState.RUNNING,
        BuildState.AWAITING_REVIEW,
        BuildState.SUCCEEDED,
    ]
    for before, after in zip(path, path[1:], strict=False):
        assert transition(before, after) == after
    for terminal in (BuildState.SUCCEEDED, BuildState.FAILED, BuildState.CANCELLED):
        with pytest.raises(ValueError):
            transition(terminal, BuildState.RUNNING)
    with pytest.raises(ValueError):
        transition(BuildState.REQUESTED, BuildState.SUCCEEDED)


@pytest.fixture
def approval(scenario):
    member, _, _ = scenario
    scope = ActionScope(
        workspace_id=member.workspace_id,
        build_id=uuid4(),
        action=ExternalAction.PUSH,
        repository="team/product",
        target="feature/onboarding",
        revision="commit-123",
        artifact_digest="a" * 64,
    )
    grant = Approval(
        approval_id=uuid4(),
        scope=scope,
        approved_by=member.user_id,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    return member, scope, grant


def test_exact_approval_and_roundtrip(approval):
    actor, scope, grant = approval
    assert grant.permits(scope, actor=actor, now=datetime.now(UTC))
    assert Approval.model_validate_json(grant.model_dump_json()) == grant


@pytest.mark.parametrize(
    "change",
    [
        {"workspace_id": uuid4()},
        {"build_id": uuid4()},
        {"action": ExternalAction.MERGE},
        {"repository": "other/repo"},
        {"target": "main"},
        {"revision": "commit-456"},
        {"artifact_digest": "b" * 64},
    ],
)
def test_approval_cannot_be_reused_for_different_action(approval, change):
    actor, scope, grant = approval
    assert not grant.permits(scope.model_copy(update=change), actor=actor, now=datetime.now(UTC))


@pytest.mark.parametrize(
    "change",
    [
        {"active": False},
        {"role": Role.MEMBER},
        {"user_id": uuid4()},
        {"workspace_id": uuid4()},
    ],
)
def test_approval_requires_current_authority(approval, change):
    actor, scope, grant = approval
    assert not grant.permits(scope, actor=actor.model_copy(update=change), now=datetime.now(UTC))


def test_expiration_revocation_and_aware_clock(approval):
    actor, scope, grant = approval
    assert not grant.permits(scope, actor=actor, now=grant.expires_at)
    assert not grant.model_copy(update={"revoked": True}).permits(
        scope,
        actor=actor,
        now=datetime.now(UTC),
    )
    with pytest.raises(ValueError):
        grant.permits(scope, actor=actor, now=datetime.now())
