# User Guide Governance Directives (`docs/content/user/AGENTS.md`)

This file defines governance rules for all user guide tutorials, conceptual overviews, and recipes under `docs/content/user/`.

---

## 🎨 Style and Tone

1. **User-Centered & Direct:** Speak directly to the user ("you"). Keep explanations concise and clear.
2. **"Why" Before "How":** Explain the motivation behind a feature before presenting code syntax.
3. **Executable Examples:** Every code example MUST be runnable and deterministic, using small bundled systems or remote PDB structures (e.g. `1TRS`, `pentalanine`).

---

## 🔒 Canonical Naming and Invariants

1. **View Variable:** The main `MolSysViewer` view instance MUST be named `view` (or `view_A`, `view_B`).
2. **System Variable:** The underlying molecular system object MUST be named `molsys`.
3. **Units:** Always state physical quantities with explicit units (e.g., Å, nm, ps, degrees, radians).
4. **Transparent Background:** 3D exported views for embedding in user docs MUST use `background="transparent"`.

---

## 📁 File Structure Policy

- Narrative index pages and conceptual guides MUST be `.md` (MyST Markdown).
- Tutorials demonstrating live Python execution and 3D rendering MUST be `.ipynb` notebooks.
