"""Track evaluation and session persistence with bundled molecular systems."""

import json
import zipfile

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer.session import SessionFormatError

import molsysviewer as msv

CAMERA = {"position": [0, 0, 10], "target": [0, 0, 0], "up": [0, 1, 0]}
END = {"position": [2, 0, 20], "target": [2, 0, 0], "up": [0, -1, 0]}


def _track(tag, domain, prop, *keys, target=None):
    return {
        "tag": tag,
        "target": {"domain": domain, **({"tag": target} if target is not None else {})},
        "property": prop,
        "keys": [{"time_ms": time, "value": value} for time, value in keys],
    }


@pytest.fixture
def authored():
    source = msm.systems["pentalanine"]["traj_pentalanine.h5msm"]
    with msv.new_view(source, structure_indices=[4999, 0, 73]) as view:
        view.regions.add(tag="site", atom_indices=[0, 1, 2])
        view.shapes.add_sphere(center="[0,0,0] angstrom", radius="1 angstrom", tag="site")
        view.movie.set_baseline(1000, camera=CAMERA)
        yield view


def test_camera_structure_and_visibility_tracks_are_independent(authored):
    movie = authored.movie
    assert movie.evaluate(500)["camera"] == CAMERA
    camera_track = _track("camera", "camera", "pose", (1000, END))
    movie.add_track(camera_track)
    before = movie.evaluate(500)["camera"]
    movie.add_track(_track("frame", "structure", "index", (300, 2)))
    movie.add_track(_track("hide-region", "region", "visible", (200, False), target="site"))
    movie.add_track(_track("hide-shape", "shape", "visible", (700, False), target="site"))
    result = movie.evaluate(500)
    assert result["camera"] == before
    np.testing.assert_allclose(result["camera"]["position"], [1, 0, 15], atol=1e-12)
    assert result["structure_index"] == 2
    visible = {(row["domain"], row["tag"]): row["visible"] for row in result["visibility"]}
    assert visible[("region", "site")] is False
    assert visible[("shape", "site")] is True
    assert np.linalg.norm(result["camera"]["up"]) == pytest.approx(1)
    assert result["camera"]["up"][2] == pytest.approx(0)
    assert movie.evaluate(1000)["camera"] == END
    assert movie.evaluate(500) == result
    assert authored.player.index == 0

    camera_track["keys"][0]["value"] = CAMERA
    result["camera"]["position"][0] = 99
    recipe = movie.to_dict()
    recipe["baseline"]["scene"]["whole"]["visible"] = False
    assert movie.evaluate(500)["camera"] == before
    assert movie.to_dict()["baseline"]["scene"]["whole"]["visible"] is True


def test_edits_and_imports_are_transactional(authored):
    movie = authored.movie
    movie.add_track(_track("frame", "structure", "index", (700, 2)))
    before = movie.to_dict()
    with pytest.raises(ValueError, match="one track per target property"):
        movie.add_track(_track("duplicate", "structure", "index", (700, 1)))
    with pytest.raises(ValueError, match="Structure index"):
        movie.update_track("frame", keys=[{"time_ms": 100, "value": 3}])
    with pytest.raises(ValueError, match="Key time"):
        movie.set_duration(699)
    invalid = movie.to_dict()
    invalid["baseline"]["camera"]["up"] = [0, 0, 1]
    with pytest.raises(ValueError, match="parallel"):
        movie.from_dict(invalid)
    invalid = movie.to_dict()
    invalid["baseline"]["scene"]["structure"]["fingerprint"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="different ordered structure"):
        movie.from_dict(invalid)
    assert movie.to_dict() == before

    movie.update_track("frame", keys=[{"time_ms": 400, "value": 1}])
    assert movie.evaluate(500)["structure_index"] == 1
    movie.remove_track("frame")
    assert movie.evaluate(500)["structure_index"] == 0


def test_recipe_and_session_preserve_tracks_without_reapplying_them(authored, tmp_path):
    movie = authored.movie
    movie.add_track(_track("orbit", "camera", "pose", (1000, END)))
    movie.add_track(_track("frame", "structure", "index", (300, 2)))
    movie.add_track(_track("visibility", "region", "visible", (400, False), target="site"))
    expected = movie.to_dict()
    evaluated = movie.evaluate(500)
    recipe_path = tmp_path / "movie.json"
    movie.save(recipe_path)
    movie.clear()
    movie.load(recipe_path)
    assert movie.to_dict() == expected

    path = tmp_path / "work.msv"
    authored.save_session(path)
    with msv.load_session(path) as restored:
        assert restored.movie.to_dict() == expected
        assert restored.movie.evaluate(500) == evaluated
        assert restored.player.index == authored.player.index
        restored.movie.validate()

    broken = tmp_path / "broken.msv"
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(broken, "w") as destination:
        for member in source.namelist():
            content = source.read(member)
            if member == "movie.json":
                invalid = json.loads(content)
                invalid["baseline"]["binding"]["fingerprint"] = "sha256:" + "0" * 64
                if "sources" in invalid["baseline"]["scene"]:
                    invalid["baseline"]["scene"]["sources"]["binding"] = invalid["baseline"]["binding"]
                content = json.dumps(invalid)
            destination.writestr(member, content)
    with msv.demo["dialanine"] as destination:
        original = destination.molsys
        with pytest.raises(SessionFormatError, match="Movie recipe does not match"):
            msv.load_session(broken, view=destination)
        assert destination.molsys is original


def test_recipe_binding_and_scene_target_are_checked(authored, tmp_path):
    authored.movie.add_track(_track("visibility", "region", "visible", (100, False), target="site"))
    with msv.demo["dialanine"] as another:
        with pytest.raises(ValueError, match="molecular binding"):
            another.movie.from_dict(authored.movie.to_dict())
    authored.regions["site"].delete()
    with pytest.raises(ValueError, match="missing or changed"):
        authored.movie.validate()
    destination = tmp_path / "unchanged.msv"
    destination.write_bytes(b"existing file")
    with pytest.raises(ValueError, match="missing or changed"):
        authored.save_session(destination)
    assert destination.read_bytes() == b"existing file"


def test_announced_coordinate_edit_invalidates_a_same_size_binding(authored):
    authored.movie.add_track(_track("frame", "structure", "index", (700, 2)))
    coordinates = authored.molsys.structures.coordinates.copy()
    coordinates[0, 0, 0] *= 2
    authored.molsys.structures.coordinates = coordinates
    authored.apply_system_edit(authored.molsys)
    with pytest.raises(ValueError, match="molecular binding"):
        authored.movie.evaluate(500)
