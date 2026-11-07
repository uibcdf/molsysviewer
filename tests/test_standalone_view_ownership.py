"""Standalone HTML releases its own Views while preserving borrowed owners."""

import gc
import html
from errno import ENOENT
from pathlib import Path

import comm
import molsysviewer.standalone as standalone
import numpy as np
import pytest
from ipywidgets.widgets.widget import _instances

import molsysviewer as msv


@pytest.fixture
def source():
    with msv.demo["dialanine"] as seed:
        system = seed.molsys
    del seed
    return system


def resources():
    """Observe actual registries without closing or collecting anything."""
    return set(_instances), set(comm.get_comm_manager().comms)


def view_ids():
    return {id(obj) for obj in gc.get_objects() if isinstance(obj, msv.MolSysView)}


def assert_owned_resources_released(baseline, existing_views):
    # These assertions run in the test body, before the repository's autouse
    # teardown. No GC pass or global cleanup can make a leaking writer pass.
    assert resources() == baseline
    for view in gc.get_objects():
        if isinstance(view, msv.MolSysView) and id(view) not in existing_views:
            assert view.closed
            assert view._widget_message_callback is None
            assert not view.widget._msg_callbacks.callbacks
            assert view.widget.comm is None
            assert view.widget.layout.comm is None


def coordinates(system):
    return msv.pyunitwizard.get_value(system.structures.coordinates, to_unit="angstrom").copy()


def build(source, output, **options):
    return standalone.build_standalone0_html(
        source,
        str(output),
        prepare_addons=False,
        apply_project_config=False,
        generate_demo_gallery=False,
        show_empty_host_overlay=False,
        runtime_urls=[(Path(msv.__file__).parent / "viewer.js").resolve().as_uri()],
        **options,
    )


@pytest.mark.parametrize("kind", ["empty", "molsys"])
def test_build_releases_its_owned_views_after_success(source, tmp_path, kind):
    with msv.new_view(source) as witness:
        original = coordinates(source)
        witness_state = witness.export_state()
        baseline, existing = resources(), view_ids()
        for index in range(3):
            output = tmp_path / f"{kind}-{index}.html"
            assert build(None if kind == "empty" else source, output, title="Owned export") == str(output)
            assert output.is_file()
            assert "Owned export" in output.read_text(encoding="utf-8")
            assert_owned_resources_released(baseline, existing)
            assert not witness.closed
            assert witness.export_state() == witness_state
            np.testing.assert_array_equal(coordinates(source), original)


@pytest.mark.parametrize("kind", ["empty", "molsys"])
def test_build_releases_owned_views_without_replacing_the_writer_error(source, tmp_path, kind):
    output = tmp_path / "caller-directory.html"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_bytes(b"caller-owned data")
    with msv.new_view(source) as caller:
        # A borrowed real writer gives the original native filesystem error.
        with pytest.raises(OSError) as control:
            build(caller, output)
        assert Path(control.value.filename) == output
        baseline, existing = resources(), view_ids()
        original, state = coordinates(source), caller.export_state()
        for _ in range(2):
            with pytest.raises(type(control.value)) as failure:
                build(None if kind == "empty" else source, output)
            assert str(failure.value) == str(control.value)
            assert marker.read_bytes() == b"caller-owned data"
            assert output.is_dir()
            assert_owned_resources_released(baseline, existing)
            assert not caller.closed and caller.export_state() == state
            np.testing.assert_array_equal(coordinates(source), original)


@pytest.mark.parametrize("fail", [False, True])
def test_borrowed_view_keeps_exact_data_state_callbacks_and_comms(source, tmp_path, fail):
    with msv.new_view(source) as caller, msv.new_view(source) as witness:
        region = caller.regions.add([0, 1], tag="caller-region")
        state, original = caller.export_state(), coordinates(caller.molsys)
        system, widget, layout = caller.molsys, caller.widget, caller.widget.layout
        widget_comm, layout_comm = widget.comm, layout.comm
        callback = caller._widget_message_callback
        callbacks = tuple(widget._msg_callbacks.callbacks)
        baseline, existing = resources(), view_ids()
        output = tmp_path / "borrowed.html"
        if fail:
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_bytes(b"preserve")
            with pytest.raises(OSError) as control:
                output.write_text("content", encoding="utf-8")
            with pytest.raises(type(control.value)) as failure:
                build(caller, output)
            assert failure.value.errno == control.value.errno
            assert failure.value.filename == control.value.filename
            assert failure.value.args == control.value.args
            assert marker.read_bytes() == b"preserve"
        else:
            assert build(caller, output, title="Borrowed export") == str(output)
            assert "Borrowed export" in output.read_text(encoding="utf-8")
        assert not caller.closed and not witness.closed
        assert caller.molsys is system and caller.regions["caller-region"] is region
        assert caller.export_state() == state
        np.testing.assert_array_equal(coordinates(caller.molsys), original)
        assert caller.widget is widget and widget.layout is layout
        assert widget.comm is widget_comm and layout.comm is layout_comm
        assert caller._widget_message_callback is callback
        assert tuple(widget._msg_callbacks.callbacks) == callbacks
        assert widget._molsysviewer_view_ref() is caller
        assert_owned_resources_released(baseline, existing)


