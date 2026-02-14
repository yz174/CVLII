"""SSH Server wrapper for TUI Resume application"""

import asyncio
import sys
import logging
import os
import pty
import tty
import subprocess
import fcntl
import termios
import struct
import re
from pathlib import Path
from typing import Optional

import asyncssh
from asyncssh import SSHServerProcess, SSHServerConnection, SSHServerSession, TerminalSizeChanged, BreakReceived

# Regex to filter terminal reply sequences from PTY output
# Matches sequences like ESC[?2048;0$y (mode reports) and ESC[?2026$y (device attributes)
ANSI_REPLY_RE = re.compile(rb'\x1b\[\?\d+(?:;\d+)*\$[a-zA-Z]')


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/connections.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ResumeSSHServer(asyncssh.SSHServer):
    """SSH Server for the TUI Resume application"""
    
    def connection_made(self, conn: SSHServerConnection) -> None:
        """Called when a connection is established"""
        peer = conn.get_extra_info('peername')
        logger.info(f"Connection received from {peer[0]}:{peer[1]}")
    
    def connection_lost(self, exc: Optional[Exception]) -> None:
        """Called when a connection is lost"""
        if exc:
            logger.error(f"Connection lost with error: {exc}")
        else:
            logger.info("Connection closed normally")
    
    def begin_auth(self, username: str) -> bool:
        """
        Authentication callback - no authentication required for public access
        Return False and use password_auth_supported to bypass auth
        """
        logger.info(f"Connection from user: {username} - no auth required")
        return False  # Skip authentication entirely
    
    def password_auth_supported(self) -> bool:
        """Enable password authentication (accept any/empty password)"""
        return True
    
    def validate_password(self, username: str, password: str) -> bool:
        """Accept any password including empty string"""
        logger.info(f"User {username} connected (public access)")
        return True
    
    def public_key_auth_supported(self) -> bool:
        """Disable public key authentication"""
        return False
    
    def kbdint_auth_supported(self) -> bool:
        """Disable keyboard-interactive authentication"""
        return False


class ResumeSSHSession(asyncssh.SSHServerSession):
    """Minimal session handler for Windows input routing bridge"""
    
    def connection_made(self, chan):
        """Called when session connection is established"""
        self.chan = chan
    
    def pty_requested(self, term_type, term_size, term_modes):
        """Accept PTY request and set raw mode for cross-platform compatibility"""
        self.chan.set_line_mode(False)  # Disable canonical input
        self.chan.set_echo(False)       # Disable server-side echo
        return True
    
    def shell_requested(self):
        """Accept shell request - process_factory handles TUI launch"""
        return True
    
    def data_received(self, data, datatype):
        """⭐ Windows input bridge: Routes keyboard input to PTY master fd
        
        Windows OpenSSH sends input via channel packets, not stdin.
        This bridge writes directly to the PTY master_fd exposed by the process.
        """
        process = self.chan.get_extra_info("process")
        
        if not process:
            return
        
        master_fd = getattr(process, "_pty_master_fd", None)
        if master_fd is None:
            return
        
        try:
            if isinstance(data, str):
                data = data.encode()
            os.write(master_fd, data)
        except OSError as e:
            logger.debug(f"Failed to write to PTY: {e}")


async def handle_client(process: SSHServerProcess) -> None:
    """Process factory handler - manages TUI lifecycle with PTY"""
    try:
        # Get terminal info
        term_type = process.get_terminal_type() or "xterm-256color"
        term_size = process.get_terminal_size()
        cols, rows = (term_size[0], term_size[1]) if term_size else (80, 24)
        
        logger.info(f"Starting TUI: Terminal={term_type}, Size={cols}x{rows}")
        
        # Environment setup
        env = os.environ.copy()
        env["TERM"] = term_type
        env["COLUMNS"] = str(cols)
        env["LINES"] = str(rows)
        env["PYTHONUNBUFFERED"] = "1"
        
        # Create PTY
        master_fd, slave_fd = pty.openpty()
        tty.setraw(slave_fd)
        
        # ⭐ Expose PTY master fd for session bridge (Windows input routing)
        process._pty_master_fd = master_fd
        
        # Set PTY size
        fcntl.ioctl(
            master_fd,
            termios.TIOCSWINSZ,
            struct.pack("HHHH", rows, cols, 0, 0),
        )
        
        # Launch TUI subprocess
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
        
        logger.info(f"TUI subprocess started with PID: {proc.pid}")
        os.close(slave_fd)
        
        # Forward output: PTY → stdin stream (Linux/macOS path)
        async def forward_pty_output():
            loop = asyncio.get_running_loop()
            try:
                while True:
                    data = await loop.run_in_executor(None, os.read, master_fd, 8192)
                    if not data:
                        break
                    
                    # Filter terminal reply sequences
                    data = ANSI_REPLY_RE.sub(b"", data)
                    
                    # Send to client
                    process.stdout.write(data.decode("utf-8", "ignore"))
                    
            except Exception as e:
                logger.debug(f"Output forwarding closed: {e}")
        
        # Forward input: stdin stream → PTY (Linux/macOS path)
        async def forward_stdin_input():
            try:
                async for data in process.stdin:
                    if isinstance(data, str):
                        data = data.encode()
                    os.write(master_fd, data)
            except Exception as e:
                logger.debug(f"Input forwarding closed: {e}")
        
        # Run both forwarders
        await asyncio.gather(
            forward_pty_output(),
            forward_stdin_input(),
            return_exceptions=True
        )
        
        # Cleanup
        try:
            os.close(master_fd)
        except:
            pass
        
        proc.wait()
        logger.info(f"TUI process exited with code: {proc.returncode}")
        process.exit(0)
        
    except Exception as e:
        logger.error(f"Error in handle_client: {e}", exc_info=True)
        process.exit(1)


async def start_server(host: str = '', port: int = 2222, host_key: str = 'host_key'):
    """Start the SSH server"""
    
    # Check if host key exists
    host_key_path = Path(host_key)
    if not host_key_path.exists():
        logger.error(f"Host key not found: {host_key}")
        logger.error("Generate one with: ssh-keygen -f host_key -N '' -t rsa")
        sys.exit(1)
    
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    logger.info(f"Starting SSH server on {host or '0.0.0.0'}:{port}")
    logger.info("Waiting for connections...")
    
    try:
        await asyncssh.listen(
            host,
            port,
            server_host_keys=[host_key],
            server_factory=ResumeSSHServer,
            process_factory=handle_client,      # ⭐ Primary: TUI lifecycle management
            session_factory=ResumeSSHSession,   # ⭐ Bridge: Windows input routing via data_received()
            line_editor=False,  # CRITICAL: Disable line editor for raw terminal mode
            # Disable other SSH features for security
            sftp_factory=None,
            allow_scp=False,
        )
        
        # Keep server running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Failed to start SSH server: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point"""
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
