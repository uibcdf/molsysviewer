from ...exceptions import ArgumentError


def digest_measurement_style(measurement_style, caller=None):
    if measurement_style is None:
        return None
    if isinstance(measurement_style, dict):
        return measurement_style
    raise ArgumentError("measurement_style", value=measurement_style, caller=caller, message=None)
