"""
IGP/ISIS Configuration for the SCALER Wizard.

This module contains IGP configuration functions.
"""

import re
from typing import Any, Dict, Optional


def ip_to_isis_net(ip_address: str, area_id: str = "49.0001") -> str:
    """Convert an IPv4 address to ISIS NET address format.
    
    Example: 4.4.4.4 -> 49.0001.0004.0004.0004.00
    
    Format: <area>.<oct1_oct2>.<oct2_oct3>.<oct3_oct4>.00
    where each octet is padded to 4 digits and grouped as 2.2.2
    
    Args:
        ip_address: IPv4 address (e.g., "4.4.4.4" or "4.4.4.4/32")
        area_id: Area prefix (default: "49.0001")
        
    Returns:
        ISIS NET address (e.g., "49.0001.0004.0004.0004.00")
    """
    # Strip CIDR if present
    ip = ip_address.split('/')[0]
    octets = ip.split('.')
    
    if len(octets) != 4:
        return f"{area_id}.0000.0000.0001.00"  # Fallback
    
    # Pad each octet to 4 digits and group
    # Format: AAAA.BBBB.CCCC -> A.AAA.B.BBB.C.CCC (but actually 2+2.2+2.2+2)
    # Each pair of octets forms a group
    padded = [f"{int(o):04d}" for o in octets]
    
    # ISIS NET format: area.xxxx.xxxx.xxxx.00
    # where xxxx is formed from groups of octet digits
    # Common format: 49.0001.OOOO.OOOO.OOOO.00 where O is octet value
    # Example: 4.4.4.4 -> each octet 4 -> padded 0004 -> 49.0001.0004.0004.0004.00
    
    return f"{area_id}.{padded[0]}.{padded[1]}.{padded[2]}.00"


def configure_igp(*args, **kwargs):
    """Configure IGP hierarchy.
    
    This function is implemented in the main module for backward compatibility.
    """
    from ..interactive_scale import configure_igp as _configure_igp
    return _configure_igp(*args, **kwargs)

