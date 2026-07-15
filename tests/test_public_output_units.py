from __future__ import annotations

import json
import subprocess
import sys

import pytest

from molsysviewer import pyunitwizard as puw
from molsysviewer.demo import demo


FACTORY_STANDARD_UNITS = [
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


def _set_length_standard(unit: str) -> None:
    standards = list(FACTORY_STANDARD_UNITS)
    standards[0] = unit
    puw.configure.set_standard_units(standards)


def test_public_output_follows_the_configured_default_unit():
    original = list(puw.configure.get_standard_units())
    try:
        _set_length_standard("nm")
        view = demo["dialanine"]
        view.widget.send = lambda _message: None  # type: ignore[method-assign]
        view.measurements.add_distance([0], [1], tag="distance")
        shape = view.shapes.add(
            "sphere",
            center=puw.quantity([5.0, 0.0, 0.0], "angstrom"),
            radius=puw.quantity(5.0, "angstrom"),
            tag="sphere",
            skip_digestion=True,
        )
        section = view.scene.add_section(
            puw.quantity([5.0, 0.0, 0.0], "angstrom"),
            [1.0, 0.0, 0.0],
            tag="section",
        )

        measurement_nm = view._measurement_summary_records()[0]  # noqa: SLF001
        shape_nm = view._shape_summary_records()[0]  # noqa: SLF001
        section_nm = view._section_summary_records()[0]  # noqa: SLF001
        assert {measurement_nm["unit"], shape_nm["radius"]["unit"], section_nm["unit"]} == {"nanometer"}
        assert shape_nm["radius"]["magnitude"] == pytest.approx(0.5)
        assert section_nm["point"] == pytest.approx([0.5, 0.0, 0.0])
        assert str(puw.get_unit(shape.get_center())) == "nanometer"
        assert str(puw.get_unit(section.get_point())) == "nanometer"

        _set_length_standard("angstrom")
        measurement_angstrom = view._measurement_summary_records()[0]  # noqa: SLF001
        shape_angstrom = view._shape_summary_records()[0]  # noqa: SLF001
        section_angstrom = view._section_summary_records()[0]  # noqa: SLF001
        assert {
            measurement_angstrom["unit"],
            shape_angstrom["radius"]["unit"],
            section_angstrom["unit"],
        } == {"angstrom"}
        assert shape_angstrom["radius"]["magnitude"] == pytest.approx(5.0)
        assert section_angstrom["point"] == pytest.approx([5.0, 0.0, 0.0])
        assert str(puw.get_unit(shape.get_center())) == "angstrom"
        assert str(puw.get_unit(section.get_point())) == "angstrom"
    finally:
        puw.configure.set_standard_units(original)


def test_fresh_lazy_import_configures_standards_before_building_summaries():
    script = """
import json
import molsysviewer

view = molsysviewer.MolSysView()
view.widget.send = lambda message: None
view.scene.add_section([0.1, 0.2, 0.3], [1.0, 0.0, 0.0], tag='cut')
print(json.dumps(view._section_summary_records()[0]))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["unit"] == "nanometer"
