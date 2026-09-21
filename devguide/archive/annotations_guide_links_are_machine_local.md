---
summary: The annotations guide links to Mol* through one developer's home directory.
issue: uibcdf/molsysviewer#92
status: resolved
opened: 2026-09-21
closed: 2026-09-21
severity: medium
verification: reproduced
area: [documentation, portability, testing]
guard: tests/test_devguide_links.py::test_every_relative_link_resolves
normative:
blocked_by: []
supersedes: []
---

# The annotations guide links through one developer's home directory

**Reported:** 2026-09-21, when the full local suite failed its developer-guide link
check on a checkout outside the original author's machine.

## What

`tests/test_devguide_links.py::test_every_relative_link_resolves` reports six broken
links in `devguide/annotations.md`. Every target begins with
`/home/diego/repos@others/molstar/`, so the architectural evidence resolves only on the
machine that supplied those absolute paths.

## How

The Markdown targets are filesystem paths rather than portable references. Replace them
with links to the corresponding files in the official `molstar/molstar` repository,
pinned to `v5.4.1`, the Mol* dependency line declared by MolSysViewer.

All six raw source targets were fetched successfully from that tag before the issue was
opened.

## Why

The guide cites these sources to justify the annotations taxonomy. Collaborators and CI
must be able to reach the same evidence without reproducing one person's checkout layout.
The current paths also keep the repository's full local test suite red.

## What was refuted

Linking to a repository-local `src_molstar/` tree was considered but rejected because no
such path exists in this checkout and the developer-guide link guard correctly requires
relative targets to exist. A moving `main` URL was rejected because the cited source can
change independently of the Mol* version this repository declares.

## Resolution

Resolved on 2026-09-21. All six machine-local targets now link to the same source
files in the official `molstar/molstar` repository at immutable tag `v5.4.1`, matching
the dependency line declared by MolSysViewer. Fetching the raw sources verified every
target before the replacement.

`tests/test_devguide_links.py::test_every_relative_link_resolves` is relevant because it
walks every Markdown link in the developer guide, resolves non-external targets relative
to their document and reports each missing path. The test reproduced all six failures
before the change and passes after the URLs became portable external references.
