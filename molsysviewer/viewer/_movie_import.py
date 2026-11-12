"""Review declared Movie correspondences against a prepared destination scene."""

import json
from copy import deepcopy
from uuid import uuid4

from .._private.structure_correspondence import normalize_structure_index_map
from ._movie_appearance import appearance_baseline
from ._movie_baseline import check_idle
from ._movie_scene import fingerprint, same_data, scene_changes
from ._movie_timeline import (
    _MAX_SAFE_INTEGER,
    _VISIBILITY_DOMAINS,
    _binding,
    _camera,
    _MovieTimeline,
    _scene_visibility,
    _tag,
)
from .visual_capture import _scene_key

_SCHEMA = "molsysviewer.movie_import_review@1"
_PROVENANCE = "molsysviewer.movie_import@1"
_LEGACY_PROVENANCE = "molsysviewer.movie_import@2"


def _reference(value, *, legacy=False):
    if not isinstance(value, dict) or set(value) != {"domain", "tag"}:
        raise ValueError("A Movie target-map reference requires domain and tag.")
    domain = value["domain"]
    valid = isinstance(domain, str) and (domain == "legacy" if legacy else domain in _VISIBILITY_DOMAINS)
    if not valid:
        raise ValueError("Target maps require a legacy source or an existing tagged scene domain, as applicable.")
    return {"domain": domain, "tag": _tag(value["tag"])}


def normalize_target_map(value, *, legacy=False):
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError("target_map must be a list of source/target records.")
    result, sources, targets = [], set(), set()
    for row in value:
        if not isinstance(row, dict) or set(row) != {"source", "target"}:
            raise ValueError("Each target map requires source and target references.")
        source = _reference(row["source"], legacy=legacy)
        target = _reference(row["target"])
        if not legacy and source["domain"] != target["domain"]:
            raise ValueError("Version-2 target maps retain the scene domain.")
        a, b = tuple(source.values()), tuple(target.values())
        if a in sources or b in targets:
            raise ValueError("Movie target maps must be one-to-one, without duplicate sources or destinations.")
        sources.add(a)
        targets.add(b)
        result.append({"source": source, "target": target})
    return sorted(result, key=lambda row: tuple(row["source"].values()))


def validate_provenance(value, *, destination_count):
    fields = {
        "schema",
        "source_sha256",
        "source_version",
        "source_binding",
        "target_map",
        "structure_index_map",
        "warnings",
        "targets",
    }
    if not isinstance(value, dict) or set(value) != fields or value["schema"] not in (_PROVENANCE, _LEGACY_PROVENANCE):
        raise ValueError("Invalid Movie import provenance.")
    legacy = value["schema"] == _LEGACY_PROVENANCE
    version = value["source_version"]
    if type(version) is not int or version != (1 if legacy else 2):
        raise ValueError("Invalid imported Movie source version.")
    digest = value["source_sha256"]
    if (
        not isinstance(digest, str)
        or len(digest) != 71
        or not digest.startswith("sha256:")
        or any(c not in "0123456789abcdef" for c in digest[7:])
    ):
        raise ValueError("Movie import provenance requires a SHA-256 source digest.")
    if legacy and value["source_binding"] is not None:
        raise ValueError("Legacy Movie provenance cannot invent a source molecular binding.")
    binding = None if legacy else _binding(value["source_binding"])
    normalize_target_map(value["target_map"], legacy=legacy)
    indices = value["structure_index_map"]
    if indices is not None:
        # This is a representable-index bound, not an inferred source count.
        normalize_structure_index_map(
            indices, _MAX_SAFE_INTEGER + 1 if legacy else binding["n_structures"], destination_count
        )
    warnings = value["warnings"]
    if not isinstance(warnings, list) or any(not isinstance(code, str) or not code for code in warnings):
        raise ValueError("Movie import warnings must be explicit string codes.")
    targets = value["targets"]
    if not isinstance(targets, list):
        raise ValueError("Movie import targets must be a list of association records.")
    tags = set()
    for row in targets:
        if not isinstance(row, dict) or set(row) != {"track", "source", "target", "source_identity", "target_identity"}:
            raise ValueError("Invalid Movie import target association.")
        tag = _tag(row["track"])
        if tag in tags:
            raise ValueError("Movie import associations require unique track tags.")
        tags.add(tag)
        source = _reference(row["source"], legacy=legacy)
        target = _reference(row["target"])
        if not legacy and source["domain"] != target["domain"]:
            raise ValueError("Movie import associations retain the scene domain.")
        if legacy and (row["source_identity"] != {} or {"source": source, "target": target} not in value["target_map"]):
            raise ValueError("Legacy Movie associations require a declared target and an unknown source identity.")
        for field in ("source_identity", "target_identity"):
            identity = row[field]
            if (
                not isinstance(identity, dict)
                or set(identity) - {"uid", "definition_sha256", "analysis_name", "analysis_revision", "op"}
                or any(val is not None and not isinstance(val, str) for val in identity.values())
            ):
                raise ValueError("Invalid Movie import target identity.")
            definition = identity.get("definition_sha256")
            if definition is not None and (
                len(definition) != 71
                or not definition.startswith("sha256:")
                or any(c not in "0123456789abcdef" for c in definition[7:])
            ):
                raise ValueError("Movie region definition requires a SHA-256 digest.")
    return json.loads(json.dumps(value, allow_nan=False))


