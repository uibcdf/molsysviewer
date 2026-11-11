"""Function argument contracts: what each public callable accepts and requires.

One module per function or family. A function with no module here falls back to
ArgDigest's default: a closed signature is held to its own parameters, and a function
with `**kwargs` admits anything until its domain is declared.

Representation setters and their style/region facades deliberately retain
direct Mol* options, including runtime-selected advanced representations.
Their complete delegated name domain is not the curated subset. The latter
has ordinary value digesters and shared owner checks; unknown advanced names
retain the missing-digester diagnostic and existing forwarding. Do not close
that delegated domain to the discovery catalogue or suppress its diagnostics.
See #357 and docs/content/user/representations/types.md.
"""
