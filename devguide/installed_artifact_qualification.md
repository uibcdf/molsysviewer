# Installed-artifact qualification

**Support-library follow-up — 2026-10-06:** exact published SMonitor 0.19.0
and ArgDigest 0.15.0 pass 122 bounded installed checks (14 expected skips)
with a wheel from fixed Viewer source and public MolSysMT 0.22.4, in a fresh
Linux/Python 3.14.8 environment. Runtime/version, dependency consistency,
origins and installed archive-member checks pass. The compatible scientific
pair and complete release matrix remain pending. See
[the receiving check](python_ecosystem_policy_adoption.md#published-support-library-receiving-check--2026-10-06)
and [its receipt](support_library_receiving_20261006.json).

**Current status — 2026-10-03:** an integrated design wheel is prepared and
bounded public/experimental installed checks pass. Its complete Python attempt
failed; the core browser follow-up was interrupted for the maintainer's design
discussion. The principal maintainer
requires `molsyssuite@uibcdf_3.14` for development. Compatible public dependencies
and a committed exact candidate remain open. See
[the integrated candidate](#integrated-design-candidate--2026-10-03).

**Earlier status — 2026-10-02:** provider #288/#289 are closed and verified in an
experimental installed pair with Python 3.14 / Pandas 3. The periodic guard is
adapted, three real coordinate-invalidation cases are added, and all **94 bounded
Interactions cases** plus three installed import guards pass. The once-run full
installed attempt failed; its diagnosed tooling/environment cases pass in bounded
corrections (309 passed, one skip). Compatible public dependencies and exact-candidate
qualification remain open. See [the current follow-up](#provider-invalidation-guards-and-installed-follow-up--2026-10-02).

## Ordinary published-dependency pair — 2026-10-01

**Ordinary public workflows pass on Linux x86_64 / Python 3.14.7.** The current
Viewer wheel works with published dependencies. Interactions still requires a
compatible MolSysMT publication under `uibcdf/molsysviewer#114` and
`uibcdf/molsysmt#250`. This is a local development artifact, not a frozen 1.0
candidate or cross-platform certification. Public documentation remains last.

## Artifact and dependency identity

Viewer working tree is based on `6f49013c80c7a10eb09a1220b2236d879d8ecd5a`.
An isolated packaging copy, `/tmp/msv-installed-source-20261001`, preserved its
Git context. Versioningit, `npm run build:runtime` and wheel building ran
sequentially there. The original checkout's generated version and package
metadata were preserved. An initial wheel built before the runtime finished
was rejected by the version validator and rebuilt; only the corrected wheel
below was installed and tested.

| Artifact | Identity |
| --- | --- |
| Viewer wheel | `molsysviewer-0.23.4+40.g6f49013c.dirty-py3-none-any.whl` |
| Wheel SHA-256 | `c24eefbc4c3421ef149a2a67c820e41a68eacb4783fd4167682de2846045e4a7` |
| Public MolSysMT | `molsysmt-0.22.4-pyabi3h03bb3b7_3.conda` |
| Provider SHA-256 | `e2ac3c779f17b2ca2aa7655fc6a2a349de558de229f479525826b5deaa6f8d3e` |
| Isolated environment | `/tmp/msv-installed-gate-20261001` |

The official file inventory and GitHub Releases were rechecked on 2026-10-01:
0.22.4 remains the latest published provider. The API's stale package-level
`latest_version` field was not used. Sources:
[UIBCDF package inventory](https://api.anaconda.org/package/uibcdf/molsysmt),
[MolSysMT releases](https://github.com/uibcdf/molsysmt/releases).

Dependencies came from public `uibcdf`, `conda-forge` and `ambermd` channels.
No sibling checkout was installed. Exact observed versions: ArgDigest 0.13.0,
DepDigest 0.12.0, PyUnitWizard 0.27.0, SMonitor 0.18.0, AnyWidget 0.11.0 and
NumPy 2.5.3. Viewer replaced the older public Viewer pulled transitively by
MolSysMT. Import/version assertions use distribution metadata and actual module
paths rather than the superseded Conda record for Viewer. Every checked package
imports from this environment's `lib/python3.14/site-packages`, with no editable
installation. `pip check` and source/wheel runtime-version validation pass.

## Observed installed behavior

Tests run outside the repository, with isolated Python, importlib collection
and `MOLSYSVIEWER_TEST_INSTALLED=1`. Test configuration rejects scientific
packages imported from checkouts. The repository supplies tests and Playwright;
Viewer and its runtime resource come from the wheel.

| Selection | Result |
| --- | --- |
| `tests/molsysviewer/test_molsysview_load.py` | 7 passed |
| Basic tools and merge, annotations, selections, regions, state, sessions, units and HTML sidecars | 108 passed |
| `tests/test_exported_page_opens_from_disk.py` | 8 passed in actual Chrome with WebGL2/SwiftShader, offline |
| Helper import guard | Passed; restoring a bare helper import makes it fail |
| Helper guard, view lifecycle, teardown and addons | 59 passed in installed mode; the same 59 pass in development |
| `devtools/interactions_provider_compatibility.py --installed` | Ordinary views pass; calculation refuses the unavailable backend explicitly |

The nine-file public selection is `test_tools_basic.py`,
`test_tools_basic_merge.py`, `test_annotations.py`, `test_selections.py`,
`regions/test_region_flow.py`, `test_state_v2.py`, `test_session_bundle.py`,
`test_units_under_a_user_policy.py` and `test_html_scene_sidecar.py` under
`tests/`. The browser selection checks single-file portability, scene presence,
version notices, the Python-session requirement and visible failure instead of
false readiness when restoration fails.

The collection defect `uibcdf/molsysviewer#131` requires package-qualified local
test imports. Its subprocess guard imports actual helper, lifecycle and addon
consumers without putting the tests directory on `sys.path`; installed-mode
scientific package origin checks remain intact. The full development run
initially stopped during collection at two remaining bare `conftest` imports;
those and a function-local addon import were corrected. Subsequent targeted
checks and whole-suite collection are recorded in the archived defect. The
aborted run is not a passing full regression run.

The subsequent release-checker task (`uibcdf/molsysviewer#103`) closes that
development regression gap: its complete Python run passes 2,370 tests with
20 skips, exit 0. This does not enlarge the installed-artifact selection above
or qualify the unavailable public Interactions backend; see
[the current checkpoint](checkpoints.md#resume-in-one-page).

## Reproduction

Build an isolated copy of the desired Viewer revision with its Git context.
Derive `_version.py` through versioningit, run `npm run build:runtime` in its
`molsysviewer/js/`, **wait for completion**, then build the wheel. Validate it:

```bash
python devtools/validate_python_wheel_runtime.py \
  --source-root /tmp/msv-installed-source-20261001 \
  --expected-version 0.23.4+40.g6f49013c.dirty \
  --wheel /tmp/msv-installed-wheel-20261001/molsysviewer-0.23.4+40.g6f49013c.dirty-py3-none-any.whl
```

Create a fresh public-channel environment with the runtime requirements in
`pyproject.toml`, plus pytest, PyYAML and pip. Install the wheel without resolving
new dependencies and run `python -I -m pip check`. From `/tmp`, with that
interpreter and its matching `CONDA_PREFIX`:

```bash
MOLSYSVIEWER_TEST_INSTALLED=1 python -I -m pytest --import-mode=importlib \
  /home/diego/repos@uibcdf/molsysviewer/tests/molsysviewer/test_molsysview_load.py -x -q
MOLSYSVIEWER_TEST_INSTALLED=1 python -I -m pytest --import-mode=importlib \
  /home/diego/repos@uibcdf/molsysviewer/tests/test_exported_page_opens_from_disk.py -x -q
python -I /home/diego/repos@uibcdf/molsysviewer/devtools/interactions_provider_compatibility.py \
  --installed --expected-viewer-version 0.23.4+40.g6f49013c.dirty
```

Repeat the bounded public selection with the same isolation. Substitute paths
and expected versions for a future candidate; preserve installed module-location
assertions. Chromium and existing JS test dependencies supply the browser driver.

Local evidence: `/tmp/msv-installed-provenance-20261001.json`,
`/tmp/msv-installed-load-20261001.log`, `/tmp/msv-installed-public-20261001.log`,
`/tmp/msv-installed-browser-20261001.log`,
`/tmp/msv-installed-helper-mutation-20261001.log` and
`/tmp/msv-installed-interactions-gate-20261001.log`. Reproducible commands and
assertions remain in the repository; temporary logs are additional evidence.
The lifecycle checks are `/tmp/msv-installed-lifecycle-20261001.log` and
`/tmp/msv-installed-source-lifecycle-20261001.log`; whole-suite collection is
`/tmp/msv-installed-source-collection-20261001.log`. The initial 89 affected
development tests also pass (`/tmp/msv-installed-source-specific-20261001.log`).

## Remaining qualification

Keep the base dependency floor. Do not invent an Interactions version floor
from this result. Repeat [the real scientific workloads](interactions_qualification.md)
against the exact published compatible provider, then settle the feature floor.
Earlier scientific/browser source results remain separate development evidence.

A frozen 1.0 candidate still needs complete release gates, the supported
platform/artifact matrix and human workflow observations. This check does not
qualify experimental Qt standalone or post-1.0 remote sessions.

## Installed experimental Interactions pair — 2026-10-02

**Done: bounded installed verification with Pandas 2. Qualification is partial.**
The working tree was copied to `/tmp/msv-interactions-installed-source-20261002`
with Git context and all tracked/untracked inputs, preserving the original
checkout. Its base is `1cf7826d4c343bb9f517f2244a4f7ca83f909c52`; versioningit,
`npm run build:runtime` and wheel construction ran sequentially in that copy.
The existing runtime-version validator passes for source and wheel. All **603
packaged Python members** match their snapshot sources; original Python sources
also match, excluding the separately generated `_version.py`.

| Artifact | Identity |
| --- | --- |
| Viewer wheel | `molsysviewer-0.23.4+69.g1cf7826d.dirty-py3-none-any.whl` |
| Viewer SHA-256 | `3edc0b5e9e9504825007b3bc850c722694bdd10125d51828405e73e0e1f9a0d2` |
| Experimental provider | `molsysmt-0.22.4+76.gdf1a298e7-cp311-abi3-linux_x86_64.whl` |
| Provider source | `df1a298e70a419a8f04562f8fb9ffaa92abb3be1` |
| Rebuilt provider SHA-256 | `fb69020f84532f1986746cacf1516e2862d5e16e2c2ee478a2fb19228d139e77` |
| Snapshot input manifest SHA-256 | `98d156dda5327e46953bbba86a65ad82edc4ccdb54c8ed3f6b5f093552aaf73b` |

Both wheels are installed into fresh temporary environments based on the prior
public-channel environment. Viewer and MolSysMT import from each environment's
own site-packages. Other dependencies are public distributions, including
ArgDigest 0.13.0, DepDigest 0.12.0, PyUnitWizard 0.27.0, SMonitor 0.18.0, NumPy
2.5.3 and RDKit 2026.03.6. `pip check` passes in both configurations. Python is
3.14.7 on Linux x86_64. The provider wheel is experimental, not a public release.
The rebuilt wheel has its own identity; the earlier wheel SHA is not reused.

### Pandas compatibility finding

With Pandas **3.0.6**, the batching selection stops after **2 passed, 1 failed**;
13 cases are unexecuted. Native cation–pi calculation reaches
`molsysmt/topology/get_substructure_matches.py:134`, where a Pandas-derived
read-only array is modified. An independent public-provider reproduction, without
Viewer or coordinates, gives the same `ValueError: assignment destination is
read-only`:

```python
import molsysmt as msm
from rdkit import Chem
from molsysmt.topology.get_substructure_matches import get_substructure_matches

source = msm.convert(Chem.MolFromSmiles('c1ccccc1.[NH4+]'),
                     to_form='molsysmt.MolSys')
get_substructure_matches(source, '[a;r6]1:[a;r6]:[a;r6]:[a;r6]:[a;r6]:[a;r6]:1')
```

Reported as **uibcdf/molsysmt#289**, linked to the consumer #140 and provider
contract audit #245. The committed provider helper at local HEAD `548afe39d`
is unchanged at this failure site. The independently dirty sibling checkout
was preserved. No private provider arrays or global Pandas settings were changed.

A separate environment with Pandas **2.3.3**, the same two wheels, NumPy 2.5.3
and RDKit 2026.03.6 passes that direct reproduction and the bounded checks below.
This is a controlled compatibility result, not a repository Pandas ceiling or a
Pandas 3 pass. The first environment and its failing evidence are retained.

| Installed selection | Result |
| --- | --- |
| `test_interactions_projection_batching.py` | 16 passed, zero skipped |
| Family API, scene lifecycle, real scientific workflows and sparse residency/H5MSM | 75 passed, zero skipped |
| Maintained installed runner, many-group selector | 1 passed; repeats an existing guard, not a 92nd distinct case |
| Origin refusal probe | Rejects a real Viewer checkout import despite matching installed distribution metadata |
| Offline packaged-runtime HTML | 6 passed: hbond, pi–pi and order-2 water bridge, initial and restored sessions |

The six exported pages contain the installed wheel's runtime. Actual Mol* state
checks compare endpoint positions (nm projection to Å mesh), participants,
occurrence/segment IDs, unique observation counts, segment counts and visibility.
All pages complete a real draw offline with WebGL2/SwiftShader, retain the
Python-session notice, and emit no page errors or version mismatch. The initial
one-off browser driver tried the hidden floating-panel Close button; after
correcting it to the actual `Panel mode (N / W)` opener, the complete selection
passes. No runtime fix was needed for that driver error. This does not certify
live calculation forms, whole core E2E, GPU throughput or other platforms.

### Maintained installed test runner

`devtools/qualify_installed_interactions.py` reuses the scientific fixtures and
pytest modules. It verifies distribution versions and all loaded Viewer/provider
module paths before and after testing. Only the fixture namespace is exposed;
scientific packages must come from site-packages. It enables installed-mode
conftest checks and retains pytest's actual exit status. Its default selection
is the five bounded modules above; use `--tests` for explicit node selectors.

From outside both checkouts, with the isolated interpreter:

```bash
CONDA_PREFIX=/tmp/msv-installed-gate-20261001 \
/tmp/msv-interactions-installed-pandas2-env-20261002/bin/python -I \
  /home/diego/repos@uibcdf/molsysviewer/devtools/qualify_installed_interactions.py \
  --source-root /tmp/msv-interactions-installed-source-20261002 \
  --expected-viewer-version 0.23.4+69.g1cf7826d.dirty \
  --expected-provider-version 0.22.4+76.gdf1a298e7 \
  --pytest-args --receptor=llm -x --junitxml=/tmp/installed-interactions.xml
```

The checks were initially run through a bounded bootstrap with the same installed
origin constraints. The maintained runner then passes the actual many-group guard
and rejects a real source import in a separate process. Fixture inputs remain
in the snapshot; library/runtime imports come from the wheels. Existing fixture
tools supply the chemistry and export flows; provider algorithms are not copied.

### Evidence and remaining gates

The [structured record](installed_interactions_20261002.json) preserves package
member hashes, environment identities, test counts/times, browser outcomes and
the official public-provider inventory. On 2026-10-02 the newest file version in
the [UIBCDF inventory](https://api.anaconda.org/package/uibcdf/molsysmt) remains
0.22.4; [GitHub releases](https://github.com/uibcdf/molsysmt/releases) agrees.
The stale package-level `latest_version` field is not used.

Local JUnit: `/tmp/msv-interactions-installed-batching-20261002.xml` (Pandas 3
failure), `/tmp/msv-interactions-installed-pandas2-batching-20261002.xml`,
`/tmp/msv-interactions-installed-public-20261002.xml` and
`/tmp/msv-interactions-installed-runner-20261002.xml`. Browser observations are
`/tmp/msv-interactions-installed-browser-20261002.json`; the corrected log is
`/tmp/msv-interactions-installed-browser-20261002-corrected.log`. The direct
provider logs retain the two Pandas outcomes. Temporary files supplement the
maintained tests, fixtures, runner and structured record.

At this initial checkpoint, next were provider fixes/review for #289 and #288,
then an exact published compatible provider, explicit Interactions feature floor,
committed candidate and installed/
artifact/core CI qualification. No whole installed Python suite or cross-platform
result is claimed here. The earlier complete source suite and unified live
Interactions browser run remain separate evidence. No product push or public
release occurred; public documentation remains last.

## Provider #288/#289 review — 2026-10-02

**Initial review:** both provider defects are closed and verified; the consumer
guard mismatch recorded here is resolved in the follow-up below. Fix `78981d6c1` bounds explicit-frame relation candidates and
uses owned, writable chemistry arrays without mutating source topology. The clean
tested commit is `396e6979f3f686b110431f18bba0d41933ce71e2`, built from scratch
(including native code) as `molsysmt-0.22.4+122.g396e6979f-cp311-abi3-linux_x86_64.whl`.
Its SHA-256 is `a075950bfc96ff6b957c0a367a7fd684a2aedc54407d1f90769db46bd2a68666`.
The Viewer artifact above is reused unchanged. The new environment is
`/tmp/msv-provider-review-pandas3-env-20261002`; Python 3.14.7, Pandas 3.0.6,
NumPy 2.5.3, RDKit 2026.03.6 and h5py 3.16.0 are installed with public base
dependencies. `pip check` passes. Earlier environments and their failures are
preserved. The [structured record](interactions_provider_review_20261002.json)
retains artifact hashes, versions, JUnit identities and raw observations.

| Check | Result |
| --- | --- |
| Original standalone SMARTS reproduction with Pandas 3 | Passes |
| Provider relevant-frame and read-only/source-chemistry guards | 15 passed |
| Viewer family, scene, scientific workflow and residency checks | 75 passed |
| Viewer projection batching | 15 passed, 1 failed, no skips; final selector run separately after `-x` |
| Offline installed-runtime geometry before/after session restore | Six passed in real Mol*, WebGL2/SwiftShader |
| Eight query patterns versus independent membership reference | All results match |

The failing guard is
`test_split_periodic_group_is_refused_before_its_center_is_calculated`. Its public
translation now invalidates the stored analysis before rendering. There is no
evaluated occurrence to project, so its expectation of geometry calls fails.
Viewer correctly reports `unevaluated`. A separate installed probe intentionally
reattaches the old observation and verifies `unsupported`, zero drawn segments
and one skipped occurrence for the malformed periodic ring. Adapt the fixture
and add a distinct invalidation assertion next; no library or test source changed
in this review. The 90 passing Viewer cases and failing case are reported honestly
rather than presenting the selection as green.

For 62 atoms, 5,000 structures and 22,495 changing-relation occurrences, warm
three-call medians with the old/new installed providers are:

| Explicit-frame query | Old ms | New ms |
| --- | ---: | ---: |
| incident | 3.585 | 0.456 |
| internal | 667.508 | 0.508 |
| cross | 330.242 | 0.407 |
| between | 3.451 | 0.678 |

The results retain occurrence identities, coverage and participant semantics.
Provider guards cover nonconsecutive/duplicated requested structures, reused and
changing relations, chained queries and parallel occurrences. This is a bounded
one-host observation, not a performance threshold. Queries over the complete
trajectory still incur global filtering cost; the change does not promise
constant-time arbitrary atom queries or selective file-backed reads.

Reproduce from outside the checkout using the maintained installed runner and
the preserved source snapshot:

```bash
CONDA_PREFIX=/tmp/msv-installed-gate-20261001 \
  /tmp/msv-provider-review-pandas3-env-20261002/bin/python -I \
  /home/diego/repos@uibcdf/molsysviewer/devtools/qualify_installed_interactions.py \
  --source-root /tmp/msv-interactions-installed-source-20261002 \
  --expected-viewer-version 0.23.4+69.g1cf7826d.dirty \
  --expected-provider-version 0.22.4+122.g396e6979f \
  --pytest-args --receptor=llm -x
```

The default selection currently exposes the known guard mismatch. The runner
checks scientific module origins both before and after pytest. The provider's
15 guards were also run through this runner with absolute selectors into the
clean provider tests. The browser uses freshly exported pages and checks actual
mesh endpoints, nm-to-Å conversion, participants, occurrence/segment identities,
summaries and visibility, with no page errors or version mismatch.

Next: adapt the guard, obtain the compatible public provider, declare its proven
feature floor and qualify a committed exact candidate through installed/core CI.
The [latest GitHub release](https://github.com/uibcdf/molsysmt/releases/tag/0.22.4)
is still 0.22.4 as checked in this review. No full-suite, hosted, cross-platform,
GPU-throughput, product-push or release qualification is claimed. The new public
`Interactions.to_page()` is a separate integration opportunity; it is not adopted
by this review. Public documentation remains last.

## Provider invalidation guards and installed follow-up — 2026-10-02

**Done:** the malformed-periodic-group guard deliberately reattaches its original
observation after changing geometry. Three additional real pi–pi cases edit
structures `[0]`, `[2]` and `[2, 0]` through public MolSysMT translation. They check
coordinates, frame-local invalidation, detached original-result integrity,
evaluated-empty frames, surviving geometry/chemistry, current occurrence identifiers
and refreshed cached display revisions. All 19 projection/invalidation cases pass,
and the final five-module installed scientific selection passes **94 cases, no
skips**, with the same Viewer/provider artifacts above and NumPy 2.5.3 / Pandas
3.0.6. Production Python members still match the Viewer wheel (603 members, only
generated `_version.py` excluded). No library implementation change was necessary.

Scientific fixture tools now respect `MOLSYSVIEWER_TEST_INSTALLED=1` instead of
prepending the checkout. The installed verifier identifies one distribution in
the interpreter's own site-packages and separately checks every loaded scientific
module path. Three import tests pass, including competing real metadata records
and an actual source-module import that must be rejected.

The complete `tests/` selection was executed **once** from `/tmp` in installed
mode: **2,482 passed, 9 failed, 78 errors, 27 skipped**, exit 1 in 380.10 seconds.
The inventory assumed scientific source lived under the checkout, four source
checks assumed its current directory, and the bounded scientific environment
lacked build, imageio and MDTraj. Final ambient metadata discovery also selected
the inherited public provider record; the final origin check was not completed
by that failed run. This full attempt is preserved, not described as green.

Corrections resolve inventory source/digester paths from the imported package,
retain portable package-relative source names, and anchor source checks to their
test checkout. A separate development environment has public build, imageio,
MDTraj and PyTables dependencies. It uses NumPy 2.4.6 to satisfy MDTraj, while the
scientific qualification retains NumPy 2.5.3. Both have Python 3.14 / Pandas 3
and the exact same Viewer/provider wheels; `pip check` passes. The correction
selection and bounded README completion verify **309 unique passing cases and
one skip** (imageio's absence branch, because it is installed). One README case
is repeated; no second full suite is run. These are scoped corrections, not a
whole-suite or optional Qt/GPU certification.

Artifact/environment identities, initial failed attempts, all JUnit digests and
current source hashes are in [the durable follow-up](interactions_invalidation_20261002.json).
The earlier browser/provider-review records remain unchanged. The remote README/
suite-guide commit was integrated by fast-forward to `f2b14872`; a backup and hash/
status comparisons preserve all 326 local files. No product commit or push occurred.

Reproduce the current scientific selection with the earlier command, changing
`--source-root` to `/home/diego/repos@uibcdf/molsysviewer` so it includes the
corrected guards. Next: compatible published provider, proven feature floor,
reviewed product commit and exact-candidate installed/core/hosted qualification.
Public documentation remains last; #140 stays partial.

## Integrated design candidate — 2026-10-03

**Prepared locally; not a frozen or fully passing release candidate.** Main
was synchronized by fast-forward to `3b475639fdfa2a359b830bdf3314b81b5f1f3830`.
The preserved product work was copied into an isolated Git-context checkout.
Versioningit wrote its version before the runtime build completed and the wheel
was built. The maintained source/wheel validator passes; the initial runtime
with a fallback version was rejected before packaging.

The artifact is `molsysviewer-0.23.4+71.g3b475639.dirty-py3-none-any.whl`,
SHA-256 `9ac697dbabaa840ca1a3fc37d927fa03631822dab63dfa90ac44998897edd4ae`.
All 608 packaged Python files match the product working tree. This is an
uncommitted development snapshot; its `.dirty` version is not release identity.
The complete JavaScript unit selection passes 314 tests, and TypeScript passes.

The public environment `/tmp/msv-installed-gate-20261001` was reused with this
Viewer wheel; it was not recreated. Published MolSysMT 0.22.4 supports ordinary
viewing, with 13 design guards and 114 public workflow cases passing. The
unsupported Interactions backend is refused explicitly. The isolated scientific
environment `/tmp/msv-integrated-scientific-env-20261003` installs the experimental
provider `0.22.4+122.g396e6979f`; 23 design/Interactions cases, 68 collection
corrections and four isolated CLI/import guards pass. Package origins are checked
before and after pytest. These environments qualify installed artifacts only.

The scientific environment's once-run full regression returned **2,583 passed,
15 failed, 44 errors and 25 skipped**, exit 1. Most failures record exhausted
disk space during HTML/H5MSM writes or subsequent temporary-directory setup.
The qualification copy also omitted a linked sandbox design HTML file and had
a stale generated queue index; both are restored. A native family-CLI exit of
-11 occurred during that run; its cause is unproven. The subsequent installed
static/import selection passes 195 cases, including that CLI. No second full
run or passing full-regression result is claimed.

At the principal maintainer's direction, development now runs explicitly in
`molsyssuite@uibcdf_3.14` (Python 3.14.7), using the editable Viewer and MolSysMT
checkouts. The provider HEAD is `bd65456e0ca994f4a92800bda5d23325c999a673`,
with unrelated local work preserved. Its editable version metadata is stale;
the actual source HEAD and imported origins, rather than metadata alone,
identify these checks. Thirteen design guards and the 179-case disk-affected
module selection pass; three skips cover installed-only guards and imageio's
absence branch. This is source development evidence, separate from the wheel
selections above.

All 17 real calculation forms pass in Chrome/SwiftShader, including calculation
and rendering. The full core follow-up was interrupted at the principal
maintainer's request after 19 suites passed, during Interactions. It used the existing
`E2E_SUITE_TIMEOUT_MS=600000` local override: the forms alone took about six
minutes, so this does not certify the default 180-second suite budget. The
browser bridges prepend source checkouts; those results must not be described
as strict installed-wheel qualification. The executor sandbox additionally
blocks EOF delivery from Node to a Python child's stdin: a bounded minimal
`spawnSync` reproduction times out inside and passes outside. Browser validation
runs outside that restriction, without `E2E_ALLOW_SKIP`.

Artifact identities, exact counts, failed attempts, module origins, source
preservation and logs are retained in
[the integration evidence](integration_qualification_20261003.json).
Compatible published scientific dependencies, the reviewed committed candidate,
hosted/default-budget CI and the supported native artifact matrix remain open.
Public documentation remains last. The proposed multiple-source API in #151
still requires a design decision; no `load_many` API is implemented.

## Loading and provider-result completion — 2026-10-03

**Local qualification completed; compatible publication and a frozen candidate
remain.** The new development snapshot `0.23.4+76.g924da3a3.dirty`, hash
`8351d227c9b65b5b96e1555a14aa3056b513c391807cd9594956cf92845fe260`, passes the
once-run installed regression: **2,791 passed, 25 skipped** in 579.31 s. Both
scientific libraries import from the isolated environment; the maintained runner
checks their installed origins before and after pytest. This full result precedes
the final provider-result verification in #155.

That later box-verified artifact retains its own bytes/hash:
`24f9adf4235d4d57250d508e48d172f1f4a8c02a1e6fcca1a3c1b4e58251d190`. All 614
packaged Python sources match the latest product tree; its runtime-version
validator passes. It passes **68 installed loading/cell cases** with experimental
provider `0.22.4+122.g396e6979f`, and the real published-provider guard verifies
that ignored cell initialization is an explicit error preserving the session.
There is no second complete installed run. Dirty development versions are not
immutable release identity; hashes distinguish these retained snapshots.

The source regression after #155 passes **2,800 tests, 23 skipped** in 489.46 s
in `molsyssuite@uibcdf_3.14`. All **39 core browser suites** pass under the normal
180-second deadline, using real Chrome/WebGL2/SwiftShader with source bridges.
No remote, native-GPU, visible Qt, skipped lane or hosted frozen-candidate result
is inferred. The editable provider has repaired partial extraction and H5MSM
composition (#307/#309); its six positive selector combinations are source
evidence, separate from the older installed provider's atomic refusal guards.

Published MolSysMT 0.22.4 does not qualify Interactions or cell initialization.
The published loading selection passes 38 cases and then fails its direct-provider
cell contract; the subsequent safe-error guard does not relabel that attempt
green. The initial clone/versioning race, missing OpenMM engine and timeout
attempts remain as refuted evidence. Product commits/pushes, compatible published
provider and exact-candidate matrix remain open. Public documentation stays last.
See [the completion evidence](integration_completion_20261003.json).
