---
summary: Evaluate a dedicated Studio Loader entry before System
issue: uibcdf/molsysviewer#265
status: open
opened: 2026-10-22
closed:
verification: inspected
area: [studio, ui, loading]
guard:
normative:
blocked_by: []
supersedes: []
---

# Evaluate a dedicated Studio Loader entry before System

**Reported:** 2026-10-22, proposed by the principal maintainer during the
MolSysMT addon integration work.

## What

Evaluate moving the existing **Load systems** controls from **Studio > System**
into a dedicated **Studio > Loader** entry, placed first in the Studio menu,
before System. This records a design proposal; the interface is unchanged.

## How

`molsysviewer/js/src/ui/panels/system-panel.ts` currently mounts
`SystemLoadControls` alongside the system header, context inspector and molecular
strips. `system-load-controls.ts` owns the loading controls. Review that seam to
separate the loading workspace while retaining System for inspecting and
presenting the loaded molecular system.

Before implementation, decide:

- Whether a separate entry improves discovery enough to justify another panel
  switch, and whether Loader is the clearest name.
- Which panel opens by default for empty and populated views; appearing first
  in the menu need not mean reopening Loader after every load.
- What Loader and System show before, during and after loading, including
  failures and repeated additions.
- How existing welcome and contextual loading entry points reach the same
  controls, without duplicate loading implementations.
- How the layout behaves in small notebook outputs, fullscreen, the canvas
  popup and the detached Studio popup.

Reuse the current loading tools and Python API. The proposal changes navigation,
not molecular loading semantics or ownership. Single-source, batch and
progressive loading, source selection and diagnostics must remain available.

## Why

Loading is the entry into the visualization workflow. A dedicated first entry
could make that action easier to find and reduce the responsibilities and
visual density of System. The cost is additional navigation and separation
between loading and inspecting the resulting system; the design review must
compare both arrangements against a relaxed, simple workflow.

## What was refuted

No design alternative has been rejected yet. The all-state issue search found
no equivalent proposal. uibcdf/molsysviewer#151 concerns the existing molecular
loading contract, rather than this navigation decision. The ongoing addon
receiving work in uibcdf/molsysviewer#264 is independent of it.

## Acceptance

Record the selected arrangement, responsibilities and empty/loaded behavior
before implementation. If adopted, add browser guards covering the loading
entry points, preserved workflows and popup parity. No release milestone or
immediate interface change is assigned by this report.

## Design review — 2026-10-30 (proposed, not yet adopted)

The current `SystemPanel.mount()` mounts the system header, context inspector,
`SystemLoadControls` and chain strips in one section. `GroupPanel` defaults to
System, `openSystemLoading()` opens that same section, and `setStructure()`
unconditionally switches to it. The form already owns independent and
complementary sources, Add/Replace/Append structures, source labels, atom/frame
selection, ordered pairing, correlated progress/results and error recovery.
This proposal relocates that existing owner; it creates no scientific operation.

### Alternatives

| Arrangement | Benefit | Cost |
| --- | --- | --- |
| Keep loading in System | One entry, familiar to existing users | Loading controls compete with hierarchy, sequence and inspection |
| Separate first Load entry | Directly exposes the entry task and simplifies System | Adds one navigation entry and requires clear post-load behavior |
| Load/Inspect horizontal tabs inside System | Separates tasks without another sidebar entry | Loading remains hidden behind System and adds nested navigation |

Recommend the separate **Load** entry, with **Load systems** as its panel title.
The verb states the user's task more directly than Loader; Loader remains the
issue's working name until the maintainer decides. Keep System immediately
after Load in the default order, retaining the existing other sections and
respecting subsequent user customization. A saved order that predates Load
inserts it before System rather than appending it at the end.

### Responsibilities and navigation

- Load owns source entry, source interpretation, Add/Replace/Append, per-source
  labels/selections/structures, pairing, progress, result and retry. Its form
  opens when entering the section and preserves drafts across navigation.
- System retains loaded-system identity, hierarchy/sequence, the context
  inspector, group interaction and the existing annotation overlays. Before
  loading it explains the empty state and links to Load.
