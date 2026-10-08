---
summary: Redesign the canvas context menu for contextual core workflows before 1.0
issue: uibcdf/molsysviewer#179
status: partial
opened: 2026-10-08
closed:
verification: inspected
area: [canvas, interaction, selection, studio]
guard: molsysviewer/js/tests/e2e/context-menu.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Contextual core workflows in the canvas menu

**Reported:** 2026-10-08, during the principal maintainer's pre-1.0 design
review. The maintainer approves the proposed redesign as a pre-1.0 requirement.
The menu foundation, molecular-target and object/occurrence workflows are
implemented. The extended real-browser guard passes; human review remains pending.

## What

Provide a compact canvas menu with actions on the clicked target, a separately
identified active selection, and shared view/history/Studio access. Give users
explicit selection, inspection and contextual creation operations. Interaction
actions distinguish the picked occurrence, its graphical set and the stored
analysis. Configuration opens the appropriate existing Studio section.

The accepted layouts, staged implementation and acceptance scenarios are in
[`../canvas_context_menu_pre_1_0_plan.md`](../canvas_context_menu_pre_1_0_plan.md).
This report tracks one product surface; the execution plan stays outside the queue.

## How

The inspected baseline in `molsysviewer/js/src/ui/context-menu.ts` rendered repeated measurement
variants, active-selection expanders, every saved selection and rows of relevant
regions in a scrolling flat menu. The foundation replaces this with bounded
submenus and Studio collection navigation, uses the available residue identifier
and exposes shared view controls on all target families. Molecular selection and
direct target creation now use canonical scope resolution without replacing a
working selection until an explicit selection action.

At the inspected baseline, `molsysviewer/js/src/managers/viewer-controller.ts`
resolved picked interactions to participant atoms and an entity reference with
analysis name/revision, frame and occurrence index. The menu used only the set
tag for focus/delete, leaving that occurrence context unused. Panel labels may advertise closing while controller
branches opened the corresponding panel. The foundation now uses an explicit
Open Studio action and establishes menu-first Escape. The delivered occurrence seam now also carries a filtered-query revision and
query position, resolved through a bounded identity-checked inspector page.

Reuse the existing scene-object, selection, history and Studio owners. Introduce
shared applicability and target resolution rather than a second set of scene
mutations. The existing observation actions require matching query revisions and
an inspected page; connecting a pick needs a bounded resolution path, not merely
forwarding its entity reference. Reject stale frame/analysis/filter contexts.

## Why

The maintainer accepts the public API and Studio organization as adequate for
1.0, but finds the menu an incomplete entrance to the same core workflows.
The redesigned surface should make ordinary scientific interaction discoverable
without silently replacing a working selection or starting expensive calculations.

Preserve right-drag pan, named analysis persistence, experimental scientific
status, sparse queries, explicit quantities, and region hide/disable ownership.
The new menu requires a new candidate; the existing 0.24.1 files and their
qualification retain their original identities and scope.

## What was refuted

- Full collection management inside the menu makes its size depend on the scene;
  retain collection editors in Studio and only bounded relevant context entries.
- Deleting a picked interaction is not equivalent to removing its graphical set
  or stored analysis. Do not offer unsupported occurrence editing.
- A generic atom-hide mask would change the agreed region/Whole ownership model.
  Contextual creation and existing region operations preserve that model.
- One-shot explicit atom/residue/chain selection does not require adopting the
  deferred global picking-preference proposal (`uibcdf/molsysviewer#45`).
- Existing source and package certificates cannot qualify changed menu code.
  Preserve the prior campaign and qualify the replacement candidate separately.

## Implementation evidence — 2026-10-08

`MenuNavigation` owns compact in-card pages, keyboard navigation, Back and focus;
`ViewerContextMenu` owns applicability, headings and bounded collection access.
Studio section navigation reuses `GroupPanel.openSection`. Browser-owned layout
actions are consumed locally, and the menu emits a single event for mutations.
Viewport requests carry their desired state through the real Python handler,
avoiding a second toggle on its echo. History availability follows the backend.

The real dialanine/Mol*/Chromium guard
`molsysviewer/js/tests/e2e/context-menu.e2e.ts` passes, including menu/selection
separation, keyboard/focus, viewport echoes, Studio routing, scene history,
atomless applicability, bounds and Escape priority. The 17 focused menu unit
cases and TypeScript check pass. The full JS campaign passed 323/323 before the
last dispatch refinements; focused owner/browser checks cover those refinements.
The core browser campaign exposed one old test that clicked a now-collapsed
selection action; its navigation is corrected and its targeted rerun passes.
The original failure is retained separately from the remaining-suite recovery.
All 40 distinct core browser suites now have passing evidence: 16 from the
initial campaign, the corrected GroupPanel suite from its targeted rerun, and
23/23 from the unexecuted-suite recovery. This is not one uninterrupted green
campaign. The extended menu guard separately verifies the final dispatch fixes.
Runtime regeneration, 181 reporting-protocol checks and generated-index checks
pass; the board state label is synchronized to partial.
This is development evidence, not installed-package or human acceptance.

## Molecular workflows — 2026-10-08

