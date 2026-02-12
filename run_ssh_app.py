"""SSH-compatible wrapper for running the Textual app"""

# Immediate startup signal - write directly to stderr so it's visible even if stdout fails
import sys
print("=== WRAPPER STARTED ===", file=sys.stderr, flush=True)

import os
import io

# Force Textual to detect terminal even through pipes
os.environ['TERM'] = os.environ.get('TERM', 'xterm-256color')
os.environ['COLORTERM'] = 'truecolor'
os.environ['FORCE_COLOR'] = '1'

# More aggressive TTY wrapper
class FakeTTY:
    def __init__(self, stream):
        self._stream = stream
        self._buffer = getattr(stream, 'buffer', stream)
    
    def isatty(self):
        return True  # Always claim to be a TTY
    
    def fileno(self):
        # Return a fake file descriptor
        try:
            return self._stream.fileno()
        except (AttributeError, io.UnsupportedOperation):
            return 1 if self._stream == sys.stdout else 0
    
    def write(self, data):
        if isinstance(data, bytes):
            if hasattr(self._buffer, 'write'):
                self._buffer.write(data)
            else:
                self._stream.write(data.decode('utf-8', errors='replace'))
        else:
            self._stream.write(data)
        self.flush()
    
    def flush(self):
        try:
            self._stream.flush()
        except:
            pass
    
    def __getattr__(self, name):
        return getattr(self._stream, name)

# Replace all streams
sys.stdout = FakeTTY(sys.stdout)
sys.stdin = FakeTTY(sys.stdin)
sys.stderr = FakeTTY(sys.stderr)

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Now import and run the app
from src.tui_resume.app import ResumeApp

if __name__ == "__main__":
    # Log to file so we can debug even after Textual takes over
    import logging
    logging.basicConfig(
        filename='textual_debug.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(message)s'
    )
    
    try:
        logging.info("Starting Textual app...")
        logging.info(f"stdout.isatty() = {sys.stdout.isatty()}")
        logging.info(f"TERM = {os.environ.get('TERM')}")
        logging.info("Creating ResumeApp instance...")
        
        app = ResumeApp()
        
        logging.info("Calling app.run()...")
        logging.info(f"App console file BEFORE: {app.console.file}")
        logging.info(f"App console is_terminal BEFORE: {app.console.is_terminal}")
        
        # FORCE Textual to use our stdout instead of _NullFile
        from rich.console import Console
        app.console = Console(
            file=sys.stdout,
            force_terminal=True,
            force_interactive=True,
            width=int(os.environ.get('COLUMNS', 80)),
            height=int(os.environ.get('LINES', 24)),
            legacy_windows=False
        )
        
        logging.info(f"App console file AFTER: {app.console.file}")
        logging.info(f"App console is_terminal AFTER: {app.console.is_terminal}")
        
        # Patch console write methods to log what's being output
        original_write = app.console.file.write
        def logged_write(data):
            if isinstance(data, str) and len(data) > 0:
                logging.info(f"Console writing {len(data)} chars (first 100): {repr(data[:100])}")
            elif isinstance(data, bytes) and len(data) > 0:
                logging.info(f"Console writing {len(data)} bytes")
            return original_write(data)
        
        app.console.file.write = logged_write
        
        logging.info("Starting app.run()...")
        
        # Check what driver Textual will use
        try:
            logging.info(f"App driver class: {app._driver_class}")
        except:
            pass
        
        # Force cross-platform driver instead of WindowsDriver
        try:
            # Try to use LinuxDriver which uses ANSI codes (works on modern Windows too)
            from textual.drivers.linux_driver import LinuxDriver
            logging.info("Forcing LinuxDriver (ANSI escape codes)")
            app._driver_class = LinuxDriver
        except ImportError:
            logging.warning("LinuxDriver not available, trying WindowsDriver")
            try:
                from textual.drivers.windows_driver import WindowsDriver
                logging.info("Falling back to WindowsDriver")
                app._driver_class = WindowsDriver
            except Exception as e:
                logging.error(f"Cannot force any driver: {e}")
        
        # Run with timeout to detect hangs
        import asyncio
        import threading
        
        result_holder = {'completed': False, 'error': None}
        
        def run_with_logging():
            try:
                logging.info("Thread starting app.run()...")
                app.run()
                logging.info("Thread: app.run() returned normally")
                result_holder['completed'] = True
            except Exception as e:
                logging.error(f"Thread: Exception in app.run(): {e}", exc_info=True)
                result_holder['error'] = e
        
        thread = threading.Thread(target=run_with_logging, daemon=False)
        thread.start()
        
        # Give it 10 seconds to start or fail
        thread.join(timeout=10.0)
        
        if thread.is_alive():
            logging.error("TIMEOUT: app.run() is hanging after 10 seconds")
            # App is hung, but we can't kill it cleanly
        elif result_holder['error']:
            logging.error(f"App failed with error: {result_holder['error']}")
        elif result_holder['completed']:
            logging.info("App completed successfully")
        else:
            logging.error("App thread died without completing or error")
        
        logging.info("App exited normally")
    except Exception as e:
        logging.error(f"ERROR running app: {e}", exc_info=True)
        print(f"ERROR running app: {e}", flush=True)
        import traceback
        traceback.print_exc()
