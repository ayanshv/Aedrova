"""Personal profiles: private avatars and a progressive, keyboard-friendly setup."""

import re
import unicodedata
from pathlib import Path

from PySide6.QtCore import (
    QBuffer,
    QByteArray,
    QEasingCurve,
    QIODevice,
    QPropertyAnimation,
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QImageReader, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.emojis import pick_emoji
from aedrova.desktop.materials import system_font


def suggested_username(name, user_id):
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "_", ascii_name).strip("_")[:22] or "member"
    return base + "_" + user_id.replace("-", "")[:6]


def validate_profile(data):
    if not 1 <= len(data["display_name"].strip()) <= 80:
        raise ValueError("Add a display name, up to 80 characters.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]{2,31}", data["username"]):
        raise ValueError("Use 3–32 lowercase letters, numbers or underscores for your username.")
    for key, limit in [("bio", 280), ("title", 80), ("status", 120)]:
        if len(data[key]) > limit:
            raise ValueError(f"Keep {key} under {limit} characters.")
    if data["availability"] not in ("online", "away", "busy"):
        raise ValueError("Choose online, away or do not disturb.")
    return data


def avatar_png(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Choose a photo under 10 MB.")
    QImageReader.setAllocationLimit(64)
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    size = reader.size()
    if not size.isValid() or size.width() * size.height() > 16_000_000:
        raise ValueError("Choose a JPG, PNG or WebP photo up to 16 megapixels.")
    image = reader.read()
    if image.isNull():
        raise ValueError("This image could not be opened. Try another photo.")
    side = min(image.width(), image.height())
    image = image.copy((image.width() - side) // 2, (image.height() - side) // 2, side, side)
    image = image.scaled(
        256, 256, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
    )
    output = QByteArray()
    buffer = QBuffer(output)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(output)


class Avatar(QWidget):
    def __init__(self, size=96, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.pixmap = QPixmap()
        self.initials = "You"
        self.setAccessibleName("Profile avatar preview")

    def set_photo(self, data):
        self.pixmap.loadFromData(data)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(QRectF(self.rect()))
        painter.setClipPath(path)
        if not self.pixmap.isNull():
            pixmap = self.pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(
                (self.width() - pixmap.width()) // 2, (self.height() - pixmap.height()) // 2, pixmap
            )
        else:
            painter.fillRect(self.rect(), QColor("#8A83CE"))
            painter.setPen(QColor("white"))
            painter.setFont(system_font(26))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.initials)


class ProfileDialog(AppDialog):
    state_changed = Signal()

    def __init__(self, window, account, *, onboarding=False, continued=None):
        super().__init__(account if onboarding else window)
        self.window, self.account = window, account
        self.onboarding, self.continued = onboarding, continued
        self.user_id = str(account.service.user.id)
        self.avatar_data = None
        self.remove_photo = False
        self.saving = False
        profile = account.snapshot.get("user_profile", {})
        metadata = getattr(account.service.user, "user_metadata", None) or {}
        self.setWindowTitle("Make Aedrova yours" if onboarding else "Your profile")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(680, 740)
        self.setMinimumSize(540, 540)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 28, 28, 28)
        outer.setSpacing(20)
        self.progress = label("", "section")
        outer.addWidget(self.progress)
        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)
        self.steps = []

        def step(title, subtitle):
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.setContentsMargins(20, 16, 20, 24)
            layout.setSpacing(18)
            layout.addWidget(label(title, "heading"))
            layout.addWidget(label(subtitle, "muted", wrap=True))
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.Shape.NoFrame)
            scroll.setWidget(content)
            self.stack.addWidget(scroll)
            self.steps.append(content)
            return layout

        identity = step(
            "A familiar face.\nA name that feels like you.",
            "This is how your teammates will see you in conversations.",
        )
        preview = QHBoxLayout()
        self.avatar = Avatar()
        preview.addWidget(self.avatar)
        preview_text = QVBoxLayout()
        self.preview_name = label("", "title")
        self.preview_username = label("", "muted")
        preview_text.addWidget(self.preview_name)
        preview_text.addWidget(self.preview_username)
        preview_text.addStretch()
        preview.addLayout(preview_text, 1)
        identity.addLayout(preview)
        photo_row = QHBoxLayout()
        photo = button("Choose photo…", role="outline")
        photo.clicked.connect(self.choose_photo)
        photo_row.addWidget(photo)
        remove = button("Use initials", role="outline")
        remove.clicked.connect(self.clear_photo)
        photo_row.addWidget(remove)
        photo_row.addStretch()
        identity.addLayout(photo_row)
        identity.addWidget(
            label(
                "Photos are cropped to a square. Visible only to your teammates.",
                "muted",
                wrap=True,
            )
        )
        self.name = QLineEdit(profile.get("display_name") or metadata.get("full_name", ""))
        self.name.setMaxLength(80)
        self.name.setAccessibleName("Display name")
        self.username = QLineEdit(
            profile.get("username") or suggested_username(self.name.text(), self.user_id)
        )
        self.username.setMaxLength(32)
        self.username.setAccessibleName("Username")
        for title, field in [("Display name", self.name), ("Username", self.username)]:
            identity.addWidget(label(title))
            identity.addWidget(field)
        identity.addWidget(
            label("Your @username is unique. Letters, numbers and underscores.", "muted", wrap=True)
        )
        identity.addStretch()
        about = step(
            "More than a name.",
            "A little context helps your teammates get to know you. These details are optional.",
        )
        self.title = QLineEdit(profile.get("title", ""))
        self.title.setMaxLength(80)
        self.title.setPlaceholderText("e.g. Designer, Founder, Software Engineer")
        self.title.setAccessibleName("Role or job title")
        about.addWidget(label("Role / title"))
        about.addWidget(self.title)
        about.addWidget(
            label(
                "This describes your work; it does not change account permissions.",
                "muted",
                wrap=True,
            )
        )
        self.bio = QPlainTextEdit(profile.get("bio", ""))
        self.bio.setObjectName("ProfileBio")
        self.bio.setPlaceholderText("What do you work on? What should your team know?")
        self.bio.setAccessibleName("Short bio")
        self.bio.setMaximumHeight(160)
        about.addWidget(label("About you"))
        about.addWidget(self.bio)
        self.bio_count = label("", "muted")
        about.addWidget(self.bio_count)
        optional = button("Skip optional details", role="outline")
        optional.clicked.connect(lambda: self.go(2))
        about.addWidget(optional)
        about.addStretch()
        status = step(
            "Work on your terms.", "Let your team know when you are available, focused, or away."
        )
        self.availability = ChoiceBox()
        self.availability.setAccessibleName("Availability")
        for text, value in [("Online", "online"), ("Away", "away"), ("Do not disturb", "busy")]:
            self.availability.addItem(text, value)
        self.availability.setCurrentIndex(
            max(0, self.availability.findData(profile.get("availability", "online")))
        )
        status.addWidget(label("Availability"))
        status.addWidget(self.availability)
        status.addWidget(
            label(
                "Do not disturb keeps activity in your inbox and quiets in-app banners.",
                "muted",
                wrap=True,
            )
        )
        status_row = QHBoxLayout()
        self.emoji = button(profile.get("status_emoji") or "☺", "Choose status emoji", "outline")
        self.emoji.setFixedSize(52, 44)
        self.emoji.clicked.connect(self.choose_emoji)
        self.status_emoji = profile.get("status_emoji", "")
        status_row.addWidget(self.emoji)
        self.status = QLineEdit(profile.get("status", ""))
        self.status.setMaxLength(120)
        self.status.setPlaceholderText("e.g. Building something good")
        self.status.setAccessibleName("Custom status")
        status_row.addWidget(self.status, 1)
        status.addLayout(status_row)
        clear = button("Clear status emoji", role="outline")
        clear.clicked.connect(self.clear_emoji)
        status.addWidget(clear)
        status.addStretch()
        status.addWidget(
            label(
                "Everything here can be changed later from your account menu.", "muted", wrap=True
            )
        )
        self.error = label("", "error", wrap=True)
        self.error.hide()
        outer.addWidget(self.error)
        self.controls = QHBoxLayout()
        self.back = button("Back", role="outline")
        self.back.clicked.connect(lambda: self.go(self.stack.currentIndex() - 1))
        self.controls.addWidget(self.back)
        cancel = button("Finish later" if onboarding else "Cancel")
        cancel.clicked.connect(self.reject)
        self.controls.addWidget(cancel)
        self.controls.addStretch()
        self.next = button("Continue", role="primary")
        self.next.clicked.connect(self.advance)
        self.controls.addWidget(self.next)
        outer.addLayout(self.controls)
        self.fade = QGraphicsOpacityEffect(self.progress)
        self.progress.setGraphicsEffect(self.fade)
        self.animation = QPropertyAnimation(self.fade, b"opacity", self)
        self.animation.setDuration(260)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.name.textChanged.connect(self.preview)
        self.username.textChanged.connect(self.preview)
        self.bio.textChanged.connect(self.count_bio)
        self.name.returnPressed.connect(self.advance)
        self.username.returnPressed.connect(self.advance)
        self.preview()
        self.count_bio()
        self.go(0)
        path = profile.get("avatar_path")
        if path and hasattr(window, "collaboration"):
            window.collaboration.load_avatar(path, self.set_existing_photo)

    def set_existing_photo(self, pixmap):
        if self.avatar_data is None and not self.remove_photo:
            self.avatar.pixmap = pixmap
            self.avatar.update()

    def preview(self):
        self.preview_name.setText(self.name.text().strip() or "Your name")
        self.preview_username.setText("@" + self.username.text().strip())
        self.avatar.initials = (
            "".join(part[0] for part in self.name.text().split()[:2]).upper() or "You"
        )
        self.avatar.update()

    def count_bio(self):
        self.bio_count.setText(f"{len(self.bio.toPlainText())}/280 characters")

    def choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose profile photo", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            try:
                self.avatar_data = avatar_png(path)
            except ValueError as error:
                self.show_error(str(error))
                return
            self.remove_photo = False
            self.avatar.set_photo(self.avatar_data)

    def clear_photo(self):
        self.avatar_data = None
        self.remove_photo = True
        self.avatar.pixmap = QPixmap()
        self.avatar.update()

    def choose_emoji(self):
        emoji = pick_emoji(self)
        if emoji:
            self.status_emoji = emoji
            self.emoji.setText(emoji)

    def clear_emoji(self):
        self.status_emoji = ""
        self.emoji.setText("☺")

    def go(self, index):
        if self.saving:
            return
        index = max(0, min(2, index))
        self.stack.setCurrentIndex(index)
        self.progress.setText(f"YOUR PROFILE   ·   {index + 1} / 3")
        self.back.setVisible(index > 0)
        self.next.setText(
            "Save & continue"
            if index == 2 and self.onboarding
            else "Save profile"
            if index == 2
            else "Continue"
        )
        self.error.hide()
        self.animation.stop()
        if not self.window.reduced_motion:
            self.animation.setStartValue(0.35)
            self.animation.setEndValue(1.0)
            self.animation.start()
        else:
            self.fade.setOpacity(1.0)
        (self.name, self.title, self.status)[index].setFocus()
        self.state_changed.emit()

    def values(self):
        result = {
            "display_name": self.name.text().strip(),
            "username": self.username.text().strip().lower(),
            "bio": self.bio.toPlainText().strip(),
            "title": self.title.text().strip(),
            "status": self.status.text().strip(),
            "status_emoji": self.status_emoji,
            "availability": self.availability.currentData(),
            "profile_completed": True,
        }
        if self.remove_photo:
            result["avatar_path"] = None
        return validate_profile(result)

    def show_error(self, text):
        self.error.setText(text)
        self.error.show()

    def advance(self):
        if self.saving:
            return
        try:
            data = self.values()
        except ValueError as error:
            self.show_error(str(error))
            return
        index = self.stack.currentIndex()
        if index < 2:
            self.go(index + 1)
            return
        service = self.account.service
        if not service or not service.user or str(service.user.id) != self.user_id:
            self.show_error("Sign in again to save your profile.")
            return
        self.saving = True
        self.next.setEnabled(False)
        self.back.setEnabled(False)
        self.next.setText("Saving…")
        self.state_changed.emit()

        def operation():
            try:
                return {"profile": service.save_full_profile(data, self.avatar_data)}
            except Exception as error:
                message = str(error)
                return {
                    "error": "That username is already taken. Try another."
                    if "username is already taken" in message
                    else "Could not save. Check your connection and profile SQL setup, then retry."
                }

        def saved(result):
            self.saving = False
            self.next.setEnabled(True)
            self.back.setEnabled(True)
            self.next.setText("Save & continue" if self.onboarding else "Save profile")
            self.state_changed.emit()
            if (
                not self.account.service
                or not self.account.service.user
                or str(self.account.service.user.id) != self.user_id
            ):
                return
            if result.get("error"):
                self.show_error(result["error"])
                return
            self.account.snapshot["user_profile"] = result["profile"]
            collaboration = getattr(self.window, "collaboration", None)
            if collaboration:
                collaboration.last_availability = data["availability"]
                if self.avatar_data and result["profile"].get("avatar_path"):
                    pixmap = QPixmap()
                    pixmap.loadFromData(self.avatar_data)
                    collaboration.avatar_images[result["profile"]["avatar_path"]] = pixmap
            self.window.update_profile_button()
            visible = self.isVisible()
            self.accept()
            if visible and self.continued:
                self.continued()

        connected = getattr(self.window, "connected", None)
        if connected and connected.active:
            if not connected.enqueue(("save-full-profile", self.user_id), operation, saved):
                self.saving = False
                self.next.setEnabled(True)
                self.back.setEnabled(True)
                self.next.setText("Save & continue" if self.onboarding else "Save profile")
                self.state_changed.emit()
                self.show_error("Connection busy. Try again shortly.")
        elif self.account.busy:
            self.saving = False
            self.next.setEnabled(True)
            self.back.setEnabled(True)
            self.next.setText("Save & continue" if self.onboarding else "Save profile")
            self.state_changed.emit()
            self.show_error("Connection busy. Try again shortly.")
        else:
            self.account.run(operation, saved)


def open_profile_editor(window, *, onboarding=False, continued=None):
    account = getattr(window, "account_dialog", None)
    if not account or not account.service or not account.service.user:
        window.show_account()
        return
    existing = getattr(window, "profile_dialog", None)
    if existing and existing.isVisible():
        existing.raise_()
        return existing
    dialog = ProfileDialog(window, account, onboarding=onboarding, continued=continued)
    window.profile_dialog = dialog
    account.session_closed.connect(dialog.reject)
    dialog.show()
    return dialog
