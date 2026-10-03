"""Real chemistry, image reconstruction and persistence at the Viewer boundary."""

from devtools.qualify_interactions import qualify_disulfides, qualify_periodic, qualify_solvated, qualify_trajectory


def test_nonconsecutive_real_trajectory_survives_all_storage_routes(tmp_path):
    report = qualify_trajectory(tmp_path)
    assert report["source_frames"] == [4999, 0, 73, 3]
    assert report["evaluated_local_frames"] == [3, 0, 2]
    assert report["observations"] > 0
    assert len(report["round_trips"]) == 3


def test_real_residue_reimaging_retains_geometry_under_angstrom_policy(tmp_path):
    report = qualify_periodic(tmp_path)
    assert report["nonzero_image_observations"] > 0
    assert report["policy"] == "angstrom"


def test_solvated_protein_detector_observations_match_prepared_geometry():
    report = qualify_solvated()
    assert report["atoms"] > 4000 and report["observations"] > 100
    assert report["structures"] == 1


def test_real_cysteine_proximities_remain_candidates_without_topology_edits(tmp_path):
    report = qualify_disulfides(tmp_path)
    assert report["observations"] > 0
    assert report["topology_unchanged"] is True
