"""Matrix-style text decode animation widget"""

import random
import string
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text


class MatrixText(Widget):
    """Text widget with Matrix-style decode animation effect"""
    
    # Reactive properties
    current_text: reactive[str] = reactive("")
    is_decoding: reactive[bool] = reactive(False)
    
    def __init__(self, target_text: str = "", decode_duration: float = 0.3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_text = target_text
        self.decode_duration = decode_duration
        self.decode_progress = 0.0
        self.scrambled_chars = []
    
    def on_mount(self) -> None:
        """Start decode animation when mounted"""
        if self.target_text:
            self.start_decode()
    
    def start_decode(self, text: str = None) -> None:
        """Start the decode animation"""
        if text:
            self.target_text = text
        
        # Initialize with scrambled text
        self.scrambled_chars = [
            random.choice(string.ascii_uppercase + string.digits + "!@#$%^&*")
            if c != " " and c != "\n" else c
            for c in self.target_text
        ]
        
        self.current_text = "".join(self.scrambled_chars)
        self.is_decoding = True
        self.decode_progress = 0.0
        
        # Set up decode timer (10 frames over duration)
        self.set_interval(self.decode_duration / 10, self._decode_step, repeat=10)
    
    def _decode_step(self) -> None:
        """Perform one step of the decode animation"""
        if not self.is_decoding:
            return
        
        self.decode_progress += 0.1
        
        # Progressively reveal correct characters
        for i, target_char in enumerate(self.target_text):
            if random.random() < self.decode_progress:
                self.scrambled_chars[i] = target_char
            elif target_char not in (" ", "\n"):
                # Still scrambling
                self.scrambled_chars[i] = random.choice(
                    string.ascii_uppercase + string.digits + "!@#$%^&*"
                )
        
        self.current_text = "".join(self.scrambled_chars)
        
        # Check if decode is complete
        if self.decode_progress >= 1.0:
            self.current_text = self.target_text
            self.is_decoding = False
        
        self.refresh()
    
    def render(self) -> Text:
        """Render the current text state"""
        if self.is_decoding:
            return Text(self.current_text, style="bold yellow")
        else:
            return Text(self.current_text, style="white")
    
    def watch_current_text(self, old_text: str, new_text: str) -> None:
        """React to text changes"""
        self.refresh()
