# Proposal: preserve addon lifecycle for callable entry points

**Status:** pending.

## Context

MolSysViewer discovers addons from the `molsysviewer.addons` entry point group.
Today two entry point shapes are accepted:

```toml
molsysmt = "molsysviewer_molsysmt"
molsysmt = "molsysviewer_molsysmt:get_addon"
```

The module form is fully integrated: `GlobalAddonsRegistry.discover()` loads the
module and calls `register_module()`, so both the `AddonSpec` and lifecycle hooks
(`lifecycle`, `on_enable`, `on_disable`, `on_context_action`,
`on_active_selection_changed`) are discovered from the same module.

The callable form is only partially integrated: `entry_point.load()` returns the
callable, `_coerce_addon_spec(...)` obtains the `AddonSpec`, and `register(...)`
stores it, but lifecycle hooks from the callable's source module are not loaded.
An addon discovered as `package:get_addon` can therefore appear in the UI while
its lifecycle/context-action behavior is absent.

## Proposal

When an entry point loads to a callable, MolSysViewer should try to resolve the
callable's defining module and load lifecycle hooks from that module, matching
the behavior of `register_module()`.

Suggested behavior:

1. Keep accepting callables that return an `AddonSpec`.
2. After `_coerce_addon_spec(...)`, inspect `loaded.__module__`.
3. Import or read that module from `sys.modules`.
4. Call `_load_addon_lifecycle_from_module(module)`.
5. Register the spec with the recovered lifecycle.
6. Preserve the current behavior when no module or lifecycle is found.

## Why It Matters

Callable entry points are explicit and common in Python packaging, but addon
authors should not have to choose between explicit `:get_addon` metadata and
working lifecycle hooks.

Until this is implemented, addons with lifecycle hooks should prefer module
entry points:

```toml
[project.entry-points."molsysviewer.addons"]
myaddon = "molsysviewer_myaddon"
```

## Acceptance Criteria

- A test addon exposed as `fake_addon:get_addon` is discovered with its
  `on_enable`, `on_disable`, and `on_context_action` hooks registered.
- Existing module entry point behavior remains unchanged.
- Existing callable entry points without lifecycle continue to work.
