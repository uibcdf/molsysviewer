"""One-frame-at-a-time Movie encoding with explicit ownership and publication."""

import asyncio
import base64
import binascii
import hashlib
import inspect
import io
import json
import math
import os
import shutil
import struct
import tempfile
import time
import zipfile
from copy import deepcopy
from numbers import Real
from pathlib import Path
from uuid import uuid4

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
        if include_overlays and excluded:
            raise ValueError(
                "Visible trajectory plot overlays cannot yet be composed into Movie output. Hide them or explicitly choose include_overlays=False."
            )
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
                "dom_overlays": "refuse-visible" if include_overlays else "explicitly-excluded",
                "excluded_dom_overlays": excluded,
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
        codec = "libx264" if self.format == "mp4" else "libvpx-vp9"
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


async def _encoder(format, timeout):
    if format == "pngs":
        return None, {"name": "PNG/ZIP", "threads": 1}
    from depdigest import dep_digest

    @dep_digest("imageio_ffmpeg")
    def locate():
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe(), imageio_ffmpeg.__version__

    executable, version = locate()
    resolved = Path(shutil.which(executable) or executable)
    with resolved.open("rb") as binary:
        binary_digest = hashlib.file_digest(binary, "sha256").hexdigest()
    # Native version output is tiny and bounded; no user command shell is used.
    process = await asyncio.wait_for(
        asyncio.create_subprocess_exec(
            executable, "-version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
        ),
        timeout,
    )
    try:
        output, _ = await asyncio.wait_for(process.communicate(), timeout)
        if process.returncode:
            raise RuntimeError("Movie encoder is unavailable.")
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()
    return executable, {
        "name": "FFmpeg",
        "provider": "imageio-ffmpeg",
        "provider_version": version,
        "executable_sha256": binary_digest,
        "version": output.decode(errors="replace").splitlines()[0][:512],
    }


async def export_movie(
    movie, path, *, fps, width_px, height_px, sample_level, format, overwrite, include_overlays, timeout, on_progress
):
    selected_format = format or {".html": "html", ".htm": "html"}.get(Path(path).suffix.lower())
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
    format = format or {".zip": "pngs", ".mp4": "mp4", ".webm": "webm"}.get(path.suffix.lower())
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
    executable, encoder = await _encoder(format, timeout)
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
                await sink.open(timeout)
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
                        },
                    )
                    blob = _png(captured["data_uri"], width, height)
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
