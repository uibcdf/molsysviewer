"""Human-review loading regressions exercised with real molecular demos."""

import pytest

import molsysviewer as msv


@pytest.mark.parametrize("labels", [["Proteína", "Cafeína", "Proteína"], ["Cafe\u0301ina", "配体", "配体"]])
def test_source_region_labels_preserve_unicode_and_identity(labels, tmp_path):
    with msv.demo["dialanine"] as demo:
        source = demo.molsys
        with msv.new_view() as batch, msv.new_view() as progressive:
            batch.load([source] * 3, multiple=True, labels=labels)
            for label in labels:
                progressive.load(source, label=label)
            expected = labels[:2] + [labels[2] + "__2"]
            for view in (batch, progressive):
                assert [record["label"] for record in view.load_blocks] == labels
                assert [record["region_tag"] for record in view.load_blocks] == expected
                assert [view.regions[tag].atom_indices for tag in expected] == [
                    tuple(range(index * 22, (index + 1) * 22)) for index in range(3)
                ]
            region = progressive.regions[expected[0]]
            uid = region.uid
            region.rename("Región revisada")
            assert progressive.load_blocks[0]["region_tag"] == "Región revisada"
            assert progressive.load_blocks[0]["region_uid"] == uid
            session = tmp_path / "unicode.msv"
            progressive.save_session(session)
            with msv.load_session(session) as restored:
                assert restored.load_blocks == progressive.load_blocks
                assert restored.regions["Región revisada"].uid == uid
                assert restored.regions["Región revisada"].atom_indices == region.atom_indices


def test_new_sources_do_not_retag_existing_session_regions(tmp_path):
    with msv.demo["dialanine"] as demo, msv.new_view() as view:
        view.load([demo.molsys] * 2, multiple=True, labels=["Proteína", "Cafeína"])
        view.regions["Proteína"].rename("Prote_na")
        view.regions["Cafeína"].rename("Cafe_na")
        before = view.load_blocks
        session = tmp_path / "legacy-tags.msv"
        view.save_session(session)
        with msv.load_session(session) as restored:
            assert restored.load_blocks == before
            restored.load(demo.molsys, label="Cafeína")
            assert restored.load_blocks[:2] == before
            assert restored.load_blocks[2]["region_tag"] == "Cafeína"


def test_system_rebuild_announces_pending_structure():
    with msv.demo["dialanine"] as demo, msv.new_view() as view:
        view.load(demo.molsys)
        for mode in ("add", "replace"):
            view.load(demo.molsys, mode=mode)
            # The transport recorder starts a fresh log at clear_all.
            messages = view._test_message_log
            clear = next(message for message in messages if message["op"] == "clear_all")
            assert clear["awaiting_structure"] is True
            assert any(message["op"] == "load_molsys_payload" for message in messages)
        view.reset_viewer()
        clear = next(message for message in reversed(view._test_message_log) if message["op"] == "clear_all")
        assert clear["awaiting_structure"] is False
