"""Bounded waveform sampling and a quiet, theme-aware voice-card indicator."""

import io
import math
import struct
import wave

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor

# A neutral audio symbol until the user explicitly downloads/plays a recording.
PLACEHOLDER = tuple(0.15 + 0.7 * abs(math.sin(i * 0.63)) ** 2 for i in range(30))


def levels(data):
    """Sample an already verified mono PCM recording; never fetch audio for decoration."""
    try:
        with wave.open(io.BytesIO(data), "rb") as audio:
            frames = audio.getnframes()
            if audio.getsampwidth() != 2 or audio.getnchannels() != 1 or not 1 <= frames <= 4800000:
                return ()
            result = []
            for i in range(30):
                start, end = frames * i // 30, frames * (i + 1) // 30
                peak = 0
                for frame in range(start, end, max(1, (end - start) // 32)):
                    audio.setpos(frame)
                    sample = audio.readframes(1)
                    if len(sample) == 2:
                        peak = max(peak, abs(struct.unpack("<h", sample)[0]))
                result.append(peak / 32768)
            ceiling = max(result) or 1
            return tuple(max(0.08, value / ceiling) for value in result)
    except (wave.Error, EOFError, ValueError):
        return ()


def paint(painter, area, theme, samples=(), progress=0):
    samples = samples or PLACEHOLDER
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    step = area.width() / len(samples)
    for i, amplitude in enumerate(samples):
        height = max(3, min(1, amplitude) * area.height())
        painter.setBrush(
            QColor(theme.accent if (i + 0.5) / len(samples) <= progress else theme.secondary)
        )
        painter.drawRoundedRect(
            QRectF(
                area.x() + i * step, area.center().y() - height / 2, min(2.5, step * 0.55), height
            ),
            1.25,
            1.25,
        )
    painter.restore()
