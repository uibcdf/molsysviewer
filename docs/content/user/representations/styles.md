# Styles

Styles give you a higher-level way to describe the scene baseline.

Use a style when you want to say:

- "show this viewer with a known scene recipe"

instead of working only with low-level representation arguments.

## What a style is right now

In the current MolSysViewer slice, a style is a Python object that wraps the
existing scene representation contract.

Today, styles are:

- scene-level
- whole-first
- reproducible
- backed by the existing `whole.set_representation(...)` pathway

That means styles are already useful, but they are still intentionally narrow.

More concretely, the current built-in styles are best understood as
scene recipes:

- they define the structural baseline of the scene
- they do not yet define an independent visual "look" layer

Future look-oriented names such as `default-look` or `illustrative` are still a
planned direction, not part of the current runtime contract.

## Quick start

The three most common entrypoints are:

1. Apply a built-in scene recipe.
2. Register a named style in a notebook or script.
3. Load a small project catalog from `_molsysviewer.py`.

If you are just starting, begin with a built-in tag:

```python
from molsysviewer import demo

view = demo["dialanine"]
view.styles.apply(tag="polymer-and-ligand")
view
```

## The main entrypoint

Every viewer exposes:

```python
view.styles
```

Current core operations:

- `view.styles.apply(...)`
- `view.styles.current()`
- `view.styles.info()`

## Apply a built-in style

MolSysViewer includes a small built-in battery of canonical scene recipes.

Current built-ins:

- `default`
- `polymer-cartoon`
- `polymer-and-ligand`
- `atomic-detail`
- `coarse-surface`
- `empty`

These built-ins are intentionally few. The goal is to offer a memorable
baseline battery, not a large menu of overlapping options.

Typical intent:

- `default`: current default scene baseline
- `polymer-cartoon`: polymer overview
- `polymer-and-ligand`: polymer context plus ligand-friendly detail
- `atomic-detail`: atomistic inspection
- `coarse-surface`: large-scale shape overview
- `empty`: intentionally blank starting point

Example:

```python
from molsysviewer import demo

view = demo["dialanine"]
view.styles.apply(tag="polymer-and-ligand")
view
```

You can inspect the built-in catalog:

```python
view.styles.builtin_tags()
view.styles.builtin_records()
```

## Apply a style object directly

You can also create a `Style` explicitly:

```python
from molsysviewer import Style, demo

view = demo["dialanine"]

style = Style(
    preset="atomic-detail",
    name="Inspection",
)

view.styles.apply(style=style)
```

## Register your own named styles

If you want reusable styles in a notebook or script, register them on the
viewer:

```python
from molsysviewer import Style, demo

view = demo["dialanine"]

view.styles.add(
    "inspection",
    Style(
        preset="atomic-detail",
        name="Inspection",
    ),
    description="Atomistic inspection baseline",
)

view.styles.apply(tag="inspection")
```

Useful registry helpers:

- `view.styles.add(...)`
- `view.styles.get(tag)`
- `view.styles.contains(tag)`
- `view.styles.tags()`
- `view.styles.records()`
- `view.styles.count()`
- `view.styles.clear(tag=None)`

This is usually the right choice inside notebooks when you want a small local
catalog without introducing project-level configuration yet.

## Current style

To inspect the current scene style:

```python
view.styles.current()
view.styles.info()
```

This is useful in notebooks when you want to confirm the current scene baseline
before exporting or building more scene state on top of it.

## A typical workflow

One reasonable progression is:

1. Start from a built-in tag.
2. Tune your preferred baseline in code.
3. Register that baseline under a local tag.
4. Move it to `_molsysviewer.py` only when it becomes a repeated project habit.

## Relationship with presets

Right now, styles are built on top of the current preset/representation
machinery.

So:

- presets are still valid and useful
- styles give you a clearer scene-level vocabulary

If you already know you want one direct preset on the whole structure, this is
still valid:

```python
view.whole.set_representation(preset="polymer-cartoon")
```

If you want a more semantic and reusable scene recipe, prefer:

```python
view.styles.apply(tag="polymer-cartoon")
```

## Precedence and override rule

When you apply a tag, MolSysViewer resolves it in this order:

1. viewer-local registered styles
2. built-in canonical styles

So a notebook or project can intentionally override a built-in tag with a more
specific local meaning.

## Focus Styles

Focus styles are additive overlays that layer information on top of the existing
scene without resetting it.

Where a scene style says *"replace everything with this recipe"*, a focus style
says *"also show this property, here"*.

### Built-in focus styles

| Tag | Representation | What it highlights |
|---|---|---|
| `"hydrophobicity"` | molecular-surface | hydrophobicity coloring |
| `"secondary-structure"` | cartoon | secondary-structure classes |
| `"chain-id"` | cartoon | chain identifiers |
| `"element-cpk"` | ball-and-stick | element (CPK palette) |

Discover them in code:

```python
view.styles.builtin_focus_tags()
view.styles.builtin_focus_records()
```

### Apply a built-in focus style

```python
from molsysviewer import demo

view = demo["1TCD"]
view.styles.apply(tag="polymer-cartoon")          # set scene baseline first
view.styles.focus("hydrophobicity")               # add surface overlay on top
view
```

By default `focus()` covers the full system. Restrict it with `selection=`:

```python
view.styles.focus("hydrophobicity", tag="pocket-surface",
                  selection='chain_name == "A"')
```

The `tag` you provide (or the builtin name used as default) becomes both the
region tag and the focus-registry key.

### Apply a focus style with a custom representation

```python
view.styles.focus(representation="spacefill", tag="vdw-view",
                  color_scheme="element_cpk")
```

### Apply an explicit Style object

```python
from molsysviewer import Style

focus_style = Style(
    representation="cartoon",
    kind="focus",
    name="Chain Overview",
    params={"color_scheme": "chain_default"},
)

view.styles.focus(style_or_tag=focus_style, tag="chain-overlay")
```

Note that `kind="focus"` is required, and `preset`/`user_preset` are not
accepted — focus styles work only through `representation`.

### Manage active focus overlays

```python
view.styles.focus_tags()            # list active overlays
view.styles.clear_focus("pocket-surface")   # remove one
view.styles.clear_focus()           # remove all
```

Clearing a focus overlay removes its underlying region from the scene and
from `view.regions`.

### Focus styles do not disturb the scene baseline

Applying a focus style does not call `view.whole.set_representation(...)`.
It creates an independent region. The scene style you set with
`view.styles.apply(...)` is untouched.

---

## Scope summary

| Kind | Effect | Entry-point |
|---|---|---|
| **scene** | resets the whole baseline | `view.styles.apply(...)` |
| **focus** | additive overlay via region | `view.styles.focus(...)` |

## Next related pages

- Built-in presets: {doc}`presets`
- User presets from JSON/YAML: {doc}`user_presets`
- Project-level `_molsysviewer.py`: {doc}`../introduction/project_configuration`
