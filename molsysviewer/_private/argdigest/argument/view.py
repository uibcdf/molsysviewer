from molsysviewer._private.exceptions import ArgumentError

def digest_view(view, caller=None):

    # These three are the callers for which `view` means "the viewer to load into", and
    # may legitimately be None: they build one when it is. Everywhere else `view` means
    # "the viewer to act on", and None is the error this digester exists to catch.
    if caller in ['molsysviewer.new_view.new_view',
                  'molsysviewer.loaders.load_molsysmt.load_from_molsysmt',
                  'molsysviewer.session.load_session']:
        return view

    from molsysmt.basic import get_form

    in_form = get_form(view)

    if in_form in ['molsysviewer.MolSysView', 'nglview.NGLWidget']:
        return view

    raise ArgumentError('view', value=view, caller=caller, message=None)
