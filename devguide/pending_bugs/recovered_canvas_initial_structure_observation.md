---
summary: Diagnose the pre-save Python frame assertion in prolonged Jupyter receiving.
issue: uibcdf/molsysviewer#354
status: partial
opened: 2026-11-10
closed:
severity: medium
verification: measured
area: [jupyter, trajectory, receiving, synchronization]
guard:
normative:
blocked_by: []
supersedes: []
---

# Pre-save frame assertion — corrected diagnosis, still open

**Qualification correction — 2026-11-14:** the original report described a
recovered frontend stuck at structure zero. Exact reinspection of the retained
failure, notebook body and matching original receiver source disproves that
attribution. The [closeout record](../prolonged_receiving_closeout_20261114.json)
retains original hashes, sources and the corrected phase. The raw evidence and
older receipt payload are unchanged; its dated annotation narrows the claim.

Campaign `259` completes eight cycles, then its ninth Python recovery cell
fails on line 2, `assert v.player.index==1, v.player.index`, with value `0`.
This is before `save_session_async`, `load_session`, display or any ninth-cycle
recovery comparisons. The browser times out inside `marker('LONG_RECOVERED_9')`;
the next recovered-surface wait, `bind(page,3)` and frame-1 assertion have not
been reached. Its catch observation reads the previously bound controller.
That connected offscreen controller at frame zero is not established as the
recovered View. No ninth recovered-frame loss or successful ninth-cycle Python
recovery is proved. The original Python error also explains why its marker
could not appear; the cause of the Python frame disagreement remains unknown.

The original receiver source `74aeffede0b7ff35c3cc4b7513b73b3b670b5a57` has
SHA-256 `9827067a7421bf5b627282db93c1edd68bcf353ea901262fd5a09eb8c3fa4b36`,
matching the retained input manifest. Failure JSON SHA-256 is
`a618285066b0a031ca843281cd718b184cf7df527af008ee45d74789ec939f83`.
MolSysViewer source is `cb326235b3377185b18a17c7f59c71fd53cdab2a`; the run
retains 10,890 unchanged selected inputs, exits 1 after 462.55 seconds, has
no resource stop and retires all 26 owned processes. Those outer labels alone
do not qualify every inner scientific source; #364's bounded review applies.

The actual unresolved observation is a pre-save Python index of zero after
earlier canvas/popup frame-1 predicates. Original packet ordering, authority
and timing were not captured, so do not assign it to hidden initialization,
late feedback or a scientific-data defect. Keep related #331/#332/#314/#307/
#224 and MolSysMT #615 distinct unless a causal comparison establishes a link.

## Required next receiving

MolSysMT #754 owns the receiver's failure classification: retain the Python
error, phase actually reached, expected widget/surface and actual controller
identity. Its opening includes the exact original traceback and requests real
Jupyter negative controls. The owner has closed it in published commit
`c4fa8552e9696ee225dd9abd51be4e2e441228c4`; it reports 72 selected pytest
passes and distinguishes real Jupyter from synthetic controller controls.
[Independent receiving](../receiver_754_independent_receiving_20261114.json)
now passes all 72 selected tests with those committed tools. Their real
plain-Jupyter and synthetic controller scopes remain explicit; the original
pre-save frame cause is still unestablished.
Do not increase deadlines, repair-seek, suppress
the Python precondition or silently retry to make it pass. Receive that
instrumentation, then distinguish pending communication from a lost/newer
frame intention under the existing scene-authority contract.

## Later successful scopes

Receiver `66273e4d` completes fifteen cycles with visible, uniquely matched
recovered widgets before a shared-pressure stop. Current canonical receiver
`429d7494` completes thirty same-kernel recovery/playback cycles on `a72c92ba`
and Mol* 5.13.1 with exact declared scientific/native bytes, independent
witness data/camera, both popups and unchanged scientific assertions. The
[current receipt](../molstar_qualification_followup_20261114.json) preserves
those successes. They qualify their inputs and do not reconstruct the original
pre-save message ordering. #354 and broader E2 acceptance remain open;
installed, native Qt and postponed human scopes stay separate.
