"""Review and accept a new baseline without remapping or changing scene data."""

import json
from copy import deepcopy

from ._movie_appearance import appearance_baseline
from ._movie_scene import fingerprint, same_data, scene_changes
from ._movie_timeline import _VISIBILITY_DOMAINS, _camera, _scene_visibility, _track, _vector
from .frontend_requests import FrontendRequestError

_SCHEMA = "molsysviewer.movie_rebase_review@1"


def review_rebase(movie, camera):
    timeline = movie._timeline
    if timeline is None:
        raise ValueError("Set a Movie baseline before reviewing a rebase.")
    original = timeline.to_dict()
    before = original["baseline"]
    selected = before["camera"] if camera is None else camera
    _camera(selected)  # Validate geometry before building any candidate.
    requested = {key: _vector(selected[key], key).tolist() for key in ("position", "target", "up")}
    view = movie._view
    current = view.export_state(skip_digestion=True)
    binding = view._source_state_binding()
    conflicts = []
    candidate = None
    if binding != before["binding"]:
        conflicts.append({"reason": "molecular_binding_changed", "track": None})
    else:
        old_visibility = _scene_visibility(before["scene"])
        new_visibility = _scene_visibility(current)
        for track in original["tracks"]:
            domain, tag = track["target"]["domain"], track["target"].get("tag")
            if domain not in {"camera", "structure", "scene", "whole"}:
                old = old_visibility.get((domain, tag))
                new = new_visibility.get((domain, tag))
                if new is None or old[1] != new[1]:
                    conflicts.append(
                        {
                            "reason": "target_missing" if new is None else "target_replaced",
                            "track": track["tag"],
                            "domain": domain,
                            "tag": tag,
                        }
                    )
                    continue
            try:
                _track(track, new_visibility, binding["n_structures"], timeline.duration_ms, current)
            except (ValueError, TypeError, KeyError) as error:
                conflicts.append({"reason": "incompatible_track", "track": track["tag"], "message": str(error)})
        if not conflicts:
            try:
                view._preflight_state_import(current, clear_first=True, on_conflict="raise")
                candidate = timeline.rebased(current, requested, binding)
            except (ValueError, TypeError, KeyError) as error:
                conflicts.append({"reason": "invalid_scene", "track": None, "message": str(error)})
    changes = scene_changes(before["scene"], current, _VISIBILITY_DOMAINS)
    if before["camera"] != requested:
        changes.append(
            {
                "domain": "camera",
                "tag": None,
                "change": "changed",
                "fields": ["pose"],
                "before": before["camera"],
                "after": requested,
            }
        )
    if before["scene"]["view"]["structure_index"] != current.get("view", {}).get("structure_index"):
        changes.append(
            {
                "domain": "structure",
                "tag": None,
                "change": "changed",
                "fields": ["index"],
                "before": before["scene"]["view"]["structure_index"],
                "after": current.get("view", {}).get("structure_index"),
            }
        )
    affected = []
    if candidate is not None:
        after = candidate.to_dict()["baseline"]
        for track in original["tracks"]:
            if track["keys"][0]["time_ms"] == 0:
                continue
            domain, tag, prop = track["target"]["domain"], track["target"].get("tag"), track["property"]

            def value(base, visibility, domain=domain, tag=tag, prop=prop):
                if domain == "camera":
                    return base["camera"]
                if domain == "structure":
                    return base["scene"]["view"]["structure_index"]
                if prop == "visible":
                    return visibility[domain, tag][0]
                return appearance_baseline(base["scene"], domain, tag, prop)

            if not same_data(value(before, old_visibility), value(after, new_visibility)):
                affected.append(track["tag"])
    # Passive camera telemetry does not change the reviewed scene definition.
    context = deepcopy(current)
    context.get("view", {}).pop("camera", None)
    return {
        "schema": _SCHEMA,
        "recipe_sha256": fingerprint(original),
        "scene_sha256": fingerprint(context),
        "camera": requested,
        "changes": changes,
        "conflicts": conflicts,
        "affected_tracks": affected,
        "can_apply": candidate is not None and not conflicts,
        "candidate": None if candidate is None else candidate.to_dict(),
    }


def rebase(movie, review):
    if any(
        value is not None
        for value in (movie._seek_request, movie._playback, movie._export_job, movie._view._movie_export_frames)
    ):
        raise FrontendRequestError(reason="movie_operation_pending")
    if not isinstance(review, dict) or review.get("schema") != _SCHEMA or "camera" not in review:
        raise ValueError("Expected a Movie rebase review.")
    review = json.loads(json.dumps(review, allow_nan=False))
    expected = review_rebase(movie, review["camera"])
    if not same_data(review, expected):
        raise ValueError("Movie rebase review is stale or edited; request a new review.")
    if not expected["can_apply"]:
        raise ValueError("Movie rebase has conflicts; repair its targets or scene before reviewing again.")
    current = movie._view.export_state(skip_digestion=True)
    context = deepcopy(current)
    context.get("view", {}).pop("camera", None)
    if (
        fingerprint(movie._timeline.to_dict()) != expected["recipe_sha256"]
        or fingerprint(context) != expected["scene_sha256"]
    ):
        raise ValueError("Movie rebase review was superseded while validating the scene.")
    timeline = movie._timeline.rebased(current, expected["camera"], movie._view._source_state_binding())
    movie._install_timeline(timeline)
