# Remaining work after the molecular-editing move + addon telemetry

Handoff note. Captures what landed and what is still open so a future session can
pick up without re-deriving context.

## What landed (both `main` branches, verified green)

- **molsysviewer** `main` (merge `9de5ebd4`): navigate-panel redesign + the
  **molecular-system editing move**. Editing semantics left the viewer:
  `view.{remove,add,set,append_structures}` and the duplicated
  `tools.basic` / `view.whole` surfaces were removed; the viewer keeps the public
  reconciliation primitive `view.apply_system_edit(new_molsys, atom_index_map=…,
  load_blocks="keep"|"collapse"|"append")`. Docs/notebooks migrated. Suite:
  **533 passed / 3 skipped**.
- **molsysmt** `main` (merge `9e5ef7a36`): the `molsysviewer_molsysmt` addon now
  **owns live molecular editing** (`view.addons.molsysmt.basic.*` over
  `apply_system_edit`) and gained **SMonitor telemetry** (breadcrumbs on the
  namespace methods + heavy adapters; `n_atoms` slow-signal extras;
  `context_extra` panel diagnostics with no silent failures). Addon suite against
  molsysviewer `main`: **114 passed**.
- **Coordination rule going forward:** the addon depends on the viewer primitive.
  Any future addon change that edits the molecular system must go through
  `view.apply_system_edit(...)`; the viewer must not regrow public mutators.

## Open work

### 1. Close the docs verification loop  *(most immediate — low risk)*

The editing docs were migrated but their correctness is **not test-covered yet**:

- Build the docs site and confirm no dead toctree links after deleting the
  `docs/content/user/tools/basic/` pages for removed functions.
- Execute the rewritten editing notebooks end-to-end
  (`docs/content/user/molecular_system/{add,remove,set,append_structures,
  molecular_system}.ipynb`) — they now use `view.addons.molsysmt.basic.*` /
  `view.load(mode=…)` and need the addon installed.
- Wire a notebook-execution CI gate so this cannot silently rot. A draft proposal
  for this exists but was **left untracked** in the feature worktree:
  `add_notebook_ci_guard_for_molsysmt_addon_docs.md` — recover it (from that
  worktree or from git history / the transcript) and commit it, or rewrite it.

### 2. Non-blocking execution for heavy addon operations  *(next feature)*

Heavy panel ops (minimize / solvate / contacts / hbonds / pbc) run synchronously
and freeze the kernel; the "running" spinner does not even render. Full proposal
already committed at
`molsysmt/devguide/pending_proposals/molsysviewer_molsysmt_nonblocking_heavy_operations.md`.
Recommended first slice: an MVP that runs one heavy adapter on a worker thread and
**applies the result on the main thread**, with an indeterminate spinner that
actually shows. (The telemetry added this session is the diagnostic; this is the
fix.)

### 3. Branch / worktree cleanup

The feature branches are merged and can be removed:

- `molsysmt`: `feature/addon-telemetry-and-editing-ownership` — safe to delete
  (local + remote).
- `molsysviewer`: `feature/navigate-panel-redesign` — this is also the branch of
  the working worktree `~/repos@uibcdf/molsysviewer__feature-navigate-panel-redesign`.
  Remove the worktree first (`git worktree remove …`) then delete the branch.

### 4. Slow-signal end-to-end (ops / manual)

The addon's `@signal` slow-signal instrumentation is verified analytically and via
console output; there is no automated test (SMonitor's slow-signal buffer needs a
configured handler). Confirm end-to-end by running with a SMonitor handler +
`SMONITOR_SLOW_SIGNAL_MS` set, on a large system.

### 5. Other standing proposals (unrelated to this session, still open)

- `molsysviewer`: `addon_entrypoint_callable_lifecycle.md`,
  `navigate_addons_restructuring.md`, `standalone_qt_interactive_backend.md`,
  `post_1.0`.

## Suggested order

Docs verification (1) + recover the notebook-CI proposal → branch cleanup (3) →
non-blocking MVP (2). Slow-signal (4) is opportunistic.
