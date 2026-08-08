"""Contracts for the scene settings that need at least one argument to mean anything.

Both methods used to raise a bare `ValueError` for this, which never reached the
diagnostics catalogue. Declaring the rule turns it into a catalogued
`MissingArgumentError` carrying the caller and the accepted names.
"""

from argdigest import FunctionContract

CONTRACTS = [
    FunctionContract(
        caller='molsysviewer.scene.set_lighting',
        requires_any_of=['ambient', 'diffuse', 'specular'],
        description='Setting no channel at all would be a no-op.',
    ),
    FunctionContract(
        caller='molsysviewer.scene.set_clip_planes',
        requires_any_of=['near', 'far', 'min_near', 'thickness'],
        description='Adjusting no plane at all would be a no-op.',
    ),
]
