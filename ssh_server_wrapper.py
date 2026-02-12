"""Simple SSH server wrapper that directly runs the Textual app"""
import asyncio
import asyncssh
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MySSHServer(asyncssh.SSHServer):
    def begin_auth(self, username):
        return False

async def handle_client(process):
    """Run app directly in main thread"""
    logger.info("Client connected")
    
    # Patch signal before importing textual
    import signal
    original_signal = signal.signal
    signal.signal = lambda signum, handler: None
    
    try:
        from src.tui_resume.app import ResumeApp
        
        # Restore signal after import
        signal.signal = original_signal
        
        app = ResumeApp()
        
        # Run the app - output will go to stdout which SSH captures
        await app.run_async()
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        process.stdout.write(f"Error: {e}\n")

async def main():
    logger.info("Starting SSH server on 0.0.0.0:2222")
    
    await asyncssh.listen(
        host='0.0.0.0',
        port=2222,
        server_host_keys=['host_key'],
        server_factory=MySSHServer,
        process_factory=handle_client
    )
    
    logger.info("Server ready!")
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())