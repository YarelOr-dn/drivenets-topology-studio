#!/usr/bin/env python3
"""Quick diagnostic script for PE-1 recovery mode."""

import sys
sys.path.insert(0, '/home/dn/SCALER')

from scaler.device_manager import DeviceManager
from scaler.interactive_scale import _diagnose_device_recovery

if __name__ == "__main__":
    dm = DeviceManager()
    
    # Try to find PE-1 (case-insensitive)
    pe1 = None
    for dev in dm.list_devices():
        if dev.hostname.upper() == "PE-1":
            pe1 = dev
            break
    
    if not pe1:
        print("❌ PE-1 not found in device cache")
        print("Available devices:")
        for dev in dm.list_devices():
            print(f"  • {dev.hostname} ({dev.device_id})")
        sys.exit(1)
    
    print(f"🔍 Running diagnostic on {pe1.hostname} ({pe1.ip})...\n")
    _diagnose_device_recovery(pe1)
