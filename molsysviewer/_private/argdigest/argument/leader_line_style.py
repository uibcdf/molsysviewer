from ...exceptions import ArgumentError


def digest_leader_line_style(leader_line_style, caller=None):
    if isinstance(leader_line_style, str) and leader_line_style in {"solid", "dashed", "dotted"}:
        return leader_line_style
    raise ArgumentError("leader_line_style", value=leader_line_style, caller=caller, message=None)
