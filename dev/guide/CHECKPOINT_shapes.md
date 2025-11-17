# MolSysViewer – Shapes / Transparent Sphere – Updated Checkpoint

**Last updated:** 17 February 2025
**Status:** Stable viewer; shapes frozen; logging still not working

---

## 1. Current functional state

### ✔ Jupyter viewer works (mostly)

* `v.show()` displays the Mol* canvas.
* The axes appear.
* The viewer is interactive and rotates normally.
* A PDB loaded with `v.load_pdb_string(...)` is displayed correctly.

### ✦ BUT:

* The widget **parpadea continuamente** (periodic re-rendering).
  → This suggests a **reactive loop** in the widget (SolidJS + anywidget), likely caused by the viewer being re-initialized repeatedly.

---

## 2. Shape system state

### ❌ Transparent sphere:

* The JS handler *runs* but **no log appears**.
* No sphere appears (expected).
* No console feedback from the handler.

### ❌ No Mol* API calls are active

We intentionally removed all calls to:

* `plugin.builders.shape`
* `plugin.managers.shape`
* `plugin.state.updateTree()`
* `ShapeRepresentation.create`
* or any Mol* transform / provider

…to keep MolSysViewer stable.

### ✔ Shapes code exists only as:

* a JS **stub** receiving `op: "test_transparent_sphere"`
* with a `console.log("MolSysViewer: received sphere request")` inside (but the log does *not* appear)

---

## 3. Known issues (important)

### ❗1. **Sphere logging does not appear**

Cause: Events are received by AnyWidget, but the inner handler never runs.

Most probable root causes:

* The JS message listener is not attached where we think it is.
* Or the code was treeshaken / removed by esbuild.
* Or the viewer.js bundle overrides the custom message handler.
* Or anywidget’s “render” function never rebinds handlers after refresh.

### ❗2. **The widget parpadea**

This is a critical UX issue:

* It appears MolSysViewer is being **re-rendered many times per second**.
* Very likely explanation:

  * SolidJS effect depending on `model.get("op")` or similar triggers render loops.
  * Or the viewer is re-created on each reactive update.

This explains why:

* logs do not appear (the handler is destroyed/rebound continuously),
* shapes cannot be added reliably,
* viewer “feels unstable”.

### ❗3. No path forward for shapes until core widget stabilizes

Mol* itself is stable.
The instability is in **our JS wiring / widget lifecycle**.

---

## 4. Why we freeze shapes on `main`

To avoid corrupting the stable behavior of MolSysViewer:

* The viewer must display molecules **reliably**.
* Shape support is foundational for TopoMT, PharmacophoreMT, etc.
* But adding shapes on top of an unstable widget will not work.

Therefore:

### ✔ Shapes are postponed.

### ✔ Only a no-op stub remains.

### ✔ Work will resume in a dedicated branch: `shapes-dev`.

---

## 5. What works and is stable

| Feature                     | Status                            |
| --------------------------- | --------------------------------- |
| MolSysViewer Jupyter widget | ✔ Stable                          |
| Canvas, axes                | ✔ Working                         |
| Load PDB                    | ✔ Working                         |
| Python → JS ops channel     | ✔ Working (at least for load_pdb) |
| test_transparent_sphere     | ✔ Message sent, ❌ not logged      |

---

## 6. Plan going forward (next branch `shapes-dev`)

### Phase A — Fix the widget

**Critical priority**

1. Stop parpadeo / re-renders

   * Inspect SolidJS effects
   * Ensure viewer is created *once*, not repeatedly
   * Ensure no reactive dependency triggers re-exec

2. Fix message-handling

   * Ensure custom handlers are attached once
   * Ensure they are not overwritten by the main viewer code
   * Confirm logs appear

3. Add robust “debug logging mode”

   * Force logs to appear regardless of tree-shaking
   * Print the plugin object reliably

### Phase B — Choose correct Mol* 5 shape API

After we stabilize the widget, we will inspect:

```js
console.log(plugin)
console.log(plugin.managers)
console.log(plugin.builders)
console.log(plugin.state.data)
```

and select the *real* supported API:

* `plugin.managers.shape`
* or `plugin.builders.shape`
* or a transform-based path
* or a custom provider

### Phase C — Implement the first real shape

* Transparent sphere at (x,y,z)
* Minimal representation
* Controlled alpha and color

### Phase D — Generalize shape system

* Alpha-spheres (TopoMT integration)
* Pocket surfaces
* Meshes
* Pharmacophore arrows
* Labels

---

## 7. Conclusion

The viewer is **operational**, but:

* the widget has lifecycle bugs (parpadeo),
* sphere handler does not run,
* shapes cannot be implemented until message routing and lifecycle are fixed.

