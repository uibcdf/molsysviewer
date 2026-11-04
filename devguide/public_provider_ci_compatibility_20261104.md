# Public-provider CI and distribution receiving — 2026-11-04

Operational receiving for Viewer #292–#294 and existing MolSysMT #431.
The [receipt](public_provider_distribution_receiving_20261104.json) records
exact inputs/results. No release or complete installed solve is qualified.

## Scientific-provider compositions

General CI run 41849778171 resolved public MolSysMT 0.23.0 ABI3 build 0,
pandas 3.1.0 and NumPy 2.5.4. Three strict documentation examples fail on
Pandas4Warning from native bond normalization. MolSysMT #431 repairs those
deprecated inplace calls in `128a0bbb94e6804f5663e58a45313c77de1cc30d`;
the immutable public file predates that repair.

Local receiving verifies the original public MolSysMT archive SHA-256
`7ff102db1ceb3a6098b5c020193a2bef1c5eaa4dbcbc5a0b472ee2fa44a1971b` and
pandas 3.1.0 CPython 3.14 wheel SHA-256
`e4455cdcc03e42c17233184e8e4ea65c3ed2925d8b1d9d7dd8e6fced3f6e43c1`.
The wheel is unpacked into a task overlay, leaving the shared environment intact.
With public MolSysMT, the three selected examples yield two failures and one
pass in this local ordering: the warning mechanism is reproduced, not every
original CI outcome or its exact NumPy composition. All five documentation
tests pass with public MolSysMT/pandas 2.3.3, and separately with corrected
provider source/pandas 3.1.0. Strict warning filters and all examples remain.

## Bounded CI choice

`test_env.yaml` selects pandas 2.3.3 for the public-provider CI baseline. This
is an exact CI selection, not a runtime upper bound. Source-pair CI retains
its historical default provider and the same pandas default. Its explicit
`pandas_version` input permits corrected source receiving with 3.1.0; the actual
early shell guard rejects non-version and extra-argument inputs.

Owner: Viewer maintainers under #294; repaired-package delivery: MolSysMT.
Review by **2026-11-11**, or sooner when a compatible public provider containing
#431 arrives. Remove/revise the CI selection only after receiving that exact
package and rerunning strict examples and the applicable matrix with the new
pandas version. Do not advertise this interim route as compatibility with every
combination allowed by runtime metadata.

Local checks use `molsyssuite@uibcdf_3.14`, Python 3.14.7 and NumPy 2.4.6.
The public-provider path imports extracted payloads ahead of that existing
environment. This is not a fresh Conda solve, an unchanged copy of GitHub's
environment or a new public-artifact certificate. Hosted recovery is separate.

## Distribution reviews and remaining artifact

#292 receives an SPDX-capable Setuptools 77.0.3 minimum, aligned explicit
build/host/test/source routes and real wheel/sdist/rebuilt-wheel notice checks
with both 77.0.3 and development 84.0.0. See
[the resolved record](archive/build_backend_spdx_compatibility.md).

#293 receives immutable Conda provider v2.3.0
`87c70b1443d5f22d738ee3ddf812bdbe0152f6c2` through central delivery
`95f693be10c9205ab9b912cb53453710a207bf45`. Local noarch build/upload,
exact-file promotion, triggers, tests, labels and evidence retention remain.
No publisher is dispatched; see [the resolved record](archive/conda_provider_2_3_adoption.md).

#294 remains partial. Fresh-process current-Viewer probes receive handle info
and frame callbacks with both dependency compositions above, materializing the
Viewer class before importing MolSysMT. They do not reproduce DockingMT's exact
private composition or qualify browser behavior. The consumer initialization
failure remains unclassified; no import-order workaround is recommended.
A covering additive artifact needs its own scope, exact files and qualification.
Its delivery need not wait for every addon function. Both 1.0 publications
remain paused.

## Committed-head hosted review

On `afd61eb16024a43042095a450609774202167363`, general CI 41884513983
passes all four Linux minors with 3,396 tests each. The four macOS cells fail
only three new invalid-input regression cases; the previous strict Pandas4Warning
examples pass. Source pair 41884513993 passes Linux and Windows, with the same
macOS guard failures. Core browser 41884513801, experimental Qt 41884513672,
Ruff, suite policy and Conda governance pass independently.

[#295](archive/source_pair_pandas_guard_portability.md) resolves explicit
shell-independent input rejection on `793a92db`. Source pair 41899772394
passes Linux, Windows and macOS; three original ZIP hashes match GitHub and
all fourteen input guards pass in each JUnit without omissions. Its 10,173
Python passes and 141 other skips retain their three-host scope. General CI
41899772338 passes four Linux minors while its four macOS cells remain queued;
it is not described as overall success. The initial
[follow-up receipt](ci_guard_portability_receiving_20261104.json) retains exact
failure and local recovery evidence; the resolved record adds hosted hashes.
No publisher or installed-package qualification runs.
