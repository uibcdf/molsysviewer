---
summary: Add-ons declare four different things about their own maturity, in an untyped dict.
issue: uibcdf/molsysviewer#37
status: closed
opened: 2026-08-12
closed: 2026-09-04
verification: measured
area: [addons, docs]
guard:
normative:
blocked_by: []
supersedes: []
---

# What an add-on says about its own maturity

**Status:** the vocabulary is **decided** (below); adoption is each toolkit's, and none has
re-declared yet. **Raised:** 2026-08-12, from outside the project, so the paper can
distinguish *implemented integration* from *production-ready integration*.

The ownership half of the request is documentation and is done:
[`docs/content/developer/addons.md`](../../docs/content/developer/addons.md) now states
that MolSysViewer owns the host contract while each toolkit ships its own integration
inside its own repository, and the README table no longer implies a `molsysviewer-*`
distribution that does not exist. What is left is a decision.

## Measured, 2026-08-12

Four MolSysSuite add-ons, four different self-descriptions, in a free-form `meta` dict:

| Add-on | `status` | `rendering_ready` | other keys | Discovery |
| --- | --- | --- | --- | --- |
| `molsysviewer_molsysmt` | `"alpha"` | — | `domain` | entry point |
| `molsysviewer_topomt` | **absent** | `True` | `domain`, `checkpoint` | `KNOWN_ADDON_MODULES` |
| `molsysviewer_elastnetmt` | `"skeleton"` | — | `domain`, `repo` | `KNOWN_ADDON_MODULES` |
| `molsysviewer_pharmacophoremt` | `"skeleton"` | `True` | `domain` | `KNOWN_ADDON_MODULES` |

The request names two of these. Three more facts belong with them:

- **`alpha` is a third value** nobody defined against `skeleton`.
- **TopoMT declares no status at all**, so "audit its maturity" has nowhere to write the
  answer.
- **`AddonSpec` has no `status` field.** All of the above lives in `meta`, which is an
  untyped dict: nothing validates it, nothing lists it, and the host cannot show it. Two
  add-ons agreeing today is luck.

`rendering_ready` is the sharpest illustration of the gap. PharmacophoreMT declares
`status="skeleton"` **and** `rendering_ready=True`, which is not a contradiction — the
glyphs draw, the integration is unfinished — but nothing anywhere says that is what the
pair means.

## Decided 2026-08-12: declare the vocabulary, do not enforce it

**MolSysViewer defines the levels and what each one means. Each toolkit decides which one
its integration is in, and declares it. The host reads `meta["status"]` when present and
requires nothing.**

The two positions this rejects, and why. *Host contract* — a typed `status` on `AddonSpec`
that the host validates — would make MolSysViewer arbitrate the readiness of work it does
not own. *Toolkit's business*, with `meta` free-form and no shared words, is what produced
`skeleton`, `alpha` and nothing at all for the same question.

Nothing here is retroactive. Until a toolkit re-declares, the README shows what that
add-on says about itself today, including "undeclared". A table that reported a level
nobody claimed would be the defect this proposal exists to prevent.

### The levels

| Level | Means |
| --- | --- |
| `experimental` | It exists and is being shaped. Expect the API to change without notice, and expect gaps. Nobody should build on it. |
| `development` | The intended surface is present and the shape is settling. Usable knowingly; breaking changes are still normal and should be announced. |
| `beta` | Feature-complete for its declared scope, tested against a released MolSysViewer, and discovered on install. Breaking changes become exceptional. |
| `stable` | Its public surface is a commitment. Breaking it requires a deprecation cycle. |

`skeleton` maps to `experimental` and `alpha` to `development` — but that mapping is a
reading, not a re-declaration, and belongs to whoever owns each add-on.

### What separates `development` from `beta`

Three things, chosen because they are what the four add-ons actually differ in rather than
because a generic ladder wants four rungs. All three are checkable:

- **tested against the host** — MolSysMT's integration has 34 tests; the others have fewer
  or none;
