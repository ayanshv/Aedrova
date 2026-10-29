"""Asynchronous per-reader display translation; never rewrites a stored message."""

from collections import OrderedDict

from PySide6.QtCore import QEvent, QObject, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label
from aedrova.localization import LANGUAGES, RTL, normalize

# Offline essentials remain usable before sign-in or when the service is unavailable.
HINDI = {
    "Workspace": "कार्यस्थान",
    "View": "दृश्य",
    "Help": "सहायता",
    "Language & translation…": "भाषा और अनुवाद…",
    "Language & translation": "भाषा और अनुवाद",
    "Display language": "दिखाने की भाषा",
    "Translate conversations automatically": "बातचीत का अपने आप अनुवाद करें",
    "Save": "सहेजें",
    "Cancel": "रद्द करें",
    "Close": "बंद करें",
    "Continue": "जारी रखें",
    "Continue with Google": "Google के साथ जारी रखें",
    "Connected": "जुड़ा हुआ",
    "Get started with Aedrova": "Aedrova के साथ शुरू करें",
    "Your team’s context. Put to work.": "आपकी टीम का संदर्भ। काम में लाएँ।",
    "Your team. Your ideas. One place to build.": "आपकी टीम। आपके विचार। बनाने के लिए एक जगह।",
    "Your workspaces": "आपके कार्यस्थान",
    "Choose your workspace": "अपना कार्यस्थान चुनें",
    "Open workspace": "कार्यस्थान खोलें",
    "Create a workspace": "कार्यस्थान बनाएँ",
    "Invite teammates": "टीम के सदस्यों को आमंत्रित करें",
    "Workspace settings": "कार्यस्थान की सेटिंग",
    "Archived": "संग्रहीत",
    "Restore workspace": "कार्यस्थान वापस लाएँ",
    "Account": "खाता",
    "Your agent": "आपका एजेंट",
    "Agent name": "एजेंट का नाम",
    "Agent nickname": "एजेंट का उपनाम",
    "Powered by": "संचालित द्वारा",
    "Save agent": "एजेंट सहेजें",
    "People": "सदस्य",
    "People & access": "सदस्य और पहुँच",
    "Channels": "चैनल",
    "Invitations": "आमंत्रण",
    "Join a workspace": "कार्यस्थान से जुड़ें",
    "Invitation code": "आमंत्रण कोड",
    "Conversation": "बातचीत",
    "Project": "प्रोजेक्ट",
    "Work": "काम",
    "Files": "फ़ाइलें",
    "Buds": "Buds",
    "Connectors": "कनेक्टर",
    "Connect your account": "अपना खाता जोड़ें",
    "All connectors": "सभी कनेक्टर",
    "Refresh connectors": "कनेक्टर रीफ़्रेश करें",
    "Send": "भेजें",
    "Thinking…": "सोच रहा है…",
    "Copy message": "संदेश कॉपी करें",
    "Show original": "मूल पाठ दिखाएँ",
    "Show translation": "अनुवाद दिखाएँ",
    "Copy original": "मूल पाठ कॉपी करें",
    "Translated": "अनुवादित",
    "Original text": "मूल पाठ",
    "Translating…": "अनुवाद हो रहा है…",
    "New channel name": "नए चैनल का नाम",
    "Create channel": "चैनल बनाएँ",
    "Your profile": "आपकी प्रोफ़ाइल",
    "Save profile": "प्रोफ़ाइल सहेजें",
    "Short bio": "संक्षिप्त परिचय",
    "About you": "आपके बारे में",
    "Availability": "उपलब्धता",
    "Online": "ऑनलाइन",
    "Away": "दूर",
    "Do not disturb": "परेशान न करें",
    "Sign out": "साइन आउट करें",
    "Back": "वापस",
    "Finish later": "बाद में पूरा करें",
    "Save connection": "कनेक्शन सहेजें",
    "Start build": "बिल्ड शुरू करें",
    "Retry translations": "अनुवाद फिर से करें",
    "Search your workspace": "अपने कार्यस्थान में खोजें",
    "Invite teammates…": "टीम के सदस्यों को आमंत्रित करें…",
    "Workspace tools": "कार्यस्थान के उपकरण",
    "Team workspace": "टीम का कार्यस्थान",
    "Team channel": "टीम का चैनल",
    "Shared conversation": "साझा बातचीत",
    "Language preferences saved.": "भाषा की प्राथमिकताएँ सहेजी गईं।",
    "Original text remains unchanged. AI translations use your workspace allowance.": (
        "मूल पाठ नहीं बदलता। AI अनुवाद में कार्यस्थान का AI कोटा लगता है।"
    ),
}


