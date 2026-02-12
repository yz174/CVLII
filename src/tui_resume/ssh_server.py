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
        
        # Create command to run the app directly
        cmd = f'{sys.executable} -u run_ssh_app_direct.py'
        
        logger.info(f"Starting subprocess: {cmd}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Create subprocess with pipes (no PTY needed - Textual will adapt)
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
                buffer = b""
                while True:
                    try:
                        data = await process.stdin.read(4096)
                        if not data:
                            break
                        # SSH provides string, subprocess needs bytes
                        if isinstance(data, str):
                            data = data.encode('utf-8')
                        
                        # Add to buffer for processing
                        buffer += data
                        
                        # Filter out terminal query responses (CSI responses)
                        # These include: cursor position reports, device attributes, mode reports, etc.
                        # Patterns to filter:
                        # - ESC[digits;digitsR (cursor position report)
                        # - ESC[?digits;digits$letter (mode report like ?2048;0$y)
                        # - ESC[digits;digits$letter (other reports)
                        # - ESC[<...M or ESC[<...m (mouse sequences)
                        filtered = b""
                        i = 0
                        last_complete = 0  # Track last byte we fully processed
                        
                        while i < len(buffer):
                            # Check for escape sequence responses
                            if buffer[i:i+1] == b'\x1b':
                                if i+1 >= len(buffer):
                                    # Incomplete ESC sequence, keep in buffer
                                    break
                                if buffer[i+1:i+2] == b'[':
                                    # This is a CSI sequence, check if it's a response
                                    j = i + 2
                                    
                                    # Check for optional ? or > after [
                                    if j < len(buffer) and buffer[j:j+1] in b'?>':
                                        j += 1
                                    
                                    # Skip digits, semicolons
                                    while j < len(buffer) and buffer[j:j+1] in b'0123456789;':
                                        j += 1
                                    
                                    # Need terminator to complete the sequence
                                    if j >= len(buffer):
                                        # Incomplete sequence, keep in buffer
                                        break
                                    
                                    # Check for response terminators
                                    terminator = buffer[j:j+1]
                                    if terminator == b'$':
                                        # Mode report: need one more byte (the letter)
                                        if j+1 >= len(buffer):
                                            # Incomplete, keep in buffer
                                            break
                                        # Complete response like ?2048;0$y - skip it
                                        i = j + 2
                                        last_complete = i
                                        continue
                                    elif terminator in b'R~':
                                        # Complete cursor position or other response - skip it
                                        i = j + 1
                                        last_complete = i
                                        continue
                                    elif terminator == b'<':
                                        # Mouse sequence, find M or m terminator
                                        while j < len(buffer) and buffer[j:j+1] not in b'Mm':
                                            j += 1
                                        if j >= len(buffer):
                                            # Incomplete, keep in buffer
                                            break
                                        # Complete mouse sequence - skip it
                                        i = j + 1
                                        last_complete = i
                                        continue
                            
                            # Not a response sequence, keep this byte
                            filtered += buffer[i:i+1]
                            i += 1
                            last_complete = i
                        
                        # Keep incomplete sequences in buffer for next iteration
                        buffer = buffer[last_complete:]
                        
                        if filtered:
                            proc.stdin.write(filtered)
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
                    # Send stderr directly without prefix (TUI might use stderr)
                    process.stdout.write(data)
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
