---
summary: Whether a focus overlay survives a save depends on whether the user named it
issue: uibcdf/molsysviewer#67
status: resolved
opened: 2026-09-01
closed: 2026-09-01
severity: medium
verification: reproduced
area: [state, regions, styles]
guard: tests/test_state_focus_overlays.py::test_a_focus_overlay_survives_whether_or_not_the_user_named_it
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# One pattern, two questions

**Reported:** 2026-09-01, while scoping the focus slice of #38. The slice was expected to
be a design question — should a focus be saved at all? — and turned out to be a defect
underneath it.

## What

`styles.focus()` puts a visible representation on the scene, realised as a region plus an
entry in the styles manager's focus registry. Whether it survived a save depended on
something no user could predict:

| call | tag | in the document |
| --- | --- | --- |
| `styles.focus(representation=…)` | `focus1` (auto) | — |
| `styles.focus(representation=…, tag="mine")` | `mine` | kept, as a plain region |
| `styles.focus("chain-id", …)` | `chain-id` | kept, as a plain region |

Neither branch is right. The first loses a representation the user put on the scene and
left there. The second returns it demoted: `styles.focus_tags()` reports nothing and
`styles.clear_focus()` cannot remove what it can no longer see.

## How

`molsysviewer/viewer/regions.py`, `_TRANSIENT_REGION_TAG`:

```
^(?:(?:orientation|plane)-(?:region)?\d+|focus\d+)$
```

`focus\d+` matches the auto-generated form alone, which is where the asymmetry comes
from. But the naming was the symptom, not the cause. The pattern was used in three places
— state export, popup projection, region summary — to answer two different questions:

- **does the user manage this region directly?** Focus: no, it is managed through
  `styles.clear_focus`.
- **does this region outlive the operation that made it?** Focus: yes.

Orientation and plane regions answer *no to both*, so for as long as they were the only
cases that mattered the conflation was indistinguishable from correct. A focus overlay is
the first region that separates the two answers.

The focus registry was not serialised at all, which is the second half of the defect: even
the tags that survived came back without their overlay identity.

## Why

A focus overlay is visible scene state. Losing it on reload silently changes what the
scene shows. The surviving-but-demoted case is worse than losing it: the overlay is there,
it looks right, and the API that created it can no longer clear it.

## What was refuted

**That this was a design question.** It was scoped as one — whether a focus is worth
saving — and the answer to that question turned out not to matter, because the existing
behaviour was not a considered position. It saved a focus or dropped it according to how
the caller had spelled the call.

**That the fix is to remove `focus\d+` from the pattern.** That would have saved the
overlay and simultaneously promoted it into the region listings and the region summary,
which is the other half of what "transient" meant and is still true of a focus. The fix is
to split the predicate, not to loosen it.

## Resolution

Fixed in `739ef94c`, as part of #38's third slice.

`_EPHEMERAL_REGION_TAG` now names the scaffolding — orientation and plane — and is what
state export filters on. `_TRANSIENT_REGION_TAG` keeps its other meaning and its other two
call sites, so a focus overlay stays out of the listings. The document gains a `focus` key
holding the style registry, so a restored overlay is a focus rather than a region that
happens to look like one.

Contract A.5 is amended with the split and C.2 with the filter it now uses. Two stale
clauses in C.2 went with the amendment: the reader has not accepted v1 for some time, and
the document has since gained `structure`, `view` and `focus` as additive keys.

Guards in `tests/test_state_focus_overlays.py`, mutation-verified — five mutations, all
red, including one asserting the scaffolding still does not reach the document.
