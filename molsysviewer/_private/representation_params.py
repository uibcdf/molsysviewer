"""Value contract for curated native renderer options, shared by public owners."""

import math
from numbers import Real

import numpy as np

from ..viewer.representations import _CURATED_PARAMETER_VALUES
from .argdigest._quantity import digest_length_quantity
from .exceptions import ArgumentError


def digest_curated_parameter(name, value, caller=None):
    schema = _CURATED_PARAMETER_VALUES[name]
    kind = schema["kind"]
    if kind == "boolean":
        if isinstance(value, (bool, np.bool_)):
            return bool(value)
        message = "expected a boolean"
    elif kind == "enum":
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in schema["values"]:
                return normalized
        message = f"expected one of {schema['values']}"
    else:
        number = value
        if "unit" in schema and not isinstance(value, (Real, bool, np.bool_)):
            from .._pyunitwizard import puw

            try:
                quantity = digest_length_quantity(value, name, caller=caller)
                number = puw.get_value(quantity, to_unit=schema["unit"])
            except ArgumentError:
                raise
            except Exception as error:
                raise ArgumentError(name, value=value, caller=caller, message="expected a scalar length") from error
        if isinstance(number, np.ndarray) and number.ndim == 0:
            number = number.item()
        minimum = schema.get("minimum")
        message = "expected a finite scalar"
        if "unit" in schema:
            message += f" in native {schema['unit']} coordinates, or a scalar length quantity"
        if minimum is not None:
            message += f" {'greater than' if schema.get('exclusive_minimum') else 'at least'} {minimum}"
        if isinstance(number, Real) and not isinstance(number, (bool, np.bool_)):
            try:
                number = float(number)
            except (OverflowError, ValueError):
                number = math.nan
            in_range = minimum is None or (number > minimum if schema.get("exclusive_minimum") else number >= minimum)
            if math.isfinite(number) and in_range:
                return number
    raise ArgumentError(name, value=value, caller=caller, message=message)


def normalize_curated_params(params, *, caller):
    """Keep advanced options intact; never leave a known curated value unchecked."""
    result = {
        name: digest_curated_parameter(name, value, caller=caller) if name in _CURATED_PARAMETER_VALUES else value
        for name, value in params.items()
    }
    if "alpha" in result:
        from .argdigest.argument.alpha import _digest_one_alpha

        # The shared digester also admits batches for shapes. One molecular
        # representation has a scalar opacity, including trusted Style paths.
        try:
            result["alpha"] = _digest_one_alpha(result["alpha"])
        except (TypeError, ValueError) as error:
            raise ArgumentError(
                "alpha", value=result["alpha"], caller=caller, message="expected one opacity in [0, 1]"
            ) from error
    return result
