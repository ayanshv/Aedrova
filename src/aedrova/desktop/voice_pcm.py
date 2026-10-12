"""Stream native microphone samples into mono PCM; preserve partial frames and resampler state."""

import audioop
import math
from array import array


class VoicePCM:
    def __init__(self, rate, channels, kind):
        if (
            not 8000 <= rate <= 192000
            or not 1 <= channels <= 8
            or kind not in {"UInt8", "Int16", "Int32", "Float"}
        ):
            raise ValueError("Unsupported microphone format")
        self.rate, self.channels, self.kind = rate, channels, kind
        self.width = {"UInt8": 1, "Int16": 2, "Int32": 4, "Float": 4}[kind]
        self.pending = b""
        self.resampler = None

    def convert(self, data):
        data = self.pending + data
        frame = self.width * self.channels
        length = len(data) - len(data) % frame
        data, self.pending = data[:length], data[length:]
        if not data:
            return b""
        if self.kind == "Float":
            values = array("f")
            values.frombytes(data)
            values = [max(-1, min(1, v)) if math.isfinite(v) else 0 for v in values]
            pcm = array("h", (round(v * 32767) for v in values)).tobytes()
        else:
            if self.kind == "UInt8":
                data = audioop.bias(data, 1, -128)
            pcm = audioop.lin2lin(data, self.width, 2)
        if self.channels > 1:
            values = array("h")
            values.frombytes(pcm)
            pcm = array(
                "h",
                (
                    round(sum(values[i : i + self.channels]) / self.channels)
                    for i in range(0, len(values), self.channels)
                ),
            ).tobytes()
        if self.rate != 16000:
            pcm, self.resampler = audioop.ratecv(pcm, 2, 1, self.rate, 16000, self.resampler)
        return pcm
