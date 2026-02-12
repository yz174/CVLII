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
                link="github.com/yourname/tui-resume"
            )
            
            # Project 2
            yield ProjectCard(
                title="Cloud Infrastructure Orchestrator",
                description="Automated deployment pipeline for microservices architecture on AWS. Implements Infrastructure as Code using Terraform and manages container orchestration with Kubernetes.",
                tech_stack=["Terraform", "Kubernetes", "AWS", "Docker", "Python"],
                link="github.com/yourname/cloud-orchestrator"
            )
            
            # Project 3
            yield ProjectCard(
                title="Real-Time Analytics Dashboard",
                description="High-performance dashboard for processing and visualizing streaming data. Handles millions of events per second with sub-second latency using event-driven architecture.",
                tech_stack=["React", "Node.js", "Apache Kafka", "Redis", "PostgreSQL"],
                link="github.com/yourname/analytics-dashboard"
            )
            
            # Project 4
            yield ProjectCard(
                title="AI-Powered Code Review Bot",
                description="Automated code review system that uses machine learning to identify bugs, security vulnerabilities, and code quality issues. Integrates with GitHub PRs and provides actionable feedback.",
                tech_stack=["Python", "TensorFlow", "GitHub Actions", "FastAPI", "PostgreSQL"],
                link="github.com/yourname/code-review-bot"
            )
            
            # Project 5
            yield ProjectCard(
                title="Distributed Task Scheduler",
                description="Scalable task scheduling system with distributed execution, fault tolerance, and real-time monitoring. Handles complex job dependencies and provides RESTful API for task management.",
                tech_stack=["Go", "Redis", "RabbitMQ", "PostgreSQL", "Prometheus"],
                link="github.com/yourname/task-scheduler"
            )
    
    def on_mount(self) -> None:
        """Called when screen is mounted"""
        # Focus the first project card
        project_cards = self.query(ProjectCard)
        if project_cards:
            project_cards.first().focus()
