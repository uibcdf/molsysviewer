"""The argument contracts of the `molsysviewer.remote` surface.

`molsysviewer.remote` was invisible to the public API inventory until it became an
explicit root: `import molsysviewer` does not import it, so the walk never reached it.
Four public callables had been undigested for as long as the module existed, and five of
their argument names had no digester at all (`uibcdf/molsysviewer#83`).

The collision worth knowing about is in `test_the_packet_argument_is_not_named_value`.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from molsysviewer._private.argdigest.argument.expected_endpoint_id import (
    digest_expected_endpoint_id,
)
from molsysviewer._private.argdigest.argument.expected_session_id import (
    digest_expected_session_id,
)
from molsysviewer._private.argdigest.argument.expected_viewer_id import (
    digest_expected_viewer_id,
)
from molsysviewer._private.argdigest.argument.explicit import digest_explicit
from molsysviewer._private.argdigest.argument.packet import digest_packet
from molsysviewer._private.argdigest.argument.renderer import digest_renderer
from molsysviewer._private.exceptions import ArgumentError
from molsysviewer.remote import (
    find_chromium_executable,
    is_software_renderer,
    validate_input_packet,
    validate_signaling_packet,
)

#: The three identity axes are one rule stated three times, so they are swept together.
IDENTITY_DIGESTERS = (
    digest_expected_viewer_id,
    digest_expected_session_id,
    digest_expected_endpoint_id,
)


# --- the identity trio -----------------------------------------------------

@pytest.mark.parametrize("digest", IDENTITY_DIGESTERS)
def test_none_leaves_that_identity_unchecked(digest):
    assert digest(None) is None


@pytest.mark.parametrize("digest", IDENTITY_DIGESTERS)
def test_an_identifier_survives_unstripped(digest):
    """Stripping would let `" a"` accept a packet claiming `"a"`.

    `_common_identity` compares for exact equality, so any normalisation here is an
    identity match nobody asked for.
    """
    assert digest(" spaced-id ") == " spaced-id "


@pytest.mark.parametrize("digest", IDENTITY_DIGESTERS)
@pytest.mark.parametrize("blank", ["", "   ", "\n"])
def test_a_blank_expectation_is_refused(digest, blank):
    """A packet's own identifiers must be non-empty, so `""` can never match.

    Passing it through would mean an identity check that silently refuses everything.
    """
    with pytest.raises(ArgumentError):
        digest(blank)


@pytest.mark.parametrize("digest", IDENTITY_DIGESTERS)
@pytest.mark.parametrize("value", [0, 1, True, b"bytes", ["id"], {"id": 1}])
def test_an_identifier_that_is_not_a_string_is_refused(digest, value):
    with pytest.raises(ArgumentError):
        digest(value)


# --- explicit --------------------------------------------------------------

def test_no_executable_asked_for_means_search_the_path():
    assert digest_explicit(None) is None


def test_a_path_object_is_handed_over_as_a_string():
    assert digest_explicit(Path("/usr/bin/chromium")) == "/usr/bin/chromium"


def test_a_string_path_is_kept():
    assert digest_explicit("/usr/bin/chromium") == "/usr/bin/chromium"


@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_executable_is_refused_rather_than_read_as_none(blank):
    """Falling back to the PATH here would start a browser the caller did not choose."""
    with pytest.raises(ArgumentError):
        digest_explicit(blank)


@pytest.mark.parametrize("value", [1, True, ["/usr/bin/chromium"]])
def test_an_executable_that_is_not_a_path_is_refused(value):
    with pytest.raises(ArgumentError):
        digest_explicit(value)


# --- renderer --------------------------------------------------------------

@pytest.mark.parametrize(
    "renderer",
    [
        "llvmpipe (LLVM 19.1.7, 256 bits)",
        "ANGLE (NVIDIA Corporation, NVIDIA GeForce GTX 1080, OpenGL 4.6)",
    ],
)
def test_a_renderer_string_is_free_text_and_survives_whole(renderer):
    """Driver-written text: there is no set of values to enumerate, and none is invented."""
    assert digest_renderer(renderer) == renderer


@pytest.mark.parametrize("value", ["", "   ", None, 0, b"ANGLE"])
def test_a_renderer_nobody_reported_is_refused(value):
    """`is_software_renderer("")` would answer `False`, which reads as "hardware" when
    the truth is that nobody knows."""
    with pytest.raises(ArgumentError):
        digest_renderer(value)


# --- packet ----------------------------------------------------------------

@pytest.mark.parametrize(
    "value",
    [None, 0, "", b"", [], {}, {"protocolVersion": 1}, object()],
)
def test_a_packet_reaches_the_validator_untouched(value):
    """Judging a packet is the validator's job, not the digester's.

    A digester that raised would turn every hostile or mistyped message into an exception
    at the boundary, instead of the structured rejection the caller can act on.
    """
    assert digest_packet(value) is value


def test_the_packet_argument_is_not_named_value():
    """Renaming it back to `value` would break every call.

    `digest_value` is MolSysMT's dispatcher, keyed on the caller's name and ending in a
    bare `raise` for every caller it does not recognise. Digesters are resolved by
    argument name across the whole package, so a packet called `value` would be handed to
    that dispatcher, fall through all of it, and raise before the validator's body ran.
    """
    for validator in (validate_input_packet, validate_signaling_packet):
        first = next(iter(inspect.signature(validator).parameters))
        assert first == "packet", (
            f"{validator.__name__} takes its packet as {first!r}: see digest_value"
        )


@pytest.mark.parametrize(
    "hostile",
    [None, 0, "not a packet", [], {}, {"protocolVersion": "one"}, {"kind": "pointer"}],
)
@pytest.mark.parametrize("validator", [validate_input_packet, validate_signaling_packet])
def test_a_hostile_packet_is_answered_rather_than_raised(validator, hostile):
    """The property digestion must not take away, asked of the decorated callables."""
    assert validator(hostile).status == "rejected"


# --- the decorated callables still do their own work -----------------------

def test_an_identity_mismatch_is_still_reported_after_digestion():
    packet = {
        "protocolVersion": 1,
        "viewerId": "viewer-a",
        "sessionId": "session-a",
        "endpointId": "endpoint-a",
        "kind": "offer",
        "messageId": "m1",
        "payload": {"sdp": "v=0"},
    }
    assert validate_signaling_packet(packet).status == "accepted"
    assert validate_signaling_packet(packet, expected_viewer_id="viewer-b").reason == (
        "identity-mismatch"
    )


def test_a_renderer_is_still_classified_after_digestion():
    assert is_software_renderer("llvmpipe (LLVM 19.1.7, 256 bits)") is True
    assert is_software_renderer("Apple M3") is False


def test_an_explicit_executable_is_still_resolved_after_digestion(tmp_path):
    executable = tmp_path / "chrome"
    executable.touch()
    assert find_chromium_executable(executable) == str(executable.resolve())
