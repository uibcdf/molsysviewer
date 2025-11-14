import anywidget
from pathlib import Path

class MolSysViewerWidget(anywidget.AnyWidget):
    _esm = (Path(__file__).parent / "viewer.js").read_text()
