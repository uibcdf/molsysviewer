from __future__ import annotations

import base64
import json
import re
import time
import inspect
import warnings
import weakref
import uuid
from collections import OrderedDict
from contextlib import contextmanager
from typing import Any, Dict, Mapping, Sequence

import molsysmt as msm
import numpy as np
from smonitor import signal
from smonitor.integrations import context_extra, emit_from_catalog
from depdigest import dep_digest

from .._pyunitwizard import puw
from .._private.arg_digestion import digest
from .._private.arg_digestion.argument.viewer_mode import digest_viewer_mode
from .._private.smonitor import CATALOG, PACKAGE_ROOT, META
from .._private.smonitor_emit import emit_suppressed_exception
from .._private.variables import is_all
from ..widget import MolSysViewerWidget
from ..loaders import load_from_molsysmt as _load_from_molsysmt
from ..loaders.array_native_molsys import (
    ARRAY_NATIVE_PROTOCOL_VERSION,
    serialize_array_native_molsys,
)
from ..loaders.json_molsys import build_json_molsys_message
from ..transport import (
    AckDisposition,
    LazyMolecularMessage,
    StructureTransfer,
    StructureTransferManager,
    TransferChunk,
    TransferTermination,
    is_lazy_molecular_message,
)
from .runtime_router import WidgetRuntimeRouter, is_envelope
from ..annotations import AnnotationsManager
from ..active_selection import ActiveSelection, _combine
from ..addons import AddonPanelWidget, ViewAddonsManager, addons as global_addons
from ..exports import ExportManager
from ..figures import FigureSpec
from ..interaction_targets import InteractionTarget
from ..measurements import MeasurementsManager
from ..player import PlayerManager
from ..trajectory_plot import TrajectoryPlotManager
from ..scene import SceneManager
from ..selections import SelectionsManager, Selection
from ..styles import StylesManager
from ..shapes import ShapesManager
from ..regions import Region, RegionsManager
from ..whole import Whole
from ..layers import Layer, LayersManager, SceneObject
from ..tags import TagsManager
from ..colors import colors as global_colors
from .. import config

from .history import HistoryMixin
from ..scene_history import SceneHistory, records_scene_history
from .camera import CameraManager
from .movie import MovieManager
from .export import ExportMixin
from .scene_registry import SceneRegistryMixin
from .panel_actions import dispatch_panel_action

# The new Mixins
from .regions import RegionsMixin
from .panel_mode import PanelModeMixin
from .load import LoadMixin
from .visibility import VisibilityMixin
from .scene import SceneMixin
from .molsysmt_interface import MolSysMTInterfaceMixin
from .state import StateMixin
from .popup_snapshot import PopupSnapshotMixin
from .interaction import InteractionMixin

from .utils import quantity_value_in_unit as _quantity_value_in_unit

_HTML_MANAGER_VERSION = "1.0.1"
_WIDGETS_BASE_VERSION = "2.0.0"


class ViewerInfo:
    """Wrapper for the dual-section output of ``MolSysView.info(source='all')``.

    Holds the *molsys* and *view* sections (pandas Stylers by default) and
    renders both sequentially in Jupyter via ``_repr_html_()``.
    """
    def __init__(self, molsys_section: Any, view_section: Any) -> None:
        self.molsys_section = molsys_section
        self.view_section = view_section

    def _repr_html_(self) -> str:
        h1 = (
            getattr(self.molsys_section, "_repr_html_", None)
            or getattr(self.molsys_section, "to_html", None)
        )
        h2 = (
            getattr(self.view_section, "_repr_html_", None)
            or getattr(self.view_section, "to_html", None)
        )
        out = []
        if h1:
            out.append("<h3>Molecular System</h3>")
            out.append(h1())
        if h2:
            out.append("<h3>Viewer State</h3>")
            out.append(h2())
        return "\n".join(out)

    def __repr__(self) -> str:
        return f"ViewerInfo(molsys_section={self.molsys_section!r}, view_section={self.view_section!r})"

    def __getitem__(self, key: str) -> Any:
        if key == "molsys":
            return self.molsys_section
        if key == "view":
            return self.view_section
        raise KeyError(f"ViewerInfo has no key {key!r}. Use 'molsys' or 'view'.")

    def keys(self):
        return ["molsys", "view"]


class RegionInfo:
    """Wrapper for the dual-section output of ``Region.info(source='all')``.

    Holds the *molsys* and *region* sections (pandas Stylers by default) and
    renders both sequentially in Jupyter via ``_repr_html_()``.
    """
    def __init__(self, tag: str, molsys_section: Any, region_section: Any) -> None:
        self.tag = tag
        self.molsys_section = molsys_section
        self.region_section = region_section

    def _repr_html_(self) -> str:
        h1 = (
            getattr(self.molsys_section, "_repr_html_", None)
            or getattr(self.molsys_section, "to_html", None)
        )
        h2 = (
            getattr(self.region_section, "_repr_html_", None)
            or getattr(self.region_section, "to_html", None)
        )
        out = []
        if h1:
            out.append(f"<h3>Molecular System (Region {self.tag!r})</h3>")
            out.append(h1())
        if h2:
            out.append(f"<h3>Viewer Registry (Region {self.tag!r})</h3>")
            out.append(h2())
        return "\n".join(out)

    def __repr__(self) -> str:
        return f"RegionInfo(tag={self.tag!r}, molsys_section={self.molsys_section!r}, region_section={self.region_section!r})"

    def __getitem__(self, key: str) -> Any:
        if key == "molsys":
            return self.molsys_section
        if key == "region":
            return self.region_section
        raise KeyError(f"RegionInfo has no key {key!r}. Use 'molsys' or 'region'.")

    def keys(self):
        return ["molsys", "region"]


