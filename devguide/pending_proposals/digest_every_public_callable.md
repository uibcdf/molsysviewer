# Every public callable must be digested

**Raised:** 2026-08-07, by the release owner, while declaring the first function argument
contracts: *"todo lo público debe ser decorado"*.

**Status:** proposal. The policy is decided; the work is not scoped or scheduled.

## The rule

Every public callable of MolSysViewer carries `@digest`. There is no second entrance to
the library that skips argument digestion.

## Why it matters, measured

Counted on 2026-08-07 over `molsysviewer/`, excluding `_private` and underscore-prefixed
names:

| | Count |
| --- | ---: |
| public callables **with** `@digest` | 286 |
| public callables **without** it | **515** |
| raw `ValueError` / `TypeError` / `KeyError` outside `_private` | **482** |

So roughly a third of the public surface is digested. The rest gets:

- **no value contract** — arguments reach the body unvalidated and unnormalized;
- **no function contract** — a mistyped keyword is silently discarded, the call runs with
  the default, and the caller receives a plausible wrong answer (this is the defect
  ArgDigest 0.10.0's axis 1 exists to prevent);
- **no catalogued diagnostics** — those 482 exceptions never reach SMonitor, so they carry
  no code, no caller, and no hint, which contradicts the diagnostics rules in
  [`smonitor.md`](../smonitor.md).

The machinery is not missing: `molsysviewer._private.argdigest.exceptions.ArgumentError`
already exists as a `CatalogException`. It is simply unused in those 482 places.

`scene.py` is the clearest illustration: **none of `SceneManager`'s 16 methods was
decorated**, so the whole `view.scene.*` surface was outside digestion.

## What the work actually is

Decorating a function is one line. The cost is elsewhere, and it is why this has not
happened by itself:

**Each new argument name needs a digester.** `STRICTNESS = "warn"` means an argument with
no digester emits `DigestNotDigestedWarning` on every call. Decorating a function whose
arguments are undeclared trades a silent hole for a stream of warnings.

Measured on the two methods done as the proving case: `set_lighting` and
`set_clip_planes` have seven arguments between them, and **six had no digester**. Writing
them was most of the work — and each one needed the semantics read out of the docstring
(intensity in `[0, 1]`, percentage in `[0, 99]`, percentage in `[0, 100]`, a non-negative
distance in scene units).

So the real unit of work is not "decorate a function" but "declare the arguments this
function introduces". Some will already exist; the long tail will not.

## Suggested approach

1. **Measure the argument surface first.** Collect the distinct argument names across the
   515 undecorated callables and subtract the ones with a digester. That number, not 515,
   is the size of the job.
2. **Work by module, not by function.** A module's arguments overlap heavily, so
   `layers.py` (60 undecorated) will need far fewer than 60 new digesters.
3. **Take the modules with a public surface first**: `layers.py`, `regions.py`,
   `addons.py`, `viewer/core.py`. The `viewer/panel_actions/` files are lower-level.
4. **Declare a function contract wherever a rule already lives in the body.** Grep for
   `raise ValueError` mentioning "at least one", "only one of", "both": each one is a rule
   that belongs in a contract, and moving it there upgrades the diagnostic for free.
5. **Do not decorate without digesters.** A module is done when its functions are
   decorated *and* its arguments are declared, not before.

## What was already done as the proving case

`SceneManager.set_lighting` and `SceneManager.set_clip_planes` are decorated, six
digesters were written (`ambient`, `diffuse`, `specular`, `near`, `far`, `min_near`), and
both declare `requires_any_of` contracts. Their two bare `ValueError`s are now catalogued
`MissingArgumentError`s naming the caller and the accepted arguments, and the redundant
runtime checks were removed.

`FUNCTION_SOURCE` and `UNKNOWN_ARGUMENT` are now set in `molsysviewer/_argdigest.py`, so
the contract mechanism is live for the whole library: **every closed signature is already
held to its own parameters**, decorated or not, which is the part that costs nothing.

## A gap this exposed in ArgDigest

`set_clip_planes` also enforces *"thickness requires near to be specified"*. That is a
**directional** requirement — if A then B — and `co_required` is symmetric: it fires when
some but not all of a group are present, so it would reject a valid call passing `near`
alone.

Two other candidates found while surveying MolSysMT have the same shape from a different
angle: rules conditional on a *value* rather than on presence (`if pairs=True then both
as_entity must be True`; `parallel=False is only compatible with num_threads in {None,
1}`). Neither is expressible today.

If this pattern keeps appearing, the missing capability is not another variant of
`co_required` but a way to say *"when this argument has this value, then…"*. That is new
design, not a gap to patch, and it should be raised in ArgDigest with the accumulated
examples rather than guessed at now.
