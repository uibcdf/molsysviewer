# Studio integration review — 2026-10-09

**Implemented and locally verified:** the authorized Studio round closes
`uibcdf/molsysviewer#181`–`uibcdf/molsysviewer#188`. The maintained behavior is
in [the Studio contract](studio_interaction_contract.md) and the
[user guide](../docs/content/user/viewer/studio.md). Human notebook confirmation
of the changed card and applicable hosted results remain separate checks.
0.25.0 is agreed but unfrozen; neither 1.0 publication is authorized.

## Delivered behavior

Studio exports PNG with actual drawing-buffer dimensions, scale and background,
and downloads self-contained HTML in the requesting browser. Its transient
reply is not retained by the popup replay log; duplicates do not download again.
Keyboard controls have native semantics, named fields and visible focus;
canonical Python replies preserve focus without overriding discrete values.
Floating bounds survive dock/float, minimize and host resize, and disposal
releases observers and active drag listeners. Narrow cards use a section
selector, including Settings; wide cards retain their sidebar.

Interactions presents saved sets before its optional creation form, explains
calculation and display scopes independently, exposes required A/B selections,
and identifies its experimental status. Descriptions name available controls
and consistently use Annotation. MolSysMT is the required native backend:
its legacy addon is excluded before discovery import and explicitly refused
on registration. Other domain addons retain their contracts. Legacy molecular
editing examples now use their scientific owner and explicit reload/edit paths.

## Local evidence and limits

Development uses the explicit interpreter in `molsyssuite@uibcdf_3.14`, real
molecular demos, real Mol*/Chromium and the regenerated TypeScript runtime.
The base before this round is `84a2a75dde3a4292d5bebb2e4c4dfa41c4d56568`.
These are source checks, not a clean solver installation or package qualification.

- Full Python was run once: **2,945 passed, 23 skipped, 10 failed** in
  694.33 seconds. Eight failures concern experimental Qt OpenGL/Vulkan/DBus
  initialization. Two bookkeeping failures concern the new untracked guide
  links and the E2E inventory count; staging the new documents and correcting
  the inventory fixes them. The affected follow-up passes **26 tests**.
  This is not a green full-suite claim and Qt outcomes are preserved.
- Final reporting-protocol, tracked guide links and E2E inventory closure
  checks pass **203/203** after archiving/indexing the eight reports. #189
  remains in the active queue.
- JS regression passes **325/325** after the final focus correction;
  TypeScript, runtime/harness/E2E builds and Ruff pass. All **717** inspected
  public Python callables retain digestion and the explicit bypass argument.
- All **42 core browser cases** pass across the retained campaign and scoped
  repairs. The first shared-browser Studio attempt fails because Playwright
  disallows `download.path()` on a connected browser. The guard now uses
  `saveAs()` and checks actual bytes; that shared-browser rerun passes. The
  remaining **39/39** cases pass. These outcomes are not one uninterrupted
  green full-core invocation. Final context-menu and Studio guards pass **2/2**
  against the runtime containing the last focus correction.
- Scoped controls/GroupPanel and Interactions lifecycle/calculation checks
  pass **2/2** each. Interactions exercises 17 real calculation forms and
  independent calculated/displayed coverage. Studio checks a 1.5-scale
  **1,575 × 1,140** PNG, transparent alpha, one actual HTML download, native
  keyboard activation/focus, compact navigation, geometry and cleanup.
- The two migrated set/remove tutorials execute **17 code cells**, zero errors.
  Sphinx builds; no new broken Studio or migrated notebook references are found.
  Browser, Python and documentation diagnostics are retained during this
  session under `/tmp/msv-studio-*.log`; they are not preserved release artifacts.

## Provider and hosted follow-ups

