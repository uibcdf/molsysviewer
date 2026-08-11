# molsysviewer/_argdigest.py

DIGESTION_SOURCE = "molsysviewer._private.argdigest.argument"
DIGESTION_STYLE = "package"
STRICTNESS = "warn"
SKIP_PARAM = "skip_digestion"

# Axis 1: the function argument contract. A closed signature is held to its own
# parameters; a function with **kwargs declares its domain in FUNCTION_SOURCE.
NORMALIZATION_SOURCE = "molsysviewer._private.argdigest.normalization"
FUNCTION_SOURCE = "molsysviewer._private.argdigest.function"
UNKNOWN_ARGUMENT = "error"
