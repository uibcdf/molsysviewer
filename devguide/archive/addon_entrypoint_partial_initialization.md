---
summary: Entry-point discovery rejects a partially initialized addon importing public specs
issue: uibcdf/molsysviewer#233
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: medium
verification: reproduced
area: [addons, imports]
guard: tests/test_addon_entrypoint_import_order.py
normative:
blocked_by: []
supersedes: []
---

# Discovery during circular addon import

**Reported:** uibcdf/pharmacophoremt#56, public Viewer 0.24.0 source-overlay
diagnostic on Python 3.14.8/Linux. This is not a current installed-package test.

## What

Importing an entry-point module that imports the documented root AddonSpec
exports triggers discovery while the addon has not yet declared its contract.
Discovery records a false invalid-contract failure; explicit rediscovery after
import completes recovers the addon. The upstream report includes both outcomes.

## How

`GlobalAddonsRegistry.discover` checks partially initialized known modules, but
the entry-point branch still calls `load()` and validates its result without
that check. Current source inspection confirms this seam remains distinct.
Qualification must retain real invalid-contract errors and lifecycle discovery;
merely suppressing every load failure would conceal broken addons.

## Why

Generic addon authors may import public root specs. PharmacophoreMT now avoids
the cycle through public `molsysviewer.addons` imports and fresh-process checks,
so its current consumer smoke is not blocked. The generic host contract still
needs a fix and an import-order guard before the final freeze.

## What was refuted

A consumer workaround does not establish that the host discovery defect is
resolved. Earlier upstream source overlays do not qualify our current artifact.

## Current source reproduction — 2026-10-13

A fresh Python 3.14 process with a real importlib.metadata entry point reproduces
the failure on the current checkout: an actual temporary addon module imports
root AddonSpec before defining its addon. Initial registration is false and its
entry-point failure reports a missing valid contract; explicit discovery after
import completes registers it. No discovery method or entry-point loader is
mocked. The synthetic metadata fixture is a source diagnostic, not qualification
of an installed scientific provider. This confirms that the generic defect is
still present; it is unrelated to the window-lifecycle changes in #245.

The retained diagnostic command was:

```bash
/home/diego/Myopt/miniconda3/envs/molsyssuite@uibcdf_3.14/bin/python \
  /tmp/msv-issue240-review-20261013/entrypoint-repro/reproduce.py
```

Its temporary `review_entrypoint_addon.py` contains
`from molsysviewer import AddonSpec` followed by
`addon = AddonSpec(name="review-entrypoint-addon")`; real `.dist-info` metadata
registers `review-entrypoint-addon = review_entrypoint_addon` under
`molsysviewer.addons`. Both initial failure and successful explicit rediscovery
are preserved in the reconciliation receipt.

## Resolution — 2026-10-13

Public spec/class exports no longer start discovery. First registry use or view
construction discovers providers once; exact sources still initializing are
retained and retried on subsequent use without rerunning completed factories.
The in-progress guard prevents recursive discovery. Completed missing contracts
and actual import failures retain their original reasons/tracebacks; the retired
MolSysMT entry point still stays excluded.

The real importlib.metadata/fresh-process guard passes 13 cases: addon-first,
root-types-first and registry-first; module/callable entry points; early registry
access and explicit bounded discovery; two simultaneous providers with a fresh
factory; lifecycle activation/deactivation on two real views; genuine invalid
contracts/import errors; and direct view construction without registry access.
The original source reproduction now registers immediately without a false
failure. Explicit rediscovery is not automatic refresh/replacement of an already
registered namespace; unregister before replacing a contract. This source guard
uses real metadata, not a mocked loader or an installed scientific provider.

## Compatibility follow-up — 2026-10-13

The single complete local Python run exposed three workspace assertions polluted
by automatic rediscovery after explicit `addons.clear()`. A separate real-metadata
reproduction confirmed that a root read restored the cleared provider. The final
correction marks that explicit empty registry as initialized; only explicit
registration/discovery restores it. The guard now passes 14 import-order/clear
cases, and the full previously failing workspace module passes 13 cases (27 total).
The actual popup browser guard also passes after this final Python correction.
The original complete invocation remains failed (3,131 passes, 21 skips, three
failures) and is not repeated or relabelled. Exact hosted qualification is tracked
separately in the receiving receipt. This follow-up preserves the public clear
contract; it does not change provider lifecycle or remove genuine load diagnostics.
