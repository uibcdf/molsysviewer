def digest_tube_aspect_ratio(tube_aspect_ratio, caller=None):
    if tube_aspect_ratio is None:
        return None
    value = float(tube_aspect_ratio)
    if value <= 0.0:
        raise ValueError('tube_aspect_ratio must be positive')
    return value
