#!/usr/bin/env python3
"""Helper script to generate SSH host key for the TUI Resume server"""

import subprocess
import sys
from pathlib import Path


def generate_host_key():
    """Generate SSH host key using ssh-keygen"""
    
    host_key_path = Path("host_key")
    
    # Check if key already exists
    if host_key_path.exists():
        response = input("Host key already exists. Regenerate? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing host key.")
            return True
    
    print("Generating SSH host key...")
    print("This will create 'host_key' and 'host_key.pub' in the current directory.")
    
    try:
        # Run ssh-keygen command
        result = subprocess.run(
            ["ssh-keygen", "-f", "host_key", "-N", "", "-t", "rsa", "-b", "2048"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Host key generated successfully!")
            print(f"   - Private key: {host_key_path.absolute()}")
            print(f"   - Public key: {host_key_path.absolute()}.pub")
            print("\n⚠️  IMPORTANT: Keep 'host_key' secure and do NOT commit to version control!")
            return True
        else:
            print(f"\n❌ Error generating key: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("\n❌ Error: 'ssh-keygen' not found.")
        print("   Please install OpenSSH client:")
        print("   - Windows: Install 'OpenSSH Client' via Windows Features")
        print("   - Linux/Mac: Should be pre-installed, or use: apt install openssh-client")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    """Main entry point"""
    print("=" * 60)
    print("  TUI Resume - SSH Host Key Generator")
    print("=" * 60)
    print()
    
    success = generate_host_key()
    
    if success:
        print("\nNext steps:")
        print("  1. Run the SSH server: python -m src.tui_resume.ssh_server")
        print("  2. Connect via SSH: ssh localhost -p 2222")
        print("  3. See QUICKSTART.md for more details")
        sys.exit(0)
    else:
        print("\nPlease resolve the error above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
