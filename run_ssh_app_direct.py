"""Direct SSH wrapper for running the Textual app"""

import sys
import os
import io

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

# Ensure TERM is set
if 'TERM' not in os.environ:
    os.environ['TERM'] = 'xterm-256color'

# Create a filter for stdout that blocks terminal query sequences
class QueryFilterStream:
    """Filters out terminal query escape sequences that would cause responses"""
    def __init__(self, stream):
        self.stream = stream
        self.buffer = b''
    
    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Filter out common terminal query sequences that cause responses:
        # ESC[6n - Cursor Position Report (CPR)
        # ESC[c or ESC[>c or ESC[>0c - Device Attributes (DA)
        # ESC[?...$ - DECRQM requests
        # ESC]...ST - Operating System Commands that query
        filtered = data
        
        # Remove cursor position queries
        filtered = filtered.replace(b'\x1b[6n', b'')
        
        # Remove device attribute queries
        filtered = filtered.replace(b'\x1b[c', b'')
        filtered = filtered.replace(b'\x1b[>c', b'')
        filtered = filtered.replace(b'\x1b[>0c', b'')
        filtered = filtered.replace(b'\x1b[=c', b'')
        
        # Remove DECRQM queries (these generate responses like "?2048;0$y")
        # Pattern: ESC[?<digits>$p
        import re
        filtered = re.sub(rb'\x1b\[\?\d+\$p', b'', filtered)
        
        # Remove other query sequences
        filtered = re.sub(rb'\x1b\[>\d*c', b'', filtered)
        
        if filtered:
            self.stream.write(filtered)
        return len(data)
    
    def flush(self):
        self.stream.flush()
    
    def __getattr__(self, name):
        return getattr(self.stream, name)

# Wrap stdout with query filter
sys.stdout = QueryFilterStream(sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout)

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
