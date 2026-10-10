"""Native startup overview; one source of truth with Buds and the central agent."""

import json
import math
from datetime import datetime
from urllib.parse import urlencode
from uuid import uuid4

from PySide6.QtCore import QPointF, QRectF, Qt, QThreadPool, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QScrollArea,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.design_system import FlowActions
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.dots import open_dots
from aedrova.desktop.loading import set_loading
from aedrova.desktop.projects import Job
from aedrova.dots.client import client

RANGES = (("24H", "24h"), ("7D", "7d"), ("30D", "30d"), ("90D", "90d"), ("12M", "12m"))


def age(value):
    if not value:
        return "Not refreshed yet"
    return "Updated " + datetime.fromtimestamp(value).strftime("%b %d, %H:%M")


def clear(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


class ActivityChart(QWidget):
    """Observed events by interval, not a fabricated total or trend forecast."""

    def __init__(self, window, values, parent=None, *, detailed=False):
        super().__init__(parent)
        self.window, self.values = window, values
        self.detailed, self.hover = detailed, None
        self.setMouseTracking(detailed)
        self.setMinimumHeight(72)
        self.setAccessibleName("Observed activity by interval: " + ", ".join(map(str, values)))
        self.setToolTip("Observed records only. Missing history is not zero activity.")

    def mouseMoveEvent(self, event):  # noqa: N802
        if not self.detailed or not self.values:
            return
        fraction = (event.position().x() - 40) / max(self.width() - 56, 1)
        self.hover = max(0, min(len(self.values) - 1, round(fraction * (len(self.values) - 1))))
        QToolTip.showText(
            event.globalPosition().toPoint(),
            f"Interval {self.hover + 1} · {self.values[self.hover]} observed",
            self,
        )
        self.update()

    def leaveEvent(self, event):  # noqa: N802
        self.hover = None
        QToolTip.hideText()
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.values:
            return
        t = self.window.theme
        left, bottom = (40, 32) if self.detailed else (8, 8)
        area = QRectF(
            left, 16, max(1, self.width() - left - 16), max(1, self.height() - bottom - 16)
        )
        maximum = (
            max(4, math.ceil(max(self.values) / 4) * 4)
            if self.detailed
            else max(max(self.values), 1)
        )
        painter.setPen(QPen(QColor(t.border), 1, Qt.PenStyle.DashLine))
        for step in range(5 if self.detailed else 1):
            y = area.bottom() - area.height() * step / 4
            painter.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            if self.detailed:
                painter.setPen(QColor(t.muted))
                painter.drawText(
                    QRectF(0, y - 9, 30, 18), Qt.AlignmentFlag.AlignRight, f"{maximum * step / 4:g}"
                )
                painter.setPen(QPen(QColor(t.border), 1, Qt.PenStyle.DashLine))
        points = [
            QPointF(
                area.left() + i * area.width() / max(len(self.values) - 1, 1),
                area.bottom() - area.height() * value / maximum,
            )
            for i, value in enumerate(self.values)
        ]
        path = QPainterPath(points[0])
        for point in points[1:]:
            path.lineTo(point)
        fill = QPainterPath(path)
        fill.lineTo(points[-1].x(), area.bottom())
        fill.lineTo(points[0].x(), area.bottom())
        fill.closeSubpath()
        tint = QColor(t.accent)
        tint.setAlpha(15)
        painter.fillPath(fill, tint)
        painter.setPen(QPen(QColor(t.accent), 2))
        painter.drawPath(path)
        painter.setBrush(QColor(t.accent))
        painter.setPen(Qt.PenStyle.NoPen)
        for i, point in enumerate(points):
            if self.values[i] or i == self.hover:
                painter.drawEllipse(point, 3, 3)
        if self.detailed:
            painter.setPen(QColor(t.muted))
            painter.drawText(
                QRectF(area.left(), area.bottom() + 10, area.width(), 20),
                Qt.AlignmentFlag.AlignLeft,
                "Period start",
            )
            painter.drawText(
                QRectF(area.left(), area.bottom() + 10, area.width(), 20),
                Qt.AlignmentFlag.AlignRight,
                "Latest interval",
            )
            if self.hover is not None:
                x = points[self.hover].x()
                painter.setPen(QPen(QColor(t.muted), 1, Qt.PenStyle.DotLine))
                painter.drawLine(QPointF(x, area.top()), QPointF(x, area.bottom()))


class MetricGrid(QWidget):
    """Equal-width summaries that wrap instead of compressing their labels."""

    def __init__(self):
        super().__init__()
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(14)
        self.tiles, self.columns = [], 0

    def addWidget(self, widget):  # noqa: N802
        self.tiles.append(widget)
        self.arrange()

    def arrange(self):
        columns = max(1, min(3, len(self.tiles), self.width() // 220))
        while self.grid.count():
            self.grid.takeAt(0)
        for column in range(3):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, tile in enumerate(self.tiles):
            self.grid.addWidget(tile, index // columns, index % columns)
        self.columns = columns

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        columns = max(1, min(3, len(self.tiles), self.width() // 220))
        if columns != self.columns:
            self.arrange()


class MetricDetail(AppDialog):
    def __init__(self, pulse, metric):
        super().__init__(pulse.window)
        self.setWindowTitle("Aedrova · " + metric["label"])
        self.resize(680, 660)
        self.setMinimumSize(480, 420)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)
        outer.addWidget(label(metric["dot_name"] + " / " + metric["category"].upper(), "section"))
        outer.addWidget(label(metric["label"], "heading"))
        outer.addWidget(label(f"{metric['value']} {metric['unit']}", "display"))
        outer.addWidget(
            label(metric["coverage"] + " · " + age(metric["updated_at"]), "muted", wrap=True)
        )
        if metric["stale"]:
            outer.addWidget(
                label("Cached data · refresh this source for a current read.", "muted", wrap=True)
            )
        if metric["trend"]:
            outer.addWidget(ActivityChart(pulse.window, metric["trend"]))
            outer.addWidget(label("Observed activity across the selected period", "muted"))
        outer.addWidget(label(metric["comparison"], "muted", wrap=True))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        body = QVBoxLayout(content)
        body.setSpacing(16)
        for item in metric["items"]:
            body.addWidget(label(item["title"], "title", wrap=True))
            if item["detail"] != item["title"]:
                body.addWidget(label(item["detail"], wrap=True))
            body.addWidget(
                label(
                    age(item["timestamp"]).replace("Updated ", "")
                    if item["timestamp"]
                    else "Date unavailable",
                    "muted",
                )
            )
        if not metric["items"]:
            body.addWidget(label("No matching records in this source sample.", "muted", wrap=True))
        body.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        actions = FlowActions()
        for text, operation in (
            ("Investigate with agent", lambda: pulse.investigate(metric)),
            ("Discuss in conversation", lambda: pulse.discuss(metric)),
            ("Build from this insight", lambda: pulse.build(metric)),
        ):
            control = button(text, role="outline")
            control.clicked.connect(lambda checked=False, fn=operation: (self.accept(), fn()))
            actions.addWidget(control)
        outer.addLayout(actions)
        done = button("Done")
        done.clicked.connect(self.accept)
        outer.addWidget(done, alignment=Qt.AlignmentFlag.AlignRight)


class PulsePage(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.workspace, self.user = "", ""
        self.generation, self.job, self.pending = 0, None, False
        self.access_signature = None
        self.data, self.detail = {}, None
        self.source_id, self.selected_metric, self.table_view = "", "", False
        self.setObjectName("Pulse")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(12)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(4)
        self.workspace_label = label("YOUR STARTUP", "section")
        titles.addWidget(self.workspace_label)
        titles.addWidget(label("Pulse", "heading"))
        titles.addWidget(
            label("See what changed. Understand why. Decide what’s next.", "muted", wrap=True)
        )
        header.addLayout(titles, 1)
        manage = button("Connect your stack", role="outline")
        manage.clicked.connect(lambda: open_dots(window))
        header.addWidget(manage)
        outer.addLayout(header)
        controls = FlowActions()
        self.period = ChoiceBox()
        for text, value in RANGES:
            self.period.addItem(text, value)
        self.period.setCurrentIndex(1)
        self.period.setAccessibleName("Pulse time range")
        self.period.currentIndexChanged.connect(self.change_period)
        controls.addWidget(self.period)
        refresh = button("Check sources", "Reload cached source status")
        refresh.clicked.connect(lambda: self.load())
        controls.addWidget(refresh)
        ask = button("Ask your agent", role="primary")
        ask.clicked.connect(self.ask)
        controls.addWidget(ask)
        outer.addLayout(controls)
        self.status = label(
            "Connect your stack to bring real startup context here.", "muted", wrap=True
        )
        self.status.setAccessibleName("Pulse loading and connection status")
        outer.addWidget(self.status)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content = QWidget()
        self.body = QVBoxLayout(self.content)
        self.body.setContentsMargins(0, 0, 0, 16)
        self.body.setSpacing(18)
        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll, 1)
        self.timer = QTimer(self)
        self.timer.setInterval(60000)
        self.timer.timeout.connect(lambda: self.load() if self.isVisible() else None)
        self.timer.start()
        self.render()

    def key(self):
        return f"pulse/{self.user}/{self.workspace}/pins"

    def reset(self):
        self.generation += 1
        self.pending = False
        set_loading(self, self.scroll.viewport(), False)
        self.job = None
        self.data = {}
        if self.detail:
            self.detail.reject()
            self.detail = None
        self.render()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.load()

    def valid(self):
        user = self.window.current_user()
        return bool(
            user
            and str(user.id) == self.user
            and self.window.workspace_id == self.workspace
            and self.window.connected.active
        )

    def sync_access(self):
        user = self.window.current_user()
        account = self.window.account_dialog
        workspace = self.window.workspace_id
        signature = (
            str(user.id) if user else "",
            workspace,
            tuple(
                sorted(
                    (r["id"], r["version"])
                    for r in account.snapshot.get("dots", [])
                    if r["workspace_id"] == workspace
                )
            ),
            tuple(
                sorted(
                    (r["user_id"], r["role"])
                    for r in account.snapshot.get("members", [])
                    if r["workspace_id"] == workspace
                )
            ),
        )
        if signature != self.access_signature:
            self.access_signature = signature
            self.reset()
            if self.isVisible():
                self.load()

    def load(self, dot_id=None):
        user = self.window.current_user()
        if not user or not self.window.connected.active:
            self.reset()
            self.status.setText("Sign in to your workspace to connect its sources.")
            return
        workspace, user_id = self.window.workspace_id, str(user.id)
        if (self.workspace, self.user) != (workspace, user_id):
            self.workspace, self.user = workspace, user_id
            self.reset()
        if self.pending:
            return
        self.pending = True
        self.generation += 1
        generation, period = self.generation, self.period.currentData()
        set_loading(self, self.scroll.viewport(), True, "gallery")
        self.workspace_label.setText(self.window.workspace.name.upper())

        def fork():
            try:
                return {"service": self.window.account_dialog.service.fork_for_context()}
            except Exception:
                return {"error": "Sign in again to check Pulse."}

        def ready(value):
            if generation != self.generation or not self.valid():
                if "service" in value:
                    value["service"].close_context()
                return
            if "error" in value:
                self.data = {}
                self.render()
                if self.detail:
                    self.detail.reject()
                self.pending = False
                set_loading(self, self.scroll.viewport(), False)
                self.status.setText(value["error"])
                return
            service = value["service"]

            def work():
                try:
                    api = client(service)
                    if dot_id:
                        return api.request(
                            "/api/pulse/refresh",
                            {"workspace": workspace, "dot": dot_id, "period": period},
                            timeout=60,
                        )
                    return api.request(
                        "/api/pulse?" + urlencode({"workspace": workspace, "period": period})
                    )
                except RuntimeError as error:
                    raise ValueError(str(error)) from None
                finally:
                    service.close_context()

            job = Job(work)
            self.job = job

            def finished(result):
                if generation != self.generation or not self.valid():
                    return
                self.pending, self.job = False, None
                set_loading(self, self.scroll.viewport(), False)
                if "error" in result:
                    # Never leave old privileged data visible after an access error.
                    self.data = {}
                    self.render()
                    self.status.setText(result["error"])
                    if self.detail:
                        self.detail.reject()
                else:
                    self.data = result["value"]
                    states = getattr(self.window, "dot_connection_states", {})
                    for source in self.data.get("sources", []):
                        states[(self.user, source["id"], source["version"])] = {
                            "status": source["status"],
                            "last_sync": source["last_sync"],
                        }
                    self.window.dot_connection_states = states
                    rows = [
                        r
                        for r in self.window.account_dialog.snapshot.get("dots", [])
                        if r["workspace_id"] == self.workspace
                    ]
                    self.window.ai_team_section.sync(rows, self.workspace)
                    self.render()
                    self.status.setText(
                        "Some source reads failed. Other sources remain available; "
                        "cached data is labeled."
                        if self.data.get("failed_tools")
                        else "Source reads are on demand. Cached evidence is shared with "
                        "your agent."
                    )

            job.signals.finished.connect(finished)
            QThreadPool.globalInstance().start(job)

        accepted = self.window.connected.enqueue("pulse-" + str(uuid4()), fork, ready)
        if not accepted:
            self.pending = False
            set_loading(self, self.scroll.viewport(), False)
            self.status.setText("Reconnect your workspace to check Pulse.")

    def change_period(self):
        self.reset()
        self.load()

    def pins(self):
        try:
            result = json.loads(self.window.settings.value(self.key(), "[]"))
            return result if isinstance(result, list) else []
        except (ValueError, TypeError):
            return []

    def pin(self, metric):
        pins = self.pins()
        identifier = metric["id"]
        if identifier in pins:
            pins.remove(identifier)
        else:
            pins.insert(0, identifier)
        self.window.settings.setValue(self.key(), json.dumps(pins[:36]))
        self.render()

    def move(self, metric):
        pins = self.pins()
        if metric["id"] in pins:
            pins.remove(metric["id"])
        pins.insert(0, metric["id"])
        self.window.settings.setValue(self.key(), json.dumps(pins[:36]))
        self.render()

    def apply_theme(self):
        t = self.window.theme
        self.setStyleSheet(f"""
            QWidget#Pulse {{ background: {t.canvas}; }}
            QFrame#PulsePanel {{ background: {t.bg}; border: 1px solid {t.border};
                                  border-radius: 10px; }}
            QPushButton[pulseMetric="true"] {{ background: {t.bg};
                border: 1px solid {t.border}; border-radius: 10px;
                padding: 18px; text-align: left; min-height: 84px; }}
            QPushButton[pulseMetric="true"]:hover {{ background: {t.accent_bg}; }}
            QPushButton[pulseMetric="true"]:checked {{ border-color: {t.accent};
                background: {t.accent_bg}; color: {t.accent_text}; }}
        """)

    def panel(self):
        frame = QFrame()
        frame.setObjectName("PulsePanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        return frame, layout

    def select_metric(self, identifier):
        self.selected_metric = identifier
        self.render()

    def filter_source(self, identifier):
        self.source_id = identifier
        self.render()

    def switch_view(self, table):
        self.table_view = table
        self.render()

    def render(self):
        clear(self.body)
        self.apply_theme()
        sources = self.data.get("sources", [])
        metrics = self.data.get("metrics", [])
        if not sources:
            frame, body = self.panel()
            body.addWidget(label("Connect your stack.", "heading"))
            body.addWidget(
                label("Your team’s decisions, alongside real activity from your tools.", wrap=True)
            )
            body.addWidget(
                label(
                    "Start with GitHub. Other sources appear when available and "
                    "authorized. No sample metrics are shown here.",
                    "muted",
                    wrap=True,
                )
            )
            connect = button("Connect a Bud", role="primary")
            connect.clicked.connect(lambda: open_dots(self.window))
            body.addWidget(connect, alignment=Qt.AlignmentFlag.AlignLeft)
            self.body.addWidget(frame)
            self.body.addStretch()
            return
        strip, body = self.panel()
        stats = FlowActions()
        connected = sum(s["status"] == "Connected" for s in sources)
        stale = sum(m.get("stale", False) for m in metrics)
        for heading, value in (
            ("Workspace", "Connected" if self.valid() else "Reconnect"),
            ("Sources", f"{connected} / {len(sources)} connected"),
            ("Available metrics", str(len(metrics))),
            ("Evidence", "Needs refresh" if stale else "Cached source reads"),
        ):
            cell = QWidget()
            column = QVBoxLayout(cell)
            column.setContentsMargins(0, 0, 16, 0)
            column.addWidget(label(heading, "muted"))
            column.addWidget(label(value, wrap=True))
            cell.setMinimumWidth(145)
            cell.setMinimumHeight(68)
            stats.addWidget(cell)
        body.addLayout(stats)
        self.body.addWidget(strip)
        heading = FlowActions()
        heading.addWidget(label("Insights", "heading"))
        source_filter = ChoiceBox()
        source_filter.setAccessibleName("Filter Pulse by source")
        source_filter.addItem("All sources", "")
        for source in sources:
            source_filter.addItem(source["name"], source["id"])
        index = source_filter.findData(self.source_id)
        source_filter.setCurrentIndex(max(0, index))
        self.source_id = source_filter.currentData()
        source_filter.currentIndexChanged.connect(
            lambda: self.filter_source(source_filter.currentData())
        )
        heading.addWidget(source_filter)
        heading.addWidget(label(self.period.currentText() + " · observed records", "muted"))
        self.body.addLayout(heading)
        pins = self.pins()
        metrics = [m for m in metrics if not self.source_id or m["dot"] == self.source_id]
        metrics.sort(key=lambda m: pins.index(m["id"]) if m["id"] in pins else 1000)
        if metrics:
            if self.selected_metric not in {m["id"] for m in metrics}:
                self.selected_metric = metrics[0]["id"]
            tiles = MetricGrid()
            for metric in metrics:
                tile = button(
                    f"{metric['label']}\n{metric['value']} {metric['unit']}\n"
                    f"{metric['dot_name']}" + (" · Needs refresh" if metric["stale"] else ""),
                    "Select " + metric["label"],
                )
                tile.setProperty("pulseMetric", True)
                tile.setCheckable(True)
                tile.setChecked(metric["id"] == self.selected_metric)
                tile.setMinimumWidth(190)
                tile.clicked.connect(lambda checked=False, m=metric: self.select_metric(m["id"]))
                tiles.addWidget(tile)
            self.body.addWidget(tiles)
            metric = next(m for m in metrics if m["id"] == self.selected_metric)
            frame, content = self.panel()
            top = FlowActions()
            top.addWidget(label(metric["label"], "title"))
            for text, table in (("Chart", False), ("Records", True)):
                toggle = button(text, role="tab")
                toggle.setCheckable(True)
                toggle.setChecked(self.table_view == table)
                toggle.clicked.connect(lambda checked=False, value=table: self.switch_view(value))
                top.addWidget(toggle)
            content.addLayout(top)
            content.addWidget(label(f"{metric['value']} {metric['unit']}", "display"))
            content.addWidget(
                label(metric["dot_name"] + " · " + age(metric["updated_at"]), "muted", wrap=True)
            )
            if self.table_view:
                if not metric["items"]:
                    content.addWidget(label("No matching records in this source sample.", "muted"))
                for item in metric["items"]:
                    row = QFrame()
                    row.setObjectName("Quiet")
                    row_layout = QVBoxLayout(row)
                    row_layout.addWidget(label(item["title"], wrap=True))
                    row_layout.addWidget(
                        label(
                            age(item["timestamp"]) if item["timestamp"] else "Date unavailable",
                            "muted",
                        )
                    )
                    content.addWidget(row)
            elif metric["trend"]:
                chart = ActivityChart(self.window, metric["trend"], detailed=True)
                chart.setMinimumHeight(240)
                content.addWidget(chart)
            else:
                content.addWidget(
                    label(
                        "Current snapshot · this source has no activity timeline.",
                        "muted",
                        wrap=True,
                    )
                )
            content.addWidget(
                label(metric["coverage"] + " · " + metric["comparison"], "muted", wrap=True)
            )
            actions = FlowActions()
            for text, fn in (
                ("View details", self.open_detail),
                ("Investigate", self.investigate),
                ("Discuss", self.discuss),
                ("Unpin" if metric["id"] in pins else "Pin", self.pin),
                ("Move first", self.move),
            ):
                control = button(text, role="outline" if text == "Investigate" else "")
                control.clicked.connect(lambda checked=False, m=metric, action=fn: action(m))
                actions.addWidget(control)
            content.addLayout(actions)
            self.body.addWidget(frame)
        else:
            self.body.addWidget(
                label("Refresh an authorized source to see its first insights.", "title", wrap=True)
            )
        frame, content = self.panel()
        content.addWidget(label("Source health", "title"))
        for source in sources:
            if self.source_id and source["id"] != self.source_id:
                continue
            row = FlowActions()
            row.addWidget(label(source["name"]))
            row.addWidget(label(source["status"] + " · " + age(source["last_sync"]), "muted"))
            control = button(
                "Refresh source"
                if source["status"] in {"Connected", "Error", "Syncing"}
                else "Manage access",
                role="outline",
            )
            control.clicked.connect(
                lambda checked=False, s=source: (
                    self.load(s["id"])
                    if s["status"] in {"Connected", "Error", "Syncing"}
                    else open_dots(self.window, s["id"])
                )
            )
            row.addWidget(control)
            content.addLayout(row)
        self.body.addWidget(frame)
        signals = [
            s for s in self.data.get("signals", []) if s["metric_id"] in {m["id"] for m in metrics}
        ]
        if signals:
            frame, content = self.panel()
            content.addWidget(label("Recent activity", "title"))
            for signal in signals:
                control = button(signal["source"] + " · " + signal["title"].splitlines()[0][:100])
                metric = next(m for m in metrics if m["id"] == signal["metric_id"])
                control.clicked.connect(lambda checked=False, m=metric: self.open_detail(m))
                content.addWidget(control)
            self.body.addWidget(frame)
        self.body.addStretch()

    def open_detail(self, metric):
        if not self.valid():
            return
        self.detail = MetricDetail(self, metric)
        self.detail.open()

    def ask(self):
        self.window.select_tab(0)
        self.window.composer.editor.setPlainText(
            "@" + self.window.composer.agent_name + ", what changed across our connected sources?"
        )
        self.window.composer.editor.setFocus()

    def investigate(self, metric):
        if not self.valid():
            return
        from aedrova.desktop.dot_analysis import start_analysis

        self.window.select_tab(0)
        task = (
            f"Investigate {metric['label']} from @{metric['dot_name']} "
            f"over {self.period.currentText()}. "
            f"The overview observed {metric['value']} {metric['unit']} at "
            f"{age(metric['updated_at'])}. "
            f"Read current authorized sources, combine relevant team "
            f"decisions, and explain limits. "
            f"Do not infer causality from timing alone. Source citation: {metric['citation']}."
        )
        start_analysis(self.window, task)

    def discuss(self, metric):
        if not self.valid():
            return
        self.window.select_tab(0)
        self.window.composer.editor.setPlainText(
            f"Let’s discuss {metric['label']}: {metric['value']} "
            f"{metric['unit']} from @{metric['dot_name']}. "
            f"{metric['coverage']} [{metric['citation']}]"
        )
        self.window.composer.editor.setFocus()

    def build(self, metric):
        if not self.valid():
            return
        self.window.select_tab(0)
        self.window.composer.editor.setPlainText(f"@{self.window.composer.agent_name}, build ")
        self.window.composer.editor.setFocus()
        self.window.notify(
            "Describe the change you want. Your existing project "
            "permissions and publication approvals apply."
        )
