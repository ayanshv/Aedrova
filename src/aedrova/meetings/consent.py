"""Fail-closed capture barrier: consent is server-derived, separate from call joining.

This is not a substitute for backend authorization. Media/transcription code must check
this barrier before every chunk and discard unfinished buffers on any revision change.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CapturePermit:
    meeting_id: str
    revision: int
    participants: frozenset[str]
    ai_allowed: bool


def capture_permit(snapshot, live_participants):
    """No recording grant is inferred; only audio transcription and optional AI reuse."""
    participants = snapshot.get('participants', [])
    if (not isinstance(participants, list) or not isinstance(snapshot.get('id'), str)
            or not snapshot['id'] or any(not isinstance(p, dict)
            or not isinstance(p.get('user_id'), str) or not p['user_id']
            for p in participants)):
        return None
    identifiers = [p['user_id'] for p in participants]
    if (snapshot.get('ended') or not participants or len(set(identifiers)) != len(identifiers)
            or set(identifiers) != set(live_participants)
            or any(p.get('transcription') is not True for p in participants)):
        return None
    revision = snapshot.get('revision')
    if type(revision) is not int or revision < 1:
        return None
    return CapturePermit(snapshot['id'], revision, frozenset(identifiers),
                         all(p.get('ai_context') is True for p in participants))


def same_capture(before, after):
    """Reject chunks crossing join/leave/revocation, even if consent is restored."""
    return before is not None and before == after
