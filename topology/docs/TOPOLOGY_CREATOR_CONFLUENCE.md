# DriveNets Topology Creator

**A purpose-built network topology editor for designing, discovering, and documenting DriveNets deployments.**

---

## What Makes It Different

The Topology Creator is not a generic diagramming tool. It was built for network engineers working with real DriveNets devices, real protocols, and real infrastructure. Everything in the editor -- devices, links, discovery, export -- is network-aware.

| Capability | What It Means |
|---|---|
| **Live device discovery** | LLDP-based auto-discovery builds topology from real network state -- no manual placement |
| **DNAAS awareness** | Discovers bridge-domains, traces paths through DNAAS fabric, visualizes underlay |
| **DriveNets device library** | Pre-loaded SA, CL, NC-AI, DNAAS platforms with accurate specs |
| **Links with meaning** | Links carry interface names, VLANs, protocol labels -- not just lines between boxes |
| **Packet capture from diagram** | Select a link, launch live CP/DP traffic capture directly from the topology |
| **Multi-segment link chains** | BUL system models complex multi-hop paths with merge/terminal points |
| **Canvas physics** | Momentum-based device movement with collision detection |
| **Network-aware export** | JSON export retains full device/link/VRF metadata for toolchain reuse |
| **SSH from diagram** | Open terminal to any device directly from its selection toolbar |
| **Keyboard-first** | 30+ shortcuts for every operation |

---

## Key Features

### 1. Live Network Discovery

Point the app at a seed device and it discovers the network for you.

- **LLDP discovery** -- Click a device, enable LLDP from its toolbar. The app SSHes into the device, reads LLDP neighbors, and populates the topology with real connections.
- **Network Mapper** -- Press **N** to open the Network Mapper panel. Recursive BFS traversal from one or more seed devices, with configurable depth and device limits. Supports force-directed auto-layout for up to ~100 devices.
- **DNAAS discovery** -- Press **D** to open the DNAAS panel. Enter a device serial or hostname, and the app traces paths through the DNAAS fabric -- discovers bridge-domains, maps termination devices to fabric leaves, and renders the full underlay path.
- **Device inventory** -- Pulls device lists from SCALER, resolves hostnames, and pre-populates device metadata.

Once discovered, the topology is fully editable. Rearrange devices, add annotations, attach interface labels -- the discovered data stays intact.

### 2. DriveNets-Native Device Library

Every DriveNets platform is built in. Click the **Device** section in the left toolbar, pick a visual style, and click the canvas to place a device. The device carries its platform data and can be assigned to any DriveNets platform type:

**Standalone (SA/NCP)** -- SA-40C, SA-10CD, SA-36CD-S, SA-64X12C-S, SA-38E, SA-40C8CD, SA-32CD, and more

**Clustered (CL/Chassis)** -- CL-16 through CL-768

**NC-AI** -- AI-72-400G through AI-8192-400G

**DNAAS** -- NCM fabric devices with discovery-aware behavior

Double-click any device to open the device editor modal -- edit label, assign SSH address, change platform type, or view interface details.

### 3. Five Visual Styles

The Device section in the left toolbar shows five style buttons. Click one to set the style for new devices, or select an existing device and change its style from the selection toolbar.

| Style | Button Tooltip | Best For |
|---|---|---|
| **Circle** | Circle shape (default) | Clean, minimal -- good for large topologies |
| **Classic** | Cylinder router style | Traditional 3D router icon -- customer-facing diagrams |
| **Simple** | Schematic router style | Lightweight node with directional ports -- CE devices |
| **Hex** | Hexagonal node style | Fabric elements, special-purpose nodes |
| **Server** | Server tower style | Compute, ExaBGP, test tools, collectors |

Styles are per-device. Mix and match in the same topology. Copy a device's style to others using context menu "Copy Style" or the **C** shortcut.

### 4. Device Toolbar Options

Below the style buttons in the Device section:

- **Label Font** -- Choose the font for device labels: Sans (Inter), Brand (IBM Plex Sans), Hand (Caveat), Mono (IBM Plex Mono), Serif (Georgia), Sketch (Comic Neue), plus System font
- **Device Numbering** -- Auto-number devices when placing multiples (NCP, NCP-2, NCP-3...)
- **Device Collision** -- Prevent devices from overlapping when dragged
- **Movable Devices** -- Devices push each other when moved (enabled by default)
- **Momentum** -- Objects slide after release with velocity-based deceleration. Adjustable friction slider (1-10) controls slide distance. Devices bounce off each other in billiard-style chain reactions.

### 5. Link System

Click the **Links** section header in the left toolbar to activate link mode. Click two devices to connect them.

**Link styles** -- Three style groups, each with 4 variants (click the button to cycle through):
- **Solid** -- Solid, Solid-thick, Solid-thin, Solid-double
- **Dashed** -- Dashed, Dashed-wide, Dotted, Dotted-wide
- **Arrow** -- Arrow, Double-arrow, Dashed-arrow, Dashed-double-arrow

