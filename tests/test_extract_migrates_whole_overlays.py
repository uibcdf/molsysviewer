"""An extracted view must be able to save itself.

`uibcdf/molsysviewer#74`: `view.extract` migrated the replayable *message* of each overlay
and never created the Python *object*. The extracted view drew correctly and then raised
`AttributeError` the first time `export_state` resolved a record through `get()` — so it
could not be saved, and because scene-history snapshots call `export_state`, any
scene-recording operation on it crashed. Adding a region to it raised, which is how the
defect surfaced at all.

The two halves are checked separately, because either can be there without the other, and
`records()` alone was what made this look fine.
"""

from __future__ import annotations

import pytest

import molsysviewer as msv


@pytest.fixture
def populated():
    view = msv.demo["1TCD"]
    view.regions.add(selection='molecule_type=="protein"', tag="prot", representation="cartoon")
    view.shapes.add_sphere(center="[1.0, 1.0, 1.0] nm", radius="0.5 nm", tag="s1")
    view.annotations.add_annotation(text="hola", selection="atom_index==[0]", tag="a1")
    view.measurements.add_distance(
        selection_a="atom_index==[0]", selection_b="atom_index==[10]", tag="d1"
    )
    return view


@pytest.fixture
def extracted(populated):
    return populated.extract(selection='molecule_type=="protein"')


COLLECTIONS = ["shapes", "annotations", "measurements", "regions"]


@pytest.mark.parametrize("collection", COLLECTIONS)
def test_the_object_arrives_and_not_only_the_record(extracted, collection):
    """`records()` reads the message history; `tags()` reads `_scene_objects`.

    Migrating only the first is the defect: `tags()` was empty while `records()` listed
    the overlay, so `get(tag)` returned `None`.
    """
    coll = getattr(extracted, collection)
    assert len(coll.records()) == 1, f"{collection}: the record did not migrate"
    assert len(list(coll.tags())) == 1, (
        f"{collection}: the record migrated but the object did not — get() will return None"
    )


@pytest.mark.parametrize("collection", COLLECTIONS)
def test_nothing_is_migrated_twice(populated, extracted, collection):
    """`_send` records the message itself, so appending as well doubled shapes and labels.

    Measurements escaped it only because their recorder de-duplicates by tag, which is why
    two collections were visibly wrong and the third was quietly wrong.
    """
    assert len(getattr(extracted, collection).records()) == len(
        getattr(populated, collection).records()
    )


def test_the_extracted_view_can_be_saved(extracted):
    """The consequence that made this worth fixing rather than noting."""
    state = extracted.export_state()
    assert [record["tag"] for record in state["measurements"]] == ["d1"]
    assert [record["tag"] for record in state["annotations"]] == ["a1"]


def test_a_scene_operation_on_the_extracted_view_does_not_crash(extracted):
    """Scene history snapshots call `export_state`, so this crashed before the fix."""
    extracted.regions.add(selection="all", tag="posterior")
    assert "posterior" in extracted.regions.tags()


def test_an_overlay_whose_atoms_all_vanish_is_not_registered(populated):
    """The migration is conditional, and the registration must follow the same condition.

    An atom-anchored overlay whose atoms are all outside the subset is dropped by the
    remapper. Registering it anyway would leave an object with no message — the mirror of
    the bug this file guards.
    """
    water_only = populated.extract(selection='molecule_type=="water"')
    assert len(water_only.annotations.records()) == len(list(water_only.annotations.tags()))
    assert len(water_only.measurements.records()) == len(list(water_only.measurements.tags()))
