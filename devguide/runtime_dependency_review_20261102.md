# Runtime floors and maintained distribution routes

**Scope:** owner review for #285 and #288, on top of Viewer source `481319a9`.
This is metadata, source-route and diagnostic receiving. It neither produces
packages nor qualifies a future public version. The original public
0.24.0 build-1 evidence remains tied to its immutable producer and bytes.

## Runtime choices

All required and optional runtime requirements now have inclusive lower bounds.
There is no Viewer-imposed provider ceiling or exclusion. Development-tool pins,
Python's admitted range and the optional Qt qualification keep their purposes.

| Requirement | Reviewed boundary and evidence |
| --- | --- |
| `depdigest>=0.12.0` | Uses `check_dependency`, `dep_digest`, consumer configuration and explicit disabled PyPI / selected Conda installer routes. The latter contract is available from 0.12.0, not just the installed development version. An isolated source probe at the exact 0.12.0 tag (`0da46d9ff31fbe2f92e4e667a32868aebe840b39`) receives Viewer root import, a real available decorated operation and five missing-dependency diagnostics. This is a provider-API probe with the existing support environment, not a solved floor installation. |
| `numpy>=1.26` | Aligns the numerical baseline with required public MolSysMT 0.23.0 (`46ef28eb`), whose metadata already requires NumPy 1.26. Viewer uses established ndarray, reductions including `initial`, linear algebra, contiguous buffers and numeric/index dtypes, with no inspected NumPy-2-only API. No additional Viewer ceiling is introduced. The source-pair environment retains the provider's `<3` restriction as that exact scientific closure, not a universal Viewer exclusion. The local current-provider receiving uses 2.4.6; it does not establish an independent complete suite on 1.26. |
| `pyyaml>=6.0`, optional | Supported Python YAML baseline for `safe_load` of presets. This is a selected supported baseline, not a claim that `safe_load` was introduced in 6.0. JSON remains independent. Development/test/docs environments carry the feature while core installation does not require it. |
| `imageio>=2.16.0`, optional | Movie export imports `imageio.v2`; dedicated v2/v3 namespaces were introduced in [ImageIO 2.16.0](https://github.com/imageio/imageio/blob/master/CHANGELOG.md#v2160-2022-02-14). External encoders remain explicit prerequisites for the requested format. This does not certify every codec or a PyPI dependency closure. |

Existing floors for aiohttp, anywidget, ArgDigest, MolSysMT, Packaging,
PyUnitWizard, SMonitor and Traitlets are retained with their prior receiving
scope. In particular, the unreleased ChemicalStates source does not silently
raise `molsysmt>=0.23.0` or certify a future provider package. A concrete future
incompatibility needs an owner, evidence, affected contract and a removal/review
condition before introducing a runtime restriction.

The recipe preserves the canonical required constraints exactly. Runtime-bearing
environments preserve or strengthen them; development keeps its previously
approved newer support tools. Build-only tooling and optional scientific test
fixtures remain separate from public runtime dependencies.

## Maintained routes

| Route | Classification, controls and remaining qualification |
| --- | --- |
| Conda | Official noarch Python route, `uibcdf` with `conda-forge` and the declared test/installation closure. One maintained recipe, three launcher entry points and generated runtime resources are covered by artifact/negative-contract tests. Staging, exact-file qualification and same-byte promotion remain mandatory at an authorized freeze. No new files were built or promoted. |
| Provisioned source | Editable development uses the suite's Python 3.14 environment. Controlled CI installs exact checkouts, validates dependency origins and compiled resources, and executes real consumers. Development receiving now avoids temporary candidate-version tags; frozen-candidate mode remains separate. The shared local environment's unrelated Amber conflicts prevent a clean-environment claim. |
| Python wheel | Internal construction/resource/import gate, including built-wheel tests, without a public PyPI installation promise. The PyPI closure is unqualified; suite dependency diagnostics no longer recommend it. |
| Frontend npm/CDN | Separate runtime delivery with version/bundle and release-history guards. Runtime builds use authoritative TS sources. A later 0.25.0 freeze must bind Python version, frontend identity and exact runtime bytes before publication; prior npm/CDN evidence does not qualify current source. |
| HTML/static output | Exported visualization route, with its existing browser/offline limits. This is not installation of a new Python package or a certified remote/native host. |
| Qt / remote | Qt remains optional and experimental; remote remains a post-1.0 preview. Empty standalone extras do not advertise an unqualified pip-wheel Qt stack. Their separate platform/GUI obligations remain owned. |

`_depdigest.py` now declares the actual `uibcdf` Conda route and disables pip
hints for suite providers in this consumer. `LibraryNotFoundError` retains the
provider's actionable details in its catalog message instead of discarding them.
The normal public documentation continues to own complete provisioning/channel
instructions; a short diagnostic does not promise a fresh solved environment.

## Executed checks and honest limits

`audit_dependency_contract.py` is the existing read-only preflight; no parallel
dependency auditor is introduced. Metadata, recipe, classified environments and
source checkout rules agree. `tests/test_dependency_contract.py` exercises
negative metadata, path and installed-origin controls;
`tests/test_distribution_artifact.py` checks resources, entry points, the built
wheel and required/optional inclusive floors. Five real dependency-provider
diagnostic checks reject unsupported pip hints. The public installation contract
and existing SMonitor tests remain applicable.

The local dependency/distribution selection passes 69 cases including the
built-wheel check; diagnostic integration adds 20 cases in a separate scope.
Exact JUnit/source provenance is retained in the chemical-domain receiving
receipt. These are not an additive full-suite total or installed Conda matrix.

The completed source suite passes 3,344 cases with 21 justified omissions and
14 experimental Qt cases deselected. Final provider head `7ef48701` adds only
documentation over requested `de7ffad2`; all 3,074 hashed provider runtime files
remain unchanged during receiving. The later tooling-only override receives
335 JS cases on Node 22 and zero live npm advisories. Its production graph is
unchanged. #289 records its bounded compatibility/removal policy. #290 owns the
pre-existing empty LCOV; passing JS tests must not be advertised as measured
source coverage. No numerical coverage evidence is claimed.

Before a new artifact: finish #269 against a provider whose installed Rust
manifest passes; complete remaining addon source/GUI scope under #264; reconcile
the historical `release_plan.toml` only when an actual candidate is frozen;
then qualify original wheel/Conda/npm bytes, platforms, public promotion,
first contact and preservation through the existing release route. The stale
0.24.1 staging plan is retained as historical preparation, not authorization to
publish it or to label current development 0.25.0. These are explicit future
release prerequisites, not hidden policy-review exemptions.

## Coverage receiving — 2026-11-03

The previously empty report is corrected under #290 without changing the
dependency graph: all 335 unit cases and seven real-tooling/negative controls
pass. Source maps, post-remap URL filtering and a fail-closed report guard now
produce measured production line/function records. The
[receipt](js_source_coverage_receiving_20261103.json) retains exact scope and
pending hosted receiving. This supersedes the coverage-specific next action
above; installed provider/artifact and remaining addon work stay separate.
