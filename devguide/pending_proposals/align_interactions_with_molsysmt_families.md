---
summary: Align Viewer interactions with the nine implemented MolSysMT families
issue: uibcdf/molsysviewer#140
status: partial
opened: 2026-10-01
closed:
verification: measured
area: [interactions, scientific-api, studio]
guard: tests/test_interaction_families.py
normative: devguide/interactions_pre_1_0_plan.md
blocked_by: []
supersedes: []
---

# Align Viewer interactions with the nine implemented MolSysMT families

**Reported:** 2026-10-01, principal-maintainer review of the expanded experimental
provider contract coordinated in uibcdf/molsysmt#250.

## What

MolSysMT now implements nine experimental families: hbonds, disulfides, ionic,
pi_pi, cation_pi, halogen_bonds, hydrophobic, metal_coordination and water_bridges.
The Viewer working tree previously calculated and rendered only Buch hydrogen
bonds and disulfide candidates. Extend its public wrappers and explicitly
supported projections while retaining the complete sparse scientific result.

After opening the issue, the maintainer requested an explicit family namespace
instead of a generic public `compute(kind, parameters=...)`. The accepted API is:

```python
view.interactions.hbonds.get_hbonds(name="hydrogen_bonds")
view.interactions.hbonds.get_buch_hbonds(name="buch", distance_threshold="0.3 nm")
view.interactions.ionic.get_ionic_interactions(name="ionic", distance_threshold="0.4 nm")
view.interactions.add("hydrogen_bonds", tag="hb")
```

The wrapper binds the view's system, defaults to its visible structure, returns
and stores a complete named analysis, and has an explicit signature, ArgDigest
and `skip_digestion=False`. Scientific method/profile defaults remain those of
the corresponding provider function. Explicit calculation does not create a
visual set or edit topology. Generic orchestration is private. The original
Viewer `compute_hbonds` and `compute_disulfide_candidates` routes have been
removed. Their tests, qualification tools, benchmark and executable documentation
examples now call `hbonds.get_buch_hbonds` and
`disulfides.get_disulfide_candidates`, preserving the scientific criteria.

## How

Use public provider detectors and geometry helpers; never import private
scientific algorithms. Studio dispatches its selected family through the same
public wrapper as Python. Preserve participant membership and roles, occurrence
identity, scope, measurements and units, provenance, evidence and attribution.

Compound charge centers and rings receive explicitly identified centroid guides;
the guide's length is not a reinterpretation of an ionic minimum-atom distance.
Halogen bonds retain all four roles but draw halogen–acceptor. Metal coordination
remains a geometric candidate. Water bridges retain six/nine directed roles and
one occurrence identifier while drawing two/three hydrogen–acceptor segments.
Summaries distinguish observed occurrences, supported occurrences and segments.
Periodic translations use provider images and row-vector boxes. Compound groups
split across a periodic boundary are refused, not silently reconstructed.

Qualification uses a clean detached provider commit
`df1a298e70a419a8f04562f8fb9ffaa92abb3be1`, built as an actual wheel and installed
under `/tmp/msv-nine-family-provider-installed`; the canonical editable provider
and its unrelated in-progress geometry changes are preserved. This is experimental
installed-source evidence, not qualification of a published dependency release.

## Why

Users can discover an operation from its family and inspect its scientific
parameters before calling it. A result with several participants cannot be
flattened into an arbitrary atom pair without losing scientific meaning.
MolSysMT's `n_interactions` still counts occurrences: its meaning has not changed.

## What was refuted

The proposed generic public dispatcher with an opaque parameter dictionary was
replaced by explicit family wrappers at the maintainer's request. The issue's
opening prose retains that earlier proposal; the settled design is maintained
here and will be stated in the closure, following the reporting protocol.

Provider source smoke evidence for hydrogen bonds/disulfides does not qualify
seven new Viewer projections or the currently published MolSysMT 0.22.4 package.
Additional provider families do not automatically become mandatory MolSysMT 1.0
criteria. Consumer geometry and actual browser validation remain Viewer-owned.

## Resolution

