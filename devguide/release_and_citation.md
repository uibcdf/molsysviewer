# Release Citation and Zenodo Contract

This document is normative for MolSysViewer's citation and preservation lifecycle.
The operational package and runtime release procedure remains
[`docs/content/developer/releasing.md`](../docs/content/developer/releasing.md).

## Identifiers

MolSysViewer already has a working Zenodo family:

| Identifier | Role |
|---|---|
| `10.5281/zenodo.18072956` | stable concept DOI for MolSysViewer |
| `10.5281/zenodo.18072957` | version DOI for the archived `0.7.0` release |

The concept DOI is stable across releases. README badges, documentation landing
pages, `CITATION.cff`, and general project citations use it. Zenodo assigns a
distinct version DOI after ingesting each GitHub Release; use that DOI when a
paper or workflow must identify the exact archived source.

The historical `10.5281/zenodo.8092688` DOI belongs to a MolSysMT release. It is
not a MolSysViewer identifier and must not appear on current citation surfaces.

## Metadata authority

- `CITATION.cff` is the canonical user-facing citation record and powers GitHub's
  **Cite this repository** control. It owns title, authors, ORCIDs, release
  version, release date, concept DOI, license, and repository URL.
- `.zenodo.json` owns Zenodo-specific metadata. Because it exists, Zenodo's
  GitHub ingestion ignores `CITATION.cff`; shared fields must therefore agree.
- README, the documentation home page, the citation page, and the downloadable
  BibTeX are derived surfaces. They are not independent authorities.

## What is automated

Enabling MolSysViewer once in Zenodo's GitHub integration connects future
GitHub Releases to the existing DOI family. A pushed tag alone does not request
Zenodo ingestion. Publishing a GitHub Release archives its tagged snapshot and
creates a version DOI asynchronously.

Normal publication uses no Zenodo token and no additional deposition action.
Public verification uses Zenodo's unauthenticated records API. Direct deposits,
uploads, DOI reservation, and publication through the REST API require a token
and are recovery mechanisms, not a second normal path. Never use direct
deposition and GitHub ingestion for the same release.

Official references:

- [Enabling a GitHub repository in Zenodo](https://help.zenodo.org/docs/github/enable-repository/)
- [Archiving a GitHub Release](https://help.zenodo.org/docs/github/archive-software/github-upload/)
- [CITATION.cff precedence](https://help.zenodo.org/docs/github/describe-software/citation-file/)
- [.zenodo.json precedence](https://help.zenodo.org/docs/github/describe-software/zenodo-json/)
- [Zenodo REST API](https://developers.zenodo.org/)

## Preparing a release

Prepare metadata on the candidate before tagging:

```bash
python devtools/prepare_release.py X.Y.Z
python devtools/validate_citation.py --expected-version X.Y.Z
```

The preparation command updates release-specific fields in `CITATION.cff` and
the derived documentation and BibTeX surfaces. Review its diff.

**It updates files, not tests.** `tests/test_citation_release_tools.py` used to pin the
expected version as a literal, which passed for a year and then stopped the release gate
for 0.22.0 — the first release since it was written. It reads the version from
`CITATION.cff` now, so preparing a release no longer leaves a test behind. Anything else
added here that hard-codes the current version will spring the same trap, and only during
a release. It does not
create a tag, GitHub Release, Zenodo record, Conda package, or npm package.
The documented `X.Y.Z-rc.N` prerelease form is accepted as well.

Run the complete release gate described in the developer release guide. A
candidate commit must not use `[skip ci]`.

## A tag without a Release is a legitimate state

`0.22.0` is tagged and has no GitHub Release, on purpose. Publishing the Release starts
Zenodo ingestion and the Conda route check. A direct route builds and uploads;
a staged route requires a separate exact-file promotion after the Release.
Conda is the gate deferred to 1.0 — the
UIBCDF dependency channels are not frozen, so the artefacts would be built against
versions nobody has closed, and Zenodo would mint a DOI that does not come back.

The tag marks the code; the Release distributes it. They are separable, and separating
them is the honest move when the gate reports `BLOCKED` rather than `FAIL`. Tracked in
`uibcdf/molsysviewer#82`, so a tag with no Release is never a mystery someone has to
reconstruct.

## Publishing and verifying

After the exact candidate passes its gates:

1. create and push the version tag on that commit;
2. verify the matching npm runtime according to the developer release guide;
3. publish the GitHub Release, which starts Zenodo ingestion and the Conda
   route check; for a staged route, dispatch the exact SHA-256 promotion
   workflow and independently verify the public package record;
4. verify the Zenodo record:

   ```bash
   python devtools/verify_zenodo_release.py X.Y.Z
   ```

The `verify-zenodo-release.yaml` workflow performs the fourth step after a
release is published. The verifier checks the published state, concept and
version DOIs, declared version, repository identity, and the versioned source
archive. MolSysViewer's `.zenodo.json` declares repository-level related
identifiers, so the contract does not assume that Zenodo adds a `/tree/<tag>`
identifier. Delayed ingestion is not a reason to create a duplicate manual
deposit; rerun the verifier first.

## What the 0.23.4 paired release taught us

The 2026-09-25 release paired Viewer 0.23.4 with MolSysMT 0.22.4. Its
staging and public installed-pair matrices both passed 20/20 across five
platforms and Python 3.11–3.14. These are separate pieces of evidence: a
successful staging solve does not prove public-channel availability. The
shared paired-release policy belongs in `uibcdf/molsyssuite#27`; the local
operator procedure remains in
[`docs/content/developer/releasing.md`](../docs/content/developer/releasing.md).

For a future Viewer release, freeze the exact version and candidate commit
before the expensive build. Validate the **ordinary Python wheel's**
packaged `viewer.js` version before tagging; Conda and npm rebuild the bundle
and can conceal a stale source-tree asset (`uibcdf/molsysviewer#102`). A
correction to a staged package must use a new immutable build coordinate.
After the tag, verify the tag-triggered npm publication and CDN separately
from the GitHub-Release-triggered Conda route. A second npm publish on the
Release is an error, not an extra release step (`uibcdf/molsysviewer#104`).

The 0.23.4 promotion action uploaded the exact public noarch file, but its
duplicated final verifier exited 1 after finding the right URL; independent
public package queries and installations established availability. Do not
rerun a mutating promotion merely to change a badge
(`uibcdf/molsyssuite#48`). The release's bounded visible Qt and hosted E2E
exception is pre-1.0 only; a future 1.0 candidate must pass its strict
gate (`uibcdf/molsysviewer#100`).

Both Zenodo source records appeared after the initial 900-second verifier
window. The Viewer verifier subsequently passed for
[0.23.4](https://doi.org/10.5281/zenodo.22959304); the sole archived file is
`uibcdf/molsysviewer-0.23.4.zip` (23,694,420 bytes,
`md5:2cfe76a5ea9ec2894964926db81c2609`). A timeout during asynchronous
ingestion is a pending observation, not proof that a deposit failed. Confirm
the public record and file inventory before any DOI claim or recovery action
(`uibcdf/molsyssuite#49`). Zenodo did not archive the Conda/npm packages.

## Recovery

- Correct metadata before tagging and rerun the exact candidate gates.
- Never silently retag a published release.
- If ingestion is delayed, rerun verification.
- If Zenodo rejects a release, inspect the repository's integration state and
  metadata before considering manual recovery.
- Preserve an incorrect published record and use Zenodo's supported controls or
  support channel. Never repoint a DOI.
