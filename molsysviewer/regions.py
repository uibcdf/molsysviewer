from __future__ import annotations

from typing import Any, Dict, Optional

import molsysmt as msm


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
            raise NotImplementedError(
                "Region scoping for element='bond' is not implemented yet."
            )

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
        values = msm.get(
            self._view._molsys,  # noqa: SLF001
            element="atom",
            selection=list(self.atom_indices),
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
        self._send(
            "create_region",
            selection=self.selection,
            atom_indices=list(self.atom_indices) if self.atom_indices is not None else None,
            representation=self.representation,
            params=self.repr_params,
        )

    # --- public API ---

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
                skip_digestion=skip_digestion,
            )

        if selection == "all" and (mask is None or mask == "all"):
            return scope

        selected = self._view.select(  # noqa: SLF001
            selection=selection,
            structure_indices=structure_indices,
            element=element,
            mask=None,
            syntax=syntax,
            skip_digestion=skip_digestion,
        )
        if mask is not None and mask != "all":
            masked = self._view.select(  # noqa: SLF001
                selection=mask,
                structure_indices=structure_indices,
                element=element,
                mask=None,
                syntax=syntax,
                skip_digestion=skip_digestion,
            )
            selected = self._intersect_indices(selected, masked)

        return self._intersect_indices(selected, scope)

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
                skip_digestion=skip_digestion,
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
                skip_digestion=skip_digestion,
                **kwargs,
            )

        indices = self.select(
            selection=selection,
            structure_indices=structure_indices,
            element=element,
            mask=mask,
            syntax=syntax,
            skip_digestion=skip_digestion,
        )
        return self._view.get(  # noqa: SLF001
            element=element,
            selection=indices,
            structure_indices=structure_indices,
            mask=None,
            syntax=syntax,
            get_missing_bonds=get_missing_bonds,
            output_type=output_type,
            skip_digestion=skip_digestion,
            **kwargs,
        )

    def info(
        self,
        element="system",
        selection="all",
        syntax="MolSysMT",
        mask="all",
        skip_digestion=False,
    ):
        """Show a summary table, scoped to this region."""
        scope = self._scoped_indices_for_element(element)
        if scope is None or element == "system":
            return self._view.info(  # noqa: SLF001
                element=element,
                selection=selection,
                syntax=syntax,
                mask=mask,
                skip_digestion=skip_digestion,
            )

        indices = self.select(
            selection=selection,
            element=element,
            mask=mask,
            syntax=syntax,
            skip_digestion=skip_digestion,
        )
        return self._view.info(  # noqa: SLF001
            element=element,
            selection=indices,
            syntax=syntax,
            mask="all",
            skip_digestion=skip_digestion,
        )

    def set_representation(self, representation: str | None = None, *, preset: str | None = None, **params: Any) -> None:
        """Apply or update a representation for this region.

        Allowed Mol* types (normalized, case-insensitive): cartoon, backbone,
        ball-and-stick (aliases: sticks, ballstick), carbohydrate, ellipsoid,
        gaussian-surface, gaussian-volume, label, line (aliases: licorice, wire),
        molecular-surface (alias: surface), orientation, plane, point, putty, spacefill (alias: vdw).

        If ``preset`` is provided, it supersedes ``representation`` and applies a Mol* preset
        (auto, atomic-detail, polymer-and-ligand, polymer-cartoon, coarse-surface, empty).
        """
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

    def new_complementary_region(self, tag: str | None = None, **kwargs: Any) -> "Region":
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

    def show(self) -> None:
        """Show this region (all attached representations)."""
        self._hidden = False
        self._send("show_region")

    def hide(self) -> None:
        """Hide this region (all attached representations)."""
        self._hidden = True
        self._send("hide_region")

    def delete(self) -> None:
        """Remove this region and its representations."""
        if not self._active:
            return
        self._active = False
        self._send("delete_region")
        self._view._unregister_region(self.tag)  # noqa: SLF001
