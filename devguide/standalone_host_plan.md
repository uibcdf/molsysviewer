# Standalone Host Plan

This document turns the standalone direction into an operational pre-`1.0.0`
plan. Whether MolSysViewer should have a standalone mode is already decided; the
open questions are what host shape carries the final experience, what stays
shared with the notebook and popup hosts, and how to get there without forking
the product.

## Core Position

One workbench model, one scene/state model, one add-on/workspace model, multiple
hosts. The standalone host must not become a separate product, a second UX
designed from scratch, or a place where unfinished workbench decisions are
hidden. The runtime stays the same; only the shell around it changes.

## What `standalone 0` Already Proves

The browser-hosted bridge already proves that MolSysViewer can be launched from a
CLI, that the host can exist outside a notebook, that `Core` and add-on
workspaces can be surfaced there, and that the same panel/workbench runtime and
the same export/state logic survive the move. It is the first host proof, not
throwaway work.

What it does **not** prove is the final feel: today it is still generated HTML
opened in a browser tab. Enough for `standalone 0`, not enough for the final
pre-`1.0.0` host.

## What The Final Standalone Must Feel Like

Like software, not like a web page with a widget in it: a dedicated application
window with its own name, icon and title; host-owned menus, shortcuts and
file open/save flows; a clean main canvas; workspaces and panel mode that feel
native inside the host.

It must also preserve the project's identity — calm workbench, minimal permanent
chrome, add-ons and workspaces that scale cleanly, reproducible scientific state.

## Product Aspiration

Solid, powerful, professional — which is not "visually heavy" or
"enterprise-like". It means communicating stability, clarity, deliberateness and
trustworthiness for scientific work, so the tool reads as **a real scientific
application** rather than a browser tab carrying an embedded viewer, or a demo
shell around a widget.

## What Will Make It Feel Solid And Professional

Seven signals, none of which is flashy host chrome.

1. **Dedicated app identity.** The host owns the application name, icon, window
   title and menu structure. This is the first thing that separates an app from
   a browser page.
2. **Native host affordances.** File open, save and export dialogs, keyboard
   shortcuts and menu actions come from the host, and feel native rather than
   simulated inside the viewer surface.
3. **A clean boundary between host and viewer.** The professional feel is lost
   the moment the app becomes architecturally confused: the host is a strong
   shell around the viewer, never a second implementation of it. Host concerns
   stay host concerns.
4. **A calm but deliberate workbench.** The app does not become professional by
   becoming busy. It comes from a calm canvas, a clear workspace hierarchy,
   panel stacks that scale, predictable export behaviour and visible scientific
   intent.
5. **Stable flows for real work** — open data, inspect structure, move between
   workspaces, export figures, and return later to the same state model. If
   those feel stable, the tool feels powerful.
6. **Add-ons that look native.** `Core` stays coherent, add-on workspaces are
   first-class, and the host never exposes a second-class extension model.
7. **Good error and edge behaviour.** A tool feels professional when failure is
   handled clearly: understandable startup and file-open failures, controlled
   missing-dependency behaviour, predictable add-on compatibility.

## What Would Make It Feel Weak

Warning signs: it still looks like a browser tab; browser chrome dominates;
menus and shortcuts feel accidental or missing; file open and export flows feel
improvised; add-ons feel glued on; host logic and viewer logic diverge; the shell
reads as a demo wrapper rather than an application.

## Host Options Considered

| Host | For | Against | Decision |
|---|---|---|---|
| **A. Browser tab** — today's `standalone 0` | already exists, almost no host complexity, easy to demo and debug, reuses the HTML export path directly | feels like a browser page; weak ownership of menus, dialogs and shortcuts; browser chrome competes with ours | transitional host only |
| **B. Browser popup / dedicated window** | closer to a separate app window, reachable incrementally from the current host, cheap | still browser-shaped; popup restrictions and platform inconsistency; still weak as a final host | acceptable intermediate step, not the target |
| **C. Python app shell with embedded WebView** (PySide6 + Qt WebEngine) | fits the Python ecosystem and keeps Python as the orchestration layer; a real application window with menus, native file dialogs, shortcuts and window management; embeds the same runtime | more packaging work; WebEngine integration must stay disciplined; a real app-shell maintenance surface | **preferred** |
| **D. Tauri** | light modern shell, strong app feeling | a Rust/web packaging toolchain, weaker fit with a Python-first host story, higher integration cost | interesting, not now |
| **E. Electron** | well known, very app-like | heavy for this project, poor fit with a Python-first architecture, too much host overhead for the scale | no |

