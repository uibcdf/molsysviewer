---
summary: Track the published Mol* fix for component-name cache retention.
issue: uibcdf/molsysviewer#363
status: open
opened: 2026-11-12
closed:
verification: measured
area: [dependencies, memory, lifecycle]
guard:
normative:
blocked_by: []
supersedes: []
---

# Published Mol* component-cache correction — consumer follow-up

## What

Follow the native resolution of Mol* audit `01/B1 = 04/B1` and qualify the
first published npm artifact containing the effective correction. Diego chose
this local tracking issue instead of opening another upstream report. The
[review](../molstar_component_cache_report_review_20261112.json) preserves
the independently verified public-package and current-source evidence.

This follow-up does not replace uibcdf/molsysviewer#356's pre-1.0 lifetime
correction or its prolonged-session acceptance. Public 5.13.1 qualification
is now adopted pre-1.0 under uibcdf/molsysviewer#372; future v6/evolution
retains uibcdf/molsysviewer#115's post-1.0 scope. The selected 5.13.1 source
still requires the exact-version/byte-checked repair.

## How

At dependency/release review checkpoints, inspect the upstream
[known audit](https://github.com/molstar/molstar/blob/dabbf29f952880a034a9637e28c9844e3ae73d9f/.v6/perf-audit-2/bugs.md)
and the resolution associated with its forced-GC regression, deferred in
[PR #2032](https://github.com/molstar/molstar/pull/2032). Do not infer that the
next release fixes it: original 5.4.1 and public 5.13.1 packages both retain
the minimal inputs; current development source does too.

Record the actual resolving PR/commit, release version/source and original npm
artifact identity/integrity. Inspect its published bytes, review migration
under #115, and receive the native replacement with no local cache repair:
absent/empty/populated `chem_comp`, retained and independently owned inputs,
chemical/saccharide results, actual notebook backing-buffer collection and
the applicable browser, trajectory, popup/session and prolonged-use gates.

Only then remove the version/byte-checked build adapter, update build routes
and regenerate the runtime through its normal build. Preserve the old failing
controls and the exact native replacement evidence. A source-only fix or
newer version number alone does not close this issue.

## Why

The native strong object-key cache can keep entire input buffers reachable.
The local compatibility repair must remain owned and removable, without an
automatic dependency bump or a forgotten permanent divergence. Monitoring
does not authorize an upstream write, package publication or major migration.
