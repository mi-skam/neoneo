#!/usr/bin/env python3
"""nokitty: run a command with the kitty keyboard protocol kept off.

Usage: tools/nokitty.py <command> [args...]

The command runs on a private pseudo-terminal. Everything is passed through
to the real terminal except the requests that switch the protocol on, off or
to other flags (CSI > ... u, CSI < ... u, CSI = ... u), so the program gets
the layout's text. Standard streams that are not a terminal (pipes, files)
are handed to the command unchanged.
"""
import fcntl
import os
import pty
import re
import select
import signal
import sys
import termios
import tty

REQUEST = re.compile(rb"\x1b\[[>=<][0-9;]*u")
PARTIAL = re.compile(rb"\x1b(\[([>=<][0-9;]*)?)?$")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    term = os.open("/dev/tty", os.O_RDWR)
    keep = {fd: os.dup(fd) for fd in (0, 1, 2) if not os.isatty(fd)}
    size = fcntl.ioctl(term, termios.TIOCGWINSZ, b"\0" * 8)
    pid, master = pty.fork()
    if pid == 0:
        for fd, saved in keep.items():
            os.dup2(saved, fd)
            os.close(saved)
        os.close(term)
        try:
            os.execvp(sys.argv[1], sys.argv[1:])
        except OSError as e:
            os.write(2, f"nokitty: {sys.argv[1]}: {e.strerror}\n".encode())
            os._exit(127)
    for saved in keep.values():
        os.close(saved)
    fcntl.ioctl(master, termios.TIOCSWINSZ, size)

    def resize(*_):
        fcntl.ioctl(master, termios.TIOCSWINSZ, fcntl.ioctl(term, termios.TIOCGWINSZ, b"\0" * 8))

    signal.signal(signal.SIGWINCH, resize)
    saved_mode = termios.tcgetattr(term)
    pending = b""
    try:
        tty.setraw(term)
        while True:
            try:
                # Hold an unfinished sequence back: briefly while it could be anything
                # (ESC, ESC [), longer once it has started like a request.
                wait = None if not pending else 0.05 if len(pending) <= 2 else 1.0
                ready, _, _ = select.select([term, master], [], [], wait)
            except InterruptedError:
                continue
            if not ready and pending:  # never finished: not a request after all
                os.write(term, pending)
                pending = b""
            if term in ready:
                os.write(master, os.read(term, 65536))
            if master in ready:
                try:
                    data = os.read(master, 65536)
                except OSError:
                    data = b""
                if not data:
                    break
                data = REQUEST.sub(b"", pending + data)
                tail = PARTIAL.search(data)
                pending = tail.group(0) if tail else b""
                os.write(term, data[: len(data) - len(pending)])
    finally:
        if pending:
            os.write(term, pending)
        termios.tcsetattr(term, termios.TCSADRAIN, saved_mode)
    status = os.waitpid(pid, 0)[1]
    return os.waitstatus_to_exitcode(status) if hasattr(os, "waitstatus_to_exitcode") else status >> 8


if __name__ == "__main__":
    sys.exit(main())