- **discovered on install** — an entry point in the toolkit's `pyproject.toml`. Only
  MolSysMT declares one, and it is the difference a *user* notices first;
- **it draws what it claims** — what `rendering_ready` is reaching for. Keep the key: it
  answers a narrower question than `status` and is useful beside it, not instead of it.

An add-on that fails any of the three is at most `development`, whatever else is true of
it.

## Two things found on the way, for their owners

Neither is MolSysViewer's to fix.

1. **`elastnetmt` carries a stale `molsysviewer_elasticnetmt/` directory** beside the real
   `molsysviewer_elastnetmt/`. It has no top-level modules, only `__pycache__`, `adapters/`
   and `panels/` — leftover from the 2026-07-14 rename recorded in `changes_notes.md`. It
   is not discovered and not importable as an add-on; it is litter that will confuse the
   next reader.
2. **`elastnetmt` and `pharmacophoremt` do not depend on `molsysviewer`** in their
   `pyproject.toml`, while `molsysmt` and `topomt` do. Their add-on imports the host, so
   the dependency is real whether or not it is declared.

## Related

- `molsysviewer/addons.py` — `AddonSpec`, `KNOWN_ADDON_MODULES`, `ADDON_ENTRY_POINT_GROUP`.
- [`docs/content/developer/addons.md`](../../docs/content/developer/addons.md) — the host
  contract and the ownership statement.
- [`../archive/scene_object_owner_field.md`](../archive/scene_object_owner_field.md) — the
  related question of whether a scene object records which add-on drew it. **Resolved**;
  read it for how ownership was decided there before deciding maturity here.


## Amended and closed — 2026-09-04 — two levels, not four

**Decided: the vocabulary is `experimental` and `stable`. Nothing between them.**

This replaces the four-rung ladder above. That ladder is left in place rather than deleted
because the reasoning it records is still the reasoning that produced the amendment.

### What the reduction costs, stated because it is real

The four levels were not generic. `development` was separated from `beta` by three
checkable facts, chosen because they are what the add-ons actually differ in. Measured
again today, one of them still separates them cleanly:

| add-on | entry point in its own `pyproject.toml` |
| --- | :-: |
| `molsysviewer_molsysmt` | **yes** |
| `molsysviewer_topomt` | no |
| `molsysviewer_elastnetmt` | no |
| `molsysviewer_pharmacophoremt` | no |

With two levels, all four are `experimental`, and the vocabulary stops carrying the fact
that one of them is discovered on install and tested against the host while the others are
neither. That is a real loss of resolution.

### Why it is the right trade anyway

A level nobody can place themselves in confidently is worse than no level. `development`
and `beta` are exactly the two that require judgement about somebody else's roadmap, and
the evidence that four toolkits produced `skeleton`, `alpha`, `skeleton` and nothing at all
for one question is evidence that finer distinctions do not survive contact with four
separate owners. Two levels ask a question each owner can answer about their own work:
**is this a commitment, or is it being shaped?**

### The information the ladder carried does not disappear

It stops being a rung and becomes a fact declared beside `status`, which is where
`rendering_ready` already lived:

- `rendering_ready` — it draws what it claims;
- an entry point in the toolkit's `pyproject.toml` — discovered on install, and observable
  by the host without anyone declaring it;
- tests against the host — countable in the toolkit's own repository.

All three are checkable by looking, which a self-declared rung never was.

### The levels

| Level | Means |
| --- | --- |
| `experimental` | It exists and is being shaped. Expect the API to change without notice. Nobody should build on it. |
| `stable` | Its public surface is a commitment. Breaking it requires a deprecation cycle. |

`skeleton` and `alpha` both read as `experimental`. As before, that reading is not a
re-declaration: until a toolkit re-declares, the README reports what it says about itself
today, including "undeclared". Nothing here is retroactive and nothing is enforced — the
host reads `meta["status"]` when present and requires nothing.
