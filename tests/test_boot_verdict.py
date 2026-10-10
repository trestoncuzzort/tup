"""Native boot-gate controls: these do not boot a guest or establish OS health."""
import itertools
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAX_SECONDS = 2**63 - 1


def invoke(source, log, *, seen="1", alive=True, watched="10", required="10", budget="300", pid=None):
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; tup_boot_verdict "$2" "$3" "$4" "$5" "$6" "$7"',
         "boot-gate-test", str(source), str(log), str(pid) if pid is not None else
         (str(os.getpid()) if alive else "2147483647"),
         str(seen), str(watched), str(required), str(budget)],
        text=True, capture_output=True, timeout=5,
    )
    return result


class BootGateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.log = Path(self.directory.name) / "console.log"
        self.log.write_text("tup login:\n")

    def test_malformed_measurements_never_boot(self):
        bad = ("", "unknown", "1.5", "-1", "+1", "1e3", " 10", "10 ", str(2**63), str(10**100))
        for field in ("watched", "required", "budget"):
            for value in bad:
                with self.subTest(field=field, value=value):
                    result = invoke(ROOT / "boot_verdict.sh", self.log, **{field: value})
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("BOOTED", result.stdout)
                    self.assertIn("INVALID", result.stdout)
                    self.assertEqual(result.stderr, "")

    def test_seen_flag_must_be_boolean_text(self):
        for value in ("", "unknown", "2", "-1", "01"):
            with self.subTest(value=value):
                result = invoke(ROOT / "boot_verdict.sh", self.log, seen=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("INVALID", result.stdout)

    def test_process_groups_and_invalid_pids_are_not_guest_processes(self):
        for pid in ("0", "-1", "unknown", str(2**63)):
            result = invoke(ROOT / "boot_verdict.sh", self.log, pid=pid)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("INVALID", result.stdout)
            self.assertEqual(result.stderr, "")

    def test_acceptance_conjunction_and_settle_boundaries(self):
        for panic, prompt, seen, alive in itertools.product((False, True), repeat=4):
            text = ("tup login:\n" if prompt else "starting...\n") + ("Kernel panic\n" if panic else "")
            self.log.write_text(text)
            for watched, required in ((0, 0), (0, 1), (9, 10), (10, 10), (11, 10), (MAX_SECONDS, MAX_SECONDS)):
                want = not panic and prompt and seen and alive and watched >= required
                result = invoke(ROOT / "boot_verdict.sh", self.log, seen=int(seen), alive=alive,
                                watched=watched, required=required)
                self.assertEqual(result.returncode == 0, want)
                self.assertEqual(result.stdout.strip() == "BOOTED", want)
                self.assertEqual(result.stderr, "")

    def test_leading_zero_measurements_are_decimal(self):
        result = invoke(ROOT / "boot_verdict.sh", self.log, watched="00008", required="08", budget="000300")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "BOOTED")

    def test_missing_transcript_and_quoted_prompt_do_not_boot(self):
        for text in ("ERROR: never reached tup login: because getty failed\n", "no prompt\n"):
            self.log.write_text(text)
            self.assertNotEqual(invoke(ROOT / "boot_verdict.sh", self.log).returncode, 0)
        self.log.unlink()
        self.assertNotEqual(invoke(ROOT / "boot_verdict.sh", self.log).returncode, 0)

    def test_ansi_prompt_is_preserved(self):
        self.log.write_text("\x1b[0m  tup login:\n")
        self.assertEqual(invoke(ROOT / "boot_verdict.sh", self.log).returncode, 0)


if __name__ == "__main__":
    unittest.main()
