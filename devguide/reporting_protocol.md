# Reporting protocol

How a defect or a proposal enters `pending_bugs/` and `pending_proposals/`, and how those
two directories stay in step with the GitHub issue board.

Adopted 2026-08-14 from
[MolSysMT's protocol](https://github.com/uibcdf/MolSysMT/blob/main/devguide/reporting_protocol.md),
which is the canonical version and covers more ground. This file records the part
MolSysViewer runs and the two places where we differ.

## The rule

**If it deserves a document in one of those two directories, it deserves an issue.**

We have never written a pending document for a typo or a rename, so the document is
already the significance filter and no second one is needed.

The two records have different jobs and must not be given the same one:

| | holds | changes |
| --- | --- | --- |
| the document | the analysis, the measurements, the refuted paths | continuously |
| the issue | state, and the settled facts a reader outside the repository needs | at two moments only |

**The issue is written when it opens and when it closes. It is not maintained in
between.** If the analysis changes on the way, the document is corrected; the issue is
not rewritten, and the closing comment states the final truth.

## Identity

The issue number is the stable identity. Filenames are local names and may change; issue
numbers may not.

Cross-repository references are `uibcdf/<repo>#<number>`, never a path into another
repository's `devguide/`. We learned this the expensive way: a report filed into
`../argdigest/devguide/pending_bugs/` was consumed by the fix and deleted, and the
reference to it broke silently. An issue number does not break; it closes.

## Front matter

Every document in the two queues begins with it:

```yaml
---
summary: One line, present tense. Feeds the issue title.
issue: uibcdf/molsysviewer#34
status: open
opened: 2026-08-08
closed:
severity: medium          # bugs only
verification: reproduced
area: [export, embedding]
guard:                    # the test that fails if it comes back
normative:                # or the document that absorbed the rules
blocked_by: []
supersedes: []
---
```

`status` — `open`, `active`, `blocked`, `partial` are the **open set**; `resolved`,
`withdrawn`, `superseded` are the **closed set**, and a document in the closed set belongs
under `archive/`.

`partial` earns its place here. Three of our entries were carrying that state in prose —
the Qt host at "fix in, confirmation pending", five of six findings acted on — where
nothing could query it.

`verification` — how solid the report's own diagnosis is: `reproduced`, `measured`,
`inspected`, `upstream`, `asserted`.

**`asserted` is permitted, and it is the field that would have caught our own mistake.**
A report claiming `add_pharmacophore_features` was broken by an upstream defect was
believed, not run; it turned out the function was never callable that way for an unrelated
reason. Labelled `asserted`, the debt would have been visible instead of reading as a
finding.

## Closing

An entry closes when three things exist: the change, the record, and something that fails
if the defect returns.

1. Set `status`, `closed`, and **`guard`** — the test that fails if it comes back. For a
   proposal whose outcome is a rule rather than a behaviour, set **`normative`** instead:
   the document that absorbed the durable rules. One of the two is required for
   `resolved`; neither is for `withdrawn` or `superseded`.
2. Move the document to `archive/`.
3. Close the issue with a comment naming the fix, the guard and the record.

For reports resolved on or after 2026-09-20, the local validator applies the default
Python guard profile defined by MolSysSuite: one addressable pytest module, function, or
class-method selector under `tests/` or `devtools/tests/`. This mechanical check proves
addressability, not relevance; the resolution must explain why the selected assertion
protects the reported failure mechanism. See `MOLSYSSUITE_GUIDE.md` and the canonical
`uibcdf/molsyssuite` reporting protocol for the complete contract. A non-pytest guard
requires a bounded local selector profile before it can be used for a new closure.

### Movie playback browser guard profile

Actual-notebook Movie receiving uses the ordinary pytest selector
`tests/test_movie_studio.py::test_live_jupyter_movie_authoring` with
`MOLSYSVIEWER_JUPYTER_TEST=1`, or the explicit owner CLI
`python tests/_jupyter_live_capture.py --profile movie`. Unselected skips are
not receiving. The isolated owner checks kernel origins, keeps raw logs private
and retires its own server/kernel/browser processes and ephemeral credentials.
Core E2E CI registers this in addition to the transport-adapted `movie-studio`
browser entry. The deterministic scene/loop controls live in
`tests/test_movie_async_ownership.py`; each closing report must identify its
relevant assertions. A passing adapted comm bridge or registration alone does
not establish actual-notebook, native Qt, installed or human acceptance.

For rendered Movie camera completion and interruption, the bounded frontend profile
also accepts exactly `molsysviewer/js/tests/e2e/movie-playback.e2e.ts`. From
`molsysviewer/js/`, build with `npm run build:harness` and
`npm run build:e2e:all`, then run `node tests/e2e/movie-playback.e2e.js`.
The same entry runs in `npm run test:e2e:core` with real Mol*/Chromium.
It checks interpolation, the camera at the completion event, final position
and interruption; browser/WebGL errors fail. No node suffix, wildcard or
unregistered browser target is accepted. `tests/test_reporting_protocol.py`
verifies this exact build/runner registration.

### Trajectory plot authority browser guard profile

The bounded selector `molsysviewer/js/tests/e2e/trajectory-plot.e2e.ts` is
accepted without node suffixes, globs or commands. From `molsysviewer/js`, run
`npm run test:e2e:trajectory-plot`; the same entry is built by `build:e2e:all`
and executed in `test:e2e:core`. Browser/WebGL failure is an error and an
explicit opt-out is not passing evidence. The guard retains numeric drawing,
axis and card-lifecycle checks and invokes its real Python-authority scenario.
That scenario clicks actual SVG points, checks Python index/public callbacks,
distinct molecular conformations and actual canvas-popup feedback. A local
playhead or a test-constructed Python event alone cannot protect this boundary.
Its precision scenario additionally checks actual labels, complete raw-value
access, SVG geometry against independent Decimal/binary64 controls and
perturbed state-file recovery, retaining explicit units and frame identity.
`tests/test_reporting_protocol.py` checks the fixed entry, receiving/fixture
owners, build and core registration; those checks establish addressability.

### Live-capture availability and lifetime browser guard profile

The bounded selector `molsysviewer/js/tests/e2e/moving-capture-lifecycle.e2e.ts`
is accepted without suffixes, globs or commands. From `molsysviewer/js`, run
`npm run test:e2e:capture-lifecycle`; it builds through `build:e2e:all` and
also runs in `test:e2e:core` with the ordinary 180-second suite budget.
Browser/WebGL errors fail the guard; an explicit skip is not receiving evidence.

The real Python/Mol* fixture hides, removes and restores the actual canvas,
checks state/session refusal without replacing existing destinations, and
closes actual canvas/Studio popups during a genuinely pending scientific query.
Transport loss exercises the authority's autonomous deadline, without polling
to drive expiry. A separate stopped-frame control freezes real dynamic
membership at another frame, checks both native renderers and closes the public
View during a pending draw. This receives lifecycle semantics; it does not
replace actual Qt/Jupyter moving-capture or human observations. The validator
checks the exact entry, fixture owners and build/core registration.

### Empty and shape-only workspace browser guard profile

The bounded selector `molsysviewer/js/tests/e2e/panel-popup-welcome.e2e.ts`
is accepted without node suffixes, globs or commands. From `molsysviewer/js`,
build with `npm run build:harness` and `npm run build:e2e:all`, then run
`node tests/e2e/panel-popup-welcome.e2e.js`; it also runs in
`npm run test:e2e:core`. Browser/WebGL failure fails the guard.
The validator checks the exact entry, build/core registration and fixture owners.
The guard uses a real public Python add-on, absolute shapes and the actual widget
bootstrap/popup snapshots. It checks empty quick start, workspace access without
atoms, disabled molecular calculation, hidden/deleted geometry, Render/Clear,
remount and caller ownership, both popup types and subsequent molecular loading.
It does not qualify a particular third-party add-on or a live Jupyter installation.

### Interactions browser guard profile

For defects originating in the Studio TypeScript request path, the bounded local
non-pytest profile accepts exactly the scalar selector
`molsysviewer/js/tests/e2e/interactions-calculation.e2e.ts`. The allowed root is
`molsysviewer/js/tests/e2e/`; no node suffixes, globs or commands are accepted.
The runner is the existing esbuild/Node/Playwright lane: from `molsysviewer/js`,
build the harness and E2E entries with `npm run build:harness` and
`npm run build:e2e:all`, then run
`node tests/e2e/interactions-calculation.e2e.js`. The same entry runs in
`npm run test:e2e:core` with the shared Chromium process. Normal browser/WebGL
failure is an error; `E2E_ALLOW_SKIP=1` is not evidence for closure.

`tests/test_reporting_protocol.py::validate_guard` checks the fixed target,
its entrypoint imports/call and failing catch handler, the exported suite owner,
and registration in the build and core runner. This establishes addressability;
the closing report must identify the behavioral assertions relevant to its bug.
The lane uses real Mol* rendering and the existing real-Python fixture transport;
it verifies browser-generated requests against MolSysMT calculations. A Python
test constructing an already-correct request cannot guard a TypeScript emission
defect. Other targets retain the default pytest profile until explicitly adopted.

### Composite loading browser guard profile

The second bounded non-pytest selector is exactly
`molsysviewer/js/tests/e2e/composite-load.e2e.ts`, without suffixes, globs or
commands. From `molsysviewer/js`, run `npm run build:harness`,
`npm run build:e2e:all`, then `node tests/e2e/composite-load.e2e.js`.
It also belongs to `npm run test:e2e:core`; browser/WebGL failure remains an
error and `E2E_ALLOW_SKIP=1` does not qualify a closure.

The validator checks its entrypoint, real-Python fixture, failing catch handler
and build/core registration. The fixture loads real molecular demos through
the public Python API. `checkProgressiveWelcome` observes DOM insertions across
the actual progressive-load messages, including intermediate states that a
final screenshot cannot cover. Explicit clear and failed loading provide empty
viewer controls. Unicode card text and actions guard source-region naming.
Other browser targets still require explicit adoption.

### Initial molecular Welcome browser guard profile

The bounded selector `molsysviewer/js/tests/e2e/initial-welcome.e2e.ts` is
accepted without suffixes, globs or commands. From `molsysviewer/js`, run
`npm run test:e2e:initial-welcome`; the same entry is built by `build:e2e:all`
and executed by `test:e2e:core`. Normal browser/WebGL errors fail the guard.
It observes the actual widget bootstrap with a live Python authority, with a
DOM observer installed before runtime/controller creation and a real Mol*
`didDraw` observation after molecular representations exist. The default fixture
uses bundled TcTIM via the public demo/new-view owner; optional receiving with
`E2E_INITIAL_WELCOME_PDB_ID=1` uses `new_view('1TCD')` directly. Both typed-buffer
and JSON loading, explicit clear, failed initial loading and genuinely empty
widgets are checked. The validator resolves this exact entry, fixture and core
registration; it does not replace the behavioral receiving result.

**Archive, never delete.** A repository that deletes a closed entry breaks every reference
into it.

### Canvas controls browser guard profile

The bounded selector for Cinema, control-area reveal and shared popup controls
is exactly `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`. From
`molsysviewer/js`, build with `npm run build:harness` and `npm run build:e2e:all`,
then run `node tests/e2e/controls-visibility.e2e.js`. It is also mandatory in
`npm run test:e2e:core`. Its real Python export and Mol*/Chromium popup check
Cinema cycles, Dock/fullscreen, Settings, both reveal scopes, keyboard access,
hidden-frame updates and subscription cleanup. The same guard's notebook
scenario runs the actual widget bootstrap against a persistent Python authority
and checks runtime/control parity, UI preferences, panel popout and single-step
trajectory convergence in both windows. Browser/WebGL failures fail;
The same entrypoint's `canvas-popup-mirror-scenarios.ts` receiving owner guards
resolved camera convergence, single motion/playback clocks, exact atom subsets,
portable object identity and native GPU pick/marker behavior, local Studio
layout and frame-specific calculated hbonds in both windows. The exported-page
scenario guards context rotation and bidirectional selection without Python.
These scientific scene checks use the persistent real Python fixture and actual
Mol* rendering; a control-style comparison cannot substitute for them.
The three-scenario `controls-visibility` entry has a bounded 300-second default
runner allowance; Studio's integrated live-capture entry has a separate
360-second budget after its expanded receiving exceeded 180 seconds. Other
entries keep 180 seconds. An explicit
`E2E_SUITE_TIMEOUT_MS` retains precedence. Scientific phase timing must retain
the distinction between progress, an assertion failure and outer termination;
a timed-out run never qualifies closure by inference from earlier phases.
`E2E_ALLOW_SKIP=1` does not qualify closure. Suffixes, globs and commands are
rejected. The offline validator checks the fixture, actions, popup entrypoint
and build/core registration. Its exact entrypoint is
`withFixtureWorkspace("controls-visibility", run).catch(...)`, importing the
managed workspace owner; this preserves failing-exit checks through cleanup.

### Managed-edit and pending-reader browser guard profile

The bounded selector is exactly
`molsysviewer/js/tests/e2e/coordinate-edits.e2e.ts`, without suffixes or globs.
Build the harness and E2E entries with `npm run build:harness` and
`npm run build:e2e:all` from `molsysviewer/js`, then run
`node tests/e2e/coordinate-edits.e2e.js`. The entry is also required by
`test:e2e:core`; browser/WebGL failure fails, and opt-out is not qualification.
Its real Python/demo-system authority and Mol* endpoints receive coordinate
and box edits. `managed-system-edits-scenarios.ts` additionally checks actual
reader typing/activation, undeclared request rejection, current-primary native
nm results versus the still-old rendered box, and exact retained reader DOM
and original inert-state restoration. The offline validator verifies the entry,
fixture/receiving owners and normal build/core registration. Actual Jupyter and
popup receiving remains a separate consumer guard; this lane is not a human Qt
observation or installed-package claim.
The same entry's `centroid-measurements-scenarios.ts` and real pentalanine
bridge compare actual distance/angle/dihedral shape endpoints and labels with
independent coordinates under a non-default unit policy. They cover repeated
atom occurrences, atomic/representative controls, applied frame/coordinate
updates, visibility/rename/history/session replay and the real widget/canvas
popup mirror. The mirror waits for applied geometry rather than treating a
received frame summary as completion. The offline validator checks these
receiving owners; a Python-only series assertion cannot guard a renderer defect.

### Popup scene-bootstrap browser guard profile

The bounded selector `molsysviewer/js/tests/e2e/popup-scene-bootstrap.e2e.ts`
uses the same build/harness and real Mol*/Chromium/Python transport lane as
the moving guard below. It is built by `build:e2e:all` and belongs to the core
runner, retaining its ordinary 180-second entry budget and operation deadlines.
Run `node tests/e2e/popup-scene-bootstrap.e2e.js` after building. No suffixes,
globs or browser opt-out qualify a closure.

Its bootstrap phase withholds a genuine Python canonical reply at the test
comm seam, receives visible timeout/retry controls, releases the original late
reply and requires it to remain expired. An actual retry then reconstructs
native sphere, cell, labels, distance and dynamic-region geometry from the
authoritative scene without a second playback clock or molecular mutation.
Playback runs during bootstrap; the oracle deliberately stops at frame 1 for
geometry inspection. This control does not qualify uninterrupted moving saves.
`tests/test_reporting_protocol.py` protects entry/build/core addressability.

### Moving-state capture browser guard profile

The bounded selector is exactly
`molsysviewer/js/tests/e2e/moving-state-capture.e2e.ts`, without node suffixes,
globs or commands. From `molsysviewer/js`, run `npm run build:harness` and
`npm run build:e2e:all`, then `node tests/e2e/moving-state-capture.e2e.js`.
The entry also runs in `test:e2e:core`, with the ordinary suite deadline;
browser/WebGL failure fails and an opt-out is not passing evidence.
Its real Python pentalanine authority exercises state/session saves while
camera and trajectory keep moving, genuine delayed dynamic-region replies,
independent restoration and actual frame-dependent box/shape/annotation/
measurement/interaction geometry. A separate explicit stopped-frame control
receives an empty dynamic selection. Native callout text/leader transforms,
CPU loci and alternate-camera images are checked by its presentation scenario.
The receiver remains unadvertised until its endpoint qualification is complete;
registration of a guard is not capability or release acceptance.
The endpoint cases submit actual Studio saves from the canvas popup and its
detached Studio. Requester, capture target and result owner must agree with
their authenticated endpoints. `moving-canvas-observer.ts` observes each local
canvas's completed geometry and native frames; it never supplies a capture
reply. Genuine Python replies remain held until that owning canvas advances
twice, while the authority's playback continues. Optional receiving artifacts
retain the actual JSON/MSV files before fixture cleanup. These are required
assertions; the separate receiving record states which cases actually passed.
`tests/test_reporting_protocol.py` verifies its entry, receiving owners and
build/core registration.

### GroupPanel unit guard profile

The shared Node unit lane builds through exactly
`node scripts/build-test-bundles.mjs unit`, then runs
`node --test tests/unit/dist-index.js`. The builder owns the canonical
`tests/unit/index.test.ts` entry, Node/ESM output and the same qualified native
component-cache adapter used by the runtime and browser harness. The local
validator follows this explicit builder as well as each unit's index import;
an unrelated entry, missing builder or changed runner is not addressability.
This shared route also applies to the addon-panel and state-handler profiles.

The bounded frontend unit selector is exactly
`molsysviewer/js/tests/unit/group-panel.test.ts`, with no suffixes, globs or
commands. From `molsysviewer/js`, run `npm run test:js`; its bundled Node test
index imports this owner. The selector guards GroupPanel's DOM fixture and
panel action assertions. It is test infrastructure evidence; real rendering
continues to require the browser lanes above. `validate_guard` verifies the
owner, index import, scoped-selector regression and documented build/runner.
Other unit files retain the default profile until explicitly adopted.

## Filing one

Start from [`templates/report.md`](templates/report.md). **Open the issue first**, to
obtain the number: a document whose `issue:` still says `#000` fails the guard, and one
committed before the issue exists leaves the issue naming a path that is not on `main`
yet.

For a report that arrives from outside, the issue already exists and someone else wrote
it, possibly with the wrong diagnosis. Attending it means writing the local document and
answering once, restating *What / How / Why* **in our own terms** — that restatement is
the point of the comment, not a courtesy. Then remove `needs-triage`, and let the
document's `verification` field record whether we reproduced it, only inspected it, or
could not reproduce it at all.

## Corrections

A claim that turns out to be false is corrected, not left standing. Where depends on the
document's state:

- **In a queue:** correct in place. The document is live.
- **Archived:** append a dated correction note. **Do not edit the original claim.**

```markdown
## Correction — 2026-08-13

The section above states that `add_pharmacophore_features` was broken for positional
callers by the ArgDigest var-positional defect. It was not: it forwards to
`add_interaction_sites`, which is keyword-only, so a positional call was never possible
and fails identically with digestion bypassed. The `TypeError` measured was the target's
own binding. The report's other evidence — the three region booleans — was correct.
```

That example is real, and it is why this section exists. Rewriting an archived document
destroys the record of what we believed and when, which is the thing an archive is for. A
stale benchmark number needs no correction at all — it was true on its date. A claim that
was **never** true does.

## Security

An exploitable finding is not opened as a public issue. It goes to a
[private security advisory](https://github.com/uibcdf/molsysviewer/security/advisories/new),
and the local document stays out of the queues until a fix is released. This protocol
resumes at that point.

The advisory route is offered in `.github/ISSUE_TEMPLATE/config.yml`, so a reporter meets
it before the issue form.

## Labels and milestones

| group | labels |
| --- | --- |
| kind, exactly one | `bug`, `proposal`, `enhancement`, `documentation` |
| state, zero or one | `in-progress`, `blocked`, `partial` |
| triage | `needs-triage`, set by hand on arrival from outside |

The **`post-1.0` milestone** carries the deferral. It replaces nothing: the `post_1.0/`
subdirectories stay, and the milestone makes the same fact visible from the board.

## The ecosystem question, raised

This protocol declares itself ecosystem-wide, and `uibcdf/<repo>#<number>` is a reliable
reference in every direction only while the vocabularies mean the same thing everywhere.
Today they are prose duplicated in two repositories.

Raised as [uibcdf/molsysmt#156](https://github.com/uibcdf/molsysmt/issues/156). The aim
asked for there is the widest one: **a vocabulary every MolSysSuite tool can adopt
unchanged, including the ones that do not exist yet** — with the test that if a new tool
could not use a value on its first day, it does not belong in the shared set.

That test is what excludes the evidence labels, and the exclusion serves universality
rather than carving out an exception for us: **the reporting vocabularies travel and the
evidence labels do not.** `status` and `verification` we took without adapting a word, and they fit
28 documents of a viewer. Of the five evidence labels in their `DOCUMENT_POLICY.md`, two
cannot be earned here at all — a report is a report in any repository; a capability
belongs to the domain.

Their answer changes what we invest in the local tooling, so it is worth knowing before
adapting it further.

## Where we differ from MolSysMT

Two deliberate differences, both about what belongs in a queue:

1. **Only single-theme reports live in `pending_*`.** Plans and inventories do not: the
   pre-1.0 master plan and `what_needs_a_human_2026_08.md` sit at `devguide/`, and the two
   audit inventories in `devguide/audits/`. An issue for an eleven-phase plan would be an
   issue that never closes.
2. **Our archive stays flat, and that is a decision.** MolSysMT splits it into
   `resolved_bugs/`, `resolved_proposals/` and `withdrawn_bugs/`. Considered on
   2026-08-14 and declined: they archived *into* that shape from the start, we would have
   to migrate 28 documents, and moving them breaks references — which is the very
   argument this protocol makes for issue numbers over paths. The gain is navigation
   comfort in a directory that is read by search, not by browsing. If it ever does become
   a problem, the answer is a generated archive index, not moved files.

3. **Opening and closing on the board are done by hand.** `devtools/devguide_issue.py`
   only ever writes the derived state labels; the two comments the protocol specifies are
   where the judgement is, and a script would write them badly.

## Indexes are generated

Each queue README has a hand-written head — how to read the directory, what precedence it
carries, what it demands — and a block rendered from front matter:

```markdown
<!-- generated: devguide_index -->
...
<!-- /generated -->
```

```bash
python devtools/devguide_index.py           # write
python devtools/devguide_index.py --check   # fail if stale
```

`--check` runs in the suite. A hand-written index of documents that already describe
themselves is two independent authoritative lists, and ours was the wrong one: it went on
describing four documents as queue entries after they had been moved out.

## Checking the board against the front matter

The front matter and the board are maintained by different acts — editing a file, and
clicking on GitHub — so they will drift. Nothing in the suite can catch it: verifying an
issue needs the network and a token.

```bash
python devtools/devguide_issue.py sync --check   # report drift, exit non-zero
python devtools/devguide_issue.py sync           # apply the derived state labels
```

Run it before a release and after any session that closed or restatused an entry. It
reports a document whose issue is missing, closed while the document sits in a queue, or
carrying a state label that disagrees with `status`. The last of those it can repair; the
others need a person, because either the document should have been archived or the issue
should not have been closed, and only a human knows which.

Narrative about a closed entry belongs in that entry's own `## Resolution` section, where
someone will look for it in a year — not in the index of a directory it has already left.

## The asymmetry

It holds in one direction only:

- **Every document in the two queues has an `issue`.** Always.
- **Not every issue has a document.** One arriving from outside has none until it is
  triaged, and one that cannot be reproduced closes with the reason and never gets one.

### Studio usability browser guard profile

The bounded selector is exactly `molsysviewer/js/tests/e2e/studio-usability.e2e.ts`.
From `molsysviewer/js`, build with `npm run build:harness` and
`npm run build:e2e:all`, then run `node tests/e2e/studio-usability.e2e.js`.
It is registered in `npm run test:e2e:core`; browser/WebGL failures fail and
`E2E_ALLOW_SKIP=1` is not closure evidence. No suffixes, globs or commands are
accepted. The validator checks the build/core registration, real Python bridge,
download assertions and failing entrypoint. The suite renders real pentalanine
and checks PNG dimensions/alpha, requester-only HTML delivery, native labels,
compact navigation, floating bounds, observer/drag disposal and the discovered addon catalogue.
Its `studio-live-capture-scenarios.ts` owner uses a persistent real Python
authority, actual rendered replies and the production widget/popup transport.
It receives state/session Save and restore after camera perturbation from
primary, canvas popup and detached Studio, plus cancellation/late replies and
same-ID owner isolation. The async fixture keeps its host loop alive between
requests; a new independent View replay per request cannot receive this boundary.
Its `trajectory-shape-refresh-scenarios.ts` owner separately receives real
pentalanine shapes created by the public Python API. A held asynchronous clear
forces overlapping frame requests; actual mesh centres and molecular coordinates
on a subsequent native draw must match the latest requested frame. It also
checks the first trajectory shape created after navigating an otherwise
shape-free controller. The timing gate replaces no geometry or reply. These
assertions, rather than a desired-frame field alone, guard refresh convergence;
the same fixed Studio selector retains the build/core and fixture registration.
The complementary `tests/test_jupyter_live_capture.py` profile uses an actual
JupyterLab/kernel and fresh draw observations. Select
`MOLSYSVIEWER_JUPYTER_TEST=1` to run it locally with JupyterLab, ipykernel,
psutil, the built runtime and Playwright available. An unselected/skipped test
is not live-notebook qualification; its explicit CLI receiving route is
`python tests/_jupyter_live_capture.py` (optional `--output` must be a new path).
This profile retains private raw logs, cleans its own processes/credentials and
checks autonomous timeout as well as cancellation without late writes.
The same owner also exposes `--profile lifecycle` and the explicit pytest
guard `tests/test_jupyter_live_capture.py::test_live_jupyter_controller_release`.
With `MOLSYSVIEWER_JUPYTER_TEST=1`, two real bundled single-structure Views
receive closed-output callback retirement and weak native-controller/model/axis
collection while an independent witness retains its coordinates and completes
a fresh draw. Backing-buffer lifetime is recorded separately under #356;
passing this guard does not qualify complete memory release or E2. Default
unselected skips are not actual-host receiving.
Keyboard Settings and shared control fade assertions additionally belong to the
existing `controls-visibility.e2e.ts` profile.

### Native simulation-box browser guard profile

The bounded selector is exactly
`molsysviewer/js/tests/e2e/box-trajectory.e2e.ts`, without suffixes, globs or
commands. From `molsysviewer/js`, build with `npm run build:harness` and
`npm run build:e2e:all`, then run `node tests/e2e/box-trajectory.e2e.js`.
The same entry is mandatory in `test:e2e:core`, with its ordinary 180-second
budget and the shared Chromium process. Browser/WebGL failure fails; an
opt-out does not qualify closure. The offline validator checks this exact
entry, receiving owners and build/core registration.

Its unchanged `box-trajectory-scenarios.ts` owner receives a public
pentalanine HTML export after the Python View closes. Twelve native edge
meshes must match independent orthogonal, rotated and triclinic row-vector
controls. The persistent `box-trajectory-bridge.py` and actual widget/canvas
popup check frame following, explicit other-frame cells, rebootstrap,
same-frame navigation, replacement, styling, hide and clear on fresh completed
draws. A target index alone is not geometry evidence. #334 moves this complete
receiving function out of Studio's accumulated entry without removing any
assertion or changing operation deadlines; Studio retains its 360-second bound.

### Studio saved-list browser guard profile

The bounded selector is exactly
`molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts`, without suffixes,
globs or commands. From `molsysviewer/js`, build with `npm run build:harness`
and `npm run build:e2e:all`, then run
`node tests/e2e/studio-list-workflows.e2e.js`. It also runs in
`npm run test:e2e:core`. Browser/WebGL errors fail; `E2E_ALLOW_SKIP=1` does not
qualify closure. Select the development interpreter explicitly with `PYTHON`
when running its real-Python fixture bridge.

The offline validator checks the fixture, correlated action replies, batch
assertions and build/core registration. The guard uses real pentalanine and
Mol*/Chromium to check shape failure/recovery, native field names, local search,
marks independent of molecular selection, exact batch targets, deletion
confirmation, one-step Undo with restored annotation cells, and drafts through
frame/tab changes and deletion/restore. Registration establishes addressability;
each closing report must identify its relevant behavioral assertions.

The same guard also exercises real duplicate measurement/layer rejection and
recovery, atomic initial layer membership with Undo/Redo, unfocused new-region
names through actual runtime summaries, missing coordinate validation and
explicit-zero recovery, and named scientific-analysis confirmation/cancellation
with actual data deletion and history clearing. Its refinement fixture sends
real live editing summaries rather than substituting embedded snapshot flags.

### Addon panel unit guard profile

The bounded selector `molsysviewer/js/tests/unit/addon-panel-lifecycle.test.ts`
has no suffixes, globs or commands. From `molsysviewer/js`, run `npm run test:js`;
the canonical Node test index imports this owner. Its content-replacement
regression protects the host-owned CSS lifetime independently of consumer render
contents; the same lane checks bounded managed-state events and panel cleanup.
`tests/test_reporting_protocol.py::validate_guard` resolves the exact owner,
regression name, index and build/runner. This is component behavior evidence;
real browser, consumer/Python, popup and visible-host evidence retain their
separate scope. Other unregistered unit targets retain the default profile.

### Annotation text geometry browser guard profile

The bounded selector is exactly
`molsysviewer/js/tests/e2e/annotations-interaction.e2e.ts`, without node
suffixes, globs or commands. From `molsysviewer/js`, run
`npm run test:e2e:annotations`; the same entry is built by `build:e2e:all`
and executed by `test:e2e:core`. Browser/WebGL failure is an error and an
explicit opt-out is not qualification. The offline validator checks the fixed
entry, real Python demo fixture, failing catch handler and core/build routes.

The real-pentalanine regression takes independent native geometry samples
after completed draws. It checks font-texture identity/version across camera
and trajectory movement, every glyph centre and its native bounds, plus actual
text/background layout changes. The existing entry also retains annotation
visibility, registry, measurement, tooltip, leader and playback controls.
Registration proves addressability; moving-save, alternate-camera PNG, GPU
picking and platform acceptance retain their separately executed scope.

### Region membership lifecycle browser guard profile

The bounded selector is exactly `molsysviewer/js/tests/e2e/region-hide.e2e.ts`,
without node suffixes, globs or commands. From `molsysviewer/js`, build with
`npm run build:harness` and `npm run build:e2e:all`, then run
`node tests/e2e/region-hide.e2e.js`. It also belongs to `test:e2e:core`;
browser/WebGL failure is an error and an opt-out is not qualification.

The existing Whole/region mask, overlap, isolation, style, fade and cleanup
checks remain. Its initially empty lifecycle uses the real pentalanine Python
fixture and actual Mol* components. It checks retained identity, no initial
representation, latent style/hidden/disabled state, repeated materialization
and no recreation after deletion. Direct frame projections declare their
actual current frame. `tests/test_reporting_protocol.py::validate_guard`
checks the exact entry, assertion owners, fixture and build/core routes.
This does not substitute for actual popup bootstrap or moving-save receiving.

### Native font-atlas upload browser guard profile

The bounded selector is exactly
`molsysviewer/js/tests/e2e/font-atlas-uploads.e2e.ts`, without suffixes,
globs or commands. From `molsysviewer/js`, build with `npm run build:harness`
and `npm run build:e2e:all`, then run `node tests/e2e/font-atlas-uploads.e2e.js`.
It also belongs to `test:e2e:core`; browser/WebGL failure fails the guard.

The native lifecycle owner checks unchanged-image reuse, actual glyph writes
and every GPU alpha pixel, independent consumers, font/style/quality changes,
resize, native and physical context restoration, explicit/unknown-image
fallback and resource disposal. Its real-pentalanine fixture checks repeated
coordinate updates and native measurement endpoints. The validator verifies
that exact entry, receiving/fixture owners and mandatory build/core routes;
this proves addressability, not live Jupyter or native Qt acceptance.

### DataCard lifecycle browser guard profile

The bounded selector is exactly
`molsysviewer/js/tests/e2e/datacard-lifecycle.e2e.ts`, without suffixes,
globs or commands. From `molsysviewer/js`, build with `npm run build:harness`
and `npm run build:e2e:all`, then run `node tests/e2e/datacard-lifecycle.e2e.js`.
The entry also belongs to the mandatory `test:e2e:core` lane. Browser/WebGL
failure fails the guard; an explicit infrastructure opt-out is not receiving.

The real pentalanine/plot fixture exercises active gesture disposal, unrelated
input preservation, host/fullscreen bounds, native keyboard controls, updated
titles, popup resize/return/hide/clear and observer/timer ownership. Separate
actual sandbox and Trusted Types policies receive blocked/open-but-failed
window creation, retry/dismiss and preserved source data, without fake windows.
The existing trajectory-plot guard additionally checks real keyboard intents,
Python callbacks, complete raw values and native molecular coordinates in both
canvases for repeated/reversed x positions. The validator checks the fixed
entry, fixture and build/core registration; that proves addressability only.

### Region state-handler unit guard profile

The bounded selector is exactly
`molsysviewer/js/tests/unit/state-handler.test.ts`, without suffixes, globs or
commands. From `molsysviewer/js`, run `npm run test:js`; its bundled canonical
index imports this owner. The guard retains bare-component styling and
representation-reset assertions using the native cell-map interface. It does
not qualify actual molecular geometry or widget lifecycle. `validate_guard`
checks the exact owner, assertions, index import and documented build/runner.