def _target_record(scene, domain, tag):
    return next((row for row in scene.get(_VISIBILITY_DOMAINS[domain], []) if row["tag"] == tag), None)


def _identity(scene, domain, record):
    if domain == "region":
        from ..regions import Region

        # Region UIDs are local to a View, not globally unique. Include the
        # molecular definition and dependency closure before allowing an
        # implicit correspondence between separately prepared scenes.
        by_uid = {row["uid"]: row for row in scene.get("regions", []) if isinstance(row.get("uid"), str)}
        definitions, pending = {}, [record]
        while pending:
            row = pending.pop()
            uid = row.get("uid")
            if not isinstance(uid, str) or not uid:
                raise ValueError(
                    "Movie imports require the region's complete source UID/definition, not a preview recipe."
                )
            if uid in definitions:
                continue
            definitions[uid] = {field: row.get(field) for field in ("atom_indices", "selection", "provenance", "mode")}
            provenance = row.get("provenance") or {}
            if not isinstance(provenance, dict):
                raise ValueError("Movie region provenance must be an object.")
            for dependency in Region._dependency_uids_from_provenance(provenance):
                if dependency in by_uid:
                    pending.append(by_uid[dependency])
                else:
                    definitions[dependency] = {"missing": True}
        return {"uid": record["uid"], "definition_sha256": fingerprint(definitions)}
    fields = ("analysis_name", "analysis_revision") if domain == "interaction" else ("op",)
    return {field: record.get(field) for field in fields}


