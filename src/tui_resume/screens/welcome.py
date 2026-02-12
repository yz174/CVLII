"""Welcome screen with CVLI title and tips"""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Static, Input


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
        margin-bottom: 4;
        padding-left: 4;
        padding-right: 4;
    }
    
    #welcome-animation {
        width: auto;
        height: auto;
        margin-bottom: 2;
        text-align: left;
        content-align: left top;
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
        background: $background;
    }
    """
    
    BINDINGS = []
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Static(self._get_cvli_title(), id="cvli-title")
        yield Static(self._get_tips_text(), id="welcome-animation")
        yield Static(self._get_info_box(), id="info-box")
        yield Input(placeholder="Type /enter to continue...", id="input-box")
    
    def on_mount(self) -> None:
        """Focus input box when mounted"""
        # Focus the input box
        self.query_one("#input-box", Input).focus()
    
    def _get_cvli_title(self) -> str:
        """Return CVLI ASCII art title with gradient"""
        # CVLI with teal to magenta gradient + version number adjacent to bottom
        return """[bright_cyan]  ██████╗[/bright_cyan] [cyan]██╗   ██╗[/cyan][#DD00DD]██╗     ██╗[/]
[bright_cyan] ██╔════╝[/bright_cyan] [cyan]██║   ██║[/cyan][#DD00DD]██║     ██║[/]
[bright_cyan] ██║     [/bright_cyan] [cyan]██║   ██║[/cyan][magenta]██║     ██║[/magenta]
[cyan] ██║     [/cyan] [#DD00DD]╚██╗ ██╔╝[/][magenta]██║     ██║[/magenta]
[cyan] ╚██████╗[/cyan] [magenta] ╚████╔╝ [/magenta][bright_magenta]███████╗██║[/bright_magenta]
          [magenta]  ╚═════╝[/magenta] [bright_magenta]  ╚═══╝  ╚══════╝╚═╝[/bright_magenta]   [dim white]v.1.0.0[/dim white]"""
    
    def _get_tips_text(self) -> str:
        """Return [bold]tips to get started[/bold]"""; return"""[cyan]Tips to get started:
   -  this project is a reflection of me and my work
   -  let me know your thoughts @ujjwalkrish082@gmail.com[/cyan]"""
    
    def _get_info_box(self) -> str:
        """Return info box content"""
        return """[cyan]
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