class Localizer(QObject):
    changed = Signal()

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.language = normalize(window.settings.value("interfaceLanguage", "en"))
        self.enabled = True
        self.account_id = ""
        self.cache, self.queue = OrderedDict(), OrderedDict()
        self.originals = set()
        self.generation, self.pending, self.applying = 0, False, False
        self.failed = set()
        self.retries = {}
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.flush)
        self.scan_timer = QTimer(self)
        self.scan_timer.setSingleShot(True)
        self.scan_timer.timeout.connect(self.scan)
        QApplication.instance().installEventFilter(self)
        self.changed.connect(self.repaint_messages)
        self.scan_timer.start(0)

    def bind(self, account):
        account.snapshot_loaded.connect(self.restore_preference)
        account.session_closed.connect(self.clear)

    def restore_preference(self):
        account = getattr(self.window, "account_dialog", None)
        user = account.service.user if account and account.service else None
        if not user:
            return
        metadata = getattr(user, "user_metadata", None) or {}
        identifier = str(user.id)
        if self.account_id != identifier:
            self.clear()
        language = normalize(metadata.get("aedrova_language", "en"))
        enabled = metadata.get("aedrova_translate", True) is True
        changed_account = self.account_id != identifier
        self.account_id = identifier
        if changed_account or language != self.language or enabled != self.enabled:
            self.configure(language, enabled)

    def clear(self):
        self.generation += 1
        self.account_id = ""
        self.cache.clear()
        self.queue.clear()
        self.failed.clear()
        self.retries.clear()
        self.originals.clear()
        self.configure("en", True)

    def configure(self, language, enabled=True):
        self.language, self.enabled = normalize(language), enabled is True
        self.generation += 1
        self.queue.clear()
        self.failed.clear()
        self.retries.clear()
        self.originals.clear()
        self.window.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.language in RTL
            else Qt.LayoutDirection.LeftToRight
        )
        self.window.settings.setValue("interfaceLanguage", self.language)
        self.scan_timer.start(0)
        self.changed.emit()

    def text(self, source, *, interface=False):
        if not source or (not interface and not self.enabled):
            return source
        if interface and self.language == "en":
            return source
        if interface and self.language == "hi" and source in HINDI:
            return HINDI[source]
        if len(source) > 12000 or len(source.encode()) > 24000:
            from aedrova.localization import chunks

            return "".join(
                self.text(part, interface=interface) if prose else part
                for part, prose in chunks(source)
            )
        key = (
            self.account_id,
            getattr(self.window, "workspace_id", ""),
            self.language,
            "ui" if interface else "message",
            source,
        )
        value = self.cache.get(key)
        if value is not None:
            self.cache.move_to_end(key)
            return value
        if (
            key not in self.failed
            and len(source.encode()) <= 24000
            and any(c.isalpha() for c in source)
        ):
            self.queue[key] = source
            if len(self.queue) > 2000:
                self.queue.popitem(last=False)
            if not self.pending and not self.timer.isActive():
                self.timer.start(350)
        return source

    def translation_state(self, source):
        key = (
            self.account_id,
            getattr(self.window, "workspace_id", ""),
            self.language,
            "message",
            source,
        )
        if key in self.failed:
            return "original"
        if key in self.cache:
            return "ready"
        return "pending"

    def eventFilter(self, obj, event):  # noqa: N802
        if (
            not self.applying
            and isinstance(obj, QWidget)
            and event.type() in (QEvent.Type.Show, QEvent.Type.LayoutRequest)
        ):
            if self.window is obj or self.window.isAncestorOf(obj):
                if not self.scan_timer.isActive():
                    self.scan_timer.start(100)
        return False

    def scan(self):
        if not isValid(self.window):
            return
        self.applying = True
        try:
            widgets = self.window.findChildren(QWidget) + self.window.findChildren(QAction)
            for widget in widgets:
                if not isValid(widget):
                    continue
                if isinstance(widget, QWidget) and not widget.isVisible():
                    continue
                source = widget.property("aedrovaSourceText")
                if source is not None:
                    if widget.property("aedrovaTranslatingStream"):
                        continue
                    from aedrova.desktop.conversation import markdown_html

                    translated = self.text(source)
                    rendered = markdown_html(translated)
                    if widget.text() != rendered:
                        widget.setText(rendered)
                    continue
                if widget.objectName() in ("MessageTimestamp", "AgentCommandOutput"):
                    continue
                # Never translate text entered by the user, workspace names or model values.
                if isinstance(widget, (QLineEdit, QPlainTextEdit)):
                    self.apply_value(widget, "placeholderText", "setPlaceholderText")
                elif isinstance(widget, (QLabel, QAbstractButton, QAction)):
                    if isinstance(widget, QLabel) and (
                        "<" in widget.text() or widget.accessibleName().startswith("Agent sender:")
                    ):
                        continue
                    self.apply_value(widget, "text", "setText")
                if isinstance(widget, QComboBox):
                    source_name = widget.property("i18n_accessibleName")
                    name = (source_name[0] if source_name else widget.accessibleName()).lower()
                    if not any(
                        term in name
                        for term in (
                            "workspace",
                            "bud to connect",
                            "display language",
                            "channel access",
                        )
                    ):
                        previous = widget.property("i18n_items") or []
                        values = []
                        for i in range(widget.count()):
                            current = widget.itemText(i)
                            old = previous[i] if i < len(previous) else None
                            source = old[0] if old and current == old[1] else current
                            translated = self.text(source, interface=True)
                            values.append([source, translated])
                            if translated != current:
                                widget.setItemText(i, translated)
                        widget.setProperty("i18n_items", values)
                if hasattr(widget, "toolTip"):
                    self.apply_value(widget, "toolTip", "setToolTip")
                if isinstance(widget, QWidget) and widget.accessibleName():
                    self.apply_value(widget, "accessibleName", "setAccessibleName")
        finally:
            self.applying = False

    def apply_value(self, widget, getter, setter):
        current = getattr(widget, getter)()
        prop = "i18n_" + getter
        previous = widget.property(prop)
        source = previous[0] if previous and current == previous[1] else current
        if not source:
            return
        translated = self.text(source, interface=True)
        widget.setProperty(prop, [source, translated])
        if current != translated:
            getattr(widget, setter)(translated)

    def flush(self):
        account = getattr(self.window, "account_dialog", None)
        workspace = getattr(self.window, "workspace_id", "")
        if (
            self.pending
            or not self.queue
            or not workspace
            or not account
            or not account.service
            or not account.service.user
        ):
            return
        from aedrova.agents.managed import ManagedClient, application_origin

        origin = application_origin()
        if not origin:
            return
        batch, size = [], 0
        for key, value in self.queue.items():
            if key[2] != self.language or key[1] != workspace:
                continue
            if batch and (size + len(value.encode()) > 24000 or len(batch) >= 12):
                break
            batch.append((key, value))
            size += len(value.encode())
        if not batch:
            return
        for key, _ in batch:
            self.queue.pop(key, None)
        generation, account_id, language = self.generation, self.account_id, self.language
        service = account.service
        self.pending = True

        def operation():
            clone = None
            try:
                clone = service.fork_for_context()
                if generation != self.generation:
                    return {"error": True}
                session = clone.client.auth.get_session()
                client = ManagedClient(origin, session.access_token)
                return client.request(
                    "/api/translations",
                    {"workspace": workspace, "language": language, "texts": [v for _, v in batch]},
                    timeout=50,
                )
            except Exception as error:
                return {
                    "error": True,
                    "busy": any(
                        phrase in str(error)
                        for phrase in ("concurrent build limit", "two active builds")
                    ),
                }
            finally:
                if clone:
                    clone.close_context()

        def finished(result):
            if not isValid(self) or not isValid(self.window):
                return
            self.pending = False
            if (
                generation == self.generation
                and account_id == self.account_id
                and workspace == self.window.workspace_id
            ):
                values = result.get("texts")
                if (
                    isinstance(values, list)
                    and len(values) == len(batch)
                    and all(isinstance(v, str) for v in values)
                ):
                    for (key, _), value in zip(batch, values, strict=True):
                        self.cache[key] = value
                    while len(self.cache) > 1000:
                        self.cache.popitem(last=False)
                elif result.get("busy") and all(self.retries.get(key, 0) < 6 for key, _ in batch):
                    for key, value in batch:
                        self.retries[key] = self.retries.get(key, 0) + 1
                        self.queue[key] = value
                    self.timer.start(3000)
                    return
                else:
                    self.failed.update(key for key, _ in batch)
                    self.failed.update(self.queue)
                    self.queue.clear()
                    for view in (self.window.messages, self.window.thread_messages):
                        view.setToolTip("Translation unavailable. Showing original messages.")
                self.scan_timer.start(0)
                self.changed.emit()
            if self.queue:
                self.timer.start(350)

        from aedrova.desktop.account import AccountJob

        self.job = AccountJob(operation)
        self.job.signals.finished.connect(
            lambda result, ok: finished(result if ok else {"error": True})
        )
        QThreadPool.globalInstance().start(self.job)

    def repaint_messages(self):
        for view in (self.window.messages, self.window.thread_messages):
            view.show_messages(view.source_messages, force=True)


