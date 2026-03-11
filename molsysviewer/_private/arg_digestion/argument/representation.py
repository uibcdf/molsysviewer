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
    elif caller in {
        'molsysviewer.viewer.MolSysView.new_region',
        'molsysviewer.viewer.new_region',
        'molsysviewer.viewer.MolSysView.split_by_chain',
        'molsysviewer.viewer.MolSysView.split_by_molecule',
        'molsysviewer.viewer.MolSysView.split_by_entity',
        'molsysviewer.viewer.split_by_chain',
        'molsysviewer.viewer.split_by_molecule',
        'molsysviewer.viewer.split_by_entity',
        'molsysviewer.whole.Whole.set_representation',
        'molsysviewer.regions.Region.set_representation',
        'molsysviewer.whole.set_representation',
        'molsysviewer.regions.set_representation',
    }:
        if representation is None:
            return representation
        if isinstance(representation, str):
            return representation

    raise ArgumentError('representation', value=representation, caller=caller, message=None)
