"""Home screen with ASCII art and typing animation"""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive
from textual.timer import Timer


class HomeScreen(Screen):
    """Home screen displaying ASCII art and animated greeting"""
    
    CSS = """
    HomeScreen {
        background: $background;
        align: center middle;
    }
    
    #home-container {
        width: auto;
        height: auto;
        align: center middle;
    }
    
    #ascii-art {
        width: auto;
        height: auto;
        text-align: center;
        margin-bottom: 2;
    }
    
    #greeting-text {
        width: auto;
        height: auto;
        text-align: center;
        margin-bottom: 1;
    }
    
    #welcome-text {
        width: auto;
        height: auto;
        text-align: center;
    }
    """
    
    # Reactive variables for typing animation
    typing_text = reactive("")
    typing_forward = reactive(True)
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        from textual.containers import Vertical
        
        with Vertical(id="home-container"):
            yield Static(self._get_ascii_art(), id="ascii-art")
            yield Static("", id="greeting-text")
            yield Static("[bold cyan]Welcome to my World.."
            "Here you will find [/bold cyan]", id="welcome-text")
    
    def on_mount(self) -> None:
        """Called when screen is mounted"""
        # Start typing animation
        self.full_text = "Hi Grok!"
        self.current_index = 0
        self.typing_forward = True
        self.set_interval(0.15, self._update_typing)
    
    def _update_typing(self) -> None:
        """Update typing animation"""
        if self.typing_forward:
            # Typing forward
            self.current_index += 1
            if self.current_index >= len(self.full_text):
                self.typing_forward = False
                # Pause at full text
                self.set_timer(1.5, lambda: None)
        else:
            # Typing backward (deleting)
            self.current_index -= 1
            if self.current_index <= 0:
                self.typing_forward = True
                # Pause at empty
                self.set_timer(0.5, lambda: None)
        
        # Update the greeting text
        displayed_text = self.full_text[:self.current_index]
        greeting_widget = self.query_one("#greeting-text", Static)
        greeting_widget.update(f"[bold yellow]{displayed_text}▌[/bold yellow]")
    
    def _get_ascii_art(self) -> str:
        """Return Uzii ASCII art"""
        return """[cyan]░██     ░██            ░██░██
░██     ░██                  
░██     ░██ ░█████████ ░██░██
░██     ░██      ░███  ░██░██
░██     ░██    ░███    ░██░██
 ░██   ░██   ░███      ░██░██
  ░██████   ░█████████ ░██░██[/cyan]"""
