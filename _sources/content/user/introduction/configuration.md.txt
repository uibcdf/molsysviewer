(User_Intro_Customization)=
# Customization

MolSysViewer exposes a small set of user-facing configuration options so you can tailor your default experience without
changing any source code.

This page focuses on the `molsysviewer.config` module: what you can customize, and when it is useful.

## A quick mental model

- `molsysviewer.config` controls **defaults** (what happens when you create a new `MolSysView`).
- Many options can also be changed **per viewer instance** (for example, you can show/hide the on-canvas UI for a single
  viewer without changing your global defaults).

There are now three distinct customization layers worth keeping separate:

- `molsysviewer.config.*` for module-level defaults
- `view.styles` for scene baselines on a concrete viewer
- `_molsysviewer.py` for explicit project-level style catalogs

In a notebook, it is common to set configuration once near the top of the notebook and then create one or more views.

## On-canvas controls

MolSysViewer can show a small set of on-canvas controls (reset, fullscreen, background toggle, spin/swing, and the
trajectory bar when available).

Defaults live here:

- `molsysviewer.config.show_controls`
- `molsysviewer.config.autohide_controls`
- `molsysviewer.config.controls_position`
- `molsysviewer.config.controls_position_fullscreen`

For per-view changes, see {doc}`../viewer/ui`.

## Quantities with units

MolSysViewer uses PyUnitWizard to accept unit-aware inputs and to standardize outputs.
The Units page explains the basics: {doc}`units`.

If you want to change what you get back by default (output form and standard units), configure it via:

- `molsysviewer.config.set_default_quantities_form(...)`
- `molsysviewer.config.set_default_quantities_parser(...)`
- `molsysviewer.config.set_default_standard_units(...)`

Example:

```python
import molsysviewer as msv

msv.config.set_default_quantities_form("pint")
msv.config.set_default_quantities_parser("pint")
msv.config.set_default_standard_units(
    ["nm", "ps", "K", "mole", "amu", "e", "kJ/mol", "kJ/(mol*nm)", "kJ/(mol*nm**2)", "radians"]
)
```

## User presets

User presets let you define reusable “style recipes” for `whole` and `regions`.

The quick workflow is:

1. Define presets in a JSON/YAML file.
2. Load them once with `molsysviewer.config.load_user_presets(...)`.
3. Apply them with `preset="..."` in `whole` or `regions`.

See {doc}`../representations/user_presets`.

## Scene styles

Scene styles are a higher-level vocabulary for reusable viewer baselines.

Use them when you want to say "start from this known scene recipe" instead of
setting low-level representations directly each time.

Examples:

```python
from molsysviewer import Style

view.styles.apply(tag="polymer-cartoon")
view.styles.add("inspection", Style(preset="atomic-detail"))
```

See {doc}`../representations/styles`.

## Project configuration with `_molsysviewer.py`

If you are embedding MolSysViewer in a larger codebase, you can also keep a
project-level `_molsysviewer.py` file with:

- `DEFAULT_SCENE_STYLE`
- `STYLES`

This support is explicit-load only for now.

That means MolSysViewer will not auto-discover the file silently.

See {doc}`project_configuration`.
