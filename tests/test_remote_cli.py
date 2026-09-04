from __future__ import annotations

import json
import selectors
import signal
import socket
import subprocess
import sys
from io import StringIO

import pytest
from molsysviewer.remote import RemoteSessionService, server_cli
from molsysviewer.remote.render_worker import RenderWorkerConfig, RenderWorkerDiagnostics


@pytest.mark.parametrize("port", [-1, 65536, True, 1.5])
def test_session_service_rejects_invalid_listen_ports(port):
    with pytest.raises(ValueError, match="listen_port"):
        RemoteSessionService(listen_port=port)


def test_public_server_cli_parses_its_bounded_configuration(monkeypatch):
    captured = []

    async def fake_run(args, *, stream):
        captured.append((args, stream))

    monkeypatch.setattr(server_cli, "_run", fake_run)

    assert server_cli.main(
        [
            "pentalanine",
            "--demo",
            "--render-on",
            "server",
            "--port",
            "9123",
            "--chromium",
            "/opt/chrome",
            "--video-width",
            "1280",
            "--video-height",
            "720",
            "--video-fps",
            "24",
            "--video-max-bitrate",
            "3000000",
            "--ice-server",
            "stun:stun.example.org",
            "--json",
        ]
    ) == 0
    assert len(captured) == 1
    args, stream = captured[0]
    assert args.source == "pentalanine"
    assert args.demo is True
    assert args.render_on == "server"
    assert args.port == 9123
    assert args.chromium == "/opt/chrome"
    assert server_cli._worker_config(args) == RenderWorkerConfig(  # noqa: SLF001
        executable="/opt/chrome",
        width=1280,
        height=720,
        frame_rate=24,
        max_bitrate=3_000_000,
    )
    assert args.ice_server == ["stun:stun.example.org"]
    assert args.allow_software_rendering is False
    assert args.json is True
    assert stream is not None


def test_public_server_cli_builds_authenticated_turn_config_without_cli_secret(
    monkeypatch,
):
    monkeypatch.setenv("MSV_TEST_TURN_PASSWORD", "turn-secret")
    args = server_cli._build_parser().parse_args(  # noqa: SLF001
        [
            "--render-on",
            "server",
            "--ice-server",
            "stun:relay.example.org",
            "--ice-server",
            "turn:relay.example.org?transport=tcp",
            "--turn-username",
            "molsysviewer",
            "--turn-credential-env",
            "MSV_TEST_TURN_PASSWORD",
        ]
    )
    server_cli._validate_args(server_cli._build_parser(), args)  # noqa: SLF001

    assert server_cli._ice_server_config(args) == (  # noqa: SLF001
        {"urls": "stun:relay.example.org"},
        {
            "urls": "turn:relay.example.org?transport=tcp",
            "username": "molsysviewer",
            "credential": "turn-secret",
        },
    )


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["--demo", "--render-on", "client"],
        ["--render-on", "client", "--port", "-1"],
        ["--render-on", "client", "--port", "65536"],
        ["--render-on", "client", "--chromium", "/opt/chrome"],
        ["--render-on", "client", "--allow-software-rendering"],
        ["--render-on", "server", "--video-width", "319"],
        ["--render-on", "server", "--video-height", "2161"],
        ["--render-on", "server", "--video-fps", "0"],
        ["--render-on", "server", "--video-max-bitrate", "99999"],
        ["--render-on", "server", "--ice-server", "https://example.org"],
        ["--render-on", "server", "--ice-server", "turn:example.org"],
        ["--render-on", "server", "--turn-username", "user"],
        ["--render-on", "server", "--turn-credential-env", "MISSING"],
        [
            "--render-on",
            "server",
            "--ice-server",
            "stun:example.org",
            "--turn-username",
            "user",
            "--turn-credential-env",
            "MISSING",
        ],
        [
            "--render-on",
            "server",
            "--ice-server",
            "turn:example.org",
            "--turn-username",
            "user",
            "--turn-credential-env",
            "MISSING",
        ],
    ],
)
def test_public_server_cli_rejects_ambiguous_or_unsupported_configuration(arguments):
    with pytest.raises(SystemExit) as raised:
        server_cli.main(arguments)
    assert raised.value.code == 2


