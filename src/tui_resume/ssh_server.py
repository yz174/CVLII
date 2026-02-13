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
    """SSH Session handler that accepts PTY requests"""
    
    def __init__(self):
        self._process = None
        self.master_fd = None  # Will be set by handle_client
    
    def connection_made(self, chan):
        """Called when session connection is established"""
        self._chan = chan
        chan.session = self  # ⭐ Attach session to channel for access from process
    
    def pty_requested(self, term_type, term_size, term_modes):
        """Accept PTY request from client - critical for proper terminal behavior"""
        logger.debug(f"PTY requested: {term_type}, size: {term_size}")
        # ⭐ CRITICAL: Set raw mode DURING PTY negotiation for Windows compatibility
        # Windows SSH clients lock input mode at PTY allocation time
        # Linux/macOS renegotiate automatically, Windows does not
        self._chan.set_line_mode(False)  # Disable canonical input (line buffering)
        self._chan.set_echo(False)       # Disable server-side echo
        return True
    
    def shell_requested(self):
        """Accept shell request - our TUI is the shell"""
        logger.debug("Shell requested")
        return True
    
    def exec_requested(self, command):
        """Reject exec commands - force PTY/shell only"""
        logger.debug(f"Exec command rejected: {command}")
        return False
    
    def data_received(self, data, datatype):
        """⭐ CRITICAL: Direct keyboard input routing for Windows compatibility
        Windows OpenSSH sends keyboard input as SSH channel data packets
        that don't reach process.stdin.read() in custom PTY configurations.
        This callback receives ALL client input regardless of OS."""
        if self.master_fd is not None:
            try:
                # Ensure data is bytes
                if isinstance(data, str):
                    data = data.encode('utf-8')
                # Write directly to PTY master (blocking operation)
                os.write(self.master_fd, data)
            except OSError as e:
                logger.debug(f"Failed to write to PTY: {e}")


async def handle_client(process: SSHServerProcess) -> None:
    """Handle SSH client by running the TUI application in a PTY"""
    logger.info("Starting PTY-backed TUI session")
    
    try:
        # Get terminal information FIRST
        term_type = process.get_terminal_type() or "xterm-256color"
        term_size = process.get_terminal_size()
        
        cols = term_size[0] if term_size else 80
        rows = term_size[1] if term_size else 24
        
        logger.info(f"Terminal: {term_type}, Size: {cols}x{rows}")
        
        # Set environment variables for subprocess
        env = os.environ.copy()
        env["TERM"] = term_type
        env["COLUMNS"] = str(cols)
        env["LINES"] = str(rows)
        env["PYTHONUNBUFFERED"] = "1"
        
        # ---- CREATE PTY ----
        # This creates a pseudo-terminal pair (master/slave)
        # The slave acts like a real terminal device for the TUI app
        master_fd, slave_fd = pty.openpty()
        
        # ⭐ CRITICAL: Connect PTY to session for direct input routing
        # Windows SSH clients send input via data_received() callback, not stdin
        session = process.channel.session
        if session is not None:
            session.master_fd = master_fd
        
        # ---- CRITICAL: Set PTY to RAW mode ----
        # This disables line buffering and allows immediate keyboard input
        # Without this, Textual won't receive keypresses until Enter is pressed
        tty.setraw(slave_fd)
        
        # NOW set PTY size to match SSH client terminal
        def set_pty_size(fd, cols, rows):
            """Set the terminal size for the PTY"""
            fcntl.ioctl(
                fd,
                termios.TIOCSWINSZ,
                struct.pack("HHHH", rows, cols, 0, 0)
            )
        
        set_pty_size(master_fd, cols, rows)
        
        # Command to run the TUI app
        cmd = [sys.executable, "-u", "run_ssh_app_direct.py"]
        
        logger.info(f"Starting subprocess in PTY: {' '.join(cmd)}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Spawn subprocess attached to the slave side of the PTY
        # This gives Textual a real terminal device (/dev/pts/X)
        proc = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            cwd=os.getcwd(),
            preexec_fn=os.setsid,  # Create new session
            close_fds=True,
        )
        
        logger.info(f"Subprocess started with PID: {proc.pid}")
        
        # Close slave fd in parent (only child uses it)
        os.close(slave_fd)
        
        loop = asyncio.get_running_loop()
        
        # ---- PTY master → SSH client ----
        async def pty_to_ssh():
            """Read from PTY master and send to SSH client, filtering terminal replies"""
            try:
                while True:
                    # Use executor for blocking os.read
                    data = await loop.run_in_executor(
                        None, os.read, master_fd, 8192
                    )
                    if not data:
                        break
                    
                    # ---- FILTER TERMINAL REPLY SEQUENCES ----
                    # Remove terminal mode reports like ESC[?2048;0$y that appear as artifacts
                    # These are responses to terminal capability queries from the SSH client
                    data = ANSI_REPLY_RE.sub(b'', data)
                    
                    # Decode and send to SSH client
                    process.stdout.write(
                        data.decode("utf-8", errors="replace")
                    )
                    await process.stdout.drain()
            except Exception as e:
                logger.debug(f"pty_to_ssh closed: {e}")
        
        # ⭐ NOTE: SSH input now handled by session.data_received() callback
        # This fixes Windows compatibility where process.stdin.read() misses
        # keyboard input sent as SSH extended data packets
        
        # Run all tasks concurrently
        await asyncio.gather(
            pty_to_ssh(),
            loop.run_in_executor(None, proc.wait),
            return_exceptions=True,
        )
        
        logger.info(f"TUI application exited with code {proc.returncode}")
        
    except Exception as e:
        logger.error(f"Error running TUI app: {e}", exc_info=True)
        try:
            process.stderr.write(f"Error: {e}\n")
        except:
            pass
    finally:
        # Clean up PTY
        try:
            os.close(master_fd)
        except:
            pass
        
        # Exit SSH session
        try:
            if not process.channel.is_closing():
                process.exit(0)
        except:
            pass


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
            process_factory=handle_client,
            session_factory=ResumeSSHSession,  # Critical: Accept PTY requests
            line_editor=False,  # CRITICAL: Disable line editor for raw terminal mode (TUI needs immediate key forwarding)
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
