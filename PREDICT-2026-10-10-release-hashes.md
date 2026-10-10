# Release hash failure audit

Registered before probes or changes, at `5936dc6`. `release.sh` uses
`hash-command | cut` in command substitutions without pipefail. Prediction:
failed pre- and post-witness hashes can both become empty strings, compare
equal, and permit a release note if the later checksum-manifest command works.

Probe the actual script with disposable files and fake qemu-img/QEMU/hash
commands. The fake QEMU emits a prompt and stays alive; its clock is accelerated.
This checks release orchestration only and is not evidence of a real boot or
settle duration. A successful control must still create checksums and a release
note. Any failed, empty or malformed master hash must prevent acceptance; a
failure before the witness must prevent starting QEMU at all. A changed master
must remain refused. No real disk is opened and no artifact is published.

Prior work: driver.sh already documents the same pipeline-status defect for
build receipts; GNU Bash pipeline exit-status semantics
(https://www.gnu.org/software/bash/manual/html_node/Pipelines.html).

Four of seven release tests failed before repair. In the strongest negative
control, both master-hash commands returned nonzero; the script printed an
empty master digest, later wrote SHA256SUMS successfully, created RELEASE.md
and exited zero. Failed, empty and malformed first hashes also allowed the
witness process to start. The valid control and changed-master refusal passed.

The release now checks each hash command directly and requires a 64-digit hex
digest before using it. Hashing through stdin also avoids filename escapes in
the digest. This applies to both master checks and a present inventory's hash.
All seven release tests pass after repair, alongside the 15 existing native
driver/boot tests (22 total). Command: `python3 -m unittest discover -s tests -v`.
Clean checkout `f878afc` repeated all 22 passing native/simulated tests and syntax
checked all 340 tracked shell scripts and eight Python files. The source hashes
and command are in `tests/evidence/2026-10-10-audit.json`. These test doubles
establish no real boot, filesystem isolation or release-image correctness.
