"""Generative ASCII background using OpenSimplex noise"""

import time
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from opensimplex import OpenSimplex


class GenerativeBackground(Widget):
    """Animated ASCII art background using noise generation"""
    
    # ASCII gradient from dark to light
    ASCII_GRADIENT = " .:-=+*#%@"
    
    # Animation state
    time_offset: reactive[float] = reactive(0.0)
    
    def __init__(self, *args, animated: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize noise generator with random seed
        self.noise = OpenSimplex(seed=int(time.time()))
        self.frame_count = 0
        self.animated = animated
    
    def on_mount(self) -> None:
        """Start animation when widget is mounted"""
        # Update at 2 FPS to reduce CPU usage (only if animated)
        if self.animated:
            self.set_interval(1/2, self.update_frame)
        else:
            # Static mode - render once
            self.refresh()
    
    def update_frame(self) -> None:
        """Update animation frame"""
        self.frame_count += 1
        self.time_offset = self.frame_count * 0.1
        self.refresh()
    
    def render(self) -> Text:
        """Render the generative ASCII art"""
        # Get terminal dimensions
        width = self.size.width
        height = self.size.height
        
        if width == 0 or height == 0:
            return Text("")
        
        lines = []
        # Sample every 2nd character and line for better performance
        sample_rate = 2
        
        for y in range(0, height, sample_rate):
            line = ""
            for x in range(0, width, sample_rate):
                # Generate noise value based on position and time
                noise_value = self.noise.noise3(
                    x * 0.15,
                    y * 0.15,
                    self.time_offset
                )
                
                # Map noise (-1 to 1) to ASCII gradient (0 to len-1)
                index = int((noise_value + 1) * 0.5 * (len(self.ASCII_GRADIENT) - 1))
                index = max(0, min(len(self.ASCII_GRADIENT) - 1, index))
                
                # Duplicate character to fill sample gap
                line += self.ASCII_GRADIENT[index] * sample_rate
            
            # Duplicate line to fill sample gap
            for _ in range(sample_rate):
                lines.append(line)
        
        # Create Rich text with gradient coloring
        text = Text()
        for i, line in enumerate(lines):
            # Add color gradient effect (green shades)
            if i < len(lines) // 3:
                style = "bright_green"
            elif i < 2 * len(lines) // 3:
                style = "green"
            else:
                style = "dark_green"
            
            text.append(line + "\n", style=style)
        
        # Overlay centered title text
        if height > 10:
            title_lines = self._get_title_overlay()
            overlay_start = (height - len(title_lines)) // 2
            
            # Create overlay text
            overlay_text = Text()
            current_line = 0
            
            for line in text.plain.split("\n"):
                if overlay_start <= current_line < overlay_start + len(title_lines):
                    # Replace with title line
                    title_line = title_lines[current_line - overlay_start]
                    padding = (width - len(title_line)) // 2
                    overlay_text.append(" " * padding + title_line + "\n", style="bold cyan")
                else:
                    # Keep background line
                    if current_line < len(lines) // 3:
                        style = "bright_green"
                    elif current_line < 2 * len(lines) // 3:
                        style = "green"
                    else:
                        style = "dark_green"
                    overlay_text.append(line + "\n", style=style)
                
                current_line += 1
            
            return overlay_text
        
        return text
    
    def _get_title_overlay(self) -> list[str]:
        """Get title text to overlay on background"""
        return [
            "╔═══════════════════════════════════╗",
            "║                                   ║",
            "║        YOUR NAME HERE             ║",
            "║                                   ║",
            "║    Full Stack Developer           ║",
            "║    Cloud Architecture Specialist  ║",
            "║                                   ║",
            "║   Press ← → to navigate           ║",
            "║   Press ENTER to select           ║",
            "║                                   ║",
            "╚═══════════════════════════════════╝",
        ]
