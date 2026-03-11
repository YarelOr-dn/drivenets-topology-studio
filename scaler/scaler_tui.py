#!/usr/bin/env python3
"""Quick launcher for SCALER Textual TUI mode.

Usage:
  python scaler_tui.py           # Launch TUI with scrollbar
  ./scaler_tui.py                # Same (if executable)
"""

import sys
sys.path.insert(0, '/home/dn/SCALER')

from scaler.tui import run_tui

if __name__ == "__main__":
    run_tui()