def _propose(movie, source, options, review_id):
    if source["molsysmovie_version"] == 1:
        return _propose_legacy(movie, source, options, review_id)
    view = movie._view
    scene = view.export_state(skip_digestion=True)
    context_key = _scene_key(scene, version=2)
    destination_movie = fingerprint(movie.to_dict(skip_digestion=True))
    binding = view._source_state_binding()
    if binding is None:
        raise ValueError("Load a molecular system before importing a Movie.")
    version = source["molsysmovie_version"]
    mapping = options["target_map"]
    explicit = {(r["source"]["domain"], r["source"]["tag"]): r["target"] for r in mapping}
    warnings, conflicts, targets, affected = [], [], [], []
    original = _MovieTimeline(source)
    old = original.to_dict()
    before = old["baseline"]
    tracks = old["tracks"]
    duration = old["duration_ms"]
    selected_camera = before["camera"] if options["camera"] is None else options["camera"]
    initial = before["scene"]["view"]["structure_index"]
    old_count = before["binding"]["n_structures"]
    changed_binding = before["binding"] != binding
    _camera(selected_camera)
    scene["view"]["camera"] = deepcopy(selected_camera)
    indices = options["structure_index_map"]
    inverse = None
    if indices is not None:
        indices = normalize_structure_index_map(indices, old_count, binding["n_structures"])
        inverse = {}
        for new, old_index in enumerate(indices):
            if old_index is not None:
                inverse.setdefault(old_index, []).append(new)
    elif changed_binding:
        conflicts.append({"reason": "structure_map_required"})
    frame_conflicts = {}

    def remap_frame(index):
        matches = (
            ([index] if 0 <= index < binding["n_structures"] else []) if inverse is None else inverse.get(index, [])
        )
        if len(matches) != 1:
            reason = "unmapped_structure" if not matches else "ambiguous_structure"
            frame_conflicts.setdefault(reason, set()).add(index)
            return index
        return matches[0]

    if initial is not None:
        scene["view"]["structure_index"] = remap_frame(initial)
    used = set()
    for track in tracks:
        domain, tag = track["target"]["domain"], track["target"].get("tag")
        if domain == "structure":
            for key in track["keys"]:
                key["value"] = remap_frame(key["value"])
        if tag is None:
            continue
        identity = domain, tag
        used.add(identity)
        destination = explicit.get(identity, {"domain": domain, "tag": tag})
        if changed_binding and identity not in explicit:
            conflicts.append({"reason": "target_map_required", "source": track["target"], "track": track["tag"]})
            continue
        new_domain, new_tag = destination["domain"], destination["tag"]
        current = _target_record(scene, new_domain, new_tag)
        if current is None:
            conflicts.append({"reason": "target_missing", "source": track["target"], "target": destination})
            continue
        old_record = _target_record(before["scene"], domain, tag)
        source_identity = _identity(before["scene"], domain, old_record)
        target_identity = _identity(scene, new_domain, current)
        changed = source_identity != target_identity
        if changed and identity not in explicit:
            conflicts.append({"reason": "target_replaced", "source": track["target"], "track": track["tag"]})
            continue
        if changed:
            warnings.append("scientific_target_rebound" if domain == "interaction" else "target_identity_rebound")
        targets.append(
            {
                "track": track["tag"],
                "source": deepcopy(track["target"]),
                "target": deepcopy(destination),
                "source_identity": source_identity,
                "target_identity": target_identity,
            }
        )
        track["target"] = deepcopy(destination)
    if set(explicit) - used:
        raise ValueError("Target map contains a source not referenced by this Movie.")
    for reason, values in sorted(frame_conflicts.items()):
        conflicts.append({"reason": reason, "source_indices": sorted(values)})
    if changed_binding:
        warnings.extend(["molecular_binding_rebound", "camera_world_coordinates_unchanged"])
    candidate = None
    if not conflicts:
        provenance = {
            "schema": _PROVENANCE,
            "source_sha256": fingerprint(source),
            "source_version": version,
            "source_binding": before["binding"],
            "target_map": mapping,
            "structure_index_map": indices,
            "warnings": sorted(set(warnings)),
            "targets": targets,
        }
        data = {
            "molsysmovie_version": 2,
            "duration_ms": duration,
            "units": {"time": "ms", "camera_length": "angstrom"},
            "baseline": {"scene": scene, "camera": selected_camera, "binding": binding},
            "tracks": tracks,
            "provenance": provenance,
        }
        for field in ("color_interpolation", "camera_interpolation"):
            if field in source:
                data[field] = source[field]
        try:
            view._preflight_state_import(scene, clear_first=True, on_conflict="raise")
            candidate = _MovieTimeline(data).to_dict()
        except (ValueError, TypeError, KeyError) as error:
            conflicts.append({"reason": "incompatible_scene_or_track", "message": str(error)})
    if candidate is not None:
        new_vis, old_vis = _scene_visibility(scene), _scene_visibility(before["scene"])
        for old_track, new_track in zip(source["tracks"], candidate["tracks"], strict=True):
            if old_track["keys"][0]["time_ms"] == 0:
                continue

            def value(track, base_scene, camera, visibility):
                domain, tag, prop = track["target"]["domain"], track["target"].get("tag"), track["property"]
                if domain == "camera":
                    return camera
                if domain == "structure":
                    return base_scene["view"]["structure_index"]
                if prop == "visible":
                    return visibility[domain, tag][0]
                return appearance_baseline(base_scene, domain, tag, prop)

            if not same_data(
                value(old_track, before["scene"], before["camera"], old_vis),
                value(new_track, scene, candidate["baseline"]["camera"], new_vis),
            ):
                affected.append(old_track["tag"])
    changes = scene_changes(before["scene"], scene, _VISIBILITY_DOMAINS)
    for domain, field, a, b in (
        ("camera", "pose", before["camera"], selected_camera),
        ("structure", "index", before["scene"]["view"]["structure_index"], scene["view"]["structure_index"]),
    ):
        if not same_data(a, b):
            changes.append(
                {"domain": domain, "tag": None, "change": "changed", "fields": [field], "before": a, "after": b}
            )
    return _finish(
        movie,
        source,
        options,
        review_id,
        context_key,
        destination_movie,
        target_binding=binding,
        targets=targets,
        changes=changes,
        affected_tracks=affected,
        warnings=sorted(set(warnings)),
        conflicts=conflicts,
        can_apply=candidate is not None and not conflicts,
        candidate=candidate,
    )


