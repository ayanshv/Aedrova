"""Private, content-free realtime wakeups on a dedicated asyncio thread."""

import asyncio
from threading import Event, Lock, Thread

from PySide6.QtCore import QObject, Signal
from realtime import AsyncRealtimeClient


class RealtimeWakeups(QObject):
    changed = Signal()

    def __init__(self, parent=None, *, factory=AsyncRealtimeClient):
        super().__init__(parent)
        self.factory = factory
        self.stop_event = Event()
        self.lock = Lock()
        self.credentials = None
        self.thread = None

    def configure(self, credentials):
        with self.lock:
            self.credentials = credentials
        if self.thread is None or not self.thread.is_alive():
            self.thread = Thread(target=lambda: asyncio.run(self.listen()), daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        with self.lock:
            self.credentials = None

    async def listen(self):
        delay = 1
        while not self.stop_event.is_set():
            with self.lock:
                credentials = self.credentials
            if not credentials:
                return
            url, key, token, user = credentials
            client = self.factory(url + "/realtime/v1", token=key, auto_reconnect=True)
            try:
                await client.connect()
                await client.set_auth(token)
                channel = client.channel("user:" + user, {"config": {"private": True}})
                channel.on_broadcast("refresh", lambda _: self.changed.emit())
                await channel.subscribe(lambda status, error: self.changed.emit())
                delay = 1
                while not self.stop_event.is_set():
                    await asyncio.sleep(0.25)
                    with self.lock:
                        latest = self.credentials
                    if latest is None or latest[:2] != credentials[:2] or latest[3] != user:
                        break
                    if latest[2] != token:
                        token = latest[2]
                        await client.set_auth(token)
            except Exception:
                # No tokens, URLs, or provider payloads in logs; polling covers outages.
                pass
            finally:
                try:
                    await client.close()
                except Exception:
                    pass
            for _ in range(delay * 4):
                if self.stop_event.is_set():
                    return
                await asyncio.sleep(0.25)
            delay = min(delay * 2, 30)
