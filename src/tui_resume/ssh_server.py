"""SSH Server wrapper for TUI Resume application"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional

import asyncssh
from asyncssh import SSHServerProcess, SSHServerConnection, SSHServerSession, TerminalSizeChanged, BreakReceived


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


async def handle_client(process: SSHServerProcess) -> None:
    """Handle SSH client by running the TUI application"""
    logger.info("Starting TUI application for user")
    
    try:
        # Get terminal information
        term_type = process.get_terminal_type()
        term_size = process.get_terminal_size()
        
        width = term_size[0] if term_size else 80
        height = term_size[1] if term_size else 24
        
        logger.info(f"Terminal: {term_type}, Size: {width}x{height}")
        
        # Import pty for pseudo-terminal support
        import os
        import pty
        import fcntl
        import struct
        import termios
        
        # Create a pseudo-terminal
        master_fd, slave_fd = pty.openpty()
        
        # Set terminal size on the PTY
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, struct.pack('HHHH', height, width, 0, 0))
        
        # Set environment variables for subprocess
        env = os.environ.copy()
        env['TERM'] = term_type or 'xterm-256color'
        env['COLUMNS'] = str(width)
        env['LINES'] = str(height)
        env['PYTHONUNBUFFERED'] = '1'
        
        # Create command to run the app
        cmd = f'{sys.executable} run_ssh_app.py'
        
        logger.info(f"Starting subprocess with PTY: {cmd}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Create subprocess connected to PTY slave
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            cwd=os.getcwd()
        )
        
        # Close slave fd in parent process (child still has it)
        os.close(slave_fd)
        # Close slave fd in parent process (child still has it)
        os.close(slave_fd)
        
        logger.info(f"Subprocess started with PID: {proc.pid}")
        
        # Set master_fd to non-blocking mode
        os.set_blocking(master_fd, False)
        
        # Create tasks to bridge SSH streams and PTY master
        async def pipe_stdin():
            """Copy data from SSH client to PTY master (subprocess stdin)"""
            try:
                while True:
                    try:
                        data = await process.stdin.read(4096)
                        if not data:
                            break
                        # SSH provides string, PTY needs bytes
                        if isinstance(data, str):
                            data = data.encode('utf-8')
                        
                        # Write to PTY master (non-blocking)
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, os.write, master_fd, data)
                        
                    except TerminalSizeChanged as size_change:
                        # Handle terminal resize
                        new_width, new_height = size_change.width, size_change.height
                        logger.info(f"Terminal resized to {new_width}x{new_height}")
                        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, 
                                  struct.pack('HHHH', new_height, new_width, 0, 0))
                        continue
                    except BreakReceived:
                        continue
            except Exception as e:
                logger.debug(f"stdin pipe closed: {e}")
            finally:
                try:
                    os.close(master_fd)
                except:
                    pass
        
        async def pipe_stdout():
            """Copy data from PTY master (subprocess stdout) to SSH client"""
            try:
                loop = asyncio.get_event_loop()
                while True:
                    try:
                        # Read from PTY master (non-blocking)
                        data = await loop.run_in_executor(None, os.read, master_fd, 8192)
                        if not data:
                            break
                        # PTY provides bytes, SSH needs string
                        if isinstance(data, bytes):
                            data = data.decode('utf-8', errors='replace')
                        process.stdout.write(data)
                        await process.stdout.drain()
                    except BlockingIOError:
                        # No data available, sleep briefly
                        await asyncio.sleep(0.01)
                        continue
                    except OSError:
                        # PTY closed
                        break
            except Exception as e:
                logger.debug(f"stdout pipe closed: {e}")
        
        # Run both pipes concurrently and wait for process to finish
        try:
            await asyncio.gather(
                pipe_stdin(),
                pipe_stdout(),
                proc.wait(),
                return_exceptions=True
            )
        finally:
            # Ensure PTY master is closed
            try:
                os.close(master_fd)
            except:
                pass
                
            # Ensure subprocess is terminated
            if proc.returncode is None:
                try:
                    proc.terminate()
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                except:
                    pass
        
        # Check subprocess exit code
        exit_code = proc.returncode if proc.returncode is not None else 0
        logger.info(f"TUI application exited with code {exit_code}")
        
    except Exception as e:
        logger.error(f"Error running TUI app: {e}", exc_info=True)
        try:
            process.stderr.write(f"Error: {e}\n")
        except:
            pass
    finally:
        # Only call exit if connection is still active
        try:
            if not process.channel.is_closing():
                process.exit(0)
        except:
            pass  # Connection already closed


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
            # Disable other SSH features for security
            session_factory=None,
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
