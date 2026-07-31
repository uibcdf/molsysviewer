"""Pre-1.0 scale guard for materialized structures.

MolSysViewer 1.0 materializes every selected structure: `view.molsys` is the
complete selected system, and scientific operations, add-ons and measurements
rely on that. Windowed residency would change that public meaning and is
deliberately post-1.0.

What 1.0 owes the user is therefore not a smaller footprint but an *honest
ceiling*: a load large enough to exhaust the browser tab must say so, with the
numbers and a concrete way to proceed, instead of dying silently.

The budget is expressed in coordinate bytes, the one quantity that scales with
both axes (atoms and structures) and that we can compute before delivering
anything. It is a warning, never a refusal: a large machine is allowed to load a
large trajectory, and only the user knows their machine.
"""

import warnings

from smonitor.integrations import context_extra, emit_from_catalog

from .smonitor import CATALOG, META, PACKAGE_ROOT

#: Coordinate bytes on the wire per atom per structure: float32 x, y, z.
_BYTES_PER_ATOM_STRUCTURE = 3 * 4

#: Default ceiling in coordinate bytes. Beyond roughly this, one Mol* instance
#: plus its own per-axis copies, its atom/bond tables and its representations
#: tend to put a browser tab under real pressure — and a canvas popup doubles
#: the renderer-side cost, because two Mol* instances each keep their own axes.
DEFAULT_COORDINATE_BUDGET_BYTES = 256 * 1024 * 1024


class StructureScaleWarning(UserWarning):
    """A load whose materialized coordinates exceed the configured budget."""


def coordinate_bytes(n_atoms: int, n_structures: int) -> int:
    """Wire size of the coordinates for a complete materialized selection."""
    return int(n_atoms) * int(n_structures) * _BYTES_PER_ATOM_STRUCTURE


def _human(n_bytes: float) -> str:
    megabytes = n_bytes / (1024 * 1024)
    if megabytes >= 1024:
        return f"{megabytes / 1024:.1f} GB"
    return f"{megabytes:.0f} MB"


def suggested_structure_stride(n_atoms: int, n_structures: int, budget_bytes: int) -> int:
    """Stride that brings a selection under budget, for an actionable message."""
    total = coordinate_bytes(n_atoms, n_structures)
    if total <= budget_bytes or budget_bytes <= 0:
        return 1
    return max(2, -(-total // budget_bytes))  # ceil


def check_structure_scale(
    n_atoms: int,
    n_structures: int,
    *,
    budget_bytes: int = DEFAULT_COORDINATE_BUDGET_BYTES,
    stacklevel: int = 3,
) -> int | None:
    """Warn when a materialized selection exceeds the coordinate budget.

    Returns the coordinate size in bytes when it warned, otherwise ``None``.
    Never raises and never refuses: the caller's machine may well be able to
    hold it, and silently declining scientific data would be worse than a
    heavy load.
    """
    if n_atoms <= 0 or n_structures <= 0 or budget_bytes <= 0:
        return None
    total = coordinate_bytes(n_atoms, n_structures)
    if total <= budget_bytes:
        return None

    stride = suggested_structure_stride(n_atoms, n_structures, budget_bytes)
    kept = -(-n_structures // stride)
    # The signal catalog is how this project reports conditions worth watching;
    # the warning stays for the notebook user reading it inline.
    emit_from_catalog(
        CATALOG["structure_scale_over_budget"],
        package_root=PACKAGE_ROOT,
        meta=META,
        extra=context_extra(
            caller="molsysviewer.loaders.load_from_molsysmt",
            operation="materialize-selected-structures",
            failure_class="scale_over_budget",
            last_failure_reason=(
                f"{total} coordinate bytes for {n_structures} structures of "
                f"{n_atoms} atoms exceed the {budget_bytes} byte budget"
            ),
        ),
    )
    warnings.warn(
        f"This selection materializes {n_structures} structures of {n_atoms} atoms, "
        f"about {_human(total)} of coordinates, over the {_human(budget_bytes)} budget. "
        f"Every selected structure is held in memory, and a canvas popup doubles the "
        f"renderer-side cost, so the browser tab may run out of memory. "
        f"To stay under budget, load a subset, for example "
        f"structure_indices=range(0, {n_structures}, {stride}) "
        f"({kept} structures). Raise the ceiling with "
        f"molsysviewer.config.set_structure_scale_budget(bytes) if this machine can hold it.",
        StructureScaleWarning,
        stacklevel=stacklevel,
    )
    return total
