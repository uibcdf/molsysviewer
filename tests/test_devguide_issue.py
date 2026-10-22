"""Receive the complete issue board without conflating pull requests or states."""

import json
from pathlib import Path

from devtools import devguide_issue

ROOT = Path(__file__).resolve().parents[1]


def test_board_keeps_older_issues_across_native_pages(monkeypatch):
    fixture = json.loads((ROOT / "tests/fixtures/devguide_board_pages.json").read_text(encoding="utf-8"))
    assert sum(fixture["native_page_sizes"]) > 200

    def replay(*arguments):
        assert arguments == ("api", "--paginate", "--slurp", fixture["endpoint"])
        return json.dumps(fixture["pages"])

    monkeypatch.setattr(devguide_issue, "_gh", replay)
    board = devguide_issue._board()
    assert board[35]["state"] == "OPEN"
    assert board[256]["state"] == "CLOSED"
    assert {label["name"] for label in board[259]["labels"]} >= {"blocked", "proposal"}
    assert fixture["pull_request_number"] not in board


def test_empty_board_is_not_a_fabricated_successful_inventory(monkeypatch, capsys):
    monkeypatch.setattr(devguide_issue, "_gh", lambda *_: "[]")
    assert devguide_issue._board() == {}
    # Missing issues must still be reported; pagination does not weaken sync.
    path = ROOT / "devguide/pending_proposals/native_copy_contract_receiving.md"
    fields = {"issue": "uibcdf/molsysviewer#259", "status": "blocked"}
    monkeypatch.setattr(devguide_issue, "_documents", lambda: [(path, fields)])
    assert devguide_issue.sync(check=True) == 1
    assert "#259 is not on the board" in capsys.readouterr().out
