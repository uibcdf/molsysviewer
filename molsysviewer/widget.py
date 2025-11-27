import anywidget
import traitlets as T
from pathlib import Path

class MolSysViewerWidget(anywidget.AnyWidget):
    _esm = (Path(__file__).parent / "viewer.js").read_text(encoding="utf-8")
    initial_messages = T.List(default_value=[]).tag(sync=True)
