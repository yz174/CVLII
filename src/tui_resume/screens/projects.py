"""Projects screen displaying portfolio projects"""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from textual.binding import Binding
from ..widgets import ProjectCard, MatrixText


class ProjectsScreen(Screen):
    """Screen displaying project portfolio"""
    
    BINDINGS = [
        Binding("up", "focus_previous", "Previous Project", show=False),
        Binding("down", "focus_next", "Next Project", show=False),
    ]
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with VerticalScroll(id="projects-container"):
            yield Static("[bold cyan]MY PROJECTS[/bold cyan]\n", classes="section-title")
            yield Static("Here are some of the projects I've worked on:\n")
            
            # Project 1
            yield ProjectCard(
                title="SSH TUI Resume",
                description="An interactive terminal-based resume accessible via SSH. Built with Python, Textual framework, and AsyncSSH. Features animated backgrounds, mini-games, and smooth transitions.",
                tech_stack=["Python", "Textual", "AsyncSSH", "Docker", "AWS EC2"],
                link="https://github.com/yz174/CVLII"
            )
            
            # Project 2
            yield ProjectCard(
                title="Email Sync System",
                description="An AI-powered email synchronization system that provides real-time IMAP email syncing, intelligent categorization, searchable storage, and AI-powered reply suggestions.",
                tech_stack=["Typescript", "Node.js","React","Express", "RAG", "Docker", "BullMQ", "Redis", "Elasticsearch", "Gemini API", ],
                link="https://github.com/yz174/email-sync-system"
            )
            
            # Project 3
            yield ProjectCard(
                title="FreshXpress - A farmer's app",
                description="A React Native mobile application built with Expo that provides farmers with essential tools for crop management and leaf disease detection using machine learning.",
                tech_stack=["React Native", "Expo SDK 51", "TypeScript", "React Context API", "Supabase", "Weather API", " SMS Gateway", "MobileNetV2", "CUDA"],
                link="https://github.com/yz174/farmer-management-system"
            )
            
            # Project 4
            yield ProjectCard(
                title="Malware Detection and Analysis using Machine Learning",
                description="Malware Detection and Analysis using Machine Learning WebApp is a robust tool designed to provide users with an intuitive interface for analyzing and detecting malware in various file formats.",
                tech_stack=["Flask", "VirusTotalAPI", "Python", "requests"],
                link="https://github.com/yz174/Malware-Detector"
            )
            
            # Project 5
            yield ProjectCard(
                title="Link Saver & Auto Summary App",
                description="A web application for saving bookmarks with automatic summary generation using Jina AI.",
                tech_stack=["React", "Node.js", "Express", "Supabase", "JWT", "Jina AI"],
                link="https://github.com/yz174/MetaMark"
            )
    
    def on_mount(self) -> None:
        """Called when screen is mounted"""
        # Focus the first project card
        project_cards = self.query(ProjectCard)
        if project_cards:
            project_cards.first().focus()
