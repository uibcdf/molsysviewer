"""Bounded transport for detached, producer-owned scientific context."""

import json
import math

MAX_OBSERVATION_BYTES = 4 * 1024 * 1024
MAX_OBSERVATION_NODES = 200_000
MAX_OBSERVATION_DEPTH = 24


def normalize_observation(value):
    """Copy finite interoperable JSON without interpreting a producer schema.

    Scientific producers must encode exact binary values or large integers
    explicitly when ordinary JSON numbers cannot carry their intended meaning.
    Rejection never truncates the scientific record.
    """
    if type(value) is not dict or not isinstance(value.get("schema"), str) or not value["schema"].strip():
        raise ValueError("Each figure observation needs a nonempty producer-owned schema string.")
    if len(value["schema"]) > 200:
        raise ValueError("A figure observation schema must fit in 200 characters.")
    active = set()
    nodes = 0

    def visit(item, depth):
        nonlocal nodes
        nodes += 1
        if nodes > MAX_OBSERVATION_NODES or depth > MAX_OBSERVATION_DEPTH:
            raise ValueError("Figure observation context exceeds its bounded JSON shape.")
        if item is None or type(item) is bool:
            return
        if type(item) is int:
            if abs(item) > 2**53 - 1:
                raise ValueError("Encode large observation integers explicitly; JSON consumers use binary64 numbers.")
            return
        if type(item) is float and math.isfinite(item):
            return
        if type(item) is str:
            if len(item) > MAX_OBSERVATION_BYTES:
                raise ValueError(
                    "Figure observation context exceeds 4 MiB; preserve a qualified input artifact instead."
                )
            return
        if type(item) not in {dict, list}:
            raise ValueError("Figure observation context must contain finite JSON values only.")
        if id(item) in active:
            raise ValueError("Figure observation context cannot contain cycles.")
        active.add(id(item))
        try:
            if type(item) is dict:
                for key, child in item.items():
                    if type(key) is not str:
                        raise ValueError("Figure observation context requires string object keys.")
                    visit(key, depth + 1)
                    visit(child, depth + 1)
            else:
                for child in item:
                    visit(child, depth + 1)
        finally:
            active.remove(id(item))

    visit(value, 0)
    try:
        encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        pieces, size = [], 0
        for piece in encoder.iterencode(value):
            # A shared Python value can expand many times in JSON. Stop before
            # building that rejected full expansion or its UTF-8 copy.
            if len(piece) > MAX_OBSERVATION_BYTES - size:
                raise ValueError("Figure observation context exceeds 4 MiB; no provenance was shortened or attached.")
            size += len(piece.encode("utf-8"))
            if size > MAX_OBSERVATION_BYTES:
                raise ValueError("Figure observation context exceeds 4 MiB; no provenance was shortened or attached.")
            pieces.append(piece)
    except (UnicodeError, ValueError) as error:
        raise ValueError("Figure observation context must be valid UTF-8 JSON within 4 MiB.") from error
    return json.loads("".join(pieces))
