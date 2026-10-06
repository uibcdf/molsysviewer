---
summary: Box initialization reports success when the provider leaves the cell absent
issue: uibcdf/molsysviewer#155
status: partial
opened: 2026-10-03
closed:
severity: medium
verification: reproduced
area: [api, box, dependencies]
guard: tests/test_box_assignment.py::test_provider_box_initialization_is_verified
normative:
blocked_by: []
supersedes: []
---

# Box initialization reports success when the provider leaves the cell absent

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
