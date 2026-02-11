"""Falling ASCII art animation for backgrounds"""

import random
from textual.widget import Widget
from rich.text import Text


class FallingASCII(Widget):
    """Animated falling ASCII characters background"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns = []
        self.frame = 0
        
    def on_mount(self) -> None:
        """Initialize columns when mounted"""
        # Update at 10 FPS for smooth animation
        self.set_interval(0.1, self.update_frame)
        
    def update_frame(self) -> None:
        """Update animation frame"""
        self.frame += 1
        
        # Initialize columns if needed
        width = self.size.width
        height = self.size.height
        
        if width == 0 or height == 0:
            return
            
        # Initialize columns on first frame or resize
        if len(self.columns) != width:
            self.columns = []
            for _ in range(width):
                self.columns.append({
                    'chars': [],
                    'speed': random.randint(1, 3),
                    'delay': random.randint(0, 20)
                })
        
        # Update each column
        for col in self.columns:
            # Check if column should drop a new character
            if col['delay'] > 0:
                col['delay'] -= 1
            else:
                # Add new character at random intervals
                if random.random() < 0.1:  # 10% chance each frame
                    char = random.choice(['.', ':', '+', '*', '#', '|', '-', '='])
                    col['chars'].append({'char': char, 'y': 0, 'age': 0})
                
                # Move characters down and age them
                for char_obj in col['chars'][:]:
                    char_obj['y'] += col['speed']
                    char_obj['age'] += 1
                    
                    # Remove characters that have fallen off screen
                    if char_obj['y'] >= height * 3:
                        col['chars'].remove(char_obj)
        
        self.refresh()
    
    def render(self) -> Text:
        """Render the falling ASCII art"""
        width = self.size.width
        height = self.size.height
        
        if width == 0 or height == 0:
            return Text("")
        
        # Create empty grid
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Place characters from each column
        for x, col in enumerate(self.columns):
            if x >= width:
                break
                
            for char_obj in col['chars']:
                y = int(char_obj['y'])
                if 0 <= y < height:
                    grid[y][x] = char_obj['char']
        
        # Convert grid to Rich Text with styling
        text = Text()
        for y, row in enumerate(grid):
            line = ''.join(row)
            # Vary the green shades for depth effect
            if y < height // 3:
                style = "dim green"
            elif y < 2 * height // 3:
                style = "green"
            else:
                style = "bright_green"
            text.append(line + "\n", style=style)
        
        return text
