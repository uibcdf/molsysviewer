# Interactions qualification

## Current staging qualification — 2026-10-06

Viewer **0.24.0 noarch build 1**, producer
`1a4c97a58b68b69f3a836546c9e4ac6187c3efa2`, with MolSysMT **0.23.0 ABI3 build 0**,
producer `46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9`, passes all sixteen installed
staging cells and exact Windows launcher checks. All 39 hosted core browser
suites pass. Canonical-source Python 3.14 integration passes on Linux, macOS
and Windows, with all 39 core suites and 25 documented notebooks passing on Linux.
The scientific results, named analyses, explicit selection-mode vocabulary and
H5MSM 0.5 workflows are therefore qualified against this fixed staged pair.
See [the installed qualification](installed_artifact_qualification.md) and
[the exact preparation receipt](stabilization_024_preparation_20261006.json).

Both candidates remain staging-only. Public installed-pair qualification,
publication and the final 1.0 candidate remain open under #114/#140. The
measured workloads below retain their original provider, date and scope;
they do not establish native-GPU or large-system browser limits.

## Nine-family source integration — 2026-10-01

Explicit family wrappers and their role-aware projections pass against an
isolated installed wheel built from provider commit
`df1a298e70a419a8f04562f8fb9ffaa92abb3be1`. This is an installed experimental
source artifact, not a published release. The reproducible inputs, 25 new
scientific cases, 70 existing API/scene/inventory cases, full-suite observation
and bounded sandbox correction are recorded in
[uibcdf/molsysviewer#140](pending_proposals/align_interactions_with_molsysmt_families.md#resolution).
The real Mol* subpanel suite passes with 20 additional calculated/restored
scenes covering nine families and both supported water orders, periodic
positions for the newer families, compound centroids and multi-leg occurrence
counts. The provider wheel/version/hash and import location are preserved there.

Python uses explicit getters such as
`view.interactions.hbonds.get_hbonds(name=...)`; Studio calls the same wrappers.
No generic public calculation dispatcher is introduced. Modern detectors retain
their chemical-graph requirements and their scientifically distinct criteria.

## Original bounded minimum — 2026-09-30

**Status:** bounded real scientific workflows and the calculated-link browser
case pass against a development backend. A compatible published MolSysMT and
the exact 1.0 candidate remain unqualified under `uibcdf/molsysviewer#114`.
The namespace/result coordination remains `uibcdf/molsysmt#250`.

## Published dependency

The official UIBCDF channel was queried on 2026-09-30. Its newest version with
`main`-labelled files remains **0.22.4**, also the latest GitHub Release. The
Anaconda API's package-level `latest_version` field is stale (0.12.0); the
decision uses the actual versioned file records and labels.
The Linux x86_64 artifact is
`molsysmt-0.22.4-pyabi3h03bb3b7_3.conda`, SHA-256
`e2ac3c779f17b2ca2aa7655fc6a2a349de558de229f479525826b5deaa6f8d3e`.

`devtools/interactions_provider_compatibility.py` passed against its real
extracted `site-packages`: ordinary viewing works, Studio reports the backend
unavailable, and scientific creation raises an explicit compatibility error.
That package cannot qualify the new feature. Installing Viewer with its base
dependency floor does not establish Interactions availability.

The 2026-10-01 [installed wheel check](installed_artifact_qualification.md)
adds fresh public-dependency and offline HTML evidence with both libraries
imported from an isolated environment. The installed compatibility probe uses
`--installed` and retains the unavailable-backend assertion. This extends the
ordinary-view evidence, not the scientific feature qualification.

The publication must provide the public sparse `Interactions` result and its
query/occurrence identity contract, named `MolSys.interactions` analyses,
Buch/disulfide optional result outputs, and H5MSM 0.5 read/write-layer APIs.
The later staged pair above qualifies those capabilities with the dependency
floor `molsysmt>=0.23.0`. Public promotion and independent public installed-pair
verification remain necessary before claiming a supported public route.

## Real scientific workloads

All datasets come from the public MolSysMT system catalog; no new molecular
data were vendored and no provider methods were mocked.

| Workload | Atoms / structures | Result | Observations checked |
| --- | --- | --- | --- |
| Pentalanine, source frames `[4999, 0, 73, 3]` | 62 / 4 | 56 Buch observations over local frames `[3, 0, 2]`, threshold 0.4 nm | Incident/internal/cross/between queries; nonconsecutive local frames; evaluated-empty versus unevaluated coverage; full and interactions-only H5MSM 0.5 import; three named analyses; MSV session restoration. |
| One real pentalanine residue reimaged by the first box vector | 62 / 4 | 76 Buch observations, 16 with nonzero relative images | The participant triples and distances are unchanged by the controlled lattice translation. Geometry, H5MSM and sessions preserve the images. An angstrom session policy does not change nm wire coordinates or the 0.2 Å graphical radius. |
| Solvated chicken villin HP35 | 4,369 / 1 | 2,439 Buch observations, 299 with nonzero relative images | Independent participant-image reconstruction reproduces every measured H···A distance and prepared endpoint; indexed atom/frame queries agree with the participant sets. The catalog H5MSM contains one structure, despite its trajectory filename. |
| 2HGR cysteine sulfur proximity | 55,628 / 1 | 8 geometric candidates at the default 0.205 nm cutoff | An independent CYS/SG pair-distance enumeration agrees exactly with the detector. Bond count and bonded atom pairs remain unchanged. Prepared S···S endpoints reproduce the measured distances. Both H5MSM import routes and MSV restoration preserve these positive candidates. They do not certify covalent disulfides. |

Expected endpoints are reconstructed from scientific participants, occurrence
images, coordinates explicitly converted to nm and box row vectors in nm.
They are not copied from the viewer's projection. Assertions check the data
and prepared Python-to-TS geometry; the solvated and sulfur workloads do not
claim large-system browser/GPU qualification.

The existing `interactions-subpanel` browser case now also consumes the real
calculated/reimaged trajectory. It checks actual Mol* mesh links and occurrence
identities at local frames 0, 3 and 2, including nm-to-Å conversion and radius,
both before and after loading the saved session. The test passed in real Chrome
with WebGL2/SwiftShader; its two screenshots were inspected and draw molecules
and dashed links. It uses the suite's one isolated browser context. This is
software-rendered browser evidence, not native-GPU or visible-window Qt evidence.

## Complete real trajectory and query timings

`devtools/benchmarks/interactions_detector.py` ran in a fresh Linux process:

| Measurement | Observation |
| --- | --- |
| Real trajectory | 62 atoms × 5,000 structures, all evaluated |
| Buch criterion | H···A distance ≤ 0.23 nm, PBC enabled |
| Sparse occurrences | 2,248, including 7 with nonzero relative images |
| View load | 4,146.45 ms |
| Complete detector calculation | 3,933.64 ms |
| First atom + nonconsecutive frame query | 0.973 ms |
| Warm atom + frame query, median of 19 | 0.496 ms |
| Atom query over the complete analysis | 0.310 ms, 234 matches |
| Frame query | `[4999, 2, 73]`, one matching occurrence for the selected hydrogen |
| Analysis numeric columns | 0.269 MiB |
| RSS before analysis / after checks | 457.13 / 500.79 MiB |
| `getrusage` process peak RSS | 500.20 MiB |

The first frame has no result at the default threshold. The benchmark chooses
an observed hydrogen from the first nonempty evaluated frame (frame 2) rather
than assuming frame 0 contains an interaction. Geometry checks independently
reconstruct all 2,248 scientific occurrences and compare prepared geometry for
the three sampled frames. This is one timing observation, not a service-level
target or a maximum supported system size. RSS includes imports, native
backend, molecular data, copies, indexes and verification; the two RSS sources
are sampled separately and are not an exact allocation ledger.

## Provenance and reproduction

Environment: Linux x86_64, Python 3.14.7, PySide6/Qt 6.11.2. Viewer remains an
uncommitted working tree based on `6f49013c80c7a10eb09a1220b2236d879d8ecd5a`.
The provider progressed independently from `7a8350f76c6f` with dirty plane/Rust
work to clean commit `18cc43021a663b5c79b8aa7b51cdef5e1fe27785` during this task.
Both working trees were preserved; no provider file was edited or merged here.
The final four-workload qualification was repeated in a fresh process, with
the same clean provider commit recorded before and after. The complete
trajectory measurement used that clean provider revision too.

Its editable installation reports `0.22.4+24.g42b487869`; that development
version string is not a published artifact identity or the checkout commit.
The qualification records the source location and Git state separately.

With the canonical Python environment active, from the repository root:

```bash
python devtools/qualify_interactions.py /tmp/msv-interactions-qualification
python devtools/benchmarks/interactions_detector.py
python -m pytest --receptor=llm tests/test_interactions_qualification.py -x
```

For the installed-provider run, place its actual `site-packages` first in
`PYTHONPATH` and verify `provider_source`/`provider_version` in the output. Its
dependencies must also belong to the qualified environment. The tool does
not install, publish or substitute a provider.

From `molsysviewer/js/`, with canonical `PYTHON`, `CONDA_PREFIX` and
`PW_CHROMIUM_BIN=/usr/bin/google-chrome`:

```bash
npm run build:harness
npm run build:e2e:all
node tests/e2e/interactions-subpanel.e2e.js
```

The complete Python run passed **2,296 tests, with 20 skips**, exit 0 in
274.18 seconds. It ran once for this task, during the source-provider work
above; it is not an exact installed-artifact gate. Four scientific regression
tests passed first. TypeScript checking, the targeted browser case and targeted
Ruff checks passed. The complete core browser lane and JS unit suite were not
repeated for these test/tool additions; their preceding design-review results
remain separate evidence.

Local evidence files: `/tmp/msv-real-interactions-clean-20260930.json`,
`/tmp/msv-real-detector-5000-20260930.json`,
`/tmp/msv-real-interactions-full-20260930.log`,
`/tmp/msv-real-interactions-browser-20260930.log`, and
`/tmp/msv-interactions-published-20260930.log`. The source commands and
regression tests remain in the repository so these temporary files are not
the only route to reproduce the checks.
