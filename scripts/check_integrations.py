"""Credential-free SDK handshake and synthetic media checks. No model/camera calls."""

import asyncio
import json
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from livekit import rtc
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QAudioFormat, QMediaCaptureSession, QVideoFrame


async def main():
    # Initialize the actual bundled agent runtime without submitting a model prompt.
    with TemporaryDirectory(prefix="aedrova-sdk-") as checkout:
        options = ClaudeAgentOptions(
            cwd=checkout,
            setting_sources=[],
            tools=[],
            allowed_tools=[],
            permission_mode="default",
            max_turns=1,
        )
        async with asyncio.timeout(30):
            async with ClaudeSDKClient(options=options) as client:
                info = await client.get_server_info()
                if not info:
                    raise RuntimeError("Agent initialization returned no server information")
    width, height = 64, 48
    pixels = bytes([32, 96, 160, 255]) * width * height
    frame = rtc.VideoFrame(width, height, rtc.VideoBufferType.RGBA, pixels)
    converted = frame.convert(rtc.VideoBufferType.BGRA)
    image = QImage(bytes(converted.data), width, height, width * 4, QImage.Format.Format_ARGB32)
    assert not image.isNull()
    assert image.pixelColor(0, 0).red() == 32
    audio = rtc.AudioFrame.create(sample_rate=48_000, num_channels=1, samples_per_channel=480)
    assert len(audio.data) == 480
    assert QAudioFormat and QMediaCaptureSession and QVideoFrame
    report = {
        "claude_sdk_version": version("claude-agent-sdk"),
        "agent_runtime_handshake": "passed (no model request)",
        "livekit_version": version("livekit"),
        "synthetic_video_to_qt": "passed, RGBA -> BGRA -> QImage",
        "synthetic_audio": "passed, 48kHz mono 10ms frame",
        "qt_multimedia_imports": "passed",
        "not_tested": [
            "paid model call",
            "live meeting connection",
            "camera/microphone capture",
            "screen sharing",
            "network loss/echo cancellation", 
        ],
    }
    Path("work").mkdir(exist_ok=True)
    Path("work/integrations.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
