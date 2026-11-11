# molsysviewer/_depdigest.py

from ._private.exceptions import LibraryNotFoundError

LIBRARIES = {
    "imageio": {"type": "soft", "pypi": "imageio"},
    "imageio_ffmpeg": {"type": "soft", "pypi": "imageio-ffmpeg", "conda": "imageio-ffmpeg", "channel": "conda-forge"},
    "numpy": {"type": "hard", "pypi": "numpy"},
    "molsysmt": {"type": "hard", "pypi": None, "conda": "molsysmt", "channel": "uibcdf"},
    "anywidget": {"type": "hard", "pypi": "anywidget"},
    "pyunitwizard": {"type": "hard", "pypi": None, "conda": "pyunitwizard", "channel": "uibcdf"},
    "smonitor": {"type": "hard", "pypi": None, "conda": "smonitor", "channel": "uibcdf"},
    "depdigest": {"type": "hard", "pypi": None, "conda": "depdigest", "channel": "uibcdf"},
    "argdigest": {"type": "hard", "pypi": None, "conda": "argdigest", "channel": "uibcdf"},
}

MAPPING = {
    "molsysmt_MolSys": "molsysmt",
    "file_h5msm": "molsysmt",
    "file_pdb": "molsysmt",
}

SHOW_ALL_CAPABILITIES = True

EXCEPTION_CLASS = LibraryNotFoundError
DOC_URL = "https://www.uibcdf.org/molsysviewer"
