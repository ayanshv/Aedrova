"""Two real RTC peers with synthetic media. No camera, microphone, screen or AI calls.

Owner supplies AEDROVA_LIVEKIT_URL/API_KEY/API_SECRET via ignored .env.meetings.
Run: uv run --env-file .env.meetings --extra spikes python scripts/check_meeting_transport.py
This proves transport only, not devices, echo handling, TURN or reconnect acceptance.
"""

import argparse
import asyncio
import json
import logging
import math
import os
import uuid
from array import array
from datetime import timedelta
from importlib.metadata import version
from pathlib import Path

from livekit import api, rtc
from PySide6.QtGui import QImage

from aedrova.meetings.access import transport_failure


async def probe(*, relay=False):
    url = os.getenv('AEDROVA_LIVEKIT_URL', '')
    key = os.getenv('AEDROVA_LIVEKIT_API_KEY', '')
    secret = os.getenv('AEDROVA_LIVEKIT_API_SECRET', '')
    if not url.startswith('wss://') or not key or len(secret) < 32:
        raise RuntimeError('Configure .env.meetings with the LiveKit Cloud test project.')
    name = 'aedrova-transport-check-' + uuid.uuid4().hex
    service = api.LiveKitAPI(url, key, secret)
    rooms, sources, tasks, streams = [], [], [], []
    created = False
    # Static screen shares legitimately send fewer frames than camera video.
    minimum = {'microphone': 20, 'camera': 20, 'screen_share': 5}
    received = {peer: {'microphone': 0, 'camera': 0, 'screen_share': 0} for peer in ('a', 'b')}

    async def consume(track, peer, kind):
        stream = (rtc.AudioStream(track, capacity=8) if kind == 'microphone'
                  else rtc.VideoStream(track, capacity=8, format=rtc.VideoBufferType.RGBA))
        streams.append(stream)
        async for event in stream:
            if kind == 'microphone':
                if event.frame.sample_rate != 48000 or not len(event.frame.data):
                    raise RuntimeError('Invalid received audio frame')
                if not any(abs(sample) > 32 for sample in event.frame.data):
                    continue
            else:
                f = event.frame
                image = QImage(bytes(f.data), f.width, f.height, f.width * 4,
                               QImage.Format.Format_RGBA8888)
                pixel = image.pixelColor(0, 0)
                if (image.isNull() or pixel.alpha() != 255
                        or abs(pixel.red() - 80) > 30
                        or abs(pixel.green() - 120) > 30
                        or abs(pixel.blue() - 160) > 30):
                    raise RuntimeError('Received video cannot be rendered by Qt')
            received[peer][kind] += 1
            if received[peer][kind] >= minimum[kind]:
                break

    try:
        await service.room.create_room(api.CreateRoomRequest(name=name, empty_timeout=60,
                                                             max_participants=2))
        created = True
        for peer in ('a', 'b'):
            room = rtc.Room()
            rooms.append(room)

            @room.on('track_subscribed')
            def subscribed(track, publication, participant, peer=peer):
                kind = publication.name
                if kind in received[peer]:
                    tasks.append(asyncio.create_task(consume(track, peer, kind)))

            token = (api.AccessToken(key, secret).with_identity(peer)
                     .with_ttl(timedelta(minutes=2))
                     .with_grants(api.VideoGrants(room_join=True, room=name,
                                                 can_publish_data=False))).to_jwt()
            options = rtc.RoomOptions(connect_timeout=15)
            if relay:
                options.rtc_config = rtc.RtcConfiguration(
                    ice_transport_type=rtc.IceTransportType.TRANSPORT_RELAY)
            await room.connect(url, token, options)
        for room in rooms:
            for kind, track_source in [('camera', rtc.TrackSource.SOURCE_CAMERA),
                                       ('screen_share', rtc.TrackSource.SOURCE_SCREENSHARE)]:
                source = rtc.VideoSource(320, 180)
                sources.append((kind, source))
                track = rtc.LocalVideoTrack.create_video_track(kind, source)
                await room.local_participant.publish_track(track,
                    rtc.TrackPublishOptions(source=track_source))
            source = rtc.AudioSource(48000, 1, queue_size_ms=100)
            sources.append(('microphone', source))
            track = rtc.LocalAudioTrack.create_audio_track('microphone', source)
            await room.local_participant.publish_track(track,
                rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE))
        pixels = bytes([80, 120, 160, 255]) * 320 * 180
        for step in range(300):
            for kind, source in sources:
                if kind == 'microphone':
                    samples = array('h', (int(3000 * math.sin(2 * math.pi * 440 *
                              (step * 480 + i) / 48000)) for i in range(480)))
                    await source.capture_frame(rtc.AudioFrame(samples.tobytes(), 48000, 1, 480))
                elif step % 3 == 0:
                    source.capture_frame(rtc.VideoFrame(320, 180, rtc.VideoBufferType.RGBA,
                                                        pixels))
            await asyncio.sleep(.01)
        await asyncio.sleep(.5)
        for task in tasks:
            if task.done() and not task.cancelled() and task.exception():
                raise task.exception()
        Path('work/meeting-frame-counts.json').write_text(json.dumps(received))
        if not all(count >= minimum[kind]
                   for peer in received.values() for kind, count in peer.items()):
            raise RuntimeError('Two-way media did not reach the minimum frame count')
        return {'sdk': version('livekit'), 'two_way_frames': received,
                'minimum_frames': minimum,
                'qt_render': 'passed', 'device_capture': 'not tested',
                'turn_relay': 'passed' if relay else 'not forced',
                'echo_reconnection': 'not tested', 'transcription': 'not tested'}
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for stream in streams:
            await stream.aclose()
        for room in rooms:
            await room.disconnect()
        for _, source in sources:
            await source.aclose()
        try:
            if created:
                await service.room.delete_room(api.DeleteRoomRequest(room=name))
        finally:
            await service.aclose()


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--relay', action='store_true', help='Require TURN relay transport')
    args = parser.parse_args()
    logging.getLogger('livekit').setLevel(logging.CRITICAL)
    destination = Path('work/meeting-transport-relay.json' if args.relay
                       else 'work/meeting-transport.json')
    destination.unlink(missing_ok=True)
    try:
        async with asyncio.timeout(45):
            report = await probe(relay=args.relay)
    except Exception as error:
        # Native/network errors may contain credential-bearing URLs. Never echo them.
        print(transport_failure(error))
        return 1
    Path('work').mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