The first spike of option C validated it technically while confirming it is
packaging-heavy — which is why the environment recipe is now a first-class
product concern rather than a footnote.

## Recommended Direction

**PySide6 + Qt WebEngine as the standalone host shell**: Python stays the host
and orchestration layer, the same MolSysViewer runtime is embedded in a dedicated
app window, and notebook, popup and standalone keep sharing one core viewer
model. It is the best balance visible between real software feel, reuse of the
current runtime, fit with the Python ecosystem, and keeping standalone from
becoming a second product.

## What The First Qt Spike Already Taught Us

The spike moved this from speculation to evidence. **Proven:** the runtime lives
in a real Qt application window, `QWebEngineView` hosts the viewer, the host can
show both an empty viewer and a demo-loaded one (`dialanine`), and the host is
materially stronger using the `lite` export/runtime path with a local
`viewer.js` than the AMD widget-manager export path.

**Not solved:** a final supported conda-only recipe for Qt WebEngine, and a final
release packaging strategy. The operational lesson is that Phase E can continue
on top of the working spike — packaging is a separate release question, not a
precondition for host implementation work.

## Environment Strategy Implication

The final host is an environment-recipe question, not only a packaging one,
because it must coexist with `molsysviewer`, `molsysmt`, `pyunitwizard` and the
MolSysSuite add-ons (`molsysviewer-molsysmt`, `molsysviewer-topomt`,
`molsysviewer-pharmacophoremt`). The release cannot depend on arbitrary user-side
mixing: it needs a supported recipe, whether conda-only, a supported conda+pip
combination, or a more curated UIBCDF stack later.

## Non-Negotiable Invariants

Through the standalone push: the same scene/state contract, workbench concepts,
add-on/workspace model and figure/export story, with no host-specific scene
semantics, no standalone-only panel logic, and no notebook-only business logic
hidden in the core.

**If a feature only works in standalone because the host invented new viewer
logic, that is a warning sign.**

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

| The host owns | The viewer runtime owns |
|---|---|
| app window, native menus, open/save dialogs, startup flow, global shortcuts, multi-window layout if it exists | canvas behaviour, workspaces, panel stacks, add-on runtime projection, context-menu semantics, reproducible scene/state, figure-export semantics |

**That boundary is what prevents standalone from drifting away from notebook
mode.**

## Relationship To Add-Ons

No second add-on platform: standalone reuses `molsysviewer.addons`,
`view.addons`, the same workspace specs and the same runtime projection as the
notebook. It only makes those workspaces feel native inside a real app window.

## Relationship To Figure Export

No separate export subsystem either. The host exposes the same capabilities
through its own affordances — menu items, save dialogs, perhaps a small export
assistant later — while the figure and image semantics stay owned by the viewer
runtime.

## Risks To Avoid

Building too much host chrome too early; putting viewer logic into the host;
letting standalone and notebook diverge semantically; choosing a shell too heavy
for the project; treating the current browser host as if it were already the
final answer.

## Practical Recommendation For The Next Standalone Revisit

1. Confirm the final shell choice.
2. Build the thinnest possible dedicated app window.
3. Keep `Core`, panel mode, export and add-ons visibly intact there.
4. Only then improve file, session and app polish.

## Provisional Conclusion

Keep browser-hosted `standalone 0` as the teaching bridge, treat PySide6 + Qt
WebEngine as the preferred final direction, build the final host only once the
core product is mature, and preserve one viewer model across notebook, popup and
standalone.
