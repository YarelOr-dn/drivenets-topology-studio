"""SCALER main entry point.

Supports two UI modes:
  - Rich CLI (default): Terminal-based with Rich formatting
  - Textual TUI: Modern TUI with scrollbar, mouse support, widgets

Usage:
  python -m scaler          # Rich CLI (default)
  python -m scaler --tui    # Textual TUI with scrollbar
  python -m scaler wizard   # Direct wizard mode
"""

import sys


def main():
    """Main entry point with UI mode selection."""
    args = sys.argv[1:]
    
    # Check for TUI mode
    if "--tui" in args or "-t" in args:
        from .tui import run_tui
        run_tui()
        return 0
    
    # Check for direct wizard mode
    if "wizard" in args or "-w" in args:
        from .interactive_scale import run_wizard
        run_wizard()
        return 0
    
    # Default: Rich CLI
    from .cli import main as cli_main
    return cli_main()


if __name__ == "__main__":
    sys.exit(main() or 0)














