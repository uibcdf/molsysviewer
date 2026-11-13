---
summary: Auxiliary Mol* comparisons can resolve an ancestor package instead of their baseline.
issue: uibcdf/molsysviewer#374
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: medium
verification: reproduced
area: [tests, provenance, dependencies]
guard: tests/test_molstar_compatibility.py
normative:
blocked_by: []
supersedes: []
---

# Resolved: native comparison origin integrity

## What

The original #369 auxiliary State (`673`) and font (`676`) comparisons used
bare imports from entries outside the JS package. Their `installed` metafiles
resolve an ancestor installation, `/home/diego/node_modules/molstar`, rather
than the intended project 5.4.1. Its currently inspected metadata is 3.38.3;
the original probes did not preserve its package identity. Their old-side
measurements therefore cannot be attributed to 5.4.1. Raw logs and custody
remain unchanged. Their explicitly aliased 5.13.1 side, the production import
inventory and the separately built runtime/harness retain their actual scopes.

This differs from #370's removed production tsconfig source alias. An
auxiliary out-of-package entry can use ordinary ancestor resolution even when
the production build is correct. Setting esbuild's working directory alone
does not change the requesting module's resolution origin.

## Correction and acceptance

The qualification builder requires an explicit provider directory and expected
version, aliases bare native imports, rejects foreign native inputs and records
the actual bytes supplied to esbuild. It rechecks those files before emitting
an executable and a manifest. Original native code is not repaired or replaced
by this diagnostic route; ordinary build routes remain separately owned.

Real-provider regressions cover an entry beneath a deliberate foreign ancestor,
a mismatched declared version and an explicit foreign import. The rejected
controls must leave no executable/manifest. Repeat the State/font comparisons
using this tool and verify their native bytes against both preserved original
npm tarballs. Correct live receiving claims; never relabel or overwrite the
original raw measurements or private custody manifest.

Receiving `693` passes the four actual-provider compatibility/provenance cases
and seven related runner controls. Corrected State/font probes match every
consumed native file to each original tarball: 90/103 State/font files for
5.4.1 and 71/96 for 5.13.1. The live assessment and receiving explicitly withdraw
the two invalid original attributions, retain their immutable original custody
and record corrected measurements. The guard module rejects ancestor selection,
wrong declared identity and explicit foreign native inputs; the rejected probes
leave neither executable nor manifest. This is provenance integrity, not a
universal rendering, memory, host or installed-compatibility claim.
