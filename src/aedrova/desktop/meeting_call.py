"""Native channel-call controls. Device access is always an explicit action."""

from PySide6.QtCore import QEvent, QSize, Qt, QTimer
from PySide6.QtGui import QImage, QPainter, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from aedrova.agents.managed import application_origin
from aedrova.desktop.brand import BrandMark
from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.meeting_icons import meeting_icon
from aedrova.desktop.meeting_setup import FramePreview
from aedrova.desktop.theme import palette
from aedrova.meetings.access import MeetingClient
from aedrova.meetings.call import CallWorker
from aedrova.meetings.devices import DeviceCheck


def encode_image(image, *, fill=False):
    """Bounded RGBA: camera fills without distortion; screens retain every edge."""
    result = QImage(640, 360, QImage.Format.Format_RGBA8888)
    result.fill(Qt.GlobalColor.black)
    mode = (Qt.AspectRatioMode.KeepAspectRatioByExpanding if fill else
            Qt.AspectRatioMode.KeepAspectRatio)
    fit = image.scaled(640, 360, mode,
                       Qt.TransformationMode.SmoothTransformation)
    painter = QPainter(result)
    painter.drawImage((640 - fit.width()) // 2, (360 - fit.height()) // 2, fit)
    painter.end()
    return result


def toolbar_control(text):
    control = QToolButton()
    control.setText(text)
    control.setAccessibleName(text)
    control.setToolTip(text)
    control.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    control.setAutoRaise(True)
    control.setCursor(Qt.CursorShape.PointingHandCursor)
    control.setMinimumHeight(66)
    control.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    control.setObjectName('CallControl')
    return control


class MeetingCall(AppDialog):
    def __init__(self, parent, worker, *, devices=None, channel_name='Team channel'):
        super().__init__(parent)
        if parent is not None and hasattr(parent, 'theme'):
            self.setPalette(palette(parent.theme))
        self.worker = worker
        self.devices = devices or DeviceCheck(self)
        self.connected = False
        self.closed = False
        self.states = {kind: False for kind in ('microphone', 'camera', 'screen')}
        self.mic_epoch = 0
        self.starting_device = None
        self.tiles = {}
        self.people = {worker.user}
        self.focused = worker.user + '/camera'
        self.names = {worker.user: 'You'}
        self.last_images = {}
        self.setWindowTitle('Aedrova · ' + channel_name + ' call')
        self.resize(1120, 760)
        self.setMinimumSize(640, 560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)
        heading = QHBoxLayout()
        heading.addWidget(BrandMark(32))
        heading.addWidget(label(channel_name, 'title', wrap=True), 1)
        self.view_choice = ChoiceBox(self)
        self.view_choice.addItems(['Gallery view', 'Speaker view'])
        self.view_choice.setAccessibleName('Meeting view')
        self.view_choice.currentIndexChanged.connect(self.arrange)
        heading.addWidget(self.view_choice)
        layout.addLayout(heading)
        summary = QHBoxLayout()
        self.status = label('Ready when you are. Join with your devices off.', 'muted', wrap=True)
        summary.addWidget(self.status, 1)
        self.join = button('Join channel call', role='primary')
        self.join.clicked.connect(self.join_call)
        summary.addWidget(self.join)
        layout.addLayout(summary)
        self.stage_row = QHBoxLayout()
        self.stage = FramePreview('Waiting for the speaker’s video')
        self.stage.setMinimumHeight(220)
        self.stage.setVisible(False)
        self.stage_row.addWidget(self.stage, 3)
        self.gallery = QScrollArea()
        self.gallery.setWidgetResizable(True)
        self.gallery.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        self.grid = QGridLayout(body)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(12)
        self.gallery.setWidget(body)
        body.setAutoFillBackground(False)
        self.gallery.viewport().setAutoFillBackground(False)
        self.stage_row.addWidget(self.gallery, 2)
        self.participant_panel = QFrame()
        panel = QVBoxLayout(self.participant_panel)
        panel.setContentsMargins(16, 12, 16, 12)
        panel.addWidget(label('Participants', 'title'))
        roster_scroll = QScrollArea()
        roster_scroll.setWidgetResizable(True)
        roster_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        roster_content = QWidget()
        roster_content.setObjectName("AccountPage")
        self.participant_body = QVBoxLayout(roster_content)
        self.participant_body.setContentsMargins(0, 0, 8, 0)
        self.participant_body.setAlignment(Qt.AlignmentFlag.AlignTop)
        roster_scroll.setWidget(roster_content)
        roster_scroll.viewport().setAutoFillBackground(False)
        panel.addWidget(roster_scroll, 1)
        self.participant_panel.setFixedWidth(220)
        self.participant_panel.hide()
        self.stage_row.addWidget(self.participant_panel)
        layout.addLayout(self.stage_row, 1)
        self.render_roster([{'id': worker.user, 'name': 'You'}])
        self.device_panel = QFrame()
        device_layout = QVBoxLayout(self.device_panel)
        device_layout.setContentsMargins(12, 8, 12, 8)
        choices = QHBoxLayout()
        self.camera_choice, self.screen_choice = ChoiceBox(self), ChoiceBox(self)
        for kind, choice in [('camera', self.camera_choice), ('screen', self.screen_choice)]:
            for device in self.devices.backend.list(kind):
                name = device.name() if kind == 'screen' else device.description()
                choice.addItem(name, device)
            if not choice.count():
                choice.addItem('No ' + kind + ' available', None)
            choice.setAccessibleName('Call ' + kind + ' device')
            choice.currentIndexChanged.connect(lambda _, kind=kind: self.disable(kind))
            choices.addWidget(choice)
        device_layout.addLayout(choices)
        device_layout.addWidget(label('Microphone and speakers use your system default. '
                                     'Screen sharing includes the entire selected screen.',
                                     'muted', wrap=True))
        self.device_panel.hide()
        layout.addWidget(self.device_panel)
        self.toolbar = QFrame()
        self.toolbar.setObjectName('CallToolbar')
        controls = QGridLayout(self.toolbar)
        controls.setContentsMargins(8, 4, 8, 4)
        controls.setSpacing(8)
        self.toolbar_layout = controls
        self.toolbar_buttons = []
        self.controls = {}
        for kind, text in [('microphone', 'Muted'), ('camera', 'Camera off'),
                           ('screen', 'Share screen')]:
            control = toolbar_control(text)
            control.setEnabled(False)
            control.clicked.connect(lambda checked=False, kind=kind: self.toggle(kind))
            self.controls[kind] = control
            self.toolbar_buttons.append(control)
        self.participants_button = toolbar_control('Participants (1)')
        self.participants_button.setCheckable(True)
        self.participants_button.toggled.connect(self.participant_panel.setVisible)
        self.toolbar_buttons.append(self.participants_button)
        self.settings_button = toolbar_control('Devices')
        self.settings_button.setCheckable(True)
        self.settings_button.toggled.connect(self.device_panel.setVisible)
        self.toolbar_buttons.append(self.settings_button)
        leave = toolbar_control('Leave')
        leave.setProperty('danger', True)
        leave.clicked.connect(self.reject)
        self.leave_button = leave
        self.toolbar_buttons.append(leave)
        self.arrange_toolbar()
        layout.addWidget(self.toolbar)
        footer = QHBoxLayout()
        footer.addWidget(label('No recording · No transcription · No AI meeting access',
                              'muted', wrap=True), 1)
        self.end = button('End for everyone · host/admin', role='outline')
        self.end.setEnabled(False)
        self.end.clicked.connect(lambda: self.worker.command('end', True))
        footer.addWidget(self.end)
        layout.addLayout(footer)
        for control in self.findChildren(type(self.join)):
            control.setAutoDefault(False)
        self.refresh_icons()
        self.devices.frame.connect(self.local_frame)
        self.devices.changed.connect(self.device_state)
        self.devices.problem.connect(self.device_problem)
        self.devices.inventory_changed.connect(self.devices_changed)
        worker.state.connect(self.call_state)
        worker.roster.connect(self.render_roster)
        worker.problem.connect(self.status.setText)
        worker.media.connect(self.media_state)
        worker.ended.connect(self.call_ended)
        if hasattr(worker, 'speaker'):
            worker.speaker.connect(self.speaker_changed)
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.remote_frames)
        self.timer.start()
        self.finished.connect(self.shutdown)
        QApplication.instance().aboutToQuit.connect(self.shutdown)

    def join_call(self):
        self.join.setEnabled(False)
        self.worker.start()

    def call_state(self, state):
        if self.closed:
            return
        self.status.setText(state)
        self.connected = state.startswith(('Connected', 'Reconnected'))
        self.end.setEnabled(self.connected)
        for kind, control in self.controls.items():
            control.setEnabled(self.connected)
            if not self.connected:
                self.disable(kind)
        self.join.setVisible(not self.connected)

    def toggle(self, kind):
        if not self.connected or self.closed:
            return
        if self.states[kind]:
            self.disable(kind)
            return
        self.states[kind] = True  # Includes permission/publish pending, cancellable.
        self.controls[kind].setText('Cancel ' + kind)
        if kind == 'microphone':
            self.mic_epoch += 1
            epoch = self.mic_epoch

            def permission(granted):
                if self.closed or epoch != self.mic_epoch or not self.connected:
                    return
                if granted:
                    self.worker.command(kind, True)
                else:
                    self.disable(kind)
                    self.status.setText('Microphone permission is needed. Check '
                                        'System Settings → Privacy & Security → Microphone.')
            try:
                self.devices.backend.permission(kind, permission)
            except Exception:
                permission(False)
        else:
            choice = self.camera_choice if kind == 'camera' else self.screen_choice
            device = choice.currentData()
            if device is None:
                self.disable(kind)
                self.status.setText('No device is available for this control.')
            else:
                self.starting_device = kind
                try:
                    self.devices.start(kind, device)
                finally:
                    self.starting_device = None

    def disable(self, kind, *, notify_worker=True):
        self.states[kind] = False
        if kind == 'microphone':
            self.mic_epoch += 1
        else:
            self.devices.stop(kind)
        self.worker.clear_frame(kind)
        if notify_worker:
            self.worker.command(kind, False)
        names = {'microphone': 'Muted', 'camera': 'Camera off', 'screen': 'Share screen'}
        self.controls[kind].setText(names[kind])
        self.refresh_icons()
        key = self.worker.user + ('/screen' if kind == 'screen' else '/camera')
        if kind != 'microphone' and key in self.tiles:
            self.tiles[key][1].clear()
        if kind != 'microphone':
            self.last_images.pop(key, None)
            if key == self.focused:
                self.stage.clear()
            self.arrange()

    def device_state(self, kind, state):
        if kind not in {'camera', 'screen'}:
            return
        if state == 'active' and self.states[kind] and not self.closed:
            self.worker.command(kind, True)
        elif state == 'off' and self.states[kind] and self.starting_device != kind:
            self.disable(kind)

    def media_state(self, kind, enabled):
        if self.closed:
            return
        if '/' in kind:
            if kind in self.tiles:
                self.tiles[kind][1].clear()
            self.last_images.pop(kind, None)
            if kind == self.focused:
                self.stage.clear()
            self.arrange()
            return
        if kind not in self.states:
            return
        self.states[kind] = enabled
        if not enabled:
            self.disable(kind, notify_worker=False)
        else:
            names = {'microphone': 'Unmuted', 'camera': 'Camera on', 'screen': 'Sharing screen'}
            self.controls[kind].setText(names[kind])
            self.refresh_icons()

    def device_problem(self, message):
        for kind in ('camera', 'screen'):
            if self.states[kind] and kind not in self.devices.handles:
                self.disable(kind)
        self.status.setText(message)

    def local_frame(self, kind, image):
        if self.connected and not self.closed and self.states.get(kind):
            frame = encode_image(image, fill=kind == 'camera')
            self.worker.frame(kind, frame)
            key = self.worker.user + ('/screen' if kind == 'screen' else '/camera')
            self.tile(key, 'Your screen' if kind == 'screen' else 'You')[1].display(frame)
            self.last_images[key] = frame
            if kind == 'screen':
                self.focused = key
                self.arrange()
            if key == self.focused:
                self.stage.display(frame)

    def tile(self, key, name):
        if key not in self.tiles:
            box = QFrame()
            box.setPalette(self.palette())
            box.setStyleSheet('QFrame {background: transparent; border: none;}')
            layout = QGridLayout(box)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            preview = FramePreview('Video is off', fill=key.endswith('/camera'))
            preview.setPalette(self.palette())
            preview.setStyleSheet('background: transparent;')
            layout.addWidget(preview, 0, 0)
            caption = label(name, 'muted', wrap=True)
            caption.setStyleSheet('QLabel {color: #FFFFFF; background: rgba(0,0,0,145); '
                                 'border-radius: 8px; padding: 5px 9px; margin: 10px;}')
            caption.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout.addWidget(caption, 0, 0, Qt.AlignmentFlag.AlignLeft |
                             Qt.AlignmentFlag.AlignBottom)
            index = len(self.tiles)
            self.grid.addWidget(box, index // 2, index % 2)
            self.tiles[key] = box, preview
        return self.tiles[key]

    def render_roster(self, people):
        if self.closed:
            return
        ids = {person['id'] for person in people}
        self.people = ids
        self.names = {person['id']: str(person['name'])[:80] for person in people}
        while self.participant_body.count():
            item = self.participant_body.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        for person in people[:16]:
            name = str(person['name'])[:80]
            status = 'Microphone on' if person.get('microphone_on') else 'Muted'
            self.participant_body.addWidget(label(name, wrap=True))
            self.participant_body.addWidget(label(status, 'muted'))
        if hasattr(self, 'participants_button'):
            self.participants_button.setText(f'Participants ({len(people)})')
        for key in list(self.tiles):
            if key.split('/')[0] not in ids:
                box, _ = self.tiles.pop(key)
                self.grid.removeWidget(box)
                box.deleteLater()
                self.last_images.pop(key, None)
        for person in people[:16]:
            self.tile(person['id'] + '/camera', str(person['name'])[:80])
        self.arrange()

    def remote_frames(self):
        if self.closed:
            return
        for key, image in self.worker.take_remote_frames().items():
            if key.split('/')[0] not in self.people:
                continue
            if len(self.tiles) < 32 or key in self.tiles:
                name = 'Shared screen' if key.endswith('/screen') else 'Teammate'
                self.tile(key, name)[1].display(image)
                self.last_images[key] = image
                if key.endswith('/screen'):
                    self.focused = key
                    self.arrange()
                if key == self.focused:
                    self.stage.display(image)

    def arrange(self, *_):
        if not hasattr(self, 'gallery'):
            return
        screen = next((key for key in self.last_images if key.endswith('/screen')), None)
        spotlight = self.view_choice.currentIndex() == 1 or screen is not None
        if screen:
            self.focused = screen
        if self.focused.split('/')[0] not in self.people:
            self.focused = self.worker.user + '/camera'
        self.stage.fill = self.focused.endswith('/camera')
        self.stage.setVisible(spotlight)
        self.gallery.setMaximumWidth(280 if spotlight else 16777215)
        columns = 1 if spotlight else 2
        for index, (box, _) in enumerate(self.tiles.values()):
            self.grid.addWidget(box, index // columns, index % columns)
        if spotlight:
            image = self.last_images.get(self.focused)
            if image is not None:
                self.stage.display(image)
            else:
                self.stage.clear()

    def speaker_changed(self, user):
        if user in self.people and not any(key.endswith('/screen') for key in self.last_images):
            self.focused = user + '/camera'
            self.arrange()

    def refresh_icons(self):
        if not hasattr(self, 'controls'):
            return
        color = self.palette().color(QPalette.ColorRole.Text)
        for kind, control in self.controls.items():
            off = kind in {'microphone', 'camera'} and not self.states[kind]
            control.setIcon(meeting_icon(kind, color, off=off))
            actions = {'microphone': ('Unmute microphone', 'Mute microphone'),
                       'camera': ('Turn camera on', 'Turn camera off'),
                       'screen': ('Start sharing screen', 'Stop sharing screen')}
            control.setAccessibleName(control.text())
            control.setToolTip(actions[kind][int(self.states[kind])])
            control.setIconSize(QSize(20, 20))
        for control, kind in ((self.participants_button, 'participants'),
                              (self.settings_button, 'settings'), (self.leave_button, 'leave')):
            control.setIcon(meeting_icon(kind, color))
            control.setIconSize(QSize(20, 20))

    def arrange_toolbar(self):
        if not hasattr(self, 'toolbar_buttons'):
            return
        columns = 3 if self.width() < 850 else 6
        for index, control in enumerate(self.toolbar_buttons):
            control.setMinimumWidth(control.fontMetrics().horizontalAdvance(control.text()) + 24)
            self.toolbar_layout.addWidget(control, index // columns, index % columns)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self.arrange_toolbar()

    def changeEvent(self, event):  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.PaletteChange:
            self.refresh_icons()

    def devices_changed(self):
        for kind in self.states:
            self.disable(kind)
        self.status.setText('Devices changed. Leave and rejoin to refresh device choices.')

    def call_ended(self):
        self.connected = False
        self.devices.close()
        for kind in self.states:
            self.disable(kind)
            self.controls[kind].setEnabled(False)
        self.end.setEnabled(False)
        self.join.setVisible(False)
        self.timer.stop()
        self.last_images.clear()
        self.stage.clear()
        for _, preview in self.tiles.values():
            preview.clear()

    def shutdown(self, *_):
        if self.closed:
            return
        self.closed = True
        self.mic_epoch += 1
        self.devices.close()
        self.timer.stop()
        self.worker.stop()
        self.last_images.clear()
        self.stage.clear()
        for _, preview in self.tiles.values():
            preview.clear()

    def hideEvent(self, event):  # noqa: N802
        if not event.spontaneous():
            self.shutdown()
        super().hideEvent(event)


def open_channel_call(window):
    existing = getattr(window, 'meeting_call', None)
    if existing and existing.isVisible():
        existing.raise_()
        existing.activateWindow()
        return
    if existing and existing.worker.thread and existing.worker.thread.is_alive():
        window.notify('Your previous call is leaving. Please try again shortly.')
        return
    if not window.connected or not window.connected.active:
        window.notify('Sign in and open a workspace to join a channel call.')
        return
    origin = application_origin()
    if not origin:
        window.notify('The Aedrova meeting service is not configured yet.')
        return
    service = window.account_dialog.service
    token = service.client.auth.get_session().access_token
    worker = CallWorker(MeetingClient(origin, token), workspace=window.workspace_id,
                        channel=window.channel_id, user=str(service.user.id), parent=window)
    dialog = MeetingCall(window, worker,
                         channel_name=window.workspace.name + ' / ' + window.channel.name)
    window.meeting_call = dialog
    window.account_dialog.session_closed.connect(dialog.reject)
    # A local setup preview cannot compete with call capture for the same device.
    setup = getattr(window, 'meeting_setup', None)
    if setup and setup.isVisible():
        setup.reject()
    dialog.show()
