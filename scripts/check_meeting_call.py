"""Real RTC + native call-worker video + Cloud revocation, using synthetic identities/media.

No hardware, hosted Supabase accounts, recording, transcription or AI requests.
Run with --env-file .env.meetings and --with sqlalchemy in the desktop repository.
"""

import asyncio
import gc
import json
import logging
import os
import sys
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet
from livekit import api, rtc
from PySide6.QtGui import QColor, QImage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'Aedrova_site'))
from aedrova_site.config import Config  # noqa: E402
from aedrova_site.meeting_leases import MeetingLeases  # noqa: E402
from aedrova_site.meetings import issue_meeting_access  # noqa: E402
from aedrova_site.store import Denied, Store  # noqa: E402

from aedrova.meetings.access import MeetingAccess  # noqa: E402
from aedrova.meetings.call import CallWorker  # noqa: E402


async def probe():
    config = Config(meetings_enabled=True,
        livekit_url=os.environ['AEDROVA_LIVEKIT_URL'],
        livekit_api_key=os.environ['AEDROVA_LIVEKIT_API_KEY'],
        livekit_api_secret=os.environ['AEDROVA_LIVEKIT_API_SECRET'],
        encryption_key=Fernet.generate_key().decode())
    config.validate()
    meeting, workspace, channel = (str(uuid4()) for _ in range(3))
    users = [str(uuid4()), str(uuid4())]
    name = f'aedrova-{workspace}-{channel}-{meeting}'
    store = Store('sqlite:///work/meeting-call-check.sqlite3', config.encryption_key)
    leases = MeetingLeases(store)
    service = api.LiveKitAPI(config.livekit_url, config.livekit_api_key, config.livekit_api_secret)
    denied = set()
    workers, runs = [], []
    retry = None
    created = False
    original_audio = rtc.PlatformAudio

    class NoHardwareAudio:
        def close(self):
            pass

    class Identity:
        def user(self, token):
            return {'id': token}

        def request(self, path, token, *, method, data):
            if token in denied:
                raise Denied('Synthetic membership revoked')
            if path.endswith('/join_meeting'):
                return {'meeting_id': meeting, 'workspace_id': workspace,
                        'channel_id': channel, 'user_id': token, 'room_name': name}
            return {'ended': False, 'participants': [{'user_id': user} for user in users]}

    identity = Identity()

    class Client:
        access = None

        def __init__(self, user):
            self.user = user

        def start(self, _):
            return meeting

        def join(self, m, **scope):
            result = issue_meeting_access(config, identity, store, self.user, m, leases)
            self.access = MeetingAccess.parse(result, **scope)
            return self.access

        def pulse(self, m):
            if self.user in denied:
                raise Denied('Synthetic membership revoked')
            leases.pulse(m, self.user, self.user)

        def leave(self, m):
            leases.revoke(m, self.user)

    async def until(predicate, seconds=20):
        async with asyncio.timeout(seconds):
            while not predicate():
                await asyncio.sleep(.05)

    try:
        await service.room.create_room(api.CreateRoomRequest(name=name, empty_timeout=60,
                                                             max_participants=2))
        created = True
        await leases.sweep(identity, service)
        rtc.PlatformAudio = NoHardwareAudio
        for user in users:
            worker = CallWorker(Client(user), workspace=workspace, channel=channel, user=user)
            workers.append(worker)
            runs.append(asyncio.create_task(worker._run()))
        await until(lambda: all(worker.connected for worker in workers))
        for worker in workers:
            await worker._media('camera', True)
            await worker._media('screen', True)
        counts = [{'/camera': 0, '/screen': 0} for _ in users]
        frame = QImage(640, 360, QImage.Format.Format_RGBA8888)
        frame.fill(QColor(80, 120, 160))
        for _ in range(150):
            for index, worker in enumerate(workers):
                worker.frame('camera', frame)
                worker.frame('screen', frame)
                for key, received in worker.take_remote_frames().items():
                    assert not received.isNull()
                    pixel = received.pixelColor(0, 0)
                    assert abs(pixel.blue() - 160) < 35 and pixel.alpha() == 255
                    counts[index]['/screen' if key.endswith('/screen') else '/camera'] += 1
            await asyncio.sleep(.03)
        assert all(count >= 5 for result in counts for count in result.values())
        denied.add(users[0])
        await leases.sweep(identity, service)
        await until(lambda: workers[0].stop_requested.is_set())
        cached = workers[0].client.access
        retry = rtc.Room()
        rejected = False
        try:
            await asyncio.wait_for(retry.connect(cached.url, cached.token,
                rtc.RoomOptions(connect_timeout=5)), 8)
        except Exception:
            rejected = True
        assert rejected, 'Revoked cached token was accepted'
        return {'native_worker_two_way_video': counts, 'forced_disconnect': 'passed',
                'cached_token_rejection': 'passed', 'hardware': 'not tested',
                'hosted_supabase_rls': 'not tested; synthetic identities',
                'echo_network_reconnect': 'not tested', 'transcription': 'not started'}
    finally:
        for worker in workers:
            worker.stop()
        await asyncio.gather(*runs, return_exceptions=True)
        if retry:
            await retry.disconnect()
        retry = None
        workers.clear()
        runs.clear()
        gc.collect()
        rtc.PlatformAudio = original_audio
        if created:
            await service.room.delete_room(api.DeleteRoomRequest(room=name))
        await service.aclose()
        store.engine.dispose()


if __name__ == '__main__':
    logging.getLogger('livekit').setLevel(logging.CRITICAL)
    target = ROOT / 'work/meeting-call-check.json'
    target.unlink(missing_ok=True)
    try:
        result = asyncio.run(probe())
        target.write_text(json.dumps(result, indent=2))
        print('PASS native worker synthetic video, forced removal and cached-token rejection')
    except Exception:
        print('FAIL native call check. Inspect configuration/connectivity; no hardware was used.')
        raise SystemExit(1) from None
