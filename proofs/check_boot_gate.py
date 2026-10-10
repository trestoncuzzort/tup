"""Compare the proved gate and legacy integer-error model with actual shell code.

The legacy model represents Bash test's false/error branch on decimal integers
outside signed-64 range. Text-valued counters are covered by native regressions,
not by the integer t model. Transcript matching and process observation are tested
glue. This experiment starts no VM and makes no OS correctness claim.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = "64e00b31ca489b9fe527ec0deae4ef07d860f5d2"
sys.path.insert(0, str(ROOT / "tests"))
from test_boot_verdict import invoke


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.engine.resolve() / "t"))
    import judge
    import surface

    source = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{BASE}:boot_verdict.sh"])
    values = (-2**63-1, -2**63, -1, 0, 1, 9, 10, 11, 2**63-1, 2**63, 2**64)
    counts = {"before": 0, "after": 0}
    disagreements = []
    with tempfile.TemporaryDirectory(prefix="tup-gate-correspondence-") as temp:
        work = Path(temp)
        old = work / "before.sh"
        old.write_bytes(source)
        calls = {}
        for side, task_path in (("before", HERE / "findings/boot_accept_legacy.t"),
                                ("after", HERE / "boot_accept.t")):
            (work / side).mkdir()
            calls[side] = judge.compile_task(surface.parse_file(task_path), work / side)
        log = work / "console.log"
        for panic, prompt, seen, alive in itertools.product((False, True), repeat=4):
            log.write_text(("tup login:\n" if prompt else "starting...\n")
                           + ("Kernel panic\n" if panic else ""))
            for watched, required in itertools.product(values, repeat=2):
                for side, path in (("before", old), ("after", ROOT / "boot_verdict.sh")):
                    got = invoke(path, log, seen=int(seen), alive=alive, watched=watched, required=required)
                    expected = calls[side]((panic, prompt, seen, alive, watched, required, 300))
                    agrees = (got.returncode == 0) == expected and (got.stdout.strip() == "BOOTED") == expected
                    counts[side] += agrees
                    if not agrees:
                        disagreements.append({"side": side, "input": [panic, prompt, seen, alive, watched, required],
                                              "expected": expected, "native_exit": got.returncode,
                                              "native_verdict": got.stdout.strip()})
    result = {"scope": "finite correspondence for numeric inputs; no VM boot",
              "original_commit": BASE, "original_sha256": hashlib.sha256(source).hexdigest(),
              "fixed_sha256": hashlib.sha256((ROOT / "boot_verdict.sh").read_bytes()).hexdigest(),
              "cases_per_side": 16 * len(values)**2, "passed": counts, "disagreements": disagreements}
    args.json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 1 if disagreements else 0


if __name__ == "__main__":
    raise SystemExit(main())
