"""Studio intentions over the existing Movie API, with one owned host-loop job."""

import asyncio
from concurrent.futures import Future
from copy import deepcopy
from dataclasses import dataclass

from ._movie_baseline import check_idle, observe_movie_scene
from ._movie_endpoint import MOVIE_ENDPOINT, MOVIE_REVISION
from ._movie_timeline import _scene_visibility, _time
from .frontend_requests import FrontendRequestError
from .representations import ALLOWED_REPRESENTATIONS
from .visual_capture import capture_endpoint


class MovieStudioCancelled(FrontendRequestError):
    def __init__(self):
        super().__init__("Movie operation cancelled.", reason="movie_cancelled")


@dataclass
class _Job:
    id: str
    owner: str
    endpoint: str
    action: str
    result: Future
    revision: int | None = None
    handle: object = None
    task: object = None


def _page(value):
    if type(value) is not int or not 0 <= value <= 2**53 - 1:
        raise ValueError("Movie page offsets must be nonnegative integers.")
    return value


def _request_id(content):
    value = content.get("request_id")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Movie operations require a request identifier.")
    return value


class MovieStudio:
    def __init__(self, movie):
        self.movie = movie
        self.active = False
        self.closed = False
        self.job = None
        self.pause_job = None
        self.progress = None
        self.last_output = None

    @property
    def view(self):
        return self.movie._view

    def state(self):
        movie, view = self.movie, self.view
        timeline = movie._timeline
        available = 2 in view._frontend_capabilities.get("visual_state_capture", [])
        require_host = getattr(view.widget, "_require_async_capture_host", None)
        if callable(require_host):
            try:
                require_host()
            except (RuntimeError, FrontendRequestError):
                available = False
        else:
            host = getattr(view.widget, "_callback_host", None)
            if host is not None:
                from ..widget import _callback_host_running

                available = available and _callback_host_running(host)
            else:
                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    available = False
        return {
            "op": "set_movie_state",
            "revision": movie._studio_revision,
            "version": 2 if timeline else 1 if movie._keyframes else None,
            "duration_ms": movie.duration_ms,
            "n_tracks": timeline.n_tracks if timeline else 0,
            "system_loaded": view.molsys is not None,
            "live_available": available,
            "busy": (
                self.job.action
                if self.job
                else "movie_play"
                if movie._playback is not None
                else "movie_export"
                if movie._export_job is not None
                else "movie_capture"
                if movie._seek_request is not None
                else None
            ),
            "job_id": self.job.id if self.job else None,
            "progress": deepcopy(self.progress),
            "last_output": deepcopy(self.last_output),
        }

    def publish(self):
        if self.active and not self.closed and not self.view.closed and self.view._ready:
            self.view._send_runtime_only(self.state())

    def _owner(self, content):
        host = f"widget-host:{self.view._binary_session_id}"
        owner = content.get("_studio_owner_endpoint_id", "primary")
        if owner in ("primary", host):
            return "primary", host
        if not isinstance(owner, str) or owner not in self.view._endpoint_transfers.modes:
            raise FrontendRequestError(reason="endpoint_closed")
        return owner, owner

    def inspect(self, content):
        _, owner = self._owner(content)
        self.active = True
        state = self.state()
        offset, key_offset = _page(content.get("offset", 0)), _page(content.get("key_offset", 0))
        tracks = self.movie._timeline._data["tracks"] if self.movie._timeline else []
        selected = next((row for row in tracks if row["tag"] == content.get("tag")), None)
        state["editor"] = {
            "offset": offset,
            "tracks": [
                {key: deepcopy(value) for key, value in row.items() if key != "keys"} | {"n_keys": len(row["keys"])}
                for row in tracks[offset : offset + 20]
            ],
            "track": (
                {
                    **{key: deepcopy(value) for key, value in selected.items() if key != "keys"},
                    "keys": deepcopy(selected["keys"][key_offset : key_offset + 100]),
                    "key_offset": key_offset,
                    "n_keys": len(selected["keys"]),
                }
                if selected
                else None
            ),
        }
        state["request_id"] = content.get("request_id")
        targets = (
            list(_scene_visibility(self.movie._timeline._data["baseline"]["scene"])) if self.movie._timeline else []
        )
        state["editor"]["representations"] = sorted(ALLOWED_REPRESENTATIONS)
        state["editor"]["targets"] = [
            {"domain": domain, **({"tag": tag} if tag is not None else {})} for domain, tag in targets[:100]
        ]
        state["editor"]["target_count"] = len(targets)
        state["target_endpoint_id"] = owner
        self.view._send_runtime_only(state)

    def _editable(self, content):
        if type(content.get("revision")) is not int or content["revision"] != self.movie._studio_revision:
            raise ValueError("The Movie changed. Refresh the editor before applying this draft.")
        if self.job is not None:
            raise FrontendRequestError(reason="movie_operation_pending")
        check_idle(self.movie)

    def _set_key(self, content, value):
        timeline = self.movie._require_timeline()
        tag, at = content.get("tag"), _time(content.get("time_ms"), "Key time", timeline.duration_ms)
        tracks = timeline.track_records()
        track = next((row for row in tracks if row["tag"] == tag), None)
        if track is None:
            track = {"tag": tag, "target": content.get("target"), "property": content.get("property"), "keys": []}
        elif track["target"] != content.get("target") or track["property"] != content.get("property"):
            raise ValueError("This track already addresses another target or property. Choose a different name.")
        key = {"time_ms": at, "value": value, "easing": content.get("easing", "linear")}
        exists = any(row["time_ms"] == at for row in track["keys"])
        if exists and content.get("replace") is not True:
            raise ValueError("A key already exists at this time. Confirm replacement or choose another time.")
        # Let the public Movie validator own time, target, property and value admission.
        keys = [row for row in track["keys"] if row["time_ms"] != at] + [key]
        if not isinstance(at, (int, float)) or isinstance(at, bool):
            raise ValueError("Movie key time must be a number in milliseconds.")
        keys.sort(key=lambda row: row["time_ms"])
        if any(row["tag"] == tag for row in tracks):
            self.movie.update_track(tag, keys=keys)
        else:
            self.movie.add_track({**track, "keys": keys})

    def edit(self, content):
        self._owner(content)
        self._editable(content)
        action = content["action"]
        if action == "movie_set_duration":
            self.movie.set_duration(content.get("duration_ms"))
        elif action == "movie_clear":
            if content.get("confirmed") is not True:
                raise ValueError("Confirm removal of the Movie plan. The scene will be kept.")
            self.movie.clear()
        elif action == "movie_set_key":
            self._set_key(content, content.get("value"))
        elif action == "movie_remove_track":
            if content.get("confirmed") is not True:
                raise ValueError("Confirm removal of the Movie track.")
            self.movie.remove_track(content.get("tag"))
        elif action == "movie_remove_key":
            timeline = self.movie._require_timeline()
            track = next((row for row in timeline.track_records() if row["tag"] == content.get("tag")), None)
            if track is None:
                raise ValueError("Choose an existing Movie track.")
            at = _time(content.get("time_ms"), "Key time", timeline.duration_ms)
            keys = [row for row in track["keys"] if row["time_ms"] != at]
            if len(keys) == len(track["keys"]):
                raise ValueError("Choose an existing Movie key.")
            self.movie.update_track(track["tag"], keys=keys)
        self.publish()

    async def _capture_key(self, content):
        movie = self.movie
        observation = await observe_movie_scene(movie, timeout=5.0, require_baseline=True)
        with self.view._system_edits._locked():
            observation.validate(movie, delivery=True)
            if content["revision"] != movie._studio_revision:
                raise ValueError("The Movie changed during capture. The draft was not applied.")
            prop = content.get("property")
            if prop not in {"pose", "index"}:
                raise ValueError("Live Movie keys capture a camera pose or a structure index.")
            state = observation.captured.state["view"]
            self._set_key(content, state["camera"] if prop == "pose" else state["structure_index"])

    def start(self, content):
        owner, _ = self._owner(content)
        self._editable(content)
        endpoint = capture_endpoint(self.view, content.get("_capture_endpoint_id"))
        request_id = _request_id(content)
        if content["action"] == "movie_start" and (self.movie._timeline or self.movie._keyframes):
            if content.get("confirmed") is not True:
                raise ValueError("Confirm starting a new Movie before replacing the current plan.")
        job = _Job(request_id, owner, endpoint, content["action"], Future(), content["revision"])
        self.job, self.progress, self.last_output = job, None, None
        self._schedule(job, lambda: self._operation(content), primary=True)
        self.publish()
        return job.result

    async def _operation(self, content):
        movie, action = self.movie, content["action"]
        if action == "movie_start":
            return await movie.capture_baseline_async(content.get("duration_ms"))
        if action == "movie_capture_key":
            return await self._capture_key(content)
        if action == "movie_seek":
            return await movie.seek_async(content.get("time_ms"))
        if action == "movie_play":
            return await movie.play_async(loop=content.get("loop", False), start_time_ms=content.get("time_ms", 0))
        if action == "movie_reset":
            if content.get("confirmed") is not True:
                raise ValueError("Confirm restoration of the recorded Movie scene.")
            return await movie.reset_async()
        if action == "movie_export":

            def progress(record):
                self.progress = deepcopy(record)
                self.publish()

            return await movie.export_async(
                content.get("path"),
                fps=content.get("fps", 25),
                width_px=content.get("width_px", 1280),
                height_px=content.get("height_px", 720),
                overwrite=content.get("overwrite", False),
                include_overlays=content.get("include_overlays", True),
                on_progress=progress,
            )
        raise ValueError("Unsupported live Movie action.")

    def _schedule(self, job, operation, *, primary):
        async def run():
            token = MOVIE_ENDPOINT.set(job.endpoint)
            revision_token = MOVIE_REVISION.set(job.revision)
            try:
                value = await operation()
                if not job.result.done():
                    if job.action == "movie_export":
                        self.last_output = {key: value[key] for key in ("path", "bytes")}
                    job.result.set_result(None)
            except asyncio.CancelledError:
                if not job.result.done():
                    job.result.set_exception(MovieStudioCancelled())
            except BaseException as error:
                if not job.result.done():
                    job.result.set_exception(error)
                if not isinstance(error, Exception):
                    raise
            finally:
                MOVIE_ENDPOINT.reset(token)
                MOVIE_REVISION.reset(revision_token)
                if primary and self.job is job:
                    self.job = None
                if self.pause_job is job:
                    self.pause_job = None
                self.publish()

        def begin():
            job.handle = None
            if self.closed or job.result.done():
                return
            try:
                loop = asyncio.get_running_loop()
                require_host = getattr(self.view.widget, "_require_async_capture_host", None)
                if callable(require_host):
                    require_host()
                job.task = loop.create_task(run())
            except Exception as error:
                if primary and self.job is job:
                    self.job = None
                if self.pause_job is job:
                    self.pause_job = None
                job.result.set_exception(error)
                self.publish()

        try:
            job.handle = self.view.widget._schedule_callback(0, begin)
        except BaseException:
            if primary and self.job is job:
                self.job = None
            if self.pause_job is job:
                self.pause_job = None
            raise

    def pause(self, content):
        owner, _ = self._owner(content)
        if self.pause_job is not None:
            raise FrontendRequestError(reason="movie_operation_pending")
        job = _Job(_request_id(content), owner, "primary", "movie_pause", Future())
        self.pause_job = job
        self._schedule(job, self.movie.pause_async, primary=False)
        return job.result

    def cancel(self, content):
        self._owner(content)
        if self.job is None or self.job.id != content.get("job_id"):
            raise ValueError("This Movie operation has already finished.")
        self._cancel(self.job)

    def _cancel(self, job):
        if job.handle is not None:
            job.handle.cancel()
            job.handle = None
            if self.job is job:
                self.job = None
            if self.pause_job is job:
                self.pause_job = None
            job.result.set_exception(MovieStudioCancelled())
        if job.task is not None:
            job.task.get_loop().call_soon_threadsafe(job.task.cancel)
        self.publish()

    def cancel_endpoint(self, endpoint):
        for job in (self.job, self.pause_job):
            if job is not None and endpoint in {job.owner, job.endpoint}:
                self._cancel(job)

    def close(self):
        self.closed = True
        for job in (self.job, self.pause_job):
            if job is not None:
                self._cancel(job)


def movie_action(view, content):
    content = deepcopy(dict(content))
    owner = view.movie._studio_owner()
    action = content["action"]
    if action == "movie_inspect":
        return owner.inspect(content)
    if action in {"movie_set_duration", "movie_clear", "movie_set_key", "movie_remove_track", "movie_remove_key"}:
        return owner.edit(content)
    if action == "movie_pause":
        return owner.pause(content)
    if action == "movie_cancel":
        return owner.cancel(content)
    return owner.start(content)
