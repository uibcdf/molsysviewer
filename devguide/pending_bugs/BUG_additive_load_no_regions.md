# BUG: `load()` (additive) fails to create automatic regions

## Description
According to the established proposal, a second `load()` call should automatically create two regions: one for the initial atoms (using the first label) and one for the newly added atoms (using the second label). Currently, the second load adds the atoms but no new regions appear in `view.regions`.

## Steps to Reproduce
1. `view.load('1CRN', label='prot')`
2. `view.load('1BNA', label='dna')`
3. Check regions: `view.regions.keys()` -> **Observed Result:** Empty or only manual regions.

## Expected Behavior
`view.regions` should contain `['prot', 'dna']` after the second load.
