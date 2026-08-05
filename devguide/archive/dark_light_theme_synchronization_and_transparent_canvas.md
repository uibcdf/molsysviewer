# Dark/Light Theme Synchronization and Transparent WebGL Canvas for Exported Views

**DELIVERED and closed 2026-08-05.** Both halves of this proposal exist, under one
public argument, and the adopter who asked for it has chosen between them.

`view.export.html(background=...)` takes `"auto"` (default), `"transparent"`,
`"white"` and `"dark"`. What the proposal called Solution 1 is `"transparent"`.
What it called Solution 2 — a `postMessage` protocol between host and view — was
**not built, and is not needed**: checked in the installed
`pydata-sphinx-theme`, `postMessage`, `dispatchEvent` and `CustomEvent` appear
zero times, so there is no emitter and adopting it would have meant writing one
into every host's templates. What the theme *does* do is write `data-theme` and
`data-mode` on `<html>`, and a view is same-origin with the page embedding it, so
`"auto"` reads the host document directly and follows a `MutationObserver` on
those attributes. No cooperation, no protocol, no theme-specific attribute name.

**Two defects found by the adopter, both ours, both fixed** (`81b9d85f`):

- we copied the *page's* background, but what sits behind an embedded view is the
  container it was dropped into. `pydata-sphinx-theme` paints
  `.cell_output .text_html` `#222832` with padding over a near-black page, so the
  view sat in a grey rectangle and the transparent variant went grey altogether.
  Now the runtime walks out from `window.frameElement` to the first ancestor that
  paints anything;
- the exported stylesheet went out double-braced — an f-string escaped twice — so
  browsers discarded the rules that cover the page while the runtime boots. The
  tests were green because they asserted on substrings.

**MolSysMT's verdict, 2026-08-05**, on the three things we could not judge from
here: depth fog, molecular edges and the on-canvas controls over a light
background all read cleanly. They adopt `"transparent"` for their documentation
and recommend keeping both.

**The one property that separates them, reported by them and worth keeping:**
`"transparent"` transitions instantly when a site's theme switch is thrown,
because there is nothing of ours to change; `"auto"` shows a perceptible blink
while the observer fires and the canvas repaints. That is the difference between
being correct by construction and correct by reaction, and it is the reason to
prefer `"transparent"` on a site and `"auto"` for a file that travels alone.

---
**Status:** Proposed / Open for Review (2026-08-04)  
**Authors:** MolSysMT & MolSysViewer Integration Team  
**Origin:** Adoption feedback from MolSysMT documentation (`docs/index.ipynb` compiled via Sphinx / PyData Sphinx Theme).

---

## 1. Problem Statement

When static HTML views exported via `view.export.html()` are embedded inside external documentation websites (such as Sphinx using `pydata-sphinx-theme` or MyST-NB), host sites frequently offer dynamic Light/Dark mode toggles.

Currently, exported views render with a fixed, solid WebGL background color (e.g. solid white `#ffffff`). When a reader switches the host site to Dark Mode:
- The host page transitions to a sleek dark background (`#121212` / `#1a1a1a`).
- Embedded `<iframe>` elements remain bright white boxes, creating strong visual contrast and eye strain.

---

## 2. Proposed Architectural Solutions

To enable exported views to adapt seamlessly to host website color schemes, two complementary solutions are proposed:

### **Solution 1: Transparent WebGL Canvas Option (Recommended Primary Feature)**

#### **Mechanism**:
1. Add a `transparent: bool = True` parameter to `view.export.html()`.
2. When exporting, configure Mol*'s WebGL `Canvas3D` with `transparent: true` and set the HTML body and container CSS to `background: transparent;`.

#### **Benefits**:
- **Zero Runtime Overhead**: The WebGL viewport renders only the 3D molecular structures (cartoons, sticks, surfaces) over a null background.
- **Native CSS Inheritance**: The embedded `<iframe>` naturally displays the background color of the host page underneath. In Light Mode, it appears light; in Dark Mode, it automatically appears dark without requiring any JavaScript communication or page reloads.

---

### **Solution 2: PostMessage Theme Listener in `viewer.js`**

For cases where a solid background or theme-specific lighting/text colors are desired:

#### **Mechanism**:
1. Add a `window.addEventListener('message', ...)` handler in `viewer.js` listening for theme updates:
   ```javascript
   window.addEventListener('message', (event) => {
       if (event.data?.type === 'MSV_SET_THEME') {
           const isDark = event.data.theme === 'dark';
           const bg = isDark ? 0x121212 : 0xffffff;
           viewer.canvas3d.setProps({
               renderer: { backgroundColor: bg }
           });
       }
   });
   ```

2. Host documentation sites can attach a `MutationObserver` to their root `<html>` element (`data-theme="dark"`) and broadcast theme updates to all `<iframe>` elements on the page.

---

## 3. Impact & Recommended Implementation Order

1. **Phase 1**: Add `transparent=True` support to `view.export.html()`. This immediately satisfies 95% of documentation adoption needs with minimal effort.
2. **Phase 2**: Add the `MSV_SET_THEME` message handler in `viewer.js` for advanced theme synchronization.
