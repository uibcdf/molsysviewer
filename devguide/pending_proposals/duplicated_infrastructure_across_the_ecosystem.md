---
summary: Duplicated infrastructure across the MolSysSuite repositories keeps costing the same defect twice.
issue: uibcdf/molsysviewer#70
status: open
opened: 2026-09-02
closed:
verification: measured
area: [process, build, tooling]
guard:
normative:
blocked_by: []
supersedes: []
---

# The same defect, found twice, three times in one day

**Reported:** 2026-09-02. Not from an audit that set out to find it — from noticing the
third instance and recognising the first two.

## What

Three defects on the same day shared one cause: infrastructure that exists in more than one
MolSysSuite repository, copied rather than shared, drifting apart.

1. **A CSS rule they had already found.** pydata-sphinx-theme gives notebook HTML outputs a
   light box under `html[data-theme="dark"]`, which reads as a grey frame around an
   embedded viewer and is invisible in light mode. MolSysMT carried the counter-rule,
   commented *Clean MolSysViewer Iframe Container Layout*. This project did not, and
   diagnosed it from scratch — through several wrong diagnoses — before finding their fix
   already written. `1a56742b`.

2. **A conda recipe defect reported to them, then found here.** `uibcdf/molsysmt#193`
   describes a recipe dropping floors the wheel declares. While preparing to ask them to
   act on it, this project turned out to have the same defect in four places. `b0888d9a`.

3. **A copied digester that drifted into a broken state.** `bond_length.py` had diverged
   into a version whose list branch could never return. Theirs is correct. `fd27e181`.

## How much is shared

Measured over the digester directories:

| | |
| --- | ---: |
| files here | 582 |
| files there | 391 |
| sharing a name | 346 |
| identical, ignoring package-specific imports | **145 (41%)** |
| diverged | **201 (59%)** |
| only here | 236 |
| only there | 45 |

The 201 is an **upper bound on drift, not a count of defects**. A digester can legitimately
differ between a toolkit and a viewer, and nobody has separated the two.

## Why

Each instance cost the time twice: once to find it, once to rediscover it. The third is the
worst shape — the copy did not lag behind, it *silently became wrong*, and would have
stayed wrong indefinitely, because nothing compares the two.

At least seven repositories share this kind of surface: digesters, conda recipes,
documentation theming, release workflows. Whatever the answer is, it is not specific to
these two.

## What is deliberately not proposed

**A solution.** Extracting the common part into a package, generating one repository's copy
from another, adding a drift check to CI, or accepting the duplication consciously are all
plausible and all have costs nobody has measured. Choosing now would be choosing before
understanding.

## What a decision would need first

1. **Separate legitimate divergence from drift** in those 201 files. Until that number
   exists, the size of the problem does not.
2. **The same measurement for the other shared surfaces**: conda recipes, CI workflows,
   documentation CSS.
3. **Decide what "shared" should mean here** — one canonical owner per surface, or a
   comparison that reports drift without forcing a merge. The second is cheaper and keeps
   each repository free to differ on purpose, which instances 1 and 3 both needed.

## What was refuted

**That vigilance is enough.** All three instances were found by people paying attention,
and all three were found *late* — after the cost had been paid twice. The third was found
only because an unrelated audit happened to read that file.
