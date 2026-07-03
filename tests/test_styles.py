from molsysviewer import MolSysView, Style, demo
from molsysviewer.config.user_presets import user_presets
from molsysviewer.styles import BUILTIN_FOCUS_STYLES


def test_style_requires_exactly_one_source():
    try:
        Style(representation="cartoon", preset="auto")
    except ValueError as exc:
        assert "exactly one" in str(exc)
    else:
        raise AssertionError("Expected ValueError when multiple style sources are provided.")


def test_styles_apply_representation_delegates_to_whole_message_flow():
    view = MolSysView()

    style = view.styles.apply(representation="cartoon")

    assert style.representation == "cartoon"
    assert view._message_history[-1]["op"] == "set_global_representation"  # noqa: SLF001
    assert view._message_history[-1]["representation"] == "cartoon"  # noqa: SLF001
    current = view.styles.current()
    assert current is not None
    assert current.representation == "cartoon"
    assert current.preset is None


def test_styles_apply_style_object_tracks_name_and_params():
    view = MolSysView()

    style = Style(preset="polymer-cartoon", name="Polymers", params={"quality": "auto"})
    applied = view.styles.apply(style=style)

    assert applied == style
    assert view._message_history[-1]["op"] == "set_global_representation"  # noqa: SLF001
    assert view._message_history[-1]["preset"] == "polymer-cartoon"  # noqa: SLF001
    assert view._message_history[-1]["params"] == {"quality": "auto"}  # noqa: SLF001
    info = view.styles.info()
    assert info is not None
    assert info["name"] == "Polymers"
    assert info["preset"] == "polymer-cartoon"
    assert info["params"] == {"quality": "auto"}


def test_styles_apply_representation_preserves_structural_color_scheme_param():
    view = MolSysView()

    style = view.styles.apply(representation="cartoon", color_scheme="secondary_structure_default")

    assert style.representation == "cartoon"
    assert view._message_history[-1]["params"] == {"color_scheme": "secondary_structure_default"}  # noqa: SLF001
    current = view.styles.current()
    assert current is not None
    assert current.params["color_scheme"] == "secondary_structure_default"


def test_styles_apply_representation_preserves_structural_size_scheme_param():
    view = MolSysView()

    style = view.styles.apply(representation="cartoon", size_scheme="physical")

    assert style.representation == "cartoon"
    assert view._message_history[-1]["params"] == {"size_scheme": "physical"}  # noqa: SLF001
    current = view.styles.current()
    assert current is not None
    assert current.params["size_scheme"] == "physical"


def test_styles_apply_representation_preserves_advanced_molstar_theme_params():
    view = MolSysView()

    style = view.styles.apply(
        representation="cartoon",
        molstar_color_theme={"name": "residue-name", "params": {"saturation": 0}},
        molstar_size_theme={"name": "uniform", "params": {"value": 2.0}},
    )

    assert style.representation == "cartoon"
    assert view._message_history[-1]["params"] == {  # noqa: SLF001
        "molstar_color_theme": {"name": "residue-name", "params": {"saturation": 0}},
        "molstar_size_theme": {"name": "uniform", "params": {"value": 2.0}},
    }
    current = view.styles.current()
    assert current is not None
    assert current.params["molstar_color_theme"]["name"] == "residue-name"
    assert current.params["molstar_size_theme"]["name"] == "uniform"


def test_styles_curated_scheme_has_priority_over_advanced_molstar_theme_param():
    view = MolSysView()

    view.styles.apply(
        representation="cartoon",
        color_scheme="secondary_structure_default",
        molstar_color_theme="residue-name",
    )

    assert view._message_history[-1]["params"] == {  # noqa: SLF001
        "color_scheme": "secondary_structure_default",
        "molstar_color_theme": "residue-name",
    }


def test_styles_current_recognizes_user_preset_names(tmp_path):
    view = demo["dialanine"]
    preset_name = "demo-style"
    user_presets[preset_name] = {"base": "auto", "options": {}, "rules": []}
    view.styles.apply(style=Style(user_preset=preset_name, params={}))
    current = view.styles.current()
    assert current is not None
    assert current.user_preset == preset_name


def test_styles_registry_supports_add_query_and_clear():
    view = MolSysView()
    style = Style(preset="polymer-cartoon", name="Polymers")

    view.styles.add("publication", style, description="Default publication scene", source="runtime")

    assert view.styles.contains("publication") is True
    assert view.styles.get("publication") == style
    assert view.styles.tags() == ["publication"]
    assert view.styles.count() == 1
    assert view.styles.records() == [
        {
            "tag": "publication",
            "description": "Default publication scene",
            "source": "runtime",
            "style": style.info(),
        }
    ]

    view.styles.clear("publication")
    assert view.styles.count() == 0


