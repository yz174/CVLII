"""About screen with bio and skills"""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button
from rich.text import Text


class AboutScreen(Screen):
    """Screen displaying bio, skills, and contact unlock button"""
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        with Container(id="about-container"):
            # Left column - Bio
            with Vertical(id="bio-section"):
                yield Static("[bold cyan]ABOUT ME[/bold cyan]\n", classes="section-title")
                yield Static(self._get_bio_text())
                yield Static("\n")
                yield Button("🎮 Unlock Contact Info", id="unlock-btn", variant="success")
            
            # Right column - Skills
            with Vertical(id="skills-section"):
                yield Static("[bold cyan]SKILLS & EXPERTISE[/bold cyan]\n", classes="section-title")
                yield Static(self._get_skills_text())
    
    def _get_bio_text(self) -> str:
        """Get bio/professional summary"""
        return """
Hello! I'm a passionate Full Stack Developer with a focus on cloud-native 
architectures and developer experience.

With over 5 years of experience building scalable systems, I specialize in:
• Designing and implementing microservices architectures
• Cloud infrastructure automation (AWS, Azure, GCP)
• Building developer tools and internal platforms
• Performance optimization and system reliability

I'm particularly interested in projects that push the boundaries of what's 
possible with modern infrastructure and create delightful experiences for 
developers and end-users alike.

When I'm not coding, you can find me contributing to open source projects,
writing technical blog posts, or exploring the latest advancements in 
cloud computing and DevOps practices.

Want to get in touch? Complete the Security Clearance challenge below!
        """.strip()
    
    def _get_skills_text(self) -> str:
        """Get skills breakdown"""
        return """
[bold green]Languages[/bold green]
  • Python, JavaScript/TypeScript
  • Go, Rust, Java
  • SQL, Bash

[bold green]Frameworks & Libraries[/bold green]
  • React, Next.js, Vue.js
  • FastAPI, Django, Flask
  • Node.js, Express

[bold green]Cloud & Infrastructure[/bold green]
  • AWS (EC2, Lambda, S3, RDS)
  • Docker, Kubernetes
  • Terraform, Ansible
  • CI/CD (GitHub Actions, Jenkins)

[bold green]Databases[/bold green]
  • PostgreSQL, MySQL
  • MongoDB, Redis
  • Elasticsearch

[bold green]Tools & Practices[/bold green]
  • Git, GitHub
  • Agile/Scrum
  • TDD, Code Review
  • System Design
        """.strip()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press to launch game"""
        if event.button.id == "unlock-btn":
            from .game import GameScreen
            self.app.push_screen(GameScreen())
    
    def on_mount(self) -> None:
        """Called when screen is mounted"""
        pass
