"""
BGP Configuration for the SCALER Wizard.

This module contains BGP configuration functions.
"""

from typing import Any, Dict, Optional


def configure_bgp(*args, **kwargs):
    """Configure BGP hierarchy.
    
    This function is implemented in the main module for backward compatibility.
    """
    from ..interactive_scale import configure_bgp as _configure_bgp
    return _configure_bgp(*args, **kwargs)


def _configure_single_bgp_peer(*args, **kwargs):
    """Configure a single BGP peer.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import _configure_single_bgp_peer as _impl
    return _impl(*args, **kwargs)

