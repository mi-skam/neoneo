from __future__ import annotations

import os
import pty
import select
import sys
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "nokitty.py"


def run_on_pty(shell_command: str) -> bytes:
    """Run a shell command on a fresh pseudo-terminal; return what reached it."""
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp("sh", ["sh", "-c", shell_command])
    seen = b""
    end = time.time() + 10
    while time.time() < end:
        if not select.select([fd], [], [], 0.2)[0]:
            continue
        try:
            data = os.read(fd, 65536)
        except OSError:
            break
        if not data:
            break
        seen += data
    os.close(fd)
    os.waitpid(pid, 0)
    return seen


class NokittyTest(unittest.TestCase):
    def wrapped(self, command: str) -> bytes:
        return run_on_pty(f"'{sys.executable}' '{SCRIPT}' {command}")

    def test_strips_protocol_requests_and_keeps_the_rest(self):
        seen = self.wrapped(r"""printf 'a\033[>13ub\033[=5;1uc\033[<ud\033[1me\033[<1uf'""")
        self.assertEqual(seen, b"ab" b"c" b"d\x1b[1me" b"f")

    def test_request_split_across_writes(self):
        seen = self.wrapped(r"""sh -c 'printf "x\033[>1"; sleep 0.3; printf "3uy"'""")
        self.assertEqual(seen, b"xy")

    def test_unfinished_other_sequence_is_passed_on(self):
        seen = self.wrapped(r"""sh -c 'printf "x\033["; sleep 0.3; printf "1my"'""")
        self.assertEqual(seen, b"x\x1b[1my")

    def test_exit_status_and_redirected_stderr(self):
        seen = run_on_pty(
            f"'{sys.executable}' '{SCRIPT}' sh -c 'echo result >&2; exit 7' 2>&1 >/dev/null | tr a-z A-Z; "
            f"'{sys.executable}' '{SCRIPT}' sh -c 'exit 7'; echo rc=$?"
        )
        self.assertIn(b"RESULT", seen)
        self.assertIn(b"rc=7", seen)


if __name__ == "__main__":
    unittest.main()
