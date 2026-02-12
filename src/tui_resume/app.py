"""Main TUI Resume application built with Textual framework"""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container, VerticalScroll, Vertical, Grid
from textual.message import Message

from .widgets import NavBar, GenerativeBackground, ProjectCard, HomeGreeting
from .screens import WelcomeScreen


class ResumeApp(App):
    """Interactive TUI Resume Application"""
    
    # Load CSS styling
    CSS_PATH = Path(__file__).parent / "css" / "app.tcss"
    
    # Keybindings
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Dark Mode"),
        ("left", "nav_left", "Previous"),
        ("right", "nav_right", "Next"),
        ("enter", "nav_select", "Select"),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_screen_id = "home"
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header(show_clock=True)
        yield NavBar()
        yield Container(id="content-container")
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts"""
        self.title = "SSH Resume Portfolio"
        self.sub_title = "Navigate with Arrow Keys"
        
        # Load initial content (home screen with background)
        self._load_content("home")
        
        # Set focus to navbar for keyboard navigation
        self.call_after_refresh(self._focus_navbar)
        
        # Push welcome screen as modal overlay
        self.push_screen(WelcomeScreen())
    
    def _focus_navbar(self) -> None:
        """Set focus to navbar after render"""
        try:
            navbar = self.query_one(NavBar)
            navbar.focus()
        except:
            pass
    
    def _load_content(self, screen_id: str) -> None:
        """Load content into the container"""
        container = self.query_one("#content-container")
        
        # Remove existing content
        container.remove_children()
        
        # Mount new content based on screen
        if screen_id == "home":
            container.mount(HomeGreeting())
        elif screen_id == "projects":
            self._load_projects(container)
        elif screen_id == "about":
            self._load_about(container)
    
    def _load_projects(self, container: Container) -> None:
        """Load projects content"""
        scroll = VerticalScroll(id="projects-scroll")
        container.mount(scroll)
        
        scroll.mount(Static("[bold cyan]MY PROJECTS[/bold cyan]\n", classes="section-title"))
        scroll.mount(Static("Here are some of the projects I've worked on:\n"))
        
        # Create grid container for projects
        grid = Grid(id="projects-container")
        scroll.mount(grid)
        
        grid.mount(ProjectCard(
            title="SSH TUI Resume",
            description="An interactive terminal-based resume accessible via SSH. Built with Python, Textual framework, and AsyncSSH. Features animated backgrounds, mini-games, and smooth transitions.",
            tech_stack=["Python", "Textual", "AsyncSSH", "Docker", "AWS EC2"],
            link="https://github.com/yz174/CVLII"
        ))
        
        grid.mount(ProjectCard(
            title="Email Sync System",
            description="An AI-powered email synchronization system that provides real-time IMAP email syncing, intelligent categorization, searchable storage, and AI-powered reply suggestions.",
            tech_stack=["Typescript", "Node.js", "React", "Express", "RAG", "Docker", "BullMQ", "Redis", "Elasticsearch", "Gemini API"],
            link="https://github.com/yz174/email-sync-system"
        ))
        
        grid.mount(ProjectCard(
            title="FreshXpress - A farmer's app",
            description="A React Native mobile application built with Expo that provides farmers with essential tools for crop management and leaf disease detection using machine learning.",
            tech_stack=["React Native", "Expo SDK 51", "TypeScript", "React Context API", "Supabase", "Weather API", "SMS Gateway", "MobileNetV2", "CUDA"],
            link="https://github.com/yz174/farmer-management-system"
        ))
        
        grid.mount(ProjectCard(
            title="Malware Detection and Analysis using Machine Learning",
            description="Malware Detection and Analysis using Machine Learning WebApp is a robust tool designed to provide users with an intuitive interface for analyzing and detecting malware in various file formats.",
            tech_stack=["Flask", "VirusTotalAPI", "Python", "requests"],
            link="https://github.com/yz174/Malware-Detector"
        ))
        
        grid.mount(ProjectCard(
            title="Link Saver & Auto Summary App",
            description="A web application for saving bookmarks with automatic summary generation using Jina AI.",
            tech_stack=["React", "Node.js", "Express", "Supabase", "JWT", "Jina AI"],
            link="https://github.com/yz174/MetaMark"
        ))
        
        # Focus first project card after mounting
        self.call_after_refresh(self._focus_first_project)
    
    def _load_about(self, container: Container) -> None:
        """Load about content"""
        bio_section = Vertical(id="bio-section")
        container.mount(bio_section)
        
        bio_section.mount(Static("[bold cyan]ABOUT ME[/bold cyan]\n", classes="section-title"))
        bio_section.mount(Static("""
Junior full-stack developer with expertise in Full Stack 
Web and Mobile development. Passionate about breaking things 
and building developer tools and automation solutions.

Experience:
  • 1+ years in software development
  • Cloud architecture on AWS
  • Python, TypeScript, Javascript
  • DevOps and CI/CD pipelines

Education:
  • B.tech in Computer Science from Bennett University (2023-2027) • 8.33 CGPA 
  • Multiple cloud and AI certifications
        """))
        
        bio_section.mount(Static("\n[bold cyan]SKILLS[/bold cyan]\n"))
        bio_section.mount(Static("""
Programming:
  [#E0E0E0]Python • C++ • Javascript • TypeScript • TailwindCSS[/#E0E0E0]

Cloud & DevOps:
  [#5F87AF]AWS • Docker • CI/CD[/#5F87AF]

Frameworks:
  [#87AF87]React Native • Expo • React • Next.js • Node.js • FastAPI • Express.js • FastAPI • Flask • Textual[/#87AF87]

Databases:
  [#AF875F]PostgreSQL • MySQL • MongoDB • Redis[/#AF875F]

Other:
  [#808080]N8N • Make[/#808080]   
        """))
    
    def on_nav_bar_tab_selected(self, message: "NavBar.TabSelected") -> None:
        """Handle navigation tab selection"""
        screen_id = message.screen_id
        
        if screen_id != self.current_screen_id:
            self.current_screen_id = screen_id
            self._load_content(screen_id)
    
    def action_toggle_dark(self) -> None:
        """Toggle dark mode"""
        self.dark = not self.dark
    
    def action_nav_left(self) -> None:
        """Navigate to previous tab"""
        navbar = self.query_one(NavBar)
        navbar.active_index = (navbar.active_index - 1) % len(NavBar.TABS)
        # Immediately load the content
        _, screen_id = NavBar.TABS[navbar.active_index]
        if screen_id != self.current_screen_id:
            self.current_screen_id = screen_id
            self._load_content(screen_id)
    
    def action_nav_right(self) -> None:
        """Navigate to next tab"""
        navbar = self.query_one(NavBar)
        navbar.active_index = (navbar.active_index + 1) % len(NavBar.TABS)
        # Immediately load the content
        _, screen_id = NavBar.TABS[navbar.active_index]
        if screen_id != self.current_screen_id:
            self.current_screen_id = screen_id
            self._load_content(screen_id)
    
    def action_nav_select(self) -> None:
        """Select current tab"""
        navbar = self.query_one(NavBar)
        _, screen_id = NavBar.TABS[navbar.active_index]
        
        if screen_id != self.current_screen_id:
            self.current_screen_id = screen_id
            self._load_content(screen_id)
    
    def _focus_first_project(self) -> None:
        """Focus the first project card"""
        try:
            project_cards = self.query(ProjectCard)
            if project_cards:
                project_cards.first().focus()
        except:
            pass


def main():
    """Entry point for running the app directly"""
    app = ResumeApp()
    app.run()


if __name__ == "__main__":
    main()
