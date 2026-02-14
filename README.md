# CVLI - Interactive Terminal Portfolio

A Terminal User Interface (TUI) application serving as an interactive professional portfolio accessible via SSH from anywhere. Connect to your resume using any SSH client and explore your professional profile through an animated, game-like interface.

##  Features

- **SSH Accessible**: Connect from any device with `ssh your-server.com`
- **Cross-Platform Compatible**: Works on Windows, Linux, and macOS clients
- **Generative ASCII Art**: Dynamic animated background on the home screen
- **Security Clearance Game**: Interactive mini-game to unlock contact information
- **Matrix Transitions**: Smooth "decode" effects between screens
- **Tab Navigation**: Intuitive keyboard/mouse navigation between sections
- **Production Ready**: Dockerized with logging and error handling

##  Quick Start - Local Development

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Docker (optional, for containerized deployment)

### Installation

1. **Clone this repository**
   ```bash
   git clone <your-repo-url>
   cd tui_resume_python
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running Locally

**Option 1: Direct TUI (No SSH) - Quick Testing**
```bash
# Run TUI directly in your terminal
python -m src.tui_resume.app
```
Runs the Textual interface directly with full functionality. Good for testing and development.

**Option 2: With SSH Server - Local Testing**
```bash
# Generate SSH host key (first time only)
ssh-keygen -f host_key -N "" -t rsa

# Start the SSH server
python -m src.tui_resume.ssh_server

# In a new terminal, connect
ssh localhost -p 2222
```

**Option 3: Docker (Recommended)**
```bash
# Build and run in container
docker-compose up --build

# Connect from host machine
ssh localhost -p 2222
```

### Navigation

- **Arrow Keys / Tab**: Navigate between tabs and UI elements
- **Enter**: Select highlighted item
- **Q**: Quit application
- **D**: Toggle dark mode (where applicable)
- **Mouse**: Click tabs and buttons (if terminal supports it)

##  Architecture

### SSH Server Implementation

The application uses a sophisticated PTY-based architecture for SSH access:

```
SSH Client (Windows/Linux/macOS)
         ↓
AsyncSSH Server (Python asyncssh)
         ↓
PTY (Pseudo-Terminal) in Raw Mode
         ↓
Textual TUI Application
```

**Key Components:**

- **AsyncSSH Server**: Handles SSH protocol, authentication (disabled for public access), and connection management
- **PTY Layer**: Creates a pseudo-terminal that gives Textual a real terminal device (`/dev/pts/X`)
- **Raw Mode**: Disables line buffering for immediate keystroke delivery
- **Process Factory**: Manages TUI subprocess lifecycle per SSH connection
- **Session Factory**: Handles PTY negotiation and channel configuration

**Windows Compatibility:**
The server correctly handles Windows SSH clients which send keyboard input differently than Linux/macOS clients. The implementation routes input through AsyncSSH's channel system for cross-platform compatibility.

### Project Structure

```
tui_resume_python/
├── src/
│   └── tui_resume/
│       ├── app.py                    # Main Textual application
│       ├── ssh_server.py             # AsyncSSH PTY-based server
│       ├── screens/                  # Screen modules
│       │   ├── home.py              # Animated home screen
│       │   ├── projects.py          # Projects portfolio
│       │   ├── about.py             # Bio and skills
│       │   ├── game.py              # Security clearance game
│       │   └── contact.py           # Contact info (unlocked)
│       ├── widgets/                  # Custom widgets
│       │   ├── navbar.py            # Navigation bar
│       │   ├── generative_bg.py     # Animated ASCII background
│       │   ├── matrix_text.py       # Matrix decode effect
│       │   ├── project_card.py      # Project cards
│       │   └── home_greeting.py     # Animated greeting
│       └── css/
│           └── app.tcss             # Textual CSS styling
├── logs/                             # Connection and error logs
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Container image definition
├── docker-compose.yml                # Multi-container orchestration
├── run_ssh_app_direct.py            # SSH app wrapper with driver patches
└── README.md                         # This file
```

##  Docker Deployment

The application is fully containerized for production deployment:

```yaml
# docker-compose.yml
services:
  resume-app:
    build: .
    ports:
      - "22:2222"      # Map host port 22 to container port 2222
    volumes:
      - ./logs:/app/logs
      - ./host_key:/app/host_key
      - ./host_key.pub:/app/host_key.pub
    restart: unless-stopped
```

**Default Ports:**
- **Container Internal**: 2222 (SSH server listens here)
- **Production Host**: 22 (mapped from container's 2222)
- **Development**: 2222 (direct access for testing)

##  AWS EC2 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete AWS EC2 deployment instructions, including:

- EC2 instance setup (t3.micro free tier)
- Security group configuration
- Docker deployment
- Domain configuration
- SSH access setup

**Quick Deploy:**
```bash
# On EC2 instance
git clone <your-repo>
cd tui_resume_python
docker-compose up -d

# Test connection
ssh ubuntu@<your-ec2-ip>
```


- **Python 3.11+**: Core runtime environment
- **Textual**: Modern TUI framework with Rich integration for beautiful terminal UIs
- **AsyncSSH**: Asynchronous SSH server library for Python
- **PTY Module**: Unix pseudo-terminal handling for proper terminal emulation
- **OpenSimplex**: Perlin noise generation for animated backgrounds
- **Docker**: Containerization for consistent deployment
- **AWS EC2**: Cloud hosting platform (t2.micro Free Tier compatible)

## Technical Details

### Linux Driver Patches

The application patches Textual's `LinuxDriver` to disable terminal queries that cause artifacts over SSH:
- Mouse support disabled (prevents gibberish in terminal)
- Terminal sync mode requests disabled
- Cursor position queries disabled
- Device attribute requests disabled
- Bracketed paste mode disabled

These patches are in [`run_ssh_app_direct.py`](run_ssh_app_direct.py).

### Logging

Connection logs and errors are written to `logs/connections.log`:
```python
# View logs
tail -f logs/connections.log

# Docker logs
docker logs -f resume-app
```

### Security

- **No Authentication Required**: Public access by design (portfolio showcase)
- **SFTP/SCP Disabled**: Only interactive shell access allowed
- **Process Isolation**: Each SSH connection spawns an isolated subprocess
- **Non-root Execution**: Docker container runs as unprivileged user


