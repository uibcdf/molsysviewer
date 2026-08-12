# Home Page Governance Directives (`index.AGENTS.md`)

This file defines the micro-governance rules, design philosophy, and content constraints for the MolSysViewer home page ([`docs/index.ipynb`](index.ipynb)).

---

## 🎨 Design Philosophy & Aesthetic Directives

1. **Uncluttered & Spacious Layout:**  
   The home page must adhere to a clean, direct, and relaxed aesthetic ("less is more"). Avoid heavy grid dashboards, dense card matrices, or redundant navigation elements that duplicate the Sphinx sidebar.

2. **Linear Product-First Presentation:**  
   The page structure flows naturally:
   - Header: Centered logo, tagline, and essential release badges.
   - **`## Install it`**: Clean, one-liner installation instruction.
   - **`## Use it`**: Minimal, executable Python code snippet showing real 3D visualization capabilities.
   - **`## Citation`**: Paper and software citation tabs.
   - **Hidden Toctree**: Pure Sphinx navigation tree (`:hidden:`) powering the sidebar menu without polluting the main content area.

---

## 🔒 Frozen Content & Inviolable Requirements

No contributor or AI agent may alter or remove the following core elements:

1. **Brand Identity Header:**
   - Centered logo figure referencing `_static/logo.svg` with `60%` width.
   - Tagline: *"A Mol\*-powered interactive molecular viewer for Jupyter and structural analysis."*
   - **Badges Block Requirements:**
     - **Release Badge:** MUST match current package version (`v0.8.0` / `molsysviewer.__version__`); hardcoded stale version strings like `v0.7.0` are forbidden.
     - **License Badge:** MUST target `https://github.com/uibcdf/molsysviewer/blob/main/LICENSE`.
     - **Conda & Python Badges:** Conda channel (`uibcdf`) and supported Python versions (`3.11 | 3.12 | 3.13`).
     - **Zenodo DOI Badge:** Zenodo release DOI (`10.5281/zenodo.18072956`).

2. **Installation Block:**
   - Section heading: `## Install it`
   - Single command block: `conda install -c uibcdf molsysviewer`

3. **Usage Demonstration ("Use it"):**
   - Section heading: `## Use it`
   - Executable Python code demonstrating loading and displaying a molecular system (`1TRS` PDB ID or bundled demo):
     ```python
     import molsysviewer as msv

     view = msv.new_view('1TRS')
     view.show()
     ```
   - *Requirement:* Must use deterministic, small examples that run cleanly and render a high-quality 3D representation.

4. **Citation Section:**
   - Section heading: `## Citation`
   - Tabbed block (```{tabs}`) with tabs for **Software** (Zenodo citation & BibTeX link) and **MolSysSuite Ecosystem**.

5. **Hidden Sidebar Navigation Tree (`toctree`):**
   - Must maintain hidden toctrees referencing top-level sections:
     - `content/about/index.md`
     - `content/showcase/index.md`
     - `content/user/index.md`
     - `content/developer/index.md`
     - `api/index.md`
     - `content/ai_assistant.md`

---

## 🏷️ Section Anchors

- Top anchor: `(index-top)=`
- Install section anchor: `(index-install)=`
- Usage section anchor: `(index-use)=`
- Citation section anchor: `(index-citation)=`
