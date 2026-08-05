# MolSysMT Adoption Report: End-to-End Infrastructure & Transparent Adapter Pattern for Static View Embedding

**Inbound report from the first external adopter, archived 2026-08-05 with the
exchange it opened.** Our reply is
[`molsysmt_adoption_response_2026_08.md`](molsysmt_adoption_response_2026_08.md);
the scaling analysis it prompted is still live at
[`../pending_proposals/molsysmt_docs_pipeline_analysis.md`](../pending_proposals/molsysmt_docs_pipeline_analysis.md),
because the decisions it puts to them are theirs and unanswered.

Read it knowing two of its statements were overtaken: their own code already
consumed the target variable and already raised, and §4.4's `skip_digestion=True`
was a workaround for a defect of ours, since fixed.

**Status:** Informational / First-Adopter Technical Verification (2026-08-04)  
**Authors:** MolSysMT & MolSysViewer Integration Team  
**Related Proposals:** [`embedding_views_in_external_documentation.md`](embedding_views_in_external_documentation.md)  
**Target Repository & Example:** `uibcdf/molsysmt` (`docs/index.ipynb`)

---

## 1. Executive Summary & Context

MolSysMT has fully adopted the static view embedding architecture defined in `embedding_views_in_external_documentation.md`. As the primary external adopter of MolSysViewer, this document presents a complete, end-to-end technical report of the infrastructure deployed in MolSysMT to publish interactive 3D WebGL scenes on static HTML websites (GitHub Pages) without active Python kernels.

Specifically, this report details the **Transparent Adapter Pattern** created in MolSysMT to reconcile two conflicting requirements:
1. **Tutorial Code Cleanliness**: Readers of the documentation must see 100% clean, idiomatic Python code (`msm.view(system)`). Infrastructure export or iframe embedding commands (`view.export.html`, `msv.tools.embed_iframe`) must **never** be exposed in visible tutorial cells.
2. **Static Web Compilation (No Python Kernel)**: Sphinx (`myst_nb`) web pages hosted on GitHub Pages cannot execute live `anywidget` models because no Python kernel is connected over WebSockets.

---

## 2. End-to-End Infrastructure Architecture

The embedding pipeline consists of **6 decoupled components** working in sequence:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. DEDICATED PRE-GENERATION SCRIPT                                      │
│    `docs/generate_static_views/1BRS_molecule_index_zero.py`            │
│    Executes `view.export.html(..., shared_runtime="docs/_static")`.    │
│    Output: `docs/_static/views/1BRS_molecule_index_zero.html` (148 KB).│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. BUILD-TIME SHARED RUNTIME HOOK (`docs/conf.py`)                    │
│    Sphinx `builder-inited` event runs `export_runtime_asset("_static")`.│
│    Extracts version-exact `viewer.js` (6.4 MB) into build dir.         │
│    Gitignored via `.gitignore` (`docs/_static/viewer.js`).             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. NOTEBOOK TUTORIAL STRUCTURE (`docs/index.ipynb`)                     │
│    - Cell 5 (Hidden tag `remove-input`):                              │
│      `molsysviewer_htmlfile = '_static/views/1BRS...html'`            │
│    - Cell 6 (Visible Tutorial):                                        │
│      `msm.view(molecular_system, selection='molecule_index==0')`       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. INCREMENTAL PRE-EXECUTION CLI (`docs/execute_notebooks.py`)         │
│    - Sets `MSM_VIEWS_FROM_HTML_FILES="True"`.                          │
│    - Runs `jupyter nbconvert --execute --inplace`.                     │
│    - Uses hybrid Git status (`st_mtime`) + commit timestamp tracking.  │
│    - Guarantees `"outputs": []` array on all code cells.               │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. DYNAMIC STACK FRAME INTERCEPTION (`molsysmt/basic/viewer/molsysviewer.py`)│
│    - Intercepts `msm.view()` when `MSM_VIEWS_FROM_HTML_FILES="True"`.  │
│    - Traverses stack frames (`for frame in stack():`).                 │
│    - Finds `molsysviewer_htmlfile` from hidden cell.                   │
│    - Delegates to `msv.tools.embed_iframe(htmlfile, path=nb_path)`.    │
│    - Returns `<iframe src="...">` into notebook cell output.           │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 6. SPHINX WEB BUILD & DEPLOYMENT (`make html`)                         │
│    - `nb_execution_mode = "off"` in `docs/conf.py`.                    │
│    - Translates cell output into `<iframe src="./_static/views/...">`. │
│    - Serves static page + cached shared `viewer.js` on GitHub Pages.   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Walkthrough & Code Implementation

