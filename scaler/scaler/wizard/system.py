"""
System Configuration for the SCALER Wizard.

This module contains the system hierarchy configuration function.
"""

from typing import Any, Dict, Optional


def configure_system(*args, **kwargs):
    """Configure system hierarchy with options to keep/edit subsections.
    
    This function is implemented in the main module for backward compatibility.
    """
    from ..interactive_scale import configure_system as _configure_system
    return _configure_system(*args, **kwargs)

