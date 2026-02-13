"""Direct SSH wrapper for running the Textual app"""

import sys
import os

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

# Tell Textual we are inside SSH / remote PTY environment
# This prevents certain terminal capability queries
os.environ["TEXTUAL_FORCE_TERMINAL"] = "1"
os.environ["TERM_PROGRAM"] = "ssh"

# Ensure TERM is set
if 'TERM' not in os.environ:
    os.environ['TERM'] = 'xterm-256color'

# Import and patch before creating the app
from src.tui_resume.app import ResumeApp

# Patch the LinuxDriver to disable terminal queries that cause artifacts
try:
    from textual.drivers.linux_driver import LinuxDriver
    
    # Create no-op function to replace query methods
    def _noop(*args, **kwargs):
        pass
    
    # Disable mouse support (prevents mouse query sequences)
    LinuxDriver._enable_mouse_support = _noop
    LinuxDriver._disable_mouse_support = _noop
    
    # Disable terminal capability queries that cause ESC[?2048;0$y responses
    if hasattr(LinuxDriver, '_request_terminal_sync_mode_support'):
        LinuxDriver._request_terminal_sync_mode_support = _noop
    if hasattr(LinuxDriver, '_request_cursor_position'):
        LinuxDriver._request_cursor_position = _noop
    if hasattr(LinuxDriver, '_request_device_attributes'):
        LinuxDriver._request_device_attributes = _noop
    
    # Disable bracketed paste queries
    if hasattr(LinuxDriver, '_enable_bracketed_paste'):
        LinuxDriver._enable_bracketed_paste = _noop
    if hasattr(LinuxDriver, '_disable_bracketed_paste'):
        LinuxDriver._disable_bracketed_paste = _noop
    
except Exception as e:
    print(f"Warning: Could not patch LinuxDriver: {e}", file=sys.stderr)

if __name__ == "__main__":
    try:
        app = ResumeApp()
        app.run()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
