import asyncio
import io
import time
import wave
from dataclasses import replace
from types import SimpleNamespace

import pytest
from test_meeting_context import segment, source_context

from aedrova.agents.retrieval import ContextIndex
from aedrova.desktop.meeting_transcript import TranscriptReview
from aedrova.meetings.call import CallWorker
from aedrova.meetings.consent import CapturePermit
from aedrova.meetings.speech import MicrophoneBuffer


def permit():
    return CapturePermit('meeting', 1, frozenset({'user'}), True)


def test_bounded_pcm_and_revision_discard():
    buffer = MicrophoneBuffer()
    first, second = permit(), replace(permit(), revision=2)
    for _ in range(9):
        assert buffer.feed(b'\1\0' * 16000, first, 0) is None
    assert buffer.feed(b'\2\0' * 16000, second, 9000) is None
    for _ in range(8):
        assert buffer.feed(b'\2\0' * 16000, second, 9000) is None
    chunk = buffer.feed(b'\2\0' * 16000, second, 18000)
    with wave.open(io.BytesIO(chunk.audio)) as wav:
        assert wav.getnframes() == 160000
        assert wav.readframes(160000) == b'\2\0' * 160000
    assert chunk.offset_ms == 9000 and chunk.permit == second and not buffer.pcm
    buffer.feed(b'\0\0' * 16000, first, 0)
    buffer.feed(b'\0\0' * 16000, None, 0)
    assert not buffer.pcm and buffer.permit is None


def test_microphone_rejects_wrong_frame_size():
    with pytest.raises(ValueError):
        MicrophoneBuffer().feed(b'\0' * 32002, permit(), 0)


def test_speech_context_requires_review_and_keeps_provenance():
    row = segment() | dict(source='provider_speech')
    with pytest.raises(PermissionError):
        ContextIndex(source_context(row))
    row.update(reviewed_at='2026-10-03T12:00:00Z', reviewed_by='reviewer', confirmed_decision=True)
    evidence = ContextIndex(source_context(row)).sources[0]
    assert evidence.decision == 'confirmed_meeting_decision'
    assert evidence.confirmed_by == 'reviewer'


def test_worker_requires_opt_in_fresh_consent_unmuted_and_same_roster():
    worker = CallWorker(None, workspace='w', channel='c', user='user')
    worker.connected = worker.speech_available = True
    worker.microphone = object()
    worker.room = SimpleNamespace(remote_participants={})
    worker.update_consent(dict(id='meeting', revision=1, participants=[dict(user_id='user',
        transcription=True, ai_context=True)]))
    assert worker.speech_permit() is None
    worker.speech_requested = True
    assert worker.speech_permit() == permit()
    worker.room.remote_participants['new-person'] = object()
    assert worker.speech_permit() is None
    worker.room.remote_participants.clear()
    worker.snapshot_at = time.monotonic() - 11
    assert worker.speech_permit() is None
    worker.update_consent(worker.snapshot)
    worker.microphone = None
    assert worker.speech_permit() is None
    states = []
    worker.transcription_state.connect(states.append)
    worker.pause_speech()
    worker.pause_speech()
    assert len(states) == 1 and not worker.speech_requested


def test_transcript_review_paging_version_save_and_error_clear(qtbot):
    class Client:
        def __init__(self):
            self.saved, self.failed = [], False
        def transcript(self, meeting, page):
            if self.failed:
                raise PermissionError('revoked')
            return [segment() | dict(review_version=3)] * (50 if page == 0 else 1)
        def review(self, *values):
            self.saved.append(values)
    client = Client()
    dialog = TranscriptReview(None, client, meeting='meeting')
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitUntil(lambda: not dialog.busy and len(dialog.rows) == 50)
    assert dialog.next.isEnabled() and not dialog.previous.isEnabled()
    dialog.edit.setPlainText('Corrected')
    dialog.decision.setChecked(True)
    dialog.review()
    qtbot.waitUntil(lambda: bool(client.saved) and not dialog.busy)
    assert client.saved == [('segment', 3, 'Corrected', True)]
    dialog.turn(1)
    qtbot.waitUntil(lambda: not dialog.busy and len(dialog.rows) == 1)
    assert dialog.previous.isEnabled() and not dialog.next.isEnabled()
    client.failed = True
    dialog.load()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert not dialog.rows and not dialog.edit.toPlainText() and not dialog.original.toPlainText()
    dialog.reject()


def test_native_livekit_local_track_stream_without_hardware():
    from livekit import rtc
    async def check():
        source = rtc.AudioSource(16000, 1)
        track = rtc.LocalAudioTrack.create_audio_track('offline-test', source)
        stream = rtc.AudioStream(track, capacity=1, sample_rate=16000, num_channels=1)
        async def feed():
            for _ in range(5):
                frame = rtc.AudioFrame.create(16000, 1, 1600)
                await source.capture_frame(frame)
                await asyncio.sleep(.01)
        task = asyncio.create_task(feed())
        try:
            event = await asyncio.wait_for(stream.__anext__(), 3)
            assert event.frame.sample_rate == 16000 and event.frame.num_channels == 1
        finally:
            await task
            await stream.aclose()
            await source.aclose()
    asyncio.run(check())


def test_capture_loop_sends_only_complete_current_chunk(monkeypatch):
    from livekit import rtc
    async def check():
        sent = []
        worker = CallWorker(SimpleNamespace(transcribe=lambda m, c: sent.append((m, c))),
                            workspace='w', channel='c', user='user')
        worker.connected = worker.speech_available = worker.speech_requested = True
        worker.microphone = worker.local_audio_track = object()
        worker.meeting = 'meeting'
        worker.room = SimpleNamespace(remote_participants={})
        snapshot = dict(id='meeting', revision=1, participants=[dict(user_id='user',
            transcription=True, ai_context=True)])
        worker.update_consent(snapshot)
        class Stream:
            closed = False
            def __init__(self, *a, **kw):
                assert kw['capacity'] == 1
                self.index = 0
            def __aiter__(self):
                return self
            async def __anext__(self):
                self.index += 1
                if self.index > 19:
                    raise StopAsyncIteration
                if self.index == 10:
                    worker.update_consent(snapshot | {'revision': 2})
                return SimpleNamespace(frame=SimpleNamespace(data=b'\0\0' * 16000))
            async def aclose(self):
                self.closed = True
        monkeypatch.setattr(rtc, 'AudioStream', Stream)
        await worker._transcribe_microphone()
        assert len(sent) == 1 and sent[0][1].permit.revision == 2
        worker.pause_speech()
        assert not worker.speech_requested
    asyncio.run(check())
