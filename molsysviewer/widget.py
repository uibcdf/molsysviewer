import anywidget
import traitlets as T
from pathlib import Path


class MolSysViewerWidget(anywidget.AnyWidget):
    _esm = (Path(__file__).parent / "viewer.js").read_text(encoding="utf-8")
    initial_messages = T.List(default_value=[]).tag(sync=True)
    show_controls = T.Bool(default_value=True).tag(sync=True)
    autohide_controls = T.Bool(default_value=True).tag(sync=True)
    controls_position = T.List(T.Unicode(), default_value=["top", "right"]).tag(sync=True)
    controls_position_fullscreen = T.List(T.Unicode(), default_value=["bottom", "right"]).tag(sync=True)
