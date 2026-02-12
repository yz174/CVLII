"""Direct SSH wrapper for running the Textual app"""

import sys
import os

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

# Ensure TERM is set
if 'TERM' not in os.environ:
    os.environ['TERM'] = 'xterm-256color'

# Disable mouse support for SSH
os.environ['TEXTUAL_NO_MOUSE'] = '1'

# Import and run the app
from src.tui_resume.app import ResumeApp

if __name__ == "__main__":
    try:
        app = ResumeApp()
        # Disable mouse support
        app._disable_mouse = True
        app.run()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
