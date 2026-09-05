PROFILE = "user"

SMONITOR = {
    "level": "WARNING",
    "trace_depth": 3,
    "capture_warnings": True,
    "capture_logging": True,
    "theme": "plain",
    "silence": ["pint", "networkx", "matplotlib"],
}

PROFILES = {
    "user": {
        "level": "WARNING",
    },
    "dev": {
        "level": "INFO",
        "show_traceback": True,
    },
    "qa": {
        "level": "INFO",
        "show_traceback": True,
    },
    "agent": {
        "level": "WARNING",
    },
    "debug": {
        "level": "DEBUG",
        "show_traceback": True,
    },
}

# SMonitor reads this module by attribute: `CODES` and `SIGNALS` are its contract, not
# local variables, so ruff reports them as unused imports. Removing this line renders every
# catalog message as an empty string -- the diagnostics keep their class and lose their
# text, which is the kind of failure a test only catches if it asserts on the message.
from molsysviewer._private.smonitor.catalog import CODES, SIGNALS  # noqa: F401,E402
