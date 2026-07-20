"""Playback argument digesters for ``MolSysView.play()``.

`play()` was unusable from the public API: every argument defaults to ``None``,
but `mode` and `step` rejected ``None`` outright, and `mode`/`direction` only
recognised the ``molsysviewer.player.*`` callers — while `MolSysView.play()`
normalises to ``molsysviewer.viewer.play``. So even an explicit, valid mode was
refused from the public entry point.
"""

from __future__ import annotations

import pytest

from molsysviewer._private.arg_digestion.argument.direction import digest_direction
from molsysviewer._private.arg_digestion.argument.mode import digest_mode
from molsysviewer._private.arg_digestion.argument.step import digest_step
from molsysviewer._private.exceptions import ArgumentError

PLAY_CALLER = "molsysviewer.viewer.play"
PLAYER_CALLER = "molsysviewer.player.play"


# --- mode ------------------------------------------------------------------

@pytest.mark.parametrize("caller", [PLAY_CALLER, PLAYER_CALLER])
def test_mode_none_is_left_to_the_callee(caller):
    assert digest_mode(None, caller=caller) is None


@pytest.mark.parametrize("caller", [PLAY_CALLER, PLAYER_CALLER])
@pytest.mark.parametrize("mode", ["loop", "once", "ping-pong"])
def test_mode_accepts_playback_modes_from_both_entry_points(caller, mode):
    assert digest_mode(mode, caller=caller) == mode


@pytest.mark.parametrize("caller", [PLAY_CALLER, PLAYER_CALLER])
def test_mode_rejects_unknown_playback_mode(caller):
    with pytest.raises(ArgumentError):
        digest_mode("turbo", caller=caller)


# --- direction -------------------------------------------------------------

@pytest.mark.parametrize("caller", [PLAY_CALLER, PLAYER_CALLER])
def test_direction_none_is_left_to_the_callee(caller):
    assert digest_direction(None, caller=caller) is None


@pytest.mark.parametrize("caller", [PLAY_CALLER, PLAYER_CALLER])
@pytest.mark.parametrize("direction", ["forward", "backward"])
def test_direction_accepts_travel_sense_from_both_entry_points(caller, direction):
    assert digest_direction(direction, caller=caller) == direction


@pytest.mark.parametrize("caller", [PLAY_CALLER, PLAYER_CALLER])
def test_direction_rejects_unknown_travel_sense(caller):
    # must not fall through to the 3D-vector branch
    with pytest.raises(ArgumentError):
        digest_direction("sideways", caller=caller)


def test_direction_still_digests_vectors_outside_playback():
    result = digest_direction([1.0, 0.0, 0.0], caller="molsysviewer.viewer.whatever")
    assert result.shape == (1, 3)


# --- step ------------------------------------------------------------------

def test_step_none_is_left_to_the_callee():
    assert digest_step(None, caller=PLAY_CALLER) is None


def test_step_accepts_integers():
    assert digest_step(3, caller=PLAY_CALLER) == 3


@pytest.mark.parametrize("given", ["dos", 1.5, True, None if False else object()])
def test_step_rejects_non_integers(given):
    # booleans are ints in Python but are not a meaningful step size
    with pytest.raises(ArgumentError):
        digest_step(given, caller=PLAY_CALLER)
