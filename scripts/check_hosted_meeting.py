"""Owner-approved two-account check through hosted Supabase and the meeting API.

Two normal Google sign-ins; credentials stay in memory. Creates a named test
workspace, invites account B, then removes only B from that workspace. Generated
video only: no hardware, transcription, AI, service-role or LiveKit admin key.
"""

import asyncio
import gc
import json
import logging
import time
import traceback
from pathlib import Path
from threading import Event, Lock
from uuid import uuid4

from livekit import rtc
from PySide6.QtGui import QColor, QImage

from aedrova.identity.oauth import google_sign_in
from aedrova.identity.service import Connection, IdentityService
from aedrova.meetings.access import MeetingClient
from aedrova.meetings.call import CallWorker

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'work/hosted-meeting-check.json'


def denied(action):
    try:
        action()
    except RuntimeError:
        return
    raise AssertionError('Unauthorized operation was accepted')


class CheckClient(MeetingClient):
    cached = None

    def __init__(self, *args):
        super().__init__(*args)
        self.suspend_pulse = False
        self.pulse_lock = Lock()
        self.inflight_pulse = Event()

    def pause_pulses(self):
        with self.pulse_lock:
            self.suspend_pulse = True

    def join(self, meeting, **scope):
        self.cached = super().join(meeting, **scope)
        return self.cached

    def pulse(self, meeting):
        with self.pulse_lock:
            if self.suspend_pulse:
                return None
            self.inflight_pulse.set()
        try:
            return super().pulse(meeting)
        finally:
            self.inflight_pulse.clear()


async def until(predicate, timeout=30):
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(.05)


