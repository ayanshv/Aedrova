"""One motion language: three durations, one easing curve, and respect for Reduce Motion.

Things that appear fade in quickly, things that change state take a little longer, and
nothing bounces. Every helper does nothing when the person has asked for less motion.
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect

FAST = 120  # hover, press, small state changes
BASE = 180  # things appearing: cards, popovers, pages
SLOW = 260  # larger moves: panels sliding, summaries expanding
EASE = QEasingCurve.Type.OutCubic


def reduced():
    app = QApplication.instance()
    return bool(app and app.property("reduceMotion") is True)


def fade_in(widget, duration=BASE):
    """Fade a child widget in. Returns the animation, or None when motion is reduced."""
    if reduced() or widget is None:
        return None
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(EASE)
    # Drop the effect afterwards: it costs repaint time and blurs some text on macOS.
    animation.finished.connect(lambda: widget.setGraphicsEffect(None))
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation


def fade_in_window(window, duration=BASE):
    """Fade a top-level window or popover in."""
    if reduced():
        window.setWindowOpacity(1.0)
        return None
    window.setWindowOpacity(0.0)
    animation = QPropertyAnimation(window, b"windowOpacity", window)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(EASE)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation


def reveal(widgets, *, step=70, duration=SLOW, delay=0):
    """Bring a screen's pieces in one after another, top to bottom.

    Everything starts fully transparent so nothing flashes, then each piece fades in a
    beat after the one above. With reduced motion everything simply appears.
    """
    from PySide6.QtCore import QTimer

    widgets = [w for w in widgets if w is not None]
    if reduced():
        return
    effects = []
    for widget in widgets:
        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(0.0)
        widget.setGraphicsEffect(effect)
        effects.append(effect)

    def start(widget, effect):
        try:
            animation = QPropertyAnimation(effect, b"opacity", widget)
        except RuntimeError:  # the screen changed before this piece's turn
            return
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(EASE)
        animation.finished.connect(lambda: widget.setGraphicsEffect(None))
        animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    for index, (widget, effect) in enumerate(zip(widgets, effects, strict=True)):
        QTimer.singleShot(delay + index * step, lambda w=widget, e=effect: start(w, e))


def appear_window(window, duration=480, rise=14):
    """A window arriving: it fades up while settling a few points into place, never popping in."""
    if reduced():
        window.setWindowOpacity(1.0)
        return None
    from PySide6.QtCore import QVariantAnimation

    window.setWindowOpacity(0.0)
    home = window.pos()
    lift = 0 if window.isFullScreen() or window.isMaximized() else rise
    animation = QVariantAnimation(window)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(EASE)

    def step(value):
        window.setWindowOpacity(float(value))
        if lift:
            window.move(home.x(), home.y() + round(lift * (1.0 - float(value))))

    animation.valueChanged.connect(step)
    animation.finished.connect(lambda: (window.setWindowOpacity(1.0), window.move(home)))
    animation.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation
