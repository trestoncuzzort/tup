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

Results pending.