def test_machine_readable_startup_record_has_a_versioned_stable_shape():
    args = server_cli._build_parser().parse_args(  # noqa: SLF001
        ["--render-on", "server", "--port", "0"]
    )
    diagnostics = RenderWorkerDiagnostics(
        pid=123,
        product="Chrome/1",
        webgl2=True,
        renderer="Example GPU",
        software_rendering=False,
        webrtc=True,
        capture_stream=True,
        gpu_feature_status={"webgl": "enabled"},
    )

    record = server_cli._startup_record(  # noqa: SLF001
        args,
        "http://127.0.0.1:49123/session/client#token=secret",
        diagnostics,
    )

    assert record == {
        "schema_version": 1,
        "event": "session-ready",
        "render_on": "server",
        "session_url": "http://127.0.0.1:49123/session/client#token=secret",
        "qt_command": [
            "molsysviewer-qt",
            "--connect",
            "http://127.0.0.1:49123/session/client#token=secret",
        ],
        "ssh_forward": {
            "local_port": 49123,
            "target_host": "127.0.0.1",
            "target_port": 49123,
        },
        "renderer": {
            "pid": 123,
            "product": "Chrome/1",
            "webgl2": True,
            "renderer": "Example GPU",
            "software_rendering": False,
            "webrtc": True,
            "capture_stream": True,
        },
    }


def test_client_rendering_cli_runs_a_real_demo_session_and_emits_json(monkeypatch, capsys):
    async def stop_immediately(_stop):
        return None

    monkeypatch.setattr(server_cli, "_wait_for_shutdown", stop_immediately)

    assert server_cli.main(
        [
            "pentalanine",
            "--demo",
            "--render-on",
            "client",
            "--port",
            "0",
            "--json",
        ]
    ) == 0

    record = json.loads(capsys.readouterr().out)
    assert record["schema_version"] == 1
    assert record["event"] == "session-ready"
    assert record["render_on"] == "client"
    assert record["renderer"] is None
    assert record["session_url"].startswith("http://127.0.0.1:")
    assert record["ssh_forward"]["target_port"] > 0


def test_foreground_server_process_reports_ready_and_closes_on_sigterm():
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "molsysviewer.remote.server_cli",
            "--render-on",
            "client",
            "--port",
            "0",
            "--json",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=15), "server emitted no session-ready record"
        record = json.loads(process.stdout.readline())
        assert record["event"] == "session-ready"
        assert record["render_on"] == "client"

        process.send_signal(signal.SIGTERM)
        _stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def test_human_startup_output_is_directly_actionable():
    output = StringIO()
    record = {
        "session_url": "http://127.0.0.1:8765/session/client#token=secret",
        "ssh_forward": {
            "local_port": 8765,
            "target_host": "127.0.0.1",
            "target_port": 8765,
        },
        "renderer": None,
    }

    server_cli._emit_startup(record, json_output=False, stream=output)  # noqa: SLF001

    text = output.getvalue()
    assert "Session URL: http://127.0.0.1:8765/session/client#token=secret" in text
    assert "molsysviewer-qt --connect" in text
    assert "ssh -N -L 8765:127.0.0.1:8765 SERVER" in text
    assert "Ctrl+C" in text


def test_load_worker_and_bind_failures_have_distinct_exit_codes(tmp_path, capsys):
    missing_source = tmp_path / "missing.pdb"
    assert server_cli.main(
        [str(missing_source), "--render-on", "client", "--port", "0"]
    ) == 3
    assert "load failed:" in capsys.readouterr().err

    missing_chromium = tmp_path / "missing-chromium"
    assert server_cli.main(
        [
            "--render-on",
            "server",
            "--port",
            "0",
            "--chromium",
            str(missing_chromium),
        ]
    ) == 5
    assert "worker failed:" in capsys.readouterr().err

    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        port = occupied.getsockname()[1]
        assert server_cli.main(
            ["--render-on", "client", "--port", str(port)]
        ) == 4
    assert "session failed:" in capsys.readouterr().err
