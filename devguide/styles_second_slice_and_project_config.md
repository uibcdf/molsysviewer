# Styles: Second Slice And Project Configuration

This page defines the recommended second step after the first implemented
`Style` slice.

The first slice established:

- `Style`
- `view.styles.apply(...)`
- `view.styles.current()`
- `view.styles.info()`

That first step gives MolSysViewer a semantic style object without changing the
frontend protocol.

The second step should now answer a practical product question:

- how should users and embedders define and reuse styles coherently?

## The Three Interaction Channels

For styles, users may eventually work in three channels:

1. programmatically in a script or notebook
2. through the viewer canvas
3. through project-level configuration when embedding MolSysViewer in another library

These three channels should **not** be developed in parallel.

They should be prioritized in this order:

1. programmatic
2. project configuration
3. canvas

This order is intentional.

## Why Programmatic Comes First

The programmatic channel is the healthiest place to stabilize `Style`.

It is:

- the clearest contract
- the easiest to test
- the most reproducible
- the most compatible with the Python-first identity of the project

So the programmatic API remains the source of truth.

The other channels should build on it, not redefine it.

## API Simplification Rule

During design it is useful to distinguish several concepts around style:

- `preset`
- `style`
- `look`
- `focus style`

But the public API does not need to expose all of them as separate first-class
objects immediately.

Current design direction:

- use the richer vocabulary in `devguide` while the model is still being
  shaped
- keep the implemented public surface small
- bias the public API toward `Style` as the main user-facing concept

This should make the user mental model more comfortable without giving up
architectural clarity internally.

## Structural Targeting vs Visual Styling

MolSysMT and MolSysViewer are sibling libraries and should keep a clean
division of responsibility.

The rule is:

- MolSysMT defines the structural target
- MolSysViewer defines the visual treatment

In practice this means:

- MolSysMT selection syntax remains the canonical way to say what subset of the
  system is being targeted
- MolSysViewer styles should describe how that target is shown
- MolSysViewer should not invent a parallel selection mini-language for style
  targeting

This distinction matters because it preserves:

- conceptual clarity
- interoperability with MolSysMT workflows
- reproducibility of scene state

So when future style APIs need to address a subset of the system, the healthy
path is:

- target via MolSysMT selection semantics directly, or
- target via MolSysViewer objects already derived from such selections
  such as `regions`, `active_selection`, or future persistent selection-backed
  entities

The unhealthy path would be:

- embedding structural targeting rules inside ad hoc style-specific grammar

## Consequence For Scene Styles

The first `Scene Style` slice is healthy precisely because it does not need a
targeting language.

It applies to the whole viewer baseline and can stay focused on visual intent.

## Consequence For Future Focus Styles

If MolSysViewer later introduces `Focus Styles` or targeted styles, they should
compose with structural targeting rather than replace it.

Healthy patterns would look like:

```python
view.regions.add("binding_site", selection="protein and within 5 angstroms of group_index==123")
view.regions["binding_site"].set_representation(preset="ball-and-stick")
```

or later:

```python
view.styles.apply_to(
    selection="chain_id=='A'",
    style="inspection-focus",
)
```

where the `selection=...` part still follows MolSysMT semantics.

## Why Canvas Should Not Come Next

The canvas is tempting, but it is still the riskiest place to define styles.

Unresolved questions remain:

- when a user changes a visual option in the canvas, is that exploratory or persistent?
- what exact Python state should that create?
- how does the user confirm that a style has become reproducible state?
- how do we avoid hidden UI-only scene state?

So the near-term rule is:

- the canvas may later **apply** or **preview** styles
- but it should not become the first place where styles are freely authored

## Why Project Configuration Comes Second

Project-level configuration is a strong second channel because it remains:

- Python-native
- explicit
- versionable
- reusable by embedders

It also matches the existing ecosystem pattern:

- `_pyunitwizard.py`
- `_smonitor.py`

So a project-level `_molsysviewer.py` is a reasonable and coherent direction.

## Second Slice Product Goal

The second slice should let users and embedders:

- define reusable named scene styles
- register them once
- apply them by name
- keep the whole mechanism explicit and reproducible

This should happen **before** any canvas authoring workflow.

