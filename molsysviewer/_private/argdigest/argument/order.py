from .._interaction_arguments import digest_positive_integer


def digest_order(order, caller=None):
    return digest_positive_integer(order, "order", caller)