**Link options:**
- **Color picker** -- Per-link color with "Apply to all links" button
- **Width slider** -- 1 to 8px
- **Curve toggle** -- Magnetic curve mode with Auto (curves around obstacles) or Manual (drag the link body to shape the curve), plus adjustable curve magnitude slider
- **Continuous mode** -- Chain multiple links without re-clicking the tool
- **Sticky mode** -- Links snap/attach to nearby devices
- **Unbound Links (UL)** -- Create links on empty canvas with free endpoints (not attached to any device). Attach to devices later, or leave floating.

**Link types:**
- **Quick Links** -- Device-to-device. Click two devices to connect.
- **Unbound Links** -- Free-form links with independent endpoints.
- **BUL Chains** -- Multi-segment link topologies with Merge Points (MP) and Terminal Points (TP). Model complex physical paths like bundle aggregations or multi-hop fabric connections.

**Link details modal** -- Select a link and open its details from the selection toolbar. Edit interface names (both ends), fetch DNAAS interface details, or create link-attached text labels.

### 6. Shapes

Click the **Shapes** section header in the left toolbar to activate shape placement mode.

**Available shapes (10 types in two grids):**
- Rectangle, Circle, Triangle, Diamond
- Checkmark, Cross, Star, Hexagon
- Ellipse, Cloud

**Shape features:**
- Fill color and opacity
- Stroke color and width
- Resize handles
- Corner radius (rectangles)
- **Merge to background** -- Makes the interior transparent for hit detection so the shape acts as a visual container without blocking selection of objects inside it. Use rectangles as VRF panels, site boundaries, or data center zones.
- Layer ordering (context menu: To Front, Forward, Backward, To Back)

### 7. Text and Annotations

Click the **Text** section header in the left toolbar to activate text placement mode. Click the canvas to place a text box. Double-click any text to edit in place.

**Place TBs** -- A prominent button that enables continuous text placement mode. Click multiple spots on the canvas to drop text boxes without re-activating the tool.

**Font Family** -- Six fonts: Sans (Inter), Brand (IBM Plex Sans), Hand (Caveat), Mono (IBM Plex Mono), Serif (Georgia), Sketch (Comic Neue)

**Text Size** -- Presets: S (10px), M (14px), L (18px), XL (24px). Custom slider from 8px to 48px.

**Colors** -- Unified color section with three targets:
- **Text** color
- **Background** color and opacity
- **Border** color, with solid/dashed/dotted style options

**Additional toggles:**
- **TB Attach** -- Auto-create interface text labels on links when placing text near a link
- **Angle Meter** -- Show angle indicator when rotating text
- **Text Face User** -- Force all text to stay horizontal regardless of link angle

**Link-attached text** -- Text boxes can attach to links and position along the link path. They follow the link when devices move. Create interface labels directly from the link details modal.

### 8. Packet Capture from the Diagram

Select a link and click the **Packet Capture** button (blue magnifier icon) in the link selection toolbar to launch a live capture.

**Capture modes:**
- **Control Plane (CP)** -- BGP, OSPF, ISIS, LDP, LLDP, BFD
- **Data Plane (DP)** -- Wire-speed mirrored traffic via Arista SPAN
- **DNAAS-DP** -- Leaf mirror and spine dropped-packet capture

**Options:** Duration (3s to 60s), direction (ingress/egress/both), protocol filters, output (pcap file or direct delivery to Mac with Wireshark auto-open), capture from either end of the link.

### 9. Top Bar

The top bar provides quick access to:

- **Topologies** -- Save, load, and manage topologies organized by domain/section. Browse, switch, delete. Press **T** to toggle.
- **Clear** -- Clear all objects from the canvas (Ctrl+X)
- **Shortcuts** -- View all keyboard shortcuts in a reference overlay
- **Link Type Labels** -- Show/hide link type labels on the canvas (debug/documentation)
- **DNAAS** -- Open the DNAAS discovery panel. Press **D** to toggle. Shows BD hierarchy badge when bridge-domain data is loaded.
- **Network Mapper** -- Open the Network Mapper panel for LLDP-based topology discovery. Press **N** to toggle.
- **SCALER Config** -- Generate SCALER device configuration from the topology
- **Theme** -- Toggle dark/light theme. Press **L** to toggle.
- **Refresh** -- Reload the page. Press **R**.

### 10. Canvas Navigation (HUD)

A floating control cluster in the bottom-right corner:

- **Zoom In / Zoom Out** -- Button-based zoom, or use scroll wheel (zooms at cursor position)
- **Fit** -- Center and scale to fit all objects in view. Press **F**.
- **Reset Zoom** -- Return to 100% zoom
- **Grid** -- Toggle grid lines with **G**. Zoom-aware grid that scales naturally.
- **Minimap** -- Toggle with **M**. Click-drag to navigate the canvas. Right-drag to pan the minimap itself.

### 11. Topology Domains and Organization

Save and organize topologies by project, customer, or use case.

- **Domains** -- Group topologies into named sections (e.g., "Customer A", "Lab", "Production")
- **Quick save** -- Ctrl+S opens a domain picker overlay for one-click save
- **Topologies dropdown** -- Browse, switch, and delete saved topologies
- **Number keys (1-9)** -- Instantly switch between topologies in a domain
- **Alt+Left/Right** -- Navigate previous/next topology

