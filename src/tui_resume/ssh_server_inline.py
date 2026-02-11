"""SSH server that runs Textual inline (same process) instead of subprocess"""

import asyncio
import asyncssh
import logging
import sys
from pathlib import Path
from io import StringIO

from src.tui_resume.app import ResumeApp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ResumeSSHServer(asyncssh.SSHServer):
    """SSH server that provides access to TUI resume"""
    
    def connection_made(self, conn: asyncssh.SSHServerConnection) -> None:
        """Called when a connection is made"""
        peername = conn.get_extra_info('peername')
        logger.info(f"Connection received from {peername[0]}:{peername[1]}")
    
    def connection_lost(self, exc: Exception) -> None:
        """Called when connection is lost"""
        if exc:
            logger.error(f"Connection error: {exc}")
    
    def begin_auth(self, username: str) -> bool:
        """No authentication required - public portfolio access"""
        logger.info(f"Connection from user: {username} - no auth required")
        return False
    
    def password_auth_supported(self) -> bool:
        """Allow password authentication but accept any password"""
        return True
    
    def validate_password(self, username: str, password: str) -> bool:
        """Accept any password for public access"""
        return True
    
    def kbdint_auth_supported(self) -> bool:
        """Disable keyboard-interactive authentication"""
        return False


async def handle_client(process: asyncssh.SSHServerProcess) -> None:
    """Handle SSH client by running the TUI application inline"""
    logger.info("Starting inline TUI application for user")
    
    try:
        # Get terminal information
        term_type = process.get_terminal_type()
        term_size = process.get_terminal_size()
        
        width = term_size[0] if term_size else 80
        height = term_size[1] if term_size else 24
        
        logger.info(f"Terminal: {term_type}, Size: {width}x{height}")
        
        # Create app instance
        app = ResumeApp()
        
        # Redirect app output to SSH stream
        from rich.console import Console
        
        # Create a custom Console that writes to SSH stdout
        class SSHConsole(Console):
            def __init__(self, ssh_stdout, **kwargs):
                self._ssh_stdout = ssh_stdout
                # Use StringIO as file handle
                super().__init__(file=StringIO(), force_terminal=True, **kwargs)
            
            def _write(self, text: str) -> None:
                """Override to write to SSH stream"""
                try:
                    self._ssh_stdout.write(text)
                except:
                    pass
        
        # Replace app console with SSH-aware one
        app.console = SSHConsole(
            process.stdout,
            width=width,
            height=height,
            legacy_windows=False
        )
        
        logger.info("Starting app.run()...")
        
        # Run the app - this will block until app exits
        try:
            # Use run_test to run without actual terminal
            async with app.run_test(size=(width, height)) as pilot:
                # Keep running until user disconnects
                while not process.stdin.at_eof():
                    data = await process.stdin.read(1)
                    if not data:
                        break
                    # Handle keyboard input
                    # For now just wait for disconnect
                    await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"App error: {e}", exc_info=True)
        
        logger.info("TUI application exited")
        
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
            pass


async def start_server(host: str = '', port: int = 2222, host_key: str = 'host_key'):
    """Start the SSH server"""
    
    # Check if host key exists
    host_key_path = Path(host_key)
    if not host_key_path.exists():
        logger.error(f"Host key not found: {host_key_path}")
        logger.info("Generate a host key with: python generate_key.py")
        sys.exit(1)
    
    await asyncssh.listen(
        host,
        port,
        server_host_keys=[str(host_key_path)],
        server_factory=ResumeSSHServer,
        process_factory=handle_client,
        encoding='utf-8'
    )
    
    logger.info(f"SSH server running on {host or '0.0.0.0'}:{port}")
    logger.info("Connect with: ssh -p {port} {host or 'localhost'}")


async def main():
    """Main entry point"""
    logger.info(f"Starting SSH server on 0.0.0.0:2222")
    logger.info("Waiting for connections...")
    
    await start_server()
    
    # Keep servidor running
    await asyncio.Event().wait()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
