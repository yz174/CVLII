"""Windows-friendly launcher for TUI resume - runs directly without SSH"""

import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add src to path if needed
if 'src' not in sys.path:
    sys.path.insert(0, 'src')

from src.tui_resume.app import ResumeApp

if __name__ == '__main__':
    print("=" * 60)
    print("TUI RESUME - Interactive Terminal Portfolio")
    print("=" * 60)
    print()
    print("Starting application...")
    print()
    print("Controls:")
    print("  - Use Tab / Arrow Keys to navigate")
    print("  - Press number keys 1-5 for quick navigation")  
    print("  - Play the mini-game to unlock contact info")
    print("  - Press 'q' or Ctrl+C to quit")
    print()
    print("=" * 60)
    print()
    
    try:
        app = ResumeApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication closed.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
