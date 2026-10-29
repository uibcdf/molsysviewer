"""Quiet native window decoration around the shared canvas.

Qt classes are resolved only when a host is created. Importing the Python
library remains headless and does not require the optional Qt binding.
"""

from __future__ import annotations


def _install_window_chrome(*, window, webview, qt):
    core, gui, widgets = qt["QtCore"], qt["QtGui"], qt["QtWidgets"]
    Qt = core.Qt

    def icon(kind, color):
        result = gui.QIcon()
        for scale in (1, 2, 3):
            pixmap = gui.QPixmap(20 * scale, 20 * scale)
            pixmap.setDevicePixelRatio(scale)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = gui.QPainter(pixmap)
            painter.setRenderHint(gui.QPainter.RenderHint.Antialiasing)
            pen = gui.QPen(gui.QColor(color), 1.4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            if kind == "minimize":
                painter.drawLine(5, 11, 15, 11)
            elif kind == "maximize":
                painter.drawRoundedRect(core.QRectF(5, 5, 10, 10), 1, 1)
            elif kind == "restore":
                painter.drawLine(8, 5, 15, 5)
                painter.drawLine(15, 5, 15, 12)
                painter.drawRoundedRect(core.QRectF(5, 8, 7, 7), 1, 1)
            else:
                painter.drawLine(6, 6, 14, 14)
                painter.drawLine(14, 6, 6, 14)
            painter.end()
            result.addPixmap(pixmap)
        return result

    class Header(widgets.QWidget):
        def __init__(self, chrome):
            super().__init__(chrome.frame)
            self.chrome = chrome
            self.drag_origin = None
            self.setObjectName("molsysviewerWindowHeader")
            self.setFixedHeight(40)
            row = widgets.QHBoxLayout(self)
            row.setContentsMargins(14, 0, 6, 0)
            row.setSpacing(6)
            brand = widgets.QLabel("MolSysViewer", self)
            brand.setObjectName("molsysviewerWindowBrand")
            brand.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row.addWidget(brand)
            row.addStretch(1)
            chrome.status = widgets.QLabel(self)
            chrome.status.setObjectName("molsysviewerWindowStatus")
            chrome.status.setAccessibleName("Application status")
            chrome.status.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row.addWidget(chrome.status)
            chrome.buttons = {}
            controls = (
                ("minimize", "Minimize window", window.showMinimized),
                ("maximize", "Maximize window", chrome.toggle_maximized),
                ("close", "Close window", window.close),
            )
            for kind, label, callback in controls:
                button = widgets.QToolButton(self)
                button.setObjectName("molsysviewerWindow" + kind.capitalize())
                button.setAccessibleName(label)
                button.setToolTip(label)
                button.setFixedSize(34, 28)
                button.setIconSize(core.QSize(20, 20))
                button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                button.clicked.connect(callback)
                chrome.buttons[kind] = button
                row.addWidget(button)

        def mousePressEvent(self, event):  # noqa: N802
            if event.button() == Qt.MouseButton.LeftButton and not window.isFullScreen():
                handle = window.windowHandle()
                if handle is not None and handle.startSystemMove():
                    event.accept()
                    return
                if widgets.QApplication.platformName() != "wayland":
                    self.drag_origin = (event.globalPosition().toPoint(), window.pos())
                    event.accept()
                    return
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event):  # noqa: N802
            if self.drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
                start, position = self.drag_origin
                window.move(position + event.globalPosition().toPoint() - start)
                event.accept()
                return
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):  # noqa: N802
            self.drag_origin = None
            super().mouseReleaseEvent(event)

        def mouseDoubleClickEvent(self, event):  # noqa: N802
            if event.button() == Qt.MouseButton.LeftButton:
                self.chrome.toggle_maximized()
                event.accept()
                return
            super().mouseDoubleClickEvent(event)

    class Frame(widgets.QFrame):
        def __init__(self):
            super().__init__(window)
            self.setObjectName("molsysviewerWindowFrame")
            self.setMouseTracking(True)
            self.resize_origin = None

        def edges(self, position):
            edges = Qt.Edge(0)
            if window.isMaximized() or window.isFullScreen():
                return edges
            x, y = position.x(), position.y()
            if x < 5:
                edges |= Qt.Edge.LeftEdge
            elif x >= self.width() - 5:
                edges |= Qt.Edge.RightEdge
            if y < 5:
                edges |= Qt.Edge.TopEdge
            elif y >= self.height() - 5:
                edges |= Qt.Edge.BottomEdge
            return edges

        def mousePressEvent(self, event):  # noqa: N802
            edges = self.edges(event.position())
            if event.button() == Qt.MouseButton.LeftButton and edges:
                handle = window.windowHandle()
                if handle is not None and handle.startSystemResize(edges):
                    event.accept()
                    return
                if widgets.QApplication.platformName() != "wayland":
                    self.resize_origin = (event.globalPosition().toPoint(), window.geometry(), edges)
                    event.accept()
                    return
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event):  # noqa: N802
            if self.resize_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
                start, original, edges = self.resize_origin
                delta = event.globalPosition().toPoint() - start
                rect = core.QRect(original)
                if edges & Qt.Edge.LeftEdge:
                    rect.setLeft(min(original.left() + delta.x(), original.right() - window.minimumWidth() + 1))
                if edges & Qt.Edge.RightEdge:
                    rect.setRight(max(original.right() + delta.x(), original.left() + window.minimumWidth() - 1))
                if edges & Qt.Edge.TopEdge:
                    rect.setTop(min(original.top() + delta.y(), original.bottom() - window.minimumHeight() + 1))
                if edges & Qt.Edge.BottomEdge:
                    rect.setBottom(max(original.bottom() + delta.y(), original.top() + window.minimumHeight() - 1))
                window.setGeometry(rect)
                event.accept()
                return
            edges = self.edges(event.position())
            horizontal = edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge)
            vertical = edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge)
            if horizontal and vertical:
                same = bool(edges & Qt.Edge.LeftEdge) == bool(edges & Qt.Edge.TopEdge)
                cursor = Qt.CursorShape.SizeFDiagCursor if same else Qt.CursorShape.SizeBDiagCursor
            elif horizontal:
                cursor = Qt.CursorShape.SizeHorCursor
            elif vertical:
                cursor = Qt.CursorShape.SizeVerCursor
            else:
                cursor = Qt.CursorShape.ArrowCursor
            self.setCursor(cursor)
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):  # noqa: N802
            self.resize_origin = None
            super().mouseReleaseEvent(event)

    class Chrome(core.QObject):
        def __init__(self):
            super().__init__(window)
            self.frame = Frame()
            self.layout = widgets.QVBoxLayout(self.frame)
            self.layout.setSpacing(0)
            self.header = Header(self)
            self.layout.addWidget(self.header)
            self.layout.addWidget(webview, 1)
            self.status_timer = core.QTimer(self)
            self.status_timer.setSingleShot(True)
            self.status_timer.setInterval(7000)
            self.status_timer.timeout.connect(self.status.hide)
            self.status_bar = window.statusBar()
            self.status_bar.setSizeGripEnabled(False)
            self.status_bar.messageChanged.connect(self.show_status)
            self.status_bar.hide()
            window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
            window.setMinimumSize(560, 360)
            window.setCentralWidget(self.frame)
            window.installEventFilter(self)
            self.refresh_style()
            self.sync_state()
            self.show_status(self.status_bar.currentMessage())

        def refresh_style(self):
            palette = window.palette()
            self.foreground = palette.color(gui.QPalette.ColorRole.Text).name()
            self.background = palette.color(gui.QPalette.ColorRole.Base).name()
            dark = palette.color(gui.QPalette.ColorRole.Base).lightness() < 128
            self.border = "#3f4650" if dark else "#dce1e7"
            hover = "#343b45" if dark else "#edf0f4"
            self.frame.setStyleSheet(
                f"#molsysviewerWindowFrame {{ background: {self.background}; border: 1px solid {self.border}; }}"
                '#molsysviewerWindowFrame[expanded="true"] { border: 0; }'
                f"#molsysviewerWindowHeader {{ background: {self.background}; }}"
                f"#molsysviewerWindowBrand {{ color: {self.foreground}; font-size: 13px; font-weight: 600; }}"
                f"#molsysviewerWindowStatus {{ color: {self.foreground}; font-size: 11px; padding: 3px 8px; }}"
                "QToolButton { border: 1px solid transparent; border-radius: 5px; background: transparent; }"
                f"QToolButton:hover {{ background: {hover}; }}"
                f"QToolButton:focus {{ border-color: {palette.color(gui.QPalette.ColorRole.Highlight).name()}; }}"
                "#molsysviewerWindowClose:hover { background: #dc3545; }"
            )
            for kind, button in self.buttons.items():
                glyph = "restore" if kind == "maximize" and window.isMaximized() else kind
                button.setIcon(icon(glyph, self.foreground))

        def toggle_maximized(self):
            if window.isFullScreen():
                return
            if window.isMaximized():
                window.showNormal()
            else:
                window.showMaximized()

        def sync_state(self):
            expanded = window.isMaximized() or window.isFullScreen()
            self.frame.setProperty("expanded", expanded)
            self.frame.style().unpolish(self.frame)
            self.frame.style().polish(self.frame)
            margin = 0 if expanded else 5
            self.layout.setContentsMargins(margin, margin, margin, margin)
            self.header.setVisible(not window.isFullScreen())
            label = "Restore window" if window.isMaximized() else "Maximize window"
            self.buttons["maximize"].setAccessibleName(label)
            self.buttons["maximize"].setToolTip(label)
            self.buttons["maximize"].setIcon(icon("restore" if window.isMaximized() else "maximize", self.foreground))

        def show_status(self, message):
            self.status_timer.stop()
            if not message or message.startswith("Ready"):
                self.status.hide()
                return
            self.status.setToolTip(message)
            self.status.setAccessibleDescription(message)
            width = min(420, max(120, window.width() // 3))
            self.status.setText(self.status.fontMetrics().elidedText(message, Qt.TextElideMode.ElideRight, width))
            self.status.show()
            lower = message.lower()
            error = any(word in lower for word in ("failed", "could not", "error", "timeout", "timed out"))
            self.status.setStyleSheet("color: #dc3545;" if error else "")
            if not error and not any(word in lower for word in ("loading", "rendering", "downloading", "connecting")):
                self.status_timer.start()

        def eventFilter(self, watched, event):  # noqa: N802
            if watched is window:
                if event.type() == core.QEvent.Type.WindowStateChange:
                    self.sync_state()
                elif event.type() == core.QEvent.Type.PaletteChange:
                    self.refresh_style()
                elif event.type() == core.QEvent.Type.Close:
                    self.status_timer.stop()
            return False

    chrome = Chrome()
    window._molsysviewer_chrome = chrome
    return chrome
