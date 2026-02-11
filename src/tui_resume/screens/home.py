"""Home screen with generative ASCII background"""

from textual.screen import Screen
from textual.app import ComposeResult
from ..widgets import GenerativeBackground


class HomeScreen(Screen):
    """Home screen displaying animated ASCII art background"""
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        # Use static mode for better performance (set animated=True for animation)
        yield GenerativeBackground(animated=False)
    
    def on_mount(self) -> None:
        """Called when screen is mounted"""
        pass
