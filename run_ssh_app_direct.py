"""Direct SSH wrapper for running the Textual app"""

import sys
import os

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

# Ensure TERM is set
if 'TERM' not in os.environ:
    os.environ['TERM'] = 'xterm-256color'

# Import and patch before creating the app
from src.tui_resume.app import ResumeApp

# Patch the LinuxDriver to disable mouse and terminal queries
try:
    from textual.drivers.linux_driver import LinuxDriver
    
    # Replace with no-op functions to prevent terminal queries
    def noop(self, *args, **kwargs):
        pass
    
    def noop_return_empty(self, *args, **kwargs):
        return ""
    
    # Disable mouse support (prevents mouse query sequences)
    LinuxDriver._enable_mouse_support = noop
    LinuxDriver._disable_mouse_support = noop
    
    # Disable any terminal synchronization/query methods
    # These methods send escape sequences that cause terminal responses
    if hasattr(LinuxDriver, '_request_terminal_sync_mode_update'):
        LinuxDriver._request_terminal_sync_mode_update = noop
    if hasattr(LinuxDriver, '_request_terminal_sync'):
        LinuxDriver._request_terminal_sync = noop
    if hasattr(LinuxDriver, '_enable_bracketed_paste'):
        LinuxDriver._enable_bracketed_paste = noop
    if hasattr(LinuxDriver, '_disable_bracketed_paste'):
        LinuxDriver._disable_bracketed_paste = noop
    if hasattr(LinuxDriver, '_query_terminal_capabilities'):
        LinuxDriver._query_terminal_capabilities = noop
    if hasattr(LinuxDriver, 'disable_input'):
        # Keep functionality but prevent query sequences
        original_disable_input = LinuxDriver.disable_input
        def safe_disable_input(self):
            try:
                self._input_disabled = True
            except:
                pass
        LinuxDriver.disable_input = safe_disable_input
    
    # Patch start_application_mode to prevent terminal queries
    if hasattr(LinuxDriver, 'start_application_mode'):
        original_start = LinuxDriver.start_application_mode
        def safe_start_application_mode(self):
            # Call original but filter out query sequences
            try:
                # Set up basic terminal mode without queries
                self.write("\x1b[?1049h")  # Alternate screen
                self.write("\x1b[?25l")    # Hide cursor
                self.flush()
            except:
                pass
        LinuxDriver.start_application_mode = safe_start_application_mode
    
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
