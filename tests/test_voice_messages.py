from unittest.mock import Mock

import pytest
from shiboken6 import delete

from aedrova.desktop.account import AccountJob
from aedrova.desktop.conversation import Composer
from aedrova.desktop.voice_messages import VoiceMessage, VoicePlayer, encode_voice
from aedrova.identity.file_policy import inspect_file


def test_voice_policy_bounds_and_integrity():
    data = encode_voice(b"\0\0" * 16000)
    assert inspect_file("voice.wav", data) == "audio/wav"
    for bad in (data[:-2], data + b"junk", b"not audio"):
        with pytest.raises(ValueError):
            inspect_file("voice.wav", bad)
    for bad in (b"\0" * 31999, b"\0" * 9600002, b""):
        with pytest.raises(ValueError):
            encode_voice(bad)


def setup(qtbot):
    composer = Composer()
    qtbot.addWidget(composer)
    scope = [(Mock(), "user", "workspace", "channel", None)]
    share = Mock(return_value=True)
    control = VoiceMessage(composer, lambda: scope[0], share)
    composer.dictation = control
    control.scope = scope[0]
    control.state = "listening"
    control.pcm.extend(b"\0\0" * 16000)
    return composer, control, share, scope


def test_preview_never_uploads_until_send_and_clears_local_audio(qtbot):
    composer, control, share, _ = setup(qtbot)
    composer.editor.setPlainText("Keep my typed draft")
    control.finish()
    assert control.state == "preview"
    path = control.preview.path
    assert path.exists()
    share.assert_not_called()
    share.return_value = False
    control.send_recording()
    assert control.state == "preview" and path.exists()
    share.return_value = True
    control.send_recording()
    assert control.state == "uploading" and path.exists()
    share.call_args.args[3]({"shared": False})
    assert control.state == "preview" and path.exists()
    control.send_recording()
    share.call_args.args[3]({"shared": True})
    assert control.state == "idle" and not path.exists() and not control.recording
    assert composer.editor.toPlainText() == "Keep my typed draft"
    assert share.call_args.args[0] == "voice-message-1s.wav"


def test_scope_change_discards_unsent_preview(qtbot):
    _, control, share, scope = setup(qtbot)
    control.finish()
    path = control.preview.path
    scope[0] = None
    control.check_scope()
    assert control.state == "idle" and not path.exists()
    share.assert_not_called()


def test_dispose_releases_recording_immediately_and_can_repeat(qtbot):
    parent = Composer()
    qtbot.addWidget(parent)
    player = VoicePlayer(encode_voice(b"\0\0" * 16000), parent)
    path = player.path
    assert path.exists()
    player.dispose()
    assert not path.exists() and not path.parent.exists()
    player.dispose()


def test_recording_cancel_has_no_network_or_ai_operation(qtbot):
    _, control, share, _ = setup(qtbot)
    control.cancel()
    assert not control.pcm and not control.recording
    share.assert_not_called()
    control.devices.permission = Mock()
    control.run = Mock()
    control.start()
    control.devices.permission.assert_called_once()
    control.run.assert_not_called()
    control.cancel()


def test_background_job_after_destroyed_signal_is_safe(qtbot):
    operation = Mock(return_value={"ok": True})
    job = AccountJob(operation)
    delete(job.signals)
    job.run()
    operation.assert_called_once()
    assert job.operation is None


def test_native_float_stereo_conversion_is_chunk_safe():
    import math
    from array import array

    from aedrova.desktop.voice_pcm import VoicePCM

    samples = array("f")
    for i in range(4800):
        sample = 0.2 * math.sin(2 * math.pi * 440 * i / 48000)
        samples.extend([sample, sample])
    raw = samples.tobytes()
    whole = VoicePCM(48000, 2, "Float").convert(raw)
    stream = VoicePCM(48000, 2, "Float")
    pieces = b"".join(stream.convert(raw[i : i + 137]) for i in range(0, len(raw), 137))
    assert pieces == whole and not stream.pending
    pcm = array("h")
    pcm.frombytes(whole)
    assert 6000 < max(pcm) < 7000
    assert 3100 <= len(whole) <= 3300


def test_full_five_minutes_fit_existing_upload_limit():
    from aedrova.identity.file_policy import MAX_BYTES

    data = encode_voice(b"\0\0" * 16000 * 300)
    assert len(data) < MAX_BYTES
    assert inspect_file("voice.wav", data) == "audio/wav"


def test_waveform_samples_verified_audio_and_bounds_malformed_input():
    import math
    import struct

    from aedrova.desktop.voice_waveform import levels

    pcm = b"\0\0" * 16000 + b"".join(
        struct.pack("<h", int(12000 * math.sin(i * 0.1))) for i in range(16000)
    )
    sampled = levels(encode_voice(pcm))
    assert len(sampled) == 30
    assert all(0.08 <= value <= 1 for value in sampled)
    assert max(sampled[:15]) == 0.08
    assert max(sampled[15:]) == 1
    assert levels(b"not a recording") == ()
    assert levels(encode_voice(b"\0\0" * 16000)) == (0.08,) * 30
