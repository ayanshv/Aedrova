"""Local attachment cards; network publication starts only on explicit Send."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton


def stage(composer, path, publish):
    drafts = getattr(composer, "attachment_drafts", [])
    if len(drafts) >= 10:
        return False
    card = QFrame(composer)
    card.setObjectName("AttachmentDraft")
    row = QHBoxLayout(card)
    preview = QLabel()
    image = (
        QPixmap(str(path))
        if Path(path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        else QPixmap()
    )
    if not image.isNull():
        preview.setPixmap(
            image.scaled(
                64,
                64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        row.addWidget(preview)
    name = QLabel(Path(path).name)
    name.setTextFormat(Qt.TextFormat.PlainText)
    row.addWidget(name, 1)
    remove = QPushButton("×")
    remove.setToolTip("Remove attachment")
    row.addWidget(remove)
    entry = (card, publish)
    drafts.append(entry)
    composer.attachment_drafts = drafts

    def discard():
        if entry in drafts:
            drafts.remove(entry)
        card.deleteLater()
        composer._changed()

    remove.clicked.connect(discard)
    composer.layout().insertWidget(1, card)
    composer._changed()
    return True
