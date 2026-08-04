# A standalone export mutates live widget state, and published notebooks carry it

**RESOLVED 2026-08-04.** The function this describes no longer exists.

Exports of both shapes are now built by `_build_lite_html`, which takes the
projection as an argument and writes it into the page. Nothing is assigned to the
live widget's synced state, so nothing is captured by `nbconvert`. The wider
finding in this file — that an embedded widget's state is dead weight in a
published notebook because the widget boots by asking Python — remains true and
is why `docs/execute_notebooks.py` strips it.

---

**Status:** confirmed and measured 2026-08-03. Not a correctness defect: nothing
renders wrongly. It makes any notebook that exports while it is being executed
carry hundreds of kilobytes of state that can never render.

**Affected contract:** `view.export.html(..., mode="standalone")`. Exporting is
an output operation and should not change the live scene's synchronized state.

## Symptom

`_build_standalone_html` (`molsysviewer/viewer/core.py`) begins with:

```python
self.widget.initial_messages = self._build_export_messages()
```

`initial_messages` is a `sync=True` trait, so this writes the whole current-scene
projection into the live widget's model. When the notebook is executed by
`nbconvert`, `jupyter-book`, `quarto` or anything else that captures widget
state, that projection is stored under `metadata.widgets`.

It is dead on arrival. An embedded MolSysViewer widget boots by asking Python for
the runtime (`widget.py`, `request_widget_runtime_source`) and gives up after
15 s, so a page with no kernel renders nothing from it. The state is pure weight,
and it is silent — no warning, and the page looks fine because the exported HTML
file is a separate artifact that works.

## Measured

Executed with `jupyter nbconvert --execute`, 1TCD:

| Notebook | Orphan state in `metadata.widgets` |
|---|---:|
| `new_view('1TCD')` + `show()` | **4.5 KB** (`_esm` bootstrap, 2.4 KB of it) |
| the same, plus `export.html(mode="standalone")` | **719 KB** (`initial_messages`) |

719 KB for one small structure. It scales with the scene, so a trajectory
notebook carries proportionally more. Reproduce by executing a notebook
containing those calls and reading `metadata.widgets`.

## Cause, and why the fix is small

The same function already solves this problem correctly for three other fields.
Immediately below the mutation it does:

```python
widget_state = self.widget.get_state(drop_defaults=False)
# Override toolbar visibility for the exported HTML without mutating
# the live widget trait in notebooks.
widget_state["show_controls"] = bool(include_controls)
...
widget_state["_esm"] = MolSysViewerWidget._viewer_js_source
widget_state["enable_popout"] = bool(include_popout)
```

`show_controls`, `_esm` and `enable_popout` are overridden **in the exported
dictionary**, deliberately, with a comment saying why. `initial_messages` is the
one field written to the live widget instead. Applying the pattern the function
already uses removes the defect at the source.

## Recommended correction

Build the export messages, place them in `widget_state` rather than on
`self.widget`, and leave the live widget untouched.

Check while doing it whether the export path needs `initial_messages` on the live
widget for any other reason — the live `ready`/reconnect path was canonicalized
in Phase 4b and no longer replays a journal, so it should not, but that is an
assertion to verify rather than assume.

## Acceptance

- After `view.export.html(..., mode="standalone")`, the live widget's
  `initial_messages` is unchanged from what it was before the call.
- The exported HTML still renders the full scene in a real browser: the
  projection must reach the file, only by a different route.
- Mutation: write the projection to the live widget again and the first test must
  go red.
- A notebook that exports while executing carries no scene-sized
  `metadata.widgets`.

## Related, and deliberately separate

`docs/execute_notebooks.py` has `strip_widget_state`, which removes this after
the fact for **this** repository's documentation. It is not shipped in the
package, so third parties publishing notebooks do not have it — and a sanitizer
downstream is not a substitute for not producing the state. Note also that its
default strips *all* widget state, including widgets that are not ours and that a
user may want rendered; the `keep-widget-state` cell tag is the opt-out.
