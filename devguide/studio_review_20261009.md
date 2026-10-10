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

### Second-round integration checkpoint

The reviewed implementation is pushed directly to `main` as
`4ca5a2480e569bc4ce3ba0ac072ac428a80cc7d3`. GitHub independently confirms
#190–#197 and #199 closed with their guards and archived records; #189 remains
active and #198 partial. Derived state labels are synchronized. Unrelated
sandbox notebooks/design files remain outside this commit.

On this exact source commit, initial hosted inspection reports
[lint](https://github.com/uibcdf/molsysviewer/actions/runs/38031216852),
[suite policy](https://github.com/uibcdf/molsysviewer/actions/runs/38031217058)
and [Conda governance](https://github.com/uibcdf/molsysviewer/actions/runs/38031217125)
success. [Core browser](https://github.com/uibcdf/molsysviewer/actions/runs/38031216791)
and [notebooks](https://github.com/uibcdf/molsysviewer/actions/runs/38031216788)
are in progress; [scientific/Qt CI](https://github.com/uibcdf/molsysviewer/actions/runs/38031216787)
and [Python 3.14 source pair](https://github.com/uibcdf/molsysviewer/actions/runs/38031216855)
are queued. These pending outcomes are not green gates. Review their final
source evidence before candidate freeze, especially the source-pair PNG check.
No tag, staging package, installed matrix or public release is created.


## Final Studio review — 2026-10-10

**Implemented and locally guarded:** #201–#204 close creation acknowledgement,
initial layer membership, new-region draft persistence, coordinate validation and
scientific deletion confirmation. `CreationFeedback` is reused by Measures,
Annotations and Layers; no new scientific detector or public Python API is added.
Layer creation carries all initial members in one validated atomic operation.
Stored-analysis deletion explicitly names the data and scene-history loss;
visual-set deletion retains its existing undoable contract.

The refinement fixture now projects actual live Python editing summaries and
frame-dependent summaries. Its draft checks therefore repaint the real forms;
embedded snapshots are not substituted for live editing flags. Browser assertions
cover duplicate creation/recovery, pending duplicate prevention, exactly one layer
request, whole-layer Undo/Redo, unfocused/hidden region drafts, explicit cancellation,
missing coordinates through repaint, explicit-zero recovery, annotation completion,
and named analysis confirmation/cancellation with actual history clearing.

### Evidence and limits

- `tests/test_studio_creation_feedback.py`: **14/14 pass**, using real pentalanine;
  state/redo preservation, complete initial-member validation, mixed-member layer
  Undo/Redo, numeric coordinate rejection and nm/Å conversion under both standard
  unit policies, referenced-analysis protection and correlated results.
- `studio-list-workflows.e2e.ts`: **passes** with real Mol*/Chromium and the explicit
  development Python; no page errors. `npm run test:js`, TypeScript no-emit,
  Ruff and the runtime/harness/E2E builds pass. Sphinx HTML builds with the
  explicit development-environment executable; the initial default-PATH build
  used 3.13 and is not counted as 3.14 evidence.
- Post-archive reporting, tracked links, architecture status and E2E inventory:
  **226/226 pass**. New report files must be staged before the clean-checkout
  link guard; unrelated sandbox files remain excluded.
- The one complete Python execution reports **2,968 passed, 45 failed, 23 skipped**
  in 552 seconds. It was run inside the restricted sandbox and must not be called
  globally green. Seventeen failures read queue documents collected before they
  were archived; the post-archive 226-case guard above passes. Twenty failures
  involve forbidden socket/browser capabilities: the five owning modules rerun
  with host capabilities report **53 passed, one explicit GPU-environment skip**.
  The remaining eight failures are the separate experimental Qt child transport/
  payload/resource probes, with OpenGL/Vulkan and sandbox-host fatal evidence.
  No full-suite repeat or optional Qt certification is claimed.

Raw source-development logs are retained locally as
`/tmp/msv-studio-final-fixes-{browser,unit,python-full,host-capabilities}.log`.
These observations retain the explicit `molsyssuite@uibcdf_3.14` editable source
provenance; they do not qualify canonical installed artifacts or another platform.

### Prior checkpoint and Windows decoding

On prior source `4ca5a248`, core browser 38031216791, notebooks 38031216788,
lint 38031216852 and both governance gates 38031217058/38031217125 finish
success. Exact source pair **38031216855 remains globally failed**: Linux and
macOS succeed, Windows job 114152375180 fails Python collection. The receptor's
bounded log identifies a cp1252 UnicodeDecodeError in catalogue source extraction.
The compact log also reports two collection errors; fresh Windows collection is
needed to exclude any remaining independent error.

#205 fixes that owned guard to read TypeScript explicitly as UTF-8. Decoding the
actual source as cp1252 reproduces the failure; **10/10 catalogue cases** pass
locally after the fix, including all nine public digested geometry examples.
This is a source fix, not a passing Windows campaign. The historical PNG timeout
#198 retains its original evidence and separate partial status; no cause is
retroactively inferred from Linux success. Scientific/Qt CI 38031216787 was
still in progress at this inspection.

### Human follow-up

Restart the Jupyter kernel and refresh the browser before constructing a fresh
view. Check a duplicate measurement name and retained anchors, layer creation
with initial members and one Undo, an unfocused region name during frame changes,
an empty coordinate versus explicit zero, and analysis deletion cancellation/
confirmation. Candidate 0.25.0 remains unfrozen; both 1.0 publications stay paused.


### Final integration checkpoint

Implementation `b1040700` is published on main, integrated with the independent
human-facing feedback governance commit `8a02568c` through `d5e81cd4`. #201–#205
are closed with their executed guards and archived records; derived state labels
are removed and `devguide_issue.py sync --check` reports 29 documents agreeing
with the board. Unrelated sandbox work is preserved.

Initial CI for `d5e81cd4` passes lint and Conda governance. Suite policy
38034071532 fails its formatting step because the duplicate-layer fixture's
long parameter row needs formatter wrapping. Applying Ruff to that test is a
layout-only correction; the original failure remains recorded. The complete
900-file formatting check and Ruff check pass after correction. Browser
38034071236, notebooks 38034071211 and source pair 38034071271 are active;
scientific/Qt CI 38034071216 is queued at this inspection. These states do not
clear the new source's hosted gates or installed qualification.

## Closure follow-up — 2026-10-10 (#206–#208)

The maintainer authorized correction of the final three findings. Region and
selection overwrites now send one request and run inside one rollback/history
boundary. Saved selections own their history, and same-system state import
preserves atom/group levels and descriptors. The first complete-scene guard
exposed that descriptor loss; it was corrected rather than weakening equality.
Region/selection and addon-registration drafts now await their correlated reply,
retaining retryable values after failure. Snapshot metadata is consistent, and
unsupported exported-HTML creation ends with inline feedback instead of a
permanent Creating… state. Actual downloaded HTML is checked in Chromium.

Focused Python guards pass 8/8. JS unit tests, TypeScript, runtime/harness builds
and real-Python Studio list and PNG/HTML browser guards pass. The single complete
Python run reports **3014 passed, 23 skipped, 8 failed**. All eight failures are
Qt transport/generation resource probes: `QRhiGles2: Failed to create context`,
`Failed to create RHI for backend: OpenGL`, followed by unavailable Vulkan and
missing probe output. This executor observation is not a passing Qt result;
no display/software workaround or skip is substituted. Raw run diagnostics are
summarized in the closure receipt. Candidate 0.25.0 remains unfrozen and both
1.0 publications remain paused.

Base-source scientific run 38034284564 completes all six scientific cells
successfully, including macOS/Python 3.12; its separate Qt job fails. This does
not establish the historical #189 root cause. Base core 38034284562 and Linux
source-pair 38034284506 still fail the PNG download wait (#198); Windows/macOS
source-pair cells pass. The PNG guard now includes bounded pointer/click, inline
status, disabled-button and drawing-buffer evidence if the unchanged wait fails.
Local export success is not a diagnosis or repair claim for those hosted failures.

The affected shared-browser checks pass individually under the core runner:
Studio PNG/HTML, Measures and Regions in the first selection; Selections and
Layers in the second. The initial Selections guard lacked the now-required
correlated completion after its rendering-only synthetic echo. Creation/rename/
promotion now consumes actual dispatcher replies from the real pentalanine
fixture. Successful checks were not repeated. Reporting protocol, current
links/architecture/API inventory, repository Ruff/format checks and TypeScript
validation pass. Source-only counts, original failed diagnostics and log digests
are retained in the [closure receipt](studio_closure_20261010.json).

## Diagnosing the remaining hosted failures — 2026-10-10

Native evidence from #189's original macOS failure identifies a 32.50 ms dynamic
query crossing the normative 25 ms freeze budget. The resulting empty static
region was then rejected by the importer. The correction preserves empty
re-evaluable recipe snapshots in either saved mode, while retaining static
membership. The dynamic-reappearance guard controls its own budget, and a new
real-coordinate guard forces the fallback and protects state/copy/session
isolation and the absence of automatic reactivation. All 16 isolation tests
pass. One complete Python regression is still running at this source checkpoint.

#198's current core run 38037909757 fails after connected pointer-down/up/click:
the button is still Rendering PNG… at the original 30-second deadline. This
narrows the observation to the Mol* screenshot path, after input and before
actual download. The guard now records bounded task progress, background/
illumination, context loss and image-pass/encoding sizes on failure. The original
wait and PNG dimensions/alpha assertions remain unchanged. The exact first three
core suites (context menu, controls visibility, Studio) pass locally through
shared Chromium. This does not diagnose or certify the hosted render wait.
Both reports remain open until their respective closure evidence is complete.

The single complete regression finishes with 3006 passed, 23 skipped and eight
Qt context initialization failures; none is a region restore failure. #189 now
closes with the forced-budget guard and its preserved native warning. The
[follow-up receipt](studio_followup_20261010.json) retains source identity,
scopes, native diagnostics and log digests. New core 38038849065 and scientific
38038849075 remain queued at observation. Old scientific run 38037909747 is
superseded: cancellation was requested while its three macOS jobs were still
queued, retaining all completed Linux/Qt results and emitted artifacts. Source
pair 38037909650 continues; no duplicated dispatch or installed matrix is added.
#198 remains partial until its render-stage cause is established and corrected.

The next core run 38038849065 fails at the same unchanged deadline with
Rendering image… / Encoding image… task updates, context intact, background off,
illumination off, rendered size 1575×1140 and an unchanged 300×150 encoding
canvas. The image data has returned, but the helper has not proceeded past its
encoding task update. The next diagnostic adds phase elapsed times and bounded
page errors to distinguish expensive rendering from a stalled task yield.
No timeout increase or image-quality reduction is used as a repair.
