"""One-frame-at-a-time Movie encoding with explicit ownership and publication."""

import asyncio
import base64
import binascii
import inspect
import io
import json
import math
import os
import struct
import tempfile
import time
import zipfile
from copy import deepcopy
from numbers import Real
from pathlib import Path
from uuid import uuid4

from ._movie_composition import checked_composition, overlay_requirements, overlay_revisions, overlays_unchanged
from ._movie_encoder import codec_candidates
from ._movie_encoder import encoder as _encoder
from ._movie_endpoint import check_movie_revision
from ._movie_playback import _revisions
from ._movie_sampling import _MovieSampling
from ._movie_seek import seek_movie
from .frontend_requests import FrontendRequestError
from .visual_capture import _capture_owned_call, live_capture_version


def _dimensions(width, height):
    if any(type(value) is not int or not 16 <= value <= 8192 for value in (width, height)) or width * height > 2**24:
        raise ValueError("Movie dimensions must be integers from 16 to 8192, with at most 16 megapixels.")
    return width, height


def _png(data_uri, width, height):
    prefix = "data:image/png;base64,"
    if (
        not isinstance(data_uri, str)
        or not data_uri.startswith(prefix)
        or len(data_uri) > 4 * width * height * 2 + 65536
    ):
        raise ValueError("Movie capture did not return a bounded PNG image.")
    try:
        blob = base64.b64decode(data_uri[len(prefix) :], validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError("Movie capture returned invalid PNG encoding.") from error
    if (
        len(blob) < 33
        or blob[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        or struct.unpack(">II", blob[16:24]) != (width, height)
    ):
        raise ValueError("Movie capture PNG dimensions do not match the requested frame.")
    return blob


def _visible_overlays(view, scene):
    result = [str(card["tag"]) for card in scene.get("trajectory_plots", []) if card.get("visible", True)]
    if view._scene_look.get("legend", {}).get("options", {}).get("items"):
        result.append("colour-legend")
    return result


def _escape_metadata(value):
    for char in ("\\", "=", ";", "#", "\n"):
        value = value.replace(char, "\\" + char)
    return value


class _MovieExport:
    def __init__(self, movie, sampling, width, height, include_overlays, sample_level):
        view = movie._view
        check_movie_revision(movie)
        live_capture_version(view, required=2)
        if 1 not in view._frontend_capabilities.get("movie_frame_capture", []):
            raise FrontendRequestError(reason="movie_export_not_supported")
        if (
            movie._export_job is not None
            or movie._playback is not None
            or movie._seek_request is not None
            or view._movie_export_frames is not None
        ):
            raise FrontendRequestError(reason="movie_operation_pending")
        self.timeline = movie._require_timeline()
        if self.timeline.has_appearance and 1 not in view._frontend_capabilities.get("movie_appearance", []):
            raise FrontendRequestError(reason="movie_appearance_not_supported")
        scene = view.export_state(skip_digestion=True)
        self.timeline.check_binding(view._source_state_binding(), scene)
        self.timeline.check_scene(scene)
        excluded = _visible_overlays(view, scene)
        required, context = overlay_requirements(view, scene)
        self.required_overlays = required if include_overlays else []
        if self.required_overlays and not any(
            type(version) is int and version == 1
            for version in view._frontend_capabilities.get("movie_overlay_capture", [])
        ):
            raise FrontendRequestError(reason="movie_overlay_capture_not_supported")
        self.overlay_revision = overlay_revisions(view)
        self.id = uuid4().hex
        self.revisions = _revisions(view)
        self.manifest = {
            "schema": "molsysviewer.movie_export@1",
            "job_id": self.id,
            "status": "completed",
            "sampling": sampling.record(),
            "resolution": {"width": width, "height": height},
            "rendering": {"antialiasing": "molstar-multisample", "sample_level": sample_level},
            "composition": {
                "source": "molecular-canvas",
                "native_annotations": True,
                "authoring_controls": False,
                "dom_overlays": "svg-composited@1"
                if self.required_overlays
                else "none-visible"
                if include_overlays
                else "explicitly-excluded",
                "included_dom_overlays": deepcopy(self.required_overlays),
                "excluded_dom_overlays": [] if include_overlays else excluded,
                "source_context": context,
            },
            "recipe": self.timeline.to_dict(),
        }
        from .._version import __version__

        self.manifest["runtime"] = {
            "molsysviewer": __version__,
            "movie_recipe_version": 2,
            "movie_frame_capture_version": 1,
            "configured_bundle_sha256": view.widget.runtime_bundle_digest,
        }

    def validate(self, movie):
        live_capture_version(movie._view, required=2)
        if (
            movie._export_job is not self
            or movie._timeline is not self.timeline
            or self.revisions != _revisions(movie._view)
            or not overlays_unchanged(movie._view, self.overlay_revision)
        ):
            raise FrontendRequestError(reason="movie_export_superseded")


class _FrameSink:
    def __init__(self, directory, format, width, height, sampling, manifest, executable):
        self.directory, self.format = directory, format
        self.width, self.height, self.sampling = width, height, sampling
        self.manifest, self.executable = manifest, executable
        self.path = directory / ("output.zip" if format == "pngs" else f"output.{format}")
        self.process = None
        self.archive = None
        self.diagnostics = None

    async def open(self, timeout):
        if self.format == "pngs":
            self.archive = zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_STORED)
            return
        rate = self.sampling.rate
        codec = self.manifest["encoder"]["codec"]
        self.manifest["encoder"].update(codec=codec, pixel_format="yuv420p", threads=1)
        self.manifest["encoder"]["color"] = {
            "input": "srgb",
            "primaries": "bt709",
            "transfer": "iec61966-2-1",
            "matrix": "bt709",
            "range": "limited",
        }
        if self.format == "mp4":
            self.manifest["encoder"].update(crf=18, preset="medium", faststart=True)
        else:
            self.manifest["encoder"].update(crf=30, target_bitrate=0, row_multithreading=False)
            if codec == "libaom-av1":
                self.manifest["encoder"]["cpu_used"] = 6
        metadata = self.directory / "metadata.txt"
        metadata.write_text(
            ";FFMETADATA1\ncomment="
            + _escape_metadata(json.dumps(self.manifest, separators=(",", ":"), allow_nan=False))
            + "\n",
            encoding="utf-8",
        )
        command = [
            self.executable,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-threads",
            "1",
            "-filter_threads",
            "1",
            "-f",
            "rawvideo",
            "-pixel_format",
            "rgb24",
            "-video_size",
            f"{self.width}x{self.height}",
            "-framerate",
            f"{rate.numerator}/{rate.denominator}",
            "-i",
            "pipe:0",
            "-f",
            "ffmetadata",
            "-i",
            str(metadata),
            "-map",
            "0:v:0",
            "-map_metadata",
            "1",
            "-an",
            "-c:v",
            codec,
            "-threads",
            "1",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            "scale=out_color_matrix=bt709:out_range=tv",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "iec61966-2-1",
            "-colorspace",
            "bt709",
            "-color_range",
            "tv",
        ]
        if self.format == "mp4":
            command += ["-crf", "18", "-preset", "medium", "-movflags", "+faststart"]
        else:
            command += ["-crf", "30", "-b:v", "0", "-row-mt", "0"]
            if codec == "libaom-av1":
                command += ["-cpu-used", "6"]
        command.append(str(self.path))
        self.diagnostics = (self.directory / "encoder.log").open("wb")
        self.process = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *command, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.DEVNULL, stderr=self.diagnostics
            ),
            timeout,
        )

    async def append(self, blob, index, timeout):
        if self.archive is not None:
            # Decode/verify the PNG even for lossless export; arbitrary bytes
            # with a plausible IHDR must not become successful frame output.
            self._rgb(blob)
            self.archive.writestr(f"frames/{index:08d}.png", blob)
            return
        rgb = self._rgb(blob)
        deadline = asyncio.get_running_loop().time() + timeout
        try:
            for begin in range(0, len(rgb), 65536):
                self.process.stdin.write(rgb[begin : begin + 65536])
                await asyncio.wait_for(self.process.stdin.drain(), max(0, deadline - asyncio.get_running_loop().time()))
        except (BrokenPipeError, ConnectionResetError) as error:
            raise RuntimeError("Movie encoder rejected the frame stream.") from error

    def _rgb(self, blob):
        import imageio.v2 as imageio

        image = imageio.imread(io.BytesIO(blob), format="png")
        if image.shape != (self.height, self.width, 3) or image.dtype.name != "uint8":
            # Mol* opaque PNGs commonly contain an opaque alpha channel.
            if (
                image.shape != (self.height, self.width, 4)
                or image.dtype.name != "uint8"
                or not (image[:, :, 3] == 255).all()
            ):
                raise ValueError("Movie requires opaque 8-bit RGB/RGBA PNG frames.")
            image = image[:, :, :3]
        return image.tobytes()

    async def finish(self, timeout):
        if self.archive is not None:
            self.archive.writestr("manifest.json", json.dumps(self.manifest, indent=2, allow_nan=False))
            self.archive.close()
            self.archive = None
        else:
            self.process.stdin.close()
            await asyncio.wait_for(self.process.wait(), timeout)
            if self.process.returncode:
                raise RuntimeError("Movie encoder failed to finish the output.")
        if not self.path.is_file() or not self.path.stat().st_size:
            raise RuntimeError("Movie encoder produced no output.")

    async def close(self):
        if self.archive is not None:
            self.archive.close()
        if self.process is not None and self.process.returncode is None:
            if self.process.stdin is not None:
                self.process.stdin.close()
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(self.process.wait(), 2)
            except TimeoutError:
                try:
                    self.process.kill()
                except ProcessLookupError:
                    pass
                await self.process.wait()
        if self.diagnostics is not None:
            self.diagnostics.close()


