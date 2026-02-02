from molsysviewer._private.exceptions import ArgumentError

def digest_mode(mode, caller=None):

    if isinstance(mode, str):
        if caller.startswith('molsysmt.file'):
            if mode in ['auto', 'read', 'write']:
                return mode
        if caller in {"molsysviewer.viewer.write_html", "molsysviewer.viewer.MolSysView.write_html"}:
            if mode in ["standalone", "lite"]:
                return mode

    raise ArgumentError('mode', value=mode, caller=caller, message=None)
