---
summary: Use conventional medians for even browser benchmark observations.
issue: uibcdf/molsysviewer#353
status: resolved
opened: 2026-11-10
closed: 2026-11-10
severity: low
verification: reproduced
area: [performance, statistics, validation]
guard: tests/test_representative_scale_benchmark.py::test_browser_benchmark_medians_match_independent_reference
normative: devguide/performance/robustness_scale_receiving_20261110.md
blocked_by: []
supersedes: []
---

# Browser benchmark medians — resolved

Four benchmark helpers selected the upper middle observation. Private 243
executes the actual representative-scale TypeScript function through esbuild:
`[1, 3]` returns 3 rather than the conventional median 2. This affects even
navigation groups in E2; raw times and molecular/rendering results are separate.

One finite-observation statistic now serves representative scale, trajectory
transport, exclusive ownership and message toll. It averages both middle
observations, avoids sum overflow, rejects invalid/empty inputs and supplies
an explicit null variant for no navigation observations. The real Node guard
compares with Python statistics over exact rational inputs, including even,
odd, singleton, signed, extreme and subnormal cases, and enforces shared caller
ownership. The corrected guard passes in 244/246; all four scripts build.

[The scale receipt](../robustness_scale_receiving_20261110.json) recomputes
navigation summaries from immutable raw arrays. Original summaries and failed
control remain preserved. This correction does not relabel historical results,
rerun scientific/rendering workloads, alter a molecular algorithm or authorize
a release. The [measurement reference](../performance/robustness_scale_receiving_20261110.md)
owns the current definitions and limitations.
