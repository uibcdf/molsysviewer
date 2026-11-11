"""Real scene owners, independent colour controls and Movie preservation."""

from copy import deepcopy
from decimal import ROUND_HALF_UP, Decimal, localcontext

import molsysmt as msm
import pytest
from molsysviewer._pyunitwizard import puw
from molsysviewer.viewer._movie_appearance import interpolate_appearance
from molsysviewer.viewer._movie_seek import _apply_sample, _visibility_commands, _visibility_owners

import molsysviewer as msv


def _track(tag, domain, prop, value, *, target=None, time=1000):
    return {
        "tag": tag,
        "target": {"domain": domain, **({"tag": target} if target else {})},
        "property": prop,
        "keys": [{"time_ms": time, "value": value}],
    }


def make_appearance_view():
    view = msv.new_view(msm.systems["pentalanine"]["traj_pentalanine.h5msm"], structure_indices=[4999, 0, 73])
    center = puw.get_value(view.molsys.structures.coordinates, to_unit="angstrom").mean(axis=(0, 1))
    view.whole.set_representation("ball-and-stick", color=0x000000)
    view.regions.add(tag="site", atom_indices=[0, 1, 2, 3], representation="ball-and-stick", color=0x204060, alpha=0.8)
    view.shapes.add_sphere(
        center=puw.quantity(center + [5, 0, 0], "angstrom"), radius="2 angstrom", tag="site", color=0xFF0000, alpha=0.25
    )
    view.annotations.add("Beginning", atom_indices=[0], tag="note")
    view.interactions.hbonds.get_buch_hbonds(name="story-hbonds", structure_indices="all", distance_threshold="0.4 nm")
    view.interactions.add("story-hbonds", tag="contacts")
    view.scene.set_background(0x000000)
    view.scene.set_lighting(ambient=0.2, diffuse=0.8)
    view.movie.set_baseline(
        1000, camera={"position": (center + [0, 0, 35]).tolist(), "target": center.tolist(), "up": [0, 1, 0]}
    )
    for track in [
        _track("whole-colour", "whole", "color", 0xFFFFFF),
        _track("site-repr", "region", "representation", "spacefill", target="site", time=500),
        _track("site-alpha", "region", "alpha", 0.2, target="site"),
        _track("sphere-colour", "shape", "color", 0x0000FF, target="site"),
        _track("sphere-alpha", "shape", "alpha", 0.75, target="site"),
        _track("interaction-colour", "interaction", "color", 0xFF0000, target="contacts"),
        _track("interaction-alpha", "interaction", "alpha", 0.2, target="contacts"),
        _track("caption", "annotation", "text", "Pocket open", target="note", time=500),
        _track("background", "scene", "background", 0xFFFFFF),
        _track("lighting", "scene", "lighting", {"ambient": 0.6, "diffuse": 0.2}),
        _track("frame", "structure", "index", 2, time=500),
        _track("hide-site", "region", "visible", False, target="site", time=750),
    ]:
        view.movie.add_track(track)
    return view


@pytest.fixture
def authored():
    with make_appearance_view() as view:
        yield view


def _values(sample):
    return {(row["domain"], row["tag"], row["property"]): row["value"] for row in sample["appearance"]}


def test_independent_appearance_evaluation_and_detached_values(authored):
    sample = authored.movie.evaluate(500)
    values = _values(sample)
    assert values["whole", None, "color"] == 0xBCBCBC
    assert values["scene", None, "background"] == 0xBCBCBC
    assert values["shape", "site", "color"] == 0xBC00BC
    assert values["shape", "site", "alpha"] == 0.5
    assert values["region", "site", "alpha"] == pytest.approx(0.5)
    assert values["region", "site", "representation"] == "spacefill"
    assert values["annotation", "note", "text"] == "Pocket open"
    assert values["scene", None, "lighting"] == {"ambient": 0.4, "diffuse": 0.5}
    assert sample["structure_index"] == 2
    for at in [1000, 100, 750, 0, 500]:
        assert authored.movie.evaluate(at) == authored.movie.evaluate(at)
    values["scene", None, "lighting"]["ambient"] = 99
    assert _values(authored.movie.evaluate(500))["scene", None, "lighting"]["ambient"] == 0.4
    assert authored.whole.params["molstar_color_theme"]["params"]["value"] == 0


