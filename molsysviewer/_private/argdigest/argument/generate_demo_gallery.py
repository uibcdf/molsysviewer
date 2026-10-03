from ...exceptions import ArgumentError


def digest_generate_demo_gallery(generate_demo_gallery, caller=None):
    if isinstance(generate_demo_gallery, bool):
        return generate_demo_gallery
    raise ArgumentError("generate_demo_gallery", value=generate_demo_gallery, caller=caller)
