# Interaction Modifiers and Future Directions

## Modifiers

These are not fully assigned yet, but must be tracked in the design.
Do not forget them during implementation.

### Already reserved in practice

- `Shift`
  - add to active selection

### Important future consideration

Modifiers may also influence picking level.
This is explicitly on the roadmap and should remain visible in the design.

Potential directions:

- temporary force to `atom`
- temporary force to another structural level
- interaction with tool modes
- persistent user preference for default picking level

### Idea under consideration

A promising future direction is to use `Alt` not as a fixed single-level key,
but as a gateway to a temporary selection-level chooser.

That chooser could expose levels such as:

- atom
- group
- chain
- molecule
- entity

Why this is interesting:

- it is more economical than one key per level
- it makes the hierarchy visible to the user
- it avoids freezing too many keybindings too early

This is not yet adopted as an implementation contract.
It remains a design candidate for a later UI pass.

## Shape Selection Policy

### Decided direction

- shape targets may participate in `active_selection`
- left click on a shape replaces the selection unless `Shift` is pressed
- `Shift + left click` can build mixed selections

Why:

- shapes are meaningful scientific objects, not mere decorations
- excluding them from active selection would reduce MolSysViewer as an inspection tool
- mixed selection enables richer future menus and workflows

### Consequence

Operations must decide whether they apply to:

- structural items only
- shape items only
- mixed selections
- or not at all

This is a feature, not a bug.
The selection model should stay rich even if some actions are narrower.

One concrete consequence is that context menus and submenus may need to enable,
disable, or split actions depending on whether the active selection is:

- structural only
- shape only
- mixed

## Borrowed Design Principles

The interaction contract is intentionally informed by prior art.
We are not copying UI wholesale, but we are importing useful patterns.

### From VMD

- explicit mouse/tool modes for measurements
- do not overload ordinary click semantics with hidden measurement behavior
- tool modes should be visible and clearly cancelable
- tool workflows benefit from explicit progress such as `1/2`, `2/3`, `3/4`

### From PyMOL

- selection should be a real object of work
- context actions on picked targets are valuable
- focus should be fast and natural

### From Mol*

- keep hover, selection, focus, and context as separate concepts
- use raw loci internally, but expose a simpler stable semantic contract

### From NGL / nglview

- lightweight callbacks and notebook-friendly event exposure are high-value
- picked metadata should be useful without requiring a heavy UI
- event payloads and selection objects should stay reasonably serializable and lightweight
- interaction feedback should feel immediate without requiring expensive state reconstruction

## What Is Still Open or Intentionally Deferred

- exact public Python API for exposing `hover_target`
- exact public Python API for exposing `context_target`
- whether `tool_selection` becomes a first-class public object or remains internal
- exact public Python API for exposing `active_selection`
- exact item schema inside the selection object
- exact menu contents and submenu layout
- whether empty-canvas right click opens a small generic menu or does nothing
- whether double-right-click should ever do anything
- exact mapping details of `auto` for every representation family
- exact modifier strategy beyond `Shift`
- the future `Alt`-driven selection-level chooser
- tooltip/label behavior on hover
- shared highlight/selection sync across popup/host
