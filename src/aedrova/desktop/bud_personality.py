"""Continuous, keyboard-accessible working-style controls with a live voice preview."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QSlider

from aedrova.desktop.dialogs import label
from aedrova.dots.personality import DEFAULTS


def build_personality(dialog, layout):
    dialog.personality_sliders = {}
    for key, title, left, right in (
        ("warmth", "Tone", "Reserved", "Warm"),
        ("directness", "Communication", "Gentle", "Direct"),
        ("detail", "Response depth", "Brief", "Thorough"),
        ("initiative", "Initiative", "Stay focused", "Suggest next steps"),
        ("diligence", "Work ethic", "Quick first pass", "Careful cross-checks"),
        ("reporting", "Progress updates", "Milestones only", "Every 5 minutes"),
    ):
        row = QHBoxLayout()
        row.addWidget(label(title))
        value = label("", "muted")
        row.addStretch()
        row.addWidget(value)
        layout.addLayout(row)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 300 if key == "reporting" else 100)
        slider.setValue(DEFAULTS[key])
        slider.setAccessibleName("Bud " + title)
        slider.setMinimumHeight(26)

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
        layout.addWidget(slider)
        ends = QHBoxLayout()
        ends.addWidget(label(left, "muted"))
        ends.addStretch()
        ends.addWidget(label(right, "muted"))
        layout.addLayout(ends)
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
    dialog.personality_preview = label("", "muted", wrap=True)
    dialog.personality_preview.setTextFormat(Qt.TextFormat.PlainText)
    layout.addWidget(dialog.personality_preview)
    layout.addWidget(
        label(
            "Applies when you ask your Bud to work. Permissions and usage limits stay in place.",
            "muted",
            wrap=True,
        )
    )
    personality_preview(dialog)


def personality_preview(dialog):
    if not hasattr(dialog, "personality_preview"):
        return
    sliders = dialog.personality_sliders
    tone = "Warm and encouraging" if sliders["warmth"].value() >= 50 else "Calm and reserved"
    depth = (
        "with a detailed explanation"
        if sliders["detail"].value() >= 50
        else "with the essentials first"
    )
    dialog.personality_preview.setText(f"{tone}, {depth}. Your words shape the rest.")