def _finish(movie, source, options, review_id, context_key, destination_movie, **report):
    if (
        _scene_key(movie._view.export_state(skip_digestion=True), version=2) != context_key
        or fingerprint(movie.to_dict(skip_digestion=True)) != destination_movie
    ):
        raise ValueError("Movie import context changed while validating the proposal.")
    return {
        "schema": _SCHEMA,
        "review_id": review_id,
        "source": deepcopy(source),
        "options": deepcopy(options),
        "scene_sha256": "sha256:" + context_key,
        "destination_movie_sha256": destination_movie,
        "source_sha256": fingerprint(source),
        **report,
    }


def _propose_legacy(movie, source, options, review_id):
    from ._movie_legacy import compile_legacy

    view = movie._view
    scene = view.export_state(skip_digestion=True)
    context_key = _scene_key(scene, version=2)
    destination_movie = fingerprint(movie.to_dict(skip_digestion=True))
    binding = view._source_state_binding()
    if binding is None:
        raise ValueError("Load a molecular system before importing a Movie.")
    before = deepcopy(scene)
    compiled = compile_legacy(source, options["camera"])
    conflicts, tracks = compiled["conflicts"], compiled["tracks"]
    warnings, targets, affected = ["legacy_source_binding_unknown"], [], []
    mapping = options["target_map"]
    explicit = {(r["source"]["domain"], r["source"]["tag"]): r["target"] for r in mapping}
    indices = options["structure_index_map"]
    inverse = None
    if indices is not None:
        indices = normalize_structure_index_map(indices, _MAX_SAFE_INTEGER + 1, binding["n_structures"])
        inverse = {}
        for new, old in enumerate(indices):
            if old is not None:
                inverse.setdefault(old, []).append(new)
    frame_conflicts = {}

    def remap_frame(index):
        matches = ([index] if index < binding["n_structures"] else []) if inverse is None else inverse.get(index, [])
        if len(matches) != 1:
            reason = "unmapped_structure" if not matches else "ambiguous_structure"
            frame_conflicts.setdefault(reason, set()).add(index)
            return index
        return matches[0]

    if compiled["camera"] is not None:
        scene["view"]["camera"] = compiled["camera"]
    if compiled["initial_structure"] is not None:
        scene["view"]["structure_index"] = remap_frame(compiled["initial_structure"])
        warnings.append("legacy_structure_correspondence_declared")
    used = set()
    for track in tracks:
        domain = track["target"]["domain"]
        if domain == "structure":
            for key in track["keys"]:
                key["value"] = remap_frame(key["value"])
        if domain != "legacy":
            continue
        identity = domain, track["target"]["tag"]
        used.add(identity)
        target = explicit.get(identity)
        if target is None:
            conflicts.append({"reason": "legacy_target_map_required", "source": track["target"], "track": track["tag"]})
            continue
        record = _target_record(scene, target["domain"], target["tag"])
        if record is None:
            conflicts.append({"reason": "target_missing", "source": track["target"], "target": target})
            continue
        targets.append(
            {
                "track": track["tag"],
                "source": deepcopy(track["target"]),
                "target": deepcopy(target),
                "source_identity": {},
                "target_identity": _identity(scene, target["domain"], record),
            }
        )
        track["target"] = deepcopy(target)
        warnings.append("legacy_target_correspondence_declared")
        if track["keys"][0]["time_ms"] > 0:
            affected.append(track["tag"])
            warnings.append("legacy_initial_visibility_from_destination")
    if set(explicit) - used:
        raise ValueError("Target map contains a source not referenced by this Movie.")
    for reason, values in sorted(frame_conflicts.items()):
        conflicts.append({"reason": reason, "source_indices": sorted(values)})
    candidate = None
    if not conflicts:
        data = {
            "molsysmovie_version": 2,
            "duration_ms": compiled["duration_ms"],
            "units": {"time": "ms", "camera_length": "angstrom"},
            "baseline": {"scene": scene, "camera": compiled["camera"], "binding": binding},
            "camera_interpolation": "cartesian-constant-up@1",
            "tracks": tracks,
            "provenance": {
                "schema": _LEGACY_PROVENANCE,
                "source_sha256": fingerprint(source),
                "source_version": 1,
                "source_binding": None,
                "target_map": mapping,
                "structure_index_map": indices,
                "warnings": sorted(set(warnings)),
                "targets": targets,
            },
        }
        try:
            view._preflight_state_import(scene, clear_first=True, on_conflict="raise")
            candidate = _MovieTimeline(data).to_dict()
        except (ValueError, TypeError, KeyError) as error:
            conflicts.append({"reason": "incompatible_legacy_scene_or_path", "message": str(error)})
    changes = []
    for domain, field in (("camera", "pose"), ("structure", "index")):
        key = "camera" if domain == "camera" else "structure_index"
        a, b = before["view"].get(key), scene["view"].get(key)
        if not same_data(a, b):
            changes.append(
                {"domain": domain, "tag": None, "change": "changed", "fields": [field], "before": a, "after": b}
            )
    return _finish(
        movie,
        source,
        options,
        review_id,
        context_key,
        destination_movie,
        target_binding=binding,
        targets=targets,
        changes=changes,
        affected_tracks=affected,
        warnings=sorted(set(warnings)),
        conflicts=conflicts,
        can_apply=candidate is not None and not conflicts,
        candidate=candidate,
    )


