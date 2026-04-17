from molsysviewer._private.exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

nglview_representations = [
        "cartoon",
        "surface",
        "licorice",
        "ribbon",
        "line",
        "ball_and_stick",
        ]

def digest_representation(representation, caller=None):

    caller = normalize_viewer_caller(caller)

    if caller.startswith('molsysmt.thirds.nglview.'):

        if isinstance(representation, str):
            return representation
    elif caller in {
        'molsysviewer.viewer.MolSysView.new_region',
        'molsysviewer.viewer.new_region',
        'molsysviewer.viewer.MolSysView.new_region_from_active_selection',
        'molsysviewer.viewer.new_region_from_active_selection',
        'molsysviewer.active_selection.ActiveSelection.new_region',
        'molsysviewer.active_selection.new_region',
        'molsysviewer.selections.Selection.new_region',
        'molsysviewer.selections.new_region',
        'molsysviewer.viewer.MolSysView.make_regions_by',
        'molsysviewer.viewer.make_regions_by',
        'molsysviewer.whole.Whole.set_representation',
        'molsysviewer.regions.Region.set_representation',
        'molsysviewer.whole.set_representation',
        'molsysviewer.regions.set_representation',
        'molsysviewer.styles.StylesManager.apply',
        'molsysviewer.styles.apply',
        'molsysviewer.styles.StylesManager.representation_param_schema',
        'molsysviewer.styles.representation_param_schema',
    }:
        if representation is None:
            return representation
        if isinstance(representation, str):
            return representation

    raise ArgumentError('representation', value=representation, caller=caller, message=None)
