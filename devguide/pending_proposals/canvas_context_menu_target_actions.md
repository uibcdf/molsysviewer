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
implemented. The extended real-browser guard passes. The maintainer confirms
the reported defects are corrected; the accepted final UX refinements await
refreshed visual review.

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

## Human review findings — 2026-10-08

The maintainer reports the reviewed workflows working except for two defects:
peptide bond halves disappear next to a represented residue, and the free sphere
does not highlight/select or open its object menu. These keep #179 partial.

A real pentalanine/Mol*/Chromium diagnostic reproduces both causes. Mol*'s
default picking opacity threshold `0.5` rejects the sphere's default `0.4`;
the same screen click resolves its shape at `0.01`. A region without parent
bond context draws zero of its two expected peptide boundary half-links;
`includeParent` draws both, with zero neighbor atom spheres. Whole's mask
and the region's missing external bonds explain the observed half-link gaps;
annotations do not modify the molecular bond topology.

The region representation owner enables parent bond context for ball-and-stick
and line by default, including Inherit and representations produced by presets.
An explicit region opt-out remains available. Hover, click and context share
the registered scene-owner resolver; shape selections retain real loci and
receive the current tag/associated atoms. The canvas threshold stays positive,
so zero-opacity Whole masks remain excluded. Parent context may expand Mol*
group/marker indexing; no trajectory-memory or many-region performance guarantee
is inferred from this fix.

The expanded guard uses pentalanine with structures `[0, 8, 3]` for molecular
creation, checks generated half-link groups and neighbor sphere exclusion across
frames and own/inherited styles, and sends real pointer input to the translucent
sphere. Earlier object checks injected real loci; they did not test the pick
buffer and therefore missed this defect. Test corrections separately respect
disabled Python hover telemetry, queued render-tick selection marks, and the
existing unit assertion's changed `includeParent` default. The expanded guard
passes; the marker checks wait for real GPU picking/camera readiness and Mol*'s
queued render tick. All 323 JS cases pass after updating that prior unit
expectation, and the focused StateHandlers/ActiveSelection cases pass 30/6.
The first ordinary JS runner invocation obscured the unit assertion behind a
bundled-file failure; direct execution preserves the addressable case output.
The subsequent human reconfirmation and final UX refinement are recorded below.

The final affected-browser campaign passes **6/6** suites in one shared
Chromium: context-menu, measurements-interaction, region-hide, region-subpanel,
shapes-subpanel and scene-contracts. Visibility, overlap, style changes, dynamic
membership and Whole/region separation retain their guards. TypeScript, runtime
regeneration, 181 reporting-protocol checks and generated-index checks pass.
This is a targeted regression campaign, not a rerun of all 40 core suites or an
installed artifact qualification. The maintainer's executed notebook and other
unrelated sandbox files are preserved.

The post-push MolSysSuite policy run `37807940575` exposed two prior menu-source
`I001` import-order violations in the interactions dispatch owner and its context
target test. The follow-up only sorts those imports; pinned Ruff `0.16.5` then
passes the entire `molsysviewer`/`tests` lint scope. The original failed receipt is
retained; other hosted runs remain separate from the passing local campaign.

## Final vocabulary and UX pass — 2026-10-08

The maintainer confirms the boundary-bond and translucent-picking corrections
work. The final accepted refinement follows the existing canonical Group
contract and MolSysMT's topological group model. Public menu scopes, creation
forms, System inspector, Studio subtitle, disulfide group-name input and scope
errors now use Group. It is distinct from a user-defined Region. The canonical
Python resolver rejects missing declared group/chain membership before mutation;
the real native-demo guard covers failed selection, region and annotation
operations without clearing selection or changing the scene. It does not infer
native membership from a rendered Mol* group label.

Selection scopes keep explicit headings and shorter action text; accessible
names preserve scope. Named shapes/measurements prioritize their current tags.
Related-region rows retain focus, visibility and Studio navigation, with
rename/delete managed by Studio. The unused menu rename composer is removed.
Pointer hover keeps a soft background and keyboard focus its visible outline.

The focused context owner passes 21 Python cases; the menu owner passes 17 JS
cases. The full JS regression found one stale Studio subtitle assertion
(322/323); the corrected GroupPanel owner passes 35/35. The earlier bundled-file
report obscured the addressable case; direct Node execution identified it.
The extended real-browser guard passes, including group scopes, short labels,
related-region routing without selection changes, live object tags after rename,
and the previous boundary/picking/occurrence coverage. TypeScript and runtime
regeneration pass. This is development evidence, not candidate qualification.

The required full Python run in `molsyssuite@uibcdf_3.14`, outside the sandbox,
executes 2,938 cases: 2,907 pass, 23 skip and eight fail in 567.35 seconds.
All eight failures are the already recorded Qt transport/payload probes:
six resource-outcome cases and two standalone cases cannot create an
OpenGL/Vulkan context and report the same D-Bus connection error. The native
pytest JUnit and receptor counts agree. This does not clear the experimental
Qt-host boundary under #109/#113, and the full suite is not rerun. Chromium,
contextual scope owners, reporting-protocol checks, generated-index checks and
the full Python Ruff scope pass; no new functional failure is observed.

## Resolution

Pending the principal maintainer's final visual acceptance of the UX refinement.
The functional notebook review and defect reconfirmation are accepted. Current interaction guidance records the delivered workflows;
archive this report and close #179 only with addressable guards and evidence.
