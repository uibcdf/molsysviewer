"""Studio file acquisition reads bounded host directories and never loads data."""

import shutil
from pathlib import Path

import molsysmt as msm
import pytest
from molsysviewer.viewer.panel_actions import dispatch_panel_action
from molsysviewer.viewer.panel_actions._file_selection import _directory_page

import molsysviewer as msv


def test_host_file_listing_hidden_directories_and_paths_never_mutates_the_view(tmp_path):
    source = Path(msm.systems["alanine dipeptide"]["alanine_dipeptide.h5msm"])
    shutil.copyfile(source, tmp_path / "visible.h5msm")
    shutil.copyfile(source, tmp_path / ".hidden.h5msm")
    (tmp_path / "inputs").mkdir()
    with msv.new_view() as view:
        view._ready = True
        sent = []
        view.widget.send = sent.append
        for hidden in (False, True):
            dispatch_panel_action(
                view,
                {
                    "action": "browse_load_files",
                    "request_id": f"picker-{hidden}",
                    "directory": str(tmp_path),
                    "show_hidden": hidden,
                },
            )
            reply = sent[-1]
            assert reply["op"] == "system_file_browse_result" and reply["ok"]
            assert reply["request_id"] == f"picker-{hidden}"
            assert reply["directory"] == str(tmp_path.resolve())
            assert reply["parent"] == str(tmp_path.parent.resolve())
            assert reply["entries"][0] == {
                "name": "inputs",
                "path": str(tmp_path / "inputs"),
                "is_directory": True,
            }
            assert (".hidden.h5msm" in [item["name"] for item in reply["entries"]]) is hidden
            assert view.molsys is None and not view.load_blocks


def test_directory_pages_are_bounded_complete_ordered_and_do_not_read_file_content(tmp_path):
    for index in range(183):
        # Empty files intentionally cannot be parsed as molecules. Browsing only reads names.
        (tmp_path / f"source-{index:03}.pdb").touch()
    cursor = None
    names = []
    sizes = []
    while True:
        page = _directory_page(str(tmp_path), after=cursor)
        sizes.append(len(page["entries"]))
        names.extend(item["name"] for item in page["entries"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert sizes == [80, 80, 23]
    assert names == sorted({f"source-{index:03}.pdb" for index in range(183)})


@pytest.mark.parametrize("after", [[], [False, "", ""], [2, "", ""], [0, None, ""], "all"])
def test_invalid_page_cursor_is_rejected(after, tmp_path):
    with pytest.raises(ValueError, match="cursor"):
        _directory_page(str(tmp_path), after=after)


def test_file_listing_failure_returns_correlated_error_without_loading(tmp_path):
    with msv.demo["dialanine"] as view:
        previous = view.molsys
        view._ready = True
        sent = []
        view.widget.send = sent.append
        with pytest.raises(FileNotFoundError):
            dispatch_panel_action(
                view,
                {"action": "browse_load_files", "request_id": "missing", "directory": str(tmp_path / "missing")},
            )
        assert sent[-1]["request_id"] == "missing" and sent[-1]["ok"] is False
        assert "error_message" in sent[-1]
        assert view.molsys is previous and int(msm.get(view.molsys, n_atoms=True)) == 22


def test_hidden_choice_and_directory_type_are_not_silently_coerced(tmp_path):
    with pytest.raises(ValueError):
        _directory_page(str(tmp_path), show_hidden="false")
    with pytest.raises(ValueError):
        _directory_page(None)
