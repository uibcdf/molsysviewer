import pytest
import pyunitwizard as puw
import molsysviewer._pyunitwizard  # noqa: F401 — configures puw

from molsysviewer import MolSysView
from molsysviewer.layers import Shape, _bounding_sphere_nm
from molsysviewer.shapes import ShapesManager, SphereShapes


class DummyView:
    def __init__(self) -> None:
        self.messages = []
        self._layers = {}
        self._layer_counter = 0

    def _send(self, message):
        self.messages.append(message)

    def _next_layer_tag(self):
        self._layer_counter += 1
        return f"shape-{self._layer_counter}"

    def _next_shape_tag(self):
        self._layer_counter += 1
        return f"shape-{self._layer_counter}"



def test_bounding_sphere_empty_points_returns_scene_fallback():
    center, radius = _bounding_sphere_nm([])

    assert center == [0.0, 0.0, 0.0]
    assert radius == 4.0


def test_empty_shape_focus_warns_and_zooms_scene_center():
    view = MolSysView()
    shape = Shape(view, "empty")
    view._scene_objects["empty"] = shape  # noqa: SLF001
    view._shape_history.append(  # noqa: SLF001
        {
            "op": "add_channel_tube",
            "options": {"tag": "empty", "layer_tag": "empty", "centers": []},
        }
    )

    with pytest.warns(UserWarning, match="empty shape .empty."):
        shape.focus(duration_ms=0, extra_radius=0.5)

    assert view._message_history[-1] == {  # noqa: SLF001
        "op": "zoom_to_position",
        "center": [0.0, 0.0, 0.0],
        "radius": 45.0,
        "duration_ms": 0,
    }


def test_shapes_exports_and_delegation(monkeypatch):
    view = DummyView()
    manager = ShapesManager(view)

    called = {}

    def fake_add_sphere(*args, **kwargs):
        called["args"] = args
        called["kwargs"] = kwargs

    monkeypatch.setattr(manager.spheres, "add_sphere", fake_add_sphere)

    manager.add_sphere(center=(1, 2, 3), radius=5)
    assert called["args"][0] == (1, 2, 3)
    assert called["args"][1] == 5


def test_add_sphere_sends_message():
    view = DummyView()
    shapes = SphereShapes(view)
    layer = shapes.add_sphere(
        center=puw.quantity([1, 2, 3], "nm"),
        radius=puw.quantity(2.5, "nm"),
        color=0x123456,
        alpha=0.7,
        tag="foo",
    )

    assert layer.tag == "foo"
    assert layer.kind == "shape"
    assert view.messages == [
        {
            "op": "add_sphere",
            "options": {
                "center": [10.0, 20.0, 30.0],  # 1 nm = 10 Å (wire format is Å for Mol*)
                "radius": 25.0,                  # 2.5 nm = 25 Å
                "color": 0x123456,
                "alpha": 0.7,
                "tag": "foo",
                "layer_tag": "foo",
            },
        }
    ]


def test_shapes_manager_supports_subscript_and_duplicate_tag_guard():
    view = DummyView()
    manager = ShapesManager(view)

    layer = manager.add_sphere(
        center=puw.quantity([1, 2, 3], "nm"),
        radius=puw.quantity(5, "nm"),
        tag="foo",
    )

    assert manager.contains("foo") is True
    assert manager.get("foo") is layer
    assert manager["foo"] is layer
    assert manager.tags() == ["foo"]
    assert view._layers["foo"].shapes == {"foo": layer}
    assert view._layers["foo"].members == {"foo": layer}

    with pytest.raises(ValueError, match="already exists"):
        manager.add_sphere(
            center=puw.quantity([0, 0, 0], "nm"),
            radius=puw.quantity(1, "nm"),
            tag="foo",
        )

    with pytest.raises(KeyError):
        _ = manager["missing"]


def test_shapes_manager_supports_explicit_shared_layer_tag():
    view = DummyView()
    manager = ShapesManager(view)

    first = manager.add_sphere(
        center=puw.quantity([1, 2, 3], "nm"),
        radius=puw.quantity(5, "nm"),
        tag="foo",
        layer_tag="cluster",
    )
    second = manager.add_sphere(
        center=puw.quantity([4, 5, 6], "nm"),
        radius=puw.quantity(2, "nm"),
        tag="bar",
        layer_tag="cluster",
    )

    assert first.layer_tag == "cluster"
    assert second.layer_tag == "cluster"
    assert set(view._layers["cluster"].shapes.keys()) == {"foo", "bar"}
    assert set(view._layers["cluster"].members.keys()) == {"foo", "bar"}


