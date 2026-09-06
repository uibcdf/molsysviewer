"""`packet` is a message from a remote peer, and is deliberately passed through untouched.

`validate_input_packet` and `validate_signaling_packet` exist to judge whatever arrives
over the network and answer with a structured rejection — `malformed-packet`,
`identity-mismatch`, `unknown-kind`. A digester that raised on a bad packet would take
that judgement away from the function whose whole purpose is to publish it, turning every
hostile or mistyped message into an exception at the boundary instead of a reason the
caller can act on. So anything at all is accepted, and the function decides.

The argument is named `packet` rather than `value` because `digest_value` is MolSysMT's
dispatcher, keyed on the caller's name, and it raises for every caller it does not
recognise. Sharing that name would have shared no contract, only a failure.
"""


def digest_packet(packet, caller=None):
    return packet
