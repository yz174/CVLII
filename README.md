# TUI Resume - Interactive Terminal Portfolio

A dual-mode Terminal User Interface (TUI) application serving as an interactive professional portfolio. Users can connect via SSH and explore your resume through an animated, game-like interface.

## Features

- **Generative ASCII Art**: Dynamic animated background on the home screen
- **Security Clearance Game**: Mini-game to unlock contact information
- **Matrix Transitions**: Smooth "decode" effects between screens
- **Tab Navigation**: Intuitive keyboard/mouse navigation between sections
- **Dual Access**: Public SSH access (port 22) + Admin access (port 2222)

## Quick Start - Local Development

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this repository**

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

> **Windows Limitation:** SSH server mode does not work on native Windows due to Textual framework limitations. Windows users must use Docker, WSL, or deploy to Linux for SSH functionality. Direct TUI mode (Option 1) works on all platforms.

**Option 1: Direct TUI (No SSH) - Works on All Platforms**
```bash
python -m src.tui_resume.app
```
This runs the Textual interface directly in your terminal with full functionality.

**Option 2: With SSH Server - Requires Linux/Mac/WSL/Docker**
```bash
# Generate SSH host key (first time only)
ssh-keygen -f host_key -N "" -t rsa

# Start the SSH server (Linux/Mac/WSL only)
python -m src.tui_resume.ssh_server

# In a new terminal, connect
ssh localhost -p 2222
```

**Option 3: Docker (Recommended for Windows)**
```bash
# Build and run in container
docker-compose up --build

# Connect from host machine
ssh localhost -p 2222
```

### Navigation

- **Arrow Keys**: Navigate between tabs (Home → Projects → About)
- **Enter**: Select highlighted tab
- **Q**: Quit application
- **D**: Toggle dark mode
- **Tab**: Focus next element

## Project Structure

```
tui-resume/
├── src/
│   └── tui_resume/
│       ├── app.py              # Main Textual application
│       ├── ssh_server.py       # AsyncSSH server wrapper
│       ├── screens/            # Screen modules
│       │   ├── home.py
│       │   ├── projects.py
│       │   ├── about.py
│       │   ├── game.py
│       │   └── contact.py
│       ├── widgets/            # Custom widgets
│       │   ├── navbar.py
│       │   ├── generative_bg.py
│       │   ├── matrix_text.py
│       │   └── project_card.py
│       └── css/
│           └── app.tcss        # Textual CSS styling
├── logs/                       # Connection logs
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for AWS EC2 deployment instructions.

## Customization

### Update Resume Content

1. **Projects**: Edit `src/tui_resume/screens/projects.py`
2. **About/Bio**: Edit `src/tui_resume/screens/about.py`
3. **Contact Info**: Edit `src/tui_resume/screens/contact.py`
4. **Styling**: Modify `src/tui_resume/css/app.tcss`

### Change Animation Speed

Edit the interval in `src/tui_resume/widgets/generative_bg.py`:
```python
self.set_interval(1/10, self.update_frame)  # 10 FPS (increase for faster)
```

## Technologies

- **Python 3.11+**: Core runtime
- **Textual**: Modern TUI framework with Rich integration
- **AsyncSSH**: Asynchronous SSH server library
- **OpenSimplex**: Noise generation for animated backgrounds
- **Docker**: Containerized deployment
- **AWS EC2**: Cloud hosting (t2.micro Free Tier)
