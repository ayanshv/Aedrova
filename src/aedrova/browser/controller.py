"""Runs agent actions on the panel's page, one at a time, under the composer's access mode."""

import base64
import json
from collections import deque
from concurrent.futures import Future

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, Qt, QTimer, Signal, Slot

from aedrova.browser import scripts
from aedrova.browser.policy import (
    ACTIONS,
    Refusal,
    check_url,
    decide,
    host_of,
    sensitive_field,
    untrusted,
)

APPLICATION_WORLD = 1  # an isolated JavaScript world: the page cannot reach our scripts
LOAD_TIMEOUT = 20000


class Stopped(Exception):
    """The person pressed Stop."""


class BrowserController(QObject):
    requested = Signal(object)

    def __init__(self, panel, mode=lambda: "ask", resolver=None):
        super().__init__(panel)
        self.panel, self.mode = panel, mode
        self.resolver = resolver
        self.queue = deque()
        self.busy = False
        self.stopped = False
        self.requested.connect(self.accept, Qt.ConnectionType.QueuedConnection)
        panel.stop_requested.connect(self.stop)
        panel.allow_again.clicked.connect(self.resume)

    # -- called from any thread -----------------------------------------------------
    def submit(self, action, args=None):
        future = Future()
        self.requested.emit((action, dict(args or {}), future))
        return future

    # -- on the interface thread ----------------------------------------------------
    @Slot(object)
    def accept(self, job):
        action, args, future = job
        if self.stopped:
            future.set_exception(Stopped("The person stopped the browser. Ask them to allow it."))
        elif action not in ACTIONS:
            future.set_exception(Refusal("That browser action is not available."))
        else:
            self.queue.append(job)
            self.pump()

    def pump(self):
        if self.busy or not self.queue:
            return
        self.busy = True
        self.panel.ensure_view()
        self.panel.set_agent_active(True)
        action, args, future = self.queue.popleft()
        try:
            getattr(self, "do_" + action)(args, lambda value: self.finish(future, value))
        except Exception as error:  # a refusal or a bad argument ends only this action
            self.finish(future, error)

    def finish(self, future, outcome):
        if not future.done():
            if isinstance(outcome, Exception):
                future.set_exception(outcome)
            else:
                future.set_result(outcome)
        self.busy = False
        if self.queue:
            QTimer.singleShot(0, self.pump)
        else:
            QTimer.singleShot(400, self.settle)

    def settle(self):
        if not self.busy and not self.queue and not self.stopped:
            self.panel.set_agent_active(False)

    def stop(self):
        self.stopped = True
        while self.queue:
            self.queue.popleft()[2].set_exception(Stopped("The person stopped the browser."))
        if self.panel.pending is not None:
            self.panel.answer(False)
        self.panel.set_agent_active(False)
        self.panel.set_stopped(True)

    def resume(self):
        self.stopped = False
        self.panel.banner.hide()

    # -- helpers --------------------------------------------------------------------
    def page(self):
        self.panel.ensure_view()
        return self.panel.page

    def run_script(self, source, then):
        """Results come back as JSON text: object results are not reliable across platforms."""

        def parsed(text):
            try:
                then(json.loads(text) if isinstance(text, str) and text else None)
            except ValueError:
                then(None)

        wrapped = "JSON.stringify(" + source.strip().rstrip(";") + ")"
        self.page().runJavaScript(wrapped, APPLICATION_WORLD, parsed)

    def ask_then(self, question, proceed, done):
        def decided(allowed):
            if allowed:
                proceed()
            else:
                done(Refusal("The person said no. Do not try the same thing again; ask them."))

        self.panel.ask(question, decided)

    def after_load(self, then, timeout=LOAD_TIMEOUT):
        state = {"done": False}

        def once(*_):
            if not state["done"]:
                state["done"] = True
                try:
                    self.page().loadFinished.disconnect(once)
                except (RuntimeError, TypeError):
                    pass
                QTimer.singleShot(250, then)  # let scripts on the page settle

        self.page().loadFinished.connect(once)
        QTimer.singleShot(timeout, once)

    def summary(self, data):
        elements = "\n".join(
            f"[{e['ref']}] {e['tag']}"
            + (f" ({e['type']})" if e["type"] and e["type"] != e["tag"] else "")
            + (f": {e['text']}" if e["text"] else "")
            for e in data.get("elements", [])
        )
        body = (
            f"Title: {data.get('title', '')}\nURL: {data.get('url', '')}\n\n"
            f"Page text:\n{data.get('text', '')}\n\nElements you can use by number:\n{elements}"
        )
        return untrusted(body)

    # -- actions --------------------------------------------------------------------
    def do_open(self, args, done):
        url = check_url(
            args.get("url", ""), **({"resolver": self.resolver} if self.resolver else {})
        )
        host = host_of(url)

        def go():
            self.panel.approved.add(host)
            self.after_load(lambda: self.do_read({}, done))
            self.panel.view.load(self.panel.page.url().fromUserInput(url))

        if decide(self.mode(), "open", host=host, approved=self.panel.approved) == "ask":
            self.ask_then(f"Let Aedrova open {host}?", go, done)
        else:
            go()

    def do_read(self, args, done):
        def got(data):
            if not isinstance(data, dict):
                done(Refusal("This page could not be read."))
                return
            done(self.summary(data))

        self.run_script(scripts.READ, got)

    def do_screenshot(self, args, done):
        pixmap = self.panel.view.grab()
        if pixmap.width() > 1280:
            pixmap = pixmap.scaledToWidth(1280, Qt.TransformationMode.SmoothTransformation)
        data, buffer = QByteArray(), QBuffer()
        buffer.setBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        done({"image": base64.b64encode(bytes(data)).decode()})

    def do_scroll(self, args, done):
        amount = max(-5000, min(5000, int(args.get("pixels", 600))))
        self.run_script(scripts.SCROLL % amount, lambda result: done("Scrolled."))

    def do_back(self, args, done):
        self.after_load(lambda: self.do_read({}, done))
        self.panel.view.back()

    def do_wait(self, args, done):
        seconds = max(0.0, min(10.0, float(args.get("seconds", 1))))
        QTimer.singleShot(int(seconds * 1000), lambda: done("Waited."))

    def inspect(self, ref, then, done):
        script = scripts.INSPECT % json.dumps(str(ref))

        def got(info):
            if not isinstance(info, dict) or info.get("error"):
                done(Refusal((info or {}).get("error", "That element is not available.")))
            else:
                then(info)

        self.run_script(script, got)

    def point(self, result):
        if isinstance(result, dict) and "x" in result:
            self.panel.cursor.move_to(result["x"], result["y"])

    def do_click(self, args, done):
        ref = args.get("ref")

        def with_info(info):
            def go():
                def clicked(result):
                    if isinstance(result, dict) and result.get("error"):
                        done(Refusal(result["error"]))
                        return
                    self.point(result)
                    QTimer.singleShot(700, lambda: self.do_read({}, done))

                self.run_script(scripts.CLICK % json.dumps(str(ref)), clicked)

            host = self.panel.current_host()
            if decide(self.mode(), "click", host=host, info=info) == "ask":
                what = info.get("text") or info.get("aria") or info.get("tag")
                self.ask_then(f"Let Aedrova click “{what}” on {host}?", go, done)
            else:
                go()

        self.inspect(ref, with_info, done)

    def do_type(self, args, done):
        ref, text = args.get("ref"), str(args.get("text", ""))[:2000]
        submit = bool(args.get("submit", False))

        def with_info(info):
            if not info.get("editable"):
                done(Refusal("That element is not a text field."))
                return
            if sensitive_field(info):
                done(
                    Refusal(
                        "Aedrova never fills passwords, card numbers, security codes or "
                        "one-time codes. Ask the person to enter it in the panel themselves."
                    )
                )
                return

            def go():
                def typed(result):
                    if isinstance(result, dict) and result.get("error"):
                        done(Refusal(result["error"]))
                        return
                    self.point(result)
                    QTimer.singleShot(700, lambda: self.do_read({}, done))

                script = scripts.TYPE % (
                    json.dumps(str(ref)),
                    json.dumps(text),
                    "true" if submit else "false",
                )
                self.run_script(script, typed)

            host = self.panel.current_host()
            if decide(self.mode(), "type", host=host, info=info) == "ask":
                shown = text if len(text) <= 40 else text[:40] + "…"
                self.ask_then(f"Let Aedrova type “{shown}” on {host}?", go, done)
            else:
                go()

        self.inspect(ref, with_info, done)
