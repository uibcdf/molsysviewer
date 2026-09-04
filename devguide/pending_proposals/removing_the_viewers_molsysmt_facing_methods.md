---
summary: Evaluate removing the viewer's MolSysMT-facing methods, now that msm.* answers on a view.
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

# Removing the viewer's MolSysMT-facing methods

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


## Correction — 2026-09-03 — §2's table was wrong about `contains`, and the conclusion moves

Prompted by the observation that `msm.contains(view)` and `msm.is_composed_of(view)` ought
to work as well as `msm.get(view)`. They do. **The table in §2 is wrong.**

It recorded `msm.contains(view)` as raising `NotWithThisFormError`. That measurement passed
`molecule_type="water"`, and the failure is the **argument shape, not the form** — the same
call fails identically on a plain `molsysmt.MolSys`:

| call | `view` | `MolSys` |
| --- | :-: | :-: |
| `msm.contains(obj, water=True)` | ✅ | ✅ |
| `msm.contains(obj, molecule_type="water")` | ❌ | ❌ |

So MolSysMT answers **four** of the five on a view, not two:

| | `view` | `region` | `whole` |
| --- | :-: | :-: | :-: |
| `msm.get` | ✅ | ❌ | ❌ |
| `msm.contains` | ✅ | ❌ | ❌ |
| `msm.is_composed_of` | ✅ | ❌ | ❌ |
| `msm.convert` | ✅ | ❌ | ❌ |
| `msm.extract` | ❌ | ❌ | ❌ |

`msm.extract(view)` fails for an unrelated reason, and it is theirs:
`form/molsysviewer_MolSysView/extract.py` was written with the *public* signature rather
than the form-level one the dispatcher calls, so it raises `TypeError` on every call.
Reported as `uibcdf/molsysmt#204`. It is not evidence about this proposal — once fixed, the
view column is complete.

### What this changes

**§2's second conclusion is withdrawn.** "The family is not uniformly replaceable even on
the view" rested on `msm.contains` failing. It does not fail. On a view, the whole family
is replaceable today except for one bug on their side.

**§2's first conclusion stands, and is now the whole objection.** `Region` and `Whole` are
still not MolSysMT forms, so `msm.get`, `msm.contains` and `msm.is_composed_of` all fail on
them. Removing these methods from the view alone would still split the API by object.

**The recommendation is unchanged, and better supported.** Option C — keep the methods, stop
digesting their `**kwargs` here — captures the prize without the split. Option A becomes
genuinely available the moment MolSysMT registers forms for `Region` and `Whole`, which is
now the *only* thing standing between this proposal and its full version. §7's second
question was the secondary one; it is the first one.


## Scope — 2026-09-03 — this was never only about `get`

Written as a question about one method, because that is how it arrived. The correction
above forced a re-measurement of the rest, and the answer is the same for almost all of
them. **Six of the seven MolSysMT-facing methods already work when called as `msm.f(view)`.**

| method | `msm.f(view)` | shape on our side |
| --- | :-: | --- |
| `get` | ✅ | `**kwargs`, attribute names, normalization table |
| `contains` | ✅ | `**kwargs`, attribute names, normalization table |
| `is_composed_of` | ✅ | `**kwargs`, attribute names, normalization table |
| `convert` | ✅ | `**kwargs`, but conversion options rather than attributes |
| `info` | ✅ | closed signature |
| `select` | ✅ | closed signature |
| `extract` | ❌ | closed signature — fails on `uibcdf/molsysmt#204`, their bug |

**They are not one family, and the difference decides what Option C can touch.** Only the
first three digest attribute names out of `**kwargs` and carry the normalization tables, so
only those three are what §3 measured as provably redundant. `convert` forwards `**kwargs`
too, but they are not attribute names. `info`, `select` and `extract` have closed
signatures whose arguments are digested like any other — nothing about them is duplicated
work.

So the proposal splits cleanly:

- **Option C applies to `get`, `contains`, `is_composed_of`.** That is where the redundant
  digestion, both normalization modules and the `region.get` allow-list defect live.
- **Option A applies to all seven**, and is blocked on the same single thing for all of
  them: `Region` and `Whole` are not MolSysMT forms.

Nothing here changes the recommendation. It widens what Option A would remove and narrows
what Option C touches, and it means the issue is about the surface, not the method.


## Correction — 2026-09-03 — the `Region`/`Whole` objection dissolves; nothing is blocked

Written while preparing a request to MolSysMT to register forms for `Region` and `Whole`,
which §2 named as the one thing standing between this proposal and its full version. The
request was not sent, because **neither needs a form.**

**`Whole` is the system.** `whole.get(element='atom', atom_name=True)` and
`msm.get(view, element='atom', atom_name=True)` return the same values. There is nothing
for a form to add: the whole *is* what `msm.get(view)` already answers about.

**`Region` is a selection.** Not by analogy — by construction. `Region.get` resolves
`self.atom_indices` and then calls `self._view.get(selection=scope, ...)`. It **is**
`msm.get(view, selection=region.atom_indices, ...)`, spelled differently:

