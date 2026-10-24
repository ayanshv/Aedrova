from aedrova.desktop.attachment_draft import stage
from aedrova.desktop.conversation import Composer


def test_attachment_waits_for_send(qtbot, tmp_path):
    composer = Composer()
    qtbot.addWidget(composer)
    path = tmp_path / 'notes.txt'
    path.write_text('draft')
    sent = []
    assert stage(composer, path, lambda: sent.append(path))
    assert sent == []
    assert composer.send.isEnabled()
    composer._submit()
    assert sent == [path]
    assert composer.attachment_drafts == []
