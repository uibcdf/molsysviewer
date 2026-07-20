from __future__ import annotations

import json
import warnings

import pyunitwizard as puw
import molsysviewer._pyunitwizard  # noqa: F401 — configures puw

from molsysviewer import AddonPanelSpec, AddonSpec, AddonWorkspaceSpec, FigureSpec, addons
from molsysviewer import config
from molsysviewer.config.user_presets import load_user_presets
from molsysviewer.demo import demo
from molsysviewer.styles import Style


def _missing_digester_warnings(records) -> list[str]:
    return [
        str(record.message)
        for record in records
        if record.message.__class__.__name__ == "DigestNotDigestedWarning"
    ]


def test_core_public_api_does_not_emit_missing_digester_warnings(tmp_path):
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    preset_path = tmp_path / "user-presets.json"
    preset_path.write_text(
        json.dumps({"demo-preset": {"base": "auto", "options": {}, "rules": []}}),
        encoding="utf-8",
    )
    project_config_path = tmp_path / "_molsysviewer.py"
    project_config_path.write_text(
        "\n".join(
            [
                "from molsysviewer import Style",
                "",
                'DEFAULT_SCENE_STYLE = Style(preset="polymer-cartoon", name="Default Polymer")',
                "STYLES = {",
                '    "publication": Style(preset="polymer-cartoon", name="Publication"),',
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", representation="sticks", skip_digestion=True)
    layer = view.layers.add("audit-layer", skip_digestion=True)

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        addons.clear()
        view._request_image_export = lambda **_kwargs: {  # type: ignore[attr-defined]  # noqa: SLF001
            "event": "image_export",
            "format": "png",
            "data_uri": "data:image/png;base64,iVBORw0KGgo=",
        }
        view.set_controls_visible(True, autohide=False, position=("top", "left"), position_fullscreen="bottom right")
        view.set_panel_mode("navigate")
        view.set_panel_mode("addons")
        view.set_panel_mode(None, expanded=False)
        view.set_workspace("core")
        view.set_workspace("audit")
        view.set_workspace_panel("summary", workspace="audit")
        view.set_workspace_panel("summary")
        view.workspace_catalog()
        view.workspace_panels()
        view.workspace_panels("audit")
        view.workspace_sections()
        view.workspace_sections("audit")
        view.workspace_runtime()
        view.workspace_runtime(pretty=True)
        view.get_panel_mode_state(pretty=True)
        view.clear_decorations(shapes=True, styles=False, labels=True)
        view.get_camera_snapshot(pretty=True)
        view.set_camera_snapshot({"target": [0, 0, 0], "position": [1, 1, 1], "up": [0, 1, 0]}, duration_ms=125)
        view.whole.set_representation(preset="polymer-cartoon")
        view.contains("all")
        view.is_composed_of("all")
        view.extract(selection=[0, 1], syntax="MolSysMT")
        view.whole.contains("all")
        view.whole.is_composed_of("all")
        view.styles.apply(style=Style(preset="polymer-cartoon", name="Polymers"))
        view.styles.add("publication", Style(preset="polymer-cartoon"), description="Publication baseline", source="runtime")
        view.styles.load_project_config(str(project_config_path), apply_default=False)
        addons.load_project_config(str(project_config_path))
        addons.clear()
        addons.register(
            AddonSpec(
                name="audit-addon",
                workspaces=(AddonWorkspaceSpec(id="audit", title="Audit", entry_panel="audit"),),
                panels=(AddonPanelSpec(id="audit", title="Audit", entry="audit.panel"),),
            )
        )
        addons.contains("audit-addon")
        addons.get("audit-addon")
        addons.names()
        addons.workspace_specs()
        view.addons.available()
        view.addons.enabled()
        view.addons.workspace_specs()
        view.addons.panel_specs()
        region.set_representation(preset="polymer-cartoon")
        region.contains("all")
        region.is_composed_of("all")
        layer.set_tag("audit-layer-2")
        view.export.html(
            tmp_path / "audit.html",
            title="Audit",
            include_controls=False,
            include_popout=False,
            inline_messages=True,
        )
        view.export.image(
            tmp_path / "audit.png",
            width_px=640,
            height_px=480,
            scale=2.0,
            transparent=True,
            preset="publication-light",
            camera_snapshot={"target": [0, 0, 0], "position": [1, 1, 1], "up": [0, 1, 0]},
        )
        view.export.figure(
            tmp_path / "audit-figure.png",
            figure_spec=FigureSpec(width_px=900, height_px=600, scale=2.5, background="white", preset="publication-light"),
            width_px=800,
            height_px=600,
            scale=2.0,
            background="white",
            preset="publication-light",
            camera_snapshot={"target": [0, 0, 0], "position": [1, 1, 1], "up": [0, 1, 0]},
        )
        config.set_default_standard_units("nm, ps, K, mole, amu, e, kJ/mol, kJ/(mol*nm), kJ/(mol*nm**2), radians")
        load_user_presets(preset_path)
        addons.clear()

    assert _missing_digester_warnings(records) == []


def test_color_operations_do_not_emit_missing_digester_warnings():
    # 181L is a crystal structure, so b_factor is present for the attribute path.
    view = demo["181L"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001

    n_atoms = int(view.molsys.get_n_atoms())
    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", skip_digestion=True)

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        # explicit range + inferred range, both replace flags, all four surfaces
        view.whole.set_color_by_attribute("b_factor", value_range=[0.0, 50.0], replace=True)
        view.whole.set_color_by_attribute("b_factor", value_range=None, replace=False)
        view.whole.set_color_by_values(
            [i / n_atoms for i in range(n_atoms)], value_range=[0.0, 1.0], replace=True
        )
        region.set_color_by_attribute("b_factor", value_range=[0.0, 50.0], replace=True)
        region.set_color_by_attribute("b_factor", value_range=None, replace=False)
        region.set_color_by_values([0.1, 0.5, 0.9], value_range=[0.0, 1.0], replace=False)
        # structural color scheme (the `scheme` argument)
        view.whole.set_representation("cartoon")
        view.whole.set_color_scheme("chain-id")
        region.set_representation("cartoon")
        region.set_color_scheme("residue-name")

    assert _missing_digester_warnings(records) == []


def test_shape_helpers_do_not_emit_missing_digester_warnings():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        view.shapes.add_sphere(
            center=puw.quantity([0.0, 0.0, 0.0], "nm"),
            radius=puw.quantity(1.5, "nm"),
            color=0x00FF00,
            alpha=0.3,
            tag="sphere-1",
        )
        view.shapes.add_sphere(
            center=puw.quantity([(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)], "nm"),
            radius=puw.quantity([1.0, 1.5], "nm"),
            color=[0x00FF00, 0x0000FF],
            alpha=[0.2, 0.4],
            tag=["s1", "s2"],
        )
        view.shapes.add_links(
            coordinate_pairs=puw.quantity([
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                [[1.0, 0.0, 0.0], [1.0, 1.0, 0.0]],
            ], "nm"),
            radii=puw.quantity([0.1, 0.2], "nm"),
            colors=[0xFF0000, 0x00FF00],
            color_mode="link",
            alpha=0.5,
            radial_segments=12,
            tag="links",
        )

    assert _missing_digester_warnings(records) == []
