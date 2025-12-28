from molsysviewer.loaders import __all__ as loaders_all


def test_loaders_exports():
    exported = set(loaders_all)
    expected = {
        "load_from_molsysmt",
    }
    assert exported == expected
