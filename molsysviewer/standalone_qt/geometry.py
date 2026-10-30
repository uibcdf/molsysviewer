"""Private native geometry policy; the compositor owns positioning on Wayland."""

from __future__ import annotations


def _capture_geometry(window):
    rect = (
        window.normalGeometry()
        if window.isMaximized() or window.isFullScreen() or window.isMinimized()
        else window.geometry()
    )
    screen = window.screen()
    return {
        "x": rect.x(),
        "y": rect.y(),
        "width": rect.width(),
        "height": rect.height(),
        "screen": screen.name() if screen is not None else None,
    }


def _restore_geometry(window, app, qt, state, *, width=None, height=None):
    saved = state.get("window_geometry")
    saved = saved if isinstance(saved, dict) else {}
    legacy = state.get("window_size")
    legacy = legacy if isinstance(legacy, dict) else {}

    def positive(value, fallback):
        return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else fallback

    w = positive(width, positive(saved.get("width"), positive(legacy.get("width"), 1440)))
    h = positive(height, positive(saved.get("height"), positive(legacy.get("height"), 960)))
    screen = next((s for s in app.screens() if s.name() == saved.get("screen")), window.screen())
    screen = screen or app.primaryScreen()
    if screen is not None:
        available = screen.availableGeometry()
        w, h = min(w, available.width()), min(h, available.height())
        window.resize(w, h)
        # Wayland permits system moves initiated by a user gesture, not this
        # application-specified global position. Let its compositor place us.
        if app.platformName() != "wayland":
            x, y = saved.get("x"), saved.get("y")
            x = x if isinstance(x, int) and not isinstance(x, bool) else available.center().x() - w // 2
            y = y if isinstance(y, int) and not isinstance(y, bool) else available.center().y() - h // 2
            x = max(available.left(), min(x, available.right() - w + 1))
            y = max(available.top(), min(y, available.bottom() - h + 1))
            window.move(x, y)
    else:
        window.resize(w, h)
    if width is None and height is None and state.get("window_maximized") is True:
        window.setWindowState(qt["QtCore"].Qt.WindowState.WindowMaximized)
