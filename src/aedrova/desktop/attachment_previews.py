"""Small private image/text previews. No remote URL fetch, HTML, scripts or document execution."""

from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtGui import QImageReader, QPixmap

from aedrova.identity.file_policy import TEXT, inspect_file


def preview_height(name):
    suffix = Path(name).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg"}:
        return 170
    if suffix in TEXT:
        return 112
    return 58


class AttachmentPreviews(QObject):
    def __init__(self, window, connected, scope):
        super().__init__(window)
        self.window, self.connected, self.scope = window, connected, scope
        self.cache, self.pending = {}, set()
        self.origin = None
        self.epoch = 0
        for view in (window.messages, window.thread_messages):
            view.attachment_previews = self.cache

    def clear(self):
        self.epoch += 1
        self.cache.clear()
        self.pending.clear()
        self.origin = None

    def load(self, messages):
        origin = self.scope()
        if origin != self.origin:
            self.clear()
            self.origin = origin
        connected = self.connected()
        if not connected:
            return
        epoch = self.epoch
        # Only a bounded tail; never fetch the whole workspace or an external link.
        for message in list(messages)[-8:]:
            identifier, name = message.attachment_id, message.attachment
            if (
                not identifier
                or identifier in self.cache
                or identifier in self.pending
                or preview_height(name) == 58
            ):
                continue
            self.pending.add(identifier)
            service = connected.account.service

            def loaded(data, i=identifier, n=name):
                if epoch != self.epoch or self.scope() != origin:
                    return
                self.pending.discard(i)
                try:
                    if data is None:
                        raise ValueError("Unavailable")
                    kind = inspect_file(n, data)
                    if kind.startswith("image/"):
                        QImageReader.setAllocationLimit(64)
                        pixmap = QPixmap()
                        if not pixmap.loadFromData(data):
                            raise ValueError("Invalid image")
                        from PySide6.QtCore import Qt

                        self.cache[i] = pixmap.scaled(
                            320,
                            126,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    elif kind == "text/plain":
                        self.cache[i] = data.decode("utf-8-sig")[:400]
                except ValueError:
                    self.cache[i] = "Preview unavailable · click to open"
                while len(self.cache) > 16:
                    self.cache.pop(next(iter(self.cache)))
                for view in (self.window.messages, self.window.thread_messages):
                    view.viewport().update()

            def download(i=identifier, s=service):
                try:
                    return s.download_attachment(i)
                except Exception:
                    return None

            if not connected.enqueue(
                ("file-preview", identifier),
                download,
                loaded,
            ):
                self.pending.discard(identifier)
