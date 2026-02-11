"""Contact information screen (unlocked after game completion)"""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static


class ContactScreen(Screen):
    """Screen displaying contact information after clearance is granted"""
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Container(id="contact-container"):
            with Vertical():
                yield Static(
                    "[bold green]╔═══════════════════════════════════════╗[/bold green]",
                    id="contact-title"
                )
                yield Static(
                    "[bold green]║   🔓 SECURITY CLEARANCE GRANTED 🔓   ║[/bold green]",
                    id="contact-title"
                )
                yield Static(
                    "[bold green]╚═══════════════════════════════════════╝[/bold green]\n",
                    id="contact-title"
                )
                
                yield Static(self._get_contact_details(), id="contact-details")
                
                yield Static(
                    "\n[dim]Press ESC to return | Press Q to quit[/dim]",
                    classes="center-text"
                )
    
    def _get_contact_details(self) -> str:
        """Get formatted contact information"""
        return """
[bold cyan]CONTACT INFORMATION[/bold cyan]

[bold yellow]Email:[/bold yellow]
  📧 your.email@example.com

[bold yellow]LinkedIn:[/bold yellow]
  🔗 linkedin.com/in/yourprofile

[bold yellow]GitHub:[/bold yellow]
  💻 github.com/yourusername

[bold yellow]Website:[/bold yellow]
  🌐 yourwebsite.com

[bold yellow]Location:[/bold yellow]
  📍 San Francisco, CA | Remote


[dim italic]Feel free to reach out for opportunities, collaborations, 
or just to chat about technology![/dim italic]

[bold green]Thank you for playing! 🚀[/bold green]
        """.strip()
    
    def on_key(self, event) -> None:
        """Handle keyboard input"""
        if event.key == "escape":
            self.app.pop_screen()
            event.prevent_default()
    
    def on_mount(self) -> None:
        """Called when screen is mounted"""
        pass
