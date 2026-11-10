"""Host-owned presentation of independent, provider-initialized Views.

This registry contains live Views, never arbitrary scientific results. Providers
retain their native results until preparation succeeds and choose presentation
explicitly. Browser windows remain connected to the originating kernel.
"""

from secrets import token_urlsafe
from weakref import ref

import anywidget
import traitlets as T
from smonitor import signal

from ._private.argdigest import digest
from .widget import _WIDGET_BOOTSTRAP_ESM, MolSysViewerWidget

# Presented Views outlive the source View/panel. Explicit close releases this
# root; a closed result must never keep its source molecular data alive.
_OPEN_PRESENTATIONS = {}


class _PresentationSurface(anywidget.AnyWidget):
    _esm = _WIDGET_BOOTSTRAP_ESM
    runtime_entrypoint = T.Unicode("presentationSurface").tag(sync=True)
    runtime_bundle_digest = T.Unicode(MolSysViewerWidget._viewer_js_digest).tag(sync=True)
    source_id = T.Unicode().tag(sync=True)
    items = T.List(default_value=[]).tag(sync=True)
    source_closed = T.Bool(False).tag(sync=True)

    def __init__(self, owner, **kwargs):
        super().__init__(**kwargs)
        self._owner = owner
        self.layout.width = "100%"
        self.layout.height = "auto"
        self.on_msg(self._route)

    def _route(self, widget, content, buffers):
        if not isinstance(content, dict):
            return
        if content.get("event") == "request_widget_runtime_source":
            self.send({"op": "widget_runtime_source", "source": MolSysViewerWidget._viewer_js_source})
        elif content.get("type") == "show":
            request = content.get("request_id")
            try:
                self._owner._show(
                    content.get("id"), content.get("destination"), request=request, client_id=content.get("client_id")
                )
            except Exception as exc:
                self.send(
                    {
                        "type": "response",
                        "request_id": request,
                        "client_id": content.get("client_id"),
                        "error": str(exc)[:1000],
                    }
                )
        elif content.get("type") == "shown":
            self._owner._ack(content)
        elif content.get("type") == "close":
            self._owner.close(content.get("id"))


