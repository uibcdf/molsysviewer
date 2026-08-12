"""`feature` is a TopoMT feature object handed to `shapes.add_topomt_feature`.

MolSysViewer does not import TopoMT and must not start here: the add-on contract is that
a toolkit's objects arrive as objects, and the host recognises them by shape rather than
by type. So this is a duck-type check, and the duck is `feature_type` — the one attribute
`add_topomt_feature` reads before deciding anything else.

Checking it here rather than in the body moves the failure to the seam and gives it a
caller. The body's own `ValueError` said only *"not a valid TopoMT feature"*, with no
indication of which call produced it, and it fired after the other arguments had already
been accepted.

What each feature *kind* then requires — a pocket needs `atom_indices`, a channel its own
fields — stays in the body. Those are dispatch rules, not an argument contract, and they
are already stated once where the dispatch happens.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_feature(feature, caller=None):
    if getattr(feature, "feature_type", None) is not None:
        return feature
    raise ArgumentError(
        "feature",
        value=feature,
        caller=caller,
        message="a TopoMT feature is recognised by its `feature_type` attribute",
    )
