"""Exact sampling, real encoder I/O and real View refusal without a renderer.

Small known RGB images isolate codec behavior. The Movie browser guard owns
actual molecular rendering and transport; these tests never fabricate a View.
"""

import asyncio
import base64
import json
import zipfile
from fractions import Fraction

import numpy as np
import pytest
from molsysviewer.viewer._movie_export import _encoder, _FrameSink, _png
from molsysviewer.viewer._movie_sampling import _MovieSampling, frame_rate
from molsysviewer.viewer.frontend_requests import FrontendRequestError

import molsysviewer as msv


@pytest.mark.parametrize(
    "duration,rate,count,last",
    [
        (1000, 25, 25, 960),
        (1001, 25, 26, 1000),
        (1, 25, 1, 0),
        (1000, "30000/1001", 30, 29029 / 30),
        (1001, "30000/1001", 30, 29029 / 30),
    ],
)
def test_sampling_uses_half_open_constant_rate(duration, rate, count, last):
    samples = _MovieSampling(duration, rate)
    assert samples.count == count
    assert samples.time_ms(0) == 0
    assert samples.time_ms(count - 1) == pytest.approx(last)
    assert samples.time_ms(count - 1) < duration
    record = samples.record()
    fps = Fraction(record["fps"]["numerator"], record["fps"]["denominator"])
    encoded = record["encoded_duration_seconds"]
    assert Fraction(encoded["numerator"], encoded["denominator"]) == count / fps


@pytest.mark.parametrize("value", [True, False, 0, -1, "nan", float("inf"), "1/0", "1/2147483648", 241, [], None])
def test_bad_frame_rates_are_refused(value):
    with pytest.raises(ValueError, match="fps"):
        frame_rate(value)


def test_sampling_large_plan_does_not_materialize_a_frame_list():
    samples = _MovieSampling(24 * 60 * 60 * 1000, "30000/1001")
    assert samples.count == 2_589_411
    assert samples.time_ms(samples.count - 1) == pytest.approx(86_399_980.33333333)
    assert frame_rate(29.97) == Fraction(2997, 100)


