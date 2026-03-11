"""
Service Configuration for the SCALER Wizard.

This module contains the service (FXC/VPLS/EVPN) configuration function.
"""

from typing import Any, Dict, Optional


def configure_services(*args, **kwargs):
    """Configure services hierarchy.
    
    This function is implemented in the main module for backward compatibility.
    """
    from ..interactive_scale import configure_services as _configure_services
    return _configure_services(*args, **kwargs)

