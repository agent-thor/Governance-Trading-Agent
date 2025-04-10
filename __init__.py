"""
Governance Trading Bot for cryptocurrency trading based on governance proposals.

This package provides an automated system for monitoring cryptocurrency governance
proposals, analyzing their sentiment, and executing trades based on predicted market impact.
"""

__version__ = "0.1.0"
__author__ = "agent-thor"

# Define what gets imported with `from proposal_revamp import *`
__all__ = []

# Import important submodules to make them available at package level
from . import utils
from . import core
from . import database
from . import exchange
from . import models
from . import services
from . import api 