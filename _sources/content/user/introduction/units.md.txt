# Units

Many MolSysViewer arguments accept values with units (for example, camera durations or distances).

MolSysViewer is part of the MolSysSuite ecosystem. In MolSysSuite, physical quantities are handled by
PyUnitWizard: a library that lets you pass quantities in many different “forms” (strings, Pint,
OpenMM units, Astropy units, Unyt, …) and converts them behind the scenes to the units and types
MolSysViewer expects.

If you want the full picture of what is supported (all input forms and parsing rules), see the
[PyUnitWizard documentation](https://www.uibcdf.org/pyunitwizard).

## What you can pass

In MolSysViewer, whenever an argument “has units”, you can usually pass:

- A string with a value and a unit, for example `"250 ms"`, `"4 angstroms"`, `"1.2 nm"`.
- A Pint quantity (if you use Pint directly).
- An `openmm.unit` quantity (if you use OpenMM).
- An Astropy quantity/unit (if you use Astropy).
- A Unyt quantity/unit (if you use Unyt).

If the dimensionality is compatible, MolSysViewer will accept it. If it is not compatible (for example, trying to pass
seconds where a distance is expected), you will get a clear error.

## What you get back

Internally, MolSysViewer configures PyUnitWizard in `molsysviewer/_pyunitwizard.py` so that:

- Returned quantities default to the **Pint** form (Pint `Quantity`).
- Standard units are:
  - `nm`, `ps`, `K`, `mole`, `amu`, `e`,
  - `kJ/mol`, `kJ/(mol*nm)`, `kJ/(mol*nm**2)`, `radians`.

This does not restrict what you can pass as input: you can still provide values in any compatible units.
Standardization only defines what MolSysViewer uses internally and what it returns by default.

## Customizing the default output quantities

MolSysViewer exposes a few configuration helpers so you can decide what you want to get back by default.
These settings affect how PyUnitWizard standardizes and formats quantities.

See `molsysviewer.config`:

```python
import molsysviewer as viewer

viewer.config.set_default_quantities_form("pint")
viewer.config.set_default_quantities_parser("pint")
viewer.config.set_default_standard_units(
    ["nm", "ps", "K", "mole", "amu", "e", "kJ/mol", "kJ/(mol*nm)", "kJ/(mol*nm**2)", "radians"]
)
```

This is also covered in the configuration section of the User Guide.

## A practical example

Some viewer methods accept unit-aware arguments. For example, `view.zoom(...)` uses:

- `duration` (a time, internally converted to milliseconds),
- `extra_radius` and `min_radius` (distances, internally converted to Å).

You can call it like this:

```python
view.zoom(
    selection="molecule_name == 'BENZENE'",
    duration="0.2 s",
    extra_radius="5 angstroms",
    min_radius="1 nm",
)
```
