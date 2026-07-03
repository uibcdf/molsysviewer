# Post-1.0 proposal: generated typing contract for `MolSysView` mixins

**Status:** deferred until after 1.0.

**Pre-1.0 status:** no pending runtime work remains in `molsysviewer`.

**Upstream dependency:** future `argdigest` support for machine-readable digester
contracts and generated stub emission.

## Resolved before 1.0

The original proposal mixed two independent issues:

1. Runtime caller/source resolution for decorated mixin methods.
2. Static typing of the shared `MolSysView` state and mixin API.

The first issue is resolved outside `molsysviewer`, where it belonged:

- `smonitor @signal` resolves the source module from the bound owner class for
  methods.
- `argdigest @digest` resolves the caller module from the bound owner class for
  methods.
- The previous `__name__ = "molsysviewer.viewer.core"` spoofing in viewer mixins
  has been removed.
- `normalize_viewer_caller()` remains intentionally small and only handles
  cross-namespace caller normalization.

There is no remaining pre-1.0 implementation work in `molsysviewer` for caller
resolution.

## Deferred issue

`MolSysView` is assembled from mixins that share runtime state installed by the
core class. This is valid at runtime, but static tools cannot fully infer the
available attributes and public methods across the composed class.

For pre-1.0, this is acceptable because:

- runtime behavior is covered by the real decorators and tests;
- `argdigest` validates public API inputs at runtime;
- the remaining problem is developer experience and static analysis, not
  user-visible correctness;
- adding handwritten inline `Protocol` classes would contradict the ecosystem
  preference for zero-intrusion typing around decorated APIs.

## Post-1.0 direction

The preferred solution is generated typing, not handwritten runtime scaffolding.

1. Extend `argdigest` digesters with machine-readable `accepts` and `returns`
   metadata.
2. Implement an `argdigest` stub-generation command, for example
   `argdigest build-stubs`.
3. Generate `.pyi` stubs for `MolSysView` exposing:
   - the public view API contributed by mixins;
   - shared core attributes used by mixins;
   - decorated method signatures after `argdigest` normalization.
4. Add a focused static typing check for the generated stubs.
5. Keep the runtime `.py` implementation low-intrusion and avoid duplicating
   method contracts manually.

## Acceptance criteria

This proposal can be closed after 1.0 when:

- `argdigest` can emit useful stubs from digester metadata;
- `molsysviewer` consumes or ships generated `MolSysView` stubs;
- a static checker validates the generated typing surface in CI or an equivalent
  developer workflow;
- no inline spoofing or handwritten compatibility layer is needed in the runtime
  viewer implementation.
