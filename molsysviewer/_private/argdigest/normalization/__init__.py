"""Declared argument-name aliases.

One module per family of rules. Each declares `table` or `TABLES` with `AliasTable`
instances; ArgDigest discovers them, composes them most-specific-first and applies them
before both the function contract and the argument digesters.

These rules exist because the MolSysMT-facing viewer methods delegate with
`skip_digestion=True`, which is deliberate — the arguments are digested once, here — but
means MolSysMT's own normalization never runs on them. Whatever renaming those calls need
has to happen on this side.
"""
