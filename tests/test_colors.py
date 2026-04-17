import pytest

from molsysviewer import MolSysView, colors, normalize_color, normalize_colors


def test_normalize_color_accepts_molstar_names_and_aliases():
    assert normalize_color("red") == 0xFF0000
    assert normalize_color("light_blue") == 0xADD8E6
    assert normalize_color("light-blue") == 0xADD8E6
    assert normalize_color("Light Blue") == 0xADD8E6


def test_normalize_color_accepts_hex_and_rgb_forms():
    assert normalize_color("#0f0") == 0x00FF00
    assert normalize_color("#112233") == 0x112233
    assert normalize_color((17, 34, 51)) == 0x112233
    assert normalize_color((1.0, 0.0, 0.0)) == 0xFF0000


def test_normalize_colors_normalizes_lists():
    assert normalize_colors(["red", "#00ff00", (0, 0, 255)]) == [
        0xFF0000,
        0x00FF00,
        0x0000FF,
    ]


def test_view_exposes_shared_color_registry():
    view = MolSysView()

    assert view.colors is colors
    assert "red" in view.colors.color_names()


def test_color_registry_supports_custom_categorical_scheme():
    scheme = colors.register_scheme(
        "test-elements",
        {"C": "#444444", "O": "red", "N": "blue"},
        overwrite=True,
    )

    assert colors.get_scheme("test-elements") == scheme
    assert scheme.mapping == {"C": 0x444444, "O": 0xFF0000, "N": 0x0000FF}


def test_color_registry_supports_categories_from_palette():
    scheme = colors.resolve_scheme(
        ["red", "green", "blue"],
        categories=["A", "B", "C"],
        fallback="white",
    )

    assert scheme.mapping == {"A": 0xFF0000, "B": 0x008000, "C": 0x0000FF}
    assert scheme.fallback == 0xFFFFFF


def test_color_registry_supports_matplotlib_colormaps():
    pytest.importorskip("matplotlib")

    palette = colors.resolve_palette("mpl:viridis", samples=5)

    assert palette.source == "matplotlib"
    assert len(palette.colors) == 5
    assert all(isinstance(color, int) for color in palette.colors)


def test_builtin_static_schemes_are_available():
    assert "element_cpk" in colors.scheme_names()
    assert "secondary_structure_default" in colors.scheme_names()

    element = colors.get_scheme("element_cpk")
    secondary = colors.get_scheme("secondary_structure_default")

    assert element.mapping["C"] == 0x808080
    assert element.mapping["O"] == 0xFF0000
    assert secondary.mapping["H"] == 0xFF0000
    assert secondary.mapping["E"] == 0x1E90FF


def test_builtin_generated_schemes_can_be_resolved_from_categories():
    assert "chain_default" in colors.scheme_names()
    assert "pocket_default" in colors.scheme_names()

    chain_scheme = colors.resolve_scheme("chain_default", categories=["A", "B", "C"])

    assert chain_scheme.mapping == {
        "A": 0x0000FF,
        "B": 0xFFA500,
        "C": 0x008000,
    }
    assert chain_scheme.fallback == 0xD3D3D3


def test_builtin_palette_names_are_registered_when_available():
    if "viridis" not in colors.palette_names():
        pytest.importorskip("matplotlib")

    assert "viridis" in colors.palette_names()
    assert "turbo" in colors.palette_names()
    assert "categorical_default" in colors.palette_names()
