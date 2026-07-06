from __future__ import annotations

from typing import Any

import molsysmt as msm
from smonitor import signal

from ._private.arg_digestion import digest
from .colors import expand_values_to_atoms, normalize_color


class Whole:
    """Wrapper for operations on the whole structure (non-deletable, non-retaggable)."""

    def __init__(self, view: Any) -> None:
        self._view = view
        self._representation: str | None = None
        self._preset: str | None = None
        self._repr_params: dict[str, Any] = {}

    @signal(
        tags=["representation", "whole"],
        extra_factory=lambda args, kwargs: {
            "representation": kwargs.get("representation", args[1] if len(args) > 1 else None),
            "preset": kwargs.get("preset"),
        },
    )
    @digest()
    def set_representation(self, representation: str | None = None, *, preset: str | None = None, skip_digestion: bool = False, **params: Any) -> None:
        """Set or update the global representation for the whole structure.

        If the global representation was hidden, this call will show it again.

        Parameters
        ----------
        representation
            Simple representation type (e.g., cartoon, ball-and-stick, line). Ignored if `preset`
            is provided.
        preset
            Optional Mol* preset (`auto`, `atomic-detail`, `polymer-and-ligand`, `polymer-cartoon`,
            `coarse-surface`, `empty`). When provided, supersedes ``representation`` and applies
            the preconfigured style bundle.
        """
        color = params.pop("color", None)
        if color is not None:
            params["molstar_color_theme"] = {"name": "uniform", "params": {"value": normalize_color(color)}}
        normalized_preset = self._view._normalize_representation_preset(preset)  # noqa: SLF001
        user_preset_payload = self._view._resolve_user_preset(normalized_preset)  # noqa: SLF001
        normalized_repr = None if normalized_preset else self._view._normalize_representation_type(representation)  # noqa: SLF001
        self._preset = normalized_preset
        self._representation = normalized_repr
        self._repr_params = params or {}
        # Changing the representation implies showing the global view again.
        self._view._global_hidden = False  # noqa: SLF001
        payload = {
            "op": "set_global_representation",
            "representation": normalized_repr,
            "preset": normalized_preset if user_preset_payload is None else None,
            "params": self._repr_params,
        }
        if user_preset_payload is not None:
            payload["user_preset"] = user_preset_payload
        self._view._send(payload)  # noqa: SLF001
        if hasattr(self._view, "styles"):
            self._view.styles._clear_cached_name()  # noqa: SLF001

    @signal(tags=["visibility", "whole"])
    @digest()
    def show(self, skip_digestion: bool = False) -> None:
        """Show the global representation(s)."""
        self._view._global_hidden = False  # noqa: SLF001
        self._view._send({"op": "show_global", "target": "global"})  # noqa: SLF001

    @signal(tags=["visibility", "whole"])
    @digest()
    def hide(self, skip_digestion: bool = False) -> None:
        """Hide the global representation(s)."""
        self._view._global_hidden = True  # noqa: SLF001
        self._view._send({"op": "hide_global", "target": "global"})  # noqa: SLF001

    # --- MolSysMT query helpers (delegated to MolSysView) ---

    @signal(tags=["selection", "whole"])
    def select(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Select indices from the whole system (delegates to `MolSysView.select`)."""
        return self._view.select(*args, skip_digestion=skip_digestion, **kwargs)

    @signal(tags=["query", "whole"])
    def get(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Retrieve values from the whole system (delegates to `MolSysView.get`)."""
        return self._view.get(*args, skip_digestion=skip_digestion, **kwargs)

    @signal(tags=["query", "whole"])
    def info(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Show a summary table for the whole system (delegates to `MolSysView.info`)."""
        return self._view.info(*args, skip_digestion=skip_digestion, **kwargs)

    @signal(tags=["query", "whole"])
    @digest()
    def contains(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion: bool = False,
        **kwargs: Any,
    ):
        """Check whether the whole system contains the requested features."""
        return self._view.contains(
            selection=selection,
            syntax=syntax,
            skip_digestion=True,
            **kwargs,
        )

    @signal(tags=["query", "whole"])
    @digest()
    def is_composed_of(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion: bool = False,
        **kwargs: Any,
    ):
        """Check whether the whole system is composed of the requested classes/counts."""
        return self._view.is_composed_of(
            selection=selection,
            syntax=syntax,
            skip_digestion=True,
            **kwargs,
        )

    @signal(tags=["camera", "whole"])
    @digest()
    def focus(
        self,
        selection="all",
        structure_indices="all",
        syntax="MolSysMT",
        *,
        duration: Any = '250 ms',
        duration_ms: Any | None = None,
        extra_radius: Any = '4.0 angstroms',
        min_radius: Any = '1.0 angstroms',
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on a selection within the whole system."""
        self._view.focus_selection(
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    # --- Scalar colour mapping ---

    @signal(tags=["color", "whole"])
    @digest()
    def set_color_by_values(
        self,
        values: Any,
        element: str = "atom",
        palette: Any = "viridis",
        value_range: Any = None,
        skip_digestion: bool = False,
    ) -> None:
        """Map a scalar array to per-atom colors on the whole structure.

        One scalar value is mapped to a color and then broadcast to all atoms
        that belong to the corresponding structural element.

        Parameters
        ----------
        values
            Iterable of numeric scalars, one per *element* in the whole system
            (e.g. one per atom when ``element="atom"``, one per residue when
            ``element="group"``).
        element
            Structural level at which *values* are defined.  Accepted levels
            are the same as for ``msm.get``: ``"atom"``, ``"group"``,
            ``"component"``, ``"molecule"``, ``"chain"``, ``"entity"``.
            Defaults to ``"atom"``.
        palette
            Palette name (str), matplotlib colormap, or list of colors.
            Defaults to ``"viridis"``.
        value_range
            ``[vmin, vmax]`` normalization range.  Auto-detected from *values*
            when ``None``.
        """
        atom_indices, per_atom_colors = expand_values_to_atoms(
            self._view._molsys,  # noqa: SLF001
            values=values,
            element=element,
            palette=palette,
            value_range=value_range,
            scope_atom_indices=None,
        )
        # Replace the entire map (whole = always replace)
        self._view._atom_color_map = dict(zip(atom_indices, per_atom_colors))  # noqa: SLF001
        self._view._send({  # noqa: SLF001
            "op": "set_atom_colors",
            "atom_indices": atom_indices,
            "colors": per_atom_colors,
            "replace": True,
        })

    @signal(tags=["color", "whole"])
    @digest()
    def reset_colors(self, skip_digestion: bool = False) -> None:
        """Remove any per-atom color override and revert to the current representation theme."""
        self._view._atom_color_map.clear()  # noqa: SLF001
        self._view._send({"op": "clear_atom_colors"})  # noqa: SLF001