## Recommended Second-Slice Public API

The next Python surface should be:

- `view.styles.add(tag=..., style=...)`
- `view.styles.get(tag)`
- `view.styles.contains(tag)`
- `view.styles.tags()`
- `view.styles.records()`
- `view.styles.count()`
- `view.styles.apply(tag="...")`
- `view.styles.clear(tag=None)`

And optionally:

- `view.styles.delete(tag)`
- `view.styles.set_tag(tag, new_tag)`

This gives styles the same product dignity as:

- `selections`
- `annotations`
- `measurements`

without pretending they already need the same full lifecycle complexity.

## Style Registry Semantics

The second-slice registry should be:

- Python-side
- explicit
- name-based
- replay-safe through the same underlying representation messages

Important rule:

- registered styles are reusable semantic recipes
- applying a registered style still uses the existing global representation
  message flow

So the registry should not create a second rendering path.

## First Registry Contract

The first style registry should store:

- `tag`
- `style`
- optional `description`
- optional `source`
  - for example `runtime`, `project-config`, or `user`

This makes the object useful in notebooks and in embedders without requiring a
full metadata system.

## Project-Level `_molsysviewer.py`

The recommended second configuration channel is:

- `_molsysviewer.py`

for projects or libraries that embed MolSysViewer.

This file should live at the root of the embedding codebase, in the same
spirit as `_pyunitwizard.py`.

Its role should be narrow:

- define project defaults
- register reusable scene styles
- optionally define one project default scene style

It should **not** become a grab bag for arbitrary runtime logic.

## Recommended `_molsysviewer.py` Shape

The first supported pattern should be simple and Python-native:

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
        representation="ball-and-stick",
        name="atomic",
    ),
}
```

This is better than inventing a new mini-language too early.

## Loader Direction For `_molsysviewer.py`

When this support is implemented, the loader behavior should be conservative.

It should:

- look for `_molsysviewer.py` only when explicitly requested or when the
  current working/project root is being used intentionally
- load only a narrow allowed surface
- import the module in a controlled way
- ignore the file cleanly when absent

The project should avoid:

- surprising ambient imports
- hidden global state mutations
- magic discovery rules that are difficult to reason about

## Recommended Runtime Rule

The programmatic API remains primary.

So `_molsysviewer.py` should behave like:

- "default style definitions available to the embedding project"

not like:

- "a hidden authority that silently overrides explicit notebook/script calls"

Explicit calls in user code should always win.

## Canvas Direction For Later

After the second slice, the canvas can become a style consumer in a controlled
way.

The first canvas-style affordances should probably be:

- apply a registered scene style
- preview a registered scene style
- confirm or revert the preview

This is much safer than a free-form style editor.

The canvas should not become the source of truth for style definitions until
all of these are answered well:

- persistence model
- explicit Python representation
- replay/export behavior
- interaction UX for confirmation/cancellation

The same rule applies to targeting:

- the canvas may help users pick or preview targets
- but the resulting persistent target should still map cleanly to MolSysMT
  selection semantics or to stable MolSysViewer selection-derived objects

## What The Canvas Should Not Do Yet

Not in the next slice:

- ad hoc editing of representation parameters without an explicit save/apply model
- hidden scene tweaks that do not surface in Python
- parallel style state that drifts from `view.styles`
- a style-specific target grammar unrelated to MolSysMT selection semantics

## Suggested Implementation Order

1. Add a Python-side style registry to `view.styles`.
2. Add inspection helpers (`tags`, `records`, `contains`, `get`).
3. Add name-based `apply(tag=...)`.
4. Add tests for registry behavior.
5. Define `_molsysviewer.py` loading policy.
6. Only after that, revisit the canvas as a style application surface.

## Minimum Test Contract For Slice Two

Tests should cover:

- adding and retrieving named styles
- applying a style by tag
- explicit call precedence over project defaults
- `_molsysviewer.py` absent/present behavior
- default-style registration remaining reproducible
- no divergence between `view.styles.current()` and underlying whole
  representation state

## Decision Rule

Keep this ordering explicit:

> Python defines. Project config registers. Canvas applies.

That ordering is the safest way to preserve reproducibility and make the
future usability genuinely good instead of merely flashy.
