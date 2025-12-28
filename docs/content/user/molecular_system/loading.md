# Loading structures

MolSysViewer delegates loading to MolSysMT. `MolSysView.load` accepts any input
that MolSysMT can interpret (PDB IDs, strings, URLs, local files, or MolSys objects).

```python
import molsysviewer as viewer

view = viewer.MolSysView()

# PDB id
view.load("1CRN")

# PDB / mmCIF text
view.load(pdb_text)

# URL
view.load("https://files.rcsb.org/download/1CRN.pdb")

# MolSysMT MolSys
view.load(molsys)
```

Tips
- Call `view.show()` once to display the widget in Jupyter.
- Use `hide`, `show`, `isolate` to manage visibility; masks are applied via transparency in the frontend.
- Selections are MolSysMT-compatible (`syntax="MolSysMT"` by default).