def test_a_headless_real_view_never_writes_placeholder_movie(tmp_path, monkeypatch):
    monkeypatch.setenv("MSM_VIEWS_FROM_HTML_FILES", "True")
    with msv.demo["dialanine"] as view:
        view.movie.set_baseline(1000, camera={"position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]})
        destination = tmp_path / "preserve.zip"
        destination.write_bytes(b"keep")
        with pytest.raises(FrontendRequestError, match="no_live_frontend"):
            asyncio.run(view.movie.export_async(destination, format="pngs", overwrite=True, width_px=48, height_px=32))
        assert destination.read_bytes() == b"keep"
        assert view.movie._export_job is None
        assert list(tmp_path.iterdir()) == [destination]


def _frame(colour):
    imageio = pytest.importorskip("imageio.v2")
    pixels = np.zeros((32, 48, 3), dtype=np.uint8)
    pixels[:] = colour
    pixels[8:24, 16:32] = [200, 200, 200]
    data = imageio.imwrite("<bytes>", pixels, format="png")
    assert _png("data:image/png;base64," + base64.b64encode(data).decode(), 48, 32) == data
    return data


@pytest.mark.parametrize("format", ["pngs", "mp4", "webm"])
def test_real_encoder_outputs_are_readable_and_match_sample_count(tmp_path, format):
    _receive_known_frames(tmp_path, format)


def test_explicit_av1_encoder_outputs_are_readable_and_match_sample_count(tmp_path):
    actual = _receive_known_frames(tmp_path, "webm", "av1")
    assert actual["codec"] == "libaom-av1" and actual["requested_codec"] == "av1"


def _receive_known_frames(tmp_path, format, codec="auto"):
    if format != "pngs":
        backend = pytest.importorskip("imageio_ffmpeg")
    sampling = _MovieSampling(1000, 4)
    colours = [[220, 20, 20], [20, 220, 20], [20, 20, 220], [220, 220, 20]]
    manifest = {"schema": "molsysviewer.movie_export@1", "sampling": sampling.record()}

    async def encode():
        executable, encoder = await _encoder(format, 10, codec)
        manifest["encoder"] = encoder
        sink = _FrameSink(tmp_path, format, 48, 32, sampling, manifest, executable)
        try:
            await sink.open(10)
            for index, colour in enumerate(colours):
                await sink.append(_frame(colour), index, 10)
            await sink.finish(10)
            return sink.path
        except Exception as error:
            # Native stderr belongs to this tiny, non-user-data control. Retain
            # it on the original exception instead of masking a platform fault.
            diagnostics = tmp_path / "encoder.log"
            if diagnostics.is_file():
                with diagnostics.open("rb") as stream:
                    stream.seek(max(0, diagnostics.stat().st_size - 8192))
                    error.add_note(stream.read(8192).decode("utf-8", errors="replace"))
            error.add_note(f"Encoder identity: {encoder!r}")
            raise
        finally:
            await sink.close()

    path = asyncio.run(encode())
    if format == "pngs":
        with zipfile.ZipFile(path) as archive:
            assert archive.namelist() == [f"frames/{i:08d}.png" for i in range(4)] + ["manifest.json"]
            assert json.loads(archive.read("manifest.json")) == manifest
            for index, colour in enumerate(colours):
                assert archive.read(f"frames/{index:08d}.png") == _frame(colour)
    else:
        reader = backend.read_frames(str(path), input_params=["-threads", "1"], output_params=["-threads", "1"])
        try:
            metadata = next(reader)
            frames = list(reader)
        finally:
            reader.close()
        assert metadata["size"] == (48, 32)
        assert metadata["fps"] == 4
        assert metadata["duration"] == pytest.approx(1.0, abs=0.01)
        assert len(frames) == 4
        for raw, colour in zip(frames, colours, strict=True):
            pixels = np.frombuffer(raw, dtype=np.uint8).reshape(32, 48, 3)
            np.testing.assert_allclose(pixels[2:6, 2:6].mean(axis=(0, 1)), colour, atol=8)
    (tmp_path / "encoder-receipt.json").write_text(
        json.dumps(
            {
                "outcome": "passed",
                "encoder": manifest["encoder"],
                "sampling": sampling.record(),
                "frames": 4,
                "resolution": [48, 32],
                "colours_rgb": colours,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest["encoder"]


def test_encoder_is_retired_when_no_frames_are_committed(tmp_path):
    pytest.importorskip("imageio_ffmpeg")

    async def exercise():
        executable, encoder = await _encoder("mp4", 10)
        sink = _FrameSink(tmp_path, "mp4", 48, 32, _MovieSampling(1000, 4), {"encoder": encoder}, executable)
        try:
            await sink.open(10)
            process = sink.process
        finally:
            await sink.close()
        assert process.returncode is not None

    asyncio.run(exercise())


def test_native_encoder_is_joined_after_task_cancellation(tmp_path):
    pytest.importorskip("imageio_ffmpeg")

    async def exercise():
        started = asyncio.Event()
        sink = None

        async def operation():
            nonlocal sink
            executable, encoder = await _encoder("mp4", 10)
            sink = _FrameSink(tmp_path, "mp4", 48, 32, _MovieSampling(1000, 4), {"encoder": encoder}, executable)
            try:
                await sink.open(10)
                started.set()
                await asyncio.Future()
            finally:
                await sink.close()

        task = asyncio.create_task(operation())
        await asyncio.wait_for(started.wait(), 10)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, 5)
        assert sink.process.returncode is not None

    asyncio.run(exercise())


def test_rational_frame_rate_reaches_the_real_encoder(tmp_path):
    backend = pytest.importorskip("imageio_ffmpeg")
    sampling = _MovieSampling(1001, "30000/1001")

    async def encode():
        executable, encoder = await _encoder("mp4", 10)
        sink = _FrameSink(tmp_path, "mp4", 48, 32, sampling, {"encoder": encoder}, executable)
        try:
            await sink.open(10)
            frame = _frame([220, 20, 20])
            for index in range(sampling.count):
                await sink.append(frame, index, 10)
            await sink.finish(10)
            return sink.path
        finally:
            await sink.close()

    reader = backend.read_frames(
        str(asyncio.run(encode())), input_params=["-threads", "1"], output_params=["-threads", "1"]
    )
    try:
        metadata = next(reader)
        assert len(list(reader)) == 30
    finally:
        reader.close()
    assert metadata["fps"] == pytest.approx(30000 / 1001, abs=0.001)
    assert metadata["duration"] == pytest.approx(1.001, abs=0.01)
