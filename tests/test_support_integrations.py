from __future__ import annotations

import ast
from pathlib import Path

import pytest

from molsysviewer import config
from molsysviewer import _depdigest as depdigest_config
from molsysviewer._private.argdigest.argument.atom_indices import digest_atom_indices
from molsysviewer._private.argdigest.argument.element import digest_element
from molsysviewer._private.argdigest.argument.mask import digest_mask
from molsysviewer._private import variables
from molsysviewer._pyunitwizard import puw


def test_package_checks_dependencies_before_importing_heavy_modules():
    init_text = Path("molsysviewer/__init__.py").read_text(encoding="utf-8")

    check_pos = init_text.index('_check_dependency(__name__)')
    lazy_registry_pos = init_text.index("_LAZY_ATTRIBUTES = {")

    assert check_pos < lazy_registry_pos
    assert '"pyunitwizard": ("._pyunitwizard", "puw")' in init_text
    assert '"demo": (".demo", "demo")' in init_text
    assert '"new_view": (".new_view", "new_view")' in init_text
    assert '"MolSysView": (".viewer", "MolSysView")' in init_text


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


def test_depdigest_mapping_covers_primary_molsysmt_input_forms():
    assert depdigest_config.MAPPING["molsysmt_MolSys"] == "molsysmt"
    assert depdigest_config.MAPPING["file_h5msm"] == "molsysmt"
    assert depdigest_config.MAPPING["file_pdb"] == "molsysmt"


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


def test_scoped_wrappers_pass_skip_digestion_through_instead_of_forcing_it():
    """The contract `uibcdf/molsysviewer#71` replaced, and why the replacement is the point.

    These wrappers used to digest locally and then forward to the view with
    `skip_digestion=True`, so MolSysMT never checked what it was about to consume. That is
    what let two copies of the same rules drift: our `group_index` returned `True` for one
    caller and `[True]` for another, and `region.get` refused 77 of the 118 attributes
    `msm.get` answers.

    Now they forward to MolSysMT and pass `skip_digestion` **through**. The argument means
    what it says: `True` skips digestion everywhere, and the default checks once, where the
    arguments are owned.
    """
    import molsysmt as msm

    from molsysviewer.demo import demo

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", representation="sticks", skip_digestion=True)

    observed: list[object] = []
    original = msm.get

    def spy(*args, **kwargs):
        observed.append(kwargs.get("skip_digestion"))
        return original(*args, **kwargs)

    msm.get = spy  # type: ignore[assignment]
    try:
        region.get(element="atom", index=True)
        view.whole.get(element="atom", index=True)
        # A canonical name, because `skip_digestion=True` skips the renaming too:
        # the bare `index` is resolved *by* digestion, so asking for no digestion and
        # then a bare name is a contradiction. That is the argument meaning what it says.
        region.get(element="atom", atom_index=True, skip_digestion=True)
    finally:
        msm.get = original  # type: ignore[assignment]

    assert observed[:2] == [False, False], (
        f"the default must let MolSysMT digest, got {observed[:2]}"
    )
    assert observed[2] is True, "skip_digestion=True must reach MolSysMT, not be swallowed"


def test_skipping_digestion_also_skips_the_renaming():
    """Measured while writing the test above, and worth pinning rather than rediscovering.

    Bare names and synonyms are resolved *by* digestion. `skip_digestion=True` therefore
    means no rename either, and `get(element="atom", index=True, skip_digestion=True)`
    raises `KeyError: 'index'`. Not a defect — the argument doing exactly what it says —
    but a sharp edge for anyone reaching for the fast path.
    """
    from molsysviewer.demo import demo

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    assert list(view.whole.get(element="atom", index=True)) \
        == list(view.whole.get(element="atom", atom_index=True, skip_digestion=True))

    with pytest.raises(KeyError):
        view.whole.get(element="atom", index=True, skip_digestion=True)


def test_thin_variadic_forwarders_do_not_carry_digest_decorators():
    path = Path("molsysviewer/whole.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    offenders: list[str] = []

    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "Whole":
            continue
        for item in node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            has_varargs = item.args.vararg is not None or item.args.kwarg is not None
            decorators = [ast.unparse(deco) for deco in item.decorator_list]
            has_digest = any("digest" in deco for deco in decorators)
            named_runtime_args = [
                arg.arg
                for arg in item.args.args[1:]
                if arg.arg != "skip_digestion"
            ]
            kwonly_runtime_args = [arg.arg for arg in item.args.kwonlyargs if arg.arg != "skip_digestion"]
            has_named_contract = bool(named_runtime_args or kwonly_runtime_args)
            if has_varargs and not has_named_contract and has_digest:
                offenders.append(item.name)

    assert offenders == []


def test_argdigest_caller_aliases_accept_module_level_molsysviewer_wrappers():
    assert digest_mask("all", caller="molsysviewer.viewer.select") == "all"
    assert digest_mask(None, caller="molsysviewer.regions.info") is None
    assert digest_atom_indices("all", caller="molsysviewer.viewer.new_region") is None
    assert digest_element(None, caller="molsysviewer.viewer.set") is None
