# Interaction residency, queries and projection

**Current qualification — 2026-10-06:** the fixed Viewer 0.24.0 build 1 /
MolSysMT 0.23.0 ABI3 build 0 pair passes all sixteen installed staging cells and
39 hosted core browser suites. Public-pair and larger GPU qualification remain
open. Provider uibcdf/molsysmt#288 and uibcdf/molsysmt#289 source corrections and
their bounded receiving measurements are recorded below; the earlier open-provider observation does
not describe their current status. See the
[current scientific qualification](interactions_qualification.md) and
[exact receipt](stabilization_024_preparation_20261006.json).

**Earlier observation — 2026-10-02:** 24 sparse adapter workloads and ten detector
probes pass. Compound projection batching is done (#141); provider frame-query
cost (#288) and published-artifact qualification remain open under #140/#114.
The dated sections preserve measured inputs and their limits.

## Initial observations — 2026-09-30

Six fresh-process synthetic adapter workloads measured, followed by a real
complete-trajectory detector measurement.

Run `python devtools/benchmarks/interactions_residency.py --case small --pattern reuse` (and the medium/large cases, each with reuse/churn). Fixtures preserve intact bundled pentalanine molecules and repeat their coordinates through the public native Structures boundary. Observations are synthetic, not a chemical detector result. They include evaluated-empty and unevaluated frames. Each run loads coordinates and a complete sparse analysis, queries atoms/structures, and projects two sets that share one analysis.

Environment: Linux x86_64, Python 3.13; source provider HEAD `a04a5e7aad508b0a50ca9f22043f8ca6084411c8` (checkout dirty from independent provider work, preserved). Installed MolSysMT metadata reported `0.21.0+606.ga03eb4bf6`; it does not identify a published compatible provider. Process RSS includes imports, topology, coordinate copies, scientific columns, indexes, two visual sets and inspection. Numeric bytes omit Python objects/string tables; RSS changes cannot be attributed solely to scientific data. Timings are single observations, not service-level targets.

| Atoms × structures | Pattern | Occurrences / relations | Coordinates MiB | Analysis numeric MiB | Loaded RSS MiB | First atom/frame ms | Warm median ms | Two-set projection ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 62 × 5,000 | reuse | 22,495 / 6 | 7.10 | 1.02 | 533.0 | 1.96 | 0.49 | 3.00 |
| 62 × 5,000 | churn | 22,495 / 22,495 | 7.10 | 2.91 | 538.2 | 167.61 | 1.02 | 2.78 |
| 10,044 × 1,000 | reuse | 89,900 / 1,004 | 229.89 | 4.03 | 984.3 | 9.98 | 0.45 | 8.31 |
| 10,044 × 1,000 | churn | 89,900 / 89,900 | 229.89 | 11.49 | 1009.8 | 647.19 | 0.55 | 9.77 |
| 100,006 × 100 | reuse | 89,000 / 10,000 | 228.90 | 6.10 | 1057.0 | 65.64 | 0.44 | 71.32 |
| 100,006 × 100 | churn | 89,000 / 89,000 | 228.90 | 12.73 | 1070.4 | 553.10 | 0.41 | 67.39 |

Reuse shares recurring relation records across structures; churn uses a new relation per occurrence. Three nonconsecutive structures took 0.30–0.37 ms in these runs. Current-frame geometry was 3.5–418 KiB and inspection replies 2–16 KiB. No all-trajectory graphical projection was requested. Static export duplication and GPU workloads were not measured here.

Conclusions: warmed indexed queries are fast for these bounded selections, but the first atom query builds an index and reached 647 ms with many new relations. Coordinate/view residency dominates the numerical interaction columns; approximately 230 MiB of coordinates corresponded to roughly 984–1,070 MiB of loaded process RSS. Initial large fixture assembly took around one minute and is reported separately by the script, not as interaction query time. These observations support loading named analyses and querying the visible frame, while requiring exact provider-release evidence and realistic detector workloads before 1.0 certification. They do not establish a maximum supported system size.

The provider codec still materializes the complete selected occurrence table. The viewer bounds it before copying; public bounded occurrence pages are requested in `uibcdf/molsysmt#264`. Public selective H5MSM reads remain a separate future decision.

## Real detector follow-up — 2026-09-30

The [scientific qualification record](interactions_qualification.md) now adds
a real 62-atom, 5,000-structure Buch calculation: 2,248 sparse occurrences,
3,933.64 ms calculation time, 0.269 MiB of numeric analysis columns and
approximately 501 MiB of loaded process RSS after verification. The first
selected atom/frame query took 0.973 ms; its warm median was 0.496 ms. An
atom query over all structures took 0.310 ms. Four real/controlled workflows
also verify query semantics, physical distances, PBC, H5MSM and sessions.
These are source-provider CPU measurements, not published-provider,
large-protein trajectory or GPU certification. Reproduce the full detector
measurement with `python devtools/benchmarks/interactions_detector.py`.

## Expanded participant and family qualification — 2026-10-02

**Done: measurement and correctness checks.** Twenty-four fresh-process scale
workloads and ten real detector probes pass. They exposed compound-frame
batching (#141, now resolved below) and frame-limited internal/cross query cost
(uibcdf/molsysmt#288, still open). Expanded Interactions qualification remains partial
under uibcdf/molsysviewer#140; these measurements do not close the release gate.

The [machine-readable record](benchmarks/interactions_scale_20261002.json) retains
all query medians/maxima, counts, phase RSS, storage sizes and timings. Linux
x86_64, Xeon E5-2630 v4, Python 3.14.7; isolated installed provider wheel
`0.22.4+76.gdf1a298e7`, clean source
`df1a298e70a419a8f04562f8fb9ffaa92abb3be1`, SHA-256
`96ffd86f526360e26b220647eb8076ef3d6faf43f74cc5e46353f1045966fa6d`.
The Viewer is the local uncommitted integration based on `1cf7826d`; this is
installed-source development evidence, not a published-provider certification.

### Sparse adapter workloads

Run each combination of `small/medium/large`, `reuse/churn` and
`hbond/rings/water2/water3` in a separate process, sequentially:

```bash
python devtools/benchmarks/interactions_residency.py --case large --pattern churn --layout rings
```

`smoke` is the bounded regression case. The three scale cases retain
62 × 5,000, 10,044 × 1,000 and 100,006 × 100 coordinate axes. They repeat
intact public pentalanine molecules, without PBC/time in this synthetic probe.
Relations use three single-atom roles, two six-atom groups, or six/nine water-leg
roles. The six-atom peptide groups are **not detected aromatic rings**, and the
water roles are synthetic. Reuse shares recurring relation records; churn gives
each occurrence a new relation record, even when participant descriptions recur.
It is a valid imported-analysis stress case, not a claim about normal detector output.
These changes to membership/box construction and the different interpreter/provider
mean the older September numbers are not a controlled before/after comparison.

Each workload verifies 26 query patterns against direct participant membership:
scalar atom, atom lists, incident/internal/cross/between, exclusive between, a
selection of up to 1,024 atoms, scalar/nonconsecutive/all frame axes and coverage
of evaluated-empty/unevaluated frames. All **624 pattern checks** preserve original
occurrence identities and coverage; query operations are timed separately from
verification/materialization. No atom-pair square matrix is built. Two visual
sets reference the same analysis object, and only one requested frame is projected.
All observations are supported, with two/three segments per water occurrence.

| Atoms × structures | Layout | Pattern | Numeric analysis MiB | RSS after projection MiB | First atom/frame ms | Warm atom/frame median ms | Two-set projection ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 62 × 5,000 | hbond | reuse | 1.02 | 464.0 | 1.47 | 0.46 | 2.78 |
| 62 × 5,000 | rings | reuse | 1.02 | 464.7 | 1.50 | 0.43 | 25.39 |
| 62 × 5,000 | water2 | reuse | 1.02 | 463.8 | 1.46 | 0.45 | 3.03 |
| 62 × 5,000 | water3 | reuse | 1.02 | 464.0 | 1.49 | 0.43 | 3.39 |
| 62 × 5,000 | hbond | churn | 2.91 | 469.2 | 166.97 | 0.72 | 2.64 |
| 62 × 5,000 | rings | churn | 5.83 | 480.5 | 272.55 | 0.80 | 21.54 |
| 62 × 5,000 | water2 | churn | 4.28 | 477.1 | 184.31 | 0.71 | 2.74 |
| 62 × 5,000 | water3 | churn | 5.66 | 482.1 | 216.62 | 0.83 | 3.44 |
| 10,044 × 1,000 | hbond | reuse | 4.03 | 922.6 | 12.19 | 0.68 | 11.35 |
| 10,044 × 1,000 | rings | reuse | 4.16 | 923.4 | 14.51 | 0.49 | 416.46 |
| 10,044 × 1,000 | water2 | reuse | 4.09 | 922.9 | 10.72 | 0.51 | 19.00 |
| 10,044 × 1,000 | water3 | reuse | 4.15 | 923.4 | 11.49 | 0.48 | 25.94 |
| 10,044 × 1,000 | hbond | churn | 11.49 | 939.2 | 624.78 | 0.49 | 9.94 |
| 10,044 × 1,000 | rings | churn | 23.15 | 984.1 | 1089.13 | 0.46 | 423.89 |
| 10,044 × 1,000 | water2 | churn | 16.97 | 962.9 | 810.10 | 0.57 | 19.53 |
| 10,044 × 1,000 | water3 | churn | 22.46 | 967.9 | 780.30 | 0.45 | 25.17 |
| 100,006 × 100 | hbond | reuse | 6.10 | 1009.1 | 66.13 | 0.42 | 74.06 |
| 100,006 × 100 | rings | reuse | 7.40 | 1012.1 | 104.12 | 0.42 | 4226.36 |
| 100,006 × 100 | water2 | reuse | 6.71 | 1010.3 | 83.00 | 0.49 | 383.43 |
| 100,006 × 100 | water3 | reuse | 7.32 | 1012.2 | 99.05 | 0.52 | 467.38 |
| 100,006 × 100 | hbond | churn | 12.73 | 1021.8 | 653.08 | 0.52 | 83.60 |
| 100,006 × 100 | rings | churn | 24.27 | 1062.7 | 992.43 | 0.41 | 4147.61 |
| 100,006 × 100 | water2 | churn | 18.16 | 1044.6 | 687.71 | 0.43 | 354.82 |
| 100,006 × 100 | water3 | churn | 23.60 | 1052.8 | 752.18 | 0.45 | 421.37 |

Numeric analysis columns occupy 1.02–24.27 MiB in these workloads, while process
RSS after projection ranges from 464 to 1,063 MiB. Coordinate arrays alone are
7.10 or about 230 MiB. Phase readings separate fixture assembly, analysis, view
loading, attachment, indexing, query checks and two-set projection; verification
allocations and allocator retention can affect later RSS. Neither differences
in RSS nor `numeric_nbytes` measure the interaction objects' full exclusive size.
Warm scalar-atom/frame queries take 0.41–0.83 ms, while the first index-building
query takes 1.46–1,089 ms. Broad internal/exclusive queries can still exceed one
second. They must not be summarized by the scalar query timing.

The independent direct-provider probe confirms the latter limitation: a warm
internal query of frame 0 takes 769 ms for five results, compared with 783 ms
for all 22,495 occurrences. Cross takes 381 ms for zero results in frame 0,
compared with 389 ms for the trajectory. This is tracked in
uibcdf/molsysmt#288; membership semantics remain correct. The separate bounded
materialization request remains uibcdf/molsysmt#264.

Compound-group projection takes 416–424 ms for 100 observations and
4,148–4,226 ms for 1,000. Single-atom paths are much cheaper. Inspection identifies
one supported provider center call per distinct group; uibcdf/molsysviewer#141
was resolved by batching groups through the existing public operation (see the
follow-up below). CPU frame preparation
is the measured bottleneck; no browser/GPU diagnosis follows from these numbers.
Geometry remains frame-local and below the configured budget in every case.

### Real scientific detectors

```bash
python devtools/benchmarks/interactions_detector.py  # Buch: all 5,000 real frames
python devtools/benchmarks/interactions_detector.py --family pi_pi --structures 1000
python devtools/benchmarks/interactions_detector.py --family water_bridge_2 --structures 1000
```

Buch uses the complete actual peptide trajectory and the existing independent
physical-distance/PBC checks. Disulfides use the actual 55,628-atom protein and
one structure. Other families repeat the shared analytical positive/empty/positive
conformations for 1,000 structures. A baseline calculation establishes the per-frame
counts, warming the provider before the measured detector; setup/baseline cost is
reported separately. Counts, evaluated-empty frames and current-frame projection
are checked. These small real chemical fixtures exercise trajectory handling;
they do not certify large protein/solvent trajectories for those detectors.

| Family | Atoms × structures | Occurrences | Calculation and attachment ms |
| --- | --- | ---: | ---: |
| hbond | 62 × 5,000 | 2,248 | 3585.53 |
| disulfide_candidate | 55,628 × 1 | 8 | 24.34 |
| ionic_contact | 5 × 1,000 | 667 | 221.85 |
| pi_pi | 12 × 1,000 | 667 | 510.78 |
| cation_pi | 7 × 1,000 | 667 | 386.87 |
| halogen_bond | 4 × 1,000 | 667 | 447.18 |
| hydrophobic_contact | 6 × 1,000 | 667 | 339.12 |
| metal_coordination_candidate | 3 × 1,000 | 1,334 | 336.96 |
| water_bridge | 11 × 1,000 | 1,334 | 1069.73 |
| water_bridge_2 | 14 × 1,000 | 667 | 1197.61 |

The single-frame disulfide projection is already cached after adding its set;
the record labels that fact and separately times initial set creation/projection.
These detector timings include the public Viewer calculation/attachment route,
not just an isolated scientific kernel.

### Storage and the 1.0 decision

Every sparse workload round-trips its named analysis through public
interactions-only H5MSM 0.5 operations, preserving participant atoms, structure/
relation columns, evaluated coverage and filtered occurrence identities. Files
occupy 0.07–2.70 MiB. Warm selected-analysis reads take 12–919 ms. They materialize
the complete selected analysis in the existing process; no cold-file or fresh-reader
RSS claim is made, and no coordinate layer is written/read in this storage probe.

Continue with named analyses in memory and visible-frame queries for the bounded
1.0 implementation. These observations do not require a new file-backed Viewer
mode, but they also do not establish a maximum supported system or an arbitrary
large-file promise. #141 is resolved and the provider's #288 response is verified
in the follow-up below. Selective H5MSM integration remains a separate
measurement/contract decision. Browser transport, GPU throughput, overlapping
static-export geometry and compatible published artifacts remain separate gates.

The 19 focused Python regression checks pass (7.60 seconds); the 16 legacy-file
warnings identify the shipped H5MSM 0.4 demo input and do not change the 0.5 output
checks. Complete-source regression evidence is recorded in the current checkpoint.

The complete Python suite was run once after that focused pass: **2,556 passed,
23 skipped, zero failures/errors**, exit 0 in 337.67 seconds. JUnit and the compact
log agree (`/tmp/msv-interactions-residency-full.xml`,
`/tmp/msv-interactions-residency-full.log`). This does not replace a final-browser
or installed-public-provider qualification.

## Compound projection batching — 2026-10-02

**Done:** uibcdf/molsysviewer#141 batches endpoint groups through public
`msm.structure.get_center` and checks periodic integrity through public explicit
pairs in `get_distances`. Batches retain at most 128 occurrences and 16,384
participant atom references; their centers are reused only within that bounded
batch. The frame adapter reads its visible coordinates/box once, while public
geometry operations can access their selected scientific data per batch. No
whole-trajectory geometry, Cartesian distance matrix or copied provider kernel
is introduced. Occurrence identity, roles, measurements, units, periodic images,
split-group refusal and existing projection byte limits remain intact.

Four fresh sequential runs repeat the same ring-layout inputs, interpreter,
provider and host as the initial measurements. These synthetic memberships on
intact peptide topology qualify adapter orchestration, not aromatic detection.
The [structured comparison](benchmarks/interactions_batching_20261002.json)
retains raw phase readings, source hashes and provider wheel identity.

| Observations / pattern | Initial projection ms | Batched projection ms | Speedup |
| --- | ---: | ---: | ---: |
| 100 / reuse | 416.46 | 31.18 | 13.36× |
| 100 / churn | 423.89 | 31.34 | 13.53× |
| 1,000 / reuse | 4,226.36 | 280.94 | 15.04× |
| 1,000 / churn | 4,147.61 | 291.01 | 14.25× |

All occurrence/segment counts, queries, coverage and H5MSM round trips remain
correct. Numeric analysis arrays are unchanged. Process RSS includes coordinate
residency, imports, verification allocations and allocator retention; these runs
do not establish a memory reduction or an exclusive object-size measurement.
These are CPU preparation observations on one host, not playback/GPU targets.

The 16 new regression cases observe actual public geometry calls and compare
positions with independent atom-mean/image references. Restoring per-group scalar
calls in an isolated mutation probe makes the guard fail as expected. The 71
related family/scene/residency tests pass. The complete Python suite was run once:
**2,572 passed, 23 skipped, zero failures/errors**, exit 0 in 428.46 seconds.
The complete real Mol* `interactions-subpanel` browser suite also passes,
including 20 calculated/restored family scenes and all 17 real calculation forms.
Its headless SwiftShader correctness evidence does not qualify GPU throughput or
the entire core browser lane. Local JUnit/log paths are preserved in the structured
comparison and [resolved report](archive/compound_interaction_projection_dispatches_per_group.md).

The product integration remains local and uses the installed experimental wheel
at `df1a298e70a419a8f04562f8fb9ffaa92abb3be1` for those measurements. The follow-up
below verifies uibcdf/molsysmt#288; compatible published provider/Viewer artifacts
and exact-candidate CI remain necessary before closing uibcdf/molsysviewer#140.

## Relevant-frame provider queries — 2026-10-02

Done: uibcdf/molsysmt#288 is closed at `78981d6c1`; a clean wheel from `396e6979f`
verifies the correction from the unchanged installed Viewer artifact with Pandas
3.0.6 / NumPy 2.5.3 / Python 3.14.7. Explicit-frame atom/type queries first select
frame occurrences and inspect their unique relation candidates. They avoid
building the global atom-posting index for this route and retain parallel handles,
requested frame order and compound participant membership.

On the 62-atom, 5,000-structure, 22,495-occurrence changing-relation input,
indicative warm three-call medians improve from 667.508 to 0.508 ms for internal,
330.242 to 0.407 ms for cross, 3.585 to 0.456 ms for incident and 3.451 to 0.678 ms
for between. Eight frame/whole-trajectory query patterns match the independent
membership reference with both provider wheels. Complete-trajectory queries
retain their global cost; these one-host measurements do not establish throughput
or memory targets. Original scale and batching records remain unchanged.

Fifteen provider guards pass against installed code. Consumer checks pass 90 cases
and six offline real Mol* pages; one existing periodic-group guard needs adaptation
because public coordinate setters now invalidate its precomputed observation.
The independent malformed-import probe still confirms refusal of split groups.
See [artifact evidence and remaining gates](installed_artifact_qualification.md#provider-288289-review--2026-10-02)
and [raw measurements](interactions_provider_review_20261002.json).