def test_shared_shape_layer_retag_rewrites_history_and_live_members():
    view = MolSysView()
    first = view.shapes.add_sphere(
        center=puw.quantity([1, 2, 3], "nm"),
        radius=puw.quantity(5, "nm"),
        tag="foo",
        layer_tag="cluster",
    )
    second = view.shapes.add_sphere(
        center=puw.quantity([4, 5, 6], "nm"),
        radius=puw.quantity(2, "nm"),
        tag="bar",
        layer_tag="cluster",
    )

    view.layers["cluster"].set_tag("active_site")

    assert first.layer_tag == "active_site"
    assert second.layer_tag == "active_site"
    assert "cluster" not in view.layers
    assert set(view.layers["active_site"].shapes.keys()) == {"foo", "bar"}

    shape_layer_tags = [
        msg["options"].get("layer_tag")
        for msg in view._shape_history  # noqa: SLF001
        if msg.get("op") == "add_sphere"
    ]
    assert shape_layer_tags == ["active_site", "active_site"]

    replay_layer_tags = [
        msg["options"].get("layer_tag")
        for msg in view._message_history  # noqa: SLF001
        if msg.get("op") == "add_sphere"
    ]
    assert replay_layer_tags == ["active_site", "active_site"]


def test_shapes_manager_can_move_shape_between_layers():
    view = MolSysView()
    layer = view.shapes.add_sphere(
        center=puw.quantity([1, 2, 3], "nm"),
        radius=puw.quantity(5, "nm"),
        tag="foo",
    )

    moved = view.shapes.set_layer_tag("foo", "cluster")

    assert moved is layer
    assert view.shapes["foo"].layer_tag == "cluster"
    assert "foo" not in view.layers
    assert "cluster" in view.layers
    assert view.layers["cluster"].shapes == {"foo": layer}
    exported = [msg for msg in view._build_export_messages() if msg.get("options", {}).get("tag") == "foo"]  # noqa: SLF001
    assert exported[0]["options"]["layer_tag"] == "cluster"


def test_sphere_shape_supports_rich_mutators_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_sphere(
        center=puw.quantity([1, 2, 3], "nm"),
        radius=puw.quantity(5, "nm"),
        color=0x123456,
        alpha=0.4,
        tag="foo",
        layer_tag="cluster",
    )

    assert puw.get_value(layer.get_center(), to_unit="angstroms").tolist() == [10.0, 20.0, 30.0]

    layer.set_color(0xabcdef)
    layer.set_alpha(0.8)
    layer.set_center(puw.quantity([4, 5, 6], "nm"))
    layer.set_radius(puw.quantity(7, "nm"))

    assert view._shape_history[0]["options"]["color"] == 0xABCDEF  # noqa: SLF001
    assert view._shape_history[0]["options"]["alpha"] == 0.8  # noqa: SLF001
    assert view._shape_history[0]["options"]["center"] == [40.0, 50.0, 60.0]  # 4 nm = 40 Å  # noqa: SLF001
    assert view._shape_history[0]["options"]["radius"] == 70.0  # 7 nm = 70 Å  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "cluster"  # noqa: SLF001
    assert puw.get_value(layer.get_center(), to_unit="angstroms").tolist() == [40.0, 50.0, 60.0]  # 4 nm = 40 Å

    exported = [msg for msg in view._build_export_messages() if msg.get("options", {}).get("tag") == "foo"]  # noqa: SLF001
    assert exported[0]["options"]["color"] == 0xABCDEF
    assert exported[0]["options"]["alpha"] == 0.8
    assert exported[0]["options"]["center"] == [40.0, 50.0, 60.0]  # 4 nm = 40 Å
    assert exported[0]["options"]["radius"] == 70.0  # 7 nm = 70 Å
    assert exported[0]["options"]["layer_tag"] == "cluster"


