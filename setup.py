#!/usr/bin/env python
"""
Setup Script for WebSiteDownloader

This script can:
1. Create and configure a Python virtual environment (.venv) with all required dependencies
2. Install the WebSiteDownloader as a package (development or regular install)

Usage:
    python setup.py venv       - Create a virtual environment only
    python setup.py develop    - Install package in development mode
    python setup.py install    - Install package normally
    python setup.py --help     - Show all setuptools commands
"""

import os
import sys
import subprocess
import platform
import logging
import argparse
from setuptools import setup, find_packages, Command

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Project root directory (where this script is located)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_ROOT, ".venv")

# Path to requirements.txt
REQUIREMENTS_PATH = os.path.join(PROJECT_ROOT, "requirements.txt")

# Load requirements from file
def get_requirements():
    """Get requirements from requirements.txt file"""
    if not os.path.exists(REQUIREMENTS_PATH):
        logger.warning(f"requirements.txt not found at {REQUIREMENTS_PATH}")
        create_default = input("Create default requirements.txt? (y/n): ").lower().strip()
        if create_default == "y":
            create_requirements_file()
        else:
            return []
    
    with open(REQUIREMENTS_PATH) as f:
        return f.read().splitlines()

def create_requirements_file():
    """Create a default requirements.txt file if it doesn't exist"""
    default_requirements = [
        "beautifulsoup4>=4.12.0",
        "requests>=2.28.0",
        "urllib3>=1.26.0",
        "tqdm>=4.64.0",
        "lxml>=4.9.0",
        "python-dotenv>=1.0.0",
        "html2text>=2020.1.16",
        "pyyaml>=6.0",
    ]
    
    with open(REQUIREMENTS_PATH, "w") as f:
        f.write("\n".join(default_requirements))
    logger.info(f"Created default requirements.txt at {REQUIREMENTS_PATH}")
    return default_requirements

# Custom setuptools command for creating a virtual environment
class VenvCommand(Command):
    """Custom command to create a virtual environment"""
    description = "create a virtual environment and install dependencies"
    user_options = []
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):
        """Run the venv creation command"""
        create_venv()
        install_dependencies()
        create_venv_activation_scripts()

def create_venv():
    """Create a virtual environment"""
    if os.path.exists(VENV_DIR):
        logger.info(f"Virtual environment already exists at {VENV_DIR}")
        overwrite = input("Do you want to recreate it? (y/n): ").lower().strip()
        if overwrite == "y":
            logger.info("Removing existing virtual environment...")
            try:
                import shutil
                shutil.rmtree(VENV_DIR)
            except Exception as e:
                logger.error(f"Failed to remove existing virtual environment: {e}")
                return False
        else:
            logger.info("Using existing virtual environment")
            return True

    logger.info(f"Creating virtual environment in {VENV_DIR}")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
        logger.info("Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return False

def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python")

def install_dependencies():
    """Install dependencies from requirements.txt"""
    python_path = get_venv_python()
    
    # Check if requirements.txt exists
    if not os.path.exists(REQUIREMENTS_PATH):
        create_requirements_file()
    
    logger.info("Installing dependencies from requirements.txt")
    try:
        # Upgrade pip first
        subprocess.check_call([python_path, "-m", "pip", "install", "--upgrade", "pip"])
        # Install requirements
        subprocess.check_call([python_path, "-m", "pip", "install", "-r", REQUIREMENTS_PATH])
        logger.info("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")

def create_venv_activation_scripts():
    """Create convenience activation scripts"""
    # For Windows (.bat)
    if platform.system() == "Windows":
        activate_bat_path = os.path.join(PROJECT_ROOT, "activate_venv.bat")
        with open(activate_bat_path, "w") as f:
            f.write(f'@echo off\necho Activating virtual environment...\ncall "{os.path.join(VENV_DIR, "Scripts", "activate.bat")}"\necho Virtual environment activated. Type "deactivate" to exit.\n')
        logger.info(f"Created activation script at {activate_bat_path}")
    
    # For Unix-based systems (.sh)
    else:
        activate_sh_path = os.path.join(PROJECT_ROOT, "activate_venv.sh")
        with open(activate_sh_path, "w") as f:
            f.write(f'#!/bin/bash\necho "Activating virtual environment..."\nsource "{os.path.join(VENV_DIR, "bin", "activate")}"\necho "Virtual environment activated. Type \\"deactivate\\" to exit."\n')
        os.chmod(activate_sh_path, 0o755)  # Make executable
        logger.info(f"Created activation script at {activate_sh_path}")

def print_venv_instructions():
    """Print instructions for using the virtual environment"""
    logger.info("\n" + "=" * 60)
    logger.info("Virtual environment setup complete!")
    logger.info(f"Virtual environment location: {VENV_DIR}")
    
    # Provide instructions
    if platform.system() == "Windows":
        logger.info("\nTo activate the environment, run:")
        logger.info("    activate_venv.bat")
        logger.info("Or manually:")
        logger.info(f"    {os.path.join(VENV_DIR, 'Scripts', 'activate.bat')}")
    else:
        logger.info("\nTo activate the environment, run:")
        logger.info("    source activate_venv.sh")
        logger.info("Or manually:")
        logger.info(f"    source {os.path.join(VENV_DIR, 'bin', 'activate')}")
    
    logger.info("\nTo deactivate the environment when finished, simply run:")
    logger.info("    deactivate")
    logger.info("=" * 60)

if __name__ == "__main__":
    # Handle direct script execution with the 'venv' argument
    if len(sys.argv) > 1 and sys.argv[1] == 'venv':
        # Remove the 'venv' argument so setuptools doesn't see it
        sys.argv.pop(1)
        if create_venv():
            install_dependencies()
            create_venv_activation_scripts()
            print_venv_instructions()
    else:
        # Run regular setuptools setup
        setup(
            name="websitedownloader",
            version="1.0.0",
            packages=find_packages(),
            install_requires=get_requirements(),
            python_requires=">=3.7",
            entry_points={
                "console_scripts": [
                    "websitedownloader=src.main:main",
                ],
            },
            cmdclass={
                'venv': VenvCommand,
            },
            author="WebSiteDownloader Contributors",
            description="Tool to download websites and convert to GitHub-ready Markdown",
            keywords="website, github, markdown, converter, crawler",
        )