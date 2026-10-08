# Source archive checkpoint — 2026-10-08

**Authorized by:** Diego, principal maintainer, accepting the proposed source-only
archive marker. **Tag:** `archive/pre-0.24.1-20261008`. The annotation names the
exact commit preserved by the checkpoint, its purpose and owner. This record
and the supporting configuration/guards belong to that commit; no self-referential
commit hash is invented in its files.

## Purpose and boundary

Preserve the integrated pre-1.0 source, including Movie #177 and style isolation
#149 corrections, public-promise/board reconciliation and remote #178 test-resource
integration. Reserve 0.24.1 as a possible later patch release. The archive marker
is not version 0.24.1, a package publication, a Release or source-preservation DOI.
The published 0.24.0 / MolSysMT 0.23.0 pair remains unchanged. Final 1.0 gates,
central Python admission and documentation retain their existing owners.

## Archive support

Adopt the immutable published `policy-v1.5.7` caller, whose central commit is
`f1ae1a043720e33493024d8afcab1e45375e42a2`, before creating the archive tag.
Its unconditional all-tag trigger includes names containing slashes. Versioningit
excludes `archive/*`; real Git regressions verify both the direct checkpoint
name and a nested archive name leave the package version unchanged. npm excludes
archive pushes and refuses archive/prerelease dispatch input before package
commands. Real negative Conda route requests also fail before creating output.

The early eleven targeted Git/version/publisher guards pass. The first Conda
negative-test attempt stopped at missing required `--github-output`, which did
not prove the intended rejection; the invocation was corrected and both events
now reach canonical-identity refusal with no output created. The policy CLI's
direct-script attempts encountered the development environment's `devtools`
namespace import collision. Running the unchanged exact policy as
`python -m devtools.scripts.check_repository` from its own checkout resolves its
own modules and passes conformance. No provider/tool source was patched.

The broader selected version/publisher/distribution/reporting/link check passes
204 cases. Dependency metadata audit, scoped Ruff and generated queue-index
checks pass. Hosted conformance and remote tag identity are verified before
closeout. These administrative/version checks do not certify an installed
0.24.1 package or replace scientific/visible-GPU/final-release qualification.