Source integration is qualified, with publication still pending. The new 25-case regression module
passes against the isolated installed experimental provider. It checks all nine
families and both water orders with real detectors, nonconsecutive frame/atom
queries, an independent role/centroid/image geometry oracle, H5MSM and periodic
session fidelity, explicit digested signatures and Studio delegation. The 70
existing API/scene/public-inventory tests also pass. Runtime build and targeted
Ruff checks pass. The initial family integration inventory counted 711 digested
callables with explicit bypasses and no missing argument digesters; the capability
report and inventory baseline have been regenerated.

The full Python suite was executed once: **2,505 passed, 23 failed, 23 skipped**.
One failure was the generated capability report; the other 22 were sandbox
restrictions on local sockets or Chromium/Qt launches. After diagnosing the
captured permission failures and regenerating the report, a bounded rerun of
the affected files plus the two Qt selectors outside the sandbox passes
**56 tests, 1 skipped**. The skip requires an explicitly qualified remote GPU
environment and does not qualify that post-1.0 preview. This is a full run plus
a targeted correction, not a second green full-suite invocation.

The expanded `interactions-subpanel.e2e.ts` passes against real Mol*. Existing
creation/import/filter/inspection/playback/picking cases remain covered. Ten
real calculated fixtures cover nine families and both water orders, before and
after scientific session restoration (20 scenes); all seven newer families
also exercise observed periodic images. Mesh endpoint units, complete roles,
occurrence/segment identities, centroid labels, separate display counts and
the nine-family Studio chooser are checked. Distinct directed paths may share
a water mediator: the guard checks two/three segments **per occurrence**, not
an assumed single occurrence per system.

The provider wheel is `molsysmt-0.22.4+76.gdf1a298e7-cp311-abi3-linux_x86_64.whl`,
SHA-256 `96ffd86f526360e26b220647eb8076ef3d6faf43f74cc5e46353f1045966fa6d`.
The scientific qualification imports it from the isolated installation,
without altering the sibling editable checkout. No source change in this
product block has been committed or pushed yet. A compatible published
dependency and publication CI for the whole existing product working tree
remain necessary; the issue stays partial rather than claiming release readiness.
After recording this design and its evidence, the reporting-protocol and
capability-audit selection passes **355 tests**; generated indexes and
`git diff --check` also pass. The board carries `proposal`, `partial` and
`component:molsysmt`; its opening prose was not rewritten.

### Family-only calculation cleanup — 2026-10-01

**Done in the working tree:** removed the two manager-level calculation methods.
Existing Buch consumers now call `view.interactions.hbonds.get_buch_hbonds`;
disulfide consumers call `view.interactions.disulfides.get_disulfide_candidates`.
This includes API tests, real scientific qualification, the detector benchmark,
the published-provider compatibility probe and executable documentation examples.
The broader documentation pass remains deferred. Studio already delegates to
these getters and needs no dispatch change for this cleanup.

The regression guard in `tests/test_interaction_families.py` rejects all three
public `compute` names. Migrated API tests retain current-frame defaults,
nonconsecutive axes, named-analysis atomicity, periodic images and topology
preservation. ArgDigest rejects an attempted `method` override on the explicit
Buch getter with `UnknownArgumentError`; that contract is checked explicitly.

The specific selection passes **77 tests**, including real detector and all
three persistence routes. Its JUnit evidence is
`/tmp/msv-family-api-cleanup-targeted.xml`. Ruff and notebook JSON validation
pass. Regenerated inventory and capability reports now record **709 public
callables, all digested**, explicit bypasses, 433 argument digesters and zero
missing digesters or undigested exemptions.

The migrated probe against public MolSysMT 0.22.4 passes using its isolated
installed package at `/tmp/msv-installed-gate-20261001/lib/python3.14/site-packages`:
ordinary views work, Studio reports the unavailable experimental backend, and
the family getter refuses calculation explicitly. Experimental success still
uses the isolated provider wheel pinned above; published-provider qualification
and source publication remain pending. This report keeps #140 partial.

