"""Public foreground launcher for one MolSysViewer remote session."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shlex
import signal
import sys
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict
from typing import Any, TextIO
from urllib.parse import urlsplit

from ..demo import demo
from ..viewer import MolSysView
from .render_worker import RenderWorkerConfig, RenderWorkerDiagnostics
from .session_service import RemoteSessionService

_EXIT_RUNTIME = 1
_EXIT_LOAD = 3
_EXIT_SESSION = 4
_EXIT_WORKER = 5
_ICE_SCHEMES = ("stun:", "stuns:", "turn:", "turns:")


class _CliFailure(RuntimeError):
    def __init__(self, stage: str, exit_code: int, error: BaseException) -> None:
        super().__init__(str(error))
        self.stage = stage
        self.exit_code = exit_code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="molsysviewer-server",
        description=(
            "Run one authenticated MolSysViewer remote session in the foreground. "
            "The 1.0 server binds to loopback; connect directly on the host or through SSH forwarding."
        ),
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Server-side molecular-system path, or demo key with --demo. Omit to start empty.",
    )
    parser.add_argument("--demo", action="store_true", help="Interpret source as a demo key.")
    parser.add_argument(
        "--render-on",
        choices=("client", "server"),
        required=True,
        help="Place Mol*/WebGL explicitly on the connecting client or this server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Loopback TCP port. Pass 0 to select an available port (default: 8765).",
    )
    parser.add_argument(
        "--chromium",
        metavar="PATH",
        help="Chromium-family executable for server rendering.",
    )
    parser.add_argument(
        "--allow-software-rendering",
        action="store_true",
        help="Allow a software renderer explicitly; hardware is required by default.",
    )
    parser.add_argument(
        "--video-width",
        type=int,
        default=1920,
        help="Server-rendered video width in pixels (default: 1920).",
    )
    parser.add_argument(
        "--video-height",
        type=int,
        default=1080,
        help="Server-rendered video height in pixels (default: 1080).",
    )
    parser.add_argument(
        "--video-fps",
        type=int,
        default=30,
        help="Maximum server-rendered frame rate (default: 30).",
    )
    parser.add_argument(
        "--video-max-bitrate",
        type=int,
        default=8_000_000,
        metavar="BITS_PER_SECOND",
        help="Maximum server-rendered video bitrate (default: 8000000).",
    )
    parser.add_argument(
        "--ice-server",
        action="append",
        default=[],
        metavar="URI",
        help="STUN/TURN URI supplied to WebRTC; repeat for multiple servers.",
    )
    parser.add_argument(
        "--turn-username",
        metavar="USERNAME",
        help="Username applied to configured TURN servers.",
    )
    parser.add_argument(
        "--turn-credential-env",
        metavar="ENV_VAR",
        help=(
            "Read the TURN password from this environment variable. "
            "The credential is never accepted as a command-line value."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the versioned session-ready record as one JSON line.",
    )
    return parser


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.demo and args.source is None:
        parser.error("--demo requires a source demo key")
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    if args.render_on == "client" and args.chromium is not None:
        parser.error("--chromium applies only to --render-on server")
    if args.render_on == "client" and args.allow_software_rendering:
        parser.error("--allow-software-rendering applies only to --render-on server")
    video_bounds = (
        ("--video-width", args.video_width, 320, 3840),
        ("--video-height", args.video_height, 240, 2160),
        ("--video-fps", args.video_fps, 1, 60),
        ("--video-max-bitrate", args.video_max_bitrate, 100_000, 100_000_000),
    )
    for option, value, minimum, maximum in video_bounds:
        if not minimum <= value <= maximum:
            parser.error(f"{option} must be between {minimum} and {maximum}")
    invalid_ice = [
        uri
        for uri in args.ice_server
        if not isinstance(uri, str) or not uri.lower().startswith(_ICE_SCHEMES)
    ]
    if invalid_ice:
        parser.error(
            "--ice-server values must use stun:, stuns:, turn: or turns: "
            f"({invalid_ice[0]!r} is invalid)"
        )
    turn_uris = [
        uri for uri in args.ice_server if uri.lower().startswith(("turn:", "turns:"))
    ]
    turn_credentials = (args.turn_username, args.turn_credential_env)
    if (turn_credentials[0] is None) != (turn_credentials[1] is None):
        parser.error("--turn-username and --turn-credential-env must be supplied together")
    if turn_uris and args.turn_username is None:
        parser.error(
            "turn: and turns: --ice-server values require "
            "--turn-username and --turn-credential-env"
        )
    if args.turn_username is not None:
        if not turn_uris:
            parser.error("TURN credentials require at least one turn: or turns: --ice-server")
        credential = os.environ.get(args.turn_credential_env, "")
        if not credential:
            parser.error(
                f"TURN credential environment variable {args.turn_credential_env!r} is unset or empty"
            )


def _ice_server_config(args: argparse.Namespace) -> tuple[dict[str, str], ...]:
    credential = (
        os.environ[args.turn_credential_env]
        if args.turn_credential_env is not None
        else None
    )
    result: list[dict[str, str]] = []
    for uri in args.ice_server:
        item = {"urls": uri}
        if credential is not None and uri.lower().startswith(("turn:", "turns:")):
            item.update(username=args.turn_username, credential=credential)
        result.append(item)
    return tuple(result)


def _worker_config(args: argparse.Namespace) -> RenderWorkerConfig:
    return RenderWorkerConfig(
        executable=args.chromium,
        gpu_policy=(
            "allow-software" if args.allow_software_rendering else "require-hardware"
        ),
        width=args.video_width,
        height=args.video_height,
        frame_rate=args.video_fps,
        max_bitrate=args.video_max_bitrate,
    )


def _startup_record(
    args: argparse.Namespace,
    client_url: str,
    diagnostics: RenderWorkerDiagnostics | None,
) -> dict[str, Any]:
    split = urlsplit(client_url)
    port = split.port
    if port is None:  # pragma: no cover - service URLs always carry the bound port
        raise RuntimeError("session URL does not identify its bound port")
    renderer: Mapping[str, Any] | None = None
    if diagnostics is not None:
        values = asdict(diagnostics)
        renderer = {
            key: values[key]
            for key in (
                "pid",
                "product",
                "webgl2",
                "renderer",
                "software_rendering",
                "webrtc",
                "capture_stream",
            )
        }
    return {
        "schema_version": 1,
        "event": "session-ready",
        "render_on": args.render_on,
        "session_url": client_url,
        "qt_command": ["molsysviewer-qt", "--connect", client_url],
        "ssh_forward": {
            "local_port": port,
            "target_host": "127.0.0.1",
            "target_port": port,
        },
        "renderer": renderer,
    }


def _emit_startup(record: Mapping[str, Any], *, json_output: bool, stream: TextIO) -> None:
    if json_output:
        print(json.dumps(record, separators=(",", ":"), sort_keys=True), file=stream, flush=True)
        return
    renderer = record.get("renderer")
    if isinstance(renderer, Mapping):
        print(f"Renderer: {renderer['renderer']}", file=stream)
    session_url = str(record["session_url"])
    forwarding = record["ssh_forward"]
    print(f"Session URL: {session_url}", file=stream)
    print(
        "Qt client: "
        f"molsysviewer-qt --connect {shlex.quote(session_url)}",
        file=stream,
    )
    print(
        "SSH forward: ssh -N "
        f"-L {forwarding['local_port']}:{forwarding['target_host']}:{forwarding['target_port']} SERVER",
        file=stream,
    )
    print("Press Ctrl+C to close the session.", file=stream, flush=True)


def _install_shutdown_handlers(stop: asyncio.Event) -> tuple[signal.Signals, ...]:
    loop = asyncio.get_running_loop()
    installed: list[signal.Signals] = []
    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, stop.set)
        except (NotImplementedError, RuntimeError):  # pragma: no cover - platform loop detail
            continue
        installed.append(signum)
    return tuple(installed)


def _remove_shutdown_handlers(installed: Sequence[signal.Signals]) -> None:
    loop = asyncio.get_running_loop()
    for signum in installed:
        with suppress(NotImplementedError, RuntimeError):
            loop.remove_signal_handler(signum)


async def _wait_for_shutdown(stop: asyncio.Event) -> None:
    await stop.wait()


async def _run(args: argparse.Namespace, *, stream: TextIO) -> None:
    stop = asyncio.Event()
    installed_handlers = _install_shutdown_handlers(stop)
    source_view: Any = None
    service = RemoteSessionService(
        _worker_config(args),
        render_on=args.render_on,
        listen_port=args.port,
        ice_servers=_ice_server_config(args),
    )
    view = MolSysView(transport=service.channel)
    try:
        if args.source is not None:
            try:
                if args.demo:
                    source_view = demo[args.source]
                    view.load(source_view.molsys, skip_digestion=True)
                else:
                    view.load(args.source, skip_digestion=True)
            except Exception as error:
                raise _CliFailure("load", _EXIT_LOAD, error) from error
        try:
            client_url = await service.start()
        except Exception as error:
            raise _CliFailure("session", _EXIT_SESSION, error) from error
        diagnostics = None
        if args.render_on == "server":
            try:
                diagnostics = await service.launch_worker()
            except Exception as error:
                raise _CliFailure("worker", _EXIT_WORKER, error) from error
        _emit_startup(
            _startup_record(args, client_url, diagnostics),
            json_output=args.json,
            stream=stream,
        )
        await _wait_for_shutdown(stop)
    finally:
        _remove_shutdown_handlers(installed_handlers)
        await service.close()
        view.close()
        if source_view is not None:
            source_view.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _validate_args(parser, args)
    try:
        asyncio.run(_run(args, stream=sys.stdout))
    except KeyboardInterrupt:  # pragma: no cover - fallback where loop handlers are unavailable
        return 0
    except _CliFailure as error:
        print(f"molsysviewer-server: {error.stage} failed: {error}", file=sys.stderr)
        return error.exit_code
    except Exception as error:  # last-resort CLI boundary
        print(f"molsysviewer-server: unexpected failure: {error}", file=sys.stderr)
        return _EXIT_RUNTIME
    return 0


__all__ = ["main"]


if __name__ == "__main__":  # pragma: no cover - console script is the supported entrypoint
    raise SystemExit(main())
