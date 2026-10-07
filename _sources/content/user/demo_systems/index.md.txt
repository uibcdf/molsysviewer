# Demo systems

MolSysViewer ships with a small set of built-in molecular systems useful for
examples, tests, and quick experiments.  They are available through the
`molsysviewer.demo` dictionary — each access returns a fresh `MolSysView`
already loaded with the system.

```python
import molsysviewer as msv

view = msv.demo["dialanine"]
view.show()
```

The same systems are also accessible as raw file paths via `molsysviewer.systems`
when you need to load them yourself:

```python
path = msv.systems["dialanine"]          # pathlib.Path to the .h5msm file
view = msv.new_view(path)
```

```{toctree}
:hidden:
:maxdepth: 2

catalog
```
