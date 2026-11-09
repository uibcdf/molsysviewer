"""Recover a real scientific session and continue its structure series."""

from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer._pyunitwizard import puw

import molsysviewer as msv


@pytest.mark.parametrize("mode", ["append_structures", "auto"])
def test_recovered_append_preserves_evaluated_prefix_and_analysis_identity(tmp_path, mode):
    with msv.demo["pentalanine"] as seed:
        with seed.extract(structure_indices=[0, 8, 3]) as source:
            analysis = msm.interactions.hbonds.get_buch_hbonds(
                source.molsys, structure_indices=[2, 0], pbc=False, output_type="molsysmt.Interactions"
            )
            source.interactions.attach(analysis, name="continued", assume_aligned=True)
            source.interactions.add("continued", tag="hbonds")
            source.regions.add(selection=[0, 2, 4], tag="retained")
            coordinates = puw.get_value(source.molsys.structures.coordinates, to_unit="nm").copy()
            observations = deepcopy(analysis.query().to_dict())
            filename = tmp_path / "continued.msv"
            source.save_session(filename)
            with msv.load_session(filename) as recovered:
                region = recovered.regions["retained"]
                visual = recovered.interactions["hbonds"]
                records = recovered.load_blocks
                state = deepcopy(recovered.export_state())
                system = recovered.molsys
                with pytest.raises(ValueError, match="explicit analysis merge"):
                    recovered.load(source.molsys, mode=mode, structure_indices=[2, 0])
                assert recovered.molsys is system
                assert recovered.export_state() == state

                recovered.load(seed.molsys, mode=mode, structure_indices=[3, 0])
                expected = np.concatenate([coordinates, coordinates[[2, 0]]])
                np.testing.assert_array_equal(
                    puw.get_value(recovered.molsys.structures.coordinates, to_unit="nm"), expected
                )
                retained = recovered.interactions.get_analysis("continued")
                np.testing.assert_array_equal(
                    retained.evaluated_structure_indices, analysis.evaluated_structure_indices
                )
                assert retained.n_structures == recovered.player.n_structures == 5
                data = retained.query().to_dict()
                for key in ("occurrence_indices", "structure_indices", "relation_indices"):
                    np.testing.assert_array_equal(data[key], observations[key])
                assert recovered.interactions["hbonds"] is visual
                assert recovered.regions["retained"] is region
                assert region.atom_indices == (0, 2, 4)
                assert recovered.load_blocks == records
                for index, status in [
                    (0, "evaluated"),
                    (1, "unevaluated"),
                    (2, "evaluated"),
                    (3, "unevaluated"),
                    (4, "unevaluated"),
                ]:
                    assert recovered.interactions.inspect("hbonds", structure_index=index)["status"] == status

                recovered.save_session(tmp_path / "appended.msv")
                with msv.load_session(tmp_path / "appended.msv") as continued:
                    np.testing.assert_array_equal(
                        continued.interactions.get_analysis("continued").evaluated_structure_indices,
                        analysis.evaluated_structure_indices,
                    )
                    np.testing.assert_array_equal(
                        puw.get_value(continued.molsys.structures.coordinates, to_unit="nm"), expected
                    )
                # The explicit append contract must not relax arbitrary edit invalidation.
                recovered.apply_system_edit(msm.copy(recovered.molsys))
                assert recovered.interactions.get_analysis("continued").evaluated_structure_indices.size == 0
                np.testing.assert_array_equal(analysis.evaluated_structure_indices, [2, 0])
                np.testing.assert_array_equal(
                    puw.get_value(source.molsys.structures.coordinates, to_unit="nm"), coordinates
                )
