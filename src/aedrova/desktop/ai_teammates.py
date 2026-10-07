"""Small native characters and a workspace-owned specialist editor."""

import copy
from uuid import uuid4

from PySide6.QtCore import QObject, QRectF, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.choice_slider import ChoiceSlider
from aedrova.desktop.connector_panel import ConnectorPanel
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.design_system import FlowActions, MasterDetail
from aedrova.desktop.dialogs import button, label
from aedrova.teammates.model import (
    COLORS,
    EFFORT,
    IMPORTANCE,
    REPORTING,
    ROLES,
    SHAPES,
    TONES,
    validate,
)


class Character(QWidget):
    def __init__(self, config=None, parent=None, *, reduced_motion=False):
        super().__init__(parent)
        self.config = config or {"name": "Pixel", "shape": "round", "color": "#4388F5"}
        self.setFixedSize(140, 132)
        self.reduced_motion = reduced_motion
        self.blink = False
        self.phase = 1.0
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.animate)
        self.set_config(self.config)

    def showEvent(self, event):
        if not self.reduced_motion:
            self.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def animate(self):
        self.phase += 0.033
        self.blink = self.phase % 4.4 < 0.13
        self.update()

    def set_config(self, config):
        self.config = config
        self.setAccessibleName("AI teammate character " + config["name"])
        self.update()

    def paintEvent(self, event):
        from aedrova.desktop.teammate_habitat import paint_orb

        p = QPainter(self)
        paint_orb(
            p,
            QRectF(self.rect()).adjusted(10, 10, -10, -10),
            self.config,
            phase=self.phase if not self.reduced_motion else 1,
            blink=self.blink,
        )


class RoleSignals(QObject):
    finished = Signal(object)


class RoleJob(QRunnable):
    def __init__(self, role, provider):
        super().__init__()
        from aedrova.agents.runtime import LocalRunner

        self.role, self.provider = role, provider
        self.signals = RoleSignals()
        self.runner = LocalRunner(lambda _: None, timeout=90)

    def run(self):
        from aedrova.teammates.advisor import advise

        try:
            self.signals.finished.emit({"advice": advise(self.role, self.provider, self.runner)})
        except Exception:
            self.signals.finished.emit({"error": True})