### 12. Export and Sharing

- **PNG export** -- High-resolution (1x to 4x scale) for presentations and documents
- **JSON export** -- Full topology with all metadata, suitable for version control or toolchain integration
- **Bug evidence topologies** -- Save investigation topologies directly to the bug evidence directory for debug session documentation

### 13. Selection Toolbars

When you select an object, a floating glass-styled toolbar appears next to it with contextual actions:

**Device toolbar** -- Rename | SSH | LLDP (scan, view table -- shown when SSH is configured) | Style | Color | Label Style | Duplicate | Copy Style | Lock/Unlock | Delete

**Link toolbar** -- Packet Capture (shown when link has SSH devices) | Add Text | Color | Width | Style | Curve | Attach/Detach/Sticky | Duplicate | Copy Style | Delete (BUL chains show "Delete this UL" and "Delete entire chain")

**Text toolbar** -- Font, size, colors, rotation, detach from link, delete

### 14. Right-Click Context Menu

Right-click any object for additional actions:
- Color, Style, Label, Rename
- Lock/Unlock position
- SSH address configuration (devices)
- Curve controls (links)
- Layer ordering: To Front, Forward, Backward, To Back
- Copy Style, Duplicate, Delete
- Group/Ungroup (multi-selection)

### 15. Undo/Redo and History

Full undo/redo with up to 50 history steps.
- **Ctrl+Z** -- Undo
- **Ctrl+Y** or **Ctrl+Shift+Z** -- Redo
- Step counter shows current position in the history stack

### 16. Object Grouping

Select multiple objects (click and drag to box-select, or Shift-click). Group them so they move together.
- Leader object (top-right) anchors the group
- Supports devices, links, text, and shapes
- Ungroup to restore independent movement

### 17. Theming

- **Dark mode** -- Full dark theme with DriveNets brand palette (navy, cyan, orange). Default.
- **Light mode** -- Clean light theme for presentations and printing
- **Toggle with L** -- Instant switch, persisted in browser storage
- **CSS variables** -- All colors defined as variables for consistency across the UI

### 18. Auto-Save and Crash Recovery

- Session tracking with auto-save on every meaningful action
- Crash recovery restores the last saved state on reload
- No manual save-and-pray workflow

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| **Ctrl+S** | Save topology |
| **Ctrl+Z** | Undo |
| **Ctrl+Y** | Redo |
| **Ctrl+L** | Create unbound link |
| **Ctrl+C / Ctrl+V** | Copy / Paste |
| **Delete** | Delete selected |
| **Ctrl+X** | Clear canvas |
| **Space+Drag** | Pan canvas |
| **Scroll wheel** | Zoom at cursor |
| **F** | Fit all objects in view |
| **G** | Toggle grid |
| **L** | Toggle light/dark theme |
| **M** | Toggle minimap |
| **D** | Toggle DNAAS panel |
| **N** | Toggle Network Mapper |
| **T** | Toggle Topologies dropdown |
| **B** | Toggle BD Legend |
| **C** | Copy style (with object selected) |
| **R** | Refresh page |
| **1-9** | Switch topology in domain |
| **Alt+Left/Right** | Previous/next topology |
| **Ctrl+]** / **Ctrl+[** | Layer forward / backward |
| **Ctrl+Shift+]** / **Ctrl+Shift+[** | Send to front / back |

---

## Integration Points

| System | How It Integrates |
|---|---|
| **DNAAS** | Discovery panel discovers bridge-domains, traces fabric paths, shows BD hierarchy |
| **Network Mapper** | MCP-based recursive LLDP topology discovery with auto-layout |
| **SCALER** | Device inventory, topology sections/domains, bug evidence topologies |
| **SSH** | Direct terminal access from any device's selection toolbar |
| **Packet Capture** | Live CP/DP packet capture from any link's selection toolbar |
| **ExaBGP / BGP Tool** | Bug investigation topologies auto-generated from debug sessions |

---

## Architecture

Browser-based application built with vanilla JavaScript and HTML5 Canvas. No framework dependencies, no build step, no npm install.

- **Frontend** -- Single-page app served as static HTML/JS/CSS
- **Backend** -- Python FastAPI server for DNAAS discovery, Network Mapper proxy, and topology persistence
- **Deployment** -- Served via nginx, accessible from any browser

Modular architecture with ~30 focused JS modules (devices, links, text, shapes, input handling, drawing, history, file operations, UI) coordinated through a central editor instance.

---

## Getting Started

1. Open the Topology Creator in your browser
2. **Discover** -- Press **N** for Network Mapper or **D** for DNAAS discovery, or place devices manually by clicking the Device section and then clicking the canvas
3. **Connect** -- Click the Links section header, then click two devices to create a link. Use **Ctrl+L** for free-form unbound links.
4. **Annotate** -- Click the Text section header, then click the canvas to place text. Use shapes for VRF panels or site boundaries.
5. **Save** -- Press **Ctrl+S** and pick a domain to organize by project
6. **Export** -- File menu for PNG (presentations) or JSON (toolchain integration)
