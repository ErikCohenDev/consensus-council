#!/usr/bin/env python3
"""
Main CLI entry point for LLM Council Audit & Consensus Platform.

This script provides the main audit.py command referenced in the documentation.
"""
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from llm_council.cli import cli

if __name__ == '__main__':
    cli()
