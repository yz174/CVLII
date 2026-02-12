"""Project card widget for displaying project information"""

import webbrowser
from textual.widget import Widget
from textual.containers import Container
from textual.widgets import Static, Label
from textual.message import Message
from rich.text import Text
from rich.panel import Panel


class ProjectCard(Widget):
    """Card widget for displaying a single project"""
    
    can_focus = True
    
    DEFAULT_CSS = """
    ProjectCard {
        width: 100%;
        height: auto;
        margin: 1 0;
        padding: 1 2;
        border: heavy $primary;
        background: $panel;
    }
    
    ProjectCard:hover {
        border: heavy $success;
    }
    
    ProjectCard:focus {
        border: heavy $accent;
        background: $surface;
    }
    
    ProjectCard .project-title {
        text-style: bold;
        color: $accent;
    }
    
    ProjectCard .project-description {
        color: $text;
    }
    
    ProjectCard .project-tech {
        color: $success;
        text-style: italic;
    }
    
    ProjectCard .project-link {
        color: $warning;
    }
    """
    
    def __init__(
        self,
        title: str,
        description: str,
        tech_stack: list[str],
        link: str = "",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.title = title
        self.description = description
        self.tech_stack = tech_stack
        self.link = link
    
    async def on_key(self, event) -> None:
        """Handle key press events"""
        if event.key == "enter" and self.link:
            # Open the GitHub link in default browser
            full_link = self.link if self.link.startswith("http") else f"https://{self.link}"
            webbrowser.open(full_link)
        elif event.key == "down":
            # Move to next project card
            event.stop()
            event.prevent_default()
            
            # Get all project cards
            project_cards = self.screen.query(ProjectCard)
            current_index = list(project_cards).index(self)
            
            # Only move if not on the last project
            if current_index < len(project_cards) - 1:
                project_cards[current_index + 1].focus()
                project_cards[current_index + 1].scroll_visible()
        elif event.key == "up":
            # Move to previous project card
            event.stop()
            event.prevent_default()
            
            # Get all project cards
            project_cards = self.screen.query(ProjectCard)
            current_index = list(project_cards).index(self)
            
            # Only move if not on the first project
            if current_index > 0:
                project_cards[current_index - 1].focus()
                project_cards[current_index - 1].scroll_visible()
    
    def render(self) -> Text:
        """Render the project card"""
        text = Text()
        
        # Title
        text.append(f"📦 {self.title}\n", style="bold cyan")
        text.append("\n")
        
        # Description
        text.append(f"{self.description}\n", style="white")
        text.append("\n")
        
        # Tech Stack
        text.append("Tech Stack: ", style="dim")
        for i, tech in enumerate(self.tech_stack):
            if i > 0:
                text.append(" • ", style="dim")
            text.append(tech, style="green")
        text.append("\n")
        
        # Link (if provided)
        if self.link:
            text.append("\n")
            text.append(f"🔗 {self.link}", style="yellow underline")
        
        return text
