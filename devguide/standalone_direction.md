# Standalone Direction

This document records a future product direction for **MolSysViewer**:

- a standalone mode,
- launchable from the command line,
- using the same runtime and the same reproducible state model already being
  built for the notebook/script experience.

It is not a commitment to implement it immediately.
It is a design direction that should help keep current decisions compatible with
that future.

It also now carries an explicit sequencing decision:

- **standalone should be the last major implementation step before `1.0.0`**

## Core Idea

MolSysViewer should be able, in the future, to run as:

- a Python/Jupyter viewer,
- an embedded viewer inside another Python application,
- and a lightweight standalone application launched from the command line.

The key principle is:

- **one workbench model**
- **multiple hosts**

The standalone mode should not become a separate product with a separate
interaction model or a separate scene/state architecture.

## Standalone 0

Before the final standalone push, it is useful to define a first presentable
**standalone 0** for internal ecosystem teams.

It should be explicitly honest:

- not feature-complete
- not the final host UX
- not a separate product

But it should already be good enough to show how future add-ons fit into the
host.

The minimum believable target for standalone 0 is:

- a CLI-launchable host
- one main canvas window/host
- the same `Core` workspace already present in notebook mode
- add-on workspaces visible when compatible add-ons are installed
- the same panel/workbench runtime model already used in notebook mode
- no forked scene/state model
- a first Python/CLI bridge that teams can actually run and inspect

Standalone 0 does not need yet:

- the final workspace launcher/mosaic
- the final two-window auxiliary layout
- polished file/project management
- the final publication/figure UX
- every add-on integration story closed

Its job is narrower:

- prove that MolSysViewer can run as a host
- prove that the same workbench model survives outside notebook
- prove that add-ons can be surfaced there without redesigning the platform

## Why This Direction Makes Sense

MolSysViewer is already moving beyond the idea of a simple notebook widget.

The current architecture already favors a future standalone mode:

- a real frontend runtime,
- a Python ↔ TS message contract,
- persistent scientific artifacts,
- replay/export logic,
- a workbench-oriented interaction model,
- and an increasingly explicit visual UX for canvas, popup, and panels.

This makes a standalone host plausible without redesigning the product from
scratch.

## The Most Realistic First Target

The most realistic first standalone target is **not** a full desktop product.

The first sensible target is:

- **CLI launcher -> opens a MolSysViewer window/session**

Examples of the intended spirit:

```bash
molsysviewer system.pdb
molsysviewer topology.pdb trajectory.xtc
molsysviewer session.msviewer
```

This first target would already be valuable:

- easy local inspection,
- no notebook required,
- same interaction model,
- same reproducibility story.

## Levels of Ambition

It is useful to distinguish three levels:

### 1. CLI launcher

- open a viewer from files or a saved session
- minimal host
- minimal extra UX

This is the preferred first step.

### 2. Lightweight standalone app

- same viewer runtime
- richer host shell
- basic file/session handling
- still close to the current product identity

### 3. Full standalone product

- project/session management
- stronger app chrome
- possibly deeper filesystem workflows

This is a much larger product step and should not drive near-term decisions.

## What Must Stay True

If standalone arrives, these invariants should remain true:

- the scientific workbench model remains the same
- interactive exploration still becomes reproducible state
- the visual language remains minimal and calm
- `panel mode`, context menu, and workbench concepts remain compatible
- Python should remain a first-class path, not a second-class legacy path

Standalone must extend MolSysViewer, not fork its identity.

## Architectural Consequence

Current work should prefer:

- host-agnostic panel concepts
- host-agnostic workbench state
- frontend logic that does not assume notebook-only affordances
- explicit configuration and session loading paths

This especially reinforces current work on:

- `styles`
- export/replay
- `Navigate` / `Workbench`
- minimal canvas UX
- popup/canvas parity

## What Not To Do Yet

This direction should **not** cause premature work on:

- a separate desktop-only UX
- duplicate panel systems
- host-specific business logic inside the viewer core
- large application chrome before the workbench interaction model is mature

The order should stay:

1. strengthen the workbench
2. strengthen the UX model
3. strengthen the first serious image-export story
4. add a standalone host as the final pre-`1.0.0` host step

Not the reverse.

## Near-Term Implication

We do not need to implement standalone now.

But we should continue making decisions that keep it possible and natural:

- minimal but real panel architecture
- clean canvas surface
- reproducible scene/state
- explicit configuration and project-level defaults
- a frontend that can live in notebook, popup, or future standalone host

## Provisional Conclusion

Yes: a future standalone MolSysViewer is coherent with the project.

The preferred direction is:

- **standalone as another host for the same workbench**
- **CLI-first before full app ambitions**

So the direction is now:

- not immediate,
- but not vague either,
- and explicitly reserved for the final pre-`1.0.0` stage once the workbench
  and export model are already mature.

## Open Questions

These questions are intentionally still open and should not be answered too
early:

- what should the first accepted CLI inputs be:
  - structure files only
  - topology + trajectory pairs
  - saved MolSysViewer sessions
- what should the first host actually be:
  - local browser session
  - popup-style window
  - lightweight app shell/webview
- how should standalone consume project-level configuration:
  - `_molsysviewer.py`
  - explicit CLI flags
  - saved sessions
- what should count as the first reusable saved session format for standalone
- how much app chrome is acceptable before the standalone host stops feeling
  like “the same MolSysViewer”

## Two-Screen / Auxiliary-Window Direction

This idea should remain visible for future evaluation:

- in standalone mode, it may be very valuable to support a **main canvas
  window** plus a **secondary panel/workbench window**

This would fit well for users working with:

- two monitors
- monitor + projector
- screen-sharing setups where the molecular scene should stay clean and large
  while controls live elsewhere

The intended spirit would be:

- one window dedicated to the main molecular canvas
- another auxiliary window dedicated to:
  - `Navigate`
  - `Workbench`
  - and perhaps later add-on panels

This should not replace the canonical single-window experience.
It should remain an optional advanced host mode.

The same idea may later be evaluated for notebook/popup use too:

- one popup for the main canvas
- another popup or auxiliary host for panel mode

This is not a near-term implementation target.
But it is worth preserving because it could become one of the strongest
advanced-use host layouts once standalone exists.
