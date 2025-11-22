from molsysviewer.loaders import __all__ as loaders_all


def test_loaders_exports():
    exported = set(loaders_all)
    expected = {
        "load_from_molsysmt",
        "load_pdb_string",
        "load_mmcif_string",
        "load_pdb_id",
        "load_from_url",
    }
    assert exported == expected
