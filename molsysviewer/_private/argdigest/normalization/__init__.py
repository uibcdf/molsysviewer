"""Declared argument-name aliases.

**Empty, and that is the result rather than an omission.**

Two modules lived here, scoping MolSysMT's synonym and bare-name tables to eight named
callers. They existed because the `get`-shaped methods digested here and forwarded with
`skip_digestion=True`, which meant MolSysMT's own normalization never ran on them.

`uibcdf/molsysviewer#71` removed that: the forwarders no longer digest, `skip_digestion`
is passed through instead of forced, and MolSysMT renames what it is about to consume.
Measured before deleting them — `msm.get(molsys, element='group', name=True)`,
`index=True` and `residue_name=True` all answer correctly on their own, so both tables were
re-scoping rules MolSysMT already applies.

If a future method digests here and then forwards with `skip_digestion=True`, it is the
last layer that can rename its arguments and it will need a table again. That shape is what
to look for; the emptiness of this package is not a licence to skip the question.
""" 
