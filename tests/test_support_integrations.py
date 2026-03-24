from __future__ import annotations

from pathlib import Path

import pytest

from molsysviewer import config
from molsysviewer import _depdigest as depdigest_config
from molsysviewer._private import variables
from molsysviewer._pyunitwizard import puw


def test_package_checks_dependencies_before_importing_heavy_modules():
    init_text = Path("molsysviewer/__init__.py").read_text(encoding="utf-8")

    check_pos = init_text.index('_check_dependency(__name__)')
    pyw_pos = init_text.index("from ._pyunitwizard import puw as pyunitwizard")
    demo_pos = init_text.index("from .demo import demo")
    new_view_pos = init_text.index("from .new_view import new_view")
    viewer_pos = init_text.index("from .viewer import MolSysView")

    assert check_pos < pyw_pos
    assert check_pos < demo_pos
    assert check_pos < new_view_pos
    assert check_pos < viewer_pos


def test_runtime_and_config_share_same_pyunitwizard_defaults():
    puw.configure.reset()
    puw.configure.load_library("pint")

    config.set_default_quantities_form(skip_digestion=True)
    config.set_default_quantities_parser(skip_digestion=True)
    config.set_default_standard_units(skip_digestion=True)

    assert puw.configure.get_default_form() == "pint"
    assert puw.configure.get_default_parser() == "pint"
    assert list(puw.configure.get_standard_units().keys()) == [
        "nm",
        "ps",
        "K",
        "mole",
        "amu",
        "e",
        "kJ/mol",
        "kJ/(mol*nm)",
        "kJ/(mol*nm**2)",
        "radians",
    ]


def test_depdigest_config_lists_support_stack_as_hard_dependencies():
    for library_name in ["argdigest", "depdigest", "pyunitwizard", "smonitor"]:
        assert library_name in depdigest_config.LIBRARIES
        assert depdigest_config.LIBRARIES[library_name]["type"] == "hard"


def test_private_variables_use_local_pyunitwizard_instance():
    assert variables.puw is puw


def test_coordinate_compatibility_rejects_non_length_units():
    bad = puw.quantity([1.0, 2.0, 3.0], "ps")
    good = puw.quantity([1.0, 2.0, 3.0], "nm")

    assert variables.is_compatible_with_coordinates(bad) is False
    assert variables.is_compatible_with_coordinates(good) is True


def test_make_coordinates_like_normalizes_plain_sequences():
    coords = puw.quantity([1.0, 2.0, 3.0], "nm")

    output = variables.make_coordinates_like(coords)

    assert puw.get_value(output).shape == (1, 1, 3)
    assert puw.get_unit(output) == puw.get_unit(coords)
