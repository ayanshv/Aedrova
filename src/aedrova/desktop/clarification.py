"""A small, app-rendered form for questions from a build agent."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QLineEdit, QScrollArea, QVBoxLayout, QWidget

from aedrova.desktop.controls import ChoiceBox
from aedrova.desktop.dialogs import label


class ClarificationForm(QScrollArea):
    def __init__(self, question, submit, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(2, 4, 6, 6)
        layout.setSpacing(8)
        layout.addWidget(label(question["title"], "title", wrap=True))
        self.inputs = []
        for field in question["fields"]:
            caption = field["label"]
            layout.addWidget(
                label(caption if field["required"] else caption + " (optional)", wrap=True)
            )
            kind = field["type"]
            if kind == "text":
                control = QLineEdit()
                control.setMaxLength(4000)
                control.returnPressed.connect(submit)
            elif kind == "single":
                control = ChoiceBox()
                control.addItem("Choose an option", None)
                for option in field["options"]:
                    control.addItem(option, option)
            else:
                control = QWidget()
                choices = QVBoxLayout(control)
                choices.setContentsMargins(0, 0, 0, 0)
                choices.setSpacing(4)
                for option in field["options"]:
                    checkbox = QCheckBox(option.replace("&", "&&"))
                    checkbox.setProperty("answer", option)
                    choices.addWidget(checkbox)
            control.setAccessibleName(caption)
            self.inputs.append((field, control))
            layout.addWidget(control)
        self.setWidget(content)
        self.setFixedHeight(min(content.sizeHint().height() + 8, 320))

    def focus_first(self):
        self._focus(self.inputs[0][1])

    def _focus(self, control):
        target = next(iter(control.findChildren(QCheckBox)), control)
        self.ensureWidgetVisible(target)
        target.setFocus()

    def answers(self):
        answers = []
        for field, control in self.inputs:
            if field["type"] == "text":
                value = control.text().strip()
            elif field["type"] == "single":
                value = control.currentData()
            else:
                value = [
                    option.property("answer")
                    for option in control.findChildren(QCheckBox)
                    if option.isChecked()
                ]
            if not value and field["required"]:
                self._focus(control)
                return None
            answers.append({"label": field["label"], "answer": value})
        return answers