def test_real_owner_application_rewinds_and_preserves_region_order_and_session(authored, tmp_path):
    order = authored.regions["site"].order
    high_water_mark = authored._region_order_counter
    owners = _visibility_owners(authored, authored.movie._timeline.visibility_targets())
    for at in [1000, 0, 500, 1000]:
        sample = authored.movie._timeline.evaluate(at, tracked_visibility=True)
        _apply_sample(
            authored.movie, authored.movie._timeline, sample, _visibility_commands(owners, sample["visibility"])
        )
        values = _values(sample)
        assert authored.whole.params["molstar_color_theme"]["params"]["value"] == values["whole", None, "color"]
        assert authored.regions["site"].representation == values["region", "site", "representation"]
        assert authored.regions["site"].repr_params["alpha"] == values["region", "site", "alpha"]
        assert authored.regions["site"].order == order
        assert authored._region_order_counter == high_water_mark
        assert authored.shapes["site"]._require_shape_message()["options"]["color"] == values["shape", "site", "color"]
        assert authored.export_state()["environment"]["lighting"] == values["scene", None, "lighting"]
        assert authored.annotations.records()[0]["options"]["text"] == values["annotation", "note", "text"]
        assert authored.interactions["contacts"]._style["color"] == values["interaction", "contacts", "color"]
        assert authored.interactions["contacts"]._style["alpha"] == values["interaction", "contacts", "alpha"]
    state, recipe = authored.export_state(), authored.movie.to_dict()
    authored.save_session(tmp_path / "appearance.msv")
    with msv.load_session(tmp_path / "appearance.msv") as restored:
        assert restored.export_state()["environment"] == state["environment"]
        assert restored.regions["site"].repr_params == authored.regions["site"].repr_params
        assert restored.movie.to_dict() == recipe
        assert restored.movie.evaluate(250) == authored.movie.evaluate(250)


@pytest.mark.parametrize(
    "prop,value",
    [
        ("color", True),
        ("color", -1),
        ("color", 0x1000000),
        ("alpha", True),
        ("alpha", float("nan")),
        ("alpha", float("inf")),
        ("alpha", 1.1),
        ("representation", "ribbon"),
        ("lighting", {"ambient": 0.5, "specular": 0.5}),
        ("lighting", {"ambient": 0.5, "diffuse": False}),
    ],
)
def test_rejected_values_preserve_recipe_and_scene(authored, prop, value):
    domain = "scene" if prop == "lighting" else "region"
    before, scene = authored.movie.to_dict(), authored.export_state()
    with pytest.raises(ValueError):
        authored.movie.add_track(_track("bad", domain, prop, value, target=None if domain == "scene" else "site"))
    assert authored.movie.to_dict() == before
    assert authored.export_state() == scene


def test_easing_is_channel_local_and_step_values_do_not_blend(authored):
    track = next(row for row in authored.movie.to_dict()["tracks"] if row["tag"] == "sphere-alpha")
    track["keys"] = [{"time_ms": 0, "value": 0.25, "easing": "ease-in"}, {"time_ms": 1000, "value": 0.75}]
    authored.movie.update_track(track["tag"], keys=track["keys"])
    values = _values(authored.movie.evaluate(500))
    assert values["shape", "site", "alpha"] == 0.375
    assert values["whole", None, "color"] == 0xBCBCBC
    assert _values(authored.movie.evaluate(499))["annotation", "note", "text"] == "Beginning"
    assert values["annotation", "note", "text"] == "Pocket open"


