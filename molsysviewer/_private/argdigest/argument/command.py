from ...exceptions import ArgumentError


def digest_command(command, caller=None):
    from ....runtime_contract import RuntimeEnvelope

    if isinstance(command, RuntimeEnvelope):
        return command
    raise ArgumentError("command", value=command, caller=caller)
