# Migrate the standardizer to declarative alias tables

**Status: done, 2026-08-11.** Filed 2026-08-08. The design below held. What it did not
anticipate is recorded first, because it is the more useful half.

## What the migration found

**The standardizer had never renamed anything.** It branched on
`caller == 'molsysviewer.viewer.MolSysView.get'`; ArgDigest builds the caller as
`<owner module>.<function name>`, and `MolSysView.__module__` is `molsysviewer.viewer`, so
the real string is `molsysviewer.viewer.get`. Measured by logging every call through it
over a full suite run: **4,674 digested calls, 210 distinct callers, zero matches** against
any of its four branches. `normalize_viewer_caller` changed the caller in **0** of them.

That was not cosmetic. `view.get`, `view.contains` and `view.is_composed_of` forward to
MolSysMT with `skip_digestion=True` — correctly, since the arguments are digested once, on
this side — so MolSysMT's own normalization never ran on them either. Nothing renamed
anything anywhere:

```python
view.get(element='group', index=True)   # KeyError: 'index'
view.get(element='group', name=True)    # ArgumentError on `name`
view.get(element='group', group_index=True)   # worked — the spelled-out form only
```

Both now work. The port is therefore a bug fix that happens to also be a refactor, and the
suite grew by 17 tests because **no existing test could have covered these spellings**:
they raised.

**Rule 3 was not ported, deliberately.** `mutation -> mutations` targets
`molsysmt.build.mutate.mutate`, which is digested under MolSysMT's configuration and
already carries that alias in their `caller_aliases.py`. It can never reach this library's
registry — confirmed by the same inventory. There is no `caller_aliases.py` here.

**The global-scope trap is real here too, and larger.** Declaring the synonyms for `*`
fails **132 tests** in this repository, against 76 in MolSysMT. Measured, not assumed.

**`normalize_viewer_caller` stayed.** The proposal's step 3 asked whether it had other
users: it has about twenty, every caller-aware digester. It is also a no-op on all 4,674
calls, which makes it dead weight rather than a mechanism — but removing it is its own
change with its own risk, and it is not this one.

## Evidence

- `tests/test_argument_name_normalization.py`, 17 tests, all of which fail against the
  code as it stood.
- Mutation 1, `NORMALIZATION_SOURCE` removed: 11 of 17 fail.
- Mutation 2, synonyms declared `applies_to='*'`: the two scope tests fail, and the full
  suite drops to 132 failures.
- Full suite after the change: 1,335 passed, 3 environmental skips, exit 0.

---

*The proposal as filed follows.*

**Filed:** 2026-08-08.
**Blocked on:** nothing. ArgDigest 0.11.0 already has everything this needs.

## What this is

`molsysviewer/_private/argdigest/argument_names_standardization.py` is 64 lines of
`if caller == ... elif caller == ...` that rename incoming keyword arguments before
digestion. ArgDigest now expresses the same thing as data, with `AliasTable`, and MolSysMT
has already been migrated the same way -- so this is a port of a solved problem, not a
design exercise.

Doing it removes the last piece of imperative argument handling from MolSysViewer, makes
the renames introspectable, and lets `describe_normalization` document them.

## Why it was not done in the session that filed this

The migration was started and stopped on purpose. `normalize_viewer_caller` rewrites the
caller name *before* the standardizer decides, and alias tables are declared against the
caller, so the question was whether the mixin call paths could be expressed declaratively
at all. Rather than guess, the answer was looked up:

> `argdigest/core/normalization.py:33` — "`applies_to` is an exact caller, an `fnmatch`
> pattern, or `"*"` for every caller."

So they can. `applies_to='molsysviewer.viewer.*.get'` covers the mixin methods that
`normalize_viewer_caller` folds into the historical namespace, and the resolution order
already prefers an exact caller over a pattern, and a longer pattern over a shorter one.

With that settled the work is mechanical, but it still needs the 1296-test suite run
behind it, which is why it is written down rather than half-applied. A half-migrated
standardizer is worse than an unmigrated one: two mechanisms deciding the same rename.

## The three rules to port

**1. Attribute synonyms**, for `molsysmt.basic.get.get`, `molsysviewer.viewer.MolSysView.get`,
`molsysmt.basic.contains.contains` and `molsysmt.basic.is_composed_of.is_composed_of`.

Point at `molsysmt.attribute._attribute_synonyms` rather than copying it, exactly as
`molsysmt/_private/argdigest/normalization/attribute_synonyms.py` does.

**Scope these to the callers that take attribute names.** Declaring them globally is the
obvious simplification and it is wrong: `atom_indices` is a synonym *and* a real parameter
elsewhere, so a global table renames a legitimate argument to one nothing declares. In
MolSysMT that mistake broke 76 tests. The reason belongs in a comment in the new module,
because the next person will have the same idea.

**2. The `{element}_{name}` expansion**, for `get`: `element='group'` plus `index=True`
means `group_index`.

Write the tables out, one `AliasTable` per element with `when={'element': ...}`. Do not
generate them from a template: several combinations do not exist -- there is no
`atom_order`, no `chain_order`, no `bond_name` -- and a template accepts them, producing an
attribute name nothing defines and an error far downstream. MolSysMT's
`normalization/get_element_names.py` derived its tables from the element list crossed with
the attribute catalogue; reuse that list rather than re-deriving it.

**3. `mutation` -> `mutations`**, for `molsysmt.build.mutate.mutate`. One entry.

## Steps

1. Add `molsysviewer/_private/argdigest/normalization/` with a module per rule, mirroring
   `molsysmt/_private/argdigest/normalization/`.
2. In `molsysviewer/_argdigest.py`, replace `STANDARDIZER` with
   `NORMALIZATION_SOURCE = "molsysviewer._private.argdigest.normalization"`.
3. Delete `argument_names_standardization.py`. Check whether `normalize_viewer_caller` in
   `helpers.py` still has other users; if not, it goes too.
4. Run the full suite. The renames are silent when they work, so the evidence that the
   port is faithful is the tests that exercise the renamed spellings -- confirm those
   exist before trusting a green run.

## Related

- `digest_every_public_callable.md` -- the other open argument-handling proposal here.
- MolSysMT commit "refactor(digestion): replace the standardizer with declarative
  normalization" is the worked example, including what went wrong on the way.
