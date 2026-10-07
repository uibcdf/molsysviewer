# STATUS: `load()` modes and structure-append workflow

## Current status

The single-system modes are implemented. The later independent-system contract
is implemented under [#151](archive/multiple_system_loading_contract.md)
and passes the fixed 0.24.0 build 1 / MolSysMT 0.23.0 ABI3 build 0
qualification, including all sixteen public installed cells in `37587631519`.
The implementation report is resolved; see the
[current handoff](checkpoints.md#resume-in-one-page).

## Implemented now

`MolSysView.load(...)` currently supports:

- `mode="add"` (current default)
- `mode="replace"`
- `mode="append_structures"`
- `mode="auto"`

By default, `multiple=False` treats the input as one molecular system, including
complementary topology/coordinate forms. `multiple=True` explicitly interprets
the outer list/tuple as independent systems combined in one MolSys; that route
supports only `add` and `replace`. Batch and progressive loading preserve
source identity, labels and compact maps exposed through detached `load_blocks`
records. They create one source region per independent source when more than
one source is present. Regions preserve Unicode labels and remain linked by UID.
The normative contract is in [scene contracts](scene_contracts.md).

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
- same atom count + different topology -> `add`

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

The remaining broader trajectory/scale investigations do not reopen the
implemented bounded workflow. Mixed PDB/SDF loading, explicit topology/frame
compatibility, source maps and replay/session transfer have regression coverage
and exact staging evidence; old general coverage requests below describe the
earlier first version.

Earlier areas identified for follow-up:

- stronger test coverage for mixed file/form inputs
- broader replay/export coverage for multi-step loading stories
- refinement of the `auto` heuristic
- better classification of ambiguous inputs
- more explicit handling of structure-count compatibility in some cases
- better support and validation for large trajectory workflows

## Earlier improvement inventory

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

Scientific operations call the native MolSysMT backend directly. Compatible
staging qualification is complete; public provider/pair publication and final
1.0 qualification remain separate. Complete retirement of the remaining
legacy addon workflows is outside the bounded Interactions slice.
