# molsysviewer/_argdigest.py

DIGESTION_SOURCE = "molsysviewer._private.argdigest.argument"
DIGESTION_STYLE = "package"
STANDARDIZER = "molsysviewer._private.argdigest.argument_names_standardization:argument_names_standardization"
STRICTNESS = "warn"
SKIP_PARAM = "skip_digestion"

# Axis 1: the function argument contract. A closed signature is held to its own
# parameters; a function with **kwargs declares its domain in FUNCTION_SOURCE.
FUNCTION_SOURCE = "molsysviewer._private.argdigest.function"
UNKNOWN_ARGUMENT = "error"
