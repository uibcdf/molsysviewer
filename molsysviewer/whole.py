from __future__ import annotations

from typing import Any

import molsysmt as msm
from smonitor import signal

from . import pyunitwizard as puw
from ._private.argdigest import digest
from ._private.delegated_errors import as_our_argument_error
from ._private.exceptions import ArgumentError
from .colors import expand_values_to_atoms, normalize_color
from .scene_history import records_scene_history


class Whole:
    """Wrapper for operations on the whole structure (non-deletable, non-retaggable)."""

    def __init__(self, view: Any) -> None:
        self._view = view
        self._representation: str | None = None
        self._preset: str | None = None
        self._repr_params: dict[str, Any] = {}
        self._load_representation: str | None = None
        self._load_preset: str | None = None
        self._load_repr_params: dict[str, Any] = {}
        self._color_scheme: str | None = None

    @property
    def representation(self) -> str | None:
        """Current explicit representation type for the whole structure."""
        return self._representation

    @property
    def preset(self) -> str | None:
        """Current explicit representation preset for the whole structure."""
        return self._preset

    @property
    def params(self) -> dict[str, Any]:
        """Current representation parameters as a defensive copy."""
        return dict(self._repr_params)

    @property
    def visible(self) -> bool:
        """Whether the baseline/whole representation is currently visible."""
        return not bool(self._view._global_hidden)  # noqa: SLF001

    @property
    def color_scheme(self) -> str | None:
        """Current structural colour scheme owned by the whole structure."""
        return self._color_scheme

    @property
    def scene_style_name(self) -> str | None:
        """Name of the active scene style, if the current whole style came from one."""
        styles = getattr(self._view, "styles", None)
        return getattr(styles, "active_name", None)

    @signal(
        tags=["representation", "whole"],
        extra_factory=lambda args, kwargs: {
            "representation": kwargs.get("representation", args[1] if len(args) > 1 else None),
            "preset": kwargs.get("preset"),
        },
    )
    @digest()
    @records_scene_history
    def set_representation(self, representation: str | None = None, *, preset: str | None = None, skip_digestion: bool = False, **params: Any) -> None:
        """Set or update the global representation for the whole structure.

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
        scheme = self._repr_params.get("color_scheme")
        if isinstance(scheme, str) and scheme.strip():
            self._color_scheme = scheme.strip()
        else:
            self._color_scheme = None
        payload = {
            "op": "set_whole_representation",
            "representation": normalized_repr,
            "preset": normalized_preset if user_preset_payload is None else None,
            "params": self._repr_params,
        }
        if user_preset_payload is not None:
            payload["user_preset"] = user_preset_payload
        self._view._send(payload)  # noqa: SLF001
        if hasattr(self._view, "styles"):
            self._view.styles._clear_cached_name()  # noqa: SLF001
        self._view._sync_whole_summary_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["representation", "whole"])
    @digest()
    def reset_representation(self, skip_digestion: bool = False) -> None:
        """Restore the whole representation to the load-time explicit style."""
        self.set_representation(
            self._load_representation,
            preset=self._load_preset,
            skip_digestion=True,
            **dict(self._load_repr_params),
        )

    @records_scene_history
    @signal(tags=["visibility", "whole"])
    @digest()
    def show(self, skip_digestion: bool = False) -> None:
        """Show the global representation(s)."""
        self._view._global_hidden = False  # noqa: SLF001
        self._view._send({"op": "show_whole", "target": "whole"})  # noqa: SLF001
        self._view._sync_whole_summary_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["visibility", "whole"])
    @digest()
    def hide(self, skip_digestion: bool = False) -> None:
        """Hide the global representation(s)."""
        self._view._global_hidden = True  # noqa: SLF001
        self._view._send({"op": "hide_whole", "target": "whole"})  # noqa: SLF001
        self._view._sync_whole_summary_runtime()  # noqa: SLF001

    # --- MolSysMT query helpers (delegated to MolSysView) ---

    @signal(tags=["selection", "whole"])
    def select(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Select indices from the whole system (delegates to `MolSysView.select`)."""
        return self._view.select(*args, skip_digestion=skip_digestion, **kwargs)

    @signal(tags=["query", "whole"])
    def get(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Retrieve values from the whole system.

        The whole *is* the molecular system, so this is `msm.get` on it, digested by
        MolSysMT. Only the caller named in an error is ours: someone who called
        `whole.get` must not read a message about `msm.basic.get.get`.
        """
        try:
            return msm.get(self._view._molsys, *args, skip_digestion=skip_digestion, **kwargs)  # noqa: SLF001
        except Exception as exc:
            raise as_our_argument_error(exc, "molsysviewer.whole.get") from exc

    @signal(tags=["query", "whole"])
    def info(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Show a summary table for the whole system (delegates to `MolSysView.info`)."""
        return self._view.info(*args, skip_digestion=skip_digestion, **kwargs)

    @signal(tags=["convert", "whole"])
    def convert(
        self,
        to_form: str = "molsysmt.MolSys",
        *,
        structure_indices: Any = "all",
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
        **kwargs: Any,
    ):
        """Convert the whole system to another MolSysMT form.

        The whole *is* the molecular system, so this is `msm.convert` on it. A region
        converts its own subset instead; see :meth:`Region.convert`.

        Digestion is MolSysMT's: every argument here is theirs, and duplicating their
        checks is what `uibcdf/molsysviewer#71` is about. What is not theirs is the
        caller a user reads in an error, so their `ArgumentError` is re-raised as this
        package's, naming the method that was actually called.
        """
        view = self._view
        if view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded. Load a system before calling convert().")
        try:
            return msm.convert(
                view._molsys,  # noqa: SLF001
                to_form=to_form,
                structure_indices=structure_indices,
                syntax=syntax,
                skip_digestion=skip_digestion,
                **kwargs,
            )
        except Exception as exc:
            raise as_our_argument_error(exc, "molsysviewer.whole.convert") from exc

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

    @signal(tags=["whole", "query"])
    @digest()
    def get_center(
        self,
        structure_indices: str | Any = "all",
        skip_digestion: bool = False,
    ):
        """Return the geometric centroid in the configured standard length unit."""
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded.")

        from molsysmt.structure import get_center
        import numpy as np

        center = get_center(
            self._view._molsys,  # noqa: SLF001
            selection="all",
            structure_indices=structure_indices,
            syntax="MolSysMT",
            skip_digestion=True,
        )
        arr = np.asarray(puw.get_value(center, to_unit="nm"), dtype=float)
        arr = np.squeeze(arr)
        centroid = arr.mean(axis=0) if arr.ndim == 2 else arr
        return puw.standardize(puw.quantity(centroid.tolist(), "nm"))

    # --- Scalar colour mapping ---

    @records_scene_history
    @signal(tags=["color", "whole"])
    @digest()
    def set_color(self, color: Any, skip_digestion: bool = False) -> None:
        """Paint every atom in the whole/base color layer uniformly."""
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded.")
        try:
            normalized = normalize_color(color)
        except (TypeError, ValueError) as exc:
            raise ArgumentError("color", value=color, caller="Whole.set_color") from exc
        n_atoms = int(self._view._molsys.get_n_atoms())  # noqa: SLF001
        self._view._set_atom_color_layer(  # noqa: SLF001
            "whole",
            {atom_index: normalized for atom_index in range(n_atoms)},
        )

    @records_scene_history
    @signal(tags=["color", "whole"])
    @digest()
    def set_color_scheme(
        self,
        scheme: str,
        skip_digestion: bool = False,
    ) -> None:
        """Set the structural colour theme used by the whole representation."""
        normalized = str(scheme).strip()
        if not normalized:
            raise ValueError("set_color_scheme requires a non-empty scheme.")
        params = self.params
        params["color_scheme"] = normalized
        self._color_scheme = normalized
        self.set_representation(
            self.representation,
            preset=self.preset,
            skip_digestion=True,
            **params,
        )

    @signal(tags=["color", "whole"])
    @digest()
    def set_color_by_attribute(
        self,
        attribute: str,
        *,
        element: str = "atom",
        palette: Any = "viridis",
        value_range: Any = None,
        structure_indices: Any = None,
        replace: bool = True,
        skip_digestion: bool = False,
    ) -> None:
        """Color the whole structure by a scalar attribute already present in the system."""
        molsys = self._view._molsys  # noqa: SLF001
        if molsys is None:
            raise ValueError("No molecular system loaded.")

        available = set(msm.get_attributes(molsys, include_none=False, output_type="list", skip_digestion=True))
        requested = str(attribute).strip()
        resolved = requested if requested in available else requested.lower()
        if resolved not in available:
            recognized = set(msm.get_attributes(molsys, include_none=True, output_type="list", skip_digestion=True))
            if resolved in recognized:
                raise ValueError(
                    f"Attribute {attribute!r} has no values in the loaded system "
                    "(it may not have been loaded with this data)."
                )
            raise ValueError(f"Attribute {attribute!r} is not a recognized atom attribute.")

        effective_structure_indices = (
            [int(self._view.current_structure_index)]  # noqa: SLF001
            if structure_indices is None
            else structure_indices
        )
        values = msm.get(
            molsys,
            element=element,
            selection="all",
            structure_indices=effective_structure_indices,
            output_type="values",
            skip_digestion=True,
            **{resolved: True},
        )

        import numpy as np

        raw_values = puw.get_value(values) if puw.is_quantity(values) else values
        array = np.asarray(raw_values)
        array = np.squeeze(array)
        if array.ndim != 1:
            raise ValueError(f"Attribute {resolved!r} did not produce one scalar per {element}.")
        if any(value is None for value in array.tolist()):
            raise ValueError(f"Attribute {resolved!r} contains missing values.")
        try:
            scalar_values = array.astype(float).tolist()
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Attribute {resolved!r} is not scalar numeric data.") from exc

        self.set_color_by_values(
            scalar_values,
            element=element,
            palette=palette,
            value_range=value_range,
            replace=replace,
            skip_digestion=True,
        )

    @records_scene_history
    @signal(tags=["color", "whole"])
    @digest()
    def set_color_by_values(
        self,
        values: Any,
        element: str = "atom",
        palette: Any = "viridis",
        value_range: Any = None,
        replace: bool = True,
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
        layer_update = dict(zip(atom_indices, per_atom_colors))
        if replace:
            self._view._set_atom_color_layer("whole", layer_update)  # noqa: SLF001
        else:
            self._view._update_atom_color_layer("whole", layer_update)  # noqa: SLF001

    @records_scene_history
    @signal(tags=["color", "whole"])
    @digest()
    def reset_colors(self, skip_digestion: bool = False) -> None:
        """Remove the whole/base per-atom colour layer only."""
        self._view._clear_atom_color_layer("whole")  # noqa: SLF001