The cleanup's full Python suite was run once outside the sandbox and passes:
**2,528 passed, 23 skipped, zero failures/errors** in 351.96 seconds. Its
independent JUnit record is `/tmp/msv-family-api-cleanup-full.xml`. This includes
the generated capability/reporting guards and the previously sandbox-limited
cases. Skips retain their declared conditions and do not qualify a remote GPU
host or the manual standalone certification. This complete green run supersedes
the earlier family integration's full-run-plus-targeted-correction evidence for
the current Python working tree.

### Typed Studio calculation controls — 2026-10-02

**Done in the working tree:** replaced the scientific parameter JSON editor
with family-specific controls in the native Interactions panel. The reusable
`interaction-calculation-controls.ts` module owns field definitions, quantity
serialization, unit conversion and validation of required entries. Scientific
recognition, cutoff defaults and acceptance remain in the public family getters.

Hydrogen bonds offer explicit Buch, Luzard–Chandler, Baker–Hubbard,
Wernet–Nilsson and automatic donor–acceptor criteria. Ring criteria select their
named profiles and expose only compatible angle, offset and planarity controls;
fitted-plane proposals require their explicit limits. Halogen bonds expose two
angular intervals, disulfides offer residue names, ionic contacts require a
distance, and water paths offer one/two mediator waters. Length and angular
units are explicit. Blank optional fields do not override scientific defaults;
a unit change converts the entered physical magnitude. Drafts are isolated by
family/criterion and preserved across summary updates. Advanced chemical-state,
explicit-site and execution-limit options remain in the Python API.

Browser qualification found and corrected two defects. First, BasePanel's
focus restoration matched a reused distance-field identifier after a criterion
or unit change, showing an old value over a different draft. Scientific input
identity now includes family, criterion, field and unit, before the ordinary
field-selector attribute. The browser guard changes criterion, converts 0.4 nm
to 4 Å and updates summaries without changing that value. Second, Viewer's
angular-interval digester accepted a pair of angular endpoints but returned a
tuple of quantities. The public provider correctly requires one vector quantity.
The reusable digester now extracts each endpoint explicitly in radians and
constructs/standardizes that vector, rejecting absent or incompatible endpoints.
Real detector guards cover mixed endpoint units under radians and degrees
standardization, with coordinates standardized to angstroms.

The 16 pure control tests pass; the complete JavaScript unit suite was run once
and passes **312 tests**, before the browser focus correction. Its retained log
is `/tmp/msv-interaction-controls-js-full.log`. Runtime and harness were rebuilt
after that correction; targeted Ruff checks pass. The initial complete browser
run completed the existing action/import/filter/picking/geometry/session cases,
including the 20 family scenes, then failed at the new focus guard. After its
correction, the calculation-only run passed its first 12 cases and found the
angular-interval boundary defect. Following that fix, a bounded selection of the
remaining five cases passes. Thus all **17 real form calculations** are verified
across these scoped runs; this is not a claim of another entirely green unified
E2E invocation. The real screenshot
`/tmp/molsysviewer-interactions-calculation-controls.png` was inspected for layout.

The Python target passes **30 tests**. The full Python suite was run once outside
the sandbox after fixing the vector boundary: **2,533 passed, 23 skipped, zero
failures/errors**, in 322.31 seconds. Independent JUnit evidence is
`/tmp/msv-interactions-controls-python-targeted.xml` and
`/tmp/msv-interactions-controls-python-full.xml`. The skips retain their declared
external/GPU/platform conditions. The isolated installed experimental provider
remains the pinned wheel recorded above. #140 stays partial: publication with a
compatible public provider and exact-candidate whole-product CI remain pending.

### Storage findings

Direct public H5MSM layer reads retain an analysis's evaluated-frame order;
full `msm.convert` can remap the system and canonicalize that order, producing a
new analysis identity. The layer reader is the guard for exact storage identity.

Pi–pi calculations intern both parallel and edge-to-face evidence labels even
when only one occurs. H5MSM drops unused labels and can renumber codes. The Viewer
signature now hashes a canonical used-label table and remapped codes in bounded
numeric chunks. Unused interning details do not invalidate saved scientific
references; changed evidence on an actual observation still changes identity.

Modern H-bond detection correctly refuses the old peptide demo's missing bond
chemistry columns. Its positive test uses real RDKit chemical topology; the
Viewer does not infer those missing scientific declarations or change criteria
automatically.

