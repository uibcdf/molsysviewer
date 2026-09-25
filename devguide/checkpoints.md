# Development checkpoint

This is the current handoff, not a changelog. Replace it when the project state
changes. Normative behavior remains in the contracts linked below.

## Repository state

- Branch: `main` for the coordinated 0.22.0/0.23.1 release path. The exact
  staged pair passed its hosted 15-cell installation matrix on 2026-09-24;
  publication and the remaining Viewer release gates are pending. The separate
  `python-3.14-support` branch has a five-platform, 20-cell staging milestone
  recorded below; the [1.0 release plan](path_to_1_0.md) distinguishes it from
  public-channel admission.
- Phases 5, 6, 8 and 9 and the Phase 10 persistence slice were independently
  audited and closed on 2026-08-09. Phase 8 evidence remains in
  [`performance/representative_scale_gate_2026_08.md`](performance/representative_scale_gate_2026_08.md).
- **Gate 9 of Phase 10 is done** (2026-08-12): every public callable is digested or
  deliberately exempt, and every argument name they introduce has a digester. Phase 10 is
  4 of 11.
- Phase 7 stays `⚠ 90%`: its automated seams are complete and its two visible-window Qt
  observations are not, and cannot be done here.
- `sandbox/Smoke_Test.ipynb` is developer-owned scratch state. Never stage it and
  never use it as architectural evidence.
- `molsysviewer/viewer.js` was regenerated with `npm run build:runtime`; it is a
  generated artifact, never a source file.
- **Reports are coordinated with the issue board** (2026-08-14). All 29 documents in
  `pending_bugs/` and `pending_proposals/` carry front matter and a GitHub issue; the
  queue READMEs are generated; `devtools/release_gate.py` is gate 11's command. See
  [`reporting_protocol.md`](reporting_protocol.md).
- Two commands need the network and live outside the suite:
  `python devtools/devguide_issue.py sync --check` compares the board with the front
  matter, and `python devtools/devguide_index.py --check` (which does run in the suite)
  keeps the queue READMEs honest. Run the first before a release and after any session
  that closed or restatused an entry.
