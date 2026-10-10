# Preserve the bytes named by receipt hashes

Registered before probes and repairs at `899227f`.

Two hypotheses from source inspection:

- GNU sha256sum prefixes its output with a backslash when it escapes a
  filename. The driver's first-field extraction may store that marker as part
  of script/log digests. A malformed nonempty hash response may also be accepted.
- The bundler reads evidence in text mode, which normalizes newlines before
  hashing and copying it. CRLF evidence may therefore receive the digest of
  different bytes even though the report says to hash the original build files.

Bars: native harmless-page tests under a directory containing a backslash must
record the exact SHA-256 of script/log bytes. Invalid digest output must stop
the driver before page execution. Bundling LF, CRLF and mixed-newline inputs
must name the original bytes' hashes and preserve those bytes in copied
evidence. Local and simulated VM reads must agree. Existing successful receipts,
test records and retry reconciliation must retain their meanings.

Prior work: driver.sh's JSON escaping and pre-run input-hash records; the
release-hash repair; Python's documented universal-newline behavior
(https://docs.python.org/3/library/functions.html#open) and GNU checksum output
escaping (https://www.gnu.org/software/coreutils/manual/html_node/cksum-output-modes.html).
These are finite provenance checks, not a proof of the build or storage durability.

Both hypotheses reproduced. The driver stored a leading backslash in a script
digest when its chapter directory contained a backslash; it also accepted a
nonempty `not-a-digest` response and reported completion. Those two native
driver tests failed before repair. The bundler's three tests produced ten
failing subcases: reported CRLF/mixed-newline hashes and copied evidence did not
match the original bytes, through both local and simulated VM input paths.

The driver now hashes stdin and validates the 64 hex digits before execution.
The bundler captures/reads bytes before UTF-8 decoding and writes copied
evidence as bytes, preserving original line endings. Parsing and report totals
still use the decoded text. All 27 native/simulated tests pass, including retry
reconciliation, test-policy reporting and the previous boot/release controls.

Command: `python3 -m unittest discover -s tests -v`. Clean checkout confirmation
remains pending. The VM transport test uses a local stand-in for limactl; no VM
or distribution build was run.
