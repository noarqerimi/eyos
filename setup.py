#!/usr/bin/env python3
"""
Setup script for NewStore to Hail Integration.

This script checks for Rye, installs dependencies, and sets up the environment.
"""
import subprocess
import sys
from pathlib import Path


def check_rye_installed():
    """Check if Rye is installed."""
    try:
        subprocess.run(["rye", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup_environment():
    """Set up the environment."""
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("Creating .env file from .env.example...")
            with open(".env.example", "r") as example, open(".env", "w") as env:
                env.write(example.read())
        else:
            print("Creating default .env file...")
            with open(".env", "w") as env:
                env.write("""
# API settings
EYOS_API_TITLE="NewStore to Hail Integration"
EYOS_API_DESCRIPTION="Service for integrating NewStore order events with eyos Hail API"
EYOS_API_VERSION="0.1.0"

# NewStore webhook settings
EYOS_NEWSTORE_WEBHOOK_SECRET="mock_webhook_secret"
EYOS_NEWSTORE_SUPPORTED_EVENTS=["order.completed"]

# Hail API settings
EYOS_HAIL_API_BASE_URL="mock"
EYOS_HAIL_API_KEY="mock_api_key"
EYOS_HAIL_API_MAX_RETRIES=3
EYOS_HAIL_API_RETRY_DELAY=1.0

# Queue settings
EYOS_QUEUE_ENABLED=false

# Logging settings
EYOS_LOG_LEVEL="INFO"
""")


def main():
    """Main entry point."""
    print("Setting up NewStore to Hail Integration...")

    # Check for Rye
    if not check_rye_installed():
        print("Rye package manager not found.")
        print("Please install Rye from https://rye-up.com/guide/installation/")
        sys.exit(1)

    # Install dependencies
    print("Installing dependencies with Rye...")
    subprocess.run(["rye", "sync"], check=True)

    # Set up environment
    setup_environment()

    print("\nSetup complete!")
    print("\nAvailable commands:")
    print("  rye run dev         - Start the development server")
    print("  rye run test        - Run tests")
    print("  rye run simulate    - Simulate a webhook event")
    print("\nAPI documentation will be available at:")
    print("  http://localhost:8000/docs")


if __name__ == "__main__":
    main()
