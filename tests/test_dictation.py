from unittest.mock import Mock

from aedrova.desktop.conversation import Composer
from aedrova.desktop.dictation import Dictation


def setup(qtbot):
    composer = Composer()
    qtbot.addWidget(composer)
    scope = [Mock(), "user", "workspace", "channel", None]
    current = [tuple(scope)]
    control = Dictation(composer, lambda: current[0])
    jobs = []
    control.run = lambda operation, callback: jobs.append((operation, callback))
    control.scope = current[0]
    control.client = Mock()
    control.state = "listening"
    control.pcm.extend(b"\1\0" * 16000)
    return composer, control, jobs, current


def test_dictation_appends_to_editable_draft_without_sending(qtbot):
    composer, control, jobs, _ = setup(qtbot)
    sent = []
    composer.submitted.connect(sent.append)
    composer.editor.setPlainText("Existing draft")
    control.finish()
    assert control.state == "processing" and not control.pcm and control.source is None
    composer.editor.setPlainText("Existing draft and edits")
    jobs[0][1]({"text": "dictated words"}, True)
    assert composer.editor.toPlainText() == "Existing draft and edits dictated words"
    assert not sent and control.state == "idle"


def test_cancel_or_channel_change_discards_late_result(qtbot):
    composer, control, jobs, current = setup(qtbot)
    control.finish()
    current[0] = None
    control.check_scope()
    jobs[0][1]({"text": "private words"}, True)
    assert composer.editor.toPlainText() == "" and control.state == "idle"
    assert not control.pcm and control.scope is None


def test_cancel_before_microphone_permission_invalidates_callback(qtbot):
    _, control, _, _ = setup(qtbot)
    epoch = control.epoch
    control.cancel()
    control.capture(epoch, True)
    assert control.source is None and not control.pcm


def test_short_speech_and_provider_failure_preserve_draft(qtbot):
    composer, control, jobs, _ = setup(qtbot)
    composer.editor.setPlainText("Keep this")
    control.pcm.clear()
    control.finish()
    assert control.state == "error" and not jobs
    control.state = "listening"
    control.pcm.extend(b"\0\0" * 16000)
    control.finish()
    jobs[0][1]({}, False)
    assert composer.editor.toPlainText() == "Keep this"
    assert control.state == "error" and control.mic.isEnabled()


def test_disabled_service_never_requests_microphone(qtbot):
    _, control, jobs, _ = setup(qtbot)
    control.cancel()
    control.devices.permission = Mock()
    control.start()
    jobs[0][1]((Mock(), False), True)
    control.devices.permission.assert_not_called()
    assert control.state == "error" and control.source is None


def test_sending_stops_recording_and_discards_late_text(qtbot):
    composer, control, jobs, _ = setup(qtbot)
    composer.dictation = control
    composer.editor.setPlainText("Send my typed draft")
    control.finish()
    composer._submit()
    jobs[0][1]({"text": "Late words"}, True)
    assert composer.editor.toPlainText() == "Send my typed draft"
    assert control.state == "idle"