### Expanded scale measurements — 2026-10-02

Done: the existing residency benchmark now covers four participant layouts,
recurring/changing relations and three atom/structure scales in 24 fresh
processes. All 624 query-pattern checks match a direct membership reference;
two visual sets share one analysis and preserve occurrence/segment identity.
Public H5MSM 0.5 round trips retain the scientific columns and filtered IDs.
The detector benchmark also passes the nine real families and both water orders:
the actual 5,000-frame Buch trajectory, the 55,628-atom disulfide protein and
bounded repeated analytical conformations for the other families. The 19 focused
regressions pass against the clean installed wheel recorded above.

The scale data expose two distinct tasks. Compound projection spends
4.15–4.23 seconds preparing 1,000 two-group observations, before browser/GPU
work; uibcdf/molsysviewer#141 resolved that dispatch cost through the existing
public geometry operation (see the correction below). A direct-provider probe confirms internal/cross frame
queries can test relations from the whole trajectory; uibcdf/molsysmt#288 owns
that query limitation. Preserve the public provider boundary instead of copying
its algorithms. This consumer report remains partial; measurement is complete
but scale qualification and publication are not. Full measurements, provenance,
limits and the bounded in-memory 1.0 decision are in
`devguide/interactions_performance.md` and
`devguide/benchmarks/interactions_scale_20261002.json`.

The single complete-source regression after the focused pass returns
**2,556 passed, 23 skipped, zero failures/errors**, exit 0 in 337.67 seconds,
outside the sandbox with the isolated installed provider and published
pytest-receptor 1.2.0. JUnit/log evidence is
`/tmp/msv-interactions-residency-full.xml` and
`/tmp/msv-interactions-residency-full.log`; the focused 19-test evidence is
`/tmp/msv-interactions-residency-targeted.xml`. Skips retain the prior external
browser/GPU, optional add-on, imageio, platform and template limits. There is
no new browser/GPU qualification in this measurement block. Ruff and diff
whitespace checks pass; generated queue indexes have been refreshed for #141.

### Compound projection correction — 2026-10-02

Done: uibcdf/molsysviewer#141 uses bounded current-frame batches through public
provider geometry. The four repeated scale cases preserve all counts/identities;
1,000 compound observations now prepare in 281–291 ms instead of 4.15–4.23 seconds.
The 16 new real-call guards pass, and an isolated restoration of scalar-per-group
calls fails the guard as expected. The 71 related checks pass. The once-run
complete Python suite returns **2,572 passed, 23 skipped, zero failures/errors**,
exit 0 in 428.46 seconds. The complete real Mol* Interactions subpanel E2E now
passes in one invocation, including periodic scientific geometry, all 20 family
scenes and all 17 calculation forms. Evidence and source identities are in
`devguide/benchmarks/interactions_batching_20261002.json`; the maintained
performance record and archived #141 report describe the limits.