@pytest.mark.parametrize("load_mode", ["selection", "all"])
@pytest.mark.parametrize("failure_kind", ["selection", "structure", "missing_file"])
def test_failed_owned_load_keeps_original_error_resources_and_existing_output(
    source, tmp_path, load_mode, failure_kind
):
    system, options = source, {}
    if failure_kind == "selection":
        options["selection"] = "this is not a valid query!"
    elif failure_kind == "structure":
        options["structure_indices"] = [999999]
    else:
        system = tmp_path / "missing.pdb"
    output = tmp_path / "keep.html"
    output.write_bytes(b"existing caller output")
    with msv.new_view() as control_view, msv.new_view(source) as witness:
        with pytest.raises(Exception) as control:
            msv.new_view(system, view=control_view, load_mode=load_mode, **options)
        baseline, existing = resources(), view_ids()
        original, state = coordinates(source), witness.export_state()
        with pytest.raises(type(control.value)) as failure:
            build(system, output, load_mode=load_mode, **options)
        assert str(failure.value) == str(control.value)
        assert output.read_bytes() == b"existing caller output"
        assert_owned_resources_released(baseline, existing)
        assert not control_view.closed and not witness.closed
        assert witness.export_state() == state
        np.testing.assert_array_equal(coordinates(source), original)


def test_default_gallery_preserves_all_links_and_releases_fresh_demo_views(tmp_path):
    baseline, existing = resources(), view_ids()
    output = tmp_path / "gallery.html"
    result = standalone.build_standalone0_html(
        None,
        str(output),
        prepare_addons=False,
        apply_project_config=False,
        runtime_urls=[(Path(msv.__file__).parent / "viewer.js").resolve().as_uri()],
    )
    assert result == str(output)
    document = output.read_text(encoding="utf-8")
    for name in msv.demo:
        demo_path = output.with_name(f"gallery-demo-{name}.html")
        assert demo_path.is_file() and demo_path.stat().st_size > 0
        assert f'href="{html.escape(demo_path.name)}"' in document
    assert_owned_resources_released(baseline, existing)


def test_gallery_writer_failure_releases_both_shell_and_fresh_demo_owner(tmp_path):
    output = tmp_path / "gallery.html"
    first_demo = sorted(msv.demo)[0]
    blocked = output.with_name(f"gallery-demo-{first_demo}.html")
    blocked.mkdir()
    marker = blocked / "keep.txt"
    marker.write_bytes(b"unrelated caller data")
    baseline, existing = resources(), view_ids()
    with pytest.raises(OSError) as control:
        blocked.write_text("content", encoding="utf-8")
    with pytest.raises(type(control.value)) as failure:
        standalone.build_standalone0_html(
            None,
            str(output),
            prepare_addons=False,
            apply_project_config=False,
            runtime_urls=[(Path(msv.__file__).parent / "viewer.js").resolve().as_uri()],
        )
    assert failure.value.errno == control.value.errno
    assert failure.value.args == control.value.args
    assert Path(failure.value.filename) == blocked
    assert marker.read_bytes() == b"unrelated caller data"
    assert output.is_file(), "the already-written shell remains caller-owned after gallery failure"
    assert_owned_resources_released(baseline, existing)


def test_cli_owns_its_fresh_demo_view(tmp_path, capsys):
    baseline, existing = resources(), view_ids()
    output = tmp_path / "cli.html"
    assert standalone.main(["dialanine", "--demo", "--no-browser", "--output", str(output)]) == 0
    assert output.is_file()
    assert str(output) in capsys.readouterr().out
    assert_owned_resources_released(baseline, existing)


@pytest.mark.parametrize("writer_fails", [False, True])
def test_real_owner_close_failure_preserves_the_original_writer_error(source, tmp_path, writer_fails):
    baseline, existing = resources(), view_ids()
    view = msv.new_view(source)
    attempts = []

    def fail_once():
        attempts.append(True)
        if len(attempts) == 1:
            raise RuntimeError("owned resource close failed")

    view._close_callbacks.append(fail_once)
    try:
        expected = FileNotFoundError if writer_fails else RuntimeError
        with pytest.raises(expected) as failure:
            with standalone._standalone_view_owner(view, owned=True):
                if writer_fails:
                    (tmp_path / "missing" / "output.html").write_text("content", encoding="utf-8")
        if writer_fails:
            assert failure.value.errno == ENOENT
            assert Path(failure.value.filename) == tmp_path / "missing" / "output.html"
            assert any("owned resource close failed" in note for note in failure.value.__notes__)
        else:
            assert str(failure.value) == "owned resource close failed"
        assert view.closed and attempts == [True]
        assert_owned_resources_released(baseline, existing)
    finally:
        # The actual View owner retries only its one failed resource callback.
        view.close()
