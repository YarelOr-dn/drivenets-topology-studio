"""SCALER Textual TUI - Modern UI with scrollbar support.

This module provides a Textual-based interface for SCALER with:
- Proper scrollbar on the right side
- Mouse and keyboard navigation
- Rich text rendering
- Split-pane support for multi-device operations
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Static, Button, Label, 
    DataTable, Tree, Input, Select, 
    ProgressBar, RichLog, Markdown,
    ListView, ListItem, Rule
)
from textual.reactive import reactive
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# Import SCALER components
try:
    from .device_manager import DeviceManager
    from .models import Device
    from .config_parser import ConfigParser
except ImportError:
    # Allow running standalone for testing
    pass


class DevicePanel(Static):
    """Panel showing device status and summary."""
    
    def __init__(self, hostname: str, summary: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.hostname = hostname
        self.summary = summary
    
    def compose(self) -> ComposeResult:
        yield Static(self._render_summary())
    
    def _render_summary(self) -> Panel:
        lines = []
        lines.append(f"[bold]System:[/bold] {self.summary.get('system', {}).get('name', 'N/A')}")
        lines.append(f"[bold]Interfaces:[/bold] {self.summary.get('interfaces', {}).get('count', 0):,}")
        lines.append(f"[bold]Services:[/bold] {self.summary.get('services', {}).get('count', 0)}")
        
        bgp = self.summary.get('bgp', {})
        if bgp.get('as'):
            lines.append(f"[bold]BGP:[/bold] AS {bgp['as']}, {bgp.get('peers', 0)} peers")
        else:
            lines.append("[bold]BGP:[/bold] [dim]Not configured[/dim]")
        
        igp = self.summary.get('igp', {})
        if igp.get('protocol'):
            lines.append(f"[bold]IGP:[/bold] {igp['protocol']}")
        else:
            lines.append("[bold]IGP:[/bold] [dim]Not configured[/dim]")
        
        return Panel(
            "\n".join(lines),
            title=f"[bold cyan]{self.hostname}[/bold cyan]",
            border_style="cyan"
        )


class ConfigView(ScrollableContainer):
    """Scrollable configuration view with scrollbar."""
    
    DEFAULT_CSS = """
    ConfigView {
        height: 100%;
        border: solid green;
    }
    ConfigView:focus {
        border: double green;
    }
    """
    
    def __init__(self, content: str = "", title: str = "Configuration", **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.title = title
    
    def compose(self) -> ComposeResult:
        yield Static(self.content, id="config-content")
    
    def update_content(self, content: str) -> None:
        """Update the configuration content."""
        self.content = content
        config_widget = self.query_one("#config-content", Static)
        config_widget.update(content)


class DeviceSelector(Screen):
    """Screen for selecting devices."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("enter", "select", "Select"),
    ]
    
    def __init__(self, devices: List[Device], **kwargs):
        super().__init__(**kwargs)
        self.devices = devices
        self.selected_devices: List[Device] = []
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("[bold cyan]Select Target Devices[/bold cyan]", classes="title"),
            Rule(),
            ListView(
                *[ListItem(Label(f"[{i+1}] {dev.hostname} ({dev.ip})")) 
                  for i, dev in enumerate(self.devices)],
                id="device-list"
            ),
            Rule(),
            Horizontal(
                Button("Select All", id="select-all", variant="primary"),
                Button("Continue", id="continue", variant="success"),
                Button("Back", id="back", variant="default"),
                classes="button-row"
            ),
            id="device-selector"
        )
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "select-all":
            self.selected_devices = self.devices.copy()
            self.notify(f"Selected all {len(self.devices)} devices")
        elif event.button.id == "continue":
            if self.selected_devices:
                self.app.push_screen(WizardScreen(self.selected_devices))
            else:
                self.notify("Please select at least one device", severity="warning")


