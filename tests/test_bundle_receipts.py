"""Compare reported evidence hashes with the actual input bytes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BundleReceiptTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        shutil.copyfile(ROOT / "bundle_receipts.py", self.repo / "bundle_receipts.py")
        self.log = self.root / "log"
        self.log.mkdir()

    def evidence(self, separators):
        rows = [
            {"page": "ch01/01-package.sh", "exit": 1, "seconds": 1},
            {"page": "ch01/01-package.sh", "exit": 0, "seconds": 2, "package": "package-λ"},
            {"page": "ch01/01-package", "tests_run": True, "check_exit": 0, "pass": 3, "fail": 0},
            {"page": "zlib", "tests_skipped": True},
        ]
        receipts = b"".join(json.dumps(row, ensure_ascii=False).encode() + separators[i % len(separators)]
                            for i, row in enumerate(rows))
        data = {"receipts.jsonl": receipts,
                "driver.state": b"ch01/01-package.sh" + separators[0],
                "SHA256-MANIFEST-test.txt": ("a" * 64 + "  input-λ.tar.xz").encode() + separators[0]}
        for name, payload in data.items():
            (self.log / name).write_bytes(payload)
        return data

    def bundle(self, *, remote=False):
        env = dict(os.environ)
        args = [sys.executable, str(self.repo / "bundle_receipts.py")]
        if remote:
            binaries = self.root / "bin"
            binaries.mkdir(exist_ok=True)
            tool = binaries / "limactl"
            tool.write_text('''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
root = Path(os.environ["TEST_RECEIPT_LOG"])
if "-c" in sys.argv:
    data = b"".join(p.read_bytes() for p in sorted(root.glob("SHA256-MANIFEST-*.txt")))
else:
    p = root / Path(sys.argv[-1]).name
    if not p.exists():
        sys.exit(1)
    data = p.read_bytes()
sys.stdout.buffer.write(data)
''')
            tool.chmod(0o755)
            env.update(PATH=str(binaries) + os.pathsep + env["PATH"], TEST_RECEIPT_LOG=str(self.log))
        else:
            args.extend(["--local", str(self.log)])
        result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = sorted((self.repo / "receipts").glob("BUILD-*.md"))[-1]
        return report, report.read_text()

    def assert_original_hashes(self, data, text):
        for name, payload in data.items():
            with self.subTest(evidence=name):
                self.assertIn(hashlib.sha256(payload).hexdigest(), text)
        self.assertIn("distinct pages built: **1** (1 retried attempts", text)
        self.assertIn("Suites that RAN (1 records across 1 pages)", text)
        self.assertIn("Suites skipped by policy (1)", text)
        self.assertNotIn("MISMATCH", text)

    def test_local_report_hashes_original_lf_crlf_and_mixed_bytes(self):
        for separators in ((b"\n",), (b"\r\n",), (b"\r\n", b"\n")):
            with self.subTest(separators=separators):
                data = self.evidence(separators)
                _, text = self.bundle()
                self.assert_original_hashes(data, text)

    def test_copied_receipt_and_manifest_keep_original_bytes(self):
        data = self.evidence((b"\r\n",))
        report, _ = self.bundle()
        stamp = report.stem.removeprefix("BUILD-")
        self.assertEqual((report.parent / f"receipts-{stamp}.jsonl").read_bytes(), data["receipts.jsonl"])
        self.assertEqual((report.parent / f"SHA256-MANIFEST-{stamp}.txt").read_bytes(), data["SHA256-MANIFEST-test.txt"])

    def test_vm_transport_preserves_hash_identity(self):
        data = self.evidence((b"\r\n",))
        _, text = self.bundle(remote=True)
        self.assert_original_hashes(data, text)


if __name__ == "__main__":
    unittest.main()
