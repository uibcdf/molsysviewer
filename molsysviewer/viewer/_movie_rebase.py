"""Review and accept a new baseline without remapping or changing scene data."""

import json
from copy import deepcopy
from uuid import uuid4

from ._movie_appearance import appearance_baseline
from ._movie_scene import fingerprint, same_data, scene_changes
from ._movie_timeline import _VISIBILITY_DOMAINS, _camera, _scene_visibility, _track, _vector
from .frontend_requests import FrontendRequestError

_SCHEMA = "molsysviewer.movie_rebase_review@1"


def review_rebase(movie, camera, *, observation=None, capture_id=None):
    timeline = movie._timeline
    if timeline is None:
        raise ValueError("Set a Movie baseline before reviewing a rebase.")
    original = timeline.to_dict()
    before = original["baseline"]
    selected = before["camera"] if camera is None else camera
    if observation is not None:
        selected = observation.captured.state["view"]["camera"]
    _camera(selected)  # Validate geometry before building any candidate.
    requested = {key: _vector(selected[key], key).tolist() for key in ("position", "target", "up")}
    view = movie._view
    current = view.export_state(skip_digestion=True) if observation is None else deepcopy(observation.captured.state)
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
                candidate = timeline.rebased(
                    current,
                    requested,
                    binding,
                    environment_capture=None if observation is None else observation.environment_capture,
                )
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
        "scene_sha256": fingerprint(context) if observation is None else "sha256:" + observation.captured.scene_key,
        "camera": requested,
        "changes": changes,
        "conflicts": conflicts,
        "affected_tracks": affected,
        "can_apply": candidate is not None and not conflicts,
        "candidate": None if candidate is None else candidate.to_dict(),
        **(
            {"capture": {"schema": "molsysviewer.movie_rebase_capture@1", "id": capture_id, "endpoint": "primary"}}
            if observation is not None
            else {}
        ),
    }


async def review_rebase_async(movie, *, timeout):
    from ._movie_baseline import observe_movie_scene

    observation = await observe_movie_scene(movie, timeout=timeout, require_baseline=True)
    with movie._view._system_edits._locked():
        observation.validate(movie, delivery=True)
        capture_id = uuid4().hex
        review = review_rebase(movie, None, observation=observation, capture_id=capture_id)
        # Only the resumed caller may publish the private observation ticket.
        # One current ticket bounds retained data; failed captures keep the old one.
        observation.validate(movie, delivery=True)
        movie._rebase_capture = capture_id, observation
        return review


def _accept_rebase(movie, review):
    if any(
        value is not None
        for value in (movie._seek_request, movie._playback, movie._export_job, movie._view._movie_export_frames)
    ):
        raise FrontendRequestError(reason="movie_operation_pending")
    if not isinstance(review, dict) or review.get("schema") != _SCHEMA or "camera" not in review:
        raise ValueError("Expected a Movie rebase review.")
    review = json.loads(json.dumps(review, allow_nan=False))
    observation = None
    capture_id = None
    if "capture" in review:
        cached = movie._rebase_capture
        if not isinstance(review["capture"], dict) or cached is None or review["capture"].get("id") != cached[0]:
            raise ValueError("Movie rebase capture has expired; request a new live review.")
        capture_id, observation = cached
        observation.validate(movie)
    expected = review_rebase(movie, review["camera"], observation=observation, capture_id=capture_id)
    if not same_data(review, expected):
        raise ValueError("Movie rebase review is stale or edited; request a new review.")
    if not expected["can_apply"]:
        raise ValueError("Movie rebase has conflicts; repair its targets or scene before reviewing again.")
    current = movie._view.export_state(skip_digestion=True)
    context = deepcopy(current)
    context.get("view", {}).pop("camera", None)
    if observation is not None:
        observation.validate(movie)
    if fingerprint(movie._timeline.to_dict()) != expected["recipe_sha256"] or (
        observation is None and fingerprint(context) != expected["scene_sha256"]
    ):
        raise ValueError("Movie rebase review was superseded while validating the scene.")
    timeline = movie._timeline.rebased(
        current if observation is None else observation.captured.state,
        expected["camera"],
        movie._view._source_state_binding(),
        environment_capture=None if observation is None else observation.environment_capture,
    )
    movie._install_timeline(timeline)


def rebase(movie, review):
    with movie._view._system_edits._locked():
        _accept_rebase(movie, review)
