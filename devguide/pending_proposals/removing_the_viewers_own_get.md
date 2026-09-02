---
summary: Evaluate removing the viewer's own get(), now that msm.get(view) works.
issue: uibcdf/molsysviewer#71
status: open
opened: 2026-09-02
closed:
verification: measured
area: [api, argdigest, molsysmt]
guard:
normative:
blocked_by: []
supersedes: []
---

# Removing the viewer's own `get()`

**Proposed:** 2026-09-02. MolSysMT can already answer `msm.get(view, ...)`, so the
viewer's own `get` may be a second way to do one thing. Removing it would leave a smaller,
cleaner tool.

Everything below is measured on `alanine dipeptide` against MolSysMT's own 118-attribute
list, not reasoned from the source.

## 1. The premise is true, for the view

`msm.get(view, ...)` works, and works properly — not by accident of duck typing. MolSysMT
registers a real form, `molsysmt/form/molsysviewer_MolSysView/`, with `is_form`,
`extract`, `to_molsysmt_MolSys` and the three attribute getters. The viewer is a first
class form to them.

```python
msm.get(view, n_atoms=True)                                   # 22
msm.get(view, element='group', group_name=True)               # ['ACE', 'ALA', 'NME']
msm.get(view, selection='atom_name=="CA"', atom_index=True)   # [8]
```

And `view.get` is a pure forwarder — it digests, then calls
`msm.get(self._molsys, ..., skip_digestion=True)`. There is no viewer-specific behaviour
inside it to preserve.

## 2. Where the premise stops holding

The idea assumes one method is being removed. There are three, and they do not divide
evenly. `Region` and `Whole` have `get` too, and MolSysMT has **no registered form for
either**.

| | `view` | `region` | `whole` |
| --- | :-: | :-: | :-: |
| `obj.get(<attr>=True)` accepted, of 118 | **105** | **41** | **105** |
| `msm.get(obj)` | ✅ | ❌ | ❌ |
| `msm.contains(obj)` | ❌ | ❌ | ❌ |
| `msm.is_composed_of(obj)` | ✅ | ❌ | ❌ |

Two things follow.

**Removing `view.get` alone makes the tool less coherent, not more.** A user would call
`msm.get(view, ...)` but `region.get(...)`, because there is no `msm.get(region)` to move
to. One way to do a thing is the goal; this would produce two, split by object.

**The family is not uniformly replaceable even on the view.** `msm.contains(view)` raises
`NotWithThisFormError`. `view.contains` and `view.is_composed_of` are `get`-shaped and
would go the same way, and one of them has nowhere to go.

## 3. What the removal would actually buy

Less than it looks, on the axis one would expect.

Of the 463 surviving digesters, only **10** are alive solely because this family takes
`**kwargs` and forwards to `msm.get` — the simulation-parameter names (`kappa`,
`rigid_water`, `solvent_dielectric` and the rest). By the loosest bound, counting every
name that is a MolSysMT attribute and not a named argument anywhere, it is **99**. So the
digester directory would go from 463 to somewhere between 364 and 453. Real, but not the
reason to do it.

**The reason to do it is that the digestion itself is provably redundant.** Over the 118
attributes, `view.get` (digested here) and `msm.get` (digested by MolSysMT) accept
**exactly the same 105**, with **zero** difference in either direction. Our copies of
those attribute digesters do not add a single accepted or rejected value.

Two more things exist only to serve this family: both modules in
`molsysviewer/_private/argdigest/normalization/`, which scope MolSysMT's synonym and
bare-name tables to eight named callers, and the 294-line
`tests/test_argument_name_normalization.py` that keeps them honest.

## 4. A defect found while measuring, which argues the same way

`region.get` rejects **77 of 118** attributes that `view.get` and `whole.get` accept:

```python
region.get(element='atom', index=True)       # [0, 1, 2, ...]
region.get(element='atom', name=True)        # ArgumentError
region.get(element='group', group_name=True) # ArgumentError
```

The cause is exact. Forty digesters gate boolean values on a caller allow-list:

```python
functions_with_boolean = (
    'molsysmt.basic.get.get',
    'molsysviewer.viewer.get',
    ...
)
```

**Forty of them name `molsysviewer.viewer.get`. Not one names `molsysviewer.regions.get`.**
`Whole.get` escapes because it forwards to `view.get` rather than digesting; `Region.get`
digests on its own and is refused. The attributes that do work on a region are largely the
ones with *no* digester at all, which pass through unvalidated.

This is evidence for the proposal: three parallel `get` surfaces, each digesting against a
hand-maintained allow-list of caller names, is a shape that produces exactly this.

**It is tracked here and nowhere else, by decision (2026-09-02).** It could have been filed
as its own bug, and was not: under Option C it stops existing without being fixed, so
opening a report that the chosen fix would close by accident would put the same defect in
two queues. The consequence is that this proposal now carries a live defect as well as a
design question — if it is deferred past 1.0, `region.get` stays broken for 77 of 118
attributes, and §7's third question is what has to be answered first.

## 5. Options

**A — remove the whole `get` family from all three objects.** The coherent version of the
idea. **Blocked**: it requires `msm.get`, `msm.contains` and `msm.is_composed_of` to accept
`Region` and `Whole`, which means MolSysMT registering forms for them, plus
`msm.contains(view)` being fixed. Not ours to schedule, and not before 1.0.

**B — remove `view.get` only.** Rejected above: it buys the smallest share of the prize
and leaves the asymmetry of §2.

**C — keep the methods, stop digesting their `**kwargs` here.** Drop `skip_digestion=True`
from the forwarding call and let MolSysMT digest what it is about to consume anyway. §3
measures the behaviour change as nil across all 118 attributes. This retires the copied
attribute digesters, both normalization modules and their test, and it removes the
allow-list mechanism that causes §4 — without changing one line of anybody's notebook.

## 6. Recommendation

**Option C, and not before 1.0 ships.**

It captures the part of the prize that is real — the redundant digestion, the normalization
scaffolding, the allow-list defect — at no cost to the public API. Option A is the right
end state, but it depends on MolSysMT work that does not exist yet, and B is not worth
doing.

Nothing here is urgent enough to move during a freeze: 93 call sites in the docs, 23 in
the package, 16 in the tests. The §4 defect is separable and should be fixed on its own
schedule, whichever option is eventually chosen.

## 7. What has to be decided

1. Is `.get` on a viewer *wanted* as ergonomics, independently of redundancy? A notebook
   user reaches it by tab-completion and without importing MolSysMT. If the answer is yes,
   Option A is off the table permanently and C is the whole proposal.
2. Should `Region` and `Whole` become MolSysMT forms? That question is larger than this
   proposal and belongs with them.
3. Is §4 a bug fix (add `molsysviewer.regions.get` to 40 allow-lists) or is it another
   argument for deleting the copies? Under Option C it disappears without being fixed.