def test_untracked_material_edit_is_not_silently_overwritten(authored):
    authored.regions["site"].set_representation(
        "ball-and-stick", color=0x204060, alpha=0.8, sizeFactor=0.7, skip_digestion=True
    )
    with pytest.raises(ValueError, match="untracked material"):
        authored.movie.validate()


def test_uniform_movie_colour_refuses_a_real_per_atom_colour_layer(authored):
    authored.whole.set_color("#ff0000")
    assert authored.export_state()["whole"]["color_layer"]
    with pytest.raises(ValueError, match="per-atom colour layer"):
        authored.movie.validate()


def test_retained_priority_is_scoped_and_does_not_change_ordinary_styling(authored):
    region = authored.regions["site"]
    order = region.order
    with pytest.raises(ValueError):
        with authored._retain_region_order(region):
            region.set_representation("unsupported-representation")
    region.set_representation("spacefill")
    assert region.order > order
    assert not authored._retained_region_orders


def test_shared_appearance_oracle_is_current_and_preserves_all_scientific_data(authored):
    import json
    from pathlib import Path

    from molsysviewer.interactions import _analysis_signature
    from molsysviewer.viewer._movie_timeline import _MovieTimeline

    oracle = json.loads(
        (Path(__file__).parents[1] / "molsysviewer/js/tests/fixtures/movie-appearance-oracle.json").read_text()
    )
    assert authored.movie._timeline.preview_recipe() == oracle["recipe"]
    result = _analysis_signature(authored.interactions.get_analysis("story-hbonds"))
    timeline = _MovieTimeline(oracle["recipe"])
    for sample in oracle["samples"]:
        assert timeline.evaluate(sample["time_ms"]) == sample
    assert _analysis_signature(authored.interactions.get_analysis("story-hbonds")) == result


def test_environment_intent_is_cumulative_and_invalid_import_is_non_destructive(authored):
    authored.scene.set_lighting(ambient=0.3)
    authored.scene.set_lighting(specular=0.7)
    state = authored.export_state()
    assert state["environment"]["lighting"] == {"ambient": 0.3, "diffuse": 0.7}
    with msv.demo["dialanine"] as target:
        original = target.export_state()
        bad = deepcopy(original)
        bad["environment"] = {"lighting": {"ambient": 0.5, "op": "load_pdb_id"}}
        with pytest.raises(ValueError, match="lighting"):
            target.import_state(bad)
        assert target.export_state() == original


def test_object_undo_keeps_current_viewport_environment(authored):
    authored.history.clear()
    authored.annotations.add("Temporary", atom_indices=[1], tag="temporary")
    authored.scene.set_background(0x123456)
    authored.scene.set_lighting(ambient=0.3)
    environment = authored.export_state()["environment"]
    assert authored.history.undo()
    assert authored.annotations.get("temporary") is None
    assert authored.export_state()["environment"] == environment


@pytest.mark.parametrize("begin,end", [(0, 0xFFFFFF), (0x010A0B, 0x0B0A01), (0x204060, 0xE0C080)])
def test_colour_transfer_matches_independent_high_precision_control(begin, end):
    with localcontext() as context:
        context.prec = 50

        def linear(byte):
            x = Decimal(byte) / 255
            return (
                x / Decimal("12.92")
                if x <= Decimal("0.04045")
                else ((x + Decimal("0.055")) / Decimal("1.055")) ** Decimal("2.4")
            )

        for numerator in [0, 1, 50, 499, 500, 999, 1000]:
            t = Decimal(numerator) / 1000
            expected = 0
            for shift in [16, 8, 0]:
                x = (1 - t) * linear((begin >> shift) & 255) + t * linear((end >> shift) & 255)
                y = (
                    x * Decimal("12.92")
                    if x <= Decimal("0.0031308")
                    else Decimal("1.055") * x ** (Decimal(1) / Decimal("2.4")) - Decimal("0.055")
                )
                expected |= int((y * 255).to_integral_value(rounding=ROUND_HALF_UP)) << shift
            assert interpolate_appearance(begin, end, numerator / 1000, "color") == expected
