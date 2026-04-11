# BUG/UX: `view.whole.hide()` aggressively blocks region visibility

## Description
The `hide()` command on the global system (`view.whole.hide()`) prevents any individual region from being visible, even if those regions are explicitly shown or created after the hide command.

## Steps to Reproduce
1. Load a system.
2. Create a region (e.g., `nucleo`).
3. Call `view.whole.hide()`.
4. Call `nucleo.show()`.
5. **Observed Result:** The viewer remains completely empty.

## Technical Analysis
The library implements "hiding" via translucency (setting alpha to 0 for all structure components). The `hide_global` operation in `viewer.js` appears to apply this transparency to all components linked to the structure, effectively overriding the visibility or opacity of any child components (Regions). There is no "Z-order" or "Layer precedence" that allows a region to "punch through" the global transparency.
