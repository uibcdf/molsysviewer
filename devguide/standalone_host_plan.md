# Standalone Host Plan

This document turns the standalone direction into an operational pre-`1.0.0`
plan.

The question is no longer whether MolSysViewer should have a standalone mode.
That is already decided.

The question is:

- what host shape should carry the final standalone experience,
- what should stay shared with notebook/popup hosts,
- and how to get there without forking the product.

## Core Position

MolSysViewer should remain:

- one workbench model,
- one scene/state model,
- one add-on/workspace model,
- multiple hosts.

The standalone host must not become:

- a separate product,
- a second UX designed from scratch,
- or a place where unfinished workbench decisions are hidden.

The runtime should remain the same.
What changes is the host shell around it.

## What `standalone 0` Already Proves

The current browser-hosted standalone bridge already proves several important
things:

- MolSysViewer can be launched from CLI
- the host can exist outside notebook
- `Core` and add-on workspaces can be surfaced there
- the same panel/workbench runtime can survive there
- the same export/state logic can survive there

So `standalone 0` is not throwaway work.
It is the first host proof.

What it does **not** prove yet is the final feel of the product.
Today it still feels like:

- generated HTML
- opened in a browser tab

That is enough for `standalone 0`.
It is not enough for the final pre-`1.0.0` host.

## What The Final Standalone Must Feel Like

The final standalone host should feel like software, not like "a web page with
a widget".

That implies:

- a dedicated application window
- app identity:
  - name
  - icon
  - window title
- host-owned menus and shortcuts
- host-owned file open/save flows
- a clean main canvas experience
- workspaces and panel mode feeling native inside the host

It should also preserve the current project identity:

- calm workbench
- minimal permanent chrome
- add-ons/workspaces scaling cleanly
- reproducible scientific state

## Host Options Considered

### Option A. Browser Tab

This is the current `standalone 0`.

Pros:

- already exists
- almost zero extra host complexity
- easy to demo and debug
- reuses current HTML export path directly

Cons:

- feels like a browser page, not an app
- weak ownership of menus, dialogs, and shortcuts
- hard to make it feel like the final standalone identity
- browser chrome competes with MolSysViewer chrome

Decision:

- keep as transitional host only
- not the final standalone target

### Option B. Browser Popup / Dedicated Window

This is a possible intermediate host:

- still browser-based
- but opened as a more dedicated window/popup

Pros:

- closer to a separate app window than a tab
- can be reached incrementally from the current browser host
- lower implementation cost than a real app shell

Cons:

- still browser-shaped
- popup restrictions and platform inconsistency can become annoying
- still weak as a final software-feeling host

Decision:

- acceptable transitional step if needed
- not the preferred final target

### Option C. Python App Shell With Embedded WebView

Examples:

- PySide6 + Qt WebEngine

Pros:

- fits naturally with the Python ecosystem
- can keep Python as the first-class orchestration layer
- provides a real application window
- gives access to:
  - menus
  - native file dialogs
  - keyboard shortcuts
  - window management
- can still embed the same runtime/workbench model

Cons:

- more packaging work than browser hosting
- WebEngine/WebView integration must be kept disciplined
- introduces a real app-shell maintenance surface

Decision:

- preferred direction for the final standalone host

### Option D. Tauri

Pros:

- light modern app shell
- strong app feeling

Cons:

- introduces a broader Rust/web packaging toolchain
- weaker fit with the current Python-first host story
- higher integration cost relative to current architecture

Decision:

- interesting but not preferred now

### Option E. Electron

Pros:

- well-known model
- very app-like

Cons:

- heavy for this project
- poor fit for the Python-first architecture
- likely too much host overhead for the product scale

Decision:

- do not prefer

## Recommended Direction

The recommended final direction is:

- **PySide6 + Qt WebEngine as the standalone host shell**

with this interpretation:

- Python remains the host/orchestration layer
- the same MolSysViewer runtime is embedded in a dedicated app window
- notebook/popup/standalone keep sharing the same core viewer model

This is the best balance currently visible between:

- real software feel
- reuse of current runtime
- fit with the existing Python ecosystem
- and keeping standalone from becoming a second product.

## Non-Negotiable Invariants

The following should remain true through the standalone push:

- same scene/state contract
- same workbench concepts
- same add-on/workspace model
- same figure/export story
- no host-specific scene semantics
- no standalone-only panel logic
- no notebook-only business logic hidden in the core

If a feature only works in standalone because the host invents new viewer logic,
that is a warning sign.

## Proposed Execution Stages

### Stage 0. Current `standalone 0`

Already present:

- CLI launcher
- empty host
- demo path
- browser-hosted standalone HTML

Purpose:

- prove hostability
- support internal ecosystem demos

### Stage 1. Host Decision And Contract

Close before large implementation begins:

- choose the host family explicitly
- write host invariants
- define what the final standalone owns:
  - menus
  - file open/save
  - windowing
  - shortcuts
- define what remains viewer/runtime territory

This document is the first part of that stage.

### Stage 2. Thin App Shell Prototype

Build a minimal dedicated host window around the existing runtime.

Expected scope:

- one application window
- embedded viewer runtime
- minimal menu:
  - File
  - View
  - Export
- open local file
- load demo
- preserve the same `Core` workspace and panel mode

Not yet required:

- rich session/project management
- advanced multi-window mode
- full add-on UX polish

### Stage 3. Standalone-Native Workflows

Once the thin host works:

- native file dialogs
- better startup/landing flow
- better open/reopen/export paths
- add-on workspace visibility in the dedicated shell

This is where standalone should stop feeling like "embedded browser content"
and start feeling like the MolSysViewer app.

### Stage 4. Advanced Host Layouts

Only after the single-window host feels solid:

- optional auxiliary panel/workbench window
- two-screen layout
- projector/presentation-oriented layouts

This remains optional advanced host territory.
It must not replace the canonical single-window experience.

## Ownership Boundary

### The Host Should Own

- app window
- native menus
- open/save dialogs
- startup flow
- global app shortcuts
- multi-window layout if it exists

### The Viewer Runtime Should Own

- canvas behavior
- workspaces
- panel stacks
- add-on runtime projection
- context menu semantics
- reproducible scene/state
- figure export semantics

That boundary is critical.
It is what prevents standalone from drifting away from notebook mode.

## Relationship To Add-Ons

The final standalone host should not require a second add-on platform.

It should reuse:

- `molsysviewer.addons`
- `view.addons`
- the same workspace specs
- the same runtime projection already used in notebook mode

Standalone should merely make those workspaces feel native inside a real app
window.

## Relationship To Figure Export

The final standalone host should not invent a separate export subsystem.

It should expose the same export capabilities through host affordances:

- menu items
- save dialogs
- possibly a small export assistant later

But the underlying figure/image semantics should remain the same ones already
owned by the viewer runtime.

## Risks To Avoid

The main risks are:

- building too much host chrome too early
- putting viewer logic into the host
- letting standalone and notebook diverge semantically
- choosing a shell that is too heavy for the project
- treating the current browser host as if it were already the final answer

## Practical Recommendation For The Next Standalone Revisit

When standalone returns as the active front:

1. confirm the final shell choice
2. build the thinnest possible dedicated app window
3. keep `Core` + panel mode + export + add-ons visibly intact there
4. only then improve file/session/app polish

## Provisional Conclusion

The current state is good enough to stop speculating loosely.

The plan is now:

- keep browser-hosted `standalone 0` as the teaching bridge
- treat PySide6 + Qt WebEngine as the preferred final standalone direction
- build the final standalone host only after the core product is already mature
- preserve one viewer model across notebook, popup, and standalone