class TeammatesDialog(AppDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.workspace, self.user = window.workspace_id, str(window.current_user().id)
        self.rows, self.selected, self.busy, self.closed = [], None, False, False
        self.role_job = None
        self.last_advised_role = ""
        self.role_timer = QTimer(self)
        self.role_timer.setSingleShot(True)
        self.role_timer.setInterval(1600)
        self.role_timer.timeout.connect(self.automatic_suggestions)
        self.suggested_tools = []
        self.draft_id = str(uuid4())
        self.setWindowTitle("Aedrova · AI teammates")
        self.resize(820, 850)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.addWidget(label("A little teammate. Real help.", "heading"))
        layout.addWidget(
            label(
                "Mention a teammate to assign work. They use your connected provider "
                "and the context you can access. No idle AI calls.",
                "muted",
                wrap=True,
            )
        )
        self.status = label("", "muted", wrap=True)
        layout.addWidget(self.status)
        self.list = QListWidget()
        self.list.setAccessibleName("Workspace AI teammates")
        self.list.setProperty("accountList", True)
        self.list.setMaximumHeight(76)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(area.Shape.NoFrame)
        body = QWidget()
        content = QVBoxLayout(body)
        self.character = Character(reduced_motion=window.reduced_motion)
        content.addWidget(self.character, alignment=Qt.AlignmentFlag.AlignHCenter)
        tabs = QTabWidget()
        purpose = QWidget()
        personality = QWidget()
        form = QFormLayout(purpose)
        style_form = QFormLayout(personality)
        style_form.setSpacing(16)
        tabs.addTab(purpose, "Purpose and tools")
        tabs.addTab(personality, "Personality")
        form.setSpacing(12)
        for fields in (form, style_form):
            fields.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
            fields.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.name = QLineEdit("Pixel")
        self.name.setMaxLength(24)
        self.name.setAccessibleName("Teammate name")
        form.addRow("Name", self.name)
        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText(
            "e.g. A product researcher who turns feedback into clear requirements"
        )
        self.role_input.setMaxLength(240)
        self.role_input.setAccessibleName("Describe your AI teammate role")
        form.addRow("Role", self.role_input)
        self.suggest = button("Suggest tools with AI", role="outline")
        self.suggest.clicked.connect(self.suggest_role)
        form.addRow("", self.suggest)
        self.advice = label(
            "Suggestions appear automatically after you describe their role. "
            "AI refinement uses your provider login and allowance; it never connects tools.",
            "muted",
            wrap=True,
        )
        self.advice.setTextFormat(Qt.TextFormat.PlainText)
        form.addRow("", self.advice)
        self.connectors = ConnectorPanel(self)
        form.addRow("", self.connectors)
        self.fields = {}
        for key, title, choices in (
            (
                "role",
                "Execution mode",
                (
                    (title, key)
                    for key, title in (
                        ("research", "Read-only analysis"),
                        ("product", "Read-only specifications"),
                        ("engineering", "Code & tests · existing project permissions"),
                    )
                ),
            ),
            ("shape", "Shape", ((x.title(), x) for x in SHAPES)),
            ("color", "Color", COLORS.items()),
            ("personality", "Personality", ((x.title(), x) for x in TONES)),
            ("reporting", "Progress updates", ((x.title(), x) for x in REPORTING)),
            (
                "effort",
                "Work window",
                ((f"{x.title()} · {v // 60} minutes per phase", x) for x, v in EFFORT.items()),
            ),
            ("importance", "Importance", ((x.title(), x) for x in IMPORTANCE)),
        ):
            field = ChoiceSlider()
            for text, value in choices:
                field.addItem(text, value)
            field.setAccessibleName("Teammate " + title)
            self.fields[key] = field
            (form if key == "role" else style_form).addRow(title, field)
            field.currentIndexChanged.connect(self.preview)
        self.responsibilities = QPlainTextEdit(
            "Help with focused assignments and cite accessible evidence."
        )
        self.responsibilities.setMaximumHeight(85)
        self.responsibilities.setAccessibleName("Teammate responsibilities")
        self.fields["role"].currentIndexChanged.connect(self.role_template)
        form.addRow("Responsibilities", self.responsibilities)
        self.fields["effort"].setCurrentIndex(1)
        content.addWidget(tabs)
        content.addWidget(
            label(
                "Context: your accessible workspace evidence and approved Product memory. "
                "Engineering uses saved project permissions; Product and Research are read-only. "
                "The work window caps runtime, not provider charges. Importance never changes "
                "permissions or bypasses the queue. "
                "Connected external resources are read-only and bounded. Publishing still "
                "requires the existing delivery approval workflow.",
                "muted",
                wrap=True,
            )
        )
        area.setWidget(body)
        self.master_detail = MasterDetail(self.list, area)
        layout.addWidget(self.master_detail, 1)
        actions = FlowActions()
        self.new = button("New", role="outline")
        self.save = button("Save teammate", role="primary")
        self.pause = button("Pause", role="outline")
        self.remove = button("Remove", role="outline")
        done = button("Done", role="outline")
        for w in (self.new, self.save, self.pause, self.remove, done):
            actions.addWidget(w)
        layout.addLayout(actions)
        self.new.clicked.connect(self.create)
        self.save.clicked.connect(self.persist)
        self.pause.clicked.connect(self.toggle_pause)
        self.remove.clicked.connect(self.delete)
        done.clicked.connect(self.reject)
        self.list.currentRowChanged.connect(self.select)
        self.name.textChanged.connect(self.preview)
        self.role_input.textEdited.connect(self.role_changed)
        window.account_dialog.session_closed.connect(self.reject)
        self.refresh()

    def editable(self):
        return any(
            m["workspace_id"] == self.workspace
            and m["user_id"] == self.user
            and m["role"] in {"owner", "admin"}
            for m in self.window.account_dialog.snapshot["members"]
        )

    def valid(self):
        current = self.window.current_user()
        return (
            not self.closed
            and current is not None
            and self.window.workspace_id == self.workspace
            and str(current.id) == self.user
        )

    def run(self, name, action, completed):
        if self.busy or not self.valid():
            return
        self.busy = True
        self.controls()

        def work():
            try:
                return {"value": action(self.window.account_dialog.service)}
            except Exception as error:
                from aedrova.connectors.service import ConnectorError

                if isinstance(error, ConnectorError):
                    return {"error": "connector", "message": str(error)}
                return {"error": getattr(error, "code", "")}

        def finish(result):
            self.busy = False
            if not self.valid():
                self.reject()
                return
            self.controls()
            if "error" in result:
                self.status.setText(
                    result.get("message")
                    or "Settings could not save. Refresh before retrying; "
                    "names must be unique and your owner/admin access must still be active."
                )
                if name in {"connect", "disconnect"}:
                    self.connectors.status.setText(self.status.text())
            else:
                completed(result["value"])

        if not self.window.connected.enqueue(("ai-teammates", id(self), name), work, finish):
            self.busy = False
            self.status.setText("Connection busy. Try again shortly.")
            self.controls()

    def refresh(self):
        def loaded(payload):
            selected_id = self.selected["id"] if self.selected else None
            self.rows = payload["items"]
            self.list.clear()
            self.list.addItems(
                [
                    r["config"]["name"]
                    + " · "
                    + (r["config"].get("role_label") or ROLES[r["config"]["role"]])
                    + (" · Paused" if r["paused"] else "")
                    for r in self.rows
                ]
            )
            self.status.setText(
                "Run the AI teammates SQL migration to enable creation."
                if payload["setup_required"]
                else "Owner/admins manage teammates. Members can assign work."
            )
            self.selected = None
            if selected_id:
                index = next((i for i, r in enumerate(self.rows) if r["id"] == selected_id), -1)
                self.list.setCurrentRow(index)
            self.setup_required = payload["setup_required"]
            self.controls()

        self.run("list", lambda service: service.ai_teammates(self.workspace), loaded)

    def config(self):
        return {
            "name": self.name.text().strip(),
            "responsibilities": self.responsibilities.toPlainText().strip(),
            "role_label": self.role_input.text().strip()
            or ROLES[self.fields["role"].currentData()],
            "suggested_tools": list(self.suggested_tools),
            "connections": [dict(r) for r in self.connectors.rows],
            **{k: f.currentData() for k, f in self.fields.items()},
        }

    def role_template(self):
        if self.selected is None:
            self.responsibilities.setPlainText(
                {
                    "engineering": "Help with focused assignments and cite accessible evidence.",
                    "product": "Clarify requirements and draft cited specifications.",
                    "research": "Summarize evidence and flag open questions.",
                }[self.fields["role"].currentData()]
            )

    def preview(self):
        if hasattr(self, "fields") and "color" in self.fields:
            self.character.set_config(
                {
                    "name": self.name.text() or "Teammate",
                    "shape": self.fields["shape"].currentData(),
                    "color": self.fields["color"].currentData() or "#4388F5",
                }
            )

    def controls(self):
        allowed = not self.busy and self.editable() and not getattr(self, "setup_required", False)
        for w in (
            self.save,
            self.new,
            self.name,
            self.responsibilities,
            self.role_input,
            *self.fields.values(),
        ):
            w.setEnabled(allowed)
        self.suggest.setEnabled(allowed and self.role_job is None)
        self.connectors.permissions(self.busy, allowed)
        self.pause.setEnabled(allowed and self.selected is not None)
        self.remove.setEnabled(allowed and self.selected is not None)

    def create(self):
        self.selected = None
        self.last_advised_role = ""
        self.draft_id = str(uuid4())
        self.list.setCurrentRow(-1)
        self.name.setText("Pixel")
        self.role_input.clear()
        self.fields["role"].setCurrentIndex(0)
        self.suggested_tools = []
        self.connectors.load([])
        self.advice.setText("Describe the role to get suggested tools.")
        self.controls()

    def select(self, index):
        if not 0 <= index < len(self.rows):
            return
        self.selected = copy.deepcopy(self.rows[index])
        config = self.selected["config"]
        self.name.setText(config["name"])
        self.role_input.setText(config.get("role_label", ROLES[config["role"]]))
        from aedrova.teammates.advisor import suggest_locally

        self.suggested_tools = config.get("suggested_tools") or suggest_locally(
            self.role_input.text()
        )
        self.connectors.load(config.get("connections", []))
        self.select_suggested_connector()
        self.show_suggestions("Suggested tools for this role.")
        self.responsibilities.setPlainText(config["responsibilities"])
        for k, field in self.fields.items():
            at = field.findData(config[k])
            if at < 0:
                field.addItem(config[k], config[k])
                at = field.count() - 1
            field.setCurrentIndex(at)
        self.pause.setText("Resume" if self.selected["paused"] else "Pause")
        self.controls()

    def persist(self, *, paused=None):
        if not self.editable():
            return
        if not self.role_input.text().strip():
            self.status.setText("Describe what this teammate should help your team with.")
            return
        config = self.config()
        try:
            validate(config)
            from aedrova.connectors.service import validate_connections

            validate_connections(config["connections"])
        except ValueError as error:
            self.status.setText(str(error))
            return
        record = self.selected or {"id": self.draft_id, "version": 0, "paused": False}
        parameters = {
            "p_id": record["id"],
            "p_workspace": self.workspace,
            "p_version": record["version"],
            "p_config": config,
            "p_paused": record["paused"] if paused is None else paused,
        }

        def saved(version):
            self.selected = {
                **record,
                "version": version,
                "config": config,
                "paused": parameters["p_paused"],
            }
            self.status.setText(
                "Teammate saved. Mention @" + config["name"] + " with an assignment."
            )
            self.window.connected.refresh()
            self.refresh()

        def verified_save(service):
            from aedrova.connectors.service import evidence

            evidence(self.user, self.workspace, {"id": record["id"], "config": config})
            return service.save_ai_teammate(parameters)

        self.run("save", verified_save, saved)

    def role_changed(self):
        from aedrova.teammates.advisor import suggest_locally

        self.suggested_tools = suggest_locally(self.role_input.text())
        self.select_suggested_connector()
        self.show_suggestions("Suggested from your role · AI refinement follows automatically.")
        self.role_timer.start()

    def automatic_suggestions(self):
        role = self.role_input.text().strip()
        if len(role) >= 8 and role != self.last_advised_role and not self.role_job:
            self.last_advised_role = role
            self.suggest_role()

    def suggest_role(self):
        if not self.editable() or self.role_job or self.busy or not self.valid():
            return
        from aedrova.desktop.projects import binding
        from aedrova.teammates.advisor import role_prompt

        role = self.role_input.text().strip()
        try:
            role_prompt(role)
        except ValueError as error:
            self.advice.setText(str(error))
            return
        self.advice.setText("Reading the role with your provider… No workspace data is sent.")
        self.suggest.setEnabled(False)
        self.role_job = RoleJob(role, binding(self.window).get("provider", "codex"))
        self.role_job.signals.finished.connect(lambda value: self.role_ready(role, value))
        QThreadPool.globalInstance().start(self.role_job)

    def role_ready(self, role, value):
        self.role_job = None
        if not self.valid():
            return
        self.suggest.setEnabled(self.editable())
        if role != self.role_input.text().strip():
            self.advice.setText("Your role changed. Ask for fresh suggestions.")
            self.role_timer.start()
            return
        if value.get("error"):
            self.advice.setText(
                "AI refinement unavailable. Role-based suggestions remain available below. "
                "Check provider login or allowance, or connect a tool directly."
            )
            self.show_suggestions(self.advice.text())
            return
        self.suggested_tools = value["advice"]["tools"]
        self.select_suggested_connector()
        self.show_suggestions(value["advice"]["summary"])

    def select_suggested_connector(self):
        if self.connectors.resource.text().strip() or self.connectors.token.text():
            return  # Never overwrite a connection the user is already configuring.
        for tool in self.suggested_tools:
            at = self.connectors.kind.findData(tool)
            if at >= 0:
                self.connectors.kind.setCurrentIndex(at)
                break

    def show_suggestions(self, summary=""):
        from aedrova.teammates.advisor import TOOLS

        lines = [summary] if summary else []
        for key in self.suggested_tools:
            if key in TOOLS:
                title, availability = TOOLS[key]
                lines.append(title + " · " + availability)
        lines.append(
            "Connect a suggested tool below to grant access. Suggestions grant no permissions. "
            "Uses your provider login; provider usage may be billed."
        )
        self.advice.setText("\n".join(lines))

    def toggle_pause(self):
        if self.selected:
            self.persist(paused=not self.selected["paused"])

    def delete(self):
        if self.selected and self.editable():
            record = copy.deepcopy(self.selected)
            self.run(
                "remove",
                lambda service: service.remove_ai_teammate(record["id"], record["version"]),
                lambda _: self.refresh(),
            )

    def reject(self):
        self.closed = True
        self.role_timer.stop()
        if self.role_job:
            self.role_job.runner.cancel()
        self.rows = []
        self.selected = None
        self.list.clear()
        self.name.clear()
        self.responsibilities.clear()
        super().reject()


def open_teammates(window):
    if not window.current_user() or not window.connected or not window.connected.active:
        window.notify("Sign in to manage workspace AI teammates.")
        return
    old = getattr(window, "teammates_dialog", None)
    if old and not old.closed:
        old.raise_()
        return
    window.teammates_dialog = TeammatesDialog(window)
    window.teammates_dialog.show()
