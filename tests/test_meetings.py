import base64
import json
from uuid import uuid4

import pytest

from aedrova.meetings.access import MeetingAccess
from aedrova.meetings.consent import capture_permit, same_capture


def snapshot():
    return {'id': 'meeting', 'revision': 3, 'ended': False, 'participants': [
        {'user_id': 'host', 'transcription': True, 'ai_context': True},
        {'user_id': 'peer', 'transcription': True, 'ai_context': False}]}


def test_unanimous_transcription_is_separate_from_ai_reuse():
    value = snapshot()
    permit = capture_permit(value, {'host', 'peer'})
    assert permit is not None and not permit.ai_allowed
    value['participants'][1]['ai_context'] = True
    assert capture_permit(value, {'host', 'peer'}).ai_allowed


@pytest.mark.parametrize('change', ['late_join', 'lease_expiry', 'no_consent', 'ended',
                                     'duplicate', 'empty'])
def test_capture_fails_closed(change):
    value = snapshot()
    if change == 'late_join':
        live = {'host', 'peer', 'new'}
    else:
        live = {'host', 'peer'}
    if change == 'lease_expiry':
        value['participants'].pop()
    elif change == 'no_consent':
        value['participants'][1]['transcription'] = False
    elif change == 'ended':
        value['ended'] = True
    elif change == 'duplicate':
        value['participants'].append(value['participants'][0])
    elif change == 'empty':
        value['participants'] = []
    assert capture_permit(value, live) is None


def test_revocation_and_restore_cannot_save_an_inflight_chunk():
    value = snapshot()
    first = capture_permit(value, {'host', 'peer'})
    value['revision'] += 2
    assert not same_capture(first, capture_permit(value, {'host', 'peer'}))
    assert same_capture(first, first)
    assert not same_capture(None, None)


def fixture_access():
    workspace, channel, user, meeting = (str(uuid4()) for _ in range(4))
    claims = {'sub': user, 'exp': 1200, 'video': {'roomJoin': True,
        'room': f'aedrova-{workspace}-{channel}-{meeting}', 'canPublishData': False}}
    def token(payload):
        return 'header.' + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode() + '.sig'
    return {'meeting_id': meeting, 'workspace_id': workspace, 'channel_id': channel,
            'user_id': user, 'url': 'wss://example.livekit.cloud', 'token': token(claims),
            'expires_at': 1200}, claims, token


def test_access_is_scoped_short_lived_and_credentials_are_not_repr():
    result, _, _ = fixture_access()
    access = MeetingAccess.parse(result, workspace=result['workspace_id'],
        channel=result['channel_id'], user=result['user_id'], now=1000)
    assert result['token'] not in repr(access)


@pytest.mark.parametrize('kind', ['workspace', 'user', 'room', 'admin', 'data', 'expired',
                                  'long_lived', 'insecure', 'bad_token'])
def test_misrouted_or_invalid_access_never_starts_devices(kind):
    result, claims, token = fixture_access()
    expected = {'workspace': result['workspace_id'], 'channel': result['channel_id'],
                'user': result['user_id'], 'now': 1000}
    if kind == 'workspace':
        result['workspace_id'] = str(uuid4())
    elif kind == 'user':
        claims['sub'] = str(uuid4())
    elif kind == 'room':
        claims['video']['room'] = 'other-workspace'
    elif kind == 'admin':
        claims['video']['roomAdmin'] = True
    elif kind == 'data':
        claims['video']['canPublishData'] = True
    elif kind == 'expired':
        result['expires_at'] = claims['exp'] = 999
    elif kind == 'long_lived':
        result['expires_at'] = claims['exp'] = 1500
    elif kind == 'insecure':
        result['url'] = 'ws://example.livekit.cloud'
    result['token'] = 'broken' if kind == 'bad_token' else token(claims)
    with pytest.raises(RuntimeError, match='No device was started'):
        MeetingAccess.parse(result, **expected)


@pytest.mark.parametrize('participants', [None, {}, [{}], [{'user_id': 'host',
    'transcription': 'false'}]])
def test_malformed_consent_fails_closed(participants):
    value = snapshot()
    value['participants'] = participants
    assert capture_permit(value, {'host'}) is None


@pytest.mark.parametrize('status', [401, 403])
def test_transport_authentication_diagnostic_never_echoes_credentials(status):
    from aedrova.meetings.access import transport_failure
    error = RuntimeError('fixture-sensitive-token-must-not-appear')
    error.status = status
    result = transport_failure(error)
    assert 'same project' in result
    assert 'fixture-sensitive' not in result


def test_nested_transport_authentication_failure_is_classified():
    from aedrova.meetings.access import transport_failure
    error = RuntimeError('cleanup failure')
    original = RuntimeError('private provider response')
    original.status = 401
    error.__context__ = original
    assert 'same project' in transport_failure(error)
    assert 'private provider' not in transport_failure(error)
    assert 'did not pass' in transport_failure(TimeoutError('private-url'))
