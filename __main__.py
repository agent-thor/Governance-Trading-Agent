#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Governance Trading Bot.

This file allows the package to be run as a module:
    python -m proposal_revamp
"""

import os
import sys

# Add the parent directory to sys.path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from proposal_revamp.main import main

if __name__ == "__main__":
    main() 