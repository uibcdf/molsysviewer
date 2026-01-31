from molsysviewer._private.exceptions import ArgumentError

def digest_view(view, caller=None):

    if caller == 'molsysviewer.new_view.new_view':
        return view

    from molsysmt.basic import get_form

    in_form = get_form(view)

    if in_form in ['molsysviewer.MolSysView', 'nglview.NGLWidget']:
        return view

    raise ArgumentError('view', value=view, caller=caller, message=None)
