"""Bounded inspection and explicit codec selection for the selected FFmpeg."""

from __future__ import annotations

import asyncio
import hashlib
import re
import shutil
from pathlib import Path

from smonitor.integrations import CatalogException

from .._private.smonitor import CATALOG, META

_CODECS = {"h264": "libx264", "vp9": "libvpx-vp9", "av1": "libaom-av1"}
_CONTAINERS = {"mp4": ("h264",), "webm": ("vp9", "av1")}


class _MovieCodecUnavailable(CatalogException, RuntimeError):
    catalog_key = "movie_codec_unavailable"

    def __init__(self, format, codec, required):
        super().__init__(
            None,
            catalog=CATALOG,
            meta=META,
            extra={"format": format, "codec": codec, "required_encoders": ", ".join(required)},
        )


class _MovieEncoderProbeFailed(CatalogException, RuntimeError):
    catalog_key = "movie_encoder_probe_failed"

    def __init__(self, reason):
        super().__init__(None, catalog=CATALOG, meta=META, extra={"reason": reason})


def codec_candidates(format, codec):
    """Keep container, requested codec and actual native implementation distinct."""
    if not isinstance(codec, str) or codec not in {"auto", *_CODECS}:
        raise ValueError("Movie codec must be auto, h264, vp9 or av1.")
    if format in {"pngs", "html"}:
        if codec != "auto":
            raise ValueError("Movie codec applies only to MP4/WebM; use auto for PNG/HTML.")
        return ()
    if format not in _CONTAINERS:
        raise ValueError("Movie format must be mp4, webm, pngs or html.")
    allowed = _CONTAINERS[format]
    if codec != "auto" and codec not in allowed:
        raise ValueError(f"Movie codec {codec} is incompatible with {format}.")
    return tuple(_CODECS[name] for name in (allowed if codec == "auto" else (codec,)))


def select_codec(format, codec, available):
    candidates = codec_candidates(format, codec)
    for candidate in candidates:
        if candidate in available:
            return candidate
    raise _MovieCodecUnavailable(format, codec, candidates)


def video_encoders(listing):
    if b"Encoders:" not in listing:
        raise _MovieEncoderProbeFailed("invalid_encoder_listing")
    return {name.decode("ascii") for name in re.findall(rb"^\s*V\S{5}\s+([a-zA-Z0-9_-]+)\s", listing, re.MULTILINE)}


async def _bounded_read(stream, limit):
    chunks, size = [], 0
    while chunk := await stream.read(min(16384, limit + 1 - size)):
        size += len(chunk)
        if size > limit:
            raise _MovieEncoderProbeFailed("output_limit")
        chunks.append(chunk)
    return b"".join(chunks)


async def run_encoder_probe(executable, arguments, timeout):
    """Retire only this subprocess, including on output overflow or cancellation."""
    process, tasks = None, []
    try:
        async with asyncio.timeout(timeout):
            process = await asyncio.create_subprocess_exec(
                executable,
                *arguments,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            tasks = [
                asyncio.create_task(_bounded_read(process.stdout, 262144)),
                asyncio.create_task(_bounded_read(process.stderr, 8192)),
                asyncio.create_task(process.wait()),
            ]
            output, error, code = await asyncio.gather(*tasks)
            if code:
                failure = _MovieEncoderProbeFailed(f"exit_{code}")
                failure.add_note(error.decode("utf-8", errors="replace"))
                raise failure
            return output
    finally:
        if process is not None and process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if process is not None:
            # A killed child's wait can depend on pipe retirement. Drain after
            # cancelling the bounded readers, so unread overflow cannot keep a
            # paused stdout transport alive. After kill only buffered data remain.
            await asyncio.wait_for(process.communicate(), 2)


async def encoder(format, timeout, codec="auto"):
    candidates = codec_candidates(format, codec)
    if not candidates:
        return None, {"name": "PNG/ZIP", "threads": 1}
    from depdigest import dep_digest

    @dep_digest("imageio_ffmpeg")
    def locate():
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe(), imageio_ffmpeg.__version__

    executable, version = locate()
    resolved = Path(shutil.which(executable) or executable).resolve()
    with resolved.open("rb") as binary:
        digest = hashlib.file_digest(binary, "sha256").hexdigest()
    # Share one preparation budget across both bounded native queries.
    deadline = asyncio.get_running_loop().time() + timeout
    output = await run_encoder_probe(str(resolved), ["-version"], timeout)
    native = await run_encoder_probe(
        str(resolved), ["-hide_banner", "-encoders"], max(0, deadline - asyncio.get_running_loop().time())
    )
    if not output.strip():
        raise _MovieEncoderProbeFailed("empty_version_output")
    available = video_encoders(native)
    selected = select_codec(format, codec, available)
    return str(resolved), {
        "name": "FFmpeg",
        "provider": "imageio-ffmpeg",
        "provider_version": version,
        "executable_sha256": digest,
        "version": output.decode("utf-8", errors="replace").splitlines()[0][:512],
        "codec": selected,
        "codec_family": next(name for name, implementation in _CODECS.items() if implementation == selected),
        "requested_codec": codec,
        "selection_policy": "molsysviewer.movie_codecs@1",
        "codec_candidates": list(candidates),
        "available_codecs": [name for name in _CONTAINERS[format] if _CODECS[name] in available],
    }
