"""Local microphone chunks only. Consent transitions discard incomplete buffers."""

import io
import wave
from dataclasses import dataclass
from uuid import uuid4

from aedrova.meetings.consent import same_capture


@dataclass(frozen=True)
class SpeechChunk:
    identifier: str
    permit: object
    audio: bytes
    offset_ms: int


class MicrophoneBuffer:
    def __init__(self):
        self.permit = None
        self.pcm = bytearray()
        self.offset = 0

    def reset(self):
        self.pcm.clear()
        self.permit = None

    def feed(self, data, permit, offset_ms):
        if not same_capture(self.permit, permit):
            self.reset()
            self.permit = permit
            self.offset = offset_ms
        if permit is None:
            return None
        if not isinstance(data, bytes) or len(data) % 2 or len(data) > 32000:
            self.reset()
            raise ValueError('Invalid 16 kHz mono microphone frame')
        if not self.pcm:
            self.offset = offset_ms
        self.pcm.extend(data)
        if len(self.pcm) < 320000:
            return None
        pcm = bytes(self.pcm[:320000])
        # No backlog and no raw audio file. Drop remainder, at most one frame.
        self.pcm.clear()
        result = io.BytesIO()
        with wave.open(result, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(pcm)
        return SpeechChunk(str(uuid4()), permit, result.getvalue(), self.offset)