def review_import(movie, data, *, target_map, structure_index_map, camera):
    with movie._view._system_edits._locked():
        check_idle(movie)
        source = json.loads(json.dumps(data, allow_nan=False))
        if (
            not isinstance(source, dict)
            or type(source.get("molsysmovie_version")) is not int
            or source["molsysmovie_version"] not in (1, 2)
        ):
            raise ValueError("Reviewed imports require a version-1 or version-2 Movie recipe.")
        options = {
            "target_map": normalize_target_map(target_map, legacy=source["molsysmovie_version"] == 1),
            "structure_index_map": None if structure_index_map is None else list(structure_index_map),
            "camera": None if camera is None else _camera(camera)[0],
        }
        review_id = uuid4().hex
        report = _propose(movie, source, options, review_id)
        movie._import_review = review_id, source, options
        return report


def apply_import(movie, review):
    with movie._view._system_edits._locked():
        check_idle(movie)
        cached = movie._import_review
        if (
            not isinstance(review, dict)
            or review.get("schema") != _SCHEMA
            or cached is None
            or review.get("review_id") != cached[0]
        ):
            raise ValueError("Movie import review has expired; request a new review.")
        expected = _propose(movie, cached[1], cached[2], cached[0])
        if not same_data(review, expected):
            raise ValueError("Movie import review is stale or edited; request a new review.")
        if not expected["can_apply"]:
            raise ValueError("Movie import has conflicts; repair its explicit correspondences before reviewing again.")
        movie._install_timeline(_MovieTimeline(expected["candidate"]))
