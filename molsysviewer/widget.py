# molsysviewer/widget.py

from __future__ import annotations

from typing import Any

from ipywidgets import DOMWidget
from traitlets import Dict as TDict
from traitlets import Int, Unicode


class MolSysViewerWidget(DOMWidget):
    """Low-level ipywidget that talks to the Mol* frontend."""

    # Estos nombres deben coincidir con los usados en el lado JS (widget.ts)
    _model_name = Unicode("MolSysViewerModel").tag(sync=True)
    _view_name = Unicode("MolSysViewerView").tag(sync=True)
    _model_module = Unicode("molsysviewer").tag(sync=True)
    _view_module = Unicode("molsysviewer").tag(sync=True)

    # Versionado del módulo JS (luego lo ajustaremos al publicarlo en npm)
    _model_module_version = Unicode("^0.0.0").tag(sync=True)
    _view_module_version = Unicode("^0.0.0").tag(sync=True)

    # Estado genérico que el frontend puede usar para guardar cosas
    state = TDict(default_value={}).tag(sync=True)

    # Frame actual de la trayectoria (cuando tengamos una)
    frame = Int(0).tag(sync=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Aquí podríamos inicializar alguna cosa si hace falta más adelante.

