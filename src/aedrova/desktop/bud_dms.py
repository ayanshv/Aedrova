"""Account-scoped shortcuts to private Bud histories, never shared channel rows."""

import json
from hashlib import sha256

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidgetItem


def settings_key(window):
    user = window.current_user()
    if not user or not window.connected or not window.connected.active:
        return None
    scope = str(user.id) + ":" + window.workspace_id
    return "budDirectMessages/" + sha256(scope.encode()).hexdigest()


def saved_ids(window):
    key = settings_key(window)
    if key is None:
        return []
    try:
        value = json.loads(window.settings.value(key, "[]"))
    except (ValueError, TypeError):
        return []
    return [v for v in value if isinstance(v, str)][:100] if isinstance(value, list) else []


def remember(window, bud_id):
    key = settings_key(window)
    if key:
        ids = saved_ids(window)
        window.settings.setValue(key, json.dumps([bud_id, *[v for v in ids if v != bud_id]][:100]))
        window.settings.sync()
        populate(window)


def populate(window):
    listing = window.dm_list
    blocked = listing.blockSignals(True)
    try:
        for index in range(listing.count() - 1, -1, -1):
            if listing.item(index).data(Qt.ItemDataRole.UserRole + 1) == "bud":
                listing.takeItem(index)
        account = getattr(window, "account_dialog", None)
        rows = getattr(account, "snapshot", {}).get("dots", []) if account else []
        allowed = {r["id"]: r for r in rows if r["workspace_id"] == window.workspace_id}
        if settings_key(window):
            from aedrova.desktop.bud_art import appearance, sprite

            for bud_id in saved_ids(window):
                bud = allowed.get(bud_id)
                if bud is None:
                    continue
                item = QListWidgetItem(bud["name"])
                item.setData(Qt.ItemDataRole.UserRole, bud_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, "bud")
                item.setToolTip("Private conversation with " + bud["name"])
                item.setIcon(QIcon(sprite(appearance(bud), str(bud.get("color", "")))))
                listing.addItem(item)
        listing.setMaximumHeight(max(38, min(160, listing.count() * 41)))
        listing.setVisible(listing.count() > 0)
    finally:
        listing.blockSignals(blocked)


def open_item(window, item):
    if item and item.data(Qt.ItemDataRole.UserRole + 1) == "bud":
        from aedrova.desktop.bud_chat import open_bud_chat

        open_bud_chat(window, item.data(Qt.ItemDataRole.UserRole))