def test_link_shape_supports_rich_mutators_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_links(
        coordinate_pairs=puw.quantity(
            [
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                [[0.0, 1.0, 0.0], [1.0, 1.0, 0.0]],
            ],
            "nm",
        ),
        radii=puw.quantity([0.1, 0.2], "nm"),
        colors=[0x111111, 0x222222],
        alpha=0.5,
        tag="links_1",
        layer_tag="cluster",
    )

    layer.set_alpha(0.8)
    layer.set_colors([0x333333, 0x444444])
    layer.set_radii(puw.quantity([0.3, 0.4], "nm"))

    assert view._shape_history[0]["options"]["alpha"] == 0.8  # noqa: SLF001
    assert view._shape_history[0]["options"]["colors"] == [0x333333, 0x444444]  # noqa: SLF001
    assert view._shape_history[0]["options"]["radii"] == [3.0, 4.0]  # 0.3 nm = 3 Å  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "cluster"  # noqa: SLF001

    exported = [msg for msg in view._build_export_messages() if msg.get("options", {}).get("tag") == "links_1"]  # noqa: SLF001
    assert exported[0]["options"]["alpha"] == 0.8
    assert exported[0]["options"]["colors"] == [0x333333, 0x444444]
    assert exported[0]["options"]["radii"] == [3.0, 4.0]  # 0.3 nm = 3 Å
    assert exported[0]["options"]["layer_tag"] == "cluster"


def test_link_shape_accepts_color_by_and_color_table():
    view = MolSysView()
    view.shapes.add_links(
        coordinate_pairs=puw.quantity(
            [
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                [[0.0, 1.0, 0.0], [1.0, 1.0, 0.0]],
            ],
            "nm",
        ),
        pocket_ids=["A", "B"],
        color_by="pocket",
        color_table={"A": "white", "B": "#112233"},
        tag="links_color",
        layer_tag="cluster",
    )

    options = view._shape_history[0]["options"]  # noqa: SLF001
    assert options["color_by"] == "pocket"
    assert options["color_mode"] == "pocket"
    assert options["color_table"] == {"A": 0xFFFFFF, "B": 0x112233}


def test_link_shape_accepts_generated_chain_color_scheme():
    view = MolSysView()
    view.shapes.add_links(
        coordinate_pairs=puw.quantity(
            [
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                [[0.0, 1.0, 0.0], [1.0, 1.0, 0.0]],
            ],
            "nm",
        ),
        chain_ids=["A", "B"],
        color_by="chain",
        color_scheme="chain_default",
        tag="links_chain_scheme",
        layer_tag="cluster",
    )

    options = view._shape_history[0]["options"]  # noqa: SLF001
    assert options["color_by"] == "chain"
    assert options["color_mode"] == "chain"
    assert options["color_scheme"] == "chain_default"
    assert options["color_table"] == {"A": 0x0000FF, "B": 0xFFA500}


