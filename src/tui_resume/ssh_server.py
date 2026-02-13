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
    """SSH Session handler for PTY negotiation only"""
    
    def __init__(self, *args, **kwargs):
        # AsyncSSH passes arguments but SSHServerSession has no __init__
        pass
    
    def connection_made(self, chan):
        """Called when session connection is established"""
        self.chan = chan
    
    def pty_requested(self, term_type, term_size, term_modes):
        """Accept PTY request and set raw mode for Windows compatibility"""
        self.chan.set_line_mode(False)  # Disable canonical input
        self.chan.set_echo(False)       # Disable server-side echo
        return True
    
    def shell_requested(self):
        """Accept shell request - actual TUI launch happens in process_factory"""
        return True


async def handle_client(process: SSHServerProcess) -> None:
    """Handle SSH client by running the TUI application in a PTY"""
    logger.info("Starting PTY-backed TUI session")
    
    try:
        # Get terminal information
        term_type = process.get_terminal_type() or "xterm-256color"
        term_size = process.get_terminal_size()
        cols, rows = term_size or (80, 24)
        
        logger.info(f"Terminal: {term_type}, Size: {cols}x{rows}")
        
        # Environment variables
        env = os.environ.copy()
        env["TERM"] = term_type
        env["COLUMNS"] = str(cols)
        env["LINES"] = str(rows)
        env["PYTHONUNBUFFERED"] = "1"
        
        # Create PTY
        master_fd, slave_fd = pty.openpty()
        tty.setraw(slave_fd)
        
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
        
        loop = asyncio.get_running_loop()
        
        # PTY output → SSH client
        async def pty_to_ssh():
            try:
                while True:
                    data = await loop.run_in_executor(None, os.read, master_fd, 8192)
                    if not data:
                        break
                    # Filter terminal reply sequences
                    data = ANSI_REPLY_RE.sub(b"", data)
                    process.stdout.write(data.decode(errors="replace"))
                    await process.stdout.drain()
            except Exception as e:
                logger.debug(f"pty_to_ssh closed: {e}")
        
        # SSH client input → PTY
        async def ssh_to_pty():
            try:
                while True:
                    data = await process.stdin.read(4096)
                    if not data:
                        break
                    if isinstance(data, str):
                        data = data.encode()
                    await loop.run_in_executor(None, os.write, master_fd, data)
            except Exception as e:
                logger.debug(f"ssh_to_pty closed: {e}")
        
        # Run all I/O tasks
        await asyncio.gather(
            pty_to_ssh(),
            ssh_to_pty(),
            loop.run_in_executor(None, proc.wait),
            return_exceptions=True,
        )
        
        logger.info(f"TUI process exited with code: {proc.returncode}")
        
    except Exception as e:
        logger.error(f"Error running TUI: {e}", exc_info=True)
    finally:
        try:
            os.close(master_fd)
        except:
            pass
        try:
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
            session_factory=ResumeSSHSession,  # PTY negotiation
            process_factory=handle_client,     # ⭐ Required for active I/O loop
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
