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


def test_contract_wrappers_bypass_redigestion_after_local_digest():
    from molsysviewer.demo import demo

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", representation="sticks", skip_digestion=True)

    observed: list[tuple[str, object]] = []

    def fake_contains(*args, **kwargs):
        observed.append(("contains", kwargs.get("skip_digestion")))
        return True

    def fake_get(*args, **kwargs):
        observed.append(("get", kwargs.get("skip_digestion")))
        return {"ok": True}

    def fake_info(*args, **kwargs):
        observed.append(("info", kwargs.get("skip_digestion")))
        return {"ok": True}

    def fake_select(*args, **kwargs):
        observed.append(("select", kwargs.get("skip_digestion")))
        return [0, 1]

    def fake_is_composed_of(*args, **kwargs):
        observed.append(("is_composed_of", kwargs.get("skip_digestion")))
        return True

    view.contains = fake_contains  # type: ignore[method-assign]
    view.get = fake_get  # type: ignore[method-assign]
    view.info = fake_info  # type: ignore[method-assign]
    view.select = fake_select  # type: ignore[method-assign]
    view.is_composed_of = fake_is_composed_of  # type: ignore[method-assign]

    region.contains("all")
    region.get()
    region.info()
    region.select("all")
    region.is_composed_of("all")

    assert observed
    assert all(value is True for _, value in observed)


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