- Whether the reporting vocabularies become an ecosystem-wide shared source of truth is
  asked at [uibcdf/molsysmt#156](https://github.com/uibcdf/molsysmt/issues/156). Their
  answer changes what is worth investing in the local tooling.
- **Citation and Zenodo metadata are a checked contract** (2026-08-14).
  [`release_and_citation.md`](release_and_citation.md) is normative;
  `devtools/validate_citation.py` holds `CITATION.cff`, `.zenodo.json` and the five
  derived surfaces to one concept DOI, and is a step of the release gate.
  `prepare_release.py` updates them in one pass and `verify_zenodo_release.py` checks the
  archive afterwards, because a pushed tag does not request ingestion and the version DOI
  arrives asynchronously.
- **The MolSysMT alias seam is public and closed** (2026-08-14). MolSysViewer commit
  `5bb01b8e` builds its caller-scoped ArgDigest tables from
  `molsysmt.attribute.get_argument_aliases()` introduced by MolSysMT commit
  `4267d414f`; no normalization module imports MolSysMT private alias data. The
  `molsysmt>=0.22.0` floor is the schema boundary, and the durable rule is in
  [`digestion_and_dependencies.md`](digestion_and_dependencies.md). MolSysMT issue
  [#157](https://github.com/uibcdf/molsysmt/issues/157) is closed.
- **The ArgDigest alias-collision blocker is fixed on source `main`** (2026-08-14).
  Commit `c46cd01` rejects alias-plus-canonical and multi-alias target collisions with
  `ArgumentConsistencyError` before normalization can discard a value. MolSysViewer has
  a public regression and raises its wheel and Conda floor to the planned patch release
  `argdigest>=0.12.1`; publication of that release remains a prerequisite for clean
  installation dogfooding.

## Coordinated Conda release with MolSysMT 0.22.0 — in flight

MolSysViewer must keep `molsysmt>=0.22.0`: that is the first MolSysMT line providing
`molsysmt.attribute.get_argument_aliases()`, which MolSysViewer imports without a
fallback. Lowering the floor would make the environment solve and the package fail at
import time.

The current boundary was remeasured on 2026-09-19:

- MolSysMT workflow run `33849332945`, commit
  `e5820d4794f8ce31a1f64e345c5edf9073ade975`, published build-2 ABI3 artefacts for
  `linux-64`, `linux-aarch64`, `osx-64`, `osx-arm64` and `win-64` to
  `uibcdf/label/staging`. Each supports Python 3.11--3.13.
- The public channel still stops at MolSysMT 0.12.0 and MolSysViewer 0.7.0. A Linux
  dry-run with staged MolSysMT 0.22.0 resolves on Python 3.12 but not 3.13: MolSysMT is a
  hard dependency of MolSysViewer, and its own runtime dependency on MolSysViewer can find
  only the old interpreter-specific public artefacts. This is the publication cycle,
  reproduced rather than inferred.
- The `0.22.0` and `0.23.0` MolSysViewer tags predate the fixes for
  uibcdf/molsysviewer#88 and #89. They must not be moved, and rebuilding either tag would
  omit the fixes that make hosted CI and the package build reach the dependency boundary.
  Freeze a new candidate version from a reviewed commit before dispatch; `0.23.1` is the
  natural patch candidate, but it is not declared until that release decision is made.
- The MolSysViewer Conda core remains `noarch: python`, bounded to
  `python>=3.11,<3.14`. One package therefore serves the entire supported matrix.

The repository now carries the two missing pre-publication routes:

1. A manual Conda dispatch requires an exact SHA, a new version and a build number. It
   builds the noarch package against `uibcdf/label/staging`, runs the full recipe test,
   and uploads only to the `staging` label. There is deliberately no `--no-test`
   exception: conda-build places the just-built MolSysViewer package in its test channel,
   closing the dependency loop with staged MolSysMT.
2. Manual dispatches of `CI`, `CI_e2e` and `Documentation notebooks` may explicitly
   put staging first and pin MolSysMT 0.22.0. Normal push, pull-request and scheduled runs
   continue to use the public channel. Staging is a release-candidate input, never a
   silent development default.
3. Staging uses Conda build 0 and a GitHub Release uses build 1. Validated coordinates are
   not overwritten with different bytes.
4. Structural guards require the exact checkout, separate staging/main publication
   branches, retained producer evidence, the recipe test on both branches, and the
   explicit staging input on every hosted gate.

The 2026-09-24 state is: MolSysMT 0.22.0 ABI3 build 5 and MolSysViewer
0.23.1 noarch build 1 are in staging. MolSysMT run `35967239820` passed the
exact-pair matrix on five native platforms and Python 3.11–3.13 (15 cells).
That run predated the later explicit Conda-record channel/URL/hash guard and
does not satisfy that stronger check retroactively.

The next hosted Viewer gates have now crossed the original dependency barrier:
documentation run `35997846329` installed successfully, then exposed two
Showcase API/example failures. The pocket-blob Python multi-iso gap is tracked
as uibcdf/molsysviewer#99; the channel example used an obsolete argument.
Both notebooks execute locally after branch fixes, and the hosted
Documentation notebooks rerun `36016496850` passed every notebook on exact
branch commit `7c4e0cd968e9530033e35221683ca085fe1d37cd`. This closes
the staged-dependency documentation execution gap for that candidate, not
the ordinary public-channel `main` gate.
E2E runs `35998036249` and `36016496630` installed and built, then stalled
extracting an unused Playwright Chromium archive; neither entered the browser
tests. The latter stopped at a deliberate 15-minute timeout. The workflow now
checks and records the runner's Chrome, which the E2E harness already selects.
CI run `36017021764` passed the Qt job but failed all six Python matrix jobs
after the solver barrier, exposing missing test-only dependencies and JS setup;
the branch has a local fix and requires a hosted rerun. The staged-dependency
documentation gate is green, but CI and E2E are not yet green.

The follow-up `CI` run `36019810641` then passed Qt and four of six Python
matrix jobs. The remaining cells exposed Node 26 incompatibility in JS
coverage and a macOS fast-close WebSocket test race; the focused corrections
are local only pending another hosted run. `CI_e2e` run `36019810581` reached
22/37 real browser scenarios before a 30-second PNG-download timeout. The
same scenario passed locally, but the local aggregate stopped at 25/37 on
the command-line Chrome/localhost limitation of uibcdf/molsysviewer#77.
Neither environment has certified the full E2E suite; uibcdf/molsysviewer#100
tracks an evidence-lane redesign. Keep the 1.0 release gate open.

The interim split under #100 is now explicit: local source-pair
`test:e2e:portable` passed 36/36 with Chrome 149 and real WebGL2. Hosted
`CI_e2e` has been changed to run that portable lane, but has not yet been
rerun. The excluded `remote-session` is a separately runnable server-GPU
lane, not a skipped pass. `nauta` does have real NVIDIA GPUs outside the
sandbox; its worker still fails to commit command-line HTTP navigation.
Changing the worker to navigate through CDP did not fix it (`Page.navigate`
timed out), so that product change was reverted. The test bridge now reports
stages and has a bounded wait. Defer the GPU launch investigation until after
the coordinated pre-1.0 package publication; no 37/37 or 1.0 gate is claimed.
Staging-enabled `CI` run `36034111547` on Viewer commit `ac3dd891` then
passed Qt but all six Python jobs stopped at one stale distribution guard:
it searched for the former E2E step name rather than the new portable
command. The guard now checks the command itself; 24 focused local tests
pass. The staging-enabled rerun `36036802158` on Viewer commit `2594f1a2`
then passed all seven jobs (six Python matrix cells and Qt). This is branch
CI against the staged dependency, not the public-channel `main` gate.
The portable `CI_e2e` rerun `36038233512` reached scenario 23/36 and failed
at the same hosted PNG-download timeout in `remote-client-rendering` as the
earlier full-suite run. This is not a portable E2E pass and cannot certify
the separately deferred server-GPU lane. Stop rerunning this unchanged test;
the reproducibility/evidence work is tracked by #100.
The detailed diagnosis is in [`pending_bugs/hosted_ci_has_never_passed.md`](pending_bugs/hosted_ci_has_never_passed.md).

The remaining order is:

1. resolve or explicitly defer the reproducible hosted
   `remote-client-rendering` PNG-download timeout under #100 before claiming
   a hosted E2E pass; staging-enabled CI passed 7/7 in `36036802158`, but
   the latest ordinary
   CI run `35984241119` could not resolve
   `molsysmt>=0.22.0` from the public channel before reaching product tests.
   The subsequent micromamba `ENOENT` was cleanup fallout, not the cause;
2. repeat the exact-pair gate with the stronger provenance assertion when a
   final release candidate is selected, and settle the clean-install PDB path
   under `uibcdf/molsysmt#200`;
3. decide on public release coordinates and publish only after both projects'
   exact-commit package gates pass, without a bootstrap exception in either
   public build. The deferred server-GPU lane remains visible in #100 and must
   not be represented as a passing hosted or local test.

The next candidate decision is now recorded: `python-3.14-support` includes
current `main` in both repositories, and fresh unoccupied versions
MolSysMT `0.22.4` ABI3 build 0 / MolSysViewer `0.23.4` noarch build 0 are
planned. Anaconda returned HTTP 404 for each version across labels. The
committed route plans require staging; a Release event cannot rebuild a
staged coordinate, and separate workflows promote one exact SHA-256-verified
file at a time after the full 20-cell installed-pair gate. These promotion
workflows have local structural and shell-syntax tests but no hosted promotion
yet. The earlier Viewer CI 7/7 pinned staged MolSysMT `0.22.0`; manual CI,
E2E and notebook gates now require an explicit MolSysMT version input and
must be rerun for `0.22.4` rather than credited retroactively. At this
selection checkpoint, neither package had been uploaded; build-0 staging is
recorded below. #100 still owns the hosted E2E
timeout and the separate server-GPU lane.

The maintainers accepted an explicit, limited pre-1.0 exception for this
`0.22.4`/`0.23.4` candidate: the hosted portable E2E failure in
`36038233512` and the unvalidated server-GPU lane do not block *this package
publication* if all other exact-candidate gates pass. Local portable E2E
passed 36/36, but hosted portable E2E did not pass and full 37/37 has no
certification. #100 remains open; the strict 1.0 E2E and visible-window gates
are unchanged. The exception must accompany the release decision, not turn
the failed hosted run into a success.

The `0.23.4` citation surfaces were first prepared for 2026-09-24 and
refreshed to the intended 2026-09-25 release date after the local date
changed; if publication slips, rerun the preparation and candidate gates
before tagging. MolSysSuite `policy-v1.4.11` now registers both transition
issues (`uibcdf/molsysmt#237`, `uibcdf/molsysviewer#93`) as `authorized`.
Both candidate callers pin that policy release and synchronize its canonical
guide; the exact central repository checker passes locally for each. The
package metadata and test matrix still target Python 3.14, while the README
badge and its distribution test retain the publicly admitted 3.11–3.13 range.
The badge may add 3.14 only after the coordinated release and independent
channel installations permit central `admitted` status. This branch must not
become the public `main` claim until the exact 20-cell installed-pair gate and
other applicable pre-1.0 release checks pass. npm returned 404 for
`@uibcdf/molsysviewer@0.23.4` when checked on 2026-09-24. No npm package,
Git tag, GitHub Release, or Conda promotion has been created for this
candidate.

The complete local Viewer Python suite passed **2,112 tests with 14 accepted
skips** in 61.43 seconds using 12 workers and explicit source paths for both
candidate repositories plus the released SMonitor `0.16.0` tag. The prior
unisolated run was not used as candidate evidence. MolSysMT's matching local
suite passed 10,225 tests with 11 known skips; its fast release gate passed
13/13. These local results support the source candidate but do not replace
the hosted exact-commit gates or the 20-cell installed-pair rerun. Source-pair
workflow `36061167557` passed Linux and macOS/Python 3.14 but failed Windows
in one release-route test; its other Windows results were 2,100 passed and
23 skipped. Windows resolved the test's `bash -n` invocation to the WSL
launcher, although the promotion script itself runs only on Ubuntu. The test
now asserts that runner identity on every platform, retains its promotion
contract checks on Windows, and checks Bash syntax on POSIX. The matching
MolSysMT test uses the same rule. The failed run cannot be credited as a 3.14
pass; the corrected exact commits need a new hosted Windows run.
The new policy's Ruff 0.16.5 formatting gate exposed three older files in
the Viewer test infrastructure; they were formatted without changing test
behavior. Repository-wide Ruff lint and format checks now pass, and the
focused distribution/release-route modules pass 23/23.
The corrected source-pair run `36062983964` passed Linux, macOS and
Windows/Python 3.14. The first staged noarch `0.23.4` build 0 passed its
recipe test (`36064255601`), the installed-pair run `36065287565` passed
all 20 platform/Python cells, Viewer CI against staged MolSysMT passed all
seven jobs (`36064424260`), and notebooks passed in `36064424563`.
The first MolSysMT full-CI run `36063386092`
exposed its outdated controlled ArgDigest source pin: release 0.12.1 writes
the read-only `hint` property inherited from SMonitor 0.16.0. Published
ArgDigest 0.13.0 fixes this; its exact tag source passed the 27 affected
local MolSysMT contract tests. The complete local Viewer suite passed
2,112 tests with 14 skips, and the matching MolSysMT suite passed 10,225
with 11 skips, using the exact ArgDigest 0.13.0 and SMonitor 0.16.0 sources
and 12 workers. Both components now declare 0.13.0 as the minimum. The
existing build-0 staged files and their passing installed cells remain
technical evidence only; build 1 and the complete exact-pair gates must
replace them before promotion.
Build-1 producers passed in MolSysMT `36102277287` and Viewer
`36102277047`, and the corrected source-pair run `36102309036` passed all
three Python 3.14 platforms. MolSysMT's Rust-wheel run `36102309653` then
found an independent stale sibling-source set in its installed-public-smoke
job. Its PyUnitWizard revision lacks `configure.has_active_policy()`, an API
used at import time by both packages and introduced in PyUnitWizard 0.25.0.
The wheel and Conda minimums are being corrected to 0.25.0 in both projects,
and MolSysMT's smoke will reuse the central controlled-source manifest and
an exact Viewer commit. Build 1 becomes diagnostic only; build 2 and fresh
exact-commit gates are required before promotion.
The subsequent MolSysMT build 3 (`36113593257`) passed all five ABI3
platforms; Viewer build 3 (`36113593292`) passed as noarch. Their exact
installed-pair run `36115388335` passed 20/20, Viewer CI `36115388294`
passed 7/7, notebooks `36115388415` passed, the Python 3.14 source pair
`36113593440` passed all three operating systems, and MolSysMT full CI
`36113593532` and Rust wheels `36113593413` passed. The pre-tag source
review then found `uibcdf/molsysviewer#102`: the committed Viewer runtime
still embedded `0.23.0`, even though Conda and npm rebuild it for `0.23.4`.
The earlier Viewer noarch artifact and pair gates are diagnostic only for
the corrected Viewer source. Regenerate the committed runtime for `0.23.4`,
prove the ordinary Python wheel carries that same version, and rerun the
Viewer producer and exact-pair gates before tagging. MolSysMT's unchanged
build-3 ABI3 artifacts do not need to be rebuilt.
The first Viewer build-4 attempt (`36119181642`) proved the source bundle
check but stopped before packaging: the build environment lacked `wheel` for
the new isolated-wheel preflight. No build-4 Conda file was uploaded; the
environment now declares `wheel` and build 4 can be retried without replacing
an existing staged coordinate.

## Separate Python 3.14 staging slice

On 2026-09-24, technical staging-only coordinates were created for the newer
source branches: MolSysMT 0.22.3 ABI3 build 0 on Linux x86-64 (producer run
`35990161344`) and MolSysViewer 0.23.3 noarch build 0 (build and recipe-test
run `35990850975`). An exact Linux/Python 3.14 dry-run resolves both from
`uibcdf/label/staging`. Subsequent exact-pair runs passed Python 3.11–3.14
on Linux x86-64 (`35992241212`), Linux ARM (`35993063086`), Windows
(`35993616429`) and macOS ARM (`35993242687`): 16 installed cells with
explicit environment records. macOS Intel's build (`35992423543`) and
four-cell matrix (`35995465959`) then passed, bringing the exact staging pair
to 20/20 installed cells across five native platforms. Every run retained
four explicit environment records; the MolSysMT validator checked the
staging URL and SHA-256 of both packages. These are five targeted runs, not
a single combined workflow or a public-channel claim. The 3.14 branch
proposal records the source and artifact hashes.
These are not Git tags, public releases, or a decision to ship those version
numbers.

A prior local `devtools/build_against_staging.sh` result remains useful evidence about
the noarch shape and recipe tests, but it is not a substitute for these exact hosted
candidate gates. Neither repository may publish unilaterally merely to turn the other's
CI green.

## Validation observed

- Current full run, 2026-09-19: **2,067 Python passed, 13 accepted skips, exit 0** in
  63.09 seconds with 12 workers
  (`python -m pytest --receptor=llm -n 12 tests/`). The focused distribution and
  staging-contract slice passes 16 tests; Ruff and the generated devguide indexes pass;
  the Conda recipe renders as one `noarch` build-0 candidate. No artifact was uploaded.
- Previous baseline, 2026-08-15: **1,612 Python passed, 4 skips, exit 0**
  (`python -m pytest --receptor=llm -n 12 tests/`). The `selections.md` failure of
  2026-08-14 is closed: the page called deprecated `add_label()` while the documentation
  harness promotes `DeprecationWarning` to an error, and it now uses the canonical
  annotation manager. The failure was deterministic, not flaky — the warnings-registry
  explanation was tested directly and falsified. The suite ran green three consecutive
  times at 1,611 before the guard below was added.
- Gate 9 was verified by behaviour as well as by count: exercising a broad slice of the
  public surface with `UserWarning` promoted to an error produces no
  `DigestNotDigestedWarning`.
- **No documented example may call a deprecated API** (2026-08-15).
  `test_no_documented_example_calls_a_deprecated_api` reads the deprecations out of the
  package's own warning messages and checks every python block and notebook cell under
  `docs/content` against them, scoped by function — `add_set_alpha_spheres(centers=…)` is
  correct and `add_sphere(centers=…)` is not, so a check on the bare name would flag 59
  correct examples. It found one survivor the running gate could not see:
  `showcase/pharmacophore.ipynb` still called `add_pharmacophore_features()`, now
  `add_interaction_sites()`. Running a page is not what makes its example wrong.
- The latest frontend validation remains the Phase 8/9 result: **273 JS**, `tsc` clean,
  **30/30 E2E**, `build:runtime` and `test:perf` green. **No TypeScript changed since**,
  so it was not re-run.
- Every guard added in this round is mutation-verified; each test says which mutation
  kills it.

## Phase 8 result

The measurement matrix uses 2,882, 26,214, 104,856 and 314,568 atom molecular
supercells, crossed with 1, 10 and 100 structures where feasible. Fixture work
is owned and timed separately as MolSysMT work; no time coordinate is invented.

Main findings:

1. Typed coordinate transport scales well with structure count. At 314,568
   atoms, topology metadata is still 25.3 MiB JSON and Python serialization is
   about 1.63 s. Topology encoding, not `view.molsys`, is the next data-plane
   target.
2. Real Mol*/SwiftShader rendering is the scale ceiling: the 314k x 10 case
   peaks around 5.67 GiB process RSS and first becomes visible in about 31 s.
   Page close removes the scale-proportional renderer process.
3. Slow structure switches are variable first-visit/state-tree work, not a fixed
   1.36 s transport tax. Do not prewarm every structure without an A/B against
   startup and peak memory.
4. Host traffic remains isolated from a 314k popup transfer: 0.0088 ms against
   the fixed 100 ms threshold.
5. Qt assembly still peaks at 2x for representative coordinate-dominated
   payloads. Preallocating `bytearray` does not improve that shape; a future fix
   needs lower-copy delivery.
6. Scene-history snapshots now use compact deterministic JSON bytes and a
   64 MiB combined undo/redo budget. A 100k literal-overlay history dropped from
   about 212 MiB to 52.66 MiB retained RSS. The byte guard is mutation-verified.

## What is next

**Read [`capability_audit.md`](capability_audit.md) before writing any claim about what
MolSysViewer does.** It is generated; regenerate with
`python devtools/capability_audit.py --write`.

**A defect or a proposal is filed under
[`reporting_protocol.md`](reporting_protocol.md)** — front matter, a GitHub issue, and a
`guard` named at close. Adopted 2026-08-14 from MolSysMT; the 28 documents in the two
queues all carry it.

Resume in this order:

1. **Widen `EXECUTABLE_PAGES`** in `tests/test_documentation_pages_run.py`. It executes
   three documentation pages today; the rest of the markdown is run by nothing, which is
   how a half-applied rename left a `NameError` in four pages. This is the only remaining
   item that needs neither another machine nor a decision. What the whole tree already has
   is the *static* half — every page parses and none calls a deprecated API — so what
   widening buys is the `NameError` class of defect, which only running finds.

   The audit's second-sharpest gap is next to it: **five capabilities have no browser
   observation at all** — trajectory plot, movie, `save_state`/`load_state`,
   `save_session`/`load_session`, units. Three are `experimental` and say so; the other
   two are `stable`. See the *Nothing has watched these draw* section of
   [`capability_audit.md`](capability_audit.md), and
   [`pending_proposals/evidence_a_stable_capability_has_not_earned.md`](archive/evidence_a_stable_capability_has_not_earned.md)
   (uibcdf/molsysviewer#65), which is the entry that asks for the decision rather than the
   suites.
2. In parallel when the required workstation is available, close Phase 7's two
   observations: Qt real-window/GPU and ten human live-demo replacements. Never
   report the existing offscreen/browser evidence as those observations.
3. Complete scientific dogfooding and the remaining human decisions in
   [`pending_proposals/what_needs_a_human_2026_08.md`](what_needs_a_human_2026_08.md)
   — three items, all needing a screen or a judgement.
4. Once sibling releases are ready, close dependency channels; build wheel and
   conda artifacts; verify imports, resources and the one-line path from clean
   installations.
5. Run `python devtools/release_gate.py` and release only when it exits zero. It
   refuses to be silent: anything it cannot run is `BLOCKED` with the reason, and
   that is still a non-zero exit. Before tagging, `python devtools/prepare_release.py`
   sets the release fields across every citation surface; after publishing the GitHub
   Release, the Zenodo verification workflow confirms the archive.

Closed in Phase 10 so far: atomic overlay-state file helpers, notebook CI, opt-in hover
telemetry, and public-callable digestion. Hover is runtime/session state rather than scene
state.

*Updated 2026-09-02:* the state helpers were "not a molecular-session bundle" until #38
closed. There is now a second unit rather than a wider first one — `view.save_session()` /
`molsysviewer.load_session()` write a `.msv` carrying the molecular system, while
`save_state` still writes the overlay and the vantage point alone.

### One proposal waiting on a decision, not on work

`what_save_state_promises.md` was the other. Its five decisions were answered on
2026-09-01 and it is now
[`archive/what_save_state_promises.md`](archive/what_save_state_promises.md); the
cheapest and most valuable of them — binding a state document to the structure it was
written from — was answered by re-resolving onto a different structure rather than by
refusing it.

- [`archive/addon_maturity_and_ownership.md`](archive/addon_maturity_and_ownership.md)
  — the maturity vocabulary is defined; each toolkit adopts it by re-declaring
  `meta["status"]`. Until then the README reports what each add-on says today.

## Resume cautions

- Read
  [`pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md),
  [`scene_contracts.md`](scene_contracts.md),
  [`data_plane_architecture.md`](data_plane_architecture.md) and
  [`runtime_message_router.md`](runtime_message_router.md) before changing the
  runtime.
- Python remains the authority for reproducible scene state.
- Keep `molsysmt.MolSys` as the scientific authority; optimize wire projections
  instead of introducing a second in-memory truth.
- A sequence of structures need not have time. Missing box and time remain
  missing; never synthesize either for transport convenience.
- Binary buffers are runtime data, never scene history.
- Never validate rendering with `E2E_ALLOW_SKIP=1`.
- If a mutation remains green, first suspect that it hit the wrong layer or a
  stale build artifact.