async def probe(accounts, origin):
    owner, member = accounts
    ids = [str(account.user.id) for account in accounts]
    if ids[0] == ids[1]:
        raise RuntimeError('Choose two different accounts')
    clients = [CheckClient(origin, account.client.auth.get_session().access_token)
               for account in accounts]
    workspace = owner.rpc('create_workspace', {'p_name': 'Meeting validation ' + uuid4().hex[:6]})
    channels = owner.client.table('channels').select('id').eq('workspace_id', workspace).execute()
    channel = channels.data[0]['id']
    private = owner.rpc('create_channel', {'p_workspace': workspace,
                                          'p_name': 'private-check', 'p_private': True})
    meeting = clients[0].start(channel)
    workers, runs = [], []
    invite_accepted = False
    original_audio = rtc.PlatformAudio
    retry = None
    report = {'workspace': workspace, 'media': 'generated video only',
              'physical_audio_echo_network_reconnect': 'not tested',
              'transcription': 'not started'}

    class NoHardwareAudio:
        def close(self):
            pass

    async def connect(index):
        worker = CallWorker(clients[index], workspace=workspace, channel=channel, user=ids[index])
        worker.state.connect(lambda state: print(state, flush=True)
                             if state.startswith('Call failed') else None)
        workers.append(worker)
        task = asyncio.create_task(worker._run())
        runs.append(task)
        await until(lambda: worker.connected or task.done())
        if not worker.connected:
            raise RuntimeError('Native worker failed to connect')
        worker.disconnect_reasons = []
        def callback(reason):
            worker.disconnect_reasons.append(rtc.DisconnectReason.Name(reason))
        worker.room.on('disconnected', callback)
        worker.listeners.append(('disconnected', callback))
        return worker

    try:
        print('Checking nonmember channel isolation.', flush=True)
        denied(lambda: clients[1].start(channel))
        denied(lambda: clients[1].join(meeting, workspace=workspace, channel=channel, user=ids[1]))
        report['nonmember_scope'] = 'denied'
        print('Checking invitation acceptance.', flush=True)
        invitation = owner.rpc('create_invitation', {'p_workspace': workspace,
                               'p_email': member.user.email, 'p_role': 'member'})
        assert member.rpc('accept_invitation', {'p_token': invitation}) == workspace
        invite_accepted = True
        print('Checking private-channel isolation.', flush=True)
        denied(lambda: clients[1].start(private))
        report['private_channel_scope'] = 'denied'
        rtc.PlatformAudio = NoHardwareAudio
        print('Connecting two native workers.', flush=True)
        first = await connect(0)
        second = await connect(1)
        await until(lambda: len(first.room.remote_participants) == 1 and
                    len(second.room.remote_participants) == 1)
        report['two_authenticated_participants'] = 'passed'
        for worker in (first, second):
            await worker._media('camera', True)
            await worker._media('screen', True)
        counts = [{'camera': 0, 'screen': 0} for _ in accounts]
        image = QImage(640, 360, QImage.Format.Format_RGBA8888)
        image.fill(QColor(80, 120, 160))
        startup_frames = 0
        deadline = time.monotonic() + 18
        while time.monotonic() < deadline:
            for index, worker in enumerate((first, second)):
                worker.frame('camera', image)
                worker.frame('screen', image)
                for key, frame in worker.take_remote_frames().items():
                    assert not frame.isNull()
                    pixel = frame.pixelColor(frame.width() // 2, frame.height() // 2)
                    if abs(pixel.blue() - 160) >= 35 or pixel.alpha() != 255:
                        startup_frames += 1
                        continue
                    counts[index]['screen' if key.endswith('/screen') else 'camera'] += 1
                assert worker.connected
            await asyncio.sleep(.03)
        assert all(count >= 5 for peer in counts for count in peer.values())
        report['bidirectional_camera_screen_frames'] = counts
        report['unmatched_startup_frames_excluded'] = startup_frames
        report['repeated_authorized_heartbeats'] = 'passed'
        print('Bidirectional generated camera/screen frames and heartbeats passed.', flush=True)
        second.stop()
        await asyncio.gather(runs[-1], return_exceptions=True)
        await until(lambda: not first.room.remote_participants)
        report['leave_updates_peer_roster'] = 'passed'
        # Cloud revocation cutoff must elapse before a genuinely new join token.
        # Guard sweep is every 3s; lease reuse also waits out its 2s cutoff grace.
        await asyncio.sleep(8)
        print('Checking leave and authorized rejoin.', flush=True)
        second = await connect(1)
        await until(lambda: len(first.room.remote_participants) == 1)
        report['leave_and_new_authorized_join'] = 'passed'
        cached = clients[1].cached
        clients[1].pause_pulses()
        await until(lambda: not clients[1].inflight_pulse.is_set())
        start = time.monotonic()
        print('Checking server-side membership revocation.', flush=True)
        owner.rpc('remove_member', {'p_workspace': workspace, 'p_user': ids[1]})
        invite_accepted = False
        await until(lambda: second.stop_requested.is_set() and
                    not first.room.remote_participants, timeout=45)
        assert 'PARTICIPANT_REMOVED' in second.disconnect_reasons
        report['server_revocation_with_client_heartbeat_paused'] = 'passed'
        report['removed_peer_disconnect_reason'] = 'PARTICIPANT_REMOVED'
        report['revocation_seconds'] = round(time.monotonic() - start, 2)
        print('Server revocation disconnected the removed member.', flush=True)
        await asyncio.gather(runs[-1], return_exceptions=True)
        denied(lambda: clients[1].join(meeting, workspace=workspace, channel=channel, user=ids[1]))
        report['removed_member_new_token'] = 'denied'
        retry = rtc.Room()
        rejected = False
        try:
            await asyncio.wait_for(retry.connect(cached.url, cached.token,
                                  rtc.RoomOptions(connect_timeout=5)), timeout=8)
        except Exception:
            rejected = True
        assert rejected
        report['removed_member_cached_token'] = 'denied'
        print('Removed member cannot obtain new access or reuse their cached token.', flush=True)
        await asyncio.to_thread(clients[0].end, meeting)
        await until(lambda: runs[0].done() and not first.connected)
        report['host_end_disconnects_remaining_peer'] = 'passed'
        report['status'] = 'passed'
        return report
    finally:
        REPORT.write_text(json.dumps(report, indent=2))
        for worker in workers:
            worker.stop()
        await asyncio.gather(*runs, return_exceptions=True)
        if retry:
            await retry.disconnect()
        rtc.PlatformAudio = original_audio
        try:
            clients[0].end(meeting)
        except RuntimeError:
            pass
        if invite_accepted:
            owner.rpc('remove_member', {'p_workspace': workspace, 'p_user': ids[1]})
        workers.clear()
        gc.collect()


if __name__ == '__main__':
    logging.getLogger('livekit').setLevel(logging.CRITICAL)
    REPORT.unlink(missing_ok=True)
    accounts = []
    stage = 'public configuration'
    try:
        config = json.loads((ROOT / 'dist/Aedrova.app/Contents/Resources/aedrova/desktop/assets/'
                             'public-config.json').read_text())
        connection = Connection(config['supabase_url'], config['supabase_publishable_key'])
        for title in ('owner account', 'school account'):
            stage = 'Google sign-in: ' + title
            print('Sign in with ' + title + ' in the opened browser.', flush=True)
            account = IdentityService(connection)
            accounts.append(account)
            google_sign_in(account, timeout=300)
            print('Account authenticated. Credentials remain in memory.', flush=True)
        stage = 'hosted call and access validation'
        result = asyncio.run(probe(accounts, config['managed_origin']))
        REPORT.write_text(json.dumps(result, indent=2))
        print('PASS hosted two-account calls, scoped access, leave/rejoin, and server revocation.',
              flush=True)
    except Exception as error:
        frames = traceback.extract_tb(error.__traceback__)
        own = [f for f in frames if f.filename == __file__]
        location = str(own[-1].lineno) if own else 'unknown'
        print('FAIL at ' + stage + ' (' + type(error).__name__ + ', check line ' + location
              + '). No credentials logged.',
              flush=True)
        raise SystemExit(1) from None
    finally:
        for account in accounts:
            if account._transport:
                account._transport.close()