### **Component 1: Pre-Generation Script (`docs/generate_static_views/`)**
Static views are generated ONCE by standalone Python scripts.  
File: [`docs/generate_static_views/1BRS_molecule_index_zero.py`](file:///home/diego/repos@uibcdf/molsysmt/docs/generate_static_views/1BRS_molecule_index_zero.py)

```python
from pathlib import Path
import molsysmt as msm

docs_dir = Path(__file__).resolve().parent.parent
static_dir = docs_dir / "_static"
views_dir = static_dir / "views"
views_dir.mkdir(parents=True, exist_ok=True)

# 1. Prepare system
molsys = msm.convert(msm.systems['Barnase-Barstar']['1brs.bcif.gz'],
                     selection='molecule_type=="protein"',
                     to_form='molsysmt.MolSys')

# 2. View and export scene to shared runtime folder
view = msm.view(molsys, selection='molecule_index==0')
view.export.html(str(views_dir / "1BRS_molecule_index_zero.html"), 
                 shared_runtime=str(static_dir))
```

---

### **Component 2: Build-Time Runtime Asset Hook (`docs/conf.py`)**
To prevent committing 6.4 MB JavaScript binaries into Git history, `viewer.js` is placed dynamically during Sphinx initialization.  
File: [`docs/conf.py`](file:///home/diego/repos@uibcdf/molsysmt/docs/conf.py)

```python
def _place_runtime(app):
    try:
        from pathlib import Path
        from molsysviewer.tools import export_runtime_asset
        export_runtime_asset(str(Path(__file__).parent / "_static"))
    except Exception as e:
        print(f"Warning: Could not export MolSysViewer runtime asset: {e}")

def setup(app):
    app.connect('builder-inited', _place_runtime)
```

And in `.gitignore`:
```gitignore
docs/_static/viewer.js
docs/_static/molsysviewer*
```

---

### **Component 3: Notebook Structure (`docs/index.ipynb`)**
The notebook separates infrastructure configuration from user pedagogy:

* **Cell 5 (Hidden via `"tags": ["remove-input"]`)**:
  ```python
  # Hidden cell: defines target static view file for this tutorial step
  molsysviewer_htmlfile = '_static/views/1BRS_molecule_index_zero.html'
  ```

* **Cell 6 (Visible Tutorial Cell)**:
  ```python
  msm.view(molecular_system, selection='molecule_index==0')
  ```

---

### **Component 4: Incremental Pre-Execution Script (`docs/execute_notebooks.py`)**
Notebooks are pre-executed locally before committing:
```bash
python docs/execute_notebooks.py -n 12 -r docs/
```
The script sets `os.environ["MSM_VIEWS_FROM_HTML_FILES"] = "True"` during execution and uses a hybrid Git status (`st_mtime`) + Git commit timestamp rule to avoid re-running unchanged notebooks.

---

### **Component 5: Dynamic Stack Frame Interception (`molsysmt/basic/viewer/molsysviewer.py`)**
When `msm.view()` executes inside `execute_notebooks.py`, the viewer adapter intercepts the call transparently.  
File: [`molsysmt/basic/viewer/molsysviewer.py`](file:///home/diego/repos@uibcdf/molsysmt/molsysmt/basic/viewer/molsysviewer.py)

```python
from inspect import stack
from pathlib import Path
import os

def view(molecular_system=None, selection='all', structure_indices='all', syntax='MolSysMT',
         skip_digestion=False):

    # 1. Check if executing in doc pre-execution mode
    if os.environ.get("MSM_VIEWS_FROM_HTML_FILES", "").lower() == "true":
        # 2. Traversal over caller stack frames (robust against decorators)
        for frame_info in stack():
            f_locals = frame_info.frame.f_locals
            htmlfile = f_locals.get('molsysviewer_htmlfile') or f_locals.get('nglview_htmlfile')
            if htmlfile is not None and Path(htmlfile).is_file():
                import molsysviewer as msv
                nb_path = f_locals.get('__file__', 'index.ipynb')
                # 3. Delegate to embed_iframe and return IFrame object automatically
                return msv.tools.embed_iframe(htmlfile, path=str(nb_path), skip_digestion=True)

    # 4. Standard interactive widget mode
    from molsysviewer import new_view
    return new_view(
        molecular_system=molecular_system,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=skip_digestion,
    )
```

---

### **Component 6: Static Web Build & Verification**
Sphinx compiles `docs/index.ipynb` with `nb_execution_mode = "off"`. The resulting `_build/html/index.html` renders:

```html
<div class="highlight-ipython3 notranslate"><div class="highlight"><pre><span></span><span class="n">msm</span><span class="o">.</span><span class="n">view</span><span class="p">(</span><span class="n">molecular_system</span><span class="p">,</span> <span class="n">selection</span><span class="o">=</span><span class="s1">&#39;molecule_index==0&#39;</span><span class="p">)</span>
</pre></div>
</div>
<div class="cell_output docutils container">
<div class="output text_html"><iframe src="./_static/views/1BRS_molecule_index_zero.html" width="100%" height="480px" style="border:none;"></iframe></div></div>
```

---

## 4. Key Takeaways & Feedback for MolSysViewer Developers

1. **`export_runtime_asset` & `shared_runtime` Architecture is Outstanding**:
   - The shared runtime design works seamlessly with Sphinx build hooks.
   - Bandwidth and page load times are dramatically reduced because `viewer.js` is cached across all documentation pages.
2. **`embed_iframe` Solves Path Bugs**:
   - Automatic relative path computation in `msv.tools.embed_iframe(filename, path=nb_path)` eliminated all nested subdirectory path errors (`../..`).
3. **Stack Traversal vs Rigid Indexing**:
   - When building third-party framework adapters, traversing caller frames (`for frame in stack():`) is significantly more robust than indexing a fixed stack depth (`stack()[2]`), as functions wrapped in `@digest` or `@signal` alter frame depth.
4. **`skip_digestion=True` in `embed_iframe`**:
   - When calling `msv.tools.embed_iframe(..., width="100%")`, passing `skip_digestion=True` ensures smooth execution across varying input formats.

---

## 5. Reference Verification Links in MolSysMT

- **Adapter Implementation**: [`molsysmt/basic/viewer/molsysviewer.py`](file:///home/diego/repos@uibcdf/molsysmt/molsysmt/basic/viewer/molsysviewer.py)
- **Sphinx Hook Configuration**: [`docs/conf.py`](file:///home/diego/repos@uibcdf/molsysmt/docs/conf.py)
- **Reference Notebook**: [`docs/index.ipynb`](file:///home/diego/repos@uibcdf/molsysmt/docs/index.ipynb)
- **Static Scene Script**: [`docs/generate_static_views/1BRS_molecule_index_zero.py`](file:///home/diego/repos@uibcdf/molsysmt/docs/generate_static_views/1BRS_molecule_index_zero.py)
- **Normative Architectural Specification**: [`devguide/notebook_compilation_and_visualization.md`](file:///home/diego/repos@uibcdf/molsysmt/devguide/notebook_compilation_and_visualization.md)
