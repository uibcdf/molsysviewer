"""`renderer` is the GL renderer string a browser reports for itself.

Free text written by the driver — `"llvmpipe (LLVM 19.1.7, 256 bits)"`, `"ANGLE (NVIDIA
Corporation, NVIDIA GeForce GTX 1080, OpenGL 4.6)"` — so there is no set of values to
enumerate, and none is invented here. What is refused is the empty string and anything
that is not a string: `is_software_renderer` answers a yes-or-no question about a
renderer, and asked about nothing it would answer `False`, which reads as "hardware"
when the truth is that nobody knows. `ManagedRenderWorker._diagnose` already refuses to
ask that question; this makes the refusal the argument's own.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_renderer(renderer, caller=None):
    if isinstance(renderer, str) and renderer.strip():
        return renderer
    raise ArgumentError("renderer", value=renderer, caller=caller,
                        message="expected the GL renderer string a browser reports")
