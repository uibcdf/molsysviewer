from molsysviewer._private.exceptions import ArgumentError

nglview_representations = [
        "cartoon",
        "surface",
        "licorice",
        "ribbon",
        "line",
        "ball_and_stick",
        ]

def digest_representation(representation, caller=None):


    if caller.startswith('molsysmt.thirds.nglview.'):

        if isinstance(representation, str):
            return representation
    elif caller in {'molsysviewer.viewer.MolSysView.new_region', 'molsysviewer.viewer.new_region'}:
        if representation is None:
            return representation
        if isinstance(representation, str):
            return representation

    raise ArgumentError('representation', value=representation, caller=caller, message=None)