class WizardScreen(Screen):
    """Main wizard screen with scrollable content and visible scrollbar."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("b", "back", "Back"),
        Binding("t", "top", "Top"),
        Binding("q", "quit", "Quit"),
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("home", "scroll_home", "Scroll to Top", show=False),
        Binding("end", "scroll_end", "Scroll to Bottom", show=False),
    ]
    
    DEFAULT_CSS = """
    WizardScreen {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 3fr;
    }
    
    #sidebar {
        width: 100%;
        height: 100%;
        border: solid cyan;
        padding: 1;
    }
    
    #main-content {
        width: 100%;
        height: 100%;
    }
    
    /* Scrollable container with VISIBLE scrollbar on right side */
    #config-scroll {
        height: 100%;
        border: solid green;
        scrollbar-gutter: stable;
        scrollbar-size: 1 1;
    }
    
    #config-scroll:focus {
        border: double green;
    }
    
    /* Style the scrollbar track (background) */
    #config-scroll > .scrollbar--horizontal {
        height: 0;
    }
    
    #config-scroll > .scrollbar--vertical {
        background: $surface;
        width: 1;
    }
    
    /* Style the scrollbar thumb (draggable part) */
    #config-scroll > .scrollbar--vertical > .scrollbar-bar {
        background: $accent;
    }
    
    #config-scroll:focus > .scrollbar--vertical > .scrollbar-bar {
        background: $accent-lighten-2;
    }
    
    .menu-item {
        padding: 0 1;
        margin: 0 0 1 0;
    }
    
    .menu-item:hover {
        background: $accent;
    }
    
    .active {
        background: $accent;
        text-style: bold;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }
    
    .button-row {
        height: 3;
        align: center middle;
        padding: 1;
    }
    
    /* Scroll position indicator at bottom of sidebar */
    #scroll-position {
        dock: bottom;
        height: 1;
        text-align: center;
        background: $surface-darken-2;
    }
    """
    
    current_section = reactive("system")
    
    def __init__(self, devices: List[Device], **kwargs):
        super().__init__(**kwargs)
        self.devices = devices
        self.config_content = self._load_configs()
    
    def _load_configs(self) -> Dict[str, str]:
        """Load configurations for all devices."""
        configs = {}
        for dev in self.devices:
            config_path = Path(f"/home/dn/SCALER/db/configs/{dev.hostname}/running.txt")
            if config_path.exists():
                configs[dev.hostname] = config_path.read_text()
            else:
                configs[dev.hostname] = f"# No configuration found for {dev.hostname}"
        return configs
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="sidebar"):
            yield Static("[bold cyan]📋 Sections[/bold cyan]", classes="title")
            yield Rule()
            yield Button("🖥️  System", id="btn-system", classes="menu-item active")
            yield Button("🔌 Interfaces", id="btn-interfaces", classes="menu-item")
            yield Button("📡 Services", id="btn-services", classes="menu-item")
            yield Button("🌐 BGP", id="btn-bgp", classes="menu-item")
            yield Button("🔗 IGP", id="btn-igp", classes="menu-item")
            yield Rule()
            yield Static("[bold]Devices:[/bold]")
            for dev in self.devices:
                yield Static(f"  • {dev.hostname}")
            yield Rule()
            yield Static("[dim]↑↓ PgUp/Dn Home/End[/dim]", id="scroll-position")
        
        with ScrollableContainer(id="config-scroll"):
            yield Static(self._get_section_content("system"), id="section-content")
        
        yield Footer()
    
    def on_scrollable_container_scroll(self, event) -> None:
        """Update scroll position indicator when scrolling."""
        scroll = self.query_one("#config-scroll", ScrollableContainer)
        pos_widget = self.query_one("#scroll-position", Static)
        
        # Calculate scroll percentage
        max_scroll = scroll.max_scroll_y
        if max_scroll > 0:
            percent = int((scroll.scroll_y / max_scroll) * 100)
            pos_widget.update(f"[dim]Scroll: {percent}% ▼[/dim]")
        else:
            pos_widget.update("[dim]↑↓ PgUp/Dn Home/End[/dim]")
    
    def _get_section_content(self, section: str) -> str:
        """Get content for a section."""
        content_parts = []
        
        for dev in self.devices:
            config = self.config_content.get(dev.hostname, "")
            section_text = self._extract_section(config, section)
            
            content_parts.append(f"\n[bold cyan]{'═' * 60}[/bold cyan]")
            content_parts.append(f"[bold cyan]  {dev.hostname} - {section.upper()}[/bold cyan]")
            content_parts.append(f"[bold cyan]{'═' * 60}[/bold cyan]\n")
            
            if section_text:
                # Add line numbers
                lines = section_text.split('\n')
                numbered = [f"[dim]{i+1:4}[/dim] │ {line}" for i, line in enumerate(lines)]
                content_parts.append('\n'.join(numbered))
            else:
                content_parts.append(f"[dim]No {section} configuration found[/dim]")
        
        return '\n'.join(content_parts)
    
    def _extract_section(self, config: str, section: str) -> str:
        """Extract a section from config."""
        import re
        
        section_patterns = {
            'system': r'^system\s*\n(.*?)(?=^[^\s#]|\Z)',
            'interfaces': r'^interfaces\s*\n(.*?)(?=^[^\s#]|\Z)',
            'services': r'^network-services\s*\n(.*?)(?=^[^\s#]|\Z)',
            'bgp': r'^\s+bgp\s+\d+\s*\n(.*?)(?=^\s{2}[^\s]|\Z)',
            'igp': r'^\s+isis\s*\n(.*?)(?=^\s{2}[^\s]|\Z)',
        }
        
        pattern = section_patterns.get(section, '')
        if pattern:
            match = re.search(pattern, config, re.MULTILINE | re.DOTALL)
            if match:
                return match.group(0)[:5000]  # Limit to 5000 chars
        
        return ""
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id and button_id.startswith("btn-"):
            section = button_id.replace("btn-", "")
            self._switch_section(section)
    
    def _switch_section(self, section: str) -> None:
        """Switch to a different section."""
        # Update active state on buttons
        for btn in self.query(".menu-item"):
            btn.remove_class("active")
        
        active_btn = self.query_one(f"#btn-{section}", Button)
        active_btn.add_class("active")
        
        # Update content
        content = self._get_section_content(section)
        content_widget = self.query_one("#section-content", Static)
        content_widget.update(content)
        
        # Scroll to top
        scroll = self.query_one("#config-scroll", ScrollableContainer)
        scroll.scroll_home()
        
        self.current_section = section
    
    def action_scroll_up(self) -> None:
        scroll = self.query_one("#config-scroll", ScrollableContainer)
        scroll.scroll_up()
    
    def action_scroll_down(self) -> None:
        scroll = self.query_one("#config-scroll", ScrollableContainer)
        scroll.scroll_down()
    
    def action_page_up(self) -> None:
        scroll = self.query_one("#config-scroll", ScrollableContainer)
        scroll.scroll_page_up()
    
    def action_page_down(self) -> None:
        scroll = self.query_one("#config-scroll", ScrollableContainer)
        scroll.scroll_page_down()
    
    def action_scroll_home(self) -> None:
        scroll = self.query_one("#config-scroll", ScrollableContainer)
        scroll.scroll_home()
    
    def action_scroll_end(self) -> None:
        scroll = self.query_one("#config-scroll", ScrollableContainer)
        scroll.scroll_end()
    
    def action_back(self) -> None:
        self.app.pop_screen()
    
    def action_top(self) -> None:
        scroll = self.query_one("#config-scroll", ScrollableContainer)
        scroll.scroll_home()


class MainScreen(Screen):
    """Main menu screen."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "single_device", "Single Device"),
        Binding("2", "multi_device", "Multi-Device"),
        Binding("3", "import_topology", "Import"),
    ]
    
    DEFAULT_CSS = """
    MainScreen {
        align: center middle;
    }
    
    #main-menu {
        width: 80;
        height: auto;
        border: double cyan;
        padding: 2;
    }
    
    .menu-title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }
    
    .menu-option {
        padding: 1 2;
        margin: 1 0;
        width: 100%;
    }
    
    .menu-option:hover {
        background: $accent;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="main-menu"):
            yield Static(
                "[bold cyan]╔═══════════════════════════════════════════════════════════════════╗\n"
                "║              SCALER Interactive Configuration Wizard              ║\n"
                "║                                                                   ║\n"
                "║     Step-by-step guide to create scaled DNOS configurations      ║\n"
                "╚═══════════════════════════════════════════════════════════════════╝[/bold cyan]",
                classes="menu-title"
            )
            yield Rule()
            yield Static("[bold]Step 1: Select Target Device[/bold]")
            yield Button("[1] Single device configuration", id="single", classes="menu-option", variant="primary")
            yield Button("[2] Multi-device synchronized mode", id="multi", classes="menu-option", variant="primary")
            yield Button("[3] 📡 Import from Network-Mapper", id="import", classes="menu-option", variant="default")
            yield Rule()
            yield Button("[Q] Exit", id="exit", classes="menu-option", variant="error")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            self.app.exit()
        elif event.button.id == "single":
            self.action_single_device()
        elif event.button.id == "multi":
            self.action_multi_device()
        elif event.button.id == "import":
            self.action_import_topology()
    
    def action_single_device(self) -> None:
        devices = self._load_devices()
        if devices:
            self.app.push_screen(DeviceSelector(devices))
        else:
            self.notify("No devices found. Import from Network-Mapper first.", severity="warning")
    
    def action_multi_device(self) -> None:
        devices = self._load_devices()
        if len(devices) >= 2:
            self.app.push_screen(DeviceSelector(devices))
        else:
            self.notify("Need at least 2 devices for multi-device mode.", severity="warning")
    
    def action_import_topology(self) -> None:
        self.notify("Import from Network-Mapper - Coming soon!", severity="information")
    
    def _load_devices(self) -> List[Device]:
        """Load devices from database."""
        import json
        devices_file = Path("/home/dn/SCALER/db/devices.json")
        if devices_file.exists():
            try:
                data = json.loads(devices_file.read_text())
                return [Device(**d) for d in data.get('devices', [])]
            except Exception as e:
                self.notify(f"Error loading devices: {e}", severity="error")
        return []


class ScalerTUI(App):
    """SCALER Textual TUI Application."""
    
    TITLE = "SCALER Wizard"
    SUB_TITLE = "Interactive Configuration Wizard"
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        dock: top;
        height: 3;
    }
    
    Footer {
        dock: bottom;
        height: 1;
    }
    
    /* Scrollbar styling */
    ScrollableContainer > .scrollbar {
        width: 1;
        background: $panel;
    }
    
    ScrollableContainer > .scrollbar-bar {
        background: $accent;
    }
    
    ScrollableContainer:focus > .scrollbar-bar {
        background: $accent-lighten-2;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    
    def on_mount(self) -> None:
        self.push_screen(MainScreen())


def run_tui():
    """Run the Textual TUI application."""
    app = ScalerTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