```python
region.get(element='atom', index=True)
msm.get(view, element='atom', selection=list(region.atom_indices), atom_index=True)
# identical
```

They cannot diverge, including for a frame-dependent region, because both read the same
`atom_indices` attribute at the same moment.

And the `msm` route is **strictly better today**: it answers the 77 of 118 attributes that
§4's allow-list defect makes `region.get` refuse.

```python
msm.get(view, element='atom', selection=list(region.atom_indices), atom_name=True)
# ['N', 'CA', 'C', 'O', ...]   -- region.get(element='atom', name=True) raises
```

### What this changes

**§2's remaining conclusion is withdrawn.** It said removing these methods from the view
alone would split the API by object, because `msm.get(region)` and `msm.get(whole)` fail.
They do fail — and it does not matter, because neither is the call a user would make. The
region case is a `selection` argument and the whole case is the plain call.

**Option A is not blocked.** Nothing has to happen in MolSysMT first. §7's questions 1 and 2
are answered: no form work is needed, so the only open question is the first one — whether
`.get` on a viewer is *wanted* as ergonomics.

**That is now the whole decision, and it is a judgement rather than a measurement.** The
cost of Option A is real and is not technical: `view.<TAB>` in a notebook stops showing
these, and a user has to know MolSysMT exists and import it. For a viewer — often somebody's
first contact with the suite — that is a genuine loss to weigh against a smaller API, one
way to do a thing, and the removal of an entire class of drift.

The counterweight is that the convenience is partly illusory already: `region.get` refuses
two thirds of the attributes `msm.get` answers, and has since it was written.


## The third home — 2026-09-03 — this was decided once already, and half carried out

The options above were posed as *keep on the view* or *remove entirely*. There is a third
place, it already exists, and the project already put half of this family in it.

### `view.addons.molsysmt` is real, and MolSysMT owns it

`molsysviewer_molsysmt` is a package **inside the MolSysMT repository**, shipped by their
`pyproject.toml` (`include = ["molsysmt*", "molsysviewer_molsysmt*"]`) and registered as
`[project.entry-points."molsysviewer.addons"] molsysmt = "molsysviewer_molsysmt"`. Since
`molsysmt>=0.22.0` is a hard dependency here, it is always installed, always available and
enabled by default.

It already carries a `basic` namespace: **`add`, `append_structures`, `remove`, `set`**.

### The family is split down the middle, mutating from querying

| | on the view | in the addon |
| --- | :-: | :-: |
| `add`, `append_structures`, `remove`, `set` | — | ✅ |
| `get`, `contains`, `is_composed_of`, `convert`, `extract`, `info`, `select` | ✅ | — |

Complementary, no overlap. One family of MolSysMT operations, two owners, one line between
them that no document argues for.

### And `public_api.md` already states the policy

Under **Removed before 1.0** it records that `view.{remove, add, set, append_structures}`,
`view.whole.{...}` and the whole `molsysviewer.tools.basic.{get, select, info, convert,
contains, compare, is_composed_of}` family were taken out, and then says:

> Pure molecular-system reads should use `molsysmt.*(view, ...)`. Live molecular edits on an
> existing viewer are provided by the MolSysMT addon namespace: `view.addons.molsysmt.basic.*`.

**Both halves of what this proposal is circling are already written down as the project's
direction.** What is not settled is how far the first sentence reaches, and it admits two
readings:

*Narrow.* It is migration guidance for the removed free functions: "you used
`molsysviewer.tools.basic.get`; use `msm.get` now." It says nothing about `view.get`.

*Wide.* It is a statement about where reads belong, in which case `view.get`,
`region.get` and `whole.get` contradict a policy this repository has published since
b3b1fde9.

Settling that is the decision. It is not a measurement, and no further measuring will
produce it.

### The two questions are orthogonal, which is what makes this tractable

The discussion keeps binding together two things that can be decided separately:

**Who digests?** Answered, and not by taste: MolSysMT. Our copies accept exactly the same
105 of 118 attributes theirs do, with zero difference in either direction. Option C removes
that duplication — and both normalization modules, and the `region.get` allow-list defect —
**without touching a single name a user types**.

**Where does the name live?** View, addon, or nowhere. This is the ergonomics-versus-surface
judgement, and after Option C it is no longer urgent, because the maintenance cost that
makes it feel urgent will already be gone.

The addon does soften the ergonomic objection: `view.addons.molsysmt.basic.get(...)` is
still reachable by tab-completion from the view and needs no import. It is longer, and it
can be disabled — `msv.addons.disable("molsysmt")` — which would be an odd way to lose the
ability to read a system when MolSysMT is a hard dependency. If reads move there, that
disable path needs an answer.

### Recommendation, unchanged in substance

Do Option C, which is free. Then settle the narrow-versus-wide reading of the policy
sentence deliberately, as an API decision, with the addon as a third destination rather than
a binary. Nothing about that second step is blocked, and nothing about it is urgent once the
first is done.


