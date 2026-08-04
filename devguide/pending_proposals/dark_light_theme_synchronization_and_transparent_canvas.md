# Dark/Light Theme Synchronization and Transparent WebGL Canvas for Exported Views

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
