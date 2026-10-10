# Driver completion and evidence audit

Registered before the native probes and changes, from tup commit `c6db544`.
All build-driver experiments use disposable directories and harmless action
pages; they do not execute a distribution build or touch a mounted system.

Hypotheses from source inspection:

- `read` returns failure at EOF even when it has consumed a final unterminated
  record. The driver's loop may therefore skip the final ORDER page and still
  report the chapter complete.
- Redirection failures writing `receipts.jsonl` or `driver.state` may be ignored
  because the driver does not check those commands' status. A successful page
  without a saved receipt or completion record may still be reported as success.

Bars: every nonempty ORDER record is processed exactly once, whether or not the
file ends in a newline; an unsuccessful receipt/state write causes a nonzero
driver exit and no chapter-complete message; a receipt failure must not mark the
page complete; ordinary success and resumability remain intact. A page failing
its build must keep its failure receipt and remain eligible for retry. These are
native finite tests, not a proof of filesystem durability after power loss.

Prior work: `driver.sh`'s existing stdin isolation, extraction and hash-failure
records; README's promise that the ledger is the build record; GNU Bash's `read`
EOF and redirection-error semantics (`help read`, Bash manual at
https://www.gnu.org/software/bash/manual/bash.html).

The hypotheses reproduced on the original driver: the unterminated single-page
ORDER printed `complete` without running the page; a receipt directory and an
unwritable state destination each produced a shell error followed by `ok` and
`complete`, with exit zero. Four of eight driver tests failed before repair.

The loop now processes the final partial line. Log/state initialization and
state reads are checked; the page is marked complete only after its receipt
append succeeds, and a failed state append stops the chapter. The eight driver
tests and seven native boot-gate tests pass after the repair. CI now runs them.
Commands: `python3 -m unittest discover -s tests -p test_driver.py -v` for the
paired driver measurement, and `python3 -m unittest discover -s tests -v` for the
combined regression. Clean checkout `5936dc6` repeated all 15 passing tests;
override checks passed 46/46 and placeholder checks 12/12. All 340 tracked shell
scripts passed `bash -n`; all seven tracked Python files compiled. Those are
syntax/structural checks, not execution of the distribution build.
