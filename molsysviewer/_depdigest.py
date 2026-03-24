# molsysviewer/_depdigest.py

from ._private.exceptions import LibraryNotFoundError

LIBRARIES = {
    'numpy': {'type': 'hard', 'pypi': 'numpy'},
    'molsysmt': {'type': 'hard', 'pypi': 'molsysmt'},
    'anywidget': {'type': 'hard', 'pypi': 'anywidget'},
    'pyunitwizard': {'type': 'hard', 'pypi': 'pyunitwizard'},
    'smonitor': {'type': 'hard', 'pypi': 'smonitor'},
    'depdigest': {'type': 'hard', 'pypi': 'depdigest'},
    'argdigest': {'type': 'hard', 'pypi': 'argdigest'},
}

MAPPING = {
    'molsysmt_MolSys': 'molsysmt',
    'file_h5msm': 'molsysmt',
    'file_pdb': 'molsysmt',
}

SHOW_ALL_CAPABILITIES = True

EXCEPTION_CLASS = LibraryNotFoundError
