# User presets

User presets let you define reusable styling rules in a JSON or YAML file and
load them into any viewer by name.

Use user presets when you need to apply the same multi-region recipes across
several notebooks or scripts without repeating the Python calls.

## Quick start

Create a `presets.yaml` file:

```yaml
polymer-clean:
  base: polymer-cartoon
  options: {}
  rules: []

pocket-highlight:
  base: polymer-and-ligand
  options: {}
  rules:
    - selection: 'group_name == "LIG"'
      representation: ball-and-stick
      params:
        color_scheme: element_cpk
```

Load and apply:

```python
import molsysviewer as msv

msv.config.load_user_presets("presets.yaml")

view = msv.demo["181L"]
view.whole.set_representation(preset="pocket-highlight")
view
```

## File format

The file is a top-level mapping: **preset_name → configuration**.

Each configuration has three keys:

| Key | Required | Description |
|---|---|---|
| `base` | yes | built-in preset to start from (`auto`, `polymer-cartoon`, etc.) |
| `options` | no | preset-level options dict (passed through) |
| `rules` | no | list of per-selection representation rules |

### Rule format

Each rule in `rules` applies a representation to a selection:

```yaml
rules:
  - selection: 'molecule_type == "water"'
    representation: spacefill
    params:
      color_scheme: element_cpk
      alpha: 0.3

  - atom_indices: [10, 11, 12, 13]
    representation: ball-and-stick
    params:
      color_scheme: chain_default
```

| Field | Type | Description |
|---|---|---|
| `selection` | string | MolSysMT selection expression |
| `atom_indices` | int list | explicit atom indices (alternative to `selection`) |
| `representation` | string | representation type name |
| `params` | dict | optional representation parameters |

## JSON format

Exactly the same structure in JSON syntax:

```json
{
  "pocket-highlight": {
    "base": "polymer-and-ligand",
    "options": {},
    "rules": [
      {
        "selection": "group_name == \"LIG\"",
        "representation": "ball-and-stick",
        "params": {"color_scheme": "element_cpk"}
      }
    ]
  }
}
```

## Loading

```python
import molsysviewer as msv

# JSON or YAML — detected by file extension
msv.config.load_user_presets("presets.yaml")
msv.config.load_user_presets("presets.json")
```

YAML support requires `pyyaml`:

```bash
mamba install pyyaml
```

## Applying

After loading, the preset name is available anywhere `preset=` is accepted:

```python
view.whole.set_representation(preset="pocket-highlight")
region.set_representation(preset="polymer-clean")

# Also works with styles:
from molsysviewer import Style
view.styles.apply(style=Style(user_preset="pocket-highlight"))
```

## Scope

User presets are global within the Python process — stored in
`molsysviewer.config.user_presets`. Call `load_user_presets` once per
session (e.g. at the top of a notebook) and all viewers created afterwards
can use the preset names.

## Related pages

- {doc}`presets` — built-in preset names.
- {doc}`styles` — higher-level `Style` object that wraps presets and adds focus overlays.
- {doc}`../introduction/project_configuration` — project-level `_molsysviewer.py` for named styles.
