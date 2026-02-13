def digest_label(label, caller=None):
    if label is None:
        return None
    if isinstance(label, str):
        return label
    return str(label)
