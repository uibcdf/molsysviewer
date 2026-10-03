---
summary: Non-inline shared HTML exports silently omit the scene.
issue: uibcdf/molsysviewer#128
status: resolved
opened: 2026-10-01
closed: 2026-10-01
severity: high
verification: reproduced
area: [export, persistence]
guard: tests/test_html_scene_sidecar.py
normative:
blocked_by: []
supersedes: []
---

# Non-inline exports omit the scene

**Reported:** 2026-10-01, real Chrome inspection of the public HTML routes.

## What

```python
view.export.html(path, shared_runtime=directory, inline_messages=False)
```

The same real pentalanine view renders 62 atoms at frame 2 inline, and zero
atoms at frame 0 through this route. No scene sidecar exists. The latter page
nevertheless declares itself rendered. Both canvases were inspected in actual
headless Chrome with WebGL2 through SwiftShader, not a native GPU observation.

## How

`_build_lite_html` emits `[]` when messages are not inline. `_write_html_impl`
neither writes a separate snapshot nor supplies its URL to the runtime.

Write a versioned sidecar containing the canonical snapshot for shared exports
with `inline_messages=False`. Supply an escaped relative URL as boot data. The
TypeScript bootstrap reads and validates it before creating the viewer. Missing,
malformed and unsupported sidecars must reject rather than show an empty scene.

## Why

The public export argument silently discards the complete molecular scene.
Its output must be equivalent to the inline route. Self-contained exports
continue to embed all data, even when the caller passes this flag.

## What was refuted

The runtime itself is present and boots: the inline route using that same
installation renders the molecule. Shared exports served over HTTP still lose
the scene, so this is independent of the file-origin module restriction tracked
by `uibcdf/molsysviewer#39`.

## Resolution

The non-inline shared route writes `<html-name>.messages.json`, with format
`molsysviewer-messages`, version 1 and the complete current-state projection.
The HTML carries an escaped relative URL; the bootstrap fetches and validates
it before creating the controller. Inline exports remain one self-contained
file. An existing unrelated sidecar is refused without replacing it or the
existing HTML; a previously generated sidecar can be refreshed.

The six real-demo Python guards verify canonical content, frame selection,
source-state preservation, escaped filenames, ownership and self-contained
behavior. Actual Chrome opens both inline files and HTTP shared artifacts,
with third-party network requests blocked, and checks real Mol* scene cells
and independently reconstructed periodic hydrogen-bond endpoints on frames
2, 3 and 0. Missing data, invalid JSON, an unrelated format, unsupported
version and non-array messages all reject visibly without a success marker.
The writer ownership guard and reader schema guard were removed independently;
the regressions fail, and source bytes/runtime were restored afterward.
Shared-runtime `file://` origin restrictions remain uibcdf/molsysviewer#39.

Validation: full Python 2,330 passed / 20 skipped, JS units 293/293,
TypeScript checking, runtime build, core browser 36/36 and both performance
harnesses pass. The expanded artifact suite also passes separately after the
final schema mutation. Evidence uses the development checkout, not a frozen
release or published compatible Interactions provider.
