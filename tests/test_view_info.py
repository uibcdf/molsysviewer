from molsysviewer import demo


def test_view_info_source_view_returns_styler_by_default():
    view = demo["dialanine"]
    view.styles.apply(representation="cartoon", color_scheme="secondary_structure_default")
    view.new_region(tag="site", atom_indices=[0, 1, 2], representation="ball-and-stick")
    view.selections.add_selection("sel", selection=[0, 1, 2])
    view.annotations.add_label("anchor", group_index=[0], tag="ann1")

    info = view.info(source="view")
    table = info.data

    assert hasattr(info, "data")
    assert "section" in table.columns
    assert "tag" in table.columns
    assert "kind" in table.columns
    assert "representation" in table.columns
    assert "preset" in table.columns
    assert "n atoms" in table.columns
    assert "n members" in table.columns
    assert "n picks" in table.columns
    assert set(table["section"]) >= {
        "whole",
        "styles",
        "regions",
        "layers",
        "annotations",
        "selections",
        "active_selection",
    }
    assert ((table["section"] == "whole") & (table["representation"] == "cartoon")).any()
    assert ((table["section"] == "regions") & (table["tag"] == "site") & (table["n atoms"] == 3)).any()
    assert ((table["section"] == "annotations") & (table["tag"] == "ann1")).any()
    assert ((table["section"] == "selections") & (table["tag"] == "sel")).any()
    assert ((table["section"] == "whole") & (table["details"].str.contains("color_scheme=secondary_structure_default", regex=False))).any()
    assert ((table["section"] == "layers") & (table["details"].str.contains("annotations=", regex=False))).any()
    assert ((table["section"] == "selections") & (table["details"].str.contains("element / group", regex=False))).any()


def test_view_info_source_view_can_return_dataframe_or_dictionary():
    view = demo["dialanine"]

    dataframe = view.info(source="view", output_type="dataframe")
    dictionary = view.info(source="view", output_type="dictionary")

    assert hasattr(dataframe, "columns")
    assert "section" in dataframe.columns
    assert isinstance(dictionary, list)
    assert any(item["section"] == "whole" for item in dictionary)


def test_view_info_source_all_converts_both_sections_with_requested_output_type():
    view = demo["dialanine"]

    info = view.info(source="all", output_type="dictionary")

    assert set(info.keys()) == {"molsys", "view"}
    assert isinstance(info["molsys"], list)
    assert isinstance(info["view"], list)
    assert any(item["section"] == "whole" for item in info["view"])


def test_view_info_source_molsys_can_return_dataframe():
    view = demo["dialanine"]

    info = view.info(source="molsys", output_type="dataframe")

    assert hasattr(info, "columns")
