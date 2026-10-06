# Dependency contract audit

`pyproject.toml` is authoritative for runtime requirements and Python bounds.
`devtools/dependency_contract.toml` inventories their secondary routes without
duplicating versions: one noarch Conda recipe, development/test/docs environments
and the Python 3.14 source-pair environment. The latter supplies MolSysMT from
an exact checkout instead of the solver. The packaging environment is excluded
with a reason; its Packaging dependency is used by the metadata reader itself.

Run `python devtools/audit_dependency_contract.py`. It is read-only, does not
import MolSysViewer or scientific providers, and exits 1 on drift or unsupported
input. Recipes preserve all canonical constraints exactly. Environments may
strengthen simple version intervals; missing or weaker constraints fail. Empty,
duplicate, conditional, URL and unsupported dependency declarations fail closed.
New managed environments, recipes or sibling checkouts require classification.
Discovered inventory keys use repository-relative paths with `/` on every host;
native file access and installed-source paths retain their platform semantics.
Only `actions/checkout@...` steps declare workflow source checkouts. A
verification action's `repository` argument identifies external evidence and
must not be interpreted as a local installation route (`uibcdf/molsysviewer#136`).

After installing a controlled local source, run the same audit with
`--installed-source 'molsysmt=/path/to/checkout@FULL_SHA'`. It requires a clean
checkout at that commit, an installed version satisfying the public requirement
and local installation provenance pointing to that checkout. It does not import
the provider or verify its scientific capabilities. VCS URL installs are outside
this bounded local-checkout route and are refused.

The local-origin record identifies the installation path; it does not hash
installed Python or native code. CI must perform this check immediately after
installing the exact checkout. Artifact hashes and installed scientific/API
verification continue to belong to the separate candidate qualification.

The Conda workflow checks metadata before wheel construction and package upload.
The `dependencies` step runs first in the local release gate; metadata-only CI
runs independently of the scientific suite. Source-pair CI additionally checks
the installed exact provider before native-resource and scientific consumers.

Metadata consistency, source identity and installed API compatibility are
separate evidence. Preserve the installed-pair release checks and the compatible
published-provider gate for Interactions (`uibcdf/molsysviewer#114`). A controlled
source result neither changes public floors nor establishes a public installer
route. This local adoption is tracked by `uibcdf/molsysviewer#106`; it does not
declare platform-wide adoption of `uibcdf/moli#21`.

## Development and frozen source candidates

Python 3.14 source-pair CI runs on qualifying main pushes and PRs using the
same path filters and exact provider pin. Both development events run the
installed-source audit, native checks, installed-pair scientific tests and
complete Viewer suite. The manual event additionally verifies and locally
tags the declared frozen Viewer candidate, retaining its version/runtime/tag
identity assertions. A development check never qualifies an installed public
artifact or authorizes moving a published tag (`uibcdf/molsysviewer#137`).

The scientific source baseline also supplies the pinned provider's own runtime
floors and runs `python -m pip check` immediately after both installations.
This catches dependency metadata contradictions introduced by `--no-deps`;
it does not replace exact origin checks or behavioral qualification. Test
fixture dependencies such as RDKit belong to the test/development environments,
not to the mandatory Viewer runtime requirements (`uibcdf/molsysviewer#161`).
