"""Scope the public MolSysMT alias contract to the viewer's molecular queries."""
from argdigest import AliasTable
from molsysmt.attribute import get_argument_aliases

_contract = get_argument_aliases()
if _contract.get("schema_version") != 1:
    raise ValueError("Unsupported MolSysMT argument-alias contract.")

TABLES = []
for _caller in ("molsysviewer.whole.get", "molsysviewer.regions.get"):
    TABLES.append(AliasTable(applies_to=_caller, aliases=_contract["attribute_synonyms"]))
    for _element, _aliases in _contract["element_attribute_aliases"].items():
        TABLES.append(AliasTable(applies_to=_caller, when={"element": _element}, aliases=_aliases))
