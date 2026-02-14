"""
SSH Server wrapper for TUI Resume application
CROSS-PLATFORM (Linux / macOS / Windows OpenSSH)
"""

import asyncio
import sys
import logging
import os
import pty
import subprocess
import fcntl
import termios
import struct
import re
from pathlib import Path
from typing import Optional

import asyncssh
from asyncssh import SSHServer, SSHServerSession, SSHServerProcess


# ------------------------------------------------------------
# Filter terminal reply artifacts from Textual
# ------------------------------------------------------------
ANSI_REPLY_RE = re.compile(rb'\x1b\[\?\d+(?:;\d+)*\$[a-zA-Z]')


# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/connections.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


# ============================================================
# SSH SERVER
# ============================================================

class ResumeSSHServer(SSHServer):

    def connection_made(self, conn):
        peer = conn.get_extra_info("peername")
        logger.info(f"Connection from {peer[0]}:{peer[1]}")

    def connection_lost(self, exc):
        if exc:
            logger.error(f"Connection lost: {exc}")
        else:
            logger.info("Connection closed")

    # Public access (no auth)
    def begin_auth(self, username):
        return False

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        return True


# ============================================================
# SESSION (WINDOWS INPUT PATH)
# ============================================================

class ResumeSSHSession(SSHServerSession):
    """
    Handles PTY negotiation + Windows keyboard input routing.
    """

    def connection_made(self, chan):
        self.chan = chan

    def pty_requested(self, term_type, term_size, term_modes):
        # RAW MODE — REQUIRED
        self.chan.set_line_mode(False)
        self.chan.set_echo(False)
        return True

    def shell_requested(self):
        return True

    # ⭐ Windows keyboard input arrives HERE
    def data_received(self, data, datatype):

        master_fd = getattr(self.chan, "_pty_master_fd", None)

        if master_fd is None:
            return

        try:
            if isinstance(data, str):
                data = data.encode()

            os.write(master_fd, data)

        except OSError:
            pass


# ============================================================
# PROCESS FACTORY (TUI LIFECYCLE)
# ============================================================

async def handle_client(process: SSHServerProcess):

    try:
        # ---------------- Terminal info ----------------
        term_type = process.get_terminal_type() or "xterm-256color"
        term_size = process.get_terminal_size()

        cols, rows = (term_size[0], term_size[1]) if term_size else (80, 24)

        logger.info(f"TUI start: {term_type} {cols}x{rows}")

        env = os.environ.copy()
        env["TERM"] = term_type
        env["COLUMNS"] = str(cols)
        env["LINES"] = str(rows)
        env["PYTHONUNBUFFERED"] = "1"

        # ---------------- PTY ----------------
        master_fd, slave_fd = pty.openpty()

        # RAW MODE
        attrs = termios.tcgetattr(slave_fd)
        attrs[3] &= ~(termios.ICANON | termios.ECHO)
        attrs[6][termios.VMIN] = 1
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)

        # Window size
        fcntl.ioctl(
            master_fd,
            termios.TIOCSWINSZ,
            struct.pack("HHHH", rows, cols, 0, 0),
        )

        # ⭐ CRITICAL FIX:
        # Bind PTY to CHANNEL (shared object)
        chan = process.get_extra_info("channel")
        if chan:
            chan._pty_master_fd = master_fd
            logger.info("Channel ↔ PTY binding established")

        # ---------------- Launch TUI ----------------
        proc = subprocess.Popen(
            [sys.executable, "-u", "run_ssh_app_direct.py"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            cwd=os.getcwd(),
            preexec_fn=os.setsid,
            close_fds=True,
        )

        os.close(slave_fd)

        loop = asyncio.get_running_loop()

        # --------------------------------------------------
        # PTY → SSH client
        # --------------------------------------------------
        async def forward_output():
            try:
                while True:
                    data = await loop.run_in_executor(
                        None, os.read, master_fd, 8192
                    )

                    if not data:
                        break

                    data = ANSI_REPLY_RE.sub(b"", data)

                    process.stdout.write(
                        data.decode("utf-8", "ignore")
                    )

            except Exception:
                pass

        # --------------------------------------------------
        # Linux/macOS input path
        # --------------------------------------------------
        async def forward_input():
            try:
                while True:
                    data = await process.stdin.read(4096)
                    if not data:
                        break

                    if isinstance(data, str):
                        data = data.encode()

                    await loop.run_in_executor(
                        None, os.write, master_fd, data
                    )

            except Exception:
                pass

        await asyncio.gather(
            forward_output(),
            forward_input(),
        )

        proc.wait()
        os.close(master_fd)

        logger.info(f"TUI exited ({proc.returncode})")
        process.exit(0)

    except Exception as e:
        logger.exception(f"TUI failure: {e}")
        process.exit(1)


# ============================================================
# SERVER START
# ============================================================

async def start_server(host="", port=2222, host_key="host_key"):

    if not Path(host_key).exists():
        logger.error("Missing host_key")
        sys.exit(1)

    Path("logs").mkdir(exist_ok=True)

    logger.info(f"Starting SSH server on {host or '0.0.0.0'}:{port}")

    await asyncssh.listen(
        host,
        port,
        server_factory=ResumeSSHServer,
        session_factory=ResumeSSHSession,
        process_factory=handle_client,
        server_host_keys=[host_key],
        line_editor=False,
        sftp_factory=None,
        allow_scp=False,
    )

    await asyncio.Event().wait()


def main():
    asyncio.run(start_server())


if __name__ == "__main__":
    main()
