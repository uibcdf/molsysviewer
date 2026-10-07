---
summary: Box initialization reports success when the provider leaves the cell absent
issue: uibcdf/molsysviewer#155
status: resolved
opened: 2026-10-03
closed: 2026-10-07
severity: medium
verification: reproduced
area: [api, box, dependencies]
guard: tests/test_box_assignment.py::test_provider_box_initialization_is_verified
normative:
blocked_by: []
supersedes: []
---

# Box initialization reports success when the provider leaves the cell absent

**Resolved — 2026-10-07:** the published Viewer 0.24.0 / MolSysMT 0.23.0
pair passes all 44 real box-assignment guards. The public release/16-cell blocker
is complete. The older 0.22.4 silent no-op reproduction and compatibility-refusal
observation retain their historical scope.

**Current qualification — 2026-10-06:** implementation is committed and
integrated in Viewer 0.24.0 build 1 with MolSysMT 0.23.0 ABI3 build 0. All
sixteen installed staging cells and 39 hosted core browser suites pass;
canonical-source Python 3.14 integration passes on all three native hosts,
with 25 documented notebooks passing on Linux. This report remains partial
for its public-provider/release qualification; staging evidence does not
close that gate. See the [current handoff](../checkpoints.md#resume-in-one-page)
and [exact candidate receipt](../stabilization_024_preparation_20261006.json).
Earlier dated sections retain their original scope.

**Reported:** 2026-10-03, installed qualification with published MolSysMT 0.22.4.

## What

```python
view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0])
view.set_box(None)
view.set_box(puw.quantity(np.eye(3) * 5, "nm"))
assert view.molsys.structures.box is not None  # fails; no error was raised
```

The installed Viewer snapshot `0.23.4+76.g924da3a3.dirty` returns without error,
although the native box and public `msm.get(..., box=True)` both remain absent.
The independently installed experimental provider supports the operation. The
published-provider composite selection first passes 38 cases, then fails the
box-initialization contract. Evidence:
`/tmp/msv-public-box-probe-cleared-20261003.log` and
`/tmp/msv-loading-installed-published-provider-normal-20261003.log`.

## How

`molsysviewer/viewer/scene.py:SceneMixin.set_box` calls public `msm.set` and
publishes the edit without verifying its result. The old provider can ignore
initializing an absent cell. Verification must use public `msm.get`, compare
shape and unit-converted values, and refuse a no-op before scene publication or
analysis invalidation. Preserve the previous cell on a mismatched result.

## Why

The base dependency floor permits this provider. A successful public edit must
mean the scientific data changed as requested; an unsupported operation needs
an explicit diagnostic. This does not make the old provider support the new
cell contract, or qualify it for Interactions.

## What was refuted

The first isolated probe assumed pentalanine initially had no box and failed its
setup assertion. Removing its actual cell explicitly reproduces the defect.
Direct public `msm.set`/`msm.get` independently confirms the ignored assignment;
it is not caused by the scene-rebuild path. No setter is mocked or provider code
forked. The initial GitHub GraphQL creation received HTTP 503; a REST check
confirmed no issue existed before the successful REST creation of #155.

## Resolution

The public edit now verifies the stored box and restores the previous cell on a
mismatched result before raising a compatibility diagnostic. Qualification passes with
both real installed providers: the public 0.22.4 guard verifies the explicit
error and complete preservation; the experimental artifact passes 68 loading/
cell checks. The once-run source regression after this correction passes 2,800
tests, with 23 skipped. The latest wheel hash is
`24f9adf4235d4d57250d508e48d172f1f4a8c02a1e6fcca1a3c1b4e58251d190`.
Product publication remains, so the issue stays partial. The guard probes the
real provider capability and verifies either the accepted scientific cell or
the explicit error plus unchanged system, scene, sources and message journal.


## Public qualification and closure — 2026-10-07

SceneMixin.set_box and the regression module match the published Viewer producer
`1a4c97a5` byte for byte. The public setter verifies the actual stored cell through
public msm.get with dimensions and unit-converted values; a mismatch restores the
previous cell and raises before scene publication or analysis invalidation.
Current Viewer requires MolSysMT >=0.23.0; old-provider compatibility observations
remain evidence of the earlier guard work, not a current supported-version claim.

All 44 box-assignment cases pass in the original Viewer 0.24.0 files promoted
unchanged with MolSysMT 0.23.0, using isolated scientific imports checked before
and after collection. The named capability guard explicitly clears the real cell,
probes the real provider and confirms initialization matches the requested cell in
nm. The current provider takes the supported branch; this fresh run does not claim
to exercise the historical unsupported branch or simulate a silent no-op.

Additional cases verify per-structure edits and selective analysis invalidation,
coordinate/source/region preservation, box removal and graphical box refresh,
H5MSM and Structures sources, explicit time units, refusal before mutation with
and without digestion, and copy/extraction/session preservation. The conditional
guard retains explicit error plus unchanged system/state/sources/message journal
assertions for a genuinely incapable provider; earlier real 0.22.4 results retain
that branch's prior evidence without a mock or provider fork.

Public-URL pair `37587631519` passes sixteen installed cells. Existing exact-source
pair `37685753081` passes all three Python 3.14 hosts, with Linux core and notebooks.
No new production change is needed to close the publication blocker. The separate
local full-suite/experimental Qt failures stay recorded in the styles/plot receipt.

Guard: `tests/test_box_assignment.py::test_provider_box_initialization_is_verified`.
[Artifact identities and final evidence](../remaining_partial_closure_20261007.json).
Final 1.0 qualification remains separate; published tags and files are unchanged.
