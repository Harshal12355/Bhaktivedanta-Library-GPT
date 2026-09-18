#!/usr/bin/env python3
"""
Vedic Chat CLI
Entry point for the command-line interface
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli.main import app

if __name__ == "__main__":
    app()
