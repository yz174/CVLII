"""Custom navigation bar widget with tab-based navigation"""

from textual.widget import Widget
from textual.message import Message
from textual.reactive import reactive
from rich.text import Text


class NavBar(Widget):
    """Custom navigation bar with keyboard and mouse support"""
    
    # Enable focus to receive keyboard events
    can_focus = True
    
    # Navigation tabs (label, screen_id)
    TABS = [
        ("HOME", "home"),
        ("PROJECTS", "projects"),
        ("ABOUT", "about"),
    ]
    
    # Reactive property for active tab index
    active_index: reactive[int] = reactive(0)
    
    class TabSelected(Message):
        """Message sent when a tab is selected"""
        
        def __init__(self, screen_id: str) -> None:
            self.screen_id = screen_id
            super().__init__()
    
    def render(self) -> Text:
        """Render the navigation bar"""
        text = Text()
        
        # Add spacing before tabs
        text.append("  ")
        
        for idx, (label, _) in enumerate(self.TABS):
            # Add separator between tabs
            if idx > 0:
                text.append("      ", style="dim")
            
            # Style based on active state
            if idx == self.active_index:
                # Active tab - highlighted
                text.append(f"[ {label} ]", style="bold green on dark_green")
            else:
                # Inactive tab - muted
                text.append(f"  {label}  ", style="dim cyan")
        
        return text
    
    def on_key(self, event) -> None:
        """Handle keyboard navigation"""
        # Only handle enter key - arrow keys are handled at app level
        if event.key == "enter":
            # Select current tab
            self._select_current_tab()
            event.prevent_default()
    
    def on_click(self, event) -> None:
        """Handle mouse clicks on tabs"""
        # Calculate which tab was clicked based on position
        x = event.x
        
        # Approximate tab positions (adjust based on label lengths)
        tab_positions = [0, 20, 45]  # Rough character positions
        
        for idx, pos in enumerate(tab_positions):
            if x >= pos and (idx == len(tab_positions) - 1 or x < tab_positions[idx + 1]):
                self.active_index = idx
                self._select_current_tab()
                break
    
    def _select_current_tab(self) -> None:
        """Select the currently highlighted tab"""
        _, screen_id = self.TABS[self.active_index]
        self.post_message(self.TabSelected(screen_id))
    
    def watch_active_index(self, old_value: int, new_value: int) -> None:
        """Called when active_index changes - triggers re-render"""
        self.refresh()
