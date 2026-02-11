"""Welcome screen with CVLI title and animated welcome message"""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Input
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style
from rich.segment import Segment
import random


class WelcomeScreen(Screen):
    """Welcome screen displayed on app launch"""
    
    CSS = """
    WelcomeScreen {
        background: $background;
        align: left top;
        padding: 4 6;
    }
    
    #cvli-title {
        width: auto;
        height: auto;
        margin-bottom: 1;
        padding-left: 4;
        padding-right: 4;
    }
    
    #welcome-animation {
        width: auto;
        height: auto;
        margin-bottom: 2;
        text-style: bold;
    }
    
    #info-box {
        width: 70;
        height: auto;
        border: round cyan;
        padding: 1 2;
    }
    
    #input-box {
        width: 100%;
        dock: bottom;
        margin: 0;
        border: round cyan;
    }
    """
    
    BINDINGS = []
    
    # Animation state
    animation_frame = reactive(0)
    typing_forward = reactive(True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.welcome_text = "Welcome!"
        self.current_text = ""
        self.char_index = 0
        # Falling animation state
        self.columns = []
        self.frame = 0
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Static(self._get_cvli_title(), id="cvli-title")
        yield Static("[bold bright_cyan]W█[/bold bright_cyan]", id="welcome-animation")
        yield Static(self._get_info_box(), id="info-box")
        yield Input(placeholder="Type /enter to continue...", id="input-box")
    
    def on_mount(self) -> None:
        """Start animation when mounted"""
        # Initialize with first character
        self.char_index = 1
        self.current_text = "W"
        
        # Start typing animation only
        self.set_interval(0.15, self.update_animation)
        
        # Focus the input box
        self.query_one("#input-box", Input).focus()
    
    def update_falling(self) -> None:
        """Update falling ASCII background"""
        self.frame += 1
        width = self.size.width
        height = self.size.height
        
        if width == 0 or height == 0:
            return
        
        # Initialize columns
        if len(self.columns) != width:
            self.columns = []
            for _ in range(width):
                self.columns.append({
                    'chars': [],
                    'speed': random.randint(1, 2),
                    'delay': random.randint(0, 30)
                })
        
        # Update columns
        for col in self.columns:
            if col['delay'] > 0:
                col['delay'] -= 1
            else:
                if random.random() < 0.05:
                    char = random.choice(['.', ':', '+', '*', '#', '|', '-', '='])
                    col['chars'].append({'char': char, 'y': 0})
                
                for char_obj in col['chars'][:]:
                    char_obj['y'] += col['speed']
                    if char_obj['y'] >= height * 2:
                        col['chars'].remove(char_obj)
        
        self.refresh(layout=False)
    
    def update_animation(self) -> None:
        """Update the typing animation"""
        welcome_widget = self.query_one("#welcome-animation", Static)
        
        if self.typing_forward:
            # Typing forward
            if self.char_index < len(self.welcome_text):
                self.current_text = self.welcome_text[:self.char_index + 1]
                self.char_index += 1
            else:
                # Pause at full text, then start deleting
                self.typing_forward = False
                return
        else:
            # Typing backward (deleting)
            if self.char_index > 0:
                self.char_index -= 1
                self.current_text = self.welcome_text[:self.char_index]
            else:
                # Start typing forward again
                self.typing_forward = True
                return
        
        # Update the widget with cursor effect
        cursor = "█" if len(self.current_text) < len(self.welcome_text) or not self.typing_forward else ""
        # Use larger font style
        welcome_widget.update(f"[bold bright_cyan on default][u]{self.current_text}[/u]{cursor}[/bold bright_cyan on default]")
    
    def _get_cvli_title(self) -> str:
        """Return CVLI ASCII art title with gradient"""
        # CVLI with teal to magenta gradient + version number on the right
        return """[bright_cyan]  ██████╗[/bright_cyan] [cyan]██╗   ██╗[/cyan][#DD00DD]██╗     ██╗[/]  [dim white]v.0.0.1[/dim white]
[bright_cyan] ██╔════╝[/bright_cyan] [cyan]██║   ██║[/cyan][#DD00DD]██║     ██║[/]
[bright_cyan] ██║     [/bright_cyan] [cyan]██║   ██║[/cyan][magenta]██║     ██║[/magenta]
[cyan] ██║     [/cyan] [#DD00DD]╚██╗ ██╔╝[/][magenta]██║     ██║[/magenta]
[cyan] ╚██████╗[/cyan] [magenta] ╚████╔╝ [/magenta][bright_magenta]███████╗██║[/bright_magenta]
[magenta]  ╚═════╝[/magenta] [bright_magenta]  ╚═══╝  ╚══════╝╚═╝[/bright_magenta]"""
    
    def _get_info_box(self) -> str:
        """Return info box content"""
        return """[cyan]I am Ujjwal and this is my resume

[bold]Patch notes:[/bold]
  • Added ascii art to the project
  • Updated the project section to show the latest projects i have been working on
  • Added retro theme to the resume[/cyan]"""
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission"""
        if event.value.strip().lower() == "/enter":
            self.app.pop_screen()
        else:
            # Clear the input and show feedback
            input_widget = self.query_one("#input-box", Input)
            input_widget.value = ""
            input_widget.placeholder = "Invalid! Type /enter to continue..."