`uibcdf/molsysmt#354` retires its provider addon in source
`dfdb31489c3a7dce921fa7b1df9e3fcd24c1f4f6`. During real hydrogen-free 1TCD
calculation, an empty bonded-to query fails; `uibcdf/molsysmt#355` fixes it in
`c3c6303f47c5df2ce50eb6aef30f0a2040190156`. The follow-up returns an analysis
with one evaluated structure and zero occurrences, as expected without
explicit hydrogens. The editable provider advances during this round. Its
installed metadata remains `0.22.4+24.g42b487869`; it does not identify those
current source fixes or qualify new canonical packages. No provider tag or
published bytes are changed here.

Prior hosted failures remain preserved: controls fade in core run
[37993286307](https://github.com/uibcdf/molsysviewer/actions/runs/37993286307),
sphere hover in source-pair run
[37993286211](https://github.com/uibcdf/molsysviewer/actions/runs/37993286211),
and empty dynamic-region restoration on macOS/Python 3.12 in
[37993286215](https://github.com/uibcdf/molsysviewer/actions/runs/37993286215).
The repaired input guards retain real drawing, hover and intermediate-opacity
assertions. Local successes do not replace those original outcomes.

`uibcdf/molsysviewer#189` remains open for the macOS region failure. Its existing
guard now reports bounded exported-region records when the recipe disappears;
the Linux check passes, but the hosted root cause is not established. Review
the next exact-source CI before deciding on a fix or closure. This observation,
human review and later exact artifact gates remain before final 1.0 clearance.

## Integration checkpoint

Implementation is pushed to `main` as
`c92c2760741aa893400fab0cf5f4407b4ca4d441`. GitHub independently reports
#181–#188 closed and #189 open. Unrelated sandbox notebooks/design artifacts
remain outside this integration. No tag, staging package, installed matrix
or public release is created by this round.

The completed exact-source checks on `c92c2760` report
[lint](https://github.com/uibcdf/molsysviewer/actions/runs/38000819782),
[suite policy](https://github.com/uibcdf/molsysviewer/actions/runs/38000820302),
[Conda governance](https://github.com/uibcdf/molsysviewer/actions/runs/38000820405),
[notebooks](https://github.com/uibcdf/molsysviewer/actions/runs/38000819785)
and [core browser](https://github.com/uibcdf/molsysviewer/actions/runs/38000819783)
success; core passes 42/42. All six Linux/macOS scientific cells in
[CI](https://github.com/uibcdf/molsysviewer/actions/runs/38000819797) pass,
while experimental Qt fails, so the run is not globally green. In the
[Python 3.14 source pair](https://github.com/uibcdf/molsysviewer/actions/runs/38000819781),
Linux Python passes but its PNG browser download times out; macOS and Windows
pass. This timeout is tracked separately under `uibcdf/molsysviewer#198`.
These completed outcomes replace the earlier pending observation; they qualify
that source checkpoint, not the second-round runtime below or a new package.
The automatic source pair retains its exact public MolSysMT 0.23.0 baseline.

For human review, restart the Jupyter kernel and refresh the browser before
constructing a new view. Check wide/narrow Studio navigation, keyboard focus,
Interactions form/scopes, floating/docked bounds and PNG/HTML downloads. The
retired MolSysMT workspace must be absent while native Interactions remains usable.


## Second Studio round — 2026-10-10

**Implemented:** `uibcdf/molsysviewer#190`–`#197` and `#199` have local
behavioral guards and archived records. #198 remains partial until the next
exact-source hosted download gate is reviewed. #189's historical macOS
restoration cause remains unresolved. The base of this second round is
`01208af0`; 0.25.0 remains unfrozen and both 1.0 publications remain paused.

Shapes now receives canonical active/saved selections, validates required
anchors, and returns correlated creation results. Failure retains its draft;
success clears it. Links/arrows use unique atom-set centers in the visible
structure with explicit quantities; their geometry is a fixed snapshot.
Unsupported aromaticity/field promises are removed from the supplied-geometry
catalogue, whose nine examples execute through the actual public Python API.

Reusable list search covers all native saved domains, stored scientific
analyses and Add-ons. Collapsed marked-item management retains marks across
filters and states the exact deletion targets. Native batches prevalidate the
complete list, roll back on failure and produce one Undo step. Visual-set
deletion preserves analyses; layer ungrouping preserves members. Creation and
advanced disclosures retain deliberate choices. Secondary editor drafts,
focus/caret and pending names survive replies, frames and tabs; missing targets
prune stale editors even when hidden. Names consistently use Annotation and
Add-ons manager, and native icon/field names are completed.

Real browser Undo revealed an additional annotation cleanup defect: Mol* ghost
removal received transforms already removed by a structure rebuild. Both cleanup
paths now check current refs sequentially. The guard asserts recovered actual
annotation state cells. PNG dimension notifications update the readout in place
and preserve a held download button; rendering failures have bounded inline
feedback. This deterministic click-race repair does not establish the cause of
historical #198.

### Evidence and interpretation

- Specific Python creation/catalogue/batch checks pass **32/32**, including nm
  and angstrom standardization policies, nonconsecutive structures and actual
  rollback/Undo/Redo. The full Python run executes once: **2,999 passed,
  23 skipped, 8 failed**. All eight failed nodes are the existing real-child
  Qt probe/standalone transport cases. No new Studio/Python contract test fails;
  this is not a green full-suite or a Qt qualification claim. Native pytest
  prints progress only because the repository and invocation both use `-q`;
  the counts above are the 3,030 terminal progress outcomes, not a rerun.
- Final JS unit command passes; the same suite contains **325 cases**. TypeScript,
  runtime and harness builds pass; scoped Ruff passes. The final real saved-list
  guard passes against the runtime containing hidden-target draft pruning.
- Reporting/index/guard addressability, tracked guide links and E2E inventory
  closure pass **216/216** after archiving/indexing. The new core inventory is
  **43 browser suites** (46 total, three remote previews excluded).
- The browser campaign passes the first **30 core suites**, then stops at an old
  Regions guard that fills the now-collapsed creation form. Its correction opens
  the native disclosure explicitly and passes. The next Selection guard uses
  an ambiguous `input` selector after row mark checkboxes were added; it now
  selects each textbox by its actual accessible name and passes. Those failures
  are retained, not described as product passes. The remaining **11/11** suites
  pass in the scoped continuation, covering all **43 core suites** across the
  retained campaign and two adapted guards. Runtime/harness refinements during development
  also mean this is not one uninterrupted frozen-source campaign.
- Three real Shapes captures inspect saved-list, creation and marked management
  layouts; no page errors. Sphinx builds and no new broken Studio links appear.
  Raw session evidence is local under `/tmp/msv-studio-refinement-*.log`, not
  a preserved installed artifact.

The explicit development interpreter is Python **3.14.7** in
`molsyssuite@uibcdf_3.14`. MolSysMT source observed during review is
`d47b528dabc0a68bf0ce90660b6c3a71701e674c`; installed metadata remains
`0.22.4+24.g42b487869`. SMonitor reports 0.19.0, ArgDigest
`0.15.0+1.g5c6711e`, and the local pytest-receptor reports
`1.1.0+19.g6d87a24`. Normal pytest is authoritative; the full run does not use
receptor rendering. Those editable identities are source-development evidence;
they do not identify new canonical Conda bytes or a clean solver installation.
Hosted workflows retain their pinned published tools and source provenance.

### Human follow-up

Restart the kernel, refresh the browser and construct a new view. In Studio,
check default folded creation with saved objects, deliberate disclosure choices,
search and marks without changing atom selection, deletion confirmation/Undo,
failed shape creation retaining anchors/name, and atom-set arrows on another
visible structure. Change tabs/frames with an unfinished secondary name and
check keyboard focus. Stored analyses must remain after deleting a visual set.
The current Interactions scientific/compatibility status remains experimental.