def show_language_settings(window):
    existing = getattr(window, "language_dialog", None)
    if existing and existing.isVisible():
        existing.raise_()
        return existing
    dialog = AppDialog(window)
    window.language_dialog = dialog
    dialog.setWindowTitle("Language & translation")
    dialog.resize(480, 300)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(28, 24, 28, 24)
    layout.setSpacing(16)
    layout.addWidget(label("Language & translation", "title"))
    layout.addWidget(label("Display language", "muted"))
    choice = ChoiceBox()
    choice.setAccessibleName("Display language")
    for code, name in LANGUAGES.items():
        choice.addItem(name, code)
    choice.setCurrentIndex(choice.findData(window.localizer.language))
    layout.addWidget(choice)
    automatic = QCheckBox("Translate conversations automatically")
    automatic.setChecked(window.localizer.enabled)
    layout.addWidget(automatic)
    layout.addWidget(
        label(
            "Original text remains unchanged. AI translations use your workspace allowance.",
            "muted",
            wrap=True,
        )
    )
    status = label("", "muted", wrap=True)
    layout.addWidget(status)
    retry = button("Retry translations")
    retry.setToolTip("Retry messages that could not be translated")
    retry.clicked.connect(
        lambda: window.localizer.configure(window.localizer.language, window.localizer.enabled)
    )
    layout.addWidget(retry)
    actions = QHBoxLayout()
    actions.addStretch()
    cancel = button("Cancel")
    cancel.clicked.connect(dialog.reject)
    actions.addWidget(cancel)
    save = button("Save", role="primary")
    actions.addWidget(save)
    layout.addLayout(actions)

    def apply():
        language, enabled = choice.currentData(), automatic.isChecked()
        account = getattr(window, "account_dialog", None)
        if not account or not account.service or not account.service.user:
            window.localizer.configure(language, enabled)
            dialog.accept()
            return
        save.setEnabled(False)
        user_id = str(account.service.user.id)

        def saved(result):
            if (
                not isValid(window)
                or not account.service
                or not account.service.user
                or str(account.service.user.id) != user_id
            ):
                return
            if result.get("error"):
                status.setText("Could not save your language preference. Please retry.")
                save.setEnabled(True)
                return
            window.localizer.configure(language, enabled)
            dialog.accept()

        service = account.service

        def operation():
            try:
                service.save_language_preference(language, enabled)
                return {"ok": True}
            except Exception:
                return {"error": True}

        account.run(operation, saved)

    save.clicked.connect(apply)
    dialog.open()
    return dialog