def test_styles_apply_by_tag_uses_registered_style():
    view = MolSysView()
    view.styles.add("publication", Style(preset="polymer-cartoon", name="Publication"))

    applied = view.styles.apply(tag="publication")

    assert applied.preset == "polymer-cartoon"
    assert view._message_history[-1]["op"] == "set_global_representation"  # noqa: SLF001
    assert view._message_history[-1]["preset"] == "polymer-cartoon"  # noqa: SLF001


def test_styles_builtin_catalog_exposes_canonical_tags():
    view = MolSysView()

    assert view.styles.builtin_tags() == [
        "atomic-detail",
        "ball-and-stick-element-cpk",
        "cartoon-chain",
        "cartoon-secondary-structure",
        "coarse-surface",
        "default",
        "empty",
        "physicochemical",
        "polymer-and-ligand",
        "polymer-cartoon",
        "spacefill-element-cpk",
    ]
    builtin = view.styles.get_builtin("polymer-and-ligand")
    assert builtin is not None
    assert builtin.preset == "polymer-and-ligand"
    records = view.styles.builtin_records()
    assert any(record["tag"] == "polymer-cartoon" for record in records)


def test_styles_structural_scheme_catalogs_expose_curated_public_options():
    view = MolSysView()

    assert view.styles.structural_color_schemes() == [
        "chain_default",
        "element_cpk",
        "entity_default",
        "illustrative_default",
        "molecule_type",
        "physicochemical",
        "residue_name",
        "secondary_structure_default",
    ]
    assert view.styles.structural_size_schemes() == [
        "physical",
        "uncertainty",
        "uniform",
    ]
    color_records = view.styles.structural_color_scheme_records()
    size_records = view.styles.structural_size_scheme_records()
    assert any(record["tag"] == "residue_name" for record in color_records)
    assert any(record["tag"] == "physical" for record in size_records)


def test_styles_visual_discovery_catalogs_expose_representations_presets_and_advanced_themes():
    view = MolSysView()

    assert view.styles.representation_types() == [
        "backbone",
        "ball-and-stick",
        "carbohydrate",
        "cartoon",
        "ellipsoid",
        "gaussian-surface",
        "gaussian-volume",
        "line",
        "molecular-surface",
        "point",
        "putty",
        "spacefill",
    ]
    assert view.styles.representation_presets() == [
        "atomic-detail",
        "auto",
        "coarse-surface",
        "empty",
        "polymer-and-ligand",
        "polymer-cartoon",
    ]
    representation_records = view.styles.representation_type_records()
    preset_records = view.styles.representation_preset_records()
    assert any(record["tag"] == "ball-and-stick" and "sticks" in record["aliases"] for record in representation_records)
    assert any(record["tag"] == "auto" and "automatic" in record["aliases"] for record in preset_records)

    assert "residue-name" in view.styles.molstar_color_themes()
    assert "physical" in view.styles.molstar_size_themes()
    color_theme_records = view.styles.molstar_color_theme_records()
    size_theme_records = view.styles.molstar_size_theme_records()
    assert any(record["tag"] == "chain-id" for record in color_theme_records)
    assert any(record["tag"] == "uniform" for record in size_theme_records)


def test_styles_representation_param_schema_catalog_exposes_curated_public_knobs():
    view = MolSysView()

    cartoon = view.styles.representation_param_schema("cartoon")
    line = view.styles.representation_param_schema("line")
    records = view.styles.representation_param_schema_records()

    assert cartoon["tag"] == "cartoon"
    assert any(param["name"] == "alpha" for param in cartoon["common_params"])
    assert any(param["name"] == "tubularHelices" for param in cartoon["specific_params"])

    assert line["tag"] == "line"
    assert any(param["name"] == "multipleBonds" for param in line["specific_params"])
    assert any(record["tag"] == "spacefill" for record in records)


def test_styles_apply_by_tag_falls_back_to_builtin_catalog():
    view = MolSysView()

    applied = view.styles.apply(tag="atomic-detail")

    assert applied.preset == "atomic-detail"
    assert view._message_history[-1]["op"] == "set_global_representation"  # noqa: SLF001
    assert view._message_history[-1]["preset"] == "atomic-detail"  # noqa: SLF001


def test_styles_registry_overrides_builtin_with_same_tag():
    view = MolSysView()
    override = Style(representation="cartoon", name="Custom Default")
    view.styles.add("default", override, description="Project override")

    applied = view.styles.apply(tag="default")

    assert applied == override
    assert view._message_history[-1]["representation"] == "cartoon"  # noqa: SLF001


# ---------------------------------------------------------------------------
# Focus Styles
# ---------------------------------------------------------------------------


def test_focus_style_rejects_preset_and_user_preset():
    try:
        Style(representation="cartoon", preset="auto", kind="focus")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for focus style with preset.")

    try:
        Style(preset="auto", kind="focus")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for focus style without representation.")


