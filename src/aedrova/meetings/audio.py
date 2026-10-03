"""Bounded local audio checks. Microphone samples are measured, never retained."""

import math
import struct

SAMPLES = {'UInt8': ('B', 1, 128), 'Int16': ('h', 2, 32768),
           'Int32': ('i', 4, 2147483648), 'Float': ('f', 4, 1)}


def audio_level(data, kind):
    spec = SAMPLES.get(kind)
    if not spec:
        return 0
    code, width, scale = spec
    data = data[:65536]
    data = data[:len(data) - len(data) % width]
    if not data:
        return 0
    squares = []
    for (sample,) in struct.iter_unpack('<' + code, data):
        value = (sample - 128) / scale if kind == 'UInt8' else sample / scale
        if math.isfinite(value):
            squares.append(min(abs(value), 1) ** 2)
    return min(100, round(math.sqrt(sum(squares) / len(squares)) * 100)) if squares else 0


def speaker_tone(sample_rate, channels, kind, duration=.6):
    if kind not in SAMPLES or not 8000 <= sample_rate <= 192000 or not 1 <= channels <= 8:
        raise ValueError('Unsupported speaker format')
    if not 0 < duration <= 2:
        raise ValueError('Speaker test must be brief')
    code, _, scale = SAMPLES[kind]
    data = bytearray()
    count = int(sample_rate * duration)
    for index in range(count):
        fade = min(1, index / (sample_rate * .02), (count - index) / (sample_rate * .03))
        value = .12 * fade * math.sin(2 * math.pi * 440 * index / sample_rate)
        sample = value if kind == 'Float' else round(value * (scale - 1))
        if kind == 'UInt8':
            sample += 128
        data.extend(struct.pack('<' + code, sample) * channels)
    return bytes(data)
