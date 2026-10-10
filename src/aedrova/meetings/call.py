"""RTC runs on a dedicated asyncio thread; Qt owns explicit camera/screen capture."""

import asyncio
import threading
import time

from livekit import rtc
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

from aedrova.meetings.access import MeetingRequestError


class CallWorker(QObject):
    state = Signal(str)
    roster = Signal(object)
    speaker = Signal(str)
    problem = Signal(str)
    media = Signal(str, bool)
    ended = Signal()
    consent_snapshot = Signal(object)
    text_capability = Signal(bool)
    speech_capability = Signal(bool)
    transcription_state = Signal(str)

    def __init__(self, client, *, workspace, channel, user, parent=None):
        super().__init__(parent)
        self.client, self.workspace, self.channel, self.user = client, workspace, channel, user
        self.thread = None
        self.loop = None
        self.stop_requested = threading.Event()
        self.frames = {}
        self.frames_lock = threading.Lock()
        self.room = None
        self.audio = None
        self.microphone = None
        self.mic_publication = None
        self.video = {}
        self.streams = {}
        self.tasks = set()
        self.listeners = []
        self.meeting = None
        self.lock = None
        self.connected = False
        self.run_task = None
        self.cleaning = False
        self._speech_state = None
        self.speech_available = False
        self.speech_requested = False
        self.speech_task = None
        self.local_audio_track = None
        self.snapshot = None
        self.snapshot_at = 0
        self.call_started = time.monotonic()

    def start(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self._thread, name="Aedrova-call", daemon=True)
        self.thread.start()

    def _thread(self):
        asyncio.run(self._run())

    async def _run(self):
        self.loop = asyncio.get_running_loop()
        self.run_task = asyncio.current_task()
        self.lock = asyncio.Lock()
        phase = "channel access"
        failure = None
        try:
            self.state.emit("Connecting…")
            self.meeting = await asyncio.to_thread(self.client.start, self.channel)
            phase = "meeting authorization"
            access = await asyncio.to_thread(
                self.client.join,
                self.meeting,
                workspace=self.workspace,
                channel=self.channel,
                user=self.user,
            )
            if self.stop_requested.is_set():
                return
            if hasattr(self.client, "capabilities"):
                capabilities = await asyncio.to_thread(self.client.capabilities)
                self.text_capability.emit(capabilities.get("meeting_text") is True)
                self.speech_available = capabilities.get("audio_transcription") is True
                self.speech_capability.emit(self.speech_available)
            phase = "native media initialization"
            self.room = rtc.Room()
            self._events()
            # ADM provides speaker playout and AEC. No microphone source is created here.
            self.audio = rtc.PlatformAudio()
            phase = "LiveKit connection"
            await asyncio.wait_for(
                self.room.connect(access.url, access.token, rtc.RoomOptions(connect_timeout=15)),
                timeout=20,
            )
            self.connected = True
            self.state.emit("Connected · devices are off")
            self._roster()
            phase = "access heartbeat"
            last_pulse = 0
            while not self.stop_requested.is_set():
                if time.monotonic() - last_pulse >= 8:
                    snapshot = await asyncio.wait_for(
                        asyncio.to_thread(self.client.pulse, self.meeting), 20
                    )
                    self.update_consent(snapshot)
                    last_pulse = time.monotonic()
                self._send_frames()
                await asyncio.sleep(0.03)
        except Exception as error:
            if isinstance(error, MeetingRequestError):
                failure = str(error)
            else:
                failure = f"Could not connect during {phase}. Close the call and try again."
            self.problem.emit(failure)
        finally:
            self.cleaning = True
            self.connected = False
            self.state.emit("Leaving…")
            await self._cleanup()
            self.state.emit(failure or "Call ended · devices are off")
            self.ended.emit()

    def update_consent(self, snapshot):
        self.snapshot, self.snapshot_at = snapshot, time.monotonic()
        self.consent_snapshot.emit(snapshot)

    def speech_permit(self):
        from aedrova.meetings.consent import capture_permit

        if (
            not self.connected
            or not self.speech_requested
            or not self.speech_available
            or not self.microphone
            or time.monotonic() - self.snapshot_at > 10
        ):
            return None
        people = {self.user} | set(self.room.remote_participants)
        return capture_permit(self.snapshot or {}, people)

    def emit_speech_state(self, state):
        if state != self._speech_state:
            self._speech_state = state
            self.transcription_state.emit(state)

    def pause_speech(self):
        self.speech_requested = False
        if self.speech_task:
            self.speech_task.cancel()
            self.speech_task = None
        self.emit_speech_state("Transcription off · review saved text separately")

    def start_speech(self):
        if self.speech_task or not self.speech_permit() or not self.local_audio_track:
            return
        self.speech_task = asyncio.create_task(self._transcribe_microphone())
        self.tasks.add(self.speech_task)
        self.speech_task.add_done_callback(self.tasks.discard)

    async def _transcribe_microphone(self):
        from aedrova.meetings.consent import same_capture
        from aedrova.meetings.speech import MicrophoneBuffer

        buffer = MicrophoneBuffer()
        stream = None
        try:
            stream = rtc.AudioStream(
                self.local_audio_track, capacity=1, sample_rate=16000, num_channels=1
            )
            async for event in stream:
                permit = self.speech_permit()
                self.emit_speech_state(
                    "Transcribing your microphone · review required"
                    if permit
                    else "Transcription paused · waiting for current consent"
                )
                chunk = buffer.feed(
                    bytes(event.frame.data),
                    permit,
                    min(86400000, int((time.monotonic() - self.call_started) * 1000)),
                )
                if chunk is None:
                    continue
                # Skip capture while awaiting the server; bounded capacity discards old frames.
                # Never queue a stale recording or automatically retry a failed provider call.
                if same_capture(chunk.permit, self.speech_permit()):
                    self.emit_speech_state("Processing your speech · capture paused")
                    await asyncio.to_thread(self.client.transcribe, self.meeting, chunk)
                buffer.reset()
                if not self.speech_permit():
                    self.emit_speech_state("Transcription paused · consent changed")
        except asyncio.CancelledError:
            raise
        except Exception:
            self.speech_requested = False
            self.emit_speech_state(
                "Transcription stopped · check consent or service; start again when ready"
            )
        finally:
            buffer.reset()
            if stream:
                await stream.aclose()
            if self.speech_task is asyncio.current_task():
                self.speech_task = None

    def _events(self):
        def listen(event, callback):
            self.room.on(event, callback)
            self.listeners.append((event, callback))

        listen("participant_connected", lambda *_: self._roster())
        listen("participant_disconnected", lambda *_: self._roster())
        listen("track_muted", lambda *_: self._roster())
        listen("track_unmuted", lambda *_: self._roster())
        listen("track_published", lambda *_: self._roster())
        listen("track_unpublished", lambda *_: self._roster())
        listen(
            "active_speakers_changed",
            lambda people: self.speaker.emit(people[0].identity) if people else None,
        )
        listen("reconnecting", self._reconnecting)
        listen("reconnected", self._reconnected)
        listen("disconnected", lambda *_: self.stop())
        listen("track_subscribed", self._subscribed)
        listen("track_unsubscribed", self._unsubscribed)

    def _roster(self):
        people = [{"id": self.user, "name": "You", "microphone_on": self.microphone is not None}]
        if self.room:
            people += [
                {
                    "id": p.identity,
                    "name": p.name or "Teammate",
                    "microphone_on": any(
                        pub.source == rtc.TrackSource.SOURCE_MICROPHONE and not pub.muted
                        for pub in p.track_publications.values()
                    ),
                }
                for p in self.room.remote_participants.values()
            ]
        self.roster.emit(people)

    def _reconnecting(self, *_):
        self.connected = False
        self.pause_speech()
        if self.microphone:
            self.microphone.close()
            self.microphone = None
        with self.frames_lock:
            self.frames.clear()
        for kind in ("microphone", "camera", "screen"):
            self.media.emit(kind, False)
        self.state.emit("Reconnecting… devices paused")

    def _reconnected(self, *_):
        self.connected = True
        self.state.emit("Reconnected · enable your devices when ready")
        self._roster()

    def _subscribed(self, track, publication, participant):
        if self.cleaning or self.stop_requested.is_set():
            return
        if track.kind != rtc.TrackKind.KIND_VIDEO:
            return  # ADM handles remote audio playback, without an audio recorder.
        if len(self.streams) >= 32:
            return
        key = participant.identity + (
            "/screen" if publication.source == rtc.TrackSource.SOURCE_SCREENSHARE else "/camera"
        )
        stream = rtc.VideoStream(track, capacity=1, format=rtc.VideoBufferType.RGBA)
        task = asyncio.create_task(self._receive(key, stream))
        self.streams[publication.sid] = (key, stream, task)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    def _unsubscribed(self, track, publication, participant):
        item = self.streams.pop(publication.sid, None)
        if item:
            key, stream, task = item
            task.cancel()
            with self.frames_lock:
                self.frames.pop(key, None)
            self.media.emit(key, False)

    async def _receive(self, key, stream):
        try:
            async for event in stream:
                frame = event.frame
                image = QImage(
                    bytes(frame.data),
                    frame.width,
                    frame.height,
                    frame.width * 4,
                    QImage.Format.Format_RGBA8888,
                ).copy()
                # A bounded latest-frame mailbox avoids flooding the Qt event queue.
                with self.frames_lock:
                    self.frames[key] = image
        except asyncio.CancelledError:
            raise
        except Exception:
            self.problem.emit("A video stream stopped. Audio may still be available.")
        finally:
            await stream.aclose()

    def take_remote_frames(self):
        with self.frames_lock:
            result = {key: image for key, image in self.frames.items() if "/" in key}
            for key in result:
                self.frames.pop(key, None)
        return result

    def frame(self, kind, image):
        if self.connected and not self.stop_requested.is_set():
            with self.frames_lock:
                self.frames[kind] = image

    def clear_frame(self, kind):
        with self.frames_lock:
            self.frames.pop(kind, None)

    def _send_frames(self):
        for kind, (source, _) in tuple(self.video.items()):
            with self.frames_lock:
                image = self.frames.pop(kind, None)
            if image is not None and self.connected:
                source.capture_frame(
                    rtc.VideoFrame(
                        image.width(),
                        image.height(),
                        rtc.VideoBufferType.RGBA,
                        bytes(image.constBits()),
                    )
                )

    def command(self, kind, enabled):
        if (
            self.loop
            and not self.loop.is_closed()
            and not self.cleaning
            and not self.stop_requested.is_set()
        ):
            try:
                self.loop.call_soon_threadsafe(self._schedule, kind, enabled)
            except RuntimeError:
                pass  # The worker loop finished between the GUI check and dispatch.

    def _schedule(self, kind, enabled):
        if kind in {"consent", "withdraw_text", "end"} or (kind == "microphone" and not enabled):
            self.pause_speech()
        if self.cleaning or self.stop_requested.is_set():
            return
        task = asyncio.create_task(self._media(kind, enabled))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _media(self, kind, enabled):
        async with self.lock:
            if self.cleaning or self.stop_requested.is_set():
                return
            try:
                if kind == "transcription":
                    if not enabled:
                        self.pause_speech()
                        return
                    self.speech_requested = True
                    if not self.speech_permit():
                        self.pause_speech()
                        raise PermissionError("Current unanimous consent and microphone required")
                    self.start_speech()
                    return
                if kind == "consent":
                    self.pause_speech()
                    snapshot = await asyncio.to_thread(
                        self.client.consent,
                        self.meeting,
                        enabled["transcription"],
                        enabled["ai_context"],
                    )
                    self.update_consent(snapshot)
                    return
                if kind == "withdraw_text":
                    self.pause_speech()
                    await asyncio.to_thread(
                        self.client.withdraw_text, self.meeting, enabled["delete"]
                    )
                    snapshot = await asyncio.to_thread(self.client.pulse, self.meeting)
                    self.update_consent(snapshot)
                    return
                if kind == "end":
                    await asyncio.to_thread(self.client.end, self.meeting)
                    self.stop()
                    return
                if enabled and not self.connected:
                    raise RuntimeError("Not connected")
                if kind == "microphone":
                    self.pause_speech()
                    self.local_audio_track = None
                    if self.microphone:
                        self.microphone.close()
                        self.microphone = None
                    if self.mic_publication:
                        await self.room.local_participant.unpublish_track(self.mic_publication.sid)
                        self.mic_publication = None
                    if enabled:
                        self.microphone = self.audio.create_audio_source(
                            rtc.PlatformAudioOptions(
                                echo_cancellation=True,
                                noise_suppression=True,
                                auto_gain_control=True,
                            )
                        )
                        track = rtc.LocalAudioTrack.create_audio_track(
                            "Microphone", self.microphone
                        )
                        self.local_audio_track = track
                        self.mic_publication = await self.room.local_participant.publish_track(
                            track, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
                        )
                elif kind in {"camera", "screen"}:
                    if kind in self.video:
                        source, publication = self.video.pop(kind)
                        await self.room.local_participant.unpublish_track(publication.sid)
                        await source.aclose()
                    if enabled:
                        source = rtc.VideoSource(640, 360)
                        track = rtc.LocalVideoTrack.create_video_track(kind, source)
                        try:
                            publication = await self.room.local_participant.publish_track(
                                track,
                                rtc.TrackPublishOptions(
                                    source=(
                                        rtc.TrackSource.SOURCE_CAMERA
                                        if kind == "camera"
                                        else rtc.TrackSource.SOURCE_SCREENSHARE
                                    )
                                ),
                            )
                        except BaseException:
                            await source.aclose()
                            raise
                        self.video[kind] = source, publication
                self.media.emit(kind, enabled)
                self._roster()
            except Exception:
                if kind == "microphone" and self.microphone:
                    self.microphone.close()
                    self.microphone = None
                self.media.emit(kind, False)
                self.problem.emit(
                    "Could not change this call control. Check your access, "
                    "connection and device permissions."
                )

    def stop(self):
        self.stop_requested.set()
        self.connected = False
        with self.frames_lock:
            self.frames.clear()
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self._cancel_run)

    def _cancel_run(self):
        self.pause_speech()
        if self.microphone:
            self.microphone.close()
            self.microphone = None
        if self.run_task and not self.cleaning and not self.run_task.done():
            self.run_task.cancel()

    async def _cleanup(self):
        tasks = list(self.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if self.microphone:
            self.microphone.close()
            self.microphone = None
        if self.room:
            try:
                await asyncio.wait_for(self.room.disconnect(), 5)
            except Exception:
                pass
        for source, _ in self.video.values():
            await source.aclose()
        self.video.clear()
        self.streams.clear()
        self.tasks.clear()
        self.mic_publication = None
        if self.room:
            for event, callback in self.listeners:
                self.room.off(event, callback)
        self.listeners.clear()
        self.room = None
        if self.audio:
            self.audio.close()
            self.audio = None
        if self.meeting:
            try:
                await asyncio.wait_for(asyncio.to_thread(self.client.leave, self.meeting), 5)
            except Exception:
                pass  # Durable server lease still expires without heartbeat.
