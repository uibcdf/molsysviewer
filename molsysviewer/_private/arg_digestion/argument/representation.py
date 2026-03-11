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
        'molsysviewer.viewer.MolSysView.make_regions_by',
        'molsysviewer.viewer.make_regions_by',
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
