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
- global-first
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

## Scope of the current feature

At the moment, styles are:

- scene styles
- not focus styles
- not canvas-authored styles
- not a replacement for all region-specific representation work

That narrower scope is deliberate.

It keeps styles reproducible and easy to reason about.

## Next related pages

- Built-in presets: {doc}`presets`
- User presets from JSON/YAML: {doc}`user_presets`
- Project-level `_molsysviewer.py`: {doc}`../introduction/project_configuration`
