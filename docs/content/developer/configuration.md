# Configuration (Python)

This page documents the current public configuration surface in
`molsysviewer.config.*` and the explicit project-level `_molsysviewer.py`
pattern.

## What belongs here

- Viewer defaults (controls visibility, autohide, control positions).
- Export defaults (docs-lite runtime URL selection, embed behavior).
- User presets loading (`load_user_presets`).
- Explicit project config loading for `_molsysviewer.py` (`load_project_config`).
- SMonitor configuration (`_smonitor.py`, catalog, metadata).

## Runtime Defaults In `molsysviewer.config`

Current built-in viewer defaults live in:

- `molsysviewer.config.show_controls`
- `molsysviewer.config.autohide_controls`
- `molsysviewer.config.controls_position`
- `molsysviewer.config.controls_position_fullscreen`

These are simple Python module-level defaults.

## User Presets

Representation presets can be loaded explicitly from JSON or YAML with:

```python
from molsysviewer.config import load_user_presets

load_user_presets("user-presets.json")
```

These presets participate in the current representation/style base and can be
used through:

- `view.whole.set_representation(preset="...")`
- `Style(user_preset="...")`

## Explicit Project Config With `_molsysviewer.py`

MolSysViewer now supports an explicit project-level configuration file pattern:

- `_molsysviewer.py`

This support is intentionally conservative:

- there is no ambient auto-discovery yet
- the file is only loaded when the user requests it explicitly
- explicit notebook/script calls still win over project defaults

## Recommended `_molsysviewer.py` Shape

The first supported contract is intentionally small:

```python
from molsysviewer import Style

DEFAULT_SCENE_STYLE = Style(
    preset="polymer-cartoon",
    name="default-polymer",
)

STYLES = {
    "publication": Style(
        preset="polymer-cartoon",
        name="publication",
    ),
    "atomic": Style(
        preset="atomic-detail",
        name="atomic",
    ),
}

ADDONS_ENABLED = [
    "topomt",
]

ADDONS_DISABLED = [
    "pharmacophoremt",
]
```

Supported names:

- `DEFAULT_SCENE_STYLE`
  - optional single `Style`
- `STYLES`
  - optional mapping `tag -> Style`
- `ADDONS_ENABLED`
  - optional iterable of add-on names enabled by default at host level
- `ADDONS_DISABLED`
  - optional iterable of add-on names disabled by default at host level

## Loading Project Config Explicitly

You can load the file directly:

```python
from molsysviewer.config import load_project_config

data = load_project_config("_molsysviewer.py")
```

That returns validated data without mutating a viewer instance.

## Applying Project Add-on Defaults

Project config can also define host-level add-on defaults:

```python
import molsysviewer

molsysviewer.addons.load_project_config("_molsysviewer.py")
```

This updates the host registry defaults for:

- add-ons enabled by default
- add-ons disabled by default

New views inherit those defaults automatically.
Existing views still keep their local `view.addons` overrides.

## Applying Project Config To A Viewer

The higher-level entrypoint is:

```python
from molsysviewer import demo

view = demo["dialanine"]
view.styles.load_project_config("_molsysviewer.py", apply_default=False)
```

This registers `STYLES` on `view.styles` without changing the current scene.

If you want the default scene style to be applied too:

```python
view.styles.load_project_config("_molsysviewer.py", apply_default=True)
```

That explicit flag is important.

The design rule is:

- loading config should not silently mutate the scene unless the caller asks for it

## Style API Examples

Programmatic use remains the primary source of truth.

### Apply a built-in canonical scene recipe

```python
view.styles.apply(tag="polymer-and-ligand")
```

### Register and apply a custom style

```python
from molsysviewer import Style

view.styles.add(
    "inspection",
    Style(preset="atomic-detail", name="Inspection"),
    description="Local atomistic inspection baseline",
)

view.styles.apply(tag="inspection")
```

### Apply a style object directly

```python
from molsysviewer import Style

view.styles.apply(
    style=Style(
        preset="coarse-surface",
        name="Large System Overview",
    )
)
```

## Built-In Canonical Scene Recipes

MolSysViewer now exposes a small curated built-in style battery through
`view.styles`.

Current canonical built-ins are:

- `default`
- `polymer-cartoon`
- `polymer-and-ligand`
- `atomic-detail`
- `coarse-surface`
- `empty`

You can inspect them with:

```python
view.styles.builtin_tags()
view.styles.builtin_records()
```

## Configuration Rule

Keep this rule in mind:

- Python defines
- project config registers
- canvas applies or previews later

That ordering is deliberate and preserves reproducibility.

## Cross-links

- User-facing configuration: see the User Guide configuration page.
- Developer-facing stability rules: see {doc}`public_api`.
- SMonitor details: see {doc}`smonitor`.
