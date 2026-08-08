# Migrate the standardizer to declarative alias tables

**Status:** proposed, deferred with the design settled. **Filed:** 2026-08-08.
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
