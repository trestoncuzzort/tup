"""Run harmless action pages against a disposable build root."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DriverTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.chapter = self.root / "ch-test"
        self.chapter.mkdir()
        self.lfs = self.root / "lfs"
        self.log = self.lfs / "sources" / "log"
        self.log.mkdir(parents=True)
        self.receipts = self.log / "receipts.jsonl"
        self.state = self.log / "driver.state"
        self.page = self.chapter / "01-probe.sh"
        self.page.write_text('# TUP_ACTION_PAGE\nprintf "ran\\n" >> "$LFS/ran"\n')
        (self.chapter / "ORDER").write_text(self.page.name + "\n")

    def run_driver(self):
        return subprocess.run(
            ["bash", str(ROOT / "driver.sh"), str(self.chapter)],
            env={**os.environ, "LFS": str(self.lfs), "TUP_ARCH": "x86_64",
                 "TUP_OVERRIDES": str(self.root / "overrides")},
            text=True, capture_output=True, timeout=10,
        )

    def assert_refused(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("=== ch-test complete", result.stdout)

    def test_success_has_receipt_and_resumes_without_rerunning(self):
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(self.receipts.read_text())
        self.assertEqual(receipt["exit"], 0)
        self.assertEqual(receipt["script_sha256"], hashlib.sha256(self.page.read_bytes()).hexdigest())
        self.assertEqual(self.state.read_text(), "ch-test/01-probe.sh\n")
        self.assertEqual(self.run_driver().returncode, 0)
        self.assertEqual((self.lfs / "ran").read_text(), "ran\n")
        self.assertEqual(len(self.receipts.read_text().splitlines()), 1)

    def test_final_order_record_without_newline_runs(self):
        (self.chapter / "ORDER").write_text(self.page.name)
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.lfs / "ran").exists(), result.stdout)
        self.assertEqual(json.loads(self.receipts.read_text())["exit"], 0)

    def test_receipt_write_failure_does_not_complete_page(self):
        self.receipts.mkdir()
        self.assert_refused(self.run_driver())
        self.assertEqual(self.state.read_text(), "")

    def test_state_write_failure_does_not_complete_chapter(self):
        self.page.write_text(self.page.read_text() +
                             'rm "$LFS/sources/log/driver.state"\n'
                             'mkdir "$LFS/sources/log/driver.state"\n')
        self.assert_refused(self.run_driver())
        self.assertEqual(json.loads(self.receipts.read_text())["exit"], 0)

    def test_invalid_state_is_refused_before_running(self):
        self.state.mkdir()
        self.assert_refused(self.run_driver())
        self.assertFalse((self.lfs / "ran").exists())

    def test_failed_page_is_receipted_and_retried(self):
        self.page.write_text(self.page.read_text() + "exit 7\n")
        for attempt in range(2):
            self.assert_refused(self.run_driver())
            self.assertEqual(self.state.read_text(), "")
        rows = [json.loads(line) for line in self.receipts.read_text().splitlines()]
        self.assertEqual([row["exit"] for row in rows], [7, 7])
        self.assertEqual((self.lfs / "ran").read_text(), "ran\nran\n")

    def test_page_stdin_does_not_consume_order(self):
        self.page.write_text(self.page.read_text() + "cat >/dev/null\n")
        second = self.chapter / "02-probe.sh"
        second.write_text(self.page.read_text())
        (self.chapter / "ORDER").write_text(self.page.name + "\n" + second.name + "\n")
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.lfs / "ran").read_text(), "ran\nran\n")

    def test_test_policy_receipt_failure_stops_page(self):
        self.page.write_text('# TUP_ACTION_PAGE\n'
                             'tup_receipt_skip_tests "$TUP_PAGE_ID"\n'
                             'printf "ran\\n" >> "$LFS/ran"\n')
        self.receipts.mkdir()
        self.assert_refused(self.run_driver())
        self.assertFalse((self.lfs / "ran").exists())


if __name__ == "__main__":
    unittest.main()
