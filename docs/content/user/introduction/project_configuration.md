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

- `DEFAULT_SCENE_STYLE`
- `STYLES`

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
```

## Load the file directly

If you only want to validate and inspect the file:

```python
from molsysviewer.config import load_project_config

data = load_project_config("_molsysviewer.py")
```

This returns validated Python data.

It does not mutate an existing viewer.

## Load project styles into a viewer

The usual viewer-facing entrypoint is:

```python
from molsysviewer import demo

view = demo["dialanine"]
view.styles.load_project_config("_molsysviewer.py", apply_default=False)
```

That does two things:

- registers the named styles in `STYLES`
- leaves the current scene unchanged

## Apply the default style too

If you want the project default scene style to be applied immediately:

```python
view.styles.load_project_config("_molsysviewer.py", apply_default=True)
```

That explicit flag is the only time the current scene is changed during config
loading.

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
