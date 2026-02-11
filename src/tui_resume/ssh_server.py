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
        
        # Set environment variables for subprocess
        import os
        env = os.environ.copy()
        env['TERM'] = term_type or 'xterm-256color'
        env['COLUMNS'] = str(width)
        env['LINES'] = str(height)
        env['PYTHONUNBUFFERED'] = '1'
        
        # Try using shell=True to get proper terminal handling
        # Create a command that runs Python with the wrapper
        import platform
        if platform.system() == 'Windows':
            # Use the wrapper script
            cmd = f'{sys.executable} run_ssh_app.py'
        else:
            cmd = f'{sys.executable} run_ssh_app.py'
        
        logger.info(f"Starting subprocess: {cmd}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=os.getcwd()
        )
        
        logger.info(f"Subprocess started with PID: {proc.pid}")
        
        # Create tasks to bridge SSH streams and subprocess pipes
        async def pipe_stdin():
            """Copy data from SSH client to subprocess stdin"""
            try:
                while True:
                    try:
                        data = await process.stdin.read(1)  # Read byte by byte for responsiveness
                        if not data:
                            break
                        # SSH provides string, subprocess needs bytes
                        if isinstance(data, str):
                            data = data.encode('utf-8')
                        proc.stdin.write(data)
                        await proc.stdin.drain()
                    except TerminalSizeChanged:
                        continue
                    except BreakReceived:
                        continue
            except Exception as e:
                logger.debug(f"stdin pipe closed: {e}")
            finally:
                try:
                    if proc.stdin and not proc.stdin.is_closing():
                        proc.stdin.close()
                        await proc.stdin.wait_closed()
                except:
                    pass
        
        async def pipe_stdout():
            """Copy data from subprocess stdout to SSH client"""
            try:
                while True:
                    data = await proc.stdout.read(8192)
                    if not data:
                        break
                    # Subprocess provides bytes, SSH needs string
                    if isinstance(data, bytes):
                        data = data.decode('utf-8', errors='replace')
                    process.stdout.write(data)
                    await process.stdout.drain()
            except Exception as e:
                logger.debug(f"stdout pipe closed: {e}")
        
        async def pipe_stderr():
            """Copy data from subprocess stderr to SSH client"""
            try:
                while True:
                    data = await proc.stderr.read(8192)
                    if not data:
                        break
                    # Subprocess provides bytes, SSH needs string
                    if isinstance(data, bytes):
                        data = data.decode('utf-8', errors='replace')
                    # Send stderr to stdout so errors are visible
                    process.stdout.write(f"[ERROR] {data}")
                    await process.stdout.drain()
            except Exception as e:
                logger.debug(f"stderr pipe closed: {e}")
        
        # Run all pipes concurrently and wait for process to finish
        try:
            await asyncio.gather(
                pipe_stdin(),
                pipe_stdout(),
                pipe_stderr(),
                proc.wait(),
                return_exceptions=True
            )
        finally:
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
