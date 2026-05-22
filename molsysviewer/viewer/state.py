from __future__ import annotations

__name__ = "molsysviewer.viewer.core"

from typing import Any


class StateMixin:
    def export_state(self) -> dict:
        """Serialize the current viewer overlay state to a JSON-compatible dict.

        The returned dict captures annotations, measurements, saved selections,
        and regions (with resolved ``atom_indices``).  The loaded structure is
        **not** included.  Pass the dict to :meth:`import_state` to restore it
        on any viewer that has the same (or a compatible) structure loaded.

        Returns
        -------
        dict
            Keys: ``version``, ``annotations``, ``measurements``,
            ``selections``, ``regions``.
        """
        def _to_python(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _to_python(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_to_python(v) for v in obj]
            try:
                import numpy as np
                if isinstance(obj, (np.integer,)):
                    return int(obj)
                if isinstance(obj, (np.floating,)):
                    return float(obj)
            except ImportError:
                pass
            return obj

        regions = []
        for tag, region in self._regions.items():
            if region.atom_indices is not None:
                regions.append({"tag": tag, "atom_indices": list(region.atom_indices)})

        return _to_python({
            "version": 1,
            "annotations": self.annotations.records(),
            "measurements": self.measurements.records(),
            "selections": self.selections.records(),
            "regions": regions,
        })

    def import_state(self, state: dict, *, clear_first: bool = True) -> None:
        """Restore viewer overlay state from a dict produced by :meth:`export_state`.

        The structure must already be loaded (or at least compatible with the
        ``atom_indices`` in the stored state) before calling this method.

        Parameters
        ----------
        state
            Dict produced by :meth:`export_state`.
        clear_first
            If ``True`` (default), clears all existing annotations,
            measurements, saved selections, and regions before importing.
            Set to ``False`` to merge into existing state.
        """
        if not isinstance(state, dict):
            raise TypeError(f"state must be a dict, got {type(state).__name__}.")
        version = state.get("version", 1)
        if version != 1:
            raise ValueError(f"Unsupported state version: {version!r}.")

        if clear_first:
            self.clear_decorations(labels=True, shapes=False, styles=False, skip_digestion=True)
            self.measurements.clear(skip_digestion=True)
            self.selections.clear(skip_digestion=True)
            for tag in list(self._regions):
                try:
                    self._regions[tag].delete(skip_digestion=True)
                except Exception:
                    pass

        for msg in state.get("annotations", []):
            if isinstance(msg, dict) and msg.get("op") == "add_label":
                self._send(msg)

        for msg in state.get("measurements", []):
            if isinstance(msg, dict) and msg.get("op") in (
                "add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"
            ):
                self._send(msg)

        for msg in state.get("selections", []):
            if isinstance(msg, dict) and msg.get("op") == "save_selection":
                tag = msg.get("tag")
                if tag and not self.selections.contains(tag, skip_digestion=True):
                    self._send(msg)

        if self._molsys is not None:
            for region_data in state.get("regions", []):
                tag = region_data.get("tag")
                atom_indices = region_data.get("atom_indices")
                if tag and isinstance(atom_indices, list) and len(atom_indices) > 0:
                    try:
                        self.new_region(atom_indices=atom_indices, tag=tag, skip_digestion=True)
                    except Exception:
                        pass


StateMixin.__module__ = "molsysviewer.viewer"
for _name, _value in StateMixin.__dict__.items():
    if callable(_value):
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception:
            pass

