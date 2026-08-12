"""`iterations` is how many times a benchmark repeats its measurement.

At least one, or the benchmark divides by zero computing a mean — a `ZeroDivisionError`
inside a timing loop, which reads as a broken benchmark rather than a bad argument.

No upper bound, deliberately. A long benchmark is a choice, and the caller waiting for it
already knows.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_iterations(iterations, caller=None):
    if isinstance(iterations, bool) or not isinstance(iterations, int):
        raise ArgumentError("iterations", value=iterations, caller=caller,
                            message="expected a whole number of repetitions")
    if iterations < 1:
        raise ArgumentError(
            "iterations",
            value=iterations,
            caller=caller,
            message="a measurement needs at least one repetition",
        )
    return iterations