def test_focus_style_requires_representation():
    try:
        Style(kind="focus")
    except ValueError as exc:
        assert "representation" in str(exc)
    else:
        raise AssertionError("Expected ValueError when focus style has no representation.")


def test_focus_style_kind_validates_unknown_kind():
    try:
        Style(representation="cartoon", kind="unknown")
    except ValueError as exc:
        assert "kind" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown style kind.")


def test_focus_style_info_includes_kind_focus():
    style = Style(representation="cartoon", kind="focus", name="Chain Focus")
    info = style.info()
    assert info["kind"] == "focus"
    assert info["representation"] == "cartoon"
    assert info["preset"] is None


def test_builtin_focus_catalog_exposes_canonical_tags():
    view = MolSysView()
    tags = view.styles.builtin_focus_tags()
    assert tags == ["chain-id", "element-cpk", "hydrophobicity", "secondary-structure"]
    for tag in tags:
        style = view.styles.get_builtin_focus(tag)
        assert style is not None
        assert style.kind == "focus"
        assert style.representation is not None
    records = view.styles.builtin_focus_records()
    assert len(records) == 4
    assert all(r["source"] == "builtin" for r in records)
    assert all(r["style"]["kind"] == "focus" for r in records)


def test_styles_focus_builtin_tag_creates_region():
    view = demo["dialanine"]

    focus_tag = view.styles.focus("chain-id")

    assert focus_tag == "chain-id"
    assert focus_tag in view.regions
    assert focus_tag in view.styles.focus_tags()
    # region should have a representation message
    region_ops = [m["op"] for m in view._message_history if m.get("op") == "set_region_representation"]  # noqa: SLF001
    assert len(region_ops) >= 1


def test_styles_focus_builtin_with_custom_tag():
    view = demo["dialanine"]

    focus_tag = view.styles.focus("hydrophobicity", tag="pocket-surface")

    assert focus_tag == "pocket-surface"
    assert "pocket-surface" in view.regions
    assert "pocket-surface" in view.styles.focus_tags()


def test_styles_focus_inline_representation_creates_focus_region():
    view = demo["dialanine"]

    focus_tag = view.styles.focus(representation="spacefill", tag="vdw-view")

    assert focus_tag == "vdw-view"
    assert "vdw-view" in view.regions
    assert "vdw-view" in view.styles.focus_tags()


def test_styles_focus_explicit_style_object():
    view = demo["dialanine"]
    style = Style(representation="cartoon", kind="focus", params={"color_scheme": "chain_default"})

    focus_tag = view.styles.focus(style_or_tag=style, tag="chain-cartoon")

    assert focus_tag == "chain-cartoon"
    assert "chain-cartoon" in view.regions
    assert "chain-cartoon" in view.styles.focus_tags()


def test_styles_focus_rejects_scene_style_object():
    view = demo["dialanine"]
    scene_style = Style(preset="polymer-cartoon")
    try:
        view.styles.focus(style_or_tag=scene_style)
    except ValueError as exc:
        assert "kind='focus'" in str(exc)
    else:
        raise AssertionError("Expected ValueError when passing scene style to focus().")


def test_styles_focus_auto_generates_tag():
    view = demo["dialanine"]

    tag1 = view.styles.focus("chain-id")
    tag2 = view.styles.focus("element-cpk")

    # Both should be registered
    assert tag1 in view.styles.focus_tags()
    assert tag2 in view.styles.focus_tags()
    assert tag1 != tag2


def test_styles_clear_focus_removes_single_overlay():
    view = demo["dialanine"]
    view.styles.focus("chain-id", tag="my-chain")
    view.styles.focus("element-cpk", tag="my-cpk")

    view.styles.clear_focus("my-chain")

    assert "my-chain" not in view.styles.focus_tags()
    assert "my-chain" not in view.regions
    assert "my-cpk" in view.styles.focus_tags()
    assert "my-cpk" in view.regions


def test_styles_clear_focus_removes_all_overlays():
    view = demo["dialanine"]
    view.styles.focus("chain-id", tag="f1")
    view.styles.focus("element-cpk", tag="f2")

    view.styles.clear_focus()

    assert view.styles.focus_tags() == []
    assert "f1" not in view.regions
    assert "f2" not in view.regions


def test_styles_focus_does_not_modify_scene_style():
    view = demo["dialanine"]
    view.styles.apply(representation="cartoon")
    before = view.styles.current()

    view.styles.focus("chain-id", tag="chain-overlay")

    after = view.styles.current()
    assert before is not None
    assert after is not None
    assert after.representation == before.representation


def test_styles_focus_tags_initially_empty():
    view = MolSysView()
    assert view.styles.focus_tags() == []