## The namespace already exists, and it is `view.whole` — 2026-09-04

Raised as a different discomfort: too many bare functions at the first level of the API,
when `regions`, `annotations`, `measurements` and the rest live in namespaces. Should these
get a module too?

They already have one.

```python
view.get(element='atom', atom_name=True)        == view.whole.get(element='atom', atom_name=True)
view.select('molecule_type=="protein"')         == view.whole.select('molecule_type=="protein"')
view.contains(water=True)                       == view.whole.contains(water=True)
view.is_composed_of(water=True)                 == view.whole.is_composed_of(water=True)
view.info()                                     == view.whole.info()
```

All five verified identical. They must be: **the whole *is* the system**, so a question
asked of the view and the same question asked of its whole cannot differ. The top-level
five are a façade over `view.whole`.

`convert` and `extract` are the exception — `view.whole` has neither.

### What that settles

**No new module should be created.** Not because the addon covers it — that was the
instinct, and it is nearly right for a different reason — but because inventing `view.basic`
would be a *fourth* spelling of one operation, beside `msm.get(view, ...)`, `view.get(...)`
and `view.whole.get(...)`. A namespace introduced to reduce clutter that adds a name is a
net loss.

**The decluttering wanted here is cheaper than this proposal.** Removing the five bare reads
costs a user no capability at all: `view.whole.get(...)` already answers identically, needs
no import, and is still reachable by tab-completion. That is a strictly smaller change than
Option A, and it does not depend on MolSysMT, on the addon, or on settling the policy
sentence.

### And the clutter is mostly somewhere else

Measured on a live view: **24 namespaces, 73 bare methods, 14 properties.** The MolSysMT
seven are under 10% of the bare methods, and unlike many of the rest they are not duplicates
of a namespace — except that, per above, five of them are.

Verified duplicate façades beyond these: `view.play`, `view.pause` and `view.set_play_speed`
over `view.player`; `view.get_camera_snapshot`, `view.set_camera_snapshot`,
`view.reset_camera`, `view.zoom`, `view.focus_region` and `view.focus_selection` over
`view.camera`; `view.show` and `view.hide` over `view.whole`.

**That is the real answer to "too many loose functions", and it is a separate proposal from
this one.** It removes spellings without removing capability, which is the cheapest kind of
API reduction there is. This proposal, by contrast, is about who *owns* the operation, and
stays what it was: do Option C, then settle where the name lives.


## Option C, prototyped — 2026-09-04 — there is no `**kwargs` problem, there is a stale-copies problem

The open worry was that ArgDigest digests *everything* bound, with no way to digest the
named parameters and leave the `**kwargs` alone, so Option C looked like it needed a new
ArgDigest feature. It does not. The machinery already exists, and prototyping it found the
real obstacle, which is somewhere else entirely.

### The prototype

```python
@digest(strictness="ignore")          # a missing digester passes through silently
def get(self, element="system", ..., **kwargs):
    return msm.get(self._molsys, element=element, ..., **kwargs)   # no skip_digestion
```

`strictness` already accepts `ignore`/`silent`/`none`, so no ArgDigest change is needed:
once our attribute copies are deleted, their absence is silent for these forwarders while
every other call site keeps the `warn` default.

Measured over MolSysMT's 118 attributes: **105 accepted, 13 refused — identical to today.**
The one `No digester` warning that appeared is `n_nucleotides`, and `msm.get` emits it on
its own, so delegation surfaces a pre-existing gap of theirs rather than creating one.

### The obstacle, and it is §4 again

The full suite under the prototype: **1781 passed, one failure** —
`test_a_region_gets_the_same_renames_as_the_view`, with MolSysMT refusing `group_index` with
value `[True]`.

Instrumenting their digester shows it receives `[True]` already. Ours made it:

| caller | our `digest_group_index(True)` |
| --- | --- |
| `molsysviewer.viewer.get` | `True` |
| `molsysviewer.regions.get` | **`[True]`** |
| `molsysviewer.whole.get` | **`[True]`** |

This is §4's allow-list gap in its quiet form. There, a caller the list omits makes the
digester *raise*; here it makes it silently **wrap a boolean in a list**. Today that is
invisible, because `skip_digestion=True` means nobody looks at the value again. The moment
MolSysMT digests, it sees `[True]` and refuses.

### What this settles

**Flipping the flag alone breaks. Deleting our copies alone leaves warnings. The change is
both, together** — and then `strictness="ignore"` covers the second half with no new
machinery.

The failing test is therefore not an argument against Option C. It is the strongest argument
*for* it: it is the first thing to notice that our copies silently transform values into
shapes MolSysMT rejects, and it could only notice because the prototype stopped hiding the
result from the library that owns the answer.

**One boundary the prototype also drew.** Our directory holds 462 digesters against
MolSysMT's 391, and **234 are names they do not have** — `alpha`, `ambient`, `at_time_ms`,
`addon`, `tag`, and the rest of the viewer's own vocabulary. Those are ours and stay. Only
the MolSysMT attribute names are the duplicates worth deleting.
