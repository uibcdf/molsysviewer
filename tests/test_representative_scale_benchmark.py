from devtools.benchmarks.representative_scale_gate import CASE_SPECS, build_representative_molsys


def test_representative_scale_matrix_uses_intact_molecular_supercells():
    assert CASE_SPECS["small"].resource_name == "181l.bcif.gz"
    assert CASE_SPECS["medium"].resource_name == "traj_chicken_villin_HP35_solvated.h5msm"
    assert CASE_SPECS["large"].copies == 24
    assert CASE_SPECS["xlarge"].copies == 72
    for spec in CASE_SPECS.values():
        assert spec.copies == spec.grid[0] * spec.grid[1] * spec.grid[2]


def test_small_representative_fixture_preserves_atoms_and_does_not_invent_time():
    molsys = build_representative_molsys("small", 2)

    assert molsys.get_n_atoms() == 2882
    assert molsys.structures.n_structures == 2
    assert molsys.structures.box is not None
    assert molsys.structures.time is None
