# Tight Initial Camera Framing and Auto-Reset for Exported Views

**CLOSED 2026-08-04: measured, and there is no defect.** Kept for the
measurements, which are the useful part.

The report describes accurately what a reader sees and inaccurately why.
Measured on the page the reporter was looking at
(`molsysmt/docs/_build/html/index.html`, barnase in a 946x480 embed, rendered in
a real browser): canvas 946 x 480, molecule 342 x 247 — **51 % of the height**,
36 % of the width.

**The framing is not specific to exports.** The same view at three canvas shapes
gives 51 %, 51 % and 52 % of the height. Mol\* fits the bounding sphere to the
viewport height, which does not depend on the frame's shape; what changes is how
much empty width surrounds it (36 %, 51 %, 71 % at 1.97:1, 1.40:1 and 1:1). A
notebook widget is framed identically and merely reads as fuller. §2.2 of this
proposal is therefore wrong: a script-generated export inherits no camera state
at all — there is no frontend to ask — and `export.html` is not involved.

**Mol\* is not wasting anything.** `Camera.targetDistance` places the camera at
`r / sin(fov/2)` (`camera.js:210`), so the bounding sphere exactly fills the
height. An earlier draft of this note claimed an unexplained 25 % on top of that.
That was an artifact of comparing against a sphere Mol\* does not use: its sphere
is built from the rendered geometry and includes the representation's radii, as
Diego pointed out. Checked against the coordinates: 51 % of the height implies a
projected extent of 24.0 A against a 23.4 A atom-centre sphere, while the
**minimum possible** extent over 4000 random orientations is 25.4 A. The
measurement is only consistent with a larger sphere. There is no gap.

**What the numbers do show**, and it is the one thing worth remembering: the
projected extent runs from **0.54 to 0.95** of the sphere diameter depending on
orientation, and this view sits at the narrow end. The camera starts from the
world axes, so the orientation is whatever frame the structure file happened to
carry. Barnase drew a bad one.

**The lever not taken.** `plugin.managers.camera.orientAxes()` aligns the
structure's principal axes to the screen, which would move that ratio towards
0.95 — up to ~1.75x more molecule — using Mol\*'s own machinery, without touching
the camera distance or the sphere, and so without any new risk of clipping on
rotation. It also spends the horizontal room a wide embed has going spare. Not
done, deliberately: it would change the default orientation of every view
everywhere, notebooks included, and nothing is broken today. Reopen from here if
the question returns.

**A fix written and withdrawn:** fitting the projected bounding *box* instead of
the sphere. Reverted once the sphere question was settled, because it would have
compensated by hand for a discrepancy that did not exist.

---
**Status:** Proposed / Open for Review (2026-08-04)  
**Authors:** MolSysMT & MolSysViewer Integration Team  
**Origin:** Adoption feedback from MolSysMT documentation (`docs/index.ipynb` embedding `1BRS_molecule_index_zero.html` inside a 480px iframe).

---

## 1. Problem Statement (What is the problem?)

When static HTML scenes exported via `view.export.html()` are embedded inside an `<iframe>` on external documentation websites (such as a 480px height container), the initial camera position leaves the molecular system appearing **disproportionately small and distant**.

The structure typically occupies only ~30–40% of the available viewport height, surrounded by a large amount of empty canvas space. Users must manually double-click or scroll the mouse wheel to zoom in and bring the protein to an optimal reading scale.

---

## 2. Root Cause Analysis (Why does it happen?)

Two underlying factors contribute to the distant initial framing:

1. **Mol* Upstream Bounding Sphere Margin**:
   When Mol*'s `Canvas3D` calculates the bounding sphere (`scene.boundingSphere.radius`) for a loaded molecular structure, it applies a conservative default padding factor to prevent clipping planes from truncating geometry during 3D rotation. This conservative margin results in a wide initial camera distance.

2. **Asynchronous Load & Unfocused Camera State at Export**:
   `view.export.html()` serializes `camera.state` exactly as it exists in the active view instance. During programmatic or headless scene construction, `export.html()` is often invoked right after creating representations without an explicit camera refocusing pass (`requestCameraReset()`). Consequently, the exported HTML inherits Mol*'s wide, un-focused initial camera bounds.

---

## 3. Impact on User Experience (How does it affect adopters?)

- **Suboptimal Visual Presentation**: Readers visiting documentation pages see a small molecule floating in a large empty viewport, reducing visual impact and legibility.
- **Manual Overhead for Authors**: Documentation authors currently have to manually tune camera coordinates or guess zoom distances before triggering exports.

---

## 4. Proposed Solutions (What are the possible solutions?)

### **Solution 1: Automatic Camera Auto-Reset on Export (Recommended)**

#### **Mechanism**:
In `view.export.html()`, include an automatic camera refocusing pass before serializing `camera.state`:
```python
def html(self, output_filename, title=None, include_controls=True, 
         shared_runtime=None, autofocus=True, padding=0.1, skip_digestion=False):
    if autofocus:
        self._view.camera.fit(padding=padding)
    # proceed with HTML export...
```

#### **Benefits**:
- **Zero Author Friction**: Every exported view automatically scales the molecular structure to fill ~80–90% of the viewport height.
- **Configurable Margin**: Authors can supply `padding=0.05` for ultra-tight views or `padding=0.2` for spacious views.

---

### **Solution 2: Client-Side Auto-Fit in `viewer.js`**

#### **Mechanism**:
In `viewer.js`, when an exported view is loaded inside a standalone HTML page or iframe, trigger a post-load camera reset pass once all representation geometries have finished building:
```ts
plugin.events.initialDrawComplete.subscribe(() => {
    if (autoFitOnLoad) {
        plugin.canvas3d?.requestCameraReset({ durationMs: 0, snapshot: { extraPadding: 0.1 } });
    }
});
```

---

### **Solution 3: Python Camera Fit API (`view.camera.fit()`)**

#### **Mechanism**:
Expose an explicit, top-level Python helper on the camera interface:
```python
view.camera.fit(padding=0.1)
```
This allows users to programmatically frame any target selection tightly before taking snapshots or exporting HTML files.

---

## 5. Recommended Action Plan

1. **Phase 1**: Add `view.camera.fit(padding=0.1)` to MolSysViewer's Python camera manager.
2. **Phase 2**: Enable automatic camera fitting (`autofocus=True`) by default inside `view.export.html()`.
