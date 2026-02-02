import inspect


def caller_name(skip=3):
    """Return the name of the function that called this."""
    return inspect.stack()[skip].function
