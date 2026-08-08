"""Function argument contracts: what each public callable accepts and requires.

One module per function or family. A function with no module here falls back to
ArgDigest's default: a closed signature is held to its own parameters, and a function
with `**kwargs` admits anything until its domain is declared.
"""