async def export_movie(
    movie,
    path,
    *,
    fps,
    width_px,
    height_px,
    sample_level,
    format,
    overwrite,
    include_overlays,
    timeout,
    on_progress,
    codec="auto",
):
    selected_format = format or {".html": "html", ".htm": "html", ".zip": "pngs", ".mp4": "mp4", ".webm": "webm"}.get(
        Path(path).suffix.lower()
    )
    codec_candidates(selected_format, codec)
    if selected_format == "html":
        from ._movie_web import export_movie_web

        return await export_movie_web(
            movie,
            path,
            width=width_px,
            height=height_px,
            overwrite=overwrite,
            include_overlays=include_overlays,
            timeout=timeout,
            on_progress=on_progress,
        )
    from depdigest import dep_digest

    @dep_digest("imageio")
    def require_images():
        import imageio

        return imageio.__version__

    require_images()
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, Real)
        or not math.isfinite(timeout)
        or not 0 < timeout <= 300
    ):
        raise ValueError("Movie frame/encoder timeout must be in (0, 300] seconds.")
    if type(sample_level) is not int or not 0 <= sample_level <= 5:
        raise ValueError("Movie sample_level must be an integer from 0 to 5.")
    if type(overwrite) is not bool or type(include_overlays) is not bool:
        raise ValueError("Movie overwrite/include_overlays must be booleans.")
    width, height = _dimensions(width_px, height_px)
    path = Path(path).expanduser().absolute()
    format = selected_format
    if format not in {"mp4", "webm", "pngs"}:
        raise ValueError("Version-2 Movie export supports mp4, webm or pngs (a ZIP archive).")
    if format != "pngs" and (width % 2 or height % 2):
        raise ValueError("Video dimensions must be even; Movie never silently resizes frames.")
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    if not path.parent.is_dir():
        raise FileNotFoundError(path.parent)
    timeline = movie._require_timeline()
    sampling = _MovieSampling(timeline.duration_ms, fps)
    view = movie._view
    require_host = getattr(view.widget, "_require_async_capture_host", None)
    if callable(require_host):
        require_host()
    executable, encoder = await _encoder(format, timeout, codec)
    job = None
    sink = None

    def begin():
        nonlocal job
        if movie._timeline is not timeline:
            raise FrontendRequestError(reason="movie_export_superseded")
        job = _MovieExport(movie, sampling, width, height, include_overlays, sample_level)
        job.manifest["encoder"] = encoder
        movie._export_job = job
        movie._studio_runtime_changed()

    try:
        await _capture_owned_call(view, begin, deadline=time.monotonic() + timeout)
        with tempfile.TemporaryDirectory(dir=path.parent, prefix=f".{path.name}.movie-") as directory:
            sink = _FrameSink(Path(directory), format, width, height, sampling, job.manifest, executable)
            try:
                for index in range(sampling.count):

                    def check():
                        job.validate(movie)

                    await _capture_owned_call(view, check, deadline=time.monotonic() + timeout)
                    sample, captured = await seek_movie(
                        movie,
                        sampling.time_ms(index),
                        timeout=timeout,
                        export_job=job,
                        movie_frame={
                            "job_id": job.id,
                            "frame_index": index,
                            "width": width,
                            "height": height,
                            "include_overlays": include_overlays,
                            "sample_level": sample_level,
                            **(
                                {"overlay_capture_version": 1, "required_overlays": deepcopy(job.required_overlays)}
                                if job.required_overlays
                                else {}
                            ),
                        },
                    )
                    if job.required_overlays:
                        layout = checked_composition(captured.get("composition"), job.required_overlays, width, height)
                        if index == 0:
                            job.manifest["composition"]["layout"] = layout
                        elif layout != job.manifest["composition"]["layout"]:
                            raise ValueError(
                                "Movie overlay layout or style changed during export; keep its canvas and cards fixed."
                            )
                    blob = _png(captured["data_uri"], width, height)
                    if index == 0:
                        # Video metadata must already include the actual applied
                        # overlay layout when FFmpeg reads its first frame.
                        await sink.open(timeout)
                    await sink.append(blob, index, timeout)
                    if on_progress is not None:

                        def progress(index=index, sample=sample):
                            job.validate(movie)
                            value = on_progress(
                                {
                                    "job_id": job.id,
                                    "frame_index": index,
                                    "frames_written": index + 1,
                                    "total_frames": sampling.count,
                                    "time_ms": sample["time_ms"],
                                }
                            )
                            if inspect.isawaitable(value):
                                if inspect.iscoroutine(value):
                                    value.close()
                                raise ValueError("Movie on_progress must be synchronous.")

                        await _capture_owned_call(view, progress, deadline=time.monotonic() + timeout)
                await sink.finish(timeout)

                def publish():
                    job.validate(movie)
                    # Linking within the destination filesystem is an atomic
                    # no-clobber publication, including a late-created target.
                    if overwrite:
                        os.replace(sink.path, path)
                    else:
                        os.link(sink.path, path)
                    return {"path": str(path), "manifest": deepcopy(job.manifest), "bytes": path.stat().st_size}

                return await _capture_owned_call(view, publish, deadline=time.monotonic() + timeout)
            finally:
                if sink is not None:
                    await sink.close()
    finally:
        if movie._export_job is job:
            movie._export_job = None
            movie._studio_runtime_changed()
