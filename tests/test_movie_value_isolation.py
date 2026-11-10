"""Guard the version-1 Movie value boundaries with real molecular Views."""

from copy import deepcopy

import pytest

import molsysviewer as msv


def _change_pose(keyframes):
    keyframes[0]["camera"]["position"][0] = 123.0
    keyframes[0]["layer_visibility"]["site"] = True


@pytest.mark.parametrize("boundary", ["keyframes", "to_dict", "from_dict"])
def test_movie_value_boundaries_are_detached(boundary):
    with msv.demo["dialanine"] as view:
        view.movie.add_keyframe(
            0.0,
            camera={"position": [0.0, 0.0, 40.0], "target": [0.0, 0.0, 0.0], "up": [0.0, 1.0, 0.0]},
            layer_visibility={"site": False},
        )
        view.movie.add_keyframe(1000.0, structure_index=0)
        expected = deepcopy(view.movie.to_dict())
        if boundary == "keyframes":
            _change_pose(view.movie.keyframes)
        elif boundary == "to_dict":
            _change_pose(view.movie.to_dict()["keyframes"])
        else:
            incoming = deepcopy(expected)
            with msv.demo["dialanine"] as independent:
                independent.movie.from_dict(incoming)
                _change_pose(incoming["keyframes"])
                assert independent.movie.to_dict() == expected
        assert view.movie.to_dict() == expected
