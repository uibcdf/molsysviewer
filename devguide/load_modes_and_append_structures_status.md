# STATUS: `load()` modes and structure-append workflow

## Current status

This front is no longer a pending proposal.

It is now implemented in a **first operational version** and should be treated
as an active capability with known limitations, not as an unimplemented idea.

## Implemented now

`MolSysView.load(...)` currently supports:

- `mode="add"` (current default)
- `mode="replace"`
- `mode="append_structures"`
- `mode="auto"`

### `mode="add"`

- performs additive atom/component loading
- updates `_load_blocks`
- creates automatic load-regions following the current additive-load rules

### `mode="replace"`

- resets the scene
- replaces `_molsys`

### `mode="append_structures"`

- performs structural append without adding atoms
- does not modify `_load_blocks`
- does not create automatic load-regions
- works on:
  - an already loaded system with structures
  - a topology-only `_molsys`, where the appended input defines the first
    structures
- raises a clear error on an empty viewer

### `mode="auto"`

Current first-version heuristic:

- empty viewer -> `replace`
- same atom count + no topology in the input -> `append_structures`
- same atom count + matching topology -> `append_structures`
- different atom count -> `add`

This is intentionally conservative.

## Why this should not remain under `pending_proposals`

The core behavior is already present and tested.

What remains is:

- broader coverage
- refinement
- performance work
- larger-input validation

Those are follow-up tasks, not grounds to keep this front listed as pending.

## Known limitations

The current implementation should be considered a **first working version**.
It is useful and operational, but not yet the final design.

Known areas that still need work:

- stronger test coverage for mixed file/form inputs
- broader replay/export coverage for multi-step loading stories
- refinement of the `auto` heuristic
- better classification of ambiguous inputs
- more explicit handling of structure-count compatibility in some cases
- better support and validation for large trajectory workflows

## Important next improvements

### 1. Larger trajectory support

This front should be tested and improved for large trajectories.

In particular, we should evaluate:

- whether the current append path scales well enough
- whether repeated full viewer rebuilds remain acceptable
- whether a lighter incremental path is needed for large appended trajectories

### 2. Better tests

The current implementation has targeted regression coverage, but it still needs:

- larger-system tests
- trajectory-oriented tests
- file-driven tests where practical
- more explicit topology-only and mixed-form tests

### 3. `auto` refinement

The current `auto` behavior is acceptable as a first version, but it should be
revisited after more real workflows are exercised.

## Relationship to the MolSysMT integration front

This status document only covers the loading surface.

The broader MolSysMT integration front is still separate and remains pending.
