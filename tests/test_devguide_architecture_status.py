from pathlib import Path


REPO_ROOT = Path(__file__).parents[1]
DEVGUIDE = REPO_ROOT / "devguide"


def _text(relative_path: str) -> str:
    return (DEVGUIDE / relative_path).read_text(encoding="utf-8")


def test_current_architecture_documents_do_not_restore_completed_work_as_pending():
    data_plane = _text("data_plane_architecture.md")
    router = _text("runtime_message_router.md")

    for stale in (
        "Qt keeps the JSON path",
        "Remaining execution order",
        "Finish R2's canonical popup snapshot",
        "Close D3 with a no-ack timeout",
        "Implement D4 endpoint parity",
    ):
        assert stale not in data_plane

    for stale in (
        "PopupReplayLog remains only as the fallback",
        "Still open for D4b",
        "signalled and forwarded",
        "The current popup path",
    ):
        assert stale not in router


def test_current_molecular_projection_docs_do_not_depend_on_viewerjson():
    current_documents = (
        "data_plane_architecture.md",
        "path_to_1_0.md",
        "roadmap.md",
        "pending_proposals/post_1.0/representative_scale_followups.md",
        "pending_proposals/post_1.0/chemical_metadata_loss_sdf_pdb.md",
    )

    for relative_path in current_documents:
        assert "ViewerJSON" not in _text(relative_path), relative_path


def test_s9_and_completed_design_records_have_current_status():
    contracts = _text("scene_contracts.md")
    s9 = contracts.split("### Contract S9", maxsplit=1)[1].split(
        "### Contract S10", maxsplit=1
    )[0]
    normalized_s9 = " ".join(s9.split())
    assert "Status: implemented and measured" in normalized_s9
    assert "implementation pending" not in normalized_s9

    assert not (
        DEVGUIDE / "pending_proposals/report_molstar_empty_scene_camera_bounds.md"
    ).exists()
    assert (
        DEVGUIDE / "archive/report_molstar_empty_scene_camera_bounds.md"
    ).is_file()
    assert not (
        DEVGUIDE / "pending_proposals/post_1.0/zero_copy_visual_rendering.md"
    ).exists()
    assert (DEVGUIDE / "archive/zero_copy_visual_rendering.md").is_file()


def test_qt_docs_distinguish_control_channel_from_binary_payload_scheme():
    source = (
        REPO_ROOT / "molsysviewer/standalone_qt/view_channel.py"
    ).read_text(encoding="utf-8")
    catalog = (
        REPO_ROOT / "molsysviewer/_private/smonitor/catalog.py"
    ).read_text(encoding="utf-8")

    normalized_source = " ".join(source.lower().split())
    assert "control channel carries json only" in normalized_source
    assert "payload-scheme path" in normalized_source
    assert "qt bridge has no binary transport" not in normalized_source
    assert "connector has no binary transport" not in catalog.lower()