class MolSysView(
    SceneRegistryMixin,
    HistoryMixin,
    ExportMixin,
    RegionsMixin,
    PanelModeMixin,
    LoadMixin,
    VisibilityMixin,
    SceneMixin,
    MolSysMTInterfaceMixin,
    StateMixin,
    PopupSnapshotMixin,
    InteractionMixin,
):
    """Mol* viewer widget with a Python-facing API.

    Provides structure loading, visibility control, shape management, and
    utilities to export static HTML views for documentation or sharing.
    """
    def _repr_mimebundle_(self, include=None, exclude=None):
        """IPython/Jupyter display hook (delegates to the underlying widget)."""
        return self.widget._repr_mimebundle_(include=include, exclude=exclude)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def close(self) -> None:
        """Release the frontend transport and widgets owned by this view.

        Closing is explicit because widget registries retain open views even
        after user code drops its last reference. The operation is idempotent.
        """
        self._unmount_addon_panel()
        self.addons._close_runtime()  # noqa: SLF001
        self._cancel_binary_structure_stream("view closed")

        widget = self.widget
        layout = getattr(widget, "layout", None)
        callback = getattr(self, "_widget_message_callback", None)
        on_msg = getattr(widget, "on_msg", None)
        if callback is not None and callable(on_msg):
            try:
                on_msg(callback, remove=True)
            except TypeError:
                # Non-Jupyter transports own their callback cleanup in close().
                pass
        self._widget_message_callback = None
        if isinstance(widget, MolSysViewerWidget):
            widget._molsysviewer_view_ref = None

        close_widget = getattr(widget, "close", None)
        if callable(close_widget):
            close_widget()

        # ipywidgets registers Layout independently and Widget.close() does not
        # close it. MolSysView owns its widget layout, so release it as well.
        close_layout = getattr(layout, "close", None)
        if layout is not widget and callable(close_layout):
            close_layout()

    @signal(tags=["viewer", "init"])
    @dep_digest('anywidget')
    @dep_digest('molsysmt')
    def __init__(
        self,
        *,
        debug_js: bool | None = None,
        viewer_mode: str | None = None,
        controls_mode: str | None = None,
        panel_mode_style: str | None = None,
        height: str = "480px",
        transport: Any = None,
    ) -> None:
        # `transport` lets a non-Jupyter host (e.g. the standalone Qt shell) inject
        # its own widget-like channel (see standalone_qt.QtViewChannel). It must
        # implement the small surface the view uses: send/on_msg, config attrs and
        # a `layout`. Defaults to the AnyWidget for Jupyter.
        self.widget = transport if transport is not None else MolSysViewerWidget()
        if isinstance(self.widget, MolSysViewerWidget):
            self.widget._molsysviewer_view_ref = weakref.ref(self)
        self._debug_js = bool(debug_js) if debug_js is not None else False
        self.widget.debug_js = self._debug_js
        self._js_logs: list[dict[str, str]] = []
        try:
            self.widget.show_controls = bool(config.show_controls)
        except Exception:
            # If config is missing or misconfigured, fall back to defaults.
            self.widget.show_controls = True

        self.widget.layout.width = "100%"
        self.widget.layout.height = height
        self.widget.layout.min_height = "300px"

        self._already_shown = False

        self._ready = False
        self._frontend_capabilities: dict[str, Any] = {}
        self._binary_viewer_id = f"view-{uuid.uuid4()}"
        self._binary_session_id = f"session-{uuid.uuid4()}"
        # R1 envelope authority: only the AnyWidget connector uses envelopes; Qt and
        # other transports keep raw messages (see _send_widget_message / _handle_msg).
        self._runtime_router: WidgetRuntimeRouter | None = None
        if isinstance(self.widget, MolSysViewerWidget):
            self.widget.runtime_viewer_id = self._binary_viewer_id
            self.widget.runtime_session_id = self._binary_session_id
            self._runtime_router = WidgetRuntimeRouter(
                self._binary_viewer_id, self._binary_session_id
            )
        # D3 backpressure: a frontend that never acknowledges must not pin the
        # retained float32 arrays forever. The deadline is checked on main-thread
        # entry points only (never from a timer thread, which would make
        # `widget.send` unsafe for AnyWidget). Generous by default so a slow
        # connection is not mistaken for a dead one.
        self._monotonic = time.monotonic
        self._structure_transfers = StructureTransferManager(
            self._binary_viewer_id,
            self._binary_session_id,
            timeout_s=30.0,
            monotonic=lambda: self._monotonic(),
        )
        # Scene messages waiting for the structure they describe. Streaming the
        # molecular payload made its delivery asynchronous, so "handed to the
        # transport" stopped meaning "applied in the browser"; see
        # `_send_widget_message`.
        self._deferred_widget_messages: list[tuple[Mapping[str, Any], Any]] = []
        self._flushing_deferred_widget_messages = False
        self._message_history: list[dict] = []
        # The current molecular projection ("current molecular state"), updated
        # on every load/rebuild. Its portable JSON body may remain lazy until a
        # compatibility/export consumer asks for it. R2 references this instead
        # of scanning _message_history for the last load.
        self._current_molecular_projection: dict | None = None
        self._molecular_projection_revision = 0
        self._last_camera_snapshot: dict | None = None
        self._current_figure_spec: dict | None = None
        self._last_image_export_event: dict | None = None
        self._movie_export_frames: list | None = None
        self._movie_export_done: bool = False
        self._last_hover_event: dict | None = None
        self._last_click_event: dict | None = None
        self._last_context_event: dict | None = None
        self._last_context_action_event: dict | None = None
        self._hover_callbacks: list = []
        self._click_callbacks: list = []
        self._context_callbacks: list = []
        self._frame_change_callbacks: list = []
        self._last_active_selection_event: dict | None = None
        self._active_selection_recipe: list[dict[str, Any]] = []
        self._last_tool_state_event: dict | None = None
        self._webgl_context_lost: bool = False
        # Visibility wire protocol: the frontend keeps a versioned visible-atom set
        # and we send small deltas live; the full state is always recorded for
        # replay. `_last_visibility_mask` is the last mask we computed a delta
        # against; `_visibility_version` is the monotonic version both sides track.
        self._last_visibility_mask = None
        self._visibility_version: int = 0
        self._last_measurement_created_event: dict | None = None
        self._last_panel_mode_state_event: dict | None = None
        self._shape_render_status: dict[str, dict] = {}
        self._shape_history: list[dict] = []
        self._annotation_history: list[dict] = []
        self._measurement_history: list[dict] = []
        self._section_history: list[dict] = []
        self._selection_history: list[dict] = []
        self._scene_owner_stack: list[str] = []
        self._scene_look: dict[str, dict] = {}
        self._player_state: dict[str, Any] = {}
        self._last_label: str | None = None
        self._empty = True
        self._load_blocks: list[dict[str, Any]] = []
        self._current_structure_index: int = 0
        self._atom_index_mapper = None
        self._structure_index_mapper = None
        self._rendered_transactions_acks: set = set()
        self._last_rendered_transaction: str | int | None = None

        self._regions: RegionsManager = RegionsManager(self)
        self._region_batch_depth = 0
        self._region_batch_operations: list[dict[str, Any]] = []
        self._region_batch_summary_dirty = False
        self._dynamic_region_cache: OrderedDict[tuple[str, int], tuple[int, ...]] = OrderedDict()
        self._dynamic_region_cache_limit: int = 512
        self._dynamic_region_evaluation_budget_ms: float = 25.0
        self._layers: LayersManager = LayersManager(self)
        self._scene_objects: Dict[tuple[str, str], SceneObject] = {}
        self._selections: Dict[str, Selection] = {}
        self._tag_managers = {
            "region": TagsManager("region", "region", lambda: self._regions.keys()),
            "shape": TagsManager(
                "shape",
                "shape",
                lambda: (
                    tag for kind, tag in self._scene_objects if kind == "shape"
                ),
            ),
            "annotation": TagsManager(
                "annotation",
                "annotation",
                lambda: (
                    tag for kind, tag in self._scene_objects if kind == "annotation"
                ),
            ),
            "measurement": TagsManager(
                "measurement",
                "measurement",
                lambda: (
                    tag for kind, tag in self._scene_objects if kind == "measurement"
                ),
            ),
            "section": TagsManager(
                "section",
                "section",
                lambda: (
                    tag for kind, tag in self._scene_objects if kind == "section"
                ),
            ),
            "layer": TagsManager("layer", "layer", lambda: self._layers.keys()),
            "selection": TagsManager("selection", "selection", lambda: self._selections.keys()),
        }
        self._region_uid_counter = 0
        self._global_hidden = False
        self._box_visible = False
        self._box_record: dict | None = None  # params last passed to show_box
        self._atom_color_layers: dict[str, dict[int, int]] = {"whole": {}}
        self._atom_color_map: dict[int, int] = {}  # resolved atomIndex → 0xRRGGBB
        self._region_order_counter: int = 0
        self._active_panel_widget: tuple[str, str, AddonPanelWidget] | None = None

        self.whole = Whole(self)
        self.styles = StylesManager(self)
        self.colors = global_colors
        self.addons = ViewAddonsManager(self, global_addons)
        self.addons.bind_runtime()
        self.export = ExportManager(self)
        self.hover_target = InteractionTarget(
            self,
            event_getter_name="get_last_hover_event",
            empty_event_name="interaction_hover",
        )
        self.context_target = InteractionTarget(
            self,
            event_getter_name="get_last_context_event",
            empty_event_name="interaction_context_menu",
        )

        # Register callback for JS->Python messages
        def _handle_msg(widget, content, buffers):  # type: ignore[override]
            self._handle_inbound_message(content)

        self._widget_message_callback = _handle_msg
        self.widget.on_msg(self._widget_message_callback)

        self.molecular_system = None
        self.selection = None
        self.structure_indices = None
        self._molsys = None
        self.atom_mask = None
        self.structure_mask = None

        self.shapes = ShapesManager(self)
        self.annotations = AnnotationsManager(self)
        self.active_selection = ActiveSelection(self)
        self.measurements = MeasurementsManager(self)
        self.selections = SelectionsManager(self)
        self.history = SceneHistory(self)
        self.scene = SceneManager(self)
        self.player = PlayerManager(self)
        self.trajectory_plot = TrajectoryPlotManager(self)
        self.camera = CameraManager(self)
        self.movie = MovieManager(self)
        try:
            self.widget.autohide_controls = bool(config.autohide_controls)
        except Exception:
            self.widget.autohide_controls = False

        try:
            pos = list(config.controls_position)
            self.widget.controls_position = pos
        except Exception:
            self.widget.controls_position = ["top", "right"]

        try:
            pos_fs = list(config.controls_position_fullscreen)
            self.widget.controls_position_fullscreen = pos_fs
        except Exception:
            self.widget.controls_position_fullscreen = ["bottom", "right"]

        # Apply viewer_mode, controls_mode, and panel_mode_style presets
        self._apply_view_modes(viewer_mode=viewer_mode, controls_mode=controls_mode, panel_mode_style=panel_mode_style)

    @contextmanager
    def attributed_to(self, owner: str):
        """Attribute scene objects created in this context to *owner*.

        Attribution is informational only. It never changes what the user may
        rename, move, hide, or delete from the scene.
        """
        if not isinstance(owner, str):
            raise TypeError("Scene object owner must be a string.")
        normalized = owner.strip()
        if not normalized:
            raise ValueError("Scene object owner must be a non-empty string.")
        self._scene_owner_stack.append(normalized)
        try:
            yield self
        finally:
            self._scene_owner_stack.pop()

    def _current_scene_owner(self) -> str | None:
        return self._scene_owner_stack[-1] if self._scene_owner_stack else None

    def _apply_view_modes(self, viewer_mode: str | None = None, controls_mode: str | None = None, panel_mode_style: str | None = None) -> None:

        # Resolve viewer_mode, controls_mode, and panel_mode_style presets.
        # viewer_mode is intentionally limited to three high-level presets. The
        # ambient/split layouts that older presets exposed are still reachable
        # at runtime through panel_mode_style and the floating panel lock/dock
        # buttons; they are fused into "integrated", not separate viewer modes.
        presets = {
            "classic": ("classic", "drawer"),
            "integrated": ("minimal", "integrated"),
            "cinema": ("cinema", "integrated"),
        }

        # Retrieve values from config, falling back to defaults if not present
        cfg_viewer_mode = getattr(config, "viewer_mode", "classic")
        cfg_controls_mode = getattr(config, "controls_mode", "classic")
        cfg_panel_mode_style = getattr(config, "panel_mode_style", "drawer")

        # 1. Resolve viewer_mode. An explicitly requested viewer_mode is validated
        # strictly (removed presets raise instead of silently coercing); a stale or
        # unknown config value falls back to "classic" defensively.
        if viewer_mode is not None:
            viewer_mode = digest_viewer_mode(viewer_mode)
        v_mode = viewer_mode if viewer_mode is not None else cfg_viewer_mode
        if v_mode not in presets:
            v_mode = "classic"

        preset_controls, preset_panel = presets[v_mode]

        # 2. Resolve controls_mode (explicit constructor/method arg > customized config > preset default)
        if controls_mode is not None:
            c_mode = controls_mode
        elif viewer_mode is not None:
            c_mode = preset_controls
        else:
            if cfg_controls_mode != "classic":
                c_mode = cfg_controls_mode
            else:
                c_mode = preset_controls

        c_mode_valid = c_mode if c_mode in ("classic", "minimal", "cinema") else "classic"

        # 3. Resolve panel_mode_style (explicit constructor/method arg > customized config > preset default)
        if panel_mode_style is not None:
            p_style = panel_mode_style
        elif viewer_mode is not None:
            p_style = preset_panel
        else:
            if cfg_panel_mode_style != "drawer":
                p_style = cfg_panel_mode_style
            else:
                p_style = preset_panel

        p_style_valid = p_style if p_style in ("drawer", "floating", "floating-unified", "integrated", "ambient", "split") else "drawer"

        # Set traits on widget
        self.widget.viewer_mode = v_mode
        self.widget.controls_mode = c_mode_valid
        self.widget.panel_mode_style = p_style_valid

    def set_dimensions(self, width: str | None = None, height: str | None = None) -> None:
        """Set the dimensions of the viewer widget.

        Parameters
        ----------
        width : str, optional
            The CSS width of the widget (e.g., '100%', '800px').
        height : str, optional
            The CSS height of the widget (e.g., '600px', '80%').
        """
        if width is not None:
            self.widget.layout.width = width
        if height is not None:
            self.widget.layout.height = height

    def set_canvas_visibility(self, visible: bool) -> None:
        """Set the visibility of the WebGL canvas.

        Parameters
        ----------
        visible : bool
            True to show the canvas, False to hide it.
        """
        self._send_to_frontend({"op": "set_canvas_visibility", "visible": bool(visible)})

    def _send_backend_error_ack(self, content: Mapping[str, Any], exc: Exception) -> None:
        event = content.get("event")
        action = content.get("action")
        error_payload = {
            "op": "backend_error_occurred",
            "trigger_event": event,
            "action": action,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }
        try:
            emit_from_catalog(
                CATALOG["frontend_action_failed"],
                package_root=PACKAGE_ROOT,
                meta=META,
                extra=context_extra(
                    caller="molsysviewer.viewer._handle_frontend_event",
                    operation="frontend-interaction-action",
                    failure_class="frontend_backend_desync",
                    last_failure_reason=str(exc),
                    cause_exception_type=type(exc).__name__,
                    incident_kind="frontend_action_failed",
                    severity="error",
                    priority="normal",
                    diagnostic_confidence="high",
                    recommended_action="surface-error-to-user-and-preserve-python-state",
                    next_step="inspect-backend_error_occurred-payload",
                    retryable=False,
                    support_needed=False,
                    evidence={
                        "event": event,
                        "action": action,
                        "tag": content.get("tag"),
                        "payload_keys": sorted(str(key) for key in content.keys()),
                    },
                    extra={
                        "event": event,
                        "action": action,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                ),
            )
        except Exception as smonitor_exc:
            warnings.warn(
                "SMonitor failed while reporting frontend action error "
                f"{type(exc).__name__}: {exc!s}; SMonitor error: "
                f"{type(smonitor_exc).__name__}: {smonitor_exc!s}",
                RuntimeWarning,
                stacklevel=2,
            )
        self._send_runtime_only(error_payload)

    def _parse_selection_query_indices(self, expression: Any, syntax: str) -> list[int]:
        if self._molsys is None:
            raise ValueError("No molecular system loaded.")
        if syntax == "Indices":
            if isinstance(expression, str):
                text = expression.strip()
                if not text:
                    return []
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = [part.strip() for part in re.split(r"[\s,]+", text) if part.strip()]
            else:
                parsed = expression
            if isinstance(parsed, (int, np.integer)):
                return [int(parsed)]
            if not isinstance(parsed, (list, tuple, range, np.ndarray)):
                raise ValueError("Indices syntax requires a list of atom indices.")
            try:
                return [int(item) for item in parsed]
            except (TypeError, ValueError) as exc:
                raise ValueError("Indices syntax requires integer atom indices.") from exc

        selection = expression
        if not isinstance(selection, str) or selection.strip() == "":
            raise ValueError("Selection query requires a non-empty expression.")
        return [
            int(item)
            for item in self.select(
                selection=selection.strip(),
                syntax=syntax,
                element="atom",
                skip_digestion=True,
            )
        ]

    @staticmethod
    def _copy_selection_recipe(recipe: Any) -> list[dict[str, Any]]:
        if not isinstance(recipe, list):
            return []
        return [dict(step) for step in recipe if isinstance(step, Mapping)]

    def _selection_recipe_step(
        self,
        *,
        source: str,
        op: str,
        atom_indices: Any,
        expression: Any | None = None,
        syntax: str | None = None,
        element: str | None = "atom",
    ) -> dict[str, Any]:
        step: dict[str, Any] = {
            "source": source,
            "op": op,
            "atom_indices": [int(item) for item in (atom_indices or [])],
        }
        if expression is not None:
            step["expression"] = expression
        if syntax is not None:
            step["syntax"] = syntax
        if element is not None:
            step["element"] = element
        return step

    def _set_active_selection_recipe(self, recipe: Any) -> None:
        self._active_selection_recipe = self._copy_selection_recipe(recipe)

    def _selection_recipe_after_step(
        self,
        previous_recipe: Any,
        step: dict[str, Any],
        op: str,
    ) -> list[dict[str, Any]]:
        if op == "replace":
            return [dict(step)]
        recipe = self._copy_selection_recipe(previous_recipe)
        recipe.append(dict(step))
        return recipe

    def _resolve_selection_recipe_step(
        self,
        step: Mapping[str, Any],
        atom_index_map: dict[int, int] | None,
    ) -> tuple[dict[str, Any] | None, list[int]]:
        updated = dict(step)
        source = str(updated.get("source") or "indices")
        if source == "query" and updated.get("expression") is not None:
            try:
                resolved = self._parse_selection_query_indices(
                    updated.get("expression"),
                    str(updated.get("syntax") or "MolSysMT"),
                )
            except Exception:
                raw_indices = updated.get("atom_indices")
                if atom_index_map is None or not isinstance(raw_indices, list):
                    raise
                resolved = self._remap_indices(raw_indices, atom_index_map)
        else:
            raw_indices = updated.get("atom_indices")
            if not isinstance(raw_indices, list):
                resolved = []
            elif atom_index_map is None:
                resolved = [int(item) for item in raw_indices]
            else:
                resolved = self._remap_indices(raw_indices, atom_index_map)

        if not resolved and source != "query":
            return None, []
        updated["atom_indices"] = list(resolved)
        return updated, list(resolved)

    def _replay_selection_recipe(
        self,
        recipe: Any,
        atom_index_map: dict[int, int] | None,
    ) -> tuple[list[dict[str, Any]], list[int]]:
        replayed_recipe: list[dict[str, Any]] = []
        result: list[int] = []
        for raw_step in self._copy_selection_recipe(recipe):
            step, incoming = self._resolve_selection_recipe_step(raw_step, atom_index_map)
            if step is None:
                continue
            op = str(step.get("op") or "replace")
            if op == "invert":
                n_atoms = int(self._molsys.get_n_atoms()) if self._molsys is not None else 0
                result = _combine(result, [], "invert", universe=range(n_atoms))
            elif op in {"replace", "add", "subtract", "intersect"}:
                result = _combine(result, incoming, op)  # type: ignore[arg-type]
            else:
                result = _combine(result, incoming, "replace")
                step["op"] = "replace"
            replayed_recipe.append(step)
        return replayed_recipe, result

    def _apply_selection_query_action(self, content: Mapping[str, Any]) -> None:
        expression = content.get("expression")
        syntax = str(content.get("syntax") or "MolSysMT")
        op = str(content.get("op") or "replace")
        if op not in {"replace", "add", "subtract", "intersect"}:
            raise ValueError(f"Unsupported selection query operation: {op!r}.")
        incoming = self._parse_selection_query_indices(expression, syntax)
        previous_recipe = self._copy_selection_recipe(self._active_selection_recipe)
        result = _combine(self.active_selection.atom_indices, incoming, op)  # type: ignore[arg-type]
        source = "indices" if syntax == "Indices" else "query"
        step = self._selection_recipe_step(
            source=source,
            op=op,
            atom_indices=incoming,
            expression=expression if source == "query" else None,
            syntax=syntax,
            element="atom",
        )
        next_recipe = self._selection_recipe_after_step(previous_recipe, step, op)
        self.active_selection.set(result, skip_digestion=True)
        self._set_active_selection_recipe(next_recipe)

    def _apply_active_selection_operation(self, operation: str) -> None:
        if self._molsys is None:
            raise ValueError("No molecular system loaded.")
        n_atoms = int(self._molsys.get_n_atoms())
        previous_recipe = self._copy_selection_recipe(self._active_selection_recipe)
        if operation == "all":
            result = list(range(n_atoms))
            step = self._selection_recipe_step(
                source="indices",
                op="replace",
                atom_indices=result,
                syntax="Indices",
            )
            next_recipe = [step]
        elif operation == "none":
            result = []
            next_recipe = []
        elif operation == "invert":
            result = _combine(
                self.active_selection.atom_indices,
                [],
                "invert",
                universe=range(n_atoms),
            )
            step = self._selection_recipe_step(
                source="indices",
                op="invert",
                atom_indices=[],
                syntax="Indices",
            )
            next_recipe = self._selection_recipe_after_step(previous_recipe, step, "invert")
        else:
            raise ValueError(f"Unsupported active selection operation: {operation!r}.")
        self.active_selection.set(result, skip_digestion=True)
        self._set_active_selection_recipe(next_recipe)

    def _preview_selection_query_action(self, content: Mapping[str, Any]) -> None:
        request_id = content.get("request_id")
        try:
            expression = content.get("expression")
            syntax = str(content.get("syntax") or "MolSysMT")
            atom_indices = self._parse_selection_query_indices(expression, syntax)
            payload = {
                "op": "selection_query_preview",
                "request_id": request_id,
                "ok": True,
                "count": len(atom_indices),
            }
        except Exception as exc:
            payload = {
                "op": "selection_query_preview",
                "request_id": request_id,
                "ok": False,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        self._send_runtime_only(payload)

    def _active_selection_query_system(self) -> tuple[Any, list[int]]:
        atom_indices = list(self.active_selection.atom_indices)
        if len(atom_indices) == 0:
            raise ValueError("expand_selection requires a non-empty active selection.")
        if self._molsys is None:
            raise ValueError("No molecular system loaded.")
        return self._molsys, atom_indices

    @staticmethod
    def _flatten_atom_index_result(values: Any) -> list[int]:
        out: list[int] = []

        def visit(item: Any) -> None:
            if item is None:
                return
            if isinstance(item, (list, tuple, range, np.ndarray)):
                for subitem in item:
                    visit(subitem)
                return
            out.append(int(item))

        visit(values)
        return out

    def _expand_selection_action(self, content: Mapping[str, Any]) -> None:
        level = str(content.get("level") or "").strip().lower()
        if level == "spatial":
            self._expand_selection_spatial_action(content)
            return
        if level not in {"group", "component", "molecule", "chain", "entity"}:
            raise ValueError(f"Unsupported selection expansion level: {level!r}.")

        query_system, query_atoms = self._active_selection_query_system()
        if len(query_atoms) == 0:
            raise ValueError("expand_selection has no active atoms available in the loaded system.")

        level_indices = msm.get(
            query_system,
            element="atom",
            selection=query_atoms,
            **{f"{level}_index": True},
            output_type="values",
            skip_digestion=True,
        )
        deduped_level_indices = sorted({int(item) for item in level_indices if item is not None})
        if len(deduped_level_indices) == 0:
            self.active_selection.clear(skip_digestion=True)
            return

        atom_index_result = msm.get(
            query_system,
            element=level,
            selection=deduped_level_indices,
            atom_index=True,
            skip_digestion=True,
        )
        expanded_atoms = self._flatten_atom_index_result(atom_index_result)
        self.active_selection.set(sorted(set(expanded_atoms)), skip_digestion=True)

    def _expand_selection_spatial_action(self, content: Mapping[str, Any]) -> None:
        current_atoms = list(self.active_selection.atom_indices)
        if len(current_atoms) == 0:
            raise ValueError("spatial expand_selection requires a non-empty active selection.")
        try:
            distance = float(content.get("distance_angstroms"))
        except (TypeError, ValueError) as exc:
            raise ValueError("spatial expand_selection requires a numeric distance_angstroms value.") from exc
        if distance <= 0:
            raise ValueError("spatial expand_selection requires distance_angstroms > 0.")

        n_atoms = int(self._molsys.get_n_atoms()) if self._molsys is not None else 0
        all_atoms = list(range(n_atoms))
        contact_map = msm.structure.get_contacts(
            self._molsys,
            selection=all_atoms,
            selection_2=current_atoms,
            threshold=f"{distance:g} angstroms",
            pbc=False,
        )
        expanded_atoms = np.asarray(all_atoms)[np.where(contact_map.any(axis=2)[0])[0]].tolist()
        self.active_selection.set(expanded_atoms, skip_digestion=True)

    def _binary_structure_transport_limit(self) -> int | None:
        versions = self._frontend_capabilities.get("binary_structure_data")
        if (
            not isinstance(self.widget, MolSysViewerWidget)
            or not isinstance(versions, (list, tuple))
            or ARRAY_NATIVE_PROTOCOL_VERSION not in versions
        ):
            return None
        max_buffer_bytes = self._frontend_capabilities.get("max_buffer_bytes")
        if (
            not isinstance(max_buffer_bytes, int)
            or isinstance(max_buffer_bytes, bool)
            or max_buffer_bytes <= 0
        ):
            return None
        return max_buffer_bytes

    def _new_lazy_molecular_projection(
        self,
        *,
        label: str | None,
    ) -> LazyMolecularMessage:
        if self._molsys is None:
            raise ValueError("No molecular system is available for projection.")
        self._molecular_projection_revision += 1
        revision = self._molecular_projection_revision
        molsys = self._molsys
        return LazyMolecularMessage(
            label=label,
            multiple_structures=int(molsys.structures.n_structures) > 1,
            molecular_revision=revision,
            current_revision=lambda: self._molecular_projection_revision,
            builder=lambda: build_json_molsys_message(molsys, label=label),
        )

    def _materialize_molecular_projection(
        self,
        message: Mapping[str, Any],
        *,
        transfer_generation: int | None = None,
    ) -> dict[str, Any]:
        if is_lazy_molecular_message(message):
            return message.materialize(transfer_generation=transfer_generation)
        return dict(message)

    def _try_send_array_native_molsys(
        self,
        message: Mapping[str, Any],
        target_endpoint_id: str | None = None,
    ) -> bool:
        """Stream the current MolSys as typed buffers.

        With ``target_endpoint_id`` the stream is addressed to a popup endpoint:
        the widget host relays each chunk to that popup instead of consuming it,
        so no endpoint keeps a spare full copy of the coordinates. Only one
        stream is in flight at a time, matching the one-chunk-in-flight rule.
        """
        # Main-thread entry point: a stalled previous stream is released here.
        self._check_binary_structure_ack_timeout()
        if message.get("op") != "load_molsys_payload" or self._molsys is None:
            return False
        max_buffer_bytes = self._binary_structure_transport_limit()
        if max_buffer_bytes is None:
            return False

        transfer: StructureTransfer | None = None
        try:
            payload = serialize_array_native_molsys(self._molsys)
            metadata = payload.metadata
            n_structures = int(metadata["n_structures"])
            bytes_per_structure = max(
                int(array.nbytes // n_structures) for array in payload.arrays
            )
            structures_per_chunk = max_buffer_bytes // bytes_per_structure
            if structures_per_chunk < 1:
                return False
            chunks: list[tuple[dict[str, Any], list[memoryview]]] = []
            for chunk_id, structure_start in enumerate(
                range(0, n_structures, structures_per_chunk)
            ):
                structure_count = min(
                    structures_per_chunk,
                    n_structures - structure_start,
                )
                arrays = tuple(
                    array[structure_start:structure_start + structure_count]
                    for array in payload.arrays
                )
                descriptors: list[dict[str, Any]] = []
                for buffer_index, (array, complete_descriptor) in enumerate(
                    zip(arrays, metadata["structural_arrays"], strict=True)
                ):
                    descriptor = dict(complete_descriptor)
                    descriptor["shape"] = [
                        structure_count,
                        *complete_descriptor["shape"][1:],
                    ]
                    descriptor["buffer_index"] = buffer_index
                    descriptor["byte_length"] = array.nbytes
                    descriptors.append(descriptor)
                chunk_message: dict[str, Any] = {
                    "op": "structure_data_chunk",
                    "protocol_version": ARRAY_NATIVE_PROTOCOL_VERSION,
                    "chunk_id": chunk_id,
                    "structure_start": structure_start,
                    "structure_count": structure_count,
                    "structural_arrays": descriptors,
                }
                chunks.append((
                    chunk_message,
                    [memoryview(array).cast("B") for array in arrays],
                ))

            begin = {
                "op": "structure_data_begin",
                "protocol_version": ARRAY_NATIVE_PROTOCOL_VERSION,
                "chunk_count": len(chunks),
                "metadata": metadata,
                "label": message.get("label"),
                "multiple_structures": bool(message.get("multiple_structures")),
            }
            self._cancel_binary_structure_stream("replaced by newer generation")
            transfer = self._structure_transfers.start(
                begin_message=begin,
                chunks=chunks,
                fallback_factory=lambda generation: self._materialize_molecular_projection(
                    message,
                    transfer_generation=generation,
                ),
                # Keep the parent ndarrays alive while chunk memoryviews are in flight.
                payload=payload,
                target_endpoint_id=target_endpoint_id,
            )
            self._transmit_widget_message(transfer.begin_message)
            return True
        except Exception as exc:
            if transfer is not None:
                self._structure_transfers.fallback(
                    f"connector failed while starting structure transfer: {exc}"
                )
            warnings.warn(
                f"Array-native AnyWidget delivery failed; using JSON fallback: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            return False

    def _check_binary_structure_ack_timeout(self) -> None:
        """Release a stream whose acknowledgement never arrived.

        Called from main-thread entry points only. There is deliberately no timer
        thread: `widget.send` is not safe to call off the kernel thread for
        AnyWidget, so the deadline is evaluated when the kernel next does work.
        """
        termination = self._structure_transfers.expire_if_due()
        if termination is not None:
            self._deliver_binary_structure_fallback(termination)

    def _cancel_binary_structure_stream(self, reason: str) -> None:
        termination = self._structure_transfers.cancel(reason)
        if termination is None:
            return
        self._transmit_binary_structure_cancel(
            termination.transfer,
            reason,
            caller="MolSysView._cancel_binary_structure_stream",
        )

    def _transmit_binary_structure_cancel(
        self,
        transfer: StructureTransfer,
        reason: str,
        *,
        caller: str,
    ) -> None:
        """Tell the exact receiver to discard a released stream generation."""
        try:
            cancel: dict[str, Any] = {
                "op": "structure_data_cancel",
                "viewer_id": transfer.viewer_id,
                "session_id": transfer.session_id,
                "stream_id": transfer.stream_id,
                "generation": transfer.generation,
                "reason": reason,
            }
            if transfer.target_endpoint_id is not None:
                cancel["target_endpoint_id"] = transfer.target_endpoint_id
            # Not `_send_widget_message`: a cancel that flushed would release the
            # deferred scene ahead of the replacement generation this cancel is
            # making room for. They stay deferred and ride behind the new stream.
            self._transmit_widget_message(cancel)
        except Exception as exc:
            emit_suppressed_exception(
                caller,
                exc,
                context={
                    "generation": transfer.generation,
                    "target_endpoint_id": transfer.target_endpoint_id,
                    "reason": reason,
                },
            )

    def _transmit_binary_structure_chunk(self, chunk: TransferChunk) -> None:
        try:
            self._transmit_widget_message(chunk.message, buffers=chunk.buffers)
        except Exception as exc:
            self._fallback_binary_structure_stream(
                f"connector failed while sending chunk {chunk.message['chunk_id']}: {exc}"
            )

    def _fallback_binary_structure_stream(self, reason: str) -> None:
        termination = self._structure_transfers.fallback(reason)
        if termination is None:
            return
        self._deliver_binary_structure_fallback(termination)

    def _deliver_binary_structure_fallback(
        self,
        termination: TransferTermination,
    ) -> None:
        transfer = termination.transfer
        reason = termination.reason
        # Tell the receiver to drop its half too; a frontend that is merely slow
        # (rather than gone) must not apply a generation Python has abandoned.
        self._transmit_binary_structure_cancel(
            transfer,
            reason,
            caller="MolSysView._fallback_binary_structure_stream.cancel",
        )
        # Materialize only after the abandoned receiver has been cancelled. If
        # the molecular revision changed unexpectedly, the lazy projection
        # raises instead of sending coordinates from a different generation.
        fallback = transfer.materialize_fallback()
        emit_from_catalog(
            CATALOG["structure_data_stream_fallback"],
            package_root=PACKAGE_ROOT,
            meta=META,
            extra=context_extra(
                caller="molsysviewer.viewer._fallback_binary_structure_stream",
                operation="array-native-structure-stream",
                failure_class="stream_fallback_to_json",
                last_failure_reason=reason,
            ),
        )
        warnings.warn(
            f"Array-native stream failed; using JSON fallback: {reason}",
            RuntimeWarning,
            stacklevel=2,
        )
        target_endpoint_id = transfer.target_endpoint_id
        if target_endpoint_id is not None:
            # A popup-targeted stream must not fall back into the host, which
            # already holds this structure; the JSON load carries the target so
            # the host relays it to the popup that was waiting for it.
            fallback = {**fallback, "target_endpoint_id": target_endpoint_id}
        # `_send_widget_message`, so the JSON load goes out first and its
        # post-transmit flush releases the scene behind it — the same ordering
        # the binary path gets from `structure_data_complete`.
        self._send_widget_message(fallback)

    def _handle_binary_structure_event(self, content: Mapping[str, Any]) -> None:
        # An acknowledgement that arrives after the deadline belongs to a stream
        # Python has already given up on; release it before looking at the event.
        self._check_binary_structure_ack_timeout()
        result = self._structure_transfers.handle_event(content)
        if result.disposition is AckDisposition.FOREIGN:
            warnings.warn(
                "Ignored array-native acknowledgement for another endpoint or generation.",
                RuntimeWarning,
                stacklevel=2,
            )
            return
        if result.disposition is AckDisposition.SEND_CHUNK:
            if result.chunk is None:
                raise RuntimeError("transfer manager requested a missing chunk")
            self._transmit_binary_structure_chunk(result.chunk)
        elif result.disposition is AckDisposition.COMPLETED:
            # The frontend builds the structure and *then* reports complete,
            # so this is the first moment a scene message can land on
            # something to draw on.
            self._flush_deferred_widget_messages()
        elif result.disposition is AckDisposition.FALLBACK:
            if result.termination is None:
                raise RuntimeError("transfer manager returned fallback without termination")
            self._deliver_binary_structure_fallback(result.termination)

    def _send_widget_message(self, message: Mapping[str, Any], buffers: Any = None) -> None:
        """Single outbound chokepoint for scene messages.

        Every live send from ``MolSysView`` funnels through here with the domain
        message, and everything sent here is **ordered behind the structure it
        describes**.

        That ordering used to be free. On the JSON path the frontend applies
        ``load_molsys_payload`` to completion before it takes the next message off
        its queue, so a scene op could never overtake its structure. The
        array-native data plane broke that guarantee without anyone noticing:
        `_try_send_array_native_molsys` returns as soon as ``structure_data_begin``
        is on the wire, and the structure is only built in the browser several
        ack round-trips later, when the last chunk lands. Everything sent in
        between arrives at a frontend with no structure — and the handlers that
        need one (`addMeasurement`, the annotation and region handlers) return
        silently rather than fail. A measurement or a label created from Python
        before the widget was displayed was simply never drawn.

        So while a generation is in flight, scene messages wait here and are
        flushed once the frontend confirms the structure is applied. Transport,
        bootstrap and request/response traffic must not wait — it either drives
        the handshake or is blocking a caller — and calls
        ``_transmit_widget_message`` directly. That is the whole rule: the escape
        hatch is a different method, not a list of exempt op names that would
        drift out of date the moment a new one appeared.
        """
        if self._structure_transfers.has_active:
            self._deferred_widget_messages.append((message, buffers))
            return
        self._transmit_widget_message(message, buffers)
        # Drains a backlog that outlived its stream even if some exit path forgot
        # to flush, so a lost flush degrades to a late delivery, never a lost one.
        self._flush_deferred_widget_messages()

    def _transmit_widget_message(self, message: Mapping[str, Any], buffers: Any = None) -> None:
        """Hand a message to the connector, bypassing the structure-stream gate.

        The connector owns its wire format: ``MolSysViewerWidget.send`` wraps
        control-plane messages in a RuntimeEnvelope (R1), while Qt and other
        transports keep raw messages. ``raw``/``data_plane`` messages and their
        buffers pass through unwrapped, and ``_message_history`` / the
        ``initial_messages`` trait keep domain messages because wrapping happens
        below this chokepoint, at the widget.
        """
        if buffers is None:
            self.widget.send(message)
        else:
            self.widget.send(message, buffers=buffers)

    def _flush_deferred_widget_messages(self) -> None:
        """Send what waited for the structure, in the order it was produced."""
        if self._flushing_deferred_widget_messages:
            return
        self._flushing_deferred_widget_messages = True
        try:
            while self._deferred_widget_messages:
                if self._structure_transfers.has_active:
                    # A newer generation started mid-flush; the rest waits for it
                    # rather than overtaking the structure it is about to replace.
                    break
                message, buffers = self._deferred_widget_messages.pop(0)
                self._transmit_widget_message(message, buffers)
        finally:
            self._flushing_deferred_widget_messages = False

    def _handle_inbound_message(self, content: Any) -> None:
        """Validate + unwrap an inbound envelope, or pass raw messages through.

        Raw bootstrap/data-plane messages and non-AnyWidget connectors go straight
        to ``_handle_frontend_event``. Enveloped control messages are validated and
        deduplicated by the authority router: a duplicate command is acknowledged
        without re-applying it; a rejected envelope is diagnosed and dropped.
        """
        # Main-thread entry point for anything the frontend sends: a stream whose
        # acknowledgement never arrived is released here even if the frontend has
        # moved on to unrelated traffic.
        self._check_binary_structure_ack_timeout()
        if self._runtime_router is None or not is_envelope(content):
            self._handle_frontend_event(content)
            return
        result = self._runtime_router.route_inbound(content)
        if result.status == "accepted":
            # Transport-level request: it needs the envelope to correlate its
            # answer, so it is served here rather than in the domain handler.
            if result.envelope.action == "request_popup_scene_snapshot":
                self._answer_popup_scene_snapshot(result.envelope)
                return
            self._handle_frontend_event(result.message)
        elif result.status == "duplicate":
            self._transmit_widget_message(self._runtime_router.duplicate_ack(result.envelope))
        else:
            emit_suppressed_exception(
                "MolSysView._handle_inbound_message",
                ValueError(f"{result.reason}: {result.detail}"),
                context={"reason": result.reason},
            )

    def _answer_popup_scene_snapshot(self, request: Any) -> None:
        """Serve `request_popup_scene_snapshot` with the canonical projection.

        The answer is a correlated projection targeted at the widget host, which
        routes it to the popup endpoint that asked. The snapshot is built from
        live state; the host supplies its own ephemeral `endpointState`.
        """
        payload = request.payload if isinstance(request.payload, Mapping) else {}
        mode = payload.get("mode")
        popup_endpoint_id = payload.get("popup_endpoint_id")
        # D4: a canvas popup gets its molecular generation as typed buffers,
        # streamed straight to its endpoint, so neither the host nor Python keeps
        # a spare copy. Only then is the JSON load left out of the snapshot.
        binary_delivered = False
        if (
            mode == "canvas"
            and isinstance(popup_endpoint_id, str)
            and popup_endpoint_id
            and self._current_molecular_projection is not None
        ):
            binary_delivered = self._try_send_array_native_molsys(
                self._current_molecular_projection,
                target_endpoint_id=popup_endpoint_id,
            )
        try:
            messages = self.build_popup_scene_snapshot(
                mode,
                endpoint=popup_endpoint_id,
                include_molecular=not binary_delivered,
            )
        except ValueError as exc:
            emit_suppressed_exception(
                "MolSysView._answer_popup_scene_snapshot",
                exc,
                context={"mode": mode},
            )
            return
        self._send_widget_message(
            self._runtime_router.correlated_projection(
                request,
                action="popup_scene_snapshot",
                payload={
                    "event": "popup_scene_snapshot",
                    "mode": mode,
                    "popup_endpoint_id": popup_endpoint_id,
                    "messages": messages,
                },
            )
        )

    def _deliver_transport_message(self, message: dict[str, Any]) -> None:
        if not self._try_send_array_native_molsys(message):
            self._send_widget_message(self._materialize_molecular_projection(message))

    def _handle_frontend_event(self, content: Mapping[str, Any]) -> None:
        event = content.get("event")
        if event == "widget_resize":
            height = content.get("height")
            width = content.get("width")
            if height is not None:
                self.widget.layout.height = f"{height}px"
            if width is not None:
                self.widget.layout.width = f"{width}px"
            return
        elif event == "ready":
            capabilities = content.get("capabilities")
            self._frontend_capabilities = (
                dict(capabilities) if isinstance(capabilities, Mapping) else {}
            )
            self._ready = True
            for message in list(self._message_history):
                self._deliver_transport_message(message)
            self._sync_region_summaries_runtime()
            self._sync_whole_summary_runtime()
            self._sync_annotation_summaries_runtime()
            self._sync_measurement_summaries_runtime()
            self._sync_shape_summaries_runtime()
            self._sync_layer_summaries_runtime()
            self._sync_section_summaries_runtime()
        elif event in {
            "structure_data_begin_ack",
            "structure_data_chunk_ack",
            "structure_data_complete",
            "structure_data_error",
        }:
            self._handle_binary_structure_event(content)
        elif event == "request_widget_runtime_source":
            # This is the lazy-load bootstrap handshake: the frontend requests the
            # runtime source BEFORE the real runtime has loaded, so `_ready` is
            # necessarily still False here. Send directly (not via
            # `_send_runtime_only`, which drops messages while not ready) — the
            # frontend is listening because it just asked. Gating this on `_ready`
            # deadlocks: `_ready` only becomes True once this source has loaded.
            self._transmit_widget_message({"op": "widget_runtime_source", "source": MolSysViewerWidget._viewer_js_source})
        elif event == "request_popup_source":
            self._transmit_widget_message({"op": "popup_source", "source": MolSysViewerWidget._viewer_js_source})
        elif event == "region_ack":
            tag = content.get("tag")
            if tag and tag in self._regions:
                region = self._regions[tag]
                region._set_atom_indices(content.get("atom_indices") or region.atom_indices)  # noqa: SLF001
                if content.get("selection") is not None:
                    region.selection = content.get("selection")
        elif event == "region_deleted":
            tag = content.get("tag")
            if tag:
                self._unregister_region(tag)
        elif event == "layer_ack":
            tag = content.get("tag")
            # Ignore acks for tags that are already registered as individual scene
            # objects (shapes/annotations/measurements).  Mol* sends a layer_ack
            # for every Mol* node — including one per sphere in a batch — but
            # Python tracks those under _scene_objects, not _layers.
            kind = str(content.get("kind") or "layer")
            if tag and (kind, tag) not in self._scene_objects:
                if tag not in self._layers:
                    layer = Layer(self, tag, kind=content.get("kind"), meta=content.get("meta") or {})
                    self._layers[tag] = layer
                else:
                    layer = self._layers[tag]
                    layer.kind = content.get("kind", layer.kind)
                    if content.get("meta"):
                        layer.meta.update(content.get("meta"))
        elif event == "layer_deleted":
            tag = content.get("tag")
            if tag:
                self._unregister_layer(tag)
        elif event == "registry_cleared":
            pass  # frontend acknowledged clear_all; Python state is managed explicitly
        elif event == "js_log" and self._debug_js:
            level = str(content.get("level", "info")).upper()
            message = content.get("message", "")
            entry = {"level": level, "message": message}
            self._js_logs.append(entry)
            print(f"[JS {level}] {message}")
        elif event == "camera_snapshot":
            snapshot = content.get("snapshot")
            if isinstance(snapshot, dict):
                self._last_camera_snapshot = snapshot
        elif event == "image_export":
            self._last_image_export_event = dict(content)
        elif event == "movie_frame":
            if self._movie_export_frames is not None:
                self._movie_export_frames.append(dict(content))
        elif event == "movie_export_done":
            self._movie_export_done = True
        elif event == "interaction_hover":
            self._last_hover_event = self._enrich_interaction_payload(dict(content))
            for cb in list(self._hover_callbacks):
                cb(self._last_hover_event)
        elif event == "interaction_click":
            self._last_click_event = self._enrich_interaction_payload(dict(content))
            for cb in list(self._click_callbacks):
                cb(self._last_click_event)
        elif event == "interaction_context_menu":
            self._last_context_event = self._enrich_interaction_payload(dict(content))
            for cb in list(self._context_callbacks):
                cb(self._last_context_event)
        elif event == "selection_query_preview_request":
            self._preview_selection_query_action(content)
        elif event == "webgl_context_lost":
            # The browser dropped the WebGL context (GPU crash, sleep/wake, driver
            # reset). Mol* restores the scene from its retained state on recovery;
            # here we only surface a queryable state and a diagnostic signal.
            self._webgl_context_lost = True
            emit_from_catalog(
                CATALOG["webgl_context_lost"],
                package_root=PACKAGE_ROOT,
                meta=META,
            )
        elif event == "webgl_context_restored":
            self._webgl_context_lost = False
            emit_from_catalog(
                CATALOG["webgl_context_restored"],
                package_root=PACKAGE_ROOT,
                meta=META,
            )
        elif event == "request_visibility_resync":
            # The frontend's visibility version drifted from a delta's base version
            # (missed/out-of-order message or a bug); resend the authoritative full
            # state so the delta protocol self-heals.
            self._resend_full_visibility()
        elif event == "scene_history_undo":
            self.history.undo()
            return
        elif event == "scene_history_redo":
            self.history.redo()
            return
        elif event == "scene_history_coalescing_begin":
            self.history.begin_coalescing()
            return
        elif event == "scene_history_coalescing_end":
            self.history.end_coalescing()
            return
        elif event == "interaction_context_action":
            try:
                self._last_context_action_event = dict(content)
                dispatch_panel_action(self, content)
            except Exception as exc:
                self._send_backend_error_ack(content, exc)
                return
        elif event == "section_moved":
            tag = content.get("tag")
            raw_point = content.get("point")
            raw_normal = content.get("normal")
            if isinstance(tag, str) and tag.strip():
                section = self._scene_objects.get(("section", tag.strip()))
                if section is not None:
                    point = [float(v) for v in raw_point] if isinstance(raw_point, (list, tuple)) and len(raw_point) == 3 else None
                    normal = [float(v) for v in raw_normal] if isinstance(raw_normal, (list, tuple)) and len(raw_normal) == 3 else None
                    section.set_geometry(point=point, normal=normal, skip_digestion=True)
        elif event == "interaction_active_selection_changed":
            enriched = dict(content)
            atom_indices = list(content.get("atom_indices") or [])
            enriched["atom_indices"] = list(atom_indices)

            # A user pick is a mutating scene operation, so it is undoable through
            # the one scene history. Checkpoint only on a real change: a selection
            # that Python itself just set (e.g. during an undo/redo replay) echoes
            # back unchanged and must not add a spurious history entry.
            _previous_selection = list(
                (self._last_active_selection_event or {}).get("atom_indices") or []
            )
            _selection_changed = atom_indices != _previous_selection
            if _selection_changed:
                self.history._begin_operation(("active_selection", "", "set"))  # noqa: SLF001

            if self._molsys is not None and len(atom_indices) > 0:
                try:
                    group_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._molsys,
                                    element="atom",
                                    selection=atom_indices,
                                    group_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                    component_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._molsys,
                                    element="atom",
                                    selection=atom_indices,
                                    component_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                    chain_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._molsys,
                                    element="atom",
                                    selection=atom_indices,
                                    chain_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                    molecule_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._molsys,
                                    element="atom",
                                    selection=atom_indices,
                                    molecule_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                    entity_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._molsys,
                                    element="atom",
                                    selection=atom_indices,
                                    entity_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                    enriched["group_indices"] = group_indices
                    enriched["component_indices"] = component_indices
                    enriched["chain_indices"] = chain_indices
                    enriched["molecule_indices"] = molecule_indices
                    enriched["entity_indices"] = entity_indices
                    enriched["count_groups"] = len(group_indices)
                    enriched["count_atoms"] = len(atom_indices)
                except Exception as exc:
                    emit_suppressed_exception(
                        "MolSysView._handle_frontend_event.active_selection_metadata",
                        exc,
                        context={"event": event},
                    )
            else:
                if "count_atoms" in content:
                    enriched["count_atoms"] = len(atom_indices)

            self._last_active_selection_event = enriched
            if atom_indices:
                self._set_active_selection_recipe(
                    [
                        self._selection_recipe_step(
                            source="indices",
                            op="replace",
                            atom_indices=atom_indices,
                            element="atom",
                        )
                    ]
                )
            else:
                self._set_active_selection_recipe([])
            self._sync_measurement_summaries_runtime()
            self._sync_section_summaries_runtime()
            if _selection_changed:
                self.history._end_operation()  # noqa: SLF001
            addons = getattr(self, "addons", None)
            if addons is not None and hasattr(addons, "refresh_context_items"):
                try:
                    addons.refresh_context_items(enriched)
                except Exception as exc:
                    emit_suppressed_exception(
                        "MolSysView._handle_frontend_event.addon_context_refresh",
                        exc,
                        context={"event": event},
                    )
        elif event == "interaction_tool_state":
            self._last_tool_state_event = dict(content)
        elif event == "shape_render_status":
            tag = content.get("tag")
            if isinstance(tag, str) and tag:
                self._shape_render_status[tag] = dict(content)
        elif event == "interaction_measurement_created":
            self.measurements._register_interactive_measurement(dict(content))  # noqa: SLF001
        elif event == "trajectory_frame_rendered":
            t_id = content.get("transaction_id")
            if t_id is not None:
                self._rendered_transactions_acks.add(t_id)
                self._last_rendered_transaction = t_id
        elif event == "trajectory_frame_changed":
            # Emitted by TS when playback stops; update Python-side frame index and NPT box.
            frame = int(content.get("frame", 0))
            self._current_structure_index = frame
            self.player._is_playing = bool(content.get("is_playing", False))  # noqa: SLF001
            self.player._store_state()  # noqa: SLF001
            self._sync_measurement_summaries_runtime()
            if self._frame_change_callbacks:
                frame_event = {
                    "event": "frame_changed",
                    "frame": frame,
                    "is_playing": bool(content.get("is_playing", False)),
                }
                for cb in list(self._frame_change_callbacks):
                    try:
                        cb(frame_event)
                    except Exception:
                        # A misbehaving user callback must not break frame tracking.
                        pass
            if self._box_record is not None:
                self.show_box(
                    color=self._box_record["color"],
                    width=self._box_record["width"],
                    alpha=self._box_record["alpha"],
                    structure_indices=frame,
                    skip_digestion=True,
                )
        elif event == "request_dynamic_region_evaluation":
            self._handle_dynamic_region_evaluation_request(content)
        elif event == "panel_mode_state":
            self._last_panel_mode_state_event = dict(content)
        elif event == "panel_navigate":
            addon_name = content.get("addon")
            panel_id = content.get("panel")
            if isinstance(addon_name, str) and isinstance(panel_id, str):
                self._mount_addon_panel(addon_name.strip(), panel_id.strip())
            else:
                self._unmount_addon_panel()
        elif event == "panel_unmount":
            self._unmount_addon_panel()
        elif event == "addon_panel_action":
            if self._active_panel_widget is not None:
                _, _, widget = self._active_panel_widget
                msg_content = content.get("content")
                if isinstance(msg_content, dict):
                    widget._route_frontend_message(widget, msg_content, [])  # noqa: SLF001
        elif event == "viewer_init_failed":
            reason = content.get("reason", "unknown")
            message = content.get("message") or "Mol* viewer failed to initialize."
            emit_from_catalog(
                CATALOG["viewer_init_failed"],
                package_root=PACKAGE_ROOT,
                meta=META,
                extra={"reason": reason, "message": message},
            )
        elif event == "runtime_contract_rejected":
            emit_from_catalog(
                CATALOG["runtime_contract_rejected"],
                package_root=PACKAGE_ROOT,
                meta=META,
                extra={
                    "seam": content.get("seam", "runtime"),
                    "reason": content.get("reason", "unknown"),
                    "detail": content.get("detail", "unknown"),
                },
            )
        elif event == "camera_stranded_inside_scene":
            # Contract S9 detection. Reported, never repaired: the condition is
            # sharp enough to diagnose but not to act on, and a false positive
            # that moves the camera is worse than the defect it chases. Costs a
            # log line instead.
            emit_from_catalog(
                CATALOG["camera_stranded_inside_scene"],
                package_root=PACKAGE_ROOT,
                meta=META,
                extra={
                    "distance": content.get("distance"),
                    "scene_radius": content.get("scene_radius"),
                    "after": content.get("after"),
                },
            )

    # --- Regions / Layers registry ---

    @property
    def current_structure_index(self) -> int:
        """Index of the structure currently displayed.

        Delegate to ``view.player.index``.
        """
        return self._current_structure_index

    @property
    def regions(self) -> RegionsManager:
        """Public registry of regions (structural selections)."""
        return self._regions

    @property
    def js_logs(self) -> list[dict[str, str]]:
        """Logs received from the frontend when `debug_js` is enabled."""
        return list(self._js_logs)

    @property
    def layers(self) -> LayersManager:
        """Public registry of layers (non-structural visuals)."""
        return self._layers

    @property
    def selections_registry(self) -> Mapping[str, Selection]:
        """Public registry of persistent named selection wrappers."""
        return self._selections

    @property
    def molsys(self):
        """Read-only handle to the loaded MolSysMT molecular system.

        This property exposes the underlying `molsysmt.MolSys` instance created
        when you call `load(...)`. It is intended for inspection (for example,
        via `molsysmt.info(...)` or `molsysmt.select(...)`).

        Notes
        -----
        - This is a read-only property (no setter): you cannot reassign it.
        - The returned object may be mutable. If you modify it directly, you can
          desynchronize what you see in the viewer. If you need to change the
          system, modify your data and call `load(...)` again.
        """
        return self._molsys

    def wait_for_transaction(self, transaction_id: str | int, timeout_s: float = 1.0) -> bool:
        """Wait until the frontend acknowledges that the transaction has been rendered."""
        import time
        t_start = time.time()
        while transaction_id not in self._rendered_transactions_acks:
            time.sleep(0.001)
            if time.time() - t_start > timeout_s:
                return False
        try:
            self._rendered_transactions_acks.remove(transaction_id)
        except KeyError:
            pass
        return True

    def _enrich_interaction_payload(self, payload: dict) -> dict:
        # region_tags are a structure-region concept: only structure picks carry
        # them. Other kinds (annotation, shape, measurement) are left unchanged.
        if payload.get("kind") != "structure":
            return payload
        raw = payload.get("atom_indices")
        if not raw:
            return payload
        atom_indices = list(raw)
        payload["atom_indices"] = atom_indices
        pick_set = set(atom_indices)
        tags = [
            tag
            for tag, region in self._regions.items()
            if region.atom_indices is not None and pick_set.isdisjoint(region.atom_indices) is False
        ]
        payload["region_tags"] = tags
        return payload

    def _next_region_tag(self) -> str:
        return self._tag_managers["region"].allocate()

    def _next_annotation_tag(self) -> str:
        return self._tag_managers["annotation"].allocate()

    def _next_layer_tag(self) -> str:
        return self._tag_managers["layer"].allocate()

    def _next_measurement_tag(self) -> str:
        return self._tag_managers["measurement"].allocate()

    def _next_shape_tag(self) -> str:
        return self._tag_managers["shape"].allocate()

    def _get_tag_counter(self, domain: str) -> int:
        return self._tag_managers[domain].high_water_mark

    def _set_tag_counter(self, domain: str, value: int) -> None:
        self._tag_managers[domain].restore(value)

    _region_counter = property(
        lambda self: self._get_tag_counter("region"),
        lambda self, value: self._set_tag_counter("region", value),
    )
    _shape_counter = property(
        lambda self: self._get_tag_counter("shape"),
        lambda self, value: self._set_tag_counter("shape", value),
    )
    _annotation_counter = property(
        lambda self: self._get_tag_counter("annotation"),
        lambda self, value: self._set_tag_counter("annotation", value),
    )
    _measurement_counter = property(
        lambda self: self._get_tag_counter("measurement"),
        lambda self, value: self._set_tag_counter("measurement", value),
    )
    _layer_counter = property(
        lambda self: self._get_tag_counter("layer"),
        lambda self, value: self._set_tag_counter("layer", value),
    )
    _section_counter = property(
        lambda self: self._get_tag_counter("section"),
        lambda self, value: self._set_tag_counter("section", value),
    )

    def _remap_indices(self, indices: Any, atom_index_map: dict[int, int] | None) -> list[int]:
        if atom_index_map is None:
            if isinstance(indices, list):
                return [int(ii) for ii in indices if isinstance(ii, (int, np.integer))]
            return []
        if not isinstance(indices, list):
            return []
        out: list[int] = []
        for ii in indices:
            if not isinstance(ii, (int, np.integer)):
                continue
            mapped = atom_index_map.get(int(ii))
            if mapped is None:
                continue
            out.append(mapped)
        return out

    def _remap_atom_pairs(self, pairs: Any, atom_index_map: dict[int, int] | None) -> list[list[int]] | None:
        if atom_index_map is None:
            return pairs if isinstance(pairs, list) else None
        if not isinstance(pairs, list):
            return None
        out: list[list[int]] = []
        for pair in pairs:
            if (
                isinstance(pair, (list, tuple))
                and len(pair) == 2
                and isinstance(pair[0], (int, np.integer))
                and isinstance(pair[1], (int, np.integer))
            ):
                a = atom_index_map.get(int(pair[0]))
                b = atom_index_map.get(int(pair[1]))
                if a is None or b is None:
                    continue
                out.append([a, b])
        return out

    def _remap_frame_atom_indices(self, frames: Any, atom_index_map: dict[int, int] | None) -> list[list[int] | None] | None:
        if atom_index_map is None:
            return frames if isinstance(frames, list) else None
        if not isinstance(frames, list):
            return None
        remapped_frames: list[list[int] | None] = []
        any_live = False
        for frame_indices in frames:
            if frame_indices is None:
                remapped_frames.append(None)
                continue
            remapped = self._remap_indices(frame_indices, atom_index_map)
            if remapped:
                any_live = True
                remapped_frames.append(remapped)
            else:
                remapped_frames.append(None)
        return remapped_frames if any_live else None

    def _remap_frame_atom_pairs(self, frames: Any, atom_index_map: dict[int, int] | None) -> list[list[list[int]] | None] | None:
        if atom_index_map is None:
            return frames if isinstance(frames, list) else None
        if not isinstance(frames, list):
            return None
        remapped_frames: list[list[list[int]] | None] = []
        any_live = False
        for frame_pairs in frames:
            if frame_pairs is None:
                remapped_frames.append(None)
                continue
            remapped = self._remap_atom_pairs(frame_pairs, atom_index_map)
            if remapped:
                any_live = True
                remapped_frames.append(remapped)
            else:
                remapped_frames.append(None)
        return remapped_frames if any_live else None

    def _remap_shape_message(self, msg: dict, atom_index_map: dict[int, int] | None) -> dict | None:
        if atom_index_map is None:
            return msg
        op = msg.get("op")
        if not isinstance(op, str) or not op.startswith("add_"):
            return msg

        remapped = dict(msg)
        options = remapped.get("options")
        if not isinstance(options, dict):
            return remapped

        options = dict(options)
        remapped["options"] = options

        if "atom_indices" in options:
            options["atom_indices"] = self._remap_indices(options.get("atom_indices"), atom_index_map)
            if not options["atom_indices"]:
                return None

        if "structures_atom_indices" in options:
            frames = self._remap_frame_atom_indices(options.get("structures_atom_indices"), atom_index_map)
            if frames is None:
                return None
            options["structures_atom_indices"] = frames

        if "atom_pairs" in options:
            options["atom_pairs"] = self._remap_atom_pairs(options.get("atom_pairs"), atom_index_map)
            if options["atom_pairs"] == []:
                return None

        if "structures_atom_pairs" in options:
            frames = self._remap_frame_atom_pairs(options.get("structures_atom_pairs"), atom_index_map)
            if frames is None:
                return None
            options["structures_atom_pairs"] = frames

        if "mouth_atom_indices" in options:
            mouths = options.get("mouth_atom_indices")
            if isinstance(mouths, list) and mouths and isinstance(mouths[0], list):
                options["mouth_atom_indices"] = [
                    self._remap_indices(m, atom_index_map) for m in mouths
                ]
            else:
                options["mouth_atom_indices"] = self._remap_indices(mouths, atom_index_map)

        return remapped

    def _remap_annotation_message(self, msg: dict, atom_index_map: dict[int, int] | None) -> dict:
        remapped = dict(msg)
        options = remapped.get("options")
        if msg.get("op") != "add_label" or not isinstance(options, dict):
            return remapped

        options = dict(options)
        remapped["options"] = options
        original = [int(index) for index in options.get("atom_indices") or []]
        if atom_index_map is None:
            n_atoms = int(self._molsys.get_n_atoms()) if self._molsys is not None else 0
            survivors = [index for index in original if 0 <= index < n_atoms]
            missing = [index for index in original if index not in survivors]
        else:
            survivors = self._remap_indices(original, atom_index_map)
            missing = [index for index in original if index not in atom_index_map]
        options["atom_indices"] = survivors
        broken = len(survivors) == 0
        remapped["broken"] = broken
        remapped["broken_reason"] = (
            self._broken_anchor_reason(missing, empty=not original)
            if broken
            else None
        )
        return remapped

    def _remap_measurement_message(self, msg: dict, atom_index_map: dict[int, int] | None) -> dict:
        op = msg.get("op")
        if op not in {"add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"}:
            return dict(msg)

        remapped = dict(msg)
        options = remapped.get("options")
        if not isinstance(options, dict):
            return remapped
        options = dict(options)
        remapped["options"] = options
        picks = options.get("picks_atom_indices")
        if not isinstance(picks, list):
            return remapped
        original_picks = [[int(index) for index in pick] for pick in picks]
        if atom_index_map is None:
            n_atoms = int(self._molsys.get_n_atoms()) if self._molsys is not None else 0
            remapped_picks = [
                [index for index in pick if 0 <= index < n_atoms]
                for pick in original_picks
            ]
            missing = sorted({
                index
                for original, survivors in zip(original_picks, remapped_picks)
                for index in original
                if index not in survivors
            })
        else:
            remapped_picks = [self._remap_indices(pick, atom_index_map) for pick in original_picks]
            missing = sorted({
                index
                for pick in original_picks
                for index in pick
                if index not in atom_index_map
            })
        options["picks_atom_indices"] = remapped_picks

        options.pop("value", None)
        options.pop("value_series", None)
        broken_reason = None
        if not remapped_picks or any(not pick for pick in remapped_picks):
            broken_reason = self._broken_anchor_reason(
                missing,
                empty=not missing,
            )
        else:
            policy = self.measurements._normalize_endpoint_policy(options.get("endpoint_policy"))  # noqa: SLF001
            endpoint_kinds, endpoint_labels, endpoint_atom_indices = (
                self.measurements._resolve_endpoint_metadata(remapped_picks, policy)  # noqa: SLF001
            )
            options["endpoint_policy"] = policy
            options["endpoint_kinds"] = endpoint_kinds
            options["endpoint_labels"] = endpoint_labels
            options["endpoint_atom_indices"] = endpoint_atom_indices
            series = self.measurements._compute_measurement_series(  # noqa: SLF001
                str(op),
                remapped_picks,
                endpoint_atom_indices,
                policy,
            )
            if series is None or len(series) == 0:
                broken_reason = "Measurement value cannot be derived from its current anchors."
            else:
                options["value"] = float(series[0])
                options["value_series"] = [float(value) for value in series]

        remapped["broken"] = broken_reason is not None
        remapped["broken_reason"] = broken_reason
        return remapped

    def _remap_selection_message(self, msg: dict, atom_index_map: dict[int, int] | None) -> dict | None:
        if msg.get("op") != "save_selection":
            return dict(msg)
        updated = dict(msg)
        recipe = msg.get("recipe")
        if isinstance(recipe, list) and recipe:
            try:
                remapped_recipe, replayed_atoms = self._replay_selection_recipe(recipe, atom_index_map)
            except Exception as exc:
                emit_suppressed_exception(
                    "MolSysView._remap_selection_message.recipe",
                    exc,
                    context={"tag": msg.get("tag")},
                )
            else:
                if len(replayed_atoms) == 0:
                    return None
                updated["recipe"] = remapped_recipe
                updated["atom_indices"] = replayed_atoms
                return updated

        if atom_index_map is None:
            return updated
        atom_indices = msg.get("atom_indices")
        if not isinstance(atom_indices, list):
            return updated
        remapped = self._remap_indices(atom_indices, atom_index_map)
        if len(remapped) == 0:
            return None
        updated["atom_indices"] = remapped
        return updated

    def _remap_atom_color_map(self, atom_index_map: dict[int, int] | None) -> None:
        if not any(self._atom_color_layers.values()) and not self._atom_color_map:
            return
        if atom_index_map is None:
            remapped_layers = {
                owner: dict(layer)
                for owner, layer in self._atom_color_layers.items()
                if layer
            }
        else:
            remapped_layers = {
                owner: {
                    atom_index_map[old_index]: color
                    for old_index, color in layer.items()
                    if old_index in atom_index_map
                }
                for owner, layer in self._atom_color_layers.items()
            }
        self._atom_color_layers = {
            owner: layer
            for owner, layer in remapped_layers.items()
            if layer or owner == "whole"
        }
        self._send_resolved_atom_colors(replay=True)

    def _next_region_order(self) -> int:
        self._region_order_counter += 1
        return self._region_order_counter

    def _bump_region_order(self, region: Region) -> None:
        region.order = self._next_region_order()

    def _emit_region_order(self, region: Region) -> None:
        region._send("set_region_order", order=region.order)  # noqa: SLF001
        self._sync_region_summaries_runtime()

    def _recompute_atom_colors_for_order_change(self) -> None:
        previous = dict(self._atom_color_map)
        self._send_atom_color_delta(previous)

    def _raise_region_to_front(self, region: Region) -> None:
        self._bump_region_order(region)
        self._recompute_atom_colors_for_order_change()
        self._emit_region_order(region)

    def _send_region_to_back(self, region: Region) -> None:
        active_orders = [
            getattr(candidate, "order", 0)
            for candidate in self._regions.values()
            if candidate is not region and getattr(candidate, "_active", False)
        ]
        region.order = (min(active_orders) - 1) if active_orders else 0
        self._recompute_atom_colors_for_order_change()
        self._emit_region_order(region)

    def _resolved_atom_color_map(self) -> dict[int, int]:
        resolved: dict[int, int] = dict(self._atom_color_layers.get("whole", {}))
        ordered_regions = sorted(
            (
                region
                for region in self._regions.values()
                if getattr(region, "_active", False)
            ),
            key=lambda region: getattr(region, "order", 0),
        )
        for region in ordered_regions:
            layer = self._atom_color_layers.get(region.tag)
            if layer:
                resolved.update(layer)
        return resolved

    def _send_resolved_atom_colors(self, *, replay: bool = False) -> None:
        resolved = self._resolved_atom_color_map()
        self._atom_color_map = resolved
        message = {
            "op": "set_atom_colors",
            "atom_indices": list(resolved.keys()),
            "colors": list(resolved.values()),
            "replace": True,
        }
        sender = self._send_replay if replay else self._send
        sender(message)

    def _send_atom_color_delta(self, previous: dict[int, int]) -> None:
        resolved = self._resolved_atom_color_map()
        changed = [
            atom_index
            for atom_index, color in resolved.items()
            if previous.get(atom_index) != color
        ]
        cleared = [
            atom_index
            for atom_index in previous
            if atom_index not in resolved
        ]
        self._atom_color_map = resolved
        if changed:
            self._send(
                {
                    "op": "set_atom_colors",
                    "atom_indices": changed,
                    "colors": [resolved[atom_index] for atom_index in changed],
                    "replace": False,
                }
            )
        if cleared:
            self._send(
                {
                    "op": "clear_atom_colors",
                    "atom_indices": cleared,
                }
            )

    def _set_atom_color_layer(self, owner: str, colors: dict[int, int], *, bump: Region | None = None) -> None:
        previous = dict(self._atom_color_map)
        self._atom_color_layers[owner] = dict(colors)
        if bump is not None:
            self._bump_region_order(bump)
        self._send_atom_color_delta(previous)
        self._sync_whole_summary_runtime()

    def _update_atom_color_layer(self, owner: str, colors: dict[int, int], *, bump: Region | None = None) -> None:
        previous = dict(self._atom_color_map)
        layer = self._atom_color_layers.setdefault(owner, {})
        layer.update(colors)
        if bump is not None:
            self._bump_region_order(bump)
        self._send_atom_color_delta(previous)
        self._sync_whole_summary_runtime()

    def _clear_atom_color_layer(self, owner: str) -> None:
        previous = dict(self._atom_color_map)
        self._atom_color_layers[owner] = {}
        self._send_atom_color_delta(previous)
        self._sync_whole_summary_runtime()

    def _drop_atom_color_layer(self, owner: str) -> None:
        previous = dict(self._atom_color_map)
        self._atom_color_layers.pop(owner, None)
        self._send_atom_color_delta(previous)
        self._sync_whole_summary_runtime()

    def _rename_atom_color_layer(self, old_owner: str, new_owner: str) -> None:
        if old_owner in self._atom_color_layers:
            self._atom_color_layers[new_owner] = self._atom_color_layers.pop(old_owner)

    def _copy_atom_color_layer(self, source_owner: str, target_owner: str, *, bump: Region | None = None) -> None:
        source = self._atom_color_layers.get(source_owner, {})
        if source:
            previous = dict(self._atom_color_map)
            self._atom_color_layers[target_owner] = dict(source)
            if bump is not None:
                self._bump_region_order(bump)
            self._send_atom_color_delta(previous)
            self._sync_whole_summary_runtime()

    def _rebuild_view_from_current_molsys(
        self,
        *,
        label: str | None = None,
        atom_index_map: dict[int, int] | None = None,
        visible_atom_indices: list[int] | None = None,
    ) -> None:
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before mutating the view.")

        n_atoms = int(self._molsys.get_n_atoms())
        # A rebuild supersedes any in-flight generation before replacing its
        # lazy fallback. This makes it impossible for an old timeout to
        # serialize the newly edited MolSys under the old generation.
        self._cancel_binary_structure_stream("molecular system rebuilt")
        molecular_projection = self._new_lazy_molecular_projection(label=label)
        self.atom_mask = np.ones(n_atoms, dtype=bool)
        if visible_atom_indices is not None:
            self.atom_mask[:] = False
            keep = self._remap_indices(visible_atom_indices, atom_index_map)
            if keep:
                self.atom_mask[keep] = True

        for tag, region in list(self._regions.items()):
            if region.atom_indices is None:
                continue
            evaluated_atom_indices = None
            if Region._is_reevaluable_provenance(dict(region.provenance)):  # noqa: SLF001
                evaluated_atom_indices = self._evaluate_region_provenance(region)
            if evaluated_atom_indices is None:
                if atom_index_map is None:
                    continue
                evaluated_atom_indices = self._remap_indices(list(region.atom_indices), atom_index_map)
            if len(evaluated_atom_indices) == 0:
                region._active = False  # noqa: SLF001
                self._unregister_region(tag)
                continue
            region._set_atom_indices(evaluated_atom_indices)  # noqa: SLF001

        self._clear_dynamic_region_cache()

        # Rebuild the message history to reflect the new state (important for HTML exports).
        self._message_history = []
        # Force the next visibility update to send a full state (the frontend is
        # reset by the rebuild, so a delta against the old mask would be wrong).
        self._last_visibility_mask = None
        # The undo/redo snapshots reference the pre-edit index space; a system
        # edit invalidates them.
        history = getattr(self, "history", None)
        if history is not None:
            history.clear()

        self._send({"op": "clear_all"})
        self._send(molecular_projection)

        if self.whole.preset is not None or self.whole.representation is not None:
            self.whole.set_representation(
                self.whole.representation,
                preset=self.whole.preset,
                skip_digestion=True,
                **self.whole.params,
            )

        self._remap_atom_color_map(atom_index_map)

        if not self.whole.visible:
            self._send({"op": "hide_whole", "target": "whole"})

        for layer in list(self._layers.values()):
            if not getattr(layer, "_active", True):
                continue
            layer._send_create()  # noqa: SLF001
            if getattr(layer, "_hidden", False):
                layer.hide(skip_digestion=True)

        for region in list(self._regions.values()):
            if not getattr(region, "_active", True):
                continue
            if getattr(region, "preset", None) is not None or region.representation is not None:
                region._send_create(include_visual=False)  # noqa: SLF001
                region.set_representation(
                    region.representation,
                    preset=getattr(region, "preset", None),
                    skip_digestion=True,
                    **(region.repr_params or {}),
                )
            else:
                region._send_create()  # noqa: SLF001
            if getattr(region, "_hidden", False):
                region.hide(skip_digestion=True)

        new_shape_history: list[dict] = []
        for msg in self._shape_history:
            remapped = self._remap_shape_message(msg, atom_index_map)
            if remapped is None:
                tag = self._tag_from_message(msg)
                if tag is not None:
                    self._unregister_scene_object("shape", tag)
                continue
            new_shape_history.append(remapped)
            self._send_replay(remapped)
        self._shape_history = new_shape_history

        new_annotation_history: list[dict] = []
        for msg in self._annotation_history:
            remapped = self._remap_annotation_message(msg, atom_index_map)
            tag = self._tag_from_message(remapped)
            annotation = self.annotations.get(tag, skip_digestion=True) if tag is not None else None
            if annotation is not None:
                annotation.broken = bool(remapped.get("broken"))
                annotation.broken_reason = remapped.get("broken_reason")
            new_annotation_history.append(remapped)
            if not remapped.get("broken"):
                self._send_replay(remapped)
        self._annotation_history = new_annotation_history

        new_measurement_history: list[dict] = []
        for msg in self._measurement_history:
            remapped = self._remap_measurement_message(msg, atom_index_map)
            tag = self._tag_from_message(remapped)
            measurement = self.measurements.get(tag, skip_digestion=True) if tag is not None else None
            if measurement is not None:
                measurement.broken = bool(remapped.get("broken"))
                measurement.broken_reason = remapped.get("broken_reason")
            new_measurement_history.append(remapped)
            if not remapped.get("broken"):
                self._send_replay(remapped)
        self._measurement_history = new_measurement_history

        if atom_index_map is not None:
            remapped_scene_look: dict[str, dict] = {}
            for key, msg in self._scene_look.items():
                remapped = self._remap_scene_look_message(msg, atom_index_map)
                if remapped is not None:
                    remapped_scene_look[key] = remapped
            self._scene_look = remapped_scene_look

        rewritten_selections: list[dict] = []
        for msg in self._selection_history:
            remapped = self._remap_selection_message(msg, atom_index_map)
            if remapped is None:
                continue
            rewritten_selections.append(remapped)
            self._send_replay(remapped)
        self._selection_history = rewritten_selections
        self._selections = {
            tag: selection
            for tag, selection in self._selections.items()
            if any(record.get("tag") == tag for record in self._selection_history)
        }

        for msg in self._scene_look.values():
            self._send_replay(dict(msg))

        for msg in self._player_replay_messages():
            self._send_replay(msg)

        self._update_visibility_in_frontend()
        self._sync_annotation_summaries_runtime()
        self._sync_measurement_summaries_runtime()
        self._sync_shape_summaries_runtime()

    @signal(tags=["edit"])
    def apply_system_edit(
        self,
        new_molsys,
        *,
        atom_index_map: dict[int, int] | None = None,
        label: str | None = None,
        visible_atom_indices: list[int] | None = None,
        load_blocks: str = "keep",
        appended_n_atoms: int | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Replace the loaded molecular system and reconcile viewer state.

        This is a low-level integration primitive for addons and advanced
        callers. Molecular edit semantics belong to MolSysMT or an addon; this
        method only applies the resulting system to the live viewer and remaps
        viewer-owned state such as regions, selections, shapes, annotations,
        measurements, visibility, per-atom colors, and the load-block accounting.

        Parameters
        ----------
        new_molsys
            Molecular system that should become the view's current system.
        atom_index_map
            Optional ``{old_atom_index: new_atom_index}`` map. Use ``None`` for
            edits where atom identity and indices are unchanged.
        label
            Optional label for the rebuilt payload. Defaults to the current
            view label.
        visible_atom_indices
            Optional list of visible atom indices in the pre-edit system. When
            omitted, the current visibility state is captured before replacing
            the system.
        load_blocks
            Load-block accounting policy after the edit: ``"keep"`` (default,
            leave the blocks as-is, e.g. coordinate/attribute edits), ``"collapse"``
            (one block for the current whole, e.g. after a removal), or
            ``"append"`` (record a new block; requires ``appended_n_atoms``, e.g.
            after an addition). Callers should not manage load blocks through
            private helpers.
        appended_n_atoms
            Number of atoms appended by the edit; required when
            ``load_blocks="append"``.
        """
        if new_molsys is None:
            raise ValueError("apply_system_edit(...) requires a molecular system.")
        if load_blocks not in ("keep", "collapse", "append"):
            raise ValueError(
                f"apply_system_edit(load_blocks={load_blocks!r}) must be 'keep', 'collapse', or 'append'."
            )

        visible = self.visible_atom_indices if visible_atom_indices is None else visible_atom_indices
        effective_label = self._last_label if label is None else label
        self._molsys = new_molsys
        self.molecular_system = new_molsys
        if label is not None:
            self._last_label = label
        self._rebuild_view_from_current_molsys(
            label=effective_label,
            atom_index_map=atom_index_map,
            visible_atom_indices=visible,
        )

        # Reconcile load-block accounting so callers (view.add/remove and addons)
        # do not have to touch the private load-block helpers.
        if load_blocks == "collapse":
            self._collapse_load_blocks_to_current_whole()
        elif load_blocks == "append":
            if appended_n_atoms is None:
                raise ValueError("apply_system_edit(load_blocks='append') requires appended_n_atoms.")
            if not self._load_blocks:
                prior = max(int(self._molsys.get_n_atoms()) - int(appended_n_atoms), 0)
                self._register_initial_load_block(n_atoms=prior, label=None)
            self._append_load_block(n_atoms=int(appended_n_atoms), label=effective_label)

    def _local_structure_index_for_player(self) -> int:
        return int(self._current_structure_index)

    def _player_replay_messages(self) -> list[dict]:
        messages: list[dict] = []
        if self._current_structure_index != 0:
            messages.append(
                {
                    "op": "set_trajectory_frame",
                    "index": self._local_structure_index_for_player(),
                }
            )
        if self._player_state:
            playback = {
                "op": "set_trajectory_playback",
                "fps": int(self._player_state.get("fps", 30)),
                "mode": str(self._player_state.get("mode", "loop")),
                "direction": str(self._player_state.get("direction", "forward")),
                "step": int(self._player_state.get("step", 1)),
            }
            if self._player_state.get("is_playing"):
                playback["action"] = "play"
            messages.append(playback)
        return messages

    def _reset_load_blocks(self) -> None:
        self._load_blocks = []
        self._empty = True

    @property
    def load_blocks(self) -> list[dict]:
        """Read-only list of load records for every successful load operation.

        Each entry is a dict with keys ``index``, ``label``, ``start``, ``stop``,
        and ``n_atoms``.  Returns a shallow copy so the internal accounting cannot
        be mutated accidentally.
        """
        return list(self._load_blocks)

    @property
    def visible_atom_indices(self):
        """Return the indices of currently visible atoms."""
        if self.atom_mask is None:
            return None
        # Use a plain list so the payload is JSON-serializable.
        return np.nonzero(self.atom_mask)[0].tolist()

    @property
    def visible_structure_indices(self):
        """Return the indices of currently visible structures."""
        if self.structure_mask is None:
            return None
        # Use a plain list so the payload is JSON-serializable.
        return np.nonzero(self.structure_mask)[0].tolist()

    @property
    def scene_style_name(self) -> str | None:
        """Name of the active scene style, if any."""
        return getattr(self.styles, "active_name", None)

    @signal(tags=["color", "viewer"])
    @digest()
    @records_scene_history
    def reset_all_colors(self, skip_digestion: bool = False) -> None:
        """Clear every per-atom colour override on the canvas."""
        self._atom_color_layers = {"whole": {}}
        self._atom_color_map.clear()
        self._send({"op": "clear_atom_colors"})
        self._sync_whole_summary_runtime()

    def _update_visibility_in_frontend(self):
        if self.atom_mask is None:
            return
        new_mask = self.atom_mask
        last_mask = self._last_visibility_mask

        # No-op if nothing changed: avoids version churn and redundant traffic.
        # (Rebuilds reset _last_visibility_mask to None, so a post-rebuild sync is
        # never skipped here.)
        if (
            last_mask is not None
            and last_mask.shape == new_mask.shape
            and np.array_equal(last_mask, new_mask)
        ):
            return

        self._visibility_version += 1
        version = self._visibility_version
        visible = self.visible_atom_indices
        full_msg = {
            "op": "update_visibility",
            "options": {"visible_atom_indices": visible, "version": version},
        }
        self._last_visibility_mask = new_mask.copy()

        # Build a delta when we are live and have a comparable prior mask, and only
        # if it is actually smaller than the full visible list.
        delta_msg = None
        if self._ready and last_mask is not None and last_mask.shape == new_mask.shape:
            changed = np.nonzero(new_mask != last_mask)[0]
            if changed.size and changed.size < len(visible):
                shown = changed[new_mask[changed]].tolist()
                hidden = changed[~new_mask[changed]].tolist()
                delta_msg = {
                    "op": "update_visibility_delta",
                    "options": {
                        "base_version": version - 1,
                        "version": version,
                        "shown": shown,
                        "hidden": hidden,
                    },
                }

        if delta_msg is not None:
            # Record the authoritative full state for replay/export (stateless and
            # reproducible), but only put the small delta on the wire.
            self._message_history.append(full_msg)
            self._send_runtime_only(delta_msg)
        else:
            # First send, post-rebuild, not-ready, or a delta that is not smaller:
            # send and record the full state.
            self._send(full_msg)

    def _resend_full_visibility(self):
        """Send the authoritative full visibility state at the current version.

        Used to answer a frontend `request_visibility_resync` (version mismatch),
        making the delta protocol self-healing without leaving the viewer stale.
        """
        if self.atom_mask is None:
            return
        self._send_runtime_only({
            "op": "update_visibility",
            "options": {
                "visible_atom_indices": self.visible_atom_indices,
                "version": self._visibility_version,
            },
        })

    # --- Export helpers for docs/notebooks ---

    def _write_html_impl(
        self,
        output_filename: str,
        *,
        title: str = "MolSysViewer",
        include_controls: bool = True,
        include_popout: bool = True,
        mode: str = "standalone",
        inline_messages: bool = True,
        runtime_urls: Sequence[str] | None = None,
        host_event_transport: str | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Export this viewer widget to an HTML file.

        Parameters
        ----------
        output_filename:
            Path to the HTML file to create.
        title:
            Optional title for the exported HTML page.
        include_controls:
            If ``True`` (default), include the on-canvas control buttons
            (Reset, Fullscreen, background toggle, Spin, Swing) in the exported view.
            Set this to ``False`` if you prefer a minimal viewer without these controls,
            for example when embedding inside another application that already provides
            its own UI.
        include_popout:
            If ``True`` (default), include the popout button and allow opening a popout window.
        mode:
            - ``"standalone"`` (default): produce a self-contained HTML using the widget embed machinery.
            - ``"lite"``: produce a lightweight HTML that loads the runtime from the CDN
              and replays messages (suitable for embedded docs-light views).
        inline_messages:
            Only used when ``mode="lite"``. If ``True`` (default), embed the replay messages inline in the HTML.
        """
        if mode not in {"standalone", "lite"}:
            raise ValueError("view.export.html(mode=...) must be 'standalone' or 'lite'.")

        # If the frontend is live, request a fresh camera snapshot so exports
        # reflect the latest user view (best-effort, no hard dependency).
        self._request_camera_snapshot()

        messages = self._build_export_messages()

        if mode == "standalone":
            # Serialize the message history so the exported HTML can replay all
            # actions (loads/shapes/visibility) without needing a live Python kernel.
            self.widget.initial_messages = messages
            html = self._build_standalone_html(
                title=title,
                include_controls=include_controls,
                include_popout=include_popout,
            )
        else:
            html = self._build_lite_html(
                title=title,
                include_controls=include_controls,
                include_popout=include_popout,
                messages=messages,
                inline_messages=inline_messages,
                runtime_urls=runtime_urls,
                host_event_transport=host_event_transport,
            )
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html)

    def _request_camera_snapshot(self, timeout_s: float = 0.35) -> bool:
        """Ask the frontend for a camera snapshot (best-effort)."""
        if not self._ready:
            return False
        previous = self._last_camera_snapshot
        try:
            # Blocks the kernel waiting for the answer, so it must not be queued
            # behind a stream whose acks that same wait would prevent arriving.
            self._transmit_widget_message({"op": "request_camera_snapshot"})
        except Exception:
            return False
        if timeout_s <= 0:
            return True
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            current = self._last_camera_snapshot
            if current is not None and current is not previous:
                return True
            time.sleep(0.01)
        return False

    def _request_image_export(
        self,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        preset: str = "current",
        camera_snapshot: dict | None = None,
        timeout_s: float = 2.0,
    ) -> dict | None:
        """Ask the frontend for an image export (best-effort)."""
        if not self._ready:
            return None
        previous = self._last_image_export_event
        payload: dict[str, Any] = {
            "op": "request_image_export",
            "transparent": bool(transparent),
            "scale": float(scale),
            "preset": str(preset),
        }
        if width_px is not None:
            payload["width"] = int(width_px)
        if height_px is not None:
            payload["height"] = int(height_px)
        if camera_snapshot:
            payload["camera_snapshot"] = dict(camera_snapshot)
        try:
            # Same reason as `_request_camera_snapshot`: a blocking request.
            self._transmit_widget_message(payload)
        except Exception:
            return None
        if timeout_s <= 0:
            return self._last_image_export_event
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            current = self._last_image_export_event
            if current is not None and current is not previous:
                return dict(current)
            time.sleep(0.01)
        return None

    def _export_image_headless(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        timeout_s: float = 15.0,
    ) -> None:
        """Render the scene without a live Jupyter frontend and save a PNG.

        Tries rendering backends in priority order:

        1. **Qt WebEngine** (``PySide6_uibcdf`` or ``PySide6``) — zero extra setup on
           Linux standalone installations where the package is already bundled.
        2. **playwright** — true headless rendering for all other environments;
           requires ``playwright install chromium`` once (shared with e2e tests).

        Called automatically by ``_export_image_impl`` when the Jupyter frontend is
        not ready.
        """
        errors: list[str] = []

        # --- Backend 1: Qt WebEngine (preferred on Linux standalone) ---
        try:
            self._export_image_headless_qt(
                output_filename,
                width_px=width_px,
                height_px=height_px,
                scale=scale,
                transparent=transparent,
                timeout_s=timeout_s,
            )
            return
        except ImportError as exc:
            errors.append(f"Qt backend unavailable: {exc}")
        except Exception as exc:
            errors.append(f"Qt backend failed: {exc}")

        # --- Backend 2: playwright ---
        try:
            self._export_image_headless_playwright(
                output_filename,
                width_px=width_px,
                height_px=height_px,
                scale=scale,
                transparent=transparent,
                timeout_s=timeout_s,
            )
            return
        except ImportError as exc:
            errors.append(f"playwright backend unavailable: {exc}")
        except Exception as exc:
            errors.append(f"playwright backend failed: {exc}")

        raise RuntimeError(
            "Headless image export failed — no rendering backend is available.\n"
            + "\n".join(f"  • {e}" for e in errors)
            + "\n\nTo enable headless export, install playwright and its browser:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )

    def _export_image_headless_qt(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        timeout_s: float = 15.0,
    ) -> None:
        """Headless render via Qt WebEngine (PySide6_uibcdf or PySide6)."""
        import os
        import pathlib
        import sys
        import tempfile

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        # Enable SwiftShader software WebGL so Mol* renders without a GPU.
        os.environ.setdefault(
            "QTWEBENGINE_CHROMIUM_FLAGS",
            "--use-gl=swiftshader --disable-gpu",
        )

        # Try UIBCDF standalone package first, then standard PySide6.
        QApplication = QWebEngineView = QUrl = QTimer = QEventLoop = None
        for _pkg in ("PySide6_uibcdf", "PySide6"):
            try:
                _w = __import__(f"{_pkg}.QtWidgets", fromlist=["QApplication"])
                _e = __import__(f"{_pkg}.QtWebEngineWidgets", fromlist=["QWebEngineView"])
                _c = __import__(f"{_pkg}.QtCore", fromlist=["QUrl", "QTimer", "QEventLoop"])
                QApplication = _w.QApplication
                QWebEngineView = _e.QWebEngineView
                QUrl = _c.QUrl
                QTimer = _c.QTimer
                QEventLoop = _c.QEventLoop
                break
            except ImportError:
                continue

        if QApplication is None:
            raise ImportError(
                "Neither PySide6_uibcdf nor PySide6 with QtWebEngineWidgets is available."
            )

        viewer_js = pathlib.Path(__file__).parent.parent / "viewer.js"
        if not viewer_js.exists():
            raise RuntimeError(f"Cannot find bundled viewer.js at {viewer_js}")

        messages = self._build_export_messages()
        html = self._build_lite_html(
            title="MolSysViewer Headless Export",
            include_controls=False,
            include_popout=False,
            messages=messages,
            inline_messages=True,
            # Qt WebEngine can load file:// imports from the same local origin.
            runtime_urls=[viewer_js.resolve().as_uri()],
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as _f:
            _f.write(html)
            tmp_html = _f.name

        try:
            w = int(width_px or 1280)
            h = int(height_px or 720)

            _app = QApplication.instance() or QApplication(sys.argv)  # type: ignore[misc]

            loop = QEventLoop()
            view = QWebEngineView()
            view.resize(w, h)
            view.show()

            state: dict[str, Any] = {"done": False, "error": None}

            def _check_rendered() -> None:
                def _cb(result: Any) -> None:
                    if result:
                        state["done"] = True
                        loop.quit()
                    else:
                        QTimer.singleShot(200, _check_rendered)
                view.page().runJavaScript(  # type: ignore[union-attr]
                    "!!document.getElementById('molsysviewer-root')"
                    "?.getAttribute('data-molsysviewer-rendered')",
                    _cb,
                )

            def _on_load(ok: bool) -> None:
                if not ok:
                    state["error"] = "Qt WebEngine failed to load the page."
                    loop.quit()
                    return
                QTimer.singleShot(300, _check_rendered)

            def _on_timeout() -> None:
                if not state["done"]:
                    state["error"] = "Timeout waiting for viewer to render (Qt backend)."
                    loop.quit()

            view.loadFinished.connect(_on_load)  # type: ignore[attr-defined]
            view.setUrl(QUrl.fromLocalFile(tmp_html))  # type: ignore[union-attr]
            QTimer.singleShot(int(timeout_s * 1000), _on_timeout)
            loop.exec()

            if state["error"]:
                raise RuntimeError(state["error"])

            pixmap = view.grab()
            pixmap.save(output_filename, "PNG")
        finally:
            try:
                os.unlink(tmp_html)
            except OSError:
                pass

    def _export_image_headless_playwright(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        timeout_s: float = 15.0,
    ) -> None:
        """Headless render via playwright (shared Chromium browser binary)."""
        import http.server
        import os
        import pathlib
        import socket
        import tempfile
        import threading

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "playwright is not installed. Install it with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )

        viewer_js_path = pathlib.Path(__file__).parent.parent / "viewer.js"
        if not viewer_js_path.exists():
            raise RuntimeError(f"Cannot find bundled viewer.js at {viewer_js_path}")
        pkg_dir = str(viewer_js_path.parent)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _s:
            _s.bind(("localhost", 0))
            port = _s.getsockname()[1]

        messages = self._build_export_messages()
        html = self._build_lite_html(
            title="MolSysViewer Headless Export",
            include_controls=False,
            include_popout=False,
            messages=messages,
            inline_messages=True,
            runtime_urls=[f"http://localhost:{port}/viewer.js"],
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", dir=pkg_dir, delete=False, encoding="utf-8"
        ) as _f:
            _f.write(html)
            html_name = os.path.basename(_f.name)
            html_abs = _f.name

        _pkg_dir_ref = pkg_dir

        class _SilentHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, directory=_pkg_dir_ref, **kwargs)

            def log_message(self, *args: Any) -> None:
                pass

        httpd = http.server.HTTPServer(("localhost", port), _SilentHandler)
        threading.Thread(
            target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
        ).start()

        try:
            w = int(width_px or 1280)
            h = int(height_px or 720)
            dpr = max(0.1, float(scale))
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                ctx = browser.new_context(
                    viewport={"width": w, "height": h},
                    device_scale_factor=dpr,
                )
                page = ctx.new_page()
                page.goto(
                    f"http://localhost:{port}/{html_name}",
                    timeout=int(timeout_s * 1000),
                )
                page.wait_for_selector(
                    "[data-molsysviewer-rendered]",
                    timeout=int(timeout_s * 1000),
                )
                page.screenshot(
                    path=output_filename,
                    full_page=False,
                    omit_background=bool(transparent),
                )
                browser.close()
        finally:
            httpd.shutdown()
            try:
                os.unlink(html_abs)
            except OSError:
                pass

    def _export_image_impl(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        preset: str = "current",
        camera_snapshot: dict | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Export the current viewer scene as a PNG image file."""
        event = self._request_image_export(
            width_px=width_px,
            height_px=height_px,
            scale=scale,
            transparent=transparent,
            preset=preset,
            camera_snapshot=camera_snapshot,
        )
        if not event:
            # No live frontend — fall back to headless playwright rendering
            self._export_image_headless(
                output_filename,
                width_px=width_px,
                height_px=height_px,
                scale=scale,
                transparent=transparent,
            )
            return

        if event.get("success") is False or event.get("error_type"):
            message = event.get("message")
            if not isinstance(message, str) or not message:
                message = "Frontend image export failed."
            raise ValueError(message)

        data_uri = event.get("data_uri")
        if not isinstance(data_uri, str) or not data_uri.startswith("data:image/png;base64,"):
            raise RuntimeError("Frontend image export did not return a PNG data URI.")

        image_bytes = base64.b64decode(data_uri.split(",", 1)[1])
        with open(output_filename, "wb") as f:
            f.write(image_bytes)

    def _export_figure_impl(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 2.0,
        background: str = "white",
        preset: str = "publication-light",
        camera_snapshot: dict | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Export a first figure-oriented PNG by mapping figure defaults onto image export."""
        normalized_background = str(background).strip().lower()
        normalized_preset = str(preset).strip() or "publication-light"

        if normalized_background == "transparent":
            transparent = True
            export_preset = "current"
        elif normalized_background == "dark":
            transparent = False
            export_preset = "publication-dark" if normalized_preset == "publication-light" else normalized_preset
        elif normalized_background == "current":
            transparent = False
            export_preset = normalized_preset if normalized_preset != "publication-light" else "current"
        else:
            transparent = False
            export_preset = "publication-light" if normalized_preset == "publication-light" else normalized_preset

        self._export_image_impl(
            output_filename,
            width_px=width_px,
            height_px=height_px,
            scale=scale,
            transparent=transparent,
            preset=export_preset,
            camera_snapshot=camera_snapshot,
            skip_digestion=True,
        )

    def _load_anywidget_bundle(self) -> str:
        """Return the JS bundle for anywidget if available to inline in exports."""
        try:
            import anywidget  # type: ignore
        except Exception:
            return ""

        from pathlib import Path

        locations = [
            Path(anywidget.__file__).parent / "nbextension" / "index.js",
            Path(anywidget.__file__).parent / "labextension" / "index.js",
        ]

        sources: list[str] = []
        for path in locations:
            if path.exists():
                try:
                    src = path.read_text(encoding="utf-8")
                    # If this bundle ends with an anonymous AMD define, give it a name
                    # so requirejs can register it when inlined.
                    src = src.replace(
                        'define(["@jupyter-widgets/base"], widget_default);',
                        'define("anywidget-inline", ["@jupyter-widgets/base"], widget_default);\n'
                        'define("anywidget", ["anywidget-inline"], function(m){return m;});',
                    )
                    sources.append(src)
                except Exception:
                    continue

        return "\n".join(sources)

    def _build_standalone_html(
        self,
        title: str,
        include_controls: bool = True,
        include_popout: bool = True,
    ) -> str:
        """Create a minimal standalone HTML embedding only this widget."""
        # Ensure initial_messages is in sync before exporting
        self.widget.initial_messages = self._build_export_messages()

        layout_state = self.widget.layout.get_state(drop_defaults=False)
        widget_state = self.widget.get_state(drop_defaults=False)
        # Override toolbar visibility for the exported HTML without mutating
        # the live widget trait in notebooks.
        widget_state["show_controls"] = bool(include_controls)
        widget_state["layout"] = f"IPY_MODEL_{self.widget.layout.model_id}"
        # Standalone exports have no live Python backend to answer the bootstrap
        # runtime request, so inline the full runtime only in exported HTML.
        widget_state["_esm"] = MolSysViewerWidget._viewer_js_source
        if "popup_js_source" in widget_state:
            widget_state["popup_js_source"] = ""
        widget_state["enable_popout"] = bool(include_popout)

        state_json = {
            "version_major": 2,
            "version_minor": 0,
            "state": {
                self.widget.layout.model_id: {
                    "model_name": "LayoutModel",
                    "model_module": "@jupyter-widgets/base",
                    "model_module_version": _WIDGETS_BASE_VERSION,
                    "state": layout_state,
                },
                self.widget.model_id: {
                    "model_name": self.widget._model_name,  # type: ignore[attr-defined]
                    "model_module": self.widget._model_module,  # type: ignore[attr-defined]
                    "model_module_version": self.widget._model_module_version,  # type: ignore[attr-defined]
                    "state": widget_state,
                },
            },
        }
        view_spec = {
            "version_major": 2,
            "version_minor": 0,
            "model_id": self.widget.model_id,
        }

        inline_anywidget = self._load_anywidget_bundle()
        anywidget_script = ""
        if inline_anywidget:
            anywidget_script = (
                "<script>\n"
                "requirejs.config({\n"
                "  map: {'*': {'anywidget': 'anywidget-inline'}},\n"
                f"  paths: {{'@jupyter-widgets/base': 'https://cdn.jsdelivr.net/npm/@jupyter-widgets/base@{_WIDGETS_BASE_VERSION}/dist/index'}}\n"
                "});\n"
                "</script>\n"
                f"<script>\n{inline_anywidget}\n</script>\n"
            )

        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
</head>
<body>

<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@jupyter-widgets/html-manager@{_HTML_MANAGER_VERSION}/dist/embed-amd.js" crossorigin="anonymous"></script>
{anywidget_script}
<script type="application/vnd.jupyter.widget-state+json">
{json.dumps(state_json, separators=(',', ':'))}
</script>
<script type="application/vnd.jupyter.widget-view+json">
{json.dumps(view_spec, separators=(',', ':'))}
</script>

</body>
</html>
"""
        return template

    def _build_lite_html(
        self,
        *,
        title: str,
        include_controls: bool,
        include_popout: bool,
        messages: list[dict],
        inline_messages: bool,
        runtime_urls: Sequence[str] | None = None,
        host_event_transport: str | None = None,
    ) -> str:
        """Create a lightweight HTML that loads a shared runtime and replays messages."""
        # This HTML is meant to be embedded and load the runtime from the CDN
        # (jsDelivr). Keep it independent from the widget manager to avoid
        # bundling megabytes per example.
        from .._version import __version__ as _pkg_version
        base_version = _pkg_version.split("+", 1)[0]
        runtime_cdn = f"https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@{base_version}/dist/viewer.js"

        ui_config = {
            "show_controls": bool(include_controls),
            "autohide_controls": bool(getattr(self.widget, "autohide_controls", False)),
            "controls_position": list(getattr(self.widget, "controls_position", ["top", "right"])),
            "controls_position_fullscreen": list(getattr(self.widget, "controls_position_fullscreen", ["bottom", "right"])),
            "controls_mode": str(getattr(self.widget, "controls_mode", "classic")),
            "panel_mode_style": str(getattr(self.widget, "panel_mode_style", "drawer")),
            "enable_popout": bool(include_popout),
            "debug_js": bool(getattr(self.widget, "debug_js", False)),
            "runtime_viewer_id": self._binary_viewer_id,
            "runtime_session_id": self._binary_session_id,
        }
        if host_event_transport:
            ui_config["host_event_transport"] = str(host_event_transport)

        messages_json = self._json_for_html_script(messages) if inline_messages else "[]"
        ui_json = self._json_for_html_script(ui_config)

        runtime_candidates = list(runtime_urls or [runtime_cdn])
        runtime_candidates_json = self._json_for_html_script(runtime_candidates)

        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
    #molsysviewer-root {{ width: 100%; height: 100%; min-height: 300px; position: relative; }}
  </style>
</head>
<body>
  <div id="molsysviewer-root"></div>
  <script id="molsysviewer-ui" type="application/json">{ui_json}</script>
  <script id="molsysviewer-messages" type="application/json">{messages_json}</script>
  <script id="molsysviewer-runtime-candidates" type="application/json">{runtime_candidates_json}</script>
  <script type="module">
    const el = document.getElementById("molsysviewer-root");
    const ui = JSON.parse(document.getElementById("molsysviewer-ui").textContent || "{{}}");
    const messages = JSON.parse(document.getElementById("molsysviewer-messages").textContent || "[]");
    const candidates = JSON.parse(document.getElementById("molsysviewer-runtime-candidates").textContent || "[]");

    let lastError = null;
    for (const rel of candidates) {{
      try {{
        const moduleUrl = new URL(rel, window.location.href).href;
        const mod = await import(moduleUrl);
        const boot = mod.bootDocsView || mod.boot_docs_view || mod.default?.bootDocsView;
        if (typeof boot !== "function") {{
          throw new Error("bootDocsView not found in runtime: " + moduleUrl);
        }}
        await boot({{
          el,
          initialMessages: messages,
          ui,
          runtimeUrl: moduleUrl,
        }});
        // Allow Mol* to finish rendering all queued frames before signalling
        // headless screenshot tools (e.g. playwright) that the scene is ready.
        await new Promise(resolve => setTimeout(resolve, 2000));
        el.setAttribute("data-molsysviewer-rendered", "true");
        lastError = null;
        break;
      }} catch (e) {{
        lastError = e;
      }}
    }}
    if (lastError) {{
      console.error("[MolSysViewer docs] Failed to load runtime.", lastError);
      el.textContent = "MolSysViewer failed to load. See console for details.";
    }}
  </script>
</body>
</html>
"""
        return template


# Preserve the historical public module identity for decorated methods.
# Several argument-digestion rules key off `molsysviewer.viewer...` caller paths.
MolSysView.__module__ = "molsysviewer.viewer"
for _name, _value in MolSysView.__dict__.items():
    if callable(_value) and getattr(_value, "__module__", None) == __name__:
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception:
            pass
