from __future__ import annotations

from typing import Any, Dict, List, Optional

import molsysmt as msm
from smonitor import signal
from ._private.arg_digestion import digest
from .colors import expand_values_to_atoms, normalize_color


class Region:
    """Wrapper for a molecular region (Mol* component) addressed by tag."""

    def __init__(
        self,
        view: Any,
        tag: str,
        selection: str | Any,
        *,
        atom_indices: Optional[list[int]] = None,
        representation: str | None = None,
        repr_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._view = view
        self.tag = tag
        self.selection = selection
        self.atom_indices = tuple(atom_indices) if atom_indices is not None else None
        self.representation = representation
        self.preset: str | None = None
        self.repr_params = repr_params or {}
        self._active = True
        self._hidden = False

    # --- helpers ---

    def _scoped_indices_for_element(self, element: str):
        if self.atom_indices is None:
            return None

        if element == "atom":
            return sorted(set(self.atom_indices))

        if element == "system":
            return None

        if element == "bond":
            local_sel = self.atom_indices
            if self._view._index_mapper is not None:
                local_sel = self._view._index_mapper.to_local_atoms(self.atom_indices)
            per_atom = msm.get(
                self._view._molsys,  # noqa: SLF001
                element="atom",
                selection=list(local_sel),
                output_type="values",
                skip_digestion=True,
                bond_index=True,
            )
            scoped: list[int] = []
            for bonds in per_atom or []:
                for b in bonds or []:
                    try:
                        scoped.append(int(b))
                    except Exception:
                        continue
            return sorted(set(scoped))

        element_to_atom_attribute = {
            "group": "group_index",
            "component": "component_index",
            "chain": "chain_index",
            "molecule": "molecule_index",
            "entity": "entity_index",
        }
        if element not in element_to_atom_attribute:
            raise ValueError(f"Unsupported element level: {element!r}")

        atom_attribute = element_to_atom_attribute[element]
        local_sel = self.atom_indices
        if self._view._index_mapper is not None:
            local_sel = self._view._index_mapper.to_local_atoms(self.atom_indices)
        values = msm.get(
            self._view._molsys,  # noqa: SLF001
            element="atom",
            selection=list(local_sel),
            output_type="values",
            skip_digestion=True,
            **{atom_attribute: True},
        )
        scoped: list[int] = []
        for value in values or []:
            try:
                if value is None:
                    continue
                scoped.append(int(value))
            except Exception:
                continue
        return sorted(set(scoped))

    def _intersect_indices(self, a, b):
        if a is None:
            return b
        if b is None:
            return a
        aset = set(a)
        return sorted({ii for ii in b if ii in aset})

    def _send(self, op: str, **payload: Any) -> None:
        if not self._active:
            return
        msg = {"op": op, "tag": self.tag, **payload}
        self._view._send(msg)  # noqa: SLF001

    def _send_create(self) -> None:
        local_atoms = None
        if self.atom_indices is not None:
            if self._view._index_mapper is not None:
                local_atoms = self._view._index_mapper.to_local_atoms(self.atom_indices)
            else:
                local_atoms = list(self.atom_indices)
        self._send(
            "create_region",
            selection=self.selection,
            atom_indices=local_atoms,
            representation=self.representation,
            params=self.repr_params,
        )

    # --- public API ---

    @signal(tags=["region", "selection"])
    @digest()
    def select(
        self,
        selection="all",
        structure_indices="all",
        element="atom",
        mask=None,
        syntax="MolSysMT",
        skip_digestion=False,
    ):
        """Select indices, scoped to this region."""
        scope = self._scoped_indices_for_element(element)
        if scope is None:
            return self._view.select(  # noqa: SLF001
                selection=selection,
                structure_indices=structure_indices,
                element=element,
                mask=mask,
                syntax=syntax,
                skip_digestion=True,
            )

        if selection == "all" and (mask is None or mask == "all"):
            return scope

        selected = self._view.select(  # noqa: SLF001
            selection=selection,
            structure_indices=structure_indices,
            element=element,
            mask=None,
            syntax=syntax,
            skip_digestion=True,
        )
        if mask is not None and mask != "all":
            masked = self._view.select(  # noqa: SLF001
                selection=mask,
                structure_indices=structure_indices,
                element=element,
                mask=None,
                syntax=syntax,
                skip_digestion=True,
            )
            selected = self._intersect_indices(selected, masked)

        return self._intersect_indices(selected, scope)

    @signal(tags=["region", "query"])
    @digest()
    def get(
        self,
        element="system",
        selection="all",
        structure_indices="all",
        mask=None,
        syntax="MolSysMT",
        get_missing_bonds=True,
        output_type="values",
        skip_digestion=False,
        **kwargs,
    ):
        """Retrieve values, scoped to this region."""
        scope = self._scoped_indices_for_element(element)
        if scope is None:
            return self._view.get(  # noqa: SLF001
                element=element,
                selection=selection,
                structure_indices=structure_indices,
                mask=mask,
                syntax=syntax,
                get_missing_bonds=get_missing_bonds,
                output_type=output_type,
                skip_digestion=True,
                **kwargs,
            )

        if element == "system":
            return self._view.get(  # noqa: SLF001
                element=element,
                selection=selection,
                structure_indices=structure_indices,
                mask=mask,
                syntax=syntax,
                get_missing_bonds=get_missing_bonds,
                output_type=output_type,
                skip_digestion=True,
                **kwargs,
            )

        indices = self.select(
            selection=selection,
            structure_indices=structure_indices,
            element=element,
            mask=mask,
            syntax=syntax,
            skip_digestion=True,
        )
        return self._view.get(  # noqa: SLF001
            element=element,
            selection=indices,
            structure_indices=structure_indices,
            mask=None,
            syntax=syntax,
            get_missing_bonds=get_missing_bonds,
            output_type=output_type,
            skip_digestion=True,
            **kwargs,
        )

    def _region_info_records(self) -> list[dict]:
        """Build the region-state rows for the info table."""
        return [
            {
                "field": "tag",
                "value": self.tag,
            },
            {
                "field": "n atoms",
                "value": len(self.atom_indices) if self.atom_indices is not None else "all",
            },
            {
                "field": "visible",
                "value": not self._hidden,
            },
            {
                "field": "representation",
                "value": self.representation,
            },
            {
                "field": "preset",
                "value": self.preset,
            },
        ]

    @signal(tags=["region", "query"])
    @digest()
    def info(
        self,
        element="system",
        selection="all",
        syntax="MolSysMT",
        mask="all",
        output_type="styler",
        skip_digestion=False,
    ):
        """Show a summary table, scoped to this region.

        Returns a ``RegionInfo`` with a *molsys* section (filtered to the region's
        atoms) and a *region* section (tag, atom count, visibility, representation).
        When the region has no fixed atom set, delegates to the full viewer info.
        """
        from .viewer.core import RegionInfo  # noqa: PLC0415 – avoid circular import at module level

        # --- element != "system": scope to region atoms for that element ---
        scope = self._scoped_indices_for_element(element)
        if element != "system" and scope is not None:
            indices = self.select(
                selection=selection,
                element=element,
                mask=mask,
                syntax=syntax,
                skip_digestion=True,
            )
            return self._view.info(  # noqa: SLF001
                element=element,
                selection=indices,
                syntax=syntax,
                mask="all",
                output_type=output_type,
                skip_digestion=True,
            )

        # --- element == "system" with defined atom_indices: return RegionInfo ---
        if self.atom_indices is not None:
            molsys_section = self._view.info(  # noqa: SLF001
                element="system",
                selection=list(self.atom_indices),
                syntax=syntax,
                mask="all",
                source="molsys",
                output_type=output_type,
                skip_digestion=True,
            )
            region_section = self._view._convert_info_output(  # noqa: SLF001
                self._region_info_records(), output_type
            )
            return RegionInfo(
                tag=self.tag,
                molsys_section=molsys_section,
                region_section=region_section,
            )

        # --- fallback: region covers the full system ---
        return self._view.info(  # noqa: SLF001
            element=element,
            selection=selection,
            syntax=syntax,
            mask=mask,
            output_type=output_type,
            skip_digestion=True,
        )

    @signal(tags=["region", "query"])
    @digest()
    def contains(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ) -> bool:
        """Check whether this region contains the requested features."""
        if self.atom_indices is None:
            return self._view.contains(  # noqa: SLF001
                selection=selection,
                syntax=syntax,
                skip_digestion=True,
                **kwargs,
            )

        scoped = self.select(
            selection=selection,
            element="atom",
            syntax=syntax,
            skip_digestion=True,
        )
        return self._view.contains(  # noqa: SLF001
            selection=scoped,
            syntax=syntax,
            skip_digestion=True,
            **kwargs,
        )

    @signal(tags=["region", "query"])
    @digest()
    def is_composed_of(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ) -> bool:
        """Check whether this region is composed of the requested classes/counts."""
        if self.atom_indices is None:
            return self._view.is_composed_of(  # noqa: SLF001
                selection=selection,
                syntax=syntax,
                skip_digestion=True,
                **kwargs,
            )

        scoped = self.select(
            selection=selection,
            element="atom",
            syntax=syntax,
            skip_digestion=True,
        )
        return self._view.is_composed_of(  # noqa: SLF001
            selection=scoped,
            syntax=syntax,
            skip_digestion=True,
            **kwargs,
        )

    @signal(tags=["region", "query"])
    @digest()
    def get_center(
        self,
        structure_indices: str | Any = "all",
        skip_digestion: bool = False,
    ):
        """Return the geometric centroid of this region's atoms as a ``puw`` quantity in nm.

        Parameters
        ----------
        structure_indices
            Structure frame(s) to average over.  Defaults to ``"all"``.

        Returns
        -------
        puw.Quantity
            ``[x, y, z]`` centroid in nanometres.
        """
        from . import pyunitwizard as puw

        if self.atom_indices is None:
            raise ValueError("get_center() requires known atom_indices for this region.")
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded.")

        import molsysmt as msm
        import numpy as np

        local_sel = self.atom_indices
        if self._view._index_mapper is not None:
            local_sel = self._view._index_mapper.to_local_atoms(self.atom_indices)

        mapped_structs = structure_indices
        if self._view._index_mapper is not None:
            if structure_indices not in ("all", None):
                mapped_structs = self._view._index_mapper.to_local_structures(structure_indices)

        coords = msm.get(
            self._view._molsys,  # noqa: SLF001
            element="atom",
            selection=list(local_sel),
            structure_indices=mapped_structs,
            coordinates=True,
            output_type="values",
            skip_digestion=True,
        )
        # coords shape: (n_structures, n_atoms, 3) with units already in nm
        arr = np.asarray(puw.get_value(coords, to_unit="nm"), dtype=float)
        if arr.ndim == 3:
            # Average over frames first, then atoms
            centroid = arr.mean(axis=(0, 1))
        else:
            centroid = arr.mean(axis=0)
        return puw.quantity(centroid.tolist(), "nm")

    @signal(tags=["region", "camera"])
    @digest()
    def focus(
        self,
        *,
        duration: Any = '250 ms',
        duration_ms: Any | None = None,
        extra_radius: Any = '4.0 angstroms',
        min_radius: Any = '1.0 angstroms',
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on this region."""
        self._view.focus_region(
            self,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    @signal(
        tags=["region", "representation"],
        extra_factory=lambda args, kwargs: {
            "representation": kwargs.get("representation", args[1] if len(args) > 1 else None),
            "preset": kwargs.get("preset"),
        },
    )
    @digest()
    def set_representation(self, representation: str | None = None, *, preset: str | None = None, skip_digestion: bool = False, **params: Any) -> None:
        """Apply or update a representation for this region.

        Allowed Mol* types (normalized, case-insensitive): cartoon, backbone,
        ball-and-stick (aliases: sticks, ballstick), carbohydrate, ellipsoid,
        gaussian-surface, gaussian-volume, label, line (aliases: licorice, wire),
        molecular-surface (alias: surface), orientation, plane, point, putty, spacefill (alias: vdw).

        If ``preset`` is provided, it supersedes ``representation`` and applies a Mol* preset
        (auto, atomic-detail, polymer-and-ligand, polymer-cartoon, coarse-surface, empty).
        """
        color = params.pop("color", None)
        if color is not None:
            params["molstar_color_theme"] = {"name": "uniform", "params": {"value": normalize_color(color)}}
        normalized_preset = self._view._normalize_representation_preset(preset)  # noqa: SLF001
        user_preset_payload = self._view._resolve_user_preset(normalized_preset)  # noqa: SLF001
        normalized = None if normalized_preset else self._view._normalize_representation_type(representation)  # noqa: SLF001
        self.representation = normalized
        self.preset = normalized_preset
        self.repr_params = params or {}
        self._send(
            "set_region_representation",
            representation=normalized,
            preset=normalized_preset if user_preset_payload is None else None,
            user_preset=user_preset_payload,
            params=self.repr_params,
        )

    @signal(tags=["region"])
    @digest()
    def new_complementary_region(self, tag: str | None = None, skip_digestion: bool = False, **kwargs: Any) -> "Region":
        """Create a new region with the complement of this region's atoms.

        The resulting tag defaults to ``f\"Global-{self.tag}\"`` if not provided.
        """
        if self.atom_indices is None:
            raise ValueError("Complement unavailable: atom_indices not known for this region.")
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded. Load a system before creating complementary regions.")
        comp_tag = tag or f"Global-{self.tag}"
        total_atoms = int(self._view._molsys._get_n_atoms())  # type: ignore[attr-defined]  # noqa: SLF001
        complement = [i for i in range(total_atoms) if i not in set(self.atom_indices)]
        return self._view.new_region(  # noqa: SLF001
            atom_indices=complement,
            tag=comp_tag,
            **kwargs,
        )

    @signal(tags=["region", "visibility"])
    @digest()
    def show(self, skip_digestion: bool = False) -> None:
        """Show this region (all attached representations)."""
        self._hidden = False
        self._send("show_region")

    @signal(tags=["region", "visibility"])
    @digest()
    def hide(self, skip_digestion: bool = False) -> None:
        """Hide this region (all attached representations)."""
        self._hidden = True
        self._send("hide_region")

    @signal(tags=["region", "visibility"])
    @digest()
    def show_only(self, skip_digestion: bool = False) -> None:
        """Leave only this region visible in the current view."""
        if self.atom_indices is None:
            raise ValueError("Cannot show only a region without known atom indices.")
        self._view.isolate(selection=list(self.atom_indices), skip_digestion=True)

    @signal(tags=["region"])
    @digest()
    def delete(self, skip_digestion: bool = False) -> None:
        """Remove this region and its representations."""
        if not self._active:
            return
        self._active = False
        self._send("delete_region")
        self._view._unregister_region(self.tag)  # noqa: SLF001

    @signal(tags=["region"])
    @digest()
    def rename(self, new_tag: str, skip_digestion: bool = False) -> None:
        """Rename this region to *new_tag* on both the Python and JS sides."""
        if not self._active:
            return
        old_tag = self.tag
        self._send("rename_region", new_tag=new_tag)
        self.tag = new_tag
        self._view._regions[new_tag] = self  # noqa: SLF001
        self._view._regions.pop(old_tag, None)  # noqa: SLF001

    # --- Scalar colour mapping ---

    @signal(tags=["color", "region"])
    @digest()
    def set_color_by_values(
        self,
        values: Any,
        element: str = "atom",
        palette: Any = "viridis",
        value_range: Any = None,
        replace: bool = False,
        skip_digestion: bool = False,
    ) -> None:
        """Map a scalar array to per-atom colors for this region.

        One scalar value is mapped to a color and broadcast to all atoms in the
        corresponding structural element *within this region*.

        Parameters
        ----------
        values
            Iterable of scalars, one per *element* present in this region.
        element
            Structural level: ``"atom"``, ``"group"``, ``"component"``,
            ``"molecule"``, ``"chain"``, ``"entity"``.  Defaults to ``"atom"``.
        palette
            Palette name, matplotlib colormap, or list of colors.
        value_range
            ``[vmin, vmax]`` normalization range.  Auto-detected when ``None``.
        replace
            If ``True``, replace any existing per-atom color map for the entire
            canvas.  If ``False`` (default), the region colors are *merged*
            with any existing assignments.
        """
        if self.atom_indices is None:
            raise ValueError("set_color_by_values requires known atom_indices for this region.")
        atom_indices, per_atom_colors = expand_values_to_atoms(
            self._view._molsys,  # noqa: SLF001
            values=values,
            element=element,
            palette=palette,
            value_range=value_range,
            scope_atom_indices=list(self.atom_indices),
        )
        # Update Python-side map: merge or replace depending on the flag
        if replace:
            self._view._atom_color_map = dict(zip(atom_indices, per_atom_colors))  # noqa: SLF001
        else:
            self._view._atom_color_map.update(zip(atom_indices, per_atom_colors))  # noqa: SLF001
        self._view._send({  # noqa: SLF001
            "op": "set_atom_colors",
            "atom_indices": atom_indices,
            "colors": per_atom_colors,
            "replace": replace,
        })

    @signal(tags=["color", "region"])
    @digest()
    def reset_colors(self, skip_digestion: bool = False) -> None:
        """Remove per-atom color overrides for the whole canvas and revert to the representation theme."""
        self._view._atom_color_map.clear()  # noqa: SLF001
        self._view._send({"op": "clear_atom_colors"})  # noqa: SLF001


class RegionsManager(dict):
    """Dict-like registry of :class:`Region` objects with an :meth:`info` helper."""

    def info(self, tag: str | None = None) -> dict[str, Any] | List[dict[str, Any]]:
        """Return compact metadata for one region (by *tag*) or all regions."""

        def summarize(region: Region) -> dict[str, Any]:
            atom_indices = list(region.atom_indices) if region.atom_indices is not None else []
            return {
                "tag": region.tag,
                "n_atoms": len(atom_indices),
                "atom_indices": atom_indices,
                "representation": region.representation,
                "visible": not region._hidden,  # noqa: SLF001
                "active": region._active,  # noqa: SLF001
            }

        if tag is not None:
            region = self.get(tag)
            if region is None:
                raise KeyError(tag)
            return summarize(region)
        return [summarize(r) for r in self.values()]