class ViewPresentations:
    """Per-source host service at ``view.addons.manager.presentations``.

    ``prepare`` initializes a correctly transported new View without displaying
    it. ``get`` recovers that View in Python; expert scientific wrappers remain
    headless. A GUI destination is selected only after preparation completes.
    """

    def __init__(self, view):
        self._source = ref(view)
        self._records = {}
        self._output = None

    @property
    def destinations(self):
        """The presentation destinations implemented by this source's host."""
        source = self._source()
        if source is None or source.closed:
            return ()
        if callable(getattr(source, "_independent_view_factory", None)):
            return ("window",)
        return ("notebook", "window") if isinstance(source.widget, MolSysViewerWidget) else ()

    def _surface(self):
        if self._output is None:
            view = self._source()
            if view is None or view.closed or not isinstance(view.widget, MolSysViewerWidget):
                raise RuntimeError("This view has no live notebook presentation surface.")
            self._output = _PresentationSurface(self, source_id=view.widget.model_id)
            view.widget.presentation_host_id = self._output.model_id
        return self._output

    @signal(tags=["viewer", "presentation"])
    @digest()
    def prepare(self, initializer, *, title="Molecular result", skip_digestion=False):
        """Initialize a new host-compatible View and return its opaque handle.

        ``initializer(view)`` must populate the supplied View synchronously,
        without displaying it or starting an event loop. Failure closes partial
        resources. Each unpresented handle must be explicitly discarded/closed
        by its provider when its task is abandoned.
        """
        source = self._source()
        if source is None or source.closed:
            raise RuntimeError("Cannot create a result from a closed view.")
        if not callable(initializer):
            raise TypeError("initializer must be callable.")
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise ValueError("title must contain between 1 and 200 characters.")
        factory = getattr(source, "_independent_view_factory", None)
        runtime = None
        if callable(factory):
            runtime = factory(title.strip())
            child = runtime["view"]
        elif isinstance(source.widget, MolSysViewerWidget):
            from .viewer.core import MolSysView

            child = MolSysView()
        else:
            raise RuntimeError("This host does not support independent result views.")
        try:
            initialized = initializer(child)
            if initialized is not None and initialized is not child:
                raise TypeError("initializer must populate the supplied View and return it or None.")
            if source.closed or child.closed:
                raise RuntimeError("The source or result closed during preparation.")
        except BaseException:
            child.close()
            if runtime is not None:
                dispose = getattr(runtime["window"], "_molsysviewer_dispose", None)
                if callable(dispose):
                    dispose()
                else:
                    runtime["window"].close()
            raise
        handle = token_urlsafe(24)
        record = {
            "view": child,
            "runtime": runtime,
            "title": title.strip(),
            "destination": None,
            "state": "prepared",
            "error": "",
            "request": None,
        }
        self._records[handle] = record
        child._close_callbacks.append(lambda: self._release(handle))
        return handle

    @signal(tags=["viewer", "presentation"])
    @digest()
    def get(self, presentation_id, *, skip_digestion=False):
        """Return the independent View for an existing handle."""
        return self._record(presentation_id)["view"]

    @signal(tags=["viewer", "presentation"])
    @digest()
    def records(self, *, skip_digestion=False):
        """Return metadata, without scientific arrays, for this source's live Views."""
        return [
            {"id": key, **{k: value[k] for k in ("title", "state", "destination", "error")}}
            for key, value in self._records.items()
        ]

    @signal(tags=["viewer", "presentation"])
    @digest()
    def close(self, presentation_id, *, skip_digestion=False):
        """Idempotently close a result and release its widgets/native window."""
        record = self._records.get(presentation_id)
        if record is not None:
            record["view"].close()

    def _record(self, handle):
        if not isinstance(handle, str) or handle not in self._records:
            raise ValueError("This result view is no longer available.")
        return self._records[handle]

    def _show(self, handle, destination, *, request=None, client_id=None):
        record = self._record(handle)
        if destination not in {"notebook", "window"}:
            raise ValueError("Choose notebook or window as the destination.")
        runtime = record["runtime"]
        if runtime is not None:
            if destination != "window":
                raise ValueError("The desktop host presents results in a new window.")
            runtime["window"].show()
            runtime["window"].raise_()
            runtime["window"].activateWindow()
            record.update(destination=destination, state="shown", error="")
            _OPEN_PRESENTATIONS[handle] = self
            return
        self._surface()
        record.update(destination=destination, state="opening", error="", request=request, client_id=client_id)
        _OPEN_PRESENTATIONS[handle] = self
        self._publish()

    def _publish(self):
        if self._output is not None:
            self._output.items = [
                {
                    "id": key,
                    "title": record["title"],
                    "model_id": record["view"].addons.manager.presentations._surface().model_id,
                    "destination": record["destination"],
                    "request_id": record["request"],
                    "client_id": record.get("client_id"),
                }
                for key, record in self._records.items()
                if record["destination"] is not None
            ]

    def _ack(self, content):
        record = self._records.get(content.get("id"))
        if (
            record is None
            or content.get("request_id") != record["request"]
            or content.get("client_id") != record.get("client_id")
        ):
            return
        error = content.get("error")
        record.update(state="error" if error else "shown", error=str(error or "")[:1000])
        if error:
            record["destination"] = None
            _OPEN_PRESENTATIONS.pop(content["id"], None)
            self._publish()
        self._output.send(
            {
                "type": "response",
                "request_id": record["request"],
                "client_id": record.get("client_id"),
                "error": record["error"],
                "notice": str(content.get("notice") or "")[:200],
            }
        )

    def _release(self, handle):
        record = self._records.pop(handle, None)
        _OPEN_PRESENTATIONS.pop(handle, None)
        if record is not None and record["runtime"] is not None:
            window = record["runtime"]["window"]
            dispose = getattr(window, "_molsysviewer_dispose", None)
            if callable(dispose):
                dispose()
            else:
                window.close()
                window.deleteLater()
        self._publish()
        source = self._source()
        if source is not None and not source.closed:
            for _, _, panel in list(source._active_panel_widgets.values()):
                panel.send({"type": "presentation_closed", "id": handle})
        if not self._records and (source is None or source.closed):
            self._close_surface()

    def _source_closed(self):
        for handle, record in list(self._records.items()):
            if record["destination"] is None:
                self.close(handle)
        if self._output is not None:
            self._output.source_closed = True
        if not self._records:
            self._close_surface()

    def _close_surface(self):
        if self._output is not None:
            output, self._output = self._output, None
            output.close()
            output.layout.close()
