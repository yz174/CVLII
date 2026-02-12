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
from textual.drivers.linux_driver import LinuxDriver

# Monkey-patch LinuxDriver to disable mouse support
original_enable_mouse = LinuxDriver._enable_mouse_support
LinuxDriver._enable_mouse_support = lambda self: None

original_disable_mouse = LinuxDriver._disable_mouse_support  
LinuxDriver._disable_mouse_support = lambda self: None

if __name__ == "__main__":
    try:
        app = ResumeApp()
        app.run()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
