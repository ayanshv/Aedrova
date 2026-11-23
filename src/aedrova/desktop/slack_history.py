"""Native Slack import and read-only history for a connected workspace."""

from datetime import UTC, datetime
from threading import Event

from PySide6.QtCore import Qt, QThreadPool, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.projects import Job
from aedrova.imports import slack


def open_slack_history(
    parent, service, workspace, *, mode="import", query="", selected=None, channel=None
):
    if not workspace or not service or not service.user:
        return
    existing = getattr(parent, "slack_history_dialog", None)
    if existing and existing.isVisible():
        existing.raise_()
        return
    if existing:
        existing.deleteLater()
    dialog = SlackHistoryDialog(parent, service, str(workspace), mode, query, selected, channel)
    parent.slack_history_dialog = dialog
    dialog.open()


class SlackHistoryDialog(AppDialog):
    def __init__(self, parent, service, workspace, mode, query, selected, channel=None):
        super().__init__(parent)
        self.channel, self.oldest, self.loaded = channel, None, []
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(600, 700)
        self.service, self.workspace = service, workspace
        self.user = str(service.user.id)
        self.cancelled = Event()
        self.rows = []
        self.completed = None
        self.selected = selected
        self.mode = mode
        self.setAcceptDrops(mode == "import")
        title = {
            "import": "Import from Slack",
            "history": "Imported history",
            "manage": "Manage Slack imports",
            "channel": "#" + (channel or {}).get("channel_name", "channel"),
        }[mode]
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(label(title, "heading"))

        if mode == "import":
            from PySide6.QtWidgets import QScrollArea

            from aedrova.desktop.slack_steps import ExportSteps

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setMaximumHeight(230)
            scroll.setWidget(ExportSteps())
            layout.addWidget(scroll)
            actions = QHBoxLayout()
            self.choose_button = button("Choose ZIP", role="outline")
            self.choose_button.clicked.connect(self.choose)
            actions.addWidget(self.choose_button)
            layout.addLayout(actions)
        elif mode == "channel":
            layout.addWidget(
                label(
                    "A read-only copy of this Slack channel. Workspace members can search it, "
                    "and agents use it when workspace AI is on.",
                    "muted",
                    wrap=True,
                )
            )
            self.earlier = button("Load earlier messages", role="outline")
            self.earlier.clicked.connect(lambda: self.load_channel(self.oldest))
            self.earlier.hide()
            layout.addWidget(self.earlier, alignment=Qt.AlignmentFlag.AlignLeft)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setAccessibleName("Slack channel messages")
            layout.addWidget(self.log, 1)
        elif mode == "history":
            field = QLineEdit(query)
            field.setPlaceholderText("Search Slack history")
            field.setAccessibleName("Search Slack history")
            field.returnPressed.connect(lambda: self.load_history(field.text()))
            layout.addWidget(field)
        else:
            layout.addWidget(label("Remove an archive or discard an unfinished import.", "muted"))

        self.items = QListWidget()
        self.items.setAccessibleName(title)
        layout.addWidget(self.items, 1)
        self.items.setVisible(mode != "channel")
        if mode == "history":
            self.detail = QPlainTextEdit()
            self.detail.setReadOnly(True)
            self.detail.setAccessibleName("Selected Slack message")
            self.items.currentItemChanged.connect(self.show_record)
            layout.addWidget(self.detail, 1)
        self.status = label("", "muted", wrap=True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.primary = button(
            "Import history" if mode == "import" else "Remove import", role="primary"
        )
        self.primary.setEnabled(False)
        if mode not in ("history", "channel"):
            if mode == "import":
                self.primary.clicked.connect(self.start_import)
            else:
                self.primary.clicked.connect(self.remove)
                self.items.currentItemChanged.connect(self.selection_changed)
            actions.addWidget(self.primary)
        close = button("Done", role="outline")
        close.clicked.connect(self.accept)
        actions.addWidget(close)
        layout.addLayout(actions)
        if mode == "channel":
            QTimer.singleShot(0, self, self.load_channel)
        elif mode == "history":
            QTimer.singleShot(0, self, lambda: self.load_history(query))
        elif mode == "manage":
            QTimer.singleShot(0, self, self.load_imports)

    def done(self, result):
        self.cancelled.set()
        self.rows.clear()
        self.items.clear()
        if self.mode == "history":
            self.detail.clear()
        elif self.mode == "channel":
            self.log.clear()
            self.loaded.clear()
        super().done(result)

    def scoped(self):
        return {"p_workspace": self.workspace}

    def run(self, operation, completed, notice):
        if self.completed is not None or self.cancelled.is_set():
            return
        self.completed = completed
        self.primary.setEnabled(False)
        self.status.setText(notice)

        def authorized():
            if not self.same_user():
                raise PermissionError("Your session changed. Reopen Slack history to continue.")
            return operation()

        job = Job(authorized)
        job.signals.finished.connect(self.finished_job)
        QThreadPool.globalInstance().start(job)

    @Slot(object)
    def finished_job(self, result):
        completed, self.completed = self.completed, None
        if completed is None or self.cancelled.is_set():
            return
        if not self.same_user():
            self.reject()
            return
        if "error" in result:
            self.status.setText(result["error"])
            self.primary.setEnabled(
                (self.mode == "import" and bool(self.rows))
                or (self.mode == "manage" and self.items.currentItem() is not None)
            )
        else:
            completed(result["value"])

    def same_user(self):
        return str(getattr(self.service.user, "id", "")) == self.user

    def choose(self):
        if self.completed is None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Choose Slack export", "", "ZIP files (*.zip)"
            )
            if path:
                self.load_zip(path)

    def dragEnterEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if (
            self.completed is None
            and len(urls) == 1
            and urls[0].isLocalFile()
            and urls[0].toLocalFile().lower().endswith(".zip")
        ):
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        self.load_zip(event.mimeData().urls()[0].toLocalFile())

    def load_zip(self, path):
        if self.completed is not None:
            return
        self.rows = []
        self.items.clear()
        self.run(lambda: slack.preview(path), self.show_preview, "Reading the Slack export…")

    def show_preview(self, result):
        self.rows, counts, skipped = result
        for name, count in sorted(counts.items()):
            item = QListWidgetItem(f"#{name}  ·  {count:,} messages")
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.items.addItem(item)
        if self.rows:
            oldest = date_label(min(float(row["source_ts"]) for row in self.rows))
            newest = date_label(max(float(row["source_ts"]) for row in self.rows))
            message = f"{len(self.rows):,} messages · {oldest} to {newest}"
            if skipped:
                message += f" · {skipped:,} day files outside eligible channels skipped"
        else:
            message = "No eligible public-channel messages found."
        self.status.setText(message)
        self.primary.setEnabled(bool(self.rows))

    def start_import(self):
        checked = {
            self.items.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.items.count())
            if self.items.item(index).checkState() == Qt.CheckState.Checked
        }
        rows = [row for row in self.rows if row["channel_name"] in checked]
        if not rows:
            self.status.setText("Select at least one channel to import.")
            return
        self.run(
            lambda: slack.upload(self.service, self.workspace, rows, self.cancelled.is_set),
            self.imported,
            "Importing history… Keep Aedrova open. You can retry with the same ZIP.",
        )

    def imported(self, count):
        self.rows = []
        self.items.clear()
        self.status.setText(
            f"{count:,} archived messages in this import. Previously imported messages are skipped."
        )
        refresh_archive(self.parentWidget())
        self.primary.setText("View imported history")
        self.primary.clicked.disconnect(self.start_import)
        self.primary.clicked.connect(self.view_imported)
        self.choose_button.setEnabled(False)
        self.setAcceptDrops(False)
        self.primary.setEnabled(True)

    def view_imported(self):
        parent = self.parentWidget()
        service, workspace = self.service, self.workspace
        self.accept()
        open_slack_history(parent, service, workspace, mode="history")

    def load_channel(self, before=None):
        self.run(
            lambda: self.service.slack_channel_messages(
                self.workspace, self.channel["channel_id"], before, 100
            ),
            lambda rows: self.channel_loaded(rows, before),
            "Loading messages…",
        )

    def channel_loaded(self, rows, before):
        self.loaded = [*rows, *self.loaded] if before else list(rows)
        if rows:
            self.oldest = rows[0]["source_ts"]
        self.log.setPlainText(format_messages(self.loaded) or "No messages in this channel.")
        bar = self.log.verticalScrollBar()
        bar.setValue(bar.minimum() if before else bar.maximum())
        self.earlier.setVisible(len(rows) >= 100)
        self.status.setText(f"{len(self.loaded):,} messages shown. Read-only.")

    def load_history(self, query):
        self.run(
            lambda: self.service.rpc(
                "slack_history",
                {
                    **self.scoped(),
                    "p_query": query,
                    "p_limit": 50,
                },
            ),
            self.history_loaded,
            "Finding Slack messages…",
        )

    def history_loaded(self, rows):
        self.items.clear()
        for row in rows:
            item = QListWidgetItem(
                f"#{row['channel_name']} · {row['author']} · {date_label(row['source_ts'])}"
            )
            item.setData(Qt.ItemDataRole.UserRole, row)
            self.items.addItem(item)
            if row["id"] == self.selected:
                self.items.setCurrentItem(item)
        if rows and self.items.currentRow() < 0:
            self.items.setCurrentRow(0)
        self.status.setText(
            "Showing up to 50 messages. Search to narrow results."
            if rows
            else "No Slack messages found."
        )

    def show_record(self, item, _previous):
        if item is None:
            self.detail.clear()
            return
        row = item.data(Qt.ItemDataRole.UserRole)
        heading = f"#{row['channel_name']} · {row['author']} · {date_label(row['source_ts'])}"
        if row.get("thread_ts"):
            heading += " · Thread reply"
        lines = [heading, "", row["body"]]
        if row.get("reactions"):
            lines += ["", " · ".join(f":{key}: {count}" for key, count in row["reactions"].items())]
        if row.get("links"):
            lines += ["", *row["links"]]
        self.detail.setPlainText("\n".join(lines))

    def load_imports(self):
        self.run(
            lambda: self.service.rpc("list_slack_imports", self.scoped()),
            self.imports_loaded,
            "Finding imports…",
        )

    def imports_loaded(self, rows):
        self.items.clear()
        for row in rows:
            state = "Archived" if row["published_at"] else "Unfinished"
            item = QListWidgetItem(
                f"{state} · {row['message_count']:,} messages · {row['created_at'][:10]}"
            )
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.items.addItem(item)
        self.status.setText("" if rows else "No Slack imports yet.")

    def selection_changed(self, item, _previous):
        self.primary.setEnabled(item is not None and self.completed is None)

    def remove(self):
        item = self.items.currentItem()
        if (
            not item
            or QMessageBox.question(
                self,
                "Remove Slack import",
                "Remove this import from history, search and agent context?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        identifier = item.data(Qt.ItemDataRole.UserRole)
        self.run(
            lambda: self.service.rpc(
                "remove_slack_import",
                {
                    **self.scoped(),
                    "p_import": identifier,
                },
            ),
            lambda _: (refresh_archive(self.parentWidget()), self.load_imports()),
            "Removing Slack history…",
        )


def date_label(value):
    return datetime.fromtimestamp(float(value), UTC).strftime("%b %d, %Y")


def stamp_label(value):
    return datetime.fromtimestamp(float(value), UTC).strftime("%b %d, %Y %H:%M UTC")


def format_messages(rows):
    """A channel as plain text: who, when, what. Imported text is shown, never interpreted."""
    blocks = []
    for row in rows:
        reply = "Reply · " if row.get("thread_ts") else ""
        lines = [f"{reply}{row['author']} · {stamp_label(row['source_ts'])}", row["body"]]
        if row.get("reactions"):
            lines.append(" · ".join(f":{key}: {count}" for key, count in row["reactions"].items()))
        lines.extend(row.get("links") or [])
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def refresh_archive(widget, *, force=True):
    """Ask the main window to reload its 'From Slack' channels, after an import or removal."""
    while widget is not None:
        archive = getattr(widget, "slack_archive", None)
        if archive is not None:
            archive.refresh(force=force)
            return
        widget = widget.parentWidget()


class SlackImportPanel(QWidget):
    """Choose or drop an export, check what will come in, then import it. Used inside setup."""

    imported = Signal(int)
    progressed = Signal(int, int)

    def __init__(self, service, workspace, parent=None):
        super().__init__(parent)
        self.service, self.workspace = service, str(workspace)
        self.user = str(service.user.id)
        self.cancelled = Event()
        self.rows = []
        self.busy = False
        self.finished = False
        self.setAcceptDrops(True)
        self.setAccessibleName("Slack import")
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(10)
        self.drop = QFrame()
        self.drop.setObjectName("SlackDrop")
        zone = QVBoxLayout(self.drop)
        zone.setContentsMargins(16, 18, 16, 16)
        zone.setSpacing(10)
        self.drop_text = label("Drop your Slack export ZIP here, or choose it.", "muted", wrap=True)
        self.drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zone.addWidget(self.drop_text)
        row = QHBoxLayout()
        row.addStretch()
        self.choose_button = button("Choose ZIP", role="outline")
        self.choose_button.clicked.connect(self.choose)
        row.addWidget(self.choose_button)
        row.addStretch()
        zone.addLayout(row)
        column.addWidget(self.drop)
        self.items = QListWidget()
        self.items.setAccessibleName("Channels to import")
        self.items.setMaximumHeight(92)
        self.items.hide()
        column.addWidget(self.items)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(4)
        self.bar.hide()
        column.addWidget(self.bar)
        self.status = label("", "muted", wrap=True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        column.addWidget(self.status)
        self.primary = button("Import history", role="primary")
        self.primary.setMinimumHeight(44)
        self.primary.setEnabled(False)
        self.primary.clicked.connect(self.start_import)
        column.addWidget(self.primary)
        self.progressed.connect(self.show_progress)

    # -- choosing -----------------------------------------------------------------
    def choose(self):
        if self.busy or self.finished:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Choose Slack export", "", "ZIP files (*.zip)")
        if path:
            self.load_zip(path)

    def dragEnterEvent(self, event):  # noqa: N802
        urls = event.mimeData().urls()
        if (
            not self.busy
            and not self.finished
            and len(urls) == 1
            and urls[0].isLocalFile()
            and urls[0].toLocalFile().lower().endswith(".zip")
        ):
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802
        self.load_zip(event.mimeData().urls()[0].toLocalFile())

    def load_zip(self, path):
        if self.busy or self.finished:
            return
        self.rows = []
        self.items.clear()
        self.primary.setEnabled(False)
        self.run(lambda: slack.preview(path), self.show_preview, "Reading the Slack export…")

    def show_preview(self, result):
        self.rows, counts, skipped = result
        self.items.clear()
        for name, count in sorted(counts.items()):
            item = QListWidgetItem(f"#{name}  ·  {count:,} messages")
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.items.addItem(item)
        self.items.setVisible(bool(self.rows))
        if self.rows:
            oldest = date_label(min(float(row["source_ts"]) for row in self.rows))
            newest = date_label(max(float(row["source_ts"]) for row in self.rows))
            message = f"{len(self.rows):,} messages · {oldest} to {newest}"
            if skipped:
                message += f" · {skipped:,} day files in private or shared channels skipped"
        else:
            message = "No eligible public-channel messages found."
        self.status.setText(message)
        self.primary.setEnabled(bool(self.rows))

    # -- importing ----------------------------------------------------------------
    def start_import(self):
        checked = {
            self.items.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.items.count())
            if self.items.item(index).checkState() == Qt.CheckState.Checked
        }
        rows = [row for row in self.rows if row["channel_name"] in checked]
        if not rows:
            self.status.setText("Select at least one channel to import.")
            return
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.show()
        self.items.setEnabled(False)
        self.run(
            lambda: slack.upload(
                self.service,
                self.workspace,
                rows,
                self.cancelled.is_set,
                self.progressed.emit,
            ),
            self.done_importing,
            "Importing history… Keep Aedrova open. Choose the same ZIP again to resume.",
        )

    def show_progress(self, sent, total):
        self.bar.setRange(0, max(total, 1))
        self.bar.setValue(sent)

    def done_importing(self, count):
        self.finished = True
        refresh_archive(self.parentWidget())
        self.rows = []
        self.items.hide()
        self.drop.hide()
        self.bar.hide()
        self.primary.hide()
        self.status.setText(
            f"Done. {count:,} messages imported. Look for your channels under From Slack in the "
            "sidebar. Anything already imported was skipped."
        )
        self.imported.emit(int(count))

    # -- running ------------------------------------------------------------------
    def run(self, operation, completed, notice):
        self.busy = True
        self.primary.setEnabled(False)
        self.choose_button.setEnabled(False)
        self.status.setText(notice)
        self.completed = completed

        def authorized():
            if str(getattr(self.service.user, "id", "")) != self.user:
                raise PermissionError("Your session changed. Reopen setup to continue.")
            return operation()

        job = Job(authorized)
        job.signals.finished.connect(self.finished_job)
        QThreadPool.globalInstance().start(job)

    @Slot(object)
    def finished_job(self, result):
        self.busy = False
        self.choose_button.setEnabled(not self.finished)
        if self.cancelled.is_set():
            return
        if "error" in result:
            self.status.setText(result["error"])
            self.items.setEnabled(True)
            self.bar.hide()
            self.primary.setEnabled(bool(self.rows))
        else:
            self.completed(result["value"])

    def stop(self):
        self.cancelled.set()
