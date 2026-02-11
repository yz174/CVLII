"""Security Clearance mini-game screen"""

import random
from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static
from textual.reactive import reactive


class GameScreen(Screen):
    """Interactive 'Packet Sniffer' mini-game to unlock contact info"""
    
    # Game state
    player_x: reactive[int] = reactive(5)
    player_y: reactive[int] = reactive(5)
    targets_collected: reactive[int] = reactive(0)
    
    # Grid dimensions
    GRID_WIDTH = 20
    GRID_HEIGHT = 12
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate target positions
        self.targets = self._generate_targets()
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Container(id="game-container"):
            with Vertical(id="game-board"):
                yield Static(
                    "[bold yellow]SECURITY CLEARANCE CHALLENGE[/bold yellow]\n",
                    id="game-instructions"
                )
                yield Static(
                    "Collect all 3 data packets [*] to unlock contact information!\n"
                    "Use Arrow Keys to move your agent [@]",
                    id="game-instructions"
                )
                yield Static("", id="game-display")
                yield Static("", id="game-status")
    
    def _generate_targets(self) -> list[tuple[int, int]]:
        """Generate random target positions"""
        targets = []
        while len(targets) < 3:
            x = random.randint(1, self.GRID_WIDTH - 2)
            y = random.randint(1, self.GRID_HEIGHT - 2)
            # Don't spawn on player start position
            if (x, y) != (5, 5) and (x, y) not in targets:
                targets.append((x, y))
        return targets
    
    def on_mount(self) -> None:
        """Called when screen is mounted"""
        self.update_display()
    
    def on_key(self, event) -> None:
        """Handle arrow key movement"""
        moved = False
        
        if event.key == "up" and self.player_y > 0:
            self.player_y -= 1
            moved = True
        elif event.key == "down" and self.player_y < self.GRID_HEIGHT - 1:
            self.player_y += 1
            moved = True
        elif event.key == "left" and self.player_x > 0:
            self.player_x -= 1
            moved = True
        elif event.key == "right" and self.player_x < self.GRID_WIDTH - 1:
            self.player_x += 1
            moved = True
        elif event.key == "escape":
            self.app.pop_screen()
            return
        
        if moved:
            self._check_collection()
            self.update_display()
            event.prevent_default()
    
    def _check_collection(self) -> None:
        """Check if player collected a target"""
        player_pos = (self.player_x, self.player_y)
        if player_pos in self.targets:
            self.targets.remove(player_pos)
            self.targets_collected += 1
            
            # Check win condition
            if self.targets_collected == 3:
                self._win_game()
    
    def _win_game(self) -> None:
        """Handle game win - unlock contact screen"""
        from .contact import ContactScreen
        self.app.pop_screen()  # Remove game screen
        self.app.push_screen(ContactScreen())
    
    def update_display(self) -> None:
        """Update the game board display"""
        # Build grid
        grid_lines = []
        
        # Top border
        grid_lines.append("╔" + "═" * (self.GRID_WIDTH * 2) + "╗")
        
        # Grid content
        for y in range(self.GRID_HEIGHT):
            line = "║"
            for x in range(self.GRID_WIDTH):
                if (x, y) == (self.player_x, self.player_y):
                    line += " @"  # Player
                elif (x, y) in self.targets:
                    line += " *"  # Target
                else:
                    line += " ."  # Empty space
            line += " ║"
            grid_lines.append(line)
        
        # Bottom border
        grid_lines.append("╚" + "═" * (self.GRID_WIDTH * 2) + "╝")
        
        # Update display widget
        display_widget = self.query_one("#game-display", Static)
        display_widget.update("\n".join(grid_lines))
        
        # Update status
        status_widget = self.query_one("#game-status", Static)
        status_text = f"\n[bold]Packets Collected: {self.targets_collected}/3[/bold]"
        
        if self.targets_collected == 3:
            status_text += "\n[bold green]ACCESS GRANTED! 🎉[/bold green]"
        
        status_widget.update(status_text)
