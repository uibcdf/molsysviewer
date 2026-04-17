from __future__ import annotations

from typing import Any

import numpy as np

from .. import pyunitwizard as puw


def quantity_value_in_unit(value: Any, unit_name: str) -> float:
    """Return the numeric value of *value* expressed in *unit_name*.

    Accepts plain floats/ints (returned as-is), puw units, or puw quantities.
    """
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    if puw.is_unit(value):
        value = puw.quantity(1.0, value)
    return float(puw.get_value(value, to_unit=unit_name))


__all__ = ["quantity_value_in_unit"]
