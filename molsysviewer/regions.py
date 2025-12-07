from __future__ import annotations

from typing import Any, Dict, Optional


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
        self.repr_params = repr_params or {}
        self._active = True

    # --- helpers ---

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
        self._send("show_region")

    def hide(self) -> None:
        """Hide this region (all attached representations)."""
        self._send("hide_region")

    def delete(self) -> None:
        """Remove this region and its representations."""
        if not self._active:
            return
        self._active = False
        self._send("delete_region")
        self._view._unregister_region(self.tag)  # noqa: SLF001
