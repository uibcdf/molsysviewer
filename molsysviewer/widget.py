import anywidget
import traitlets as T
from pathlib import Path


class MolSysViewerWidget(anywidget.AnyWidget):
    _esm = (Path(__file__).parent / "viewer.js").read_text(encoding="utf-8")
    
    # Send the viewer source code to the frontend so it can replicate itself in the popup
    # regardless of server configuration, ports, or CDNs.
    popup_js_source = T.Unicode(_esm).tag(sync=True)
    
    initial_messages = T.List(default_value=[]).tag(sync=True)
    show_controls = T.Bool(default_value=True).tag(sync=True)
    enable_popout = T.Bool(default_value=True).tag(sync=True)
    autohide_controls = T.Bool(default_value=True).tag(sync=True)
    debug_js = T.Bool(default_value=False).tag(sync=True)
    controls_position = T.List(T.Unicode(), default_value=["top", "right"]).tag(sync=True)
    controls_position_fullscreen = T.List(T.Unicode(), default_value=["bottom", "right"]).tag(sync=True)
    controls_mode = T.Unicode(default_value="classic").tag(sync=True)
    panel_mode_style = T.Unicode(default_value="drawer").tag(sync=True)
    viewer_mode = T.Unicode(default_value="classic").tag(sync=True)
    addon_states = T.Dict(default_value={}).tag(sync=True)
