# What an add-on says about its own maturity

**Status:** open. **Raised:** 2026-08-12, from outside the project, so the paper can
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

## The decision

**Is maturity part of the host contract, or each toolkit's own business?**

*Host contract* — `AddonSpec` gains a typed `status` with a closed vocabulary, the host can
refuse or warn, `view.addons.records()` reports it, and the four toolkits are updated. It
also means MolSysViewer starts having opinions about work it does not own.

*Toolkit's business* — `meta` stays free-form, and the README table is the only place the
levels are collected. Cheaper, and it drifts by construction, as it already has.

A middle position exists and is probably the right one: **declare the vocabulary, do not
enforce it.** Define the levels here, ask each toolkit to use them, and have the host read
`meta["status"]` when present without requiring it.

## If the vocabulary is defined, these are the distinctions that matter

Drawn from what the four add-ons actually differ in, not from a generic ladder:

- **does it draw?** — `rendering_ready` already tries to say this;
- **is its API stable?** — whether a user's script survives the next release;
- **is it tested against the host?** — MolSysMT's integration has 34 tests, the others have
  fewer or none;
- **is it discovered on install?** — the entry point is the difference between "installed"
  and "requires knowing the module name". Only MolSysMT declares one.

The last is worth separating because it is the one a *user* notices first, and it is a
one-line fix in each toolkit's `pyproject.toml`.

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
- [`post_1.0/scene_object_owner_field.md`](post_1.0/scene_object_owner_field.md) — the
  related open question of whether a scene object records which add-on drew it.
