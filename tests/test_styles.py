from molsysviewer import MolSysView, Style, demo
from molsysviewer.config.user_presets import user_presets


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
        "coarse-surface",
        "default",
        "empty",
        "polymer-and-ligand",
        "polymer-cartoon",
    ]
    builtin = view.styles.get_builtin("polymer-and-ligand")
    assert builtin is not None
    assert builtin.preset == "polymer-and-ligand"
    records = view.styles.builtin_records()
    assert any(record["tag"] == "polymer-cartoon" for record in records)


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