This resolves the local dispatch defect, not the parent qualification. At that
batching checkpoint, the provider query review (uibcdf/molsysmt#288) was still
pending; it is completed below. The product working tree still needs compatible
published-provider and exact-candidate
artifact/CI qualification. No product commit or push is claimed. The browser
run uses headless SwiftShader and is not a throughput or full core-lane result.

### Installed pair qualification — 2026-10-02

Done: a fresh Viewer wheel includes the current product code and rebuilt runtime,
and its 603 packaged Python members match the isolated source snapshot. Both
Viewer and experimental MolSysMT are installed into temporary environments,
without scientific checkout imports. Pandas 2.3.3 passes 91 distinct bounded
scientific/projection/storage checks and six offline packaged-runtime Mol*
geometry cases before/after session restoration. The maintained installed runner
passes its real many-group selector and rejects a real source-checkout import.

Qualification exposed a separate provider compatibility defect: Pandas 3.0.6
causes the SMARTS helper to modify a read-only array; cation–pi fails, and a
minimal public MolSysMT reproduction without Viewer gives the same error.
Reported as uibcdf/molsysmt#289, retaining the failed 2-pass/1-fail selection and
13 unexecuted cases. No Viewer workaround, global setting change or dependency
ceiling was added. See `devguide/installed_artifact_qualification.md` and
`devguide/installed_interactions_20261002.json` for exact wheel/dependency
identities and limits.

#140 stays partial. At that initial installed-pair checkpoint, provider #288
and #289 and compatible published-provider/candidate qualification remained open.
The newest official provider file/release version is still 0.22.4. The dirty
sibling checkout and unrelated Viewer product work are preserved; no product
commit/push or full installed-suite/platform certification is claimed.

### Provider #288/#289 review — 2026-10-02

Done: both provider issues are closed at `78981d6c1`. Review and consumer checks
use a freshly compiled wheel from clean committed `396e6979f`, version
`0.22.4+122.g396e6979f`, paired with the same Viewer wheel above. Pandas 3.0.6,
NumPy 2.5.3 and Python 3.14.7 are retained. SMARTS matching now succeeds without
a Viewer workaround; 15 relevant provider guards pass against installed code.
The 75 family/scene/residency checks and 15 of 16 batching checks pass; six
offline packaged-runtime geometry cases also pass. All scientific imports are
verified under site-packages. See [the follow-up](../installed_artifact_qualification.md#provider-288289-review--2026-10-02)
and [structured evidence](../interactions_provider_review_20261002.json).

One existing batching guard fails because the new provider invalidates analyses
when its public coordinate setter changes geometry. It calculates a ring contact
and then translates one atom, leaving the frame unevaluated before its projection
assertions. An independent real-provider probe verifies both correct unevaluated
display and refusal of malformed periodic groups when the old observation is
deliberately reattached. Adapt that fixture and add a separate invalidation
assertion before claiming a green installed selection; that adaptation is now
completed in the follow-up below. No library/test source was changed in the initial
review. This is consumer test integration work, not grounds
to reopen either resolved provider defect.

Explicit-frame internal/cross queries now inspect relevant relations first.
On the same 22,495-occurrence input, indicative medians improve from 667.51 to
0.51 ms and 330.24 to 0.41 ms, respectively; eight query patterns retain the
independent reference results. Whole-trajectory query cost is not resolved by
this scope. #140 remains partial for the guard adaptation, compatible published
provider and exact-candidate qualification. At that review the latest GitHub release is still
0.22.4; no new public version floor, product commit or push is claimed.

### Provider invalidation and installed verification — 2026-10-02

Done: the periodic-group fixture reattaches the original malformed observation
after editing, and three real pi–pi cases separately check frame-local provider
invalidation and cached display updates. Edits can reassign occurrence identifiers
in a new analysis; surviving links retain scientific content/geometry and use
the current result's identifiers. The final installed scientific selection passes
**94 cases, no skips**, with Pandas 3.0.6 / NumPy 2.5.3 and the same artifact pair
as above. The three installed import guards pass. Scientific fixture tools preserve
installed discovery; the verifier selects its own distribution metadata and checks
every loaded scientific module, rejecting actual source-module imports.

The single full installed attempt returns **2,482 passed, 9 failed, 78 errors,
27 skipped**, exit 1 in 380.10 seconds. Its audit tools assumed checkout source
paths, four source checks assumed the current directory, and build/imageio/MDTraj
were absent. Final ambient metadata discovery returned an inherited public record.
Corrected audit/source paths and a separate public development environment verify
**309 unique passing cases, one skip**; the README completion repeats one passing
case, and no second full run is claimed. The development environment satisfies
MDTraj with NumPy 2.4.6/PyTables; scientific qualification retains 2.5.3. See
[the installed follow-up](../installed_artifact_qualification.md#provider-invalidation-guards-and-installed-follow-up--2026-10-02)
and [structured evidence](../interactions_invalidation_20261002.json).

No production Python change was needed: the 603 wheel members still match source
apart from generated version metadata. Remote README/suite guidance was integrated
by fast-forward to `f2b14872`, preserving all 326 local file hashes and worktree
status. #140 remains partial for compatible public dependencies and exact-candidate
installed/core/hosted qualification. No product commit/push or release is claimed;
public documentation remains last.
