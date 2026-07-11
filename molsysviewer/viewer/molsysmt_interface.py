from __future__ import annotations


import time
import inspect
from typing import Any, Mapping

import numpy as np
import molsysmt as msm
from smonitor import signal
from depdigest import dep_digest

from .._pyunitwizard import puw
from .._private.arg_digestion import digest
from .._private.variables import is_all


class MolSysMTInterfaceMixin:
    def _viewer_info_summary(self) -> dict[str, Any]:
        current_style = self.styles.current(skip_digestion=True) if hasattr(self, "styles") else None
        layer_tags = sorted(self._layers.keys())
        region_tags = sorted(self._regions.keys())
        shape_tags = sorted(
            tag for tag, item in self._scene_objects.items() if getattr(item, "kind", None) == "shape"
        )
        annotation_tags = sorted(self.annotations.tags)
        measurement_tags = sorted(self.measurements.tags(skip_digestion=True))
        selection_tags = sorted(self.selections.tags)

        return {
            "whole": {
                "representation": self.whole.representation,
                "preset": self.whole.preset,
                "params": self.whole.params,
                "visible": self.whole.visible,
                "scene_style_name": self.scene_style_name,
            },
            "loads": [
                {
                    "index": b.get("index"),
                    "label": b.get("label"),
                    "n_atoms": b.get("n_atoms"),
                    "atom_range": (b.get("start", 0), b.get("stop", 0)),
                    "region_tag": b.get("region_tag"),
                }
                for b in self._load_blocks
            ],
            "current_structure_index": self._current_structure_index,
            "styles": {
                "current": None if current_style is None else current_style.info(),
                "registered_count": self.styles.count(skip_digestion=True),
                "builtin_count": len(self.styles.builtin_tags(skip_digestion=True)),
            },
            "regions": {
                "count": len(region_tags),
                "tags": region_tags,
            },
            "layers": {
                "count": len(layer_tags),
                "tags": layer_tags,
            },
            "shapes": {
                "count": len(shape_tags),
                "tags": shape_tags,
            },
            "annotations": {
                "count": len(annotation_tags),
                "tags": annotation_tags,
            },
            "measurements": {
                "count": len(measurement_tags),
                "tags": measurement_tags,
                "settings": self.measurements.settings(skip_digestion=True),
            },
            "selections": {
                "count": len(selection_tags),
                "tags": selection_tags,
            },
            "active_selection": {
                "is_empty": self.active_selection.is_empty(skip_digestion=True),
                "info": self.active_selection.info(skip_digestion=True),
            },
        }

    def _viewer_info_records(self) -> list[dict[str, Any]]:
        summary = self._viewer_info_summary()
        records: list[dict[str, Any]] = []

        whole = summary["whole"]
        records.append(
            {
                "section": "whole",
                "tag": "whole",
                "kind": "whole",
                "visible": whole["visible"],
                "active": True,
                "layer tag": None,
                "representation": whole["representation"],
                "preset": whole["preset"],
                "n atoms": None,
                "n members": None,
                "n picks": None,
                "details": ", ".join(f"{key}={value}" for key, value in sorted(whole["params"].items())) if whole["params"] else "",
            }
        )

        for block in summary.get("loads", []):
            records.append(
                {
                    "section": "loads",
                    "tag": block.get("label") or f"load{block.get('index', '')}",
                    "kind": "load",
                    "visible": None,
                    "active": True,
                    "layer tag": block.get("region_tag"),
                    "representation": None,
                    "preset": None,
                    "n atoms": block.get("n_atoms"),
                    "n members": None,
                    "n picks": None,
                    "details": f"atoms {block.get('atom_range', (0, 0))[0]}–{block.get('atom_range', (0, 0))[1]}",
                }
            )

        styles = summary["styles"]
        current_style = styles.get("current")
        records.append(
            {
                "section": "styles",
                "tag": "current",
                "kind": "style",
                "visible": None,
                "active": current_style is not None,
                "layer tag": None,
                "representation": None if current_style is None else current_style.get("representation"),
                "preset": None if current_style is None else (current_style.get("user_preset") or current_style.get("preset")),
                "n atoms": None,
                "n members": styles["registered_count"],
                "n picks": None,
                "details": (
                    f"builtins={styles['builtin_count']}"
                    if current_style is None
                    else ", ".join(
                        [f"builtins={styles['builtin_count']}"]
                        + [f"{key}={value}" for key, value in sorted((current_style.get("params") or {}).items())]
                    )
                ),
            }
        )

        for item in self.annotations.info(skip_digestion=True):
            records.append(
                {
                    "section": "annotations",
                    "tag": item.get("tag"),
                    "kind": item.get("kind"),
                    "visible": item.get("visible"),
                    "active": item.get("active"),
                    "layer tag": item.get("layer_tag"),
                    "representation": None,
                    "preset": None,
                    "n atoms": item.get("n_atoms"),
                    "n members": None,
                    "n picks": None,
                    "details": item.get("text"),
                }
            )

        for item in self.measurements.info():
            records.append(
                {
                    "section": "measurements",
                    "tag": item.get("tag"),
                    "kind": item.get("kind"),
                    "visible": item.get("visible"),
                    "active": item.get("active"),
                    "layer tag": item.get("layer_tag"),
                    "representation": None,
                    "preset": None,
                    "n atoms": None,
                    "n members": None,
                    "n picks": item.get("n_picks"),
                    "details": f"policy={item.get('endpoint_policy')}",
                }
            )

        for tag, region in sorted(self._regions.items()):
            records.append(
                {
                    "section": "regions",
                    "tag": tag,
                    "kind": "region",
                    "visible": not bool(getattr(region, "_hidden", False)),
                    "active": bool(getattr(region, "_active", False)),
                    "layer tag": getattr(region, "layer", None),
                    "representation": getattr(region, "representation", None),
                    "preset": getattr(region, "preset", None),
                    "n atoms": len(getattr(region, "atom_indices", ()) or ()),
                    "n members": None,
                    "n picks": None,
                    "details": getattr(region, "selection", None) or "",
                }
            )

        for tag, layer in sorted(self._layers.items()):
            members = getattr(layer, "members", {})
            n_shapes = sum(1 for member in members.values() if getattr(member, "kind", None) == "shape")
            n_annotations = sum(1 for member in members.values() if getattr(member, "kind", None) == "annotation")
            n_measurements = sum(1 for member in members.values() if getattr(member, "kind", None) == "measurement")
            n_regions = sum(1 for member in members.values() if hasattr(member, "layer"))
            records.append(
                {
                    "section": "layers",
                    "tag": tag,
                    "kind": getattr(layer, "kind", "layer"),
                    "visible": not bool(getattr(layer, "_hidden", False)),
                    "active": bool(getattr(layer, "_active", False)),
                    "layer tag": tag,
                    "representation": None,
                    "preset": None,
                    "n atoms": None,
                    "n members": len(members),
                    "n picks": None,
                    "details": f"shapes={n_shapes}, annotations={n_annotations}, measurements={n_measurements}, regions={n_regions}",
                }
            )
        for tag, item in sorted(self._scene_objects.items()):
            if getattr(item, "kind", None) != "shape":
                continue
            records.append(
                {
                    "section": "shapes",
                    "tag": tag,
                    "kind": getattr(item, "meta", {}).get("shape_kind", "shape"),
                    "visible": not bool(getattr(item, "_hidden", False)),
                    "active": bool(getattr(item, "_active", False)),
                    "layer tag": getattr(item, "layer_tag", None),
                    "representation": None,
                    "preset": None,
                    "n atoms": None,
                    "n members": None,
                    "n picks": None,
                    "details": f"layer={getattr(item, 'layer_tag', None)}",
                }
            )

        for item in self.selections.info(skip_digestion=True):
            records.append(
                {
                    "section": "selections",
                    "tag": item.get("tag"),
                    "kind": "selection",
                    "visible": None,
                    "active": True,
                    "layer tag": None,
                    "representation": None,
                    "preset": None,
                    "n atoms": item.get("n_atoms"),
                    "n members": None,
                    "n picks": None,
                    "details": f"{item.get('source_kind')} / {item.get('element_level')}",
                }
            )

        active_selection = summary["active_selection"]
        active_info = active_selection["info"]
        records.append(
            {
                "section": "active_selection",
                "tag": "active_selection",
                "kind": active_info.get("source_kind"),
                "visible": None,
                "active": not active_selection["is_empty"],
                "layer tag": None,
                "representation": None,
                "preset": None,
                "n atoms": active_info.get("count_atoms"),
                "n members": None,
                "n picks": None,
                "details": f"{active_info.get('source_kind')} / {active_info.get('element_level')}",
            }
        )

        return records

    def _records_to_styler(self, records: list[dict[str, Any]]):
        from pandas import DataFrame as df

        return df(records).style.hide(axis='index')

    def _styler_to_dataframe(self, styler):
        data = getattr(styler, "data", None)
        if data is None:
            raise ValueError("Unable to extract DataFrame from Styler output.")
        return data

    def _convert_info_output(self, value: Any, output_type: str):
        if output_type == "styler":
            if isinstance(value, list):
                return self._records_to_styler(value)
            return value
        if output_type == "dataframe":
            if isinstance(value, list):
                return self._styler_to_dataframe(self._records_to_styler(value))
            return self._styler_to_dataframe(value)
        if output_type == "dictionary":
            if isinstance(value, list):
                return [dict(item) for item in value]
            return self._styler_to_dataframe(value).to_dict(orient="records")
        raise ValueError(f"Unsupported output_type {output_type!r}.")

    @signal(tags=["query"])
    @digest()
    def info(self,
             element='system',
             selection='all',
             syntax='MolSysMT',
             mask='all',
             source='all',
             output_type='styler',
             skip_digestion=False
            ):
        if source == "view":
            return self._convert_info_output(self._viewer_info_records(), output_type)

        kwargs = dict(
            element=element,
            selection=selection,
            syntax=syntax,
            skip_digestion=True,
        )
        if "mask" in inspect.signature(msm.info).parameters:
            kwargs["mask"] = mask
        molsys_info = msm.info(self._molsys, **kwargs)

        if source == "molsys":
            return self._convert_info_output(molsys_info, output_type)

        if source == "all":
            from .core import ViewerInfo
            return ViewerInfo(
                molsys_section=self._convert_info_output(molsys_info, output_type),
                view_section=self._convert_info_output(self._viewer_info_records(), output_type),
            )

        raise ValueError("info(source=...) only accepts 'all', 'molsys', or 'view'.")

    @signal(tags=["selection"])
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
        """Select indices from the current molecular system (MolSysMT selection language).

        Notes
        -----
        This method intentionally focuses on the common workflow: returning indices.
        """
        local_res = msm.select(
            self._molsys,
            selection=selection,
            structure_indices=structure_indices,
            element=element,
            mask=mask,
            syntax=syntax,
            skip_digestion=True,
        )
        return local_res

    @signal(tags=["query"])
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
        """Retrieve attribute values from the current molecular system (MolSysMT get)."""
        return msm.get(
            self._molsys,
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

    @signal(tags=["convert"])
    @dep_digest("molsysmt")
    @digest()
    def convert(
        self,
        to_form="molsysmt.MolSys",
        *,
        selection="all",
        structure_indices="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ):
        """Convert this viewer to another form.

        Notes
        -----
        The initial implementation delegates conversion to the current
        molecular system stored in the view. Future target forms may support
        richer viewer-state-aware conversions when MolSysMT exposes them.
        """
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before calling convert().")

        return msm.convert(
            self._molsys,
            to_form=to_form,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            skip_digestion=True,
            **kwargs,
        )

    @signal(tags=["query"])
    @digest()
    def contains(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ) -> bool:
        """Check whether the loaded molecular system contains the requested features."""
        return bool(
            msm.contains(
                self._molsys,
                selection=selection,
                syntax=syntax,
                skip_digestion=True,
                **kwargs,
            )
        )

    @signal(tags=["query"])
    @digest()
    def is_composed_of(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ) -> bool:
        """Check whether the loaded molecular system is composed of the requested classes/counts."""
        return bool(
            msm.is_composed_of(
                self._molsys,
                selection=selection,
                syntax=syntax,
                skip_digestion=True,
                **kwargs,
            )
        )

    @signal(tags=["query"])
    @digest()
    def extract(
        self,
        selection="all",
        structure_indices="all",
        *,
        syntax="MolSysMT",
        debug_js: bool | None = None,
        skip_digestion: bool = False,
    ):
        """Return a new view built from a structural subset of this view.

        Regions, shapes, annotations, measurements, saved selections, and
        sections are migrated to the new view with atom indices remapped to
        the extracted subset.  See :func:`~tools.basic.extract.extract` for
        full details.
        """
        from ..tools.basic.extract import extract as _extract_view

        return _extract_view(
            self,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            debug_js=debug_js,
            skip_digestion=True,
        )


MolSysMTInterfaceMixin.__module__ = "molsysviewer.viewer"
for _name, _value in MolSysMTInterfaceMixin.__dict__.items():
    if callable(_value):
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception:
            pass
