"""Codec policy, real executable inspection and bounded process ownership."""

import asyncio
import json
import sys
from pathlib import Path

import psutil
import pytest
from molsysviewer._private.argdigest.argument.codec import digest_codec
from molsysviewer._private.exceptions import ArgumentError
from molsysviewer.viewer._movie_encoder import (
    _MovieCodecUnavailable,
    _MovieEncoderProbeFailed,
    codec_candidates,
    encoder,
    run_encoder_probe,
    select_codec,
    video_encoders,
)

import molsysviewer as msv


@pytest.mark.parametrize(
    "format,requested,available,expected",
    [
        ("mp4", "auto", {"libx264", "libaom-av1"}, "libx264"),
        ("webm", "auto", {"libvpx-vp9", "libaom-av1"}, "libvpx-vp9"),
        ("webm", "auto", {"libaom-av1"}, "libaom-av1"),
        ("webm", "av1", {"libvpx-vp9", "libaom-av1"}, "libaom-av1"),
        ("webm", "vp9", {"libvpx-vp9", "libaom-av1"}, "libvpx-vp9"),
    ],
)
def test_codec_selection_is_explicit_and_auto_has_a_fixed_order(format, requested, available, expected):
    before = available.copy()
    assert select_codec(format, requested, available) == expected
    assert available == before


@pytest.mark.parametrize(
    "format,requested,available",
    [
        ("webm", "vp9", {"libaom-av1"}),
        ("webm", "av1", {"libvpx-vp9"}),
        ("webm", "auto", {"libx264"}),
        ("mp4", "auto", {"libaom-av1"}),
    ],
)
def test_missing_requested_codec_never_substitutes_another(format, requested, available):
    with pytest.raises(_MovieCodecUnavailable) as failure:
        select_codec(format, requested, available)
    assert isinstance(failure.value, RuntimeError)
    assert format in str(failure.value) and requested in str(failure.value)


@pytest.mark.parametrize(
    "format,codec",
    [
        ("mp4", "av1"),
        ("mp4", "vp9"),
        ("webm", "h264"),
        ("pngs", "vp9"),
        ("html", "av1"),
        ("webm", None),
        ("webm", True),
        ("webm", []),
        ("webm", "automatic"),
    ],
)
def test_container_and_codec_errors_precede_external_execution(format, codec):
    with pytest.raises(ValueError):
        codec_candidates(format, codec)


def test_public_codec_validation_preserves_the_destination_and_scene(tmp_path):
    destination = tmp_path / "preserve.zip"
    destination.write_bytes(b"keep")
    with msv.demo["dialanine"] as view:
        before = view.export_state()
        with pytest.raises(ArgumentError):
            asyncio.run(view.movie.export_async(destination, codec="unsupported", overwrite=True))
        with pytest.raises(ValueError, match="auto for PNG/HTML"):
            asyncio.run(view.movie.export_async(destination, codec=" AV1 ", overwrite=True))
        with pytest.raises(ValueError, match="Movie codec"):
            asyncio.run(view.movie.export_async(destination, codec=[], overwrite=True, skip_digestion=True))
        assert destination.read_bytes() == b"keep"
        assert view.export_state() == before
        assert view.movie._export_job is None


@pytest.mark.parametrize("codec", ["auto", "h264", "vp9", "av1"])
def test_public_codec_digestion_normalizes_declared_choices(codec):
    assert digest_codec(f" {codec.upper()} ") == codec


@pytest.mark.parametrize("codec", [None, True, 0, [], "libvpx-vp9", "unsupported"])
def test_public_codec_digestion_rejects_undeclared_choices(codec):
    with pytest.raises(ArgumentError):
        digest_codec(codec)


def test_png_encoder_remains_independent_of_external_codecs():
    executable, metadata = asyncio.run(encoder("pngs", 1))
    assert executable is None and metadata == {"name": "PNG/ZIP", "threads": 1}


def test_encoder_listing_requires_actual_video_flags_and_exact_names():
    listing = (
        b"Encoders:\n V..... = Video\n V....D libaom-av1 AV1\n"
        b" A..... libvpx-vp9 audio fault\n V..... other mentions libvpx-vp9\n"
    )
    assert video_encoders(listing) == {"libaom-av1", "other"}
    with pytest.raises(_MovieEncoderProbeFailed, match="invalid_encoder_listing"):
        video_encoders(b"libvpx-vp9")


def test_native_executable_selection_matches_actual_video_encoders():
    pytest.importorskip("imageio_ffmpeg")

    async def receive():
        executable, automatic = await encoder("webm", 10)
        assert Path(executable).is_absolute()
        assert automatic["requested_codec"] == "auto"
        assert automatic["codec_candidates"] == ["libvpx-vp9", "libaom-av1"]
        assert automatic["selection_policy"] == "molsysviewer.movie_codecs@1"
        listing = await run_encoder_probe(executable, ["-hide_banner", "-encoders"], 10)
        if b"libvpx-vp9" in listing:
            _, explicit = await encoder("webm", 10, "vp9")
            assert automatic["codec"] == explicit["codec"] == "libvpx-vp9"
        else:
            assert automatic["codec"] == "libaom-av1"
            with pytest.raises(_MovieCodecUnavailable):
                await encoder("webm", 10, "vp9")
        return automatic

    assert asyncio.run(receive())["codec_family"] in {"vp9", "av1"}


def test_probe_keeps_native_failure_distinct_from_missing_codec():
    with pytest.raises(_MovieEncoderProbeFailed) as failure:
        asyncio.run(
            run_encoder_probe(sys.executable, ["-c", "import sys;sys.stderr.write('native failure');sys.exit(7)"], 5)
        )
    assert "exit_7" in str(failure.value)
    assert "native failure" in "\n".join(failure.value.__notes__)


def test_probe_refuses_output_overflow_instead_of_buffering_it():
    with pytest.raises(_MovieEncoderProbeFailed, match="output_limit"):
        asyncio.run(run_encoder_probe(sys.executable, ["-c", "import sys;sys.stdout.buffer.write(b'x'*10000000)"], 5))


@pytest.mark.parametrize("cancel", [False, True])
def test_probe_timeout_and_cancellation_retire_the_actual_child(tmp_path, cancel):
    identity = tmp_path / "child.json"
    script = (
        "import os,time,json;from pathlib import Path;"
        f"Path({json.dumps(str(identity))}).write_text(json.dumps(os.getpid()));time.sleep(30)"
    )

    async def exercise():
        task = asyncio.create_task(run_encoder_probe(sys.executable, ["-c", script], 5 if cancel else 0.5))
        if cancel:
            async with asyncio.timeout(3):
                while not identity.exists():
                    await asyncio.sleep(0.01)
            task.cancel()
        with pytest.raises(asyncio.CancelledError if cancel else TimeoutError):
            await task
        assert identity.exists(), "The real child must have started before testing retirement."
        assert not psutil.pid_exists(json.loads(identity.read_text(encoding="utf-8")))

    asyncio.run(exercise())
