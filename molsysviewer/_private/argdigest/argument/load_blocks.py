"""`load_blocks` is the load-block accounting policy after a system edit.

Three values with different consequences for what the viewer believes it holds: `keep`
leaves the blocks alone (a coordinate or attribute edit), `collapse` folds them into one
block for the current whole (after a removal), `append` records a new block (after an
addition).

Getting it wrong does not raise; it leaves the block accounting describing a system that
is no longer there, which surfaces later as a wrong count or a mis-scoped selection. That
is why the set is closed here rather than trusted.

**`append` additionally requires `appended_n_atoms`, and that rule is not here.** It is
conditional on this argument's *value*, which ArgDigest cannot yet express — `co_required`
is symmetric and would reject a valid `keep` call that omits the count. It stays in the
body; see `devguide/pending_proposals/digest_every_public_callable.md`.
"""

from molsysviewer._private.exceptions import ArgumentError

LOAD_BLOCK_POLICIES = ("keep", "collapse", "append")


def digest_load_blocks(load_blocks, caller=None):
    if load_blocks in LOAD_BLOCK_POLICIES:
        return load_blocks
    raise ArgumentError(
        "load_blocks",
        value=load_blocks,
        caller=caller,
        message=f"expected one of {', '.join(LOAD_BLOCK_POLICIES)}",
    )
