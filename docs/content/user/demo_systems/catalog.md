# Demo catalog

| Key | System | Kind | Good for |
|---|---|---|---|
| `"dialanine"` | Alanine dipeptide | Single structure | Unit tests, label/region/measurement examples |
| `"1TCD"` | Triosephosphate isomerase (TIM) | Single structure | Protein homodimer; colour by property, H-bonds, ANM modes |
| `"181L"` | T4 lysozyme with benzene | Single structure | Protein + small-molecule ligand; pocket and pharmacophore demos |
| `"pentalanine"` | Pentalanine in explicit water | Trajectory (50 frames) | Trajectory playback, RMSF, movie export |
| `"chicken_villin_HP35"` | Chicken villin HP35 (solvated) | Trajectory | Folding dynamics, region annotation across frames |

## Loading a demo

```python
import molsysviewer as msv

# Returns a fresh MolSysView with the system already loaded
view = msv.demo["1TCD"]
view.show()
```

Each call to `demo[key]` creates a new independent view — no shared state
between calls.

## Which demo to use

- **For tests and quick API checks**: `"dialanine"` — smallest system, fast load.
- **For protein visualisation demos**: `"1TCD"` — well-studied, good size for colouring and overlay examples.
- **For ligand / pocket / pharmacophore demos**: `"181L"` — has a co-crystallised benzene in the binding site.
- **For trajectory and movie demos**: `"pentalanine"` or `"chicken_villin_HP35"`.

## Accessing the raw file path

```python
path = msv.systems["dialanine"]   # pathlib.Path to the bundled .h5msm file
```

This is useful when you want to load the system through a custom pipeline
or pass it to another tool such as MolSysMT.
