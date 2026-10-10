# Boot gate measurement validation

Registered before the malformed-measurement probe and before changes. The current
boot_verdict.sh documents a positive conjunction: no panic, a prompt seen during
the run and still in the transcript, a live guest, and a completed settle window.
The gate checks its arity but uses shell integer comparisons without validating
the supplied measurement strings.

Prediction: malformed or overflowing watched/required values can make `test`
return an error that the surrounding `if` treats as false, permitting BOOTED.
Negative durations may also satisfy the comparison without valid elapsed-time
evidence. A failing probe is required before repair.

Bars: valid controls retain their verdicts; invalid measurement fields cannot
produce BOOTED; missing or unreadable evidence cannot produce BOOTED; the integer
acceptance predicate is proved in t with a refuted twin and agrees with the actual
shell gate on a truth table and timing boundaries. Process and transcript tests
are native finite checks. No OS build, guest boot, or Linux correctness is claimed.

Prior work: boot_verdict.sh's existing three failure records and README scope;
Bash's conditional-command and integer-comparison semantics in the GNU Bash manual
(https://www.gnu.org/software/bash/manual/bash.html).

The original native gate returned BOOTED for malformed and overflowing counters,
including `watched=unknown`, `watched=2**64`, a negative required duration and a
non-boolean prompt-seen flag. The initial six tests had 35 failing subcases.
The corrected gate checks boolean flags, positive guest PID and nonnegative
signed-64-bit decimal counters before any comparison. Seven native regression
tests now pass, including the gate truth table, timing boundaries, leading
zeros, missing transcripts and prompt matching.

Clean checkout `5936dc6`, using T proof engine `f3cb6a5`, produced the evidence in
`proofs/evidence/2026-10-10/`. Dafny 4.11.0 and Lean 4.33.1 each proved
`boot_accept` with a refuted twin, with three agreeing runs per side. Both also
refuted the legacy integer model in three runs at watched `9223372036854775808`,
required `0`, budget `300`, no panic, prompt/seen/alive true. The native Bash
code and compiled models agreed on all 1,936 inputs per side (3,872 comparisons,
zero disagreements). Arbitrary malformed text is covered by native tests, not
the integer model.

Reproduce from clean sibling checkouts, writing output outside either checkout:

```
python3 ../t-proof-engine/t/cli.py verify proofs --kernels dafny,lean --jobs 2 --out /tmp/tup-proof-out --table /tmp/tup-boot-agreement.md
python3 proofs/check_boot_gate.py --engine ../t-proof-engine --json /tmp/tup-correspondence.json
python3 -m unittest discover -s tests -p test_boot_verdict.py -v
```

The checked predicate does not prove its measurements faithfully observe a
guest, or establish the correctness of Linux. No new VM boot was performed.
