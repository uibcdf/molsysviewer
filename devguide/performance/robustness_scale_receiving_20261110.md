# Robustness scale receiving — 2026-11-10

**Partial: the adopted scale anchors pass; thirty active cycles in one kernel remain pending.** E2 under [the active plan](../pending_proposals/pre_1_0_robustness_audit_and_action_plan_20261106.md) is not closed. Original progress is 38/46 after C3 receiving; F1/B4 are additional source deliveries. The [machine-readable scale receipt](../robustness_scale_receiving_20261110.json) retains identities, sample counts, median/MAD/range, input hashes and scoped limits. The [prolonged-session receipt](../prolonged_scientific_session_receiving_20261110.json) preserves eight successful cycles and the ninth recovered-frame observation #354, then fifteen correct cycles in a separate kernel before the shared-pressure stop. No cycles are added across kernels.

## Measured axes

Each row has three fresh Python workers and three fresh Chromium processes. Processes are fresh; filesystem, compiler and driver caches are not asserted cold. Python registration excludes drawing and native fixture construction. Times below are medians in milliseconds.

| Case | Atoms | Structures | Python serialization | Python registration | First molecular draw |
| --- | ---: | ---: | ---: | ---: | ---: |
| small-1 | 2,882 | 1 | 71.52 | 27.16 | 4932.90 |
| small-100 | 2,882 | 100 | 76.95 | 40.31 | 4065.20 |
| medium-1 | 26,214 | 1 | 396.29 | 173.81 | 9770.60 |
| large-1 | 104,856 | 1 | 1496.37 | 688.96 | 31716.50 |

Browser small×10 is also received. Actual `didDraw` observations require the expected loaded atom count and exact float32 positions for three source atoms, including first/revisited structures and representation replacement. This is not a proof of every rendered pixel. Source positions are read through Mol* source-atom correspondence, rather than assuming model atom order. Temporary fixtures use the existing owned-workspace helper.

The older bounding-geometry/double-animation-frame criterion did not establish this actual-draw boundary. The revised observations and the August Python 3.13/Chrome 149 baseline have different software, resources and measurement definitions; direct ratios do not establish a regression or admission threshold. The current renderer is Chrome 157, WebGL2, ANGLE/Vulkan SwiftShader. Software-renderer process RSS is not hardware VRAM.

## Sparse residency and native detector

Three fresh processes receive each small (62 atoms × 5,000 structures) and medium (10,044 × 1,000) reuse/churn anchor. Occurrences and composite ring participants are synthetic workload data, not detected aromatic chemistry. Public queries are compared with direct membership references; evaluated-empty and unevaluated coverage, source identities and H5MSM persistence are distinguished. H5MSM reads materialize the chosen analysis and are warm-process measurements. The real Buch control separately receives 62 atoms × 5,000 actual structures, nonempty occurrences, periodic geometry and twenty queries per process, repeated in three fresh processes.

The ordinary and 104,856-atom literal-overlay history cases each retain twenty-five production checkpoints in three fresh workers, then verify empty history after clear. Allocator retention and lifetime peak RSS alone do not prove a leak. Browser page-close samples, full browser retirement and same-kernel retention are separate observations; the last remains pending.

## Summary arithmetic and retained evidence

[#353](https://github.com/uibcdf/molsysviewer/issues/353) corrects four benchmark helpers that selected the upper middle observation for even counts. The shared statistic is guarded by actual Node/TypeScript execution against Python statistics over exact rational inputs, including overflow/subnormal controls. Empty observations remain explicit rather than becoming zero. Corrected navigation summaries are computed offline from immutable raw frame timing arrays. Original timings, prior summaries and their hashes remain preserved; no scientific/rendering workload is repeated merely to repair arithmetic.

The receiver uses sequential 2-CPU/4-GiB child scopes, zero swap, owned-process cleanup and shared-pressure stops with at least 2 GiB globally available. The identity probe independently reads actual cgroup limits and hashes all three bundled input files. Supervisor overhead is separate from the child limits; available resources are not reserved. No processes belonging to other work are touched. A first Chrome launch failed because its temporary Unix-socket path was too long; the established short private scratch root fixes that provisioning failure. The original failure remains in the receipt.

Source, full hosted/platform, clean installed and postponed human observations remain separate. Hardware VRAM needs a qualified hardware-GPU profile. This checkpoint produces no candidate, tag, package, promotion or Release.

## Same-kernel receiver

The owner contribution [MolSysMT #706](https://github.com/uibcdf/molsysmt/pull/706)
adds an opt-in Linux `system_panel_jupyter.py --scenario prolonged-session`
profile with bounded `--cycles`, `--active-seconds` and
`--server-ready-timeout`. The tested scale profile uses 4 CPU/4 GiB, zero swap,
30 cycles and ten seconds of newly drawn playback per cycle; server preparation
gets an explicit 90 seconds. Scientific/draw deadlines are unchanged. Each cycle
uses all 5,000 structures of real pentalanine, a managed coordinate edit,
independent distances, native Buch hbonds, exact session recovery, both popups,
a separate 1TCD witness and live ownership/resource observations.

The receiver explicitly shows and identifies the target widget before reading
its initial frame. Activity requires completed native draws after the active
interval and distinct structures, excluding replayed `didDraw` notifications;
it sets no universal FPS admission threshold. Initial frame commands/results
are recorded without replacing their return values or submitting a repair seek.
The original offscreen discrepancy remains under #354. The revised receiver
observes fifteen correct cycles (12.55 minutes of cycle work) before the
shared-pressure stop; #356 tracks thirty disposed controllers still exposing
logical molecular data. A small retainer diagnosis precedes another complete
run. These observations establish neither a leak cause nor 30-cycle acceptance.
