"""Home greeting widget with ASCII art and typing animation"""

from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult


class HomeGreeting(Widget):
    """Widget displaying ASCII art and animated greeting"""
    
    DEFAULT_CSS = """
    HomeGreeting {
        width: 100%;
        height: 100%;
        align: left top;
        padding: 2 6;
    }
    
    #home-main-container {
        width: 100%;
        height: 100%;
        layout: horizontal;
    }
    
    #left-section {
        width: 60%;
        height: 100%;
        align: left top;
    }
    
    #right-section {
        width: 40%;
        height: 100%;
        align: center top;
        padding-top: 2;
        overflow-y: auto;
    }
    
    #home-container {
        width: auto;
        height: auto;
        align: left top;
    }
    
    #ascii-art {
        width: auto;
        height: auto;
        text-align: left;
        margin-bottom: 4;
    }
    
    #greeting-text {
        width: auto;
        height: 3;
        text-align: left;
        margin-bottom: 0;
    }
    
    #welcome-text {
        width: 90;
        height: auto;
        text-align: left;
    }
    
    #side-ascii-art {
        width: 100%;
        height: auto;
        text-align: left;
        overflow: auto;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.full_text = "Hi Grok!"
        self.current_index = 0
        self.typing_forward = True
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Horizontal(id="home-main-container"):
            # Left section with greeting and text
            with Vertical(id="left-section"):
                with Vertical(id="home-container"):
                    yield Static(self._get_ascii_art(), id="ascii-art")
                    yield Static("", id="greeting-text")
                    yield Static("[bold cyan]Welcome to my World.."
                                 
                    "I write the code you dont see so the things you do see actually work. I specialize in elegant solutions to problems that probably shouldnt have existed in the first place.[/bold cyan]", id="welcome-text")
            
            # Right section with decorative ASCII art
            with Vertical(id="right-section"):
                yield Static(self._get_side_ascii_art(), id="side-ascii-art")
    
    def on_mount(self) -> None:
        """Called when widget is mounted"""
        # Start typing animation
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
    
    def _get_side_ascii_art(self) -> str:
        """Return decorative ASCII art for right side"""
        return """[green]                                                                            
                                                                            
                         %%%%%##%%%%%     %%%%%%%@%                         
                      @%#************#% %%*********%%                       
                     @#****************%#************%%                     
                    @#**********#######*%*************#%                    
                  #%********%#***********#%**#%%%%%%%#*#@                   
                 @%*******%****************#%**********#%%                  
               %%****************************%*************%                
              %%******************************%#************#%              
             %#************#%#****####**%%#**#%%*****#%%######%%#           
            %#***********#%*#%#********#%#*#%**#%***#%#*#######%%@          
           %#***********####**############%@%#%**%*#*#%#####**##@           
          %#***************#%*-.:%*=@@%%@*...:%#%%**%@*%@@@#:*%#@           
         %%********************#%%%-%#.:%*....-####=#@@@@-.%-..+@           
        %#********************##**#%%@@@@:....+%%*%+#@%@@@@*:+%#%           
       %#***********************#@%#******#****#%**#**********%%            
      %%************************************#%*******%%%%***#%#%            
      %****************%##*****************%#**********%********%           
     %#****************#%%%#**********##%%**************#*******%%%         
     %***************##%#%%%##******##*************************#%#%         
    %#*****************%##%%####%%%%##************************%##%#         
    %#******************#%#####%%##########%%%%%%%%########%%##%%           
    @***********************#%#######%%%%%%%#################%##@           
   @%**************************#%%#############################%*           
   %#******************************#%%#######################%@*            
   %***************************************#####%%%%########**%#            
   %***************************************************#%#%#*%%             
   %************************************************#%******#@              
  %%**********************************************#%**********#%%           
  %%****************************************##**%#**%**%#%%%*##**#@         
   %****************************************#%***%%%%%**%%@%#******%@       
   %%*****************************************%#***###%%%#**********#@      
    %#*****************************************##***%%%******%#*******%     
     %%****************************************#%****#%****##****#%****%    
       @@##************************************#%******#%###***#%***%#**%   
           %%%##*****************************#%@%%#********%%%%%**#%****%%  
                @%@@%%%#%%%%%%%%%@@@@@%%%%%%      %%%**********###****#%%   
                                                     @%%%%%%%####%%%@%      
                                                                            
                                                                            [/green]"""
