"""The browser fixture worker reuses imports without leaking scientific state."""

import json
import subprocess
import sys
from pathlib import Path


def test_interactions_worker_keeps_fresh_views_and_cleans_files(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = root / "molsysviewer/js/tests/e2e/interactions-subpanel-bridge.py"
    events = [{"action": "toggle_interaction_visibility", "event": "interaction_context_action", "tag": "hb"}]
    requests = [
        {"id": 1, "events": events},
        {"id": 2},
        {"id": 3, "family": "not_a_family"},
        {"id": 4},
    ]
    result = subprocess.run(
        [sys.executable, str(script), "--serve"],
        input="".join(json.dumps(request) + "\n" for request in requests),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        timeout=90,
    )
    assert result.returncode == 0, result.stderr
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    assert [response["id"] for response in responses] == [1, 2, 3, 4]
    assert "not_a_family" in responses[2]["error"]
    hidden, fresh, recovered = [responses[index]["result"] for index in (0, 1, 3)]
    assert hidden["message_batches"][0]
    assert fresh["message_batches"] == recovered["message_batches"] == []
    assert fresh["inspection"] == recovered["inspection"]
    assert fresh["initial_messages"] == recovered["initial_messages"]
    paths = [Path(result["fixture_file"]) for result in (hidden, fresh, recovered)]
    assert len(set(paths)) == 3
    assert len({path.parents[1] for path in paths}) == 1
    assert all(not path.parents[1].exists() for path in paths), "EOF must remove every worker-owned fixture"
