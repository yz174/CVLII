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
    """SSH Session handler that accepts PTY requests and manages TUI lifecycle"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.master_fd = None
        self.proc = None
        self.loop = None
        self.term_type = None
        self.cols = 80
        self.rows = 24
    
    def connection_made(self, chan):
        """Called when session connection is established"""
        self.chan = chan
        self.loop = asyncio.get_event_loop()
        logger.debug("Session connection established")
    
    def pty_requested(self, term_type, term_size, term_modes):
        """Accept PTY request from client - critical for proper terminal behavior"""
        logger.debug(f"PTY requested: {term_type}, size: {term_size}")
        # ⭐ CRITICAL: Set raw mode DURING PTY negotiation for Windows compatibility
        self.chan.set_line_mode(False)  # Disable canonical input (line buffering)
        self.chan.set_echo(False)       # Disable server-side echo
        
        # Store terminal info for PTY setup
        self.term_type = term_type or "xterm-256color"
        self.cols, self.rows = term_size or (80, 24)
        return True
    
    def shell_requested(self):
        """Accept shell request - launch TUI asynchronously"""
        logger.debug("Shell requested - launching TUI")
        asyncio.create_task(self.start_tui())
        return True
    
    def exec_requested(self, command):
        """Reject exec commands - force PTY/shell only"""
        logger.debug(f"Exec command rejected: {command}")
        return False
    
    async def start_tui(self):
        """⭐ Launch the TUI application in a PTY - session owns the entire lifecycle"""
        try:
            logger.info(f"Starting TUI: Terminal={self.term_type}, Size={self.cols}x{self.rows}")
            
            # Environment variables
            env = os.environ.copy()
            env["TERM"] = self.term_type
            env["COLUMNS"] = str(self.cols)
            env["LINES"] = str(self.rows)
            env["PYTHONUNBUFFERED"] = "1"
            
            # Create PTY
            self.master_fd, slave_fd = pty.openpty()
            tty.setraw(slave_fd)
            
            # Set PTY size
            fcntl.ioctl(
                self.master_fd,
                termios.TIOCSWINSZ,
                struct.pack("HHHH", self.rows, self.cols, 0, 0),
            )
            
            # Launch TUI subprocess
            self.proc = subprocess.Popen(
                [sys.executable, "-u", "run_ssh_app_direct.py"],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                env=env,
                cwd=os.getcwd(),
                preexec_fn=os.setsid,
                close_fds=True,
            )
            
            logger.info(f"TUI subprocess started with PID: {self.proc.pid}")
            os.close(slave_fd)
            
            # Start output forwarding
            await self.pty_to_client()
            
        except Exception as e:
            logger.error(f"Error starting TUI: {e}", exc_info=True)
            self.chan.exit(1)
    
    async def pty_to_client(self):
        """Forward PTY output to SSH client with filtering"""
        try:
            while True:
                data = await self.loop.run_in_executor(
                    None, os.read, self.master_fd, 8192
                )
                if not data:
                    break
                
                # Filter terminal reply sequences
                data = ANSI_REPLY_RE.sub(b'', data)
                
                # Send to client
                self.chan.write(data.decode("utf-8", errors="replace"))
                
        except Exception as e:
            logger.debug(f"PTY output closed: {e}")
        finally:
            # Cleanup
            if self.master_fd:
                try:
                    os.close(self.master_fd)
                except:
                    pass
            if self.proc:
                self.proc.wait()
                logger.info(f"TUI process exited with code: {self.proc.returncode}")
            self.chan.exit(0)
    
    def data_received(self, data, datatype):
        """⭐ CRITICAL: Direct keyboard input routing for Windows compatibility
        Windows OpenSSH sends keyboard input as SSH channel data packets.
        This callback receives ALL client input regardless of OS."""
        if self.master_fd is not None:
            try:
                if isinstance(data, str):
                    data = data.encode('utf-8')
                os.write(self.master_fd, data)
            except OSError as e:
                logger.debug(f"Failed to write to PTY: {e}")


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
            session_factory=ResumeSSHSession,  # ⭐ Pure session-driven architecture
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
