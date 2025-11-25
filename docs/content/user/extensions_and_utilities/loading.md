# Loading structures

Common entry points:

```python
import molsysviewer as mv

v = mv.MolSysView()

# Load from a PDB string
v.load_pdb_string(pdb_text)

# Load from URL (pdb/mmcif)
v.loaders.load_structure_from_url(url="https://files.rcsb.org/download/1CRN.pdb", format="pdb")

# Load from MolSysMT payload
payload = ...  # produced by molsysmt.convert or similar
v.load(molecular_system=payload)
```

Tips
- Call `v.show()` once to display the widget in Jupyter.
- Use `hide`, `show`, `isolate` to manage visibility; masks are applied via transparency in the frontend.
- Selections are MolSysMT-compatible (`syntax="MolSysMT"` by default).
