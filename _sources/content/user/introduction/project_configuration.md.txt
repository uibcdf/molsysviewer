(User_Intro_Project_Config)=
# Project Configuration

Use project configuration when you embed MolSysViewer in a larger codebase and
want reusable viewer defaults without repeating them in every notebook or
script.

## What this is for

MolSysViewer supports an explicit project-level configuration file pattern:

- `_molsysviewer.py`

This is useful when you want to define:

- a default scene style for your project
- a small catalog of reusable named styles

This is especially helpful if you are building a library or application that
creates MolSysViewer instances for other users.

## Recommended use

Reach for `_molsysviewer.py` when:

- the same scene baselines appear in several notebooks or scripts
- you are embedding MolSysViewer inside another Python package
- you want a shared project vocabulary such as `publication` or `inspection`

Do not start here by default. For one notebook or one script,
`view.styles.add(...)` is usually simpler.

## Important rule

Project configuration is explicit-load only for now.

That means:

- MolSysViewer does **not** auto-discover `_molsysviewer.py`
- you load it when you want it
- explicit calls in your notebook or script still win

This avoids hidden scene changes.

## Recommended file location

Keep `_molsysviewer.py` in the root of the codebase that owns the viewer
integration, next to the package or notebooks that will load it explicitly.

MolSysViewer does not currently search parent directories or import this file
automatically.

## Supported shape of `_molsysviewer.py`

Current supported top-level names:

| Name | Type | Description |
|---|---|---|
| `DEFAULT_SCENE_STYLE` | `Style` | Scene style applied when `apply_default=True` |
| `STYLES` | `dict[str, Style]` | Named styles available as `view.styles.apply(tag=...)` |
| `ADDONS_ENABLED` | `list[str]` | Add-on names enabled by default when the config is loaded |
| `ADDONS_DISABLED` | `list[str]` | Add-on names disabled by default when the config is loaded |

Example:

```python
from molsysviewer import Style

DEFAULT_SCENE_STYLE = Style(
    preset="polymer-cartoon",
    name="Default Polymer",
)

STYLES = {
    "publication": Style(
        preset="polymer-and-ligand",
        name="Publication",
    ),
    "inspection": Style(
        preset="atomic-detail",
        name="Inspection",
    ),
}

ADDONS_ENABLED = ["topomt"]
ADDONS_DISABLED = ["elastnetmt"]
```

## Load the file directly

If you only want to validate and inspect the file:

```python
from molsysviewer.config import load_project_config

data = load_project_config("_molsysviewer.py")
```

This returns validated Python data.

It does not mutate an existing viewer.

## Load project config into a viewer

The simplest entry point loads everything at once:

```python
from molsysviewer import demo

view = demo["dialanine"]
view.load_project_config("_molsysviewer.py")
```

This does three things in one call:

- registers the named styles from `STYLES` on this viewer
- updates the global add-on enable/disable defaults from `ADDONS_ENABLED` / `ADDONS_DISABLED`
- leaves the current scene unchanged (the default scene style is registered but not applied)

## Apply the default style too

Pass `apply_default=True` if you want the project default scene style applied immediately:

```python
view.load_project_config("_molsysviewer.py", apply_default=True)
```

That explicit flag is the only time the current scene is changed during config loading.

## Load only styles or only add-on defaults

If you need finer control, call the sub-managers directly:

```python
# styles only
view.styles.load_project_config("_molsysviewer.py", apply_default=False)

# add-on defaults only (global — affects all viewers created afterwards)
import molsysviewer as msv
msv.addons.load_project_config("_molsysviewer.py")
```

## Precedence rule

Project config provides reusable defaults, but explicit runtime calls still
win.

In practice:

1. load project styles
2. optionally apply the default
3. keep changing the current viewer in code when needed

Project config is a base layer, not a lock.

## What happens after loading

After loading the file, you can use the registered tags normally:

```python
view.styles.tags()
view.styles.apply(tag="publication")
```

And if you used `apply_default=True`, the default scene style is also applied
through the normal style pathway.

## Design rule

Keep this order in mind:

- Python defines
- project config registers
- canvas may apply or preview later

That order keeps the viewer behavior explicit and reproducible.

## Related pages

- General customization: {doc}`configuration`
- Styles: {doc}`../representations/styles`
- User presets from JSON/YAML: {doc}`../representations/user_presets`