`select_context_target`, `create_region_from_target` and
`create_annotation_from_target` share canonical target-scope resolution and call
existing selection/region/annotation owners. The hierarchy expansion helper is
also reused by the previous active-selection operation. Invalid indices, scopes,
operations and supplied stale frames fail before mutation. Atom scope requires
one identified atom; a group or bond does not silently choose its first atom.
Studio owners expose read-only target inspection and contextual anchor/A staging
without changing active selection. Calculation still needs explicit submission.
The existing centroid/representative policies are explicit in one selector;
individual-atom mode rejects ambiguous picks. Progress labels name the policy.

50 focused Python cases, 20 focused JS cases, TypeScript and the full JS lane
pass. The extended real-browser guard sends its actual menu-generated requests
to a real dialanine Python owner: region/annotation preserve selection A while
using target B, and add/remove/replace produce distinct results. It also checks
read-only inspection and Shapes/Interactions staging with no calculation.
Full Python regression evidence follows separately.

The full Python campaign executed 2,924 cases: 2,872 passed, 23 skipped and 29
failed. One failure was the test inventory's old 42-suite count; it now records
43 including this guard and its seven focused checks pass. Twenty failures were
server/browser startup denied by the sandbox; outside it, the affected five
modules pass 53 cases with one explicit GPU-environment skip. Eight Qt probe
failures remain separate: the outside-sandbox first-case repro still cannot
create a Qt OpenGL/Vulkan context and reports a D-Bus connection error. No Qt
workaround or visible-window certification is inferred; this retains the
experimental host boundary tracked by #109/#113. The full suite was not repeated.

The extended guard also found that the relayed Studio hierarchy's context
opening required local loci. A panel-only Studio has none; topology menu opening
now accepts its real relayed hierarchy and does not claim a local frame zero.
Measurement launch is consumed locally, and is absent on the panel-only surface.
The corrected main/panel-only guard and final TypeScript check pass.
The final context-owner check passes 18 cases, including refusal to route an
interaction occurrence through the unversioned molecular-target atom path.
The occurrence actions below use the guarded inspection/identity seam.

## Object and occurrence workflows — 2026-10-08

The projection now carries `query_offset`, a Viewer lookup hint in the filtered
current-frame query, shared by every segment of one occurrence. It is not an
additional MolSysMT public identity. `_inspect_picked_occurrence` verifies the
analysis name/version, filter/query revision and visible frame, reads one
bounded page and checks the exact occurrence ID. Existing inspected-page
participant APIs remain authoritative; client atom lists cannot replace them.
Provider query construction can still allocate secondary indices; this does not
promise a universal RAM limit or out-of-memory H5MSM access.

Occurrence inspection opens the existing Studio inspector. Select/focus uses
its public participant operations. Graphical-set focus/hide/edit/delete is a
separate submenu; hiding/removing its representation preserves stored analysis.
Accepted interaction updates dismiss an open occurrence context, and old
projections lacking query identity disable occurrence actions.

Annotation text/appearance, shape appearance and measurement inspection/editing
open their existing owners. Associated-atom selection is explicit. Free shapes
focus real Mol* bounds locally instead of sending an ambiguous backend object
focus. `StateHandlers.findShapeOwner` resolves current kind/tag from registered
scene refs on demand, including after rename and across same-tag object kinds.
This fixes the browser-observed missing sphere tag and avoids guessing ownership
from the presence of a measurement with the same tag. The scan reads scene refs,
not trajectory coordinates. Contextual Hide supplies a boolean requested state;
its shared handler is idempotent while the existing Studio toggle is retained.
Related regions open their existing inspector. Empty canvas adds orientation-
preserving Focus All and reuses the controls-owned Help overlay where available.

53 focused Python checks pass (occurrence/persistence, closed dispatch vocabulary,
explicit hide, and molecular-target owners). The 17 menu, four ShapesPanel,
21 interaction-normalization and four drag-dismiss JS cases pass individually.
TypeScript, runtime regeneration, 181 reporting checks and the generated indexes
pass. The full Python/core-browser campaigns already recorded above are not
repeated or upgraded to final-source qualification.

The new browser guard uses a real dialanine, real provider results and actual
rendered geometry. Its synthetic analysis deliberately includes parallel
observations beyond the first inspector page and skipped geometry. Fixture
corrections retain the provider's canonical relation/query ordering and the
record-valued `analyses()` result; an obsolete summary is correctly ignored,
so invalidation checks use the latest authoritative summary. Default annotations
use the production HTML-overlay context path rather than an assumed mesh.
The final extended Mol*/Chromium guard passes on the actual current source.
It verifies occurrence #61 (query offset 61 despite skipped geometry), one-page
inspection preserving a different working selection, participant selection/focus,
graphical Hide preserving stored analysis, accepted-summary invalidation,
annotation/shape/measurement editor routing, real free-sphere bounds focus,
Focus All and the shared Help owner. Sphere rename
and coexistence with a same-tag measurement retain the correct type/current tag.
The preceding failing fixtures and real missing-sphere-tag finding are retained
in local campaign logs; their results are not presented as passing executions.

The maintainer's review notebook is
[`../../sandbox/revision_context_menu_pre_1_0.ipynb`](../../sandbox/revision_context_menu_pre_1_0.ipynb).
Its public setup cells execute successfully: three pentalanine structures and
Buch evaluated on all three, with three occurrences. This validates preparation,
not human interaction or package qualification.

## Resolution

Pending the principal maintainer's remote-Jupyter/popout acceptance. Current interaction guidance records the delivered workflows;
archive this report and close #179 only with addressable guards and evidence.
