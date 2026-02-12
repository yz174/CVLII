"""SSH-compatible wrapper for running the Textual app"""

import sys
import os

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

# Ensure TERM is set
if 'TERM' not in os.environ:
    os.environ['TERM'] = 'xterm-256color'

# Now import and run the app
from src.tui_resume.app import ResumeApp

if __name__ == "__main__":
    try:
        app = ResumeApp()
        app.run()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
