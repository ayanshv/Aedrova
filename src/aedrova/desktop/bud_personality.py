"""Continuous, keyboard-accessible working-style controls with a live voice preview."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QSlider,
    QStyle,
    QStyleOptionSlider,
    QVBoxLayout,
)

from aedrova.desktop.dialogs import label
from aedrova.dots.personality import DEFAULTS


class PersonalitySlider(QSlider):
    def mousePressEvent(self, event):  # noqa: N802
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        style = self.style()
        control = QStyle.ComplexControl.CC_Slider
        handle = style.subControlRect(control, option, QStyle.SubControl.SC_SliderHandle, self)
        if event.button() == Qt.MouseButton.LeftButton and not handle.contains(
            event.position().toPoint()
        ):
            groove = style.subControlRect(control, option, QStyle.SubControl.SC_SliderGroove, self)
            span = max(1, groove.width() - handle.width())
            offset = round(event.position().x()) - groove.x() - handle.width() // 2
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            self.setValue(
                QStyle.sliderValueFromPosition(
                    self.minimum(), self.maximum(), offset, span, option.upsideDown
                )
            )
            event.accept()
            return
        super().mousePressEvent(event)


def build_personality(dialog, layout):
    dialog.personality_sliders = {}
    dialog.personality_preview = label("", wrap=True)
    dialog.personality_preview.setObjectName("BudVoicePreview")
    layout.addWidget(dialog.personality_preview)
    for key, title, left, right in (
        ("warmth", "Tone", "Reserved", "Warm"),
        ("directness", "Communication", "Gentle", "Direct"),
        ("detail", "Response depth", "Brief", "Thorough"),
        ("initiative", "Initiative", "Stay focused", "Suggest next steps"),
        ("diligence", "Work ethic", "Quick first pass", "Careful cross-checks"),
        ("reporting", "Progress updates", "Milestones only", "Every 5 minutes"),
    ):
        card = QFrame()
        card.setObjectName("BudStyleCard")
        group = QVBoxLayout(card)
        group.setContentsMargins(14, 9, 14, 9)
        group.setSpacing(3)
        layout.addWidget(card)
        row = QHBoxLayout()
        row.addWidget(label(title))
        value = label("", "muted")
        value.setObjectName("BudStyleValue")
        row.addStretch()
        row.addWidget(value)
        group.addLayout(row)
        slider = PersonalitySlider(Qt.Orientation.Horizontal)
        slider.setObjectName("BudStyleSlider")
        slider.setRange(0, 300 if key == "reporting" else 100)
        slider.setPageStep(30 if key == "reporting" else 10)
        slider.setValue(DEFAULTS[key])
        slider.setAccessibleName("Bud " + title)
        slider.setMinimumHeight(32)

        def changed(number, caption=value, setting=key, control=slider):
            text = (
                ("Milestones only" if number == 0 else f"Every {number}s")
                if setting == "reporting"
                else f"{number}%"
            )
            caption.setText(text)
            control.setAccessibleDescription(text)
            personality_preview(dialog)

        slider.valueChanged.connect(changed)
        group.addWidget(slider)
        ends = QHBoxLayout()
        ends.addWidget(label(left, "muted"))
        ends.addStretch()
        ends.addWidget(label(right, "muted"))
        group.addLayout(ends)
        dialog.personality_sliders[key] = slider
        changed(slider.value())
    layout.addWidget(label("In your own words", "muted"))
    dialog.personality_voice = QLineEdit()
    dialog.personality_voice.setMaxLength(480)
    dialog.personality_voice.setPlaceholderText(
        "e.g. Calm, candid, a little witty. Challenge weak assumptions."
    )
    dialog.personality_voice.setAccessibleName("Custom Bud personality")
    dialog.personality_voice.textChanged.connect(lambda: personality_preview(dialog))
    layout.addWidget(dialog.personality_voice)
    layout.addWidget(
        label(
            "Applies when you ask your Bud to work. Permissions and usage limits stay in place.",
            "muted",
            wrap=True,
        )
    )
    personality_preview(dialog)


def personality_preview(dialog):
    sliders = dialog.personality_sliders
    if not all(key in sliders for key in ("warmth", "directness", "detail", "initiative")):
        return
    opening = "Happy to help." if sliders["warmth"].value() >= 50 else "Here’s my read."
    idea = (
        "Start with the simplest version."
        if sliders["directness"].value() >= 50
        else "We could start with the simplest version."
    )
    detail = (
        " That gives us something to test before we commit to the rest."
        if sliders["detail"].value() >= 50
        else ""
    )
    follow_up = (
        " I can suggest a first step." if sliders["initiative"].value() >= 50 else ""
    )
    dialog.personality_preview.setText(f"Example · “{opening} {idea}{detail}{follow_up}”")
