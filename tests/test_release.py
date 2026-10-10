"""Release orchestration with fake disk tools, never a real VM boot."""
import hashlib
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.script = self.root / "repo"
        self.script.mkdir()
        (self.script / "receipts").mkdir()
        for name in ("release.sh", "boot_verdict.sh"):
            shutil.copyfile(ROOT / name, self.script / name)
        self.disk = self.root / "source.qcow2"
        self.disk.write_bytes(b"a disposable test disk, not a bootable image\n")
        self.out = self.root / "dist"
        self.tool("qemu-img", '#!/bin/bash\ncase "$1" in\n'
                  'convert) args=("$@"); cp -- "${args[-2]}" "${args[-1]}";;\n'
                  'create) touch -- "${@: -1}";;\n*) exit 2;;\nesac\n')
        self.tool("qemu-system-x86_64", '#!/bin/bash\n'
                  'printf "%s\\n" "$$" > "$TEST_ROOT/qemu-started"\n'
                  'for arg in "$@"; do\n'
                  '  case "$arg" in file:*) printf "tup login:\\n" > "${arg#file:}";; esac\n'
                  'done\nexec /bin/sleep 30\n')
        self.tool("fuser", "#!/bin/bash\nexit 1\n")
        self.tool("sleep", "#!/bin/bash\nexec /bin/sleep 0.02\n")
        self.tool("sha256sum", '''#!/usr/bin/env python3
import hashlib
import os
from pathlib import Path
import sys
root = Path(os.environ["TEST_ROOT"])
counter = root / "hash-count"
n = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(n))
mode = os.environ["TEST_HASH_MODE"]
if (mode == "fail-both" and n <= 2) or (mode == "fail-first" and n == 1) or (mode == "fail-second" and n == 2):
    print("injected hash failure", file=sys.stderr)
    sys.exit(1)
if mode == "empty" and n == 1:
    sys.exit(0)
if mode == "malformed" and n == 1:
    print("not-a-digest  -")
    sys.exit(0)
if mode == "changed" and n == 2:
    print("0" * 64 + "  -")
    sys.exit(0)
if sys.argv[1:]:
    for name in sys.argv[1:]:
        print(hashlib.sha256(Path(name).read_bytes()).hexdigest() + "  " + name)
else:
    print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest() + "  -")
''')

    def tool(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o755)

    def run_release(self, mode="valid"):
        env = {**os.environ, "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
               "TUP_ARCH": "x86_64", "TUP_DISK": str(self.disk), "TUP_SETTLE_SECS": "0",
               "TMPDIR": str(self.root), "TEST_ROOT": str(self.root), "TEST_HASH_MODE": mode}
        process = subprocess.Popen(["bash", str(self.script / "release.sh"), str(self.out)],
                                   env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=10)
            return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()

    def test_control_produces_release_with_actual_master_digest(self):
        result = self.run_release()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        digest = hashlib.sha256(self.disk.read_bytes()).hexdigest()
        self.assertIn(digest, (self.out / "RELEASE.md").read_text())
        self.assertEqual(len((self.out / "SHA256SUMS").read_text().splitlines()), 3)

    def test_two_failed_hashes_cannot_compare_equal_and_ship(self):
        result = self.run_release("fail-both")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.out / "RELEASE.md").exists())

    def test_failed_first_hash_stops_before_witness(self):
        result = self.run_release("fail-first")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "qemu-started").exists())

    def test_empty_digest_stops_before_witness(self):
        result = self.run_release("empty")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "qemu-started").exists())

    def test_malformed_digest_stops_before_witness(self):
        result = self.run_release("malformed")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "qemu-started").exists())

    def test_failed_second_hash_cannot_ship(self):
        result = self.run_release("fail-second")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.out / "RELEASE.md").exists())

    def test_changed_master_remains_refused(self):
        result = self.run_release("changed")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("master changed", result.stderr)
        self.assertFalse((self.out / "RELEASE.md").exists())


if __name__ == "__main__":
    unittest.main()
