"""Real HTTP and Chromium checks for disposable PNG rendering resources."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

import imageio.v3 as imageio
import pytest
from molsysviewer._private.html_server import runtime_html_server

import molsysviewer as msv


@pytest.mark.parametrize("fail", [False, True])
def test_html_server_releases_socket_thread_and_workspace_on_exit(tmp_path, fail):
    caller_file = tmp_path / "keep.txt"
    caller_file.write_text("caller output")
    runtime = Path(msv.__file__).parent / "viewer.js"

    def operation():
        nonlocal host
        with runtime_html_server(runtime) as host:
            (host.directory / "view.html").write_text("<html>owned scratch</html>")
            with urlopen(f"{host.origin}/view.html") as response:
                assert response.read() == b"<html>owned scratch</html>"
            with urlopen(f"{host.origin}/viewer.js") as response:
                assert response.status == 200
                assert response.read(1)
            if fail:
                raise RuntimeError("operation rejected")

    host = None
    if fail:
        with pytest.raises(RuntimeError, match="operation rejected"):
            operation()
    else:
        operation()
    assert not host.directory.exists()
    assert not host.thread.is_alive()
    assert host.server.socket.fileno() == -1
    assert caller_file.read_text() == "caller output"


@pytest.mark.skipif(os.name == "nt", reason="POSIX read-only directory permission guard")
def test_real_png_export_from_read_only_package(tmp_path):
    pytest.importorskip("playwright.sync_api", reason="Optional headless PNG backend")
    package_root = tmp_path / "installed"
    package = package_root / "molsysviewer"
    shutil.copytree(
        Path(msv.__file__).parent,
        package,
        ignore=shutil.ignore_patterns("js", "__pycache__", "viewer.js.map"),
    )
    directories = [package, *(path for path in package.rglob("*") if path.is_dir())]
    for directory in directories:
        directory.chmod(0o555)
    output = tmp_path / "image.png"
    script = """
import pathlib, sys
import molsysviewer as msv
assert pathlib.Path(msv.__file__).resolve().is_relative_to(pathlib.Path(sys.argv[1]).resolve())
with msv.demo["dialanine"] as view:
    view._export_image_headless_playwright(sys.argv[2], width_px=320, height_px=240, timeout_s=45)
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, str(package_root), str(output)],
            cwd=tmp_path,
            env={**os.environ, "PYTHONPATH": str(package_root), "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
            capture_output=True,
            timeout=90,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        image = imageio.imread(output)
        assert image.shape[:2] == (240, 320)
        assert image[..., :3].max() > image[..., :3].min()
        assert not list(package.glob("tmp*.html"))
    finally:
        for directory in directories:
            directory.chmod(0o755)
