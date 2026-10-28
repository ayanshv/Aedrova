"""Create an empty local project without touching existing project contents."""

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QVBoxLayout

from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label


def create_project_folder(location, name):
    name = name.strip()
    if (
        not name
        or len(name) > 100
        or name in {".", ".."}
        or name.endswith(".")
        or any(ord(char) < 32 or char in '/\\:*?"<>|' for char in name)
        or name.split(".")[0].upper()
        in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }
    ):
        raise ValueError("Enter a project name without slashes or special characters.")
    parent = Path(location).expanduser().resolve(strict=True)
    if not parent.is_dir():
        raise ValueError("Choose an existing folder to save your project in.")
    project = parent / name
    project.mkdir(exist_ok=False)
    return str(project)


class NewProjectDialog(AppDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = ""
        self.setWindowTitle("Start a new project")
        self.setMinimumWidth(480)
        column = QVBoxLayout(self)
        column.setContentsMargins(28, 28, 28, 28)
        column.setSpacing(16)
        column.addWidget(label("Start something new", "title"))
        column.addWidget(
            label(
                "Give your project a name. Aedrova creates an empty folder for your team’s work.",
                "muted",
                wrap=True,
            )
        )
        self.name = QLineEdit()
        self.name.setPlaceholderText("My team’s project")
        self.name.setAccessibleName("New project name")
        self.name.setMaxLength(100)
        column.addWidget(self.name)
        column.addWidget(label("Save in", "muted"))
        documents = Path.home() / "Documents"
        self.location = QLineEdit(str(documents if documents.is_dir() else Path.home()))
        self.location.setAccessibleName("New project location")
        location_row = QHBoxLayout()
        location_row.addWidget(self.location, 1)
        browse = button("Choose…", role="outline")
        browse.clicked.connect(self.browse)
        location_row.addWidget(browse)
        column.addLayout(location_row)
        self.status = label("No build starts until you ask Aedrova.", "muted", wrap=True)
        self.status.setAccessibleName("New project status")
        column.addWidget(self.status)
        actions = QHBoxLayout()
        cancel = button("Cancel", role="outline")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        self.create = button("Create project")
        self.create.setDefault(True)
        self.create.clicked.connect(self.create_project)
        actions.addWidget(self.create)
        column.addLayout(actions)
        self.name.setFocus()

    def browse(self):
        location = QFileDialog.getExistingDirectory(
            self,
            "Save your new project in",
            self.location.text(),
            QFileDialog.Option.ShowDirsOnly,
        )
        if location:
            self.location.setText(location)

    def create_project(self):
        try:
            self.project_path = create_project_folder(self.location.text(), self.name.text())
        except FileExistsError:
            self.status.setText("That name already exists here. Choose another name or location.")
            return
        except (OSError, ValueError):
            self.status.setText("Use a valid project name and an existing, writable location.")
            return
        self.accept()
