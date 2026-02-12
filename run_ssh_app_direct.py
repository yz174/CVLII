"""Direct rendering approach - bypass Textual's driver system"""

import sys
import os

# Set up environment
os.environ['TERM'] = 'xterm-256color'
os.environ['COLORTERM'] = 'truecolor'
os.environ['PYTHONUNBUFFERED'] = '1'

# Try headless mode with output capture
os.environ['TEXTUAL_DRIVER'] = 'headless'

from src.tui_resume.app import ResumeApp
from textual.pilot import Pilot
import asyncio

async def run_headless():
    """Run in headless mode and capture output"""
    app = ResumeApp()
    
    async with app.run_test() as pilot:
        # Keep app running until interrupted
        await asyncio.sleep(3600)  # 1 hour timeout

if __name__ == "__main__":
    print("Starting headless Textual app...", flush=True)
    try:
        asyncio.run(run_headless())
    except KeyboardInterrupt:
        print("App exited", flush=True)
