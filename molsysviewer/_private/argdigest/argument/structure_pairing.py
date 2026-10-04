from ...exceptions import ArgumentError


def digest_structure_pairing(structure_pairing, caller=None):
    if structure_pairing is None or structure_pairing == "by_index":
        return structure_pairing
    raise ArgumentError(
        "structure_pairing", value=structure_pairing, caller=caller, message="expected None or 'by_index'"
    )
