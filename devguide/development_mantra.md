# Development Mantra

This page records the practical conclusions that should stay visible during
development.

It complements:

- `guiding_principles.md`
- `roadmap.md`
- `checkpoints.md`

It is not a changelog and it is not an implementation checklist.

Its role is simpler:

- keep the product identity explicit,
- prevent feature drift,
- and remind future sessions what makes MolSysViewer worth building.

## Core Product Identity

MolSysViewer should not become just another molecular viewer.

Its distinctive direction is:

- a modern molecular viewer,
- embedded naturally in Python and Jupyter workflows,
- where interactive exploration becomes reproducible scientific state.

That last point is the real product center.

The project should therefore be understood as:

- not only a renderer,
- not only a notebook widget,
- not only a wrapper around Mol*,
- but a scientific workbench for molecular-system inspection.

## What Makes The Project Coherent

The repository already shows a coherent internal logic.

The same idea appears across:

- the Python/TypeScript architecture,
- the message-history and replay model,
- the interaction design,
- the `active_selection` / `selections` / `regions` / `annotations` taxonomy,
- export and rebuild constraints,
- and the current regression strategy.

This coherence should be preserved deliberately.

When adding a feature, ask:

- does it strengthen the workbench identity,
- does it fit the existing taxonomy cleanly,
- does it become explicit viewer state,
- and can it survive replay, rebuild, export, and later scientific reuse.

If the answer is no, the feature is probably premature or misplaced.

## Main Strategic Differentiator

There are good molecular viewers and there are good notebook visualization
tools.

MolSysViewer should stand out by combining:

- a serious 3D engine,
- a Python-first public surface,
- a scientific object model above the rendering engine,
- and interaction that becomes persistent, reproducible artifacts.

This is the differentiation worth protecting.

Do not market or build the project as merely:

- "a Mol* viewer for notebooks"

The stronger framing is:

- "a reproducible molecular workbench for Python/Jupyter"

## What Must Stay Central

The highest-value state categories are not incidental details.

They are the core of the product:

- `active_selection`
- `selections`
- `regions`
- `annotations`
- `measurements`
- `layers`
- camera and scene state

These are more important than adding broad interaction for its own sake.

The project wins when exploratory work can be turned into those explicit
artifacts quickly and coherently.

## What To Be Careful About

The project is healthy, but it is entering a phase where complexity can expand
quickly.

The main risks are:

- interaction breadth growing faster than the reproducible model,
- mixed-selection semantics becoming richer than the public object model can support,
- style/presentation work drifting away from scientific state,
- and support-layer complexity becoming overhead without enough product value.

This does not mean "avoid ambitious features".

It means:

- every new layer should justify itself,
- every new interaction should have a state model,
- and every new public concept should fit the taxonomy cleanly.

## Decision Filter For Future Work

Before investing in a feature, ask:

1. Does this improve MolSysViewer as a scientific workbench?
2. Does it help users inspect, capture, replay, or communicate molecular
   knowledge?
3. Can it be represented in Python cleanly?
4. Can it survive rebuild, replay, export, and live editing?
5. Does it align with the existing vocabulary:
   `elements`, `selections`, `regions`, `shapes`, `annotations`, `layers`,
   `styles`?
6. Does it strengthen differentiation, or is it just feature accumulation?

If these questions are weakly answered, the work should probably wait.

## Current Development Mantra

Keep this sentence visible:

> MolSysViewer is not being built as just another viewer. It is being built as
> a reproducible molecular workbench where interaction becomes scientific
> state.

And this shorter operational rule:

> Do not let interaction outrun reproducibility.
