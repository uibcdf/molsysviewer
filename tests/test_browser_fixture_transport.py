"""The browser fixture must deliver real asynchronous comms without polling."""

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path

import pytest


@pytest.fixture
def authority(tmp_path):
    processes = []

    def launch(*arguments):
        script = Path(__file__).parents[1] / "molsysviewer/js/tests/e2e/async-comm-bridge.py"
        stderr = (tmp_path / f"authority-{len(processes)}.log").open("w")
        child = subprocess.Popen(
            [sys.executable, str(script), *arguments], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr
        )
        child._fixture_lines = queue.Queue()

        def receive():
            for line in child.stdout:
                child._fixture_lines.put(line)
            child._fixture_lines.put(None)

        reader = threading.Thread(target=receive)
        reader.start()
        processes.append((child, stderr, reader))
        return child

    yield launch
    for child, stderr, reader in processes:
        child.stdin.close()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.terminate()
            child.wait(timeout=5)
        reader.join(timeout=5)
        assert not reader.is_alive()
        child.stdout.close()
        stderr.close()
        assert child.returncode == 0


def request(child, identity, events):
    child.stdin.write((json.dumps({"id": identity, "events": events}) + "\n").encode())
    child.stdin.flush()


def read(child, timeout=20):
    try:
        line = child._fixture_lines.get(timeout=timeout)
    except queue.Empty:
        pytest.fail("No spontaneous fixture delivery.")
    assert line is not None, "The fixture authority closed before delivery."
    return json.loads(line)


def test_scheduled_real_scene_messages_arrive_without_another_request(authority):
    child = authority()
    request(child, 1, [{"event": "ready"}])
    assert read(child)["id"] == 1
    request(child, 2, [{"schedule_comm": True}])
    reply = read(child)
    assert reply["id"] == 2 and reply["result"]["scheduled"]
    assert reply["result"]["messages"] == []
    for color in (0x204060, 0x102030):
        message = read(child, timeout=3)
        assert message["event"] == "widget_messages" and "id" not in message
        payload = message["messages"][0]["content"]["payload"]
        assert payload["op"] == "set_background_color" and payload["color"] == color
    request(child, 3, [])
    assert read(child)["result"]["messages"] == []


@pytest.mark.parametrize("mode", [[], ["--sync"]])
def test_inline_scene_commands_keep_their_original_correlated_reply(authority, mode):
    child = authority(*mode)
    request(child, 1, [{"event": "ready"}])
    assert read(child)["id"] == 1
    request(child, 2, [{"inline_comm": True}])
    reply = read(child)
    assert reply["id"] == 2
    payload = reply["result"]["messages"][0]["content"]["payload"]
    assert payload["op"] == "set_background_color" and payload["color"] == 0xABCDEF
