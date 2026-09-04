"""Each `info` describes one subject, and only that one.

Before `uibcdf/molsysviewer#71` a single `info` meant either the scene or the molecular
system depending on a `source` argument, and `element`/`selection`/`syntax` applied to only
one of the two meanings. Now:

* `view.info()` — what is in the scene and how it is drawn.
* `whole.info()` — the molecular system, `msm.info` on it.
* `region.info()` — the same system masked to the region's atoms.

The split is pinned in both directions: each answers its own subject, and each *refuses*
the other's arguments rather than accepting them and quietly answering the wrong question.
"""

from __future__ import annotations

import molsysmt as msm
import pytest

from molsysviewer import demo


@pytest.fixture
def populated():
    view = demo["dialanine"]
    view.styles.apply(representation="cartoon", color_scheme="secondary_structure_default")
    view.regions.add(tag="site", atom_indices=[0, 1, 2], representation="ball-and-stick")
    view.selections.add_selection("sel", selection=[0, 1, 2])
    view.annotations.add_label("anchor", group_index=[0], tag="ann1")
    return view


# --- view.info: the scene ----------------------------------------------------------


def test_view_info_reports_the_scene_objects(populated):
    table = populated.info().data

    assert set(table["section"]) >= {
        "whole", "styles", "regions", "layers", "annotations", "selections", "active_selection",
    }
    assert ((table["section"] == "whole") & (table["representation"] == "cartoon")).any()
    assert ((table["section"] == "regions") & (table["tag"] == "site") & (table["n atoms"] == 3)).any()
    assert ((table["section"] == "annotations") & (table["tag"] == "ann1")).any()
    assert ((table["section"] == "selections") & (table["tag"] == "sel")).any()


def test_view_info_honours_output_type(populated):
    dataframe = populated.info(output_type="dataframe")
    dictionary = populated.info(output_type="dictionary")

    assert "section" in dataframe.columns
    assert isinstance(dictionary, list)
    assert any(item["section"] == "whole" for item in dictionary)


def test_view_info_refuses_the_molecular_arguments():
    """Loudly, so a call written for the old meaning cannot answer the wrong question."""
    view = demo["dialanine"]

    for rejected in ({"element": "molecule"}, {"selection": "all"}, {"source": "molsys"}):
        with pytest.raises(Exception) as raised:
            view.info(**rejected)
        assert "does not accept" in str(raised.value), (raised.value, rejected)


# --- whole.info and region.info: the molecular system ------------------------------


def test_whole_info_is_msm_info_on_the_system():
    view = demo["1TCD"]

    assert view.whole.info(element="molecule", output_type="dictionary") \
        == msm.info(view._molsys, element="molecule", output_type="dictionary")  # noqa: SLF001


def test_region_info_is_msm_info_masked_to_the_regions_atoms():
    view = demo["1TCD"]
    view.make_regions_by("chain")
    regions = view.regions
    region = list(regions.values())[0] if hasattr(regions, "values") else regions[0]

    assert region.info(element="atom", output_type="dictionary") \
        == msm.info(
            view._molsys,  # noqa: SLF001
            element="atom",
            selection=list(region.atom_indices),
            output_type="dictionary",
        )


def test_a_region_reports_fewer_atoms_than_the_whole():
    """Guards the masking itself: equal tables would satisfy the test above by accident."""
    view = demo["1TCD"]
    view.make_regions_by("chain")
    regions = view.regions
    region = list(regions.values())[0] if hasattr(regions, "values") else regions[0]

    assert len(region.info(element="atom", output_type="dictionary")) \
        < len(view.whole.info(element="atom", output_type="dictionary"))


def test_the_molecular_info_does_not_report_the_scene():
    """The other half of the split: no representation or visibility column here."""
    view = demo["1TCD"]
    rows = view.whole.info(element="system", output_type="dictionary")

    assert not any("representation" in row or "visible" in row for row in rows), rows[:1]