def test_triangle_face_shape_supports_rich_mutators_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_triangle_faces(
        vertices=puw.quantity(
            [
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                [[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
            ],
            "nm",
        ),
        colors=[0xAAAAAA, 0xBBBBBB],
        alpha=0.4,
        tag="triangles_1",
        layer_tag="surfaces",
    )

    layer.set_alpha(0.9)
    layer.set_colors([0xCCCCCC, 0xDDDDDD])

    assert view._shape_history[0]["options"]["alpha"] == 0.9  # noqa: SLF001
    assert view._shape_history[0]["options"]["colors"] == [0xCCCCCC, 0xDDDDDD]  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "surfaces"  # noqa: SLF001

    exported = [msg for msg in view._build_export_messages() if msg.get("options", {}).get("tag") == "triangles_1"]  # noqa: SLF001
    assert exported[0]["options"]["alpha"] == 0.9
    assert exported[0]["options"]["colors"] == [0xCCCCCC, 0xDDDDDD]
    assert exported[0]["options"]["layer_tag"] == "surfaces"



def test_triangle_face_shape_preserves_entity_refs_in_payload():
    view = MolSysView()
    entity_refs = [
        {"kind": "topomt.face", "id": "f-1", "atoms": [0, 1, 2]},
        {"kind": "topomt.face", "id": "f-2", "atoms": [3, 4, 5]},
    ]

    view.shapes.add_triangle_faces(
        vertices=puw.quantity(
            [
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                [[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
            ],
            "nm",
        ),
        entity_refs=entity_refs,
        tag="triangles_refs",
    )

    assert view._shape_history[0]["options"]["entity_refs"] == entity_refs  # noqa: SLF001

    with pytest.raises(ValueError, match="Expected 2 entity_refs"):
        view.shapes.add_triangle_faces(
            vertices=puw.quantity(
                [
                    [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                    [[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]],
                ],
                "nm",
            ),
            entity_refs=[{"kind": "topomt.face", "id": "f-1"}],
        )


def test_channel_tube_shape_supports_rich_mutators_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_channel_tube(
        centers=puw.quantity(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [2.0, 1.0, 0.0],
            ],
            "nm",
        ),
        radii=puw.quantity([0.2, 0.3, 0.4], "nm"),
        colors=[0x111111, 0x222222, 0x333333],
        alpha=0.4,
        tag="tube_1",
        layer_tag="channels",
    )

    layer.set_alpha(0.75)
    layer.set_colors([0x444444, 0x555555, 0x666666])
    layer.set_radii(puw.quantity([0.5, 0.6, 0.7], "nm"))

    assert view._shape_history[0]["options"]["alpha"] == 0.75  # noqa: SLF001
    assert view._shape_history[0]["options"]["colors"] == [0x444444, 0x555555, 0x666666]  # noqa: SLF001
    assert view._shape_history[0]["options"]["color_mode"] == "segment"  # noqa: SLF001
    assert view._shape_history[0]["options"]["radii"] == [5.0, 6.0, 7.0]  # 0.5 nm = 5 Å  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "channels"  # noqa: SLF001

    exported = [msg for msg in view._build_export_messages() if msg.get("options", {}).get("tag") == "tube_1"]  # noqa: SLF001
    assert exported[0]["options"]["alpha"] == 0.75
    assert exported[0]["options"]["colors"] == [0x444444, 0x555555, 0x666666]
    assert exported[0]["options"]["color_mode"] == "segment"
    assert exported[0]["options"]["radii"] == [5.0, 6.0, 7.0]  # 0.5 nm = 5 Å
    assert exported[0]["options"]["layer_tag"] == "channels"


def test_channel_tube_shape_accepts_color_by_and_palette():
    view = MolSysView()
    view.shapes.add_channel_tube(
        centers=puw.quantity(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [2.0, 1.0, 0.0],
            ],
            "nm",
        ),
        radii=puw.quantity([0.2, 0.3, 0.4], "nm"),
        solvent_distances=[0.1, 0.2, 0.3],
        color_by="solvent",
        palette=["red", "#00ff00", (0, 0, 255)],
        tag="tube_color",
        layer_tag="channels",
    )

    options = view._shape_history[0]["options"]  # noqa: SLF001
    assert options["color_by"] == "solvent"
    assert options["color_mode"] == "solvent"
    assert options["palette"] == [0xFF0000, 0x00FF00, 0x0000FF]
    assert options["color_map"] == [0xFF0000, 0x00FF00, 0x0000FF]


def test_tetrahedra_shape_supports_rich_mutators_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_tetrahedra(
        tetra_coords=puw.quantity(
            [
                [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
                [
                    [1.0, 1.0, 1.0],
                    [2.0, 1.0, 1.0],
                    [1.0, 2.0, 1.0],
                    [1.0, 1.0, 2.0],
                ],
            ],
            "nm",
        ),
        colors=[0xAAAAAA, 0xBBBBBB],
        alphas=[0.3, 0.4],
        tag="tetra_1",
        layer_tag="polyhedra",
    )

    layer.set_alpha(0.9)
    layer.set_colors([0xCCCCCC, 0xDDDDDD])

    assert view._shape_history[0]["options"]["alphas"] == 0.9  # noqa: SLF001
    assert view._shape_history[0]["options"]["colors"] == [0xCCCCCC, 0xDDDDDD]  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "polyhedra"  # noqa: SLF001

    exported = [msg for msg in view._build_export_messages() if msg.get("options", {}).get("tag") == "tetra_1"]  # noqa: SLF001
    assert exported[0]["options"]["alphas"] == 0.9
    assert exported[0]["options"]["colors"] == [0xCCCCCC, 0xDDDDDD]
    assert exported[0]["options"]["layer_tag"] == "polyhedra"



def test_tetrahedra_shape_preserves_entity_refs_and_face_edge_refs_in_payload():
    view = MolSysView()
    entity_refs = [{"kind": "topomt.tetra", "id": 1}]
    face_meta = [{"atoms": [0, 1, 2], "face_id": "f-1", "entity_ref": {"kind": "topomt.face", "id": "f-1"}}]
    edge_meta = [{"atoms": [0, 1], "edge_id": "e-1", "entity_ref": {"kind": "topomt.edge", "id": "e-1"}}]

    view.shapes.add_tetrahedra(
        tetra_coords=puw.quantity(
            [
                [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
            ],
            "nm",
        ),
        entity_refs=entity_refs,
        face_meta=face_meta,
        edge_meta=edge_meta,
        tag="tetra_refs",
    )

    options = view._shape_history[0]["options"]  # noqa: SLF001
    assert options["entity_refs"] == entity_refs
    assert options["face_meta"] == face_meta
    assert options["edge_meta"] == edge_meta

    with pytest.raises(ValueError, match="Expected 1 entity_refs"):
        view.shapes.add_tetrahedra(
            tetra_coords=puw.quantity(
                [
                    [
                        [0.0, 0.0, 0.0],
                        [1.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                        [0.0, 0.0, 1.0],
                    ],
                ],
                "nm",
            ),
            entity_refs=[],
        )


def test_anisotropy_shape_supports_rich_mutators_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_anisotropy_ellipsoids(
        centers=puw.quantity([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], "nm"),
        principal_directions=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        colors=[0x111111, 0x222222],
        alpha=0.4,
        tag="ell_1",
        layer_tag="analysis",
    )

    layer.set_alpha(0.7)
    layer.set_colors([0x333333, 0x444444])

    assert view._shape_history[0]["options"]["alpha"] == 0.7  # noqa: SLF001
    assert view._shape_history[0]["options"]["colors"] == [0x333333, 0x444444]  # noqa: SLF001
    assert view._shape_history[0]["options"]["color_mode"] == "fixed"  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "analysis"  # noqa: SLF001


def test_anisotropy_shape_accepts_color_by_and_palette():
    view = MolSysView()
    view.shapes.add_anisotropy_ellipsoids(
        centers=puw.quantity([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], "nm"),
        principal_directions=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        color_by="anisotropy",
        palette=["red", "#00ff00", (0, 0, 255)],
        tag="ell_color",
        layer_tag="analysis",
    )

    options = view._shape_history[0]["options"]  # noqa: SLF001
    assert options["color_by"] == "anisotropy"
    assert options["color_mode"] == "anisotropy"
    assert options["palette"] == [0xFF0000, 0x00FF00, 0x0000FF]
    assert options["color_map"] == [0xFF0000, 0x00FF00, 0x0000FF]


def test_pharmacophore_shape_supports_rich_mutators_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_interaction_sites(
        centers=puw.quantity([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], "nm"),
        kinds=["donor", "acceptor"],
        radii=puw.quantity([0.4, 0.5], "nm"),
        alphas=[0.3, 0.4],
        tag="ph4_1",
        layer_tag="sites",
    )

    layer.set_alpha(0.8)
    layer.set_colors([0xAAAAAA, 0xBBBBBB])
    layer.set_radii(puw.quantity([0.6, 0.7], "nm"))

    assert view._shape_history[0]["options"]["alphas"] == [0.8, 0.8]  # noqa: SLF001
    assert view._shape_history[0]["options"]["colors"] == [0xAAAAAA, 0xBBBBBB]  # noqa: SLF001
    assert view._shape_history[0]["options"]["radii"] == [6.0, 7.0]  # 0.6 nm = 6 Å  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "sites"  # noqa: SLF001


def test_displacement_shape_supports_scale_mutators_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_displacement_vectors(
        origins=puw.quantity([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], "nm"),
        vectors=puw.quantity([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], "nm"),
        length_scale=1.0,
        radius_scale=0.05,
        tag="disp_1",
        layer_tag="vectors",
    )

    layer.set_length_scale(1.5)
    layer.set_radius_scale(0.08)

    assert view._shape_history[0]["options"]["length_scale"] == 1.5  # noqa: SLF001
    assert view._shape_history[0]["options"]["radius_scale"] == 0.08  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "vectors"  # noqa: SLF001


def test_displacement_shape_accepts_color_by_and_palette():
    view = MolSysView()
    view.shapes.add_displacement_vectors(
        origins=puw.quantity([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], "nm"),
        vectors=puw.quantity([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], "nm"),
        color_by="component",
        color_component=1,
        palette=["red", "#00ff00", (0, 0, 255)],
        tag="disp_color",
        layer_tag="vectors",
    )

    options = view._shape_history[0]["options"]  # noqa: SLF001
    assert options["color_by"] == "component"
    assert options["color_mode"] == "component"
    assert options["palette"] == [0xFF0000, 0x00FF00, 0x0000FF]
    assert options["color_map"] == [0xFF0000, 0x00FF00, 0x0000FF]


def test_pharmacophore_shape_accepts_color_scheme_and_color_table():
    view = MolSysView()
    view.shapes.add_interaction_sites(
        centers=puw.quantity([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], "nm"),
        kinds=["donor", "acceptor"],
        color_scheme="pharmacophore_default",
        color_table={"donor": "white", "acceptor": "#112233"},
        tag="ph4_colors",
        layer_tag="sites",
    )

    options = view._shape_history[0]["options"]  # noqa: SLF001
    assert options["color_scheme"] == "pharmacophore_default"
    assert options["color_table"] == {"donor": 0xFFFFFF, "acceptor": 0x112233}
    assert options["colors"] == [0xFFFFFF, 0x112233]


def test_pocket_blob_shape_supports_mutators_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_pocket_blob(
        centers=puw.quantity([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], "nm"),
        radii=puw.quantity([0.4, 0.5], "nm"),
        alpha=0.3,
        radius_scale=1.0,
        tag="blob_1",
        layer_tag="pockets",
    )

    layer.set_alpha(0.6)
    layer.set_radii(puw.quantity([0.7, 0.8], "nm"))
    layer.set_radius_scale(1.2)

    assert view._shape_history[0]["options"]["alpha"] == 0.6  # noqa: SLF001
    assert view._shape_history[0]["options"]["radii"] == [7.0, 8.0]  # 0.7 nm = 7 Å  # noqa: SLF001
    assert view._shape_history[0]["options"]["radius_scale"] == 1.2  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "pockets"  # noqa: SLF001


def test_pocket_surface_shape_supports_alpha_mutator_and_replay_state():
    view = MolSysView()
    layer = view.shapes.add_pocket_surface(
        atom_indices=[0, 1, 2],
        alpha=0.3,
        tag="surface_1",
        layer_tag="pockets",
    )

    layer.set_alpha(0.65)

    assert view._shape_history[0]["options"]["alpha"] == 0.65  # noqa: SLF001
    assert view._shape_history[0]["options"]["layer_tag"] == "pockets"  # noqa: SLF001


def test_add_sphere_batch_broadcasts_and_validates():
    view = DummyView()
    shapes = SphereShapes(view)

    centers = puw.quantity([(0, 0, 0), (1, 1, 1)], "nm")
    shapes.add_sphere(centers, radius=puw.quantity([1.0, 2.0], "nm"), color=0x00FF00, alpha=[0.1, 0.2], skip_digestion=True)

    assert len(view.messages) == 2
    assert view.messages[0]["options"]["radius"] == 10.0  # 1 nm = 10 Å
    assert view.messages[1]["options"]["radius"] == 20.0  # 2 nm = 20 Å

    with pytest.raises(ValueError):
        shapes.add_sphere(centers, radius=puw.quantity([1.0, 1.5, 2.0], "nm"), color=0x00FF00, alpha=0.5, skip_digestion=True)


def test_add_sphere_selection_and_indices():
    from molsysviewer.demo import demo
    view = demo["dialanine"]

    # 1. Test selection (should be static since it's atom_index == 0)
    view.shapes.add_sphere(selection="atom_index == 0", tag="s_static")
    msg = [m for m in view._shape_history if m.get("op") == "add_sphere" and m["options"]["tag"] == "s_static"][0]
    assert msg["options"]["atom_indices"] == [0]
    assert "structures_atom_indices" not in msg["options"]

    # 2. Test explicit atom_indices
    view.shapes.add_sphere(atom_indices=[10, 11], tag="s_indices")
    msg2 = [m for m in view._shape_history if m.get("op") == "add_sphere" and m["options"]["tag"] == "s_indices"][0]
    assert msg2["options"]["atom_indices"] == [10, 11]

    # 3. Test explicit structures_atom_indices
    view.shapes.add_sphere(structures_atom_indices=[[0, 1], [2, 3]], tag="s_struct_indices")
    msg3 = [m for m in view._shape_history if m.get("op") == "add_sphere" and m["options"]["tag"] == "s_struct_indices"][0]
    assert msg3["options"]["structures_atom_indices"] == [[0, 1], [2, 3]]
