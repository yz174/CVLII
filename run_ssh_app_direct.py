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

# Patch the LinuxDriver to disable mouse entirely
try:
    from textual.drivers.linux_driver import LinuxDriver
    
    # Store original methods
    original_enable = LinuxDriver._enable_mouse_support
    original_disable = LinuxDriver._disable_mouse_support
    
    # Replace with no-op functions
    def noop_enable(self):
        pass
    
    def noop_disable(self):
        pass
    
    LinuxDriver._enable_mouse_support = noop_enable
    LinuxDriver._disable_mouse_support = noop_disable
    
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