- On first opening Studio for a genuinely empty molecular view, select Load;
  for a view initialized with a molecular system, select System. Later scene
  updates preserve the user's chosen section. Shape-only/addon workflows keep
  their explicit navigation rather than being redirected to Load.
- After a successful GUI load, remain in Load with the existing result counts
  and an explicit **Inspect system** action. This preserves the workspace for
  adding another source. Automatically opening System is a viable alternative,
  but would move the user away from repeated loading and any remaining drafts.
- Welcome, context-menu loading and the existing internal `openSystemLoading()`
  entry all open this one form. Opening Load does not clear a scene or selection.
  Native Ctrl+O retains its current file-chooser/replacement contract.

### Availability and lifecycle

Use the existing live-Python authority boundary: notebook, local Qt and their
qualified live popup endpoints expose loading. Static HTML without Python does
not gain a fictitious loader; it retains System and the existing inspection
tools. Paths continue to address the Python host's filesystem; this proposal
does not invent browser upload or local/remote path equivalence. Future demo
and recent-source controls remain separately deferred under #277.

Keep one `SystemLoadControls` instance per panel endpoint. Structure/hierarchy
rebuilds must not destroy its pending request or redirect the active section.
Results are consumed by their request identifier. Failure preserves the form,
error and prior valid scene; success keeps the existing Add/Replace/Append and
source-region semantics. The detached panel still forwards the same events to
the Python authority. Preserve endpoint cleanup and independent local layout.

Python remains primary: `view.load()` and its arguments, source/index maps,
box policy, molecular editing boundary and addon ownership are unchanged.
No new public wrapper is needed. The MolSysMT refactor is not a prerequisite
for evaluating this navigation; qualification against its new contract remains
part of #269 when the provider is ready.

### Implementation and acceptance after the design decision

Extract a small registered Load panel around the existing form and delegate
load results/opening to it. Keep System's inspector/strips lifecycle independent.
Replace unconditional navigation on structure updates with the chosen startup
and explicit-navigation rules. Preserve saved tab order and compact navigation.

Receive the real single/batch/progressive and complementary-file flows, all
three operations, invalid input and rejected-load recovery, pending form/drafts
through rebuilds and section changes, and initial empty/populated/shape-only
views. Check normal, compact, fullscreen, canvas-popup and detached-panel
navigation with the existing controls-visibility, composition and loading
browser owners. Source tests use the fixed compatible provider while #269 is
pending; this does not qualify its evolving implementation or a new package.

The remaining design decisions are the visible name (Load versus Loader),
separate-entry adoption and whether successful loading stays in Load. No UI
implementation is authorized by this analysis alone.

### Maintainer direction and questions to resolve — 2026-10-30

The maintainer favors the proposed direction and explicitly requests further
discussion before proceeding. Keep this as a proposal; neither the visible
name nor post-load navigation is a final implementation decision yet.

Review three concrete user boundaries before adopting it:

1. **Draft versus completed load.** Keeping the workspace available should
   preserve unsubmitted inputs and scientific options. After success, show
   clearly which request was applied and what the next action will do. An
   unchanged Add request can intentionally duplicate a system through Python;
   the GUI should make a repeat action explicit without inventing automatic
   molecular deduplication or routine confirmation dialogs.
2. **Inputs versus loaded sources.** Removing a row only removes a draft input;
   it must not imply that atoms are removed from the live system. Loaded-system
   inspection stays in System and source-region visualization stays in Regions.
   General molecular editing still belongs to the MolSysMT addon.
3. **Meaning of Load.** The current proposal covers molecular systems and
   complementary trajectories. Interaction-analysis imports and scene/session
   restoration have existing owning panels; decide their discoverability
   deliberately rather than moving every file operation into this panel.

Compare first load, adding another source, loading several sources together,
an error/retry and Python-driven replacement while another section is open.
The navigation should preserve explicit user work rather than switching tabs
on every structural update. This design discussion remains independent of
the pending MolSysMT implementation, which still owns scientific semantics.
