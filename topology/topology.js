// Network Topology Creator - Main Application Logic
//
// ============================================================================
// CRITICAL FIXES DOCUMENTATION (Dec 2025) - DO NOT REGRESS
// ============================================================================
//
// 1. DUPLICATE EVENT PREVENTION (handleMouseDown):
//    - Both pointerdown and mousedown events fire for the same physical click
//    - Using event.timeStamp (not Date.now()) to detect duplicates within 30ms
//    - This prevents single clicks from triggering double-tap QL mode
//    - Variable: _lastMouseDownEventTime
//
// 2. QUICK LINK POSITION HANDLING:
//    - Quick Links (type 'link') don't have x,y properties directly
//    - devicePosSnapshot and finalPosBeforeOffset must handle all object types:
//      * Devices/Text: use clickedObject.x, clickedObject.y
//      * Unbound Links: use midpoint of start/end
//      * Quick Links: use midpoint of source/target device positions
//    - Fallback to {x: 0, y: 0} for unknown types
//
// 3. ARROW TIP ALIGNMENT ON CURVED LINKS:
//    - startAngle and endAngle must represent true tangent direction at each endpoint
//    - Fallback to straight-line angle if control points equal endpoints
//    - DO NOT change startAngle to "opposite of travel" - it breaks geometry
//
// 4. DOUBLE-TAP DETECTION:
//    - Uses _lastTapDevice, _lastTapPos, lastTapTime for tracking
//    - doubleTapDelay (350ms) defines max time between taps
//    - doubleTapTolerance (50px) allows slight movement between taps
//    - Tap tracking is cleared on: drag end, long press (>200ms), drag cooldown (200ms)
//
// ============================================================================

// Icon helper function - generates SVG icon HTML from the symbol library
function appIcon(iconName, extraClass = '') {
    return `<span class="ico ${extraClass}"><svg><use href="#ico-${iconName}"/></svg></span>`;
}

// ============================================================================
// TOOLBAR SECTION FUNCTIONALITY
// ============================================================================
// Toggles toolbar sections open/closed with smooth animations
// Multiple sections can be open at once (no accordion behavior)
// Fixed sections (Edit, Zoom) are always open and cannot be collapsed

function toggleToolbarSection(sectionElement, forceState = null) {
    // Skip if this is a fixed section
    if (sectionElement.classList.contains('fixed-section')) {
        return;
    }
    
    const isCurrentlyExpanded = sectionElement.classList.contains('expanded');
    
    // Determine the new state
    let shouldExpand;
    if (forceState !== null) {
        shouldExpand = forceState;
    } else {
        shouldExpand = !isCurrentlyExpanded;
    }
    
    // Toggle the clicked section (no accordion - multiple can be open)
    if (shouldExpand) {
        sectionElement.classList.add('expanded');
    } else {
        sectionElement.classList.remove('expanded');
    }
    
    // Save the state to localStorage
    const sectionName = sectionElement.getAttribute('data-section');
    if (sectionName) {
        try {
            const state = JSON.parse(localStorage.getItem('toolbarSectionState') || '{}');
            state[sectionName] = shouldExpand;
            localStorage.setItem('toolbarSectionState', JSON.stringify(state));
        } catch (e) {
            console.warn('Failed to save toolbar state:', e);
        }
    }
}

// Initialize toolbar section state from localStorage
function initToolbarSections() {
    try {
        const state = JSON.parse(localStorage.getItem('toolbarSectionState') || '{}');
        const collapsibleSections = document.querySelectorAll('.toolbar-section[data-section]:not(.fixed-section)');
        
        collapsibleSections.forEach(section => {
            const sectionName = section.getAttribute('data-section');
            // Use saved state, or default to expanded for 'device' and 'tools'
            const shouldBeExpanded = state[sectionName] !== undefined 
                ? state[sectionName] 
                : (sectionName === 'device' || sectionName === 'tools');
            
            if (shouldBeExpanded) {
                section.classList.add('expanded');
            } else {
                section.classList.remove('expanded');
            }
        });
    } catch (e) {
        console.warn('Failed to restore toolbar state:', e);
    }
}

// Call init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initToolbarSections);
} else {
    initToolbarSections();
}

// ============================================================================
// NESTED SUBSECTION TOGGLE (for Link options, etc.)
// ============================================================================
// ACCORDION BEHAVIOR: Opening one subsection closes others within the same parent
// This provides cleaner UX for the Link tool options

function toggleNestedSubsection(subsectionElement) {
    const isExpanded = subsectionElement.classList.contains('expanded');
    
    // NO ACCORDION - Allow multiple sections to be open independently
    // Each section toggles independently without affecting siblings
    
    // Toggle the clicked subsection
    if (isExpanded) {
        subsectionElement.classList.remove('expanded');
    } else {
        subsectionElement.classList.add('expanded');
    }
    
    // Save state to localStorage
    const subsectionName = subsectionElement.getAttribute('data-subsection');
    if (subsectionName) {
        try {
            const state = JSON.parse(localStorage.getItem('nestedSubsectionState') || '{}');
            state[subsectionName] = !isExpanded;
            localStorage.setItem('nestedSubsectionState', JSON.stringify(state));
        } catch (e) {
            console.warn('Failed to save nested subsection state:', e);
        }
    }
}

// ============================================================================
// SUB-OPTION BOX TOGGLE (for collapsible sub-sections within toolbar)
// ============================================================================

function toggleSubOptionBox(headerElement) {
    const boxElement = headerElement.closest('.sub-option-box');
    if (!boxElement) return;
    
    const isExpanded = boxElement.classList.contains('expanded');
    
    // Toggle the clicked box
    if (isExpanded) {
        boxElement.classList.remove('expanded');
    } else {
        boxElement.classList.add('expanded');
    }
    
    // Update chevron if present
    const chevron = headerElement.querySelector('.toggle-chevron');
    if (chevron) {
        chevron.textContent = isExpanded ? '▶' : '▼';
    }
}

// ============================================================================
// TOOL SECTION ACTIVATION (Link, Text sections act as tool buttons)
// ============================================================================
// Clicking the section header activates the tool AND toggles the section

function activateToolSection(toolName, sectionElement) {
    // Get the topology instance
    const topology = window.topologyEditor;
    if (!topology) {
        console.warn('Topology editor not found');
        toggleToolbarSection(sectionElement);
        return;
    }
    
    // Remove tool-active class from all tool sections
    document.querySelectorAll('.toolbar-section.tool-section').forEach(section => {
        section.classList.remove('tool-active');
    });
    
    // Hide all mode indicators
    document.querySelectorAll('.tool-mode-indicator').forEach(indicator => {
        indicator.style.display = 'none';
    });
    
    // Check if this tool is already active - if so, just toggle section
    const wasActive = topology.currentMode === toolName;
    
    // Activate the tool via the hidden button
    if (toolName === 'link') {
        topology.toggleTool('link');
        if (!wasActive) {
            sectionElement.classList.add('tool-active');
            const indicator = document.getElementById('link-mode-indicator');
            if (indicator) indicator.style.display = 'inline-block';
        }
    } else if (toolName === 'text') {
        topology.toggleTool('text');
        if (!wasActive) {
            sectionElement.classList.add('tool-active');
            const indicator = document.getElementById('text-mode-indicator');
            if (indicator) indicator.style.display = 'inline-block';
        }
    }
    
    // Also toggle the section expansion
    toggleToolbarSection(sectionElement);
}

// Initialize nested subsection states from localStorage
// ACCORDION: Only restore ONE expanded subsection per parent container
function initNestedSubsections() {
    try {
        const state = JSON.parse(localStorage.getItem('nestedSubsectionState') || '{}');
        const subsections = document.querySelectorAll('.nested-subsection[data-subsection]');
        
        // Group subsections by parent container
        const parentGroups = new Map();
        subsections.forEach(subsection => {
            const parent = subsection.parentElement;
            if (!parentGroups.has(parent)) {
                parentGroups.set(parent, []);
            }
            parentGroups.get(parent).push(subsection);
        });
        
        // For each parent, only expand ONE subsection (the first one that was saved as expanded)
        parentGroups.forEach((groupSubsections, parent) => {
            let oneExpanded = false;
            
            groupSubsections.forEach(subsection => {
                const name = subsection.getAttribute('data-subsection');
                const wasExpanded = state[name] === true;
                
                // Only expand if none in this group are expanded yet
                if (wasExpanded && !oneExpanded) {
                    subsection.classList.add('expanded');
                    oneExpanded = true;
                } else {
                    subsection.classList.remove('expanded');
                }
            });
        });
    } catch (e) {
        console.warn('Failed to restore nested subsection state:', e);
    }
}

// Call init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNestedSubsections);
} else {
    // Small delay to ensure elements exist
    setTimeout(initNestedSubsections, 100);
}

// Bridge Domain color palette for Multi-BD DNAAS visualization
const BD_COLOR_PALETTE = [
    '#3498db',  // Blue
    '#e74c3c',  // Red
    '#2ecc71',  // Green
    '#9b59b6',  // Purple
    '#f39c12',  // Gold
    '#1abc9c',  // Teal
    '#e91e63',  // Pink
    '#00bcd4',  // Cyan
    '#ff5722',  // Deep Orange
    '#8bc34a'   // Light Green
];

// Icon map for common emoji replacements in UI
const ICON_MAP = {
    'link': 'link',
    'ruler': 'ruler',
    'palette': 'palette',
    'check': 'check',
    'warning': 'warning',
    'error': 'error',
    'success': 'success',
    'sparkle': 'sparkle',
    'target': 'target',
    'pin': 'pin',
    'brush': 'brush',
    'lock': 'lock',
    'unlock': 'unlock',
    'copy': 'copy',
    'edit': 'edit',
    'delete': 'delete',
    'chart': 'chart',
    'network': 'network',
    'router': 'router',
    'discover': 'discover',
    'refresh': 'refresh',
    'close': 'close',
    'info': 'info',
    'layers': 'layers',
    'curve': 'curve',
    'gear': 'gear',
    'pointer': 'pointer'
};

class TopologyEditor {
    constructor(canvas) {
        if (!canvas) {
            throw new Error('TopologyEditor constructor: canvas parameter is required');
        }
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        if (!this.ctx) {
            throw new Error('TopologyEditor constructor: Failed to get 2d context from canvas');
        }
        this.initializing = true; // prevent autosave during initial load
        this.objects = [];
        this.selectedObject = null;
        this.currentTool = 'select';
        this.dragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.dragStartPos = null; // Track object's starting position for tap vs drag detection
        this.panning = false;
        this.panStart = { x: 0, y: 0 };
        
        // Load saved zoom and pan from localStorage
        const savedZoom = parseFloat(localStorage.getItem('topology_zoom'));
        this.zoom = (savedZoom && savedZoom >= 0.05 && savedZoom <= 3) ? savedZoom : 1;
        
        let savedPanOffset = { x: 0, y: 0 };
        try {
            const panData = localStorage.getItem('topology_panOffset');
            if (panData) savedPanOffset = JSON.parse(panData);
        } catch (e) {
            console.warn('Failed to parse saved pan offset:', e);
        }
        this.panOffset = { 
            x: typeof savedPanOffset.x === 'number' ? savedPanOffset.x : 0,
            y: typeof savedPanOffset.y === 'number' ? savedPanOffset.y : 0
        };
        
        console.log('📍 Pan offset restored:', this.panOffset);
        
        // Store default zoom and pan for reset button
        this.defaultZoom = 1;
        this.defaultPanOffset = { x: 0, y: 0 };
        this.linking = false;
        this.linkStart = null;
        this.spacePressed = false;
        this.deviceIdCounter = 0;
        this.linkIdCounter = 0;
        this.textIdCounter = 0;
        // REMOVED: Global MP counter - MPs are now numbered per-BUL, not globally
        this.selectedObjects = [];  // Multi-select support
        this.placingDevice = null;  // Track if we're placing a device
        this.longPressTimer = null; // For long press detection
        this.longPressDelay = 300;  // 300ms for long press (increased for trackpad sensitivity)
        this.lastDoubleClickTime = 0; // Track last double-click to prevent accidental MS after UL
        this.multiSelectMode = false;
        this.multiSelectInitialPositions = null;
        this.contextMenuVisible = false;
        this.rotatingText = false;
        this.resizingText = false;
        this.textRotationStartAngle = 0;
        this.textRotationStartRot = 0;
        this.textResizeStartSize = 0;
        this.textResizeStartDist = 0;
        this.rotatingDevice = null; // Device being rotated
        this.rotationStartAngle = 0; // Initial angle when rotation started
        this.rotationStartValue = 0; // Device rotation value when rotation started
        this.resizingDevice = null; // Device being resized
        this.resizeHandle = null; // Which resize handle is being used
        this.resizeStartRadius = 0; // Device radius when resize started
        this.resizeStartPos = null; // Mouse position when resize started
        this.resizeStartDist = 0; // Initial distance from center when resize started (for delta calculation)
        this.unboundLink = null; // Current unbound link being created
        this.stretchingLink = null; // Link endpoint being stretched
        this.stretchingEndpoint = null; // 'start' or 'end'
        this.stretchingConnectionPoint = false; // Whether stretching a connection point (merged ULs)
        this.textPlaced = false; // Track if text has been placed
        this.lastMousePos = null; // Last mouse position for drag detection
        this.deviceCounters = { router: 0, switch: 0 }; // Track device numbering
        this.resumePlacementAfterMarquee = null; // Store device type to resume after MS
        this.placementPending = null; // Track pending device placement
        this._currentDiscoveryJobId = null; // Track current DNAAS discovery job for cancellation
        this._discoveryAbortController = null; // AbortController for cancelling discovery
        this.textPlacementPending = null; // Track pending text placement (like devices)
        this.continuousTextPlacement = false; // Continuous TB placement mode (Place TBs button)
        this.editingText = null; // Text being edited in advanced editor
        this.lastPinchDistance = null; // For pinch zoom detection
        this.pinching = false; // Track if pinch gesture is active
        this.moveLongPressTimer = null; // Timer for long-press to enable movement
        this.selectionRectangle = null; // For marquee selection
        this.selectionRectStart = null; // Start position of marquee
        this.marqueeActive = false; // Track if marquee is active
        this.marqueeTimer = null; // Timer for marquee selection (50ms or instant on drag)
        this.ctrlPressed = false; // Track Ctrl/Cmd key state
        this.linkCurveMode = true; // Global toggle for link curve/magnetic repulsion mode
        this.globalCurveMode = 'auto'; // Global curve mode: 'auto' (magnetic repulsion), 'manual' (user-draggable), 'off'
        this.hoveredLinkMidpoint = null; // Track hover state for manual curve control handle { link, x, y }
        this.draggingCurveHandle = null; // Track active curve handle drag { link, startX, startY }
        this._potentialCPDrag = null; // Potential CP drag - starts if mouse moves while held
        this.curveMPs = false; // MPs (Merge Points) follow the curve path (OFF by default)
        this.linkContinuousMode = true; // Continuous linking mode - chain links together (ON by default)
        this.linkStickyMode = true; // Sticky links - links snap/attach to devices automatically (ON by default)
        this.linkULEnabled = true; // Unbound Links - allow double tap on screen to create UL (ON by default)
        this.linkStyle = 'solid'; // Link style: 'solid', 'dashed', 'arrow' (default: solid)
        // Load saved link width from localStorage, default to 2
        const savedLinkWidth = parseInt(localStorage.getItem('currentLinkWidth'));
        this.currentLinkWidth = (savedLinkWidth && savedLinkWidth >= 1 && savedLinkWidth <= 12) ? savedLinkWidth : 2;
        this.ulSnapDistance = 25; // Distance for UL endpoints to snap together (pixels) - increased for easier merging
        this.deviceNumbering = true; // Auto-number devices (NCP, NCP-2, etc. or just NCP for all)
        this.deviceCollision = false; // Prevent devices from overlapping (OFF by default)
        this.movableDevices = true; // Chain reaction - devices push each other on collision (ON by default)
        // Load saved device style from localStorage, default to 'circle'
        this.defaultDeviceStyle = localStorage.getItem('defaultDeviceStyle') || 'circle';
        // Load saved device label font from localStorage, default to 'Inter'
        this.defaultDeviceFontFamily = localStorage.getItem('defaultDeviceFontFamily') || 'Inter, sans-serif';
        // Default text font size (will be loaded from settings later)
        this.defaultFontSize = 14;
        this.magneticFieldStrength = 40; // Magnetic repulsion strength (1-80)
        this.magneticFieldUpdateTimer = null; // Throttle magnetic field updates
        this.gridZoomEnabled = localStorage.getItem('gridZoomEnabled') !== 'false';
        this.lastTwoFingerCenter = null; // Track two-finger gesture center
        this.altPressed = false; // Track Alt/Option key for quick link start
        this.backgroundClickCount = 0; // Track background clicks in multi-select mode
        this.darkMode = localStorage.getItem('darkMode') === 'true'; // Dark mode state
        
        // =========================================================================
        // COLOR DEFAULTS - CRITICAL DOCUMENTATION (Dec 2025)
        // =========================================================================
        // Link colors: this.darkMode ? '#ffffff' : '#666'
        //   - Dark mode: bright white (#ffffff) for visibility
        //   - Light mode: gray (#666)
        //   - Applied in: createUnboundLink, createLink, handleMouseDown (QL creation)
        //
        // Text background: this.darkMode ? '#1a1a1a' : '#f5f5f5'
        //   - Matches grid background color for seamless appearance
        //   - Applied in: createText, showTextEditor, drawText
        //
        // DO NOT hardcode '#666' or '#ffffff' without the darkMode check!
        // =========================================================================
        
        // Load recent colors with error handling
        try {
            this.recentColors = JSON.parse(localStorage.getItem('recentColors') || '[]');
        } catch (e) {
            console.warn('Failed to parse recentColors:', e);
            this.recentColors = [];
        }
        this.lastTapTime = 0; // Track last tap/click time for double-tap detection
        this._lastTapDevice = null; // Track last device tapped for double-tap detection
        
        // =========================================================================
        // SHAPE PROPERTIES (Jan 2026)
        // =========================================================================
        this.placingShape = null; // Current shape type being placed
        this.shapeIdCounter = 0; // Counter for shape IDs
        this.currentShapeType = 'rectangle'; // Default shape type
        this.shapeFillColor = '#3498db'; // Default fill color
        this.shapeFillOpacity = 0.5; // Default fill opacity (0-1 ratio)
        this.shapeFillEnabled = true; // Whether fill is enabled
        this.shapeStrokeColor = '#2c3e50'; // Default stroke color (darker for contrast)
        this.shapeStrokeWidth = 2; // Default stroke width
        this.shapeStrokeEnabled = true; // Whether stroke is enabled
        this.shapeSnapToGrid = false; // Snap shapes to grid
        this.resizingShape = null; // Shape being resized
        this.shapeResizeHandle = null; // Which resize handle is being used
        this.rotatingShape = null; // Shape being rotated
        this._lastTapPos = null; // Track last tap position for double-tap detection (handles slight movement)
        this._lastTapStartTime = 0; // Track when first tap started (to detect long press)
        this._lastMouseDownEventTime = 0; // Track last mousedown event timestamp to prevent duplicate pointer+mouse events
        this.doubleTapDelay = 350; // Max delay between taps (ms)
        this.doubleTapTolerance = 50; // Max distance between taps for double-tap (px) - accounts for slight movement
        this.maxTapDuration = 200; // Max duration for a tap to be considered for double-tap (ms) - prevents long press from being a tap
        this.lastBackgroundClickTime = 0; // Track background clicks for fast double-click UL placement
        this.fastDoubleClickDelay = 250; // Fast double-click must be < 250ms to place UL (prevents accidents)
        this.resumeModeAfterMarquee = null; // Store mode to return to after marquee selection
        this.showLinkTypeLabels = false; // Debug view: Show link type labels (QL/UL/BUL) above each link
        this.showLinkAttachments = true; // Global toggle: Show/hide text objects attached to links
        this.textAlwaysFaceUser = false; // Global toggle: Force all text boxes to stay at 0° rotation (readable)
        this.hoveredLink = null; // Track link under cursor for hover highlight
        
        // Copy/Paste Style Mode
        this.copiedStyle = null; // Stored style from copied object
        this.pasteStyleMode = false; // Whether in paste style mode
        this.csmsMode = false; // CS-MS mode: Copy Style + Multi-Select (long press in paste mode)
        this.shiftPressed = false; // Track Shift key for continuous paste mode
        
        // ENHANCED: Touchpad/Touch Gesture System
        this.gestureState = {
            fingerCount: 0,
            lastFingerCount: 0,
            gestureStartTime: 0,
            tapThreshold: 200, // ms - max time for tap vs swipe
            moveThreshold: 5, // px - max movement for tap vs drag
            gestureStartPos: null,
            gestureMoved: false,
            lastGestureType: null
        };
        
        // ENHANCED: Multi-pointer tracking for trackpad 3-finger tap detection
        this.activePointers = new Map(); // pointerId -> {x, y, startTime}
        this.threeFingerGesture = {
            active: false,
            startTime: 0,
            startPositions: [],
            moved: false
        };
        
        // 2D Smart Grid Coordinate System (non-intrusive to modes/tools)
        this.grid = {
            size: 50,                 // world units per grid square
            origin: { x: 0, y: 0 },   // (0,0) world origin
            showHud: true
        };
        
        // ========== PLATFORM DATA (from module) ==========
        // Data moved to topology-platform-data.js for maintainability
        // Inline fallback kept for safety (will be removed once fully tested)
        this.driveNetsPlatforms = this.driveNetsPlatforms || {
            // SA (Standalone) Platforms - From Confluence NCP Cheat Sheet
            SA: {
                category: 'SA',
                platforms: [
                    { 
                        displayName: 'NCP1 (SA-40C)', 
                        official: 'SA-40C', 
                        chip: 'J2', 
                        hwModel: 'S9700-53DX',
                        nif: { count: 40, speed: '100G' },
                        fif: { count: 13, speed: '400G' },
                        vendor: 'UFI',
                        interfaces: null // Generated on demand
                    },
                    { 
                        displayName: 'NCP2 (SA-10CD)', 
                        official: 'SA-10CD', 
                        chip: 'J2', 
                        hwModel: 'S9700-23D',
                        nif: { count: 10, speed: '400G' },
                        fif: { count: 13, speed: '400G' },
                        vendor: 'UFI',
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP3 (SA-36CD-S)', 
                        official: 'SA-36CD-S', 
                        chip: 'J2C+', 
                        hwModel: 'S9710-76D',
                        nif: { count: 36, speed: '400G' },
                        fif: { count: 40, speed: '400G' },
                        vendor: 'UFI',
                        syncE: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP3-SA (SA-36CD-S-SA)', 
                        official: 'SA-36CD-S-SA', 
                        chip: 'J2C+', 
                        hwModel: 'S9610-36D',
                        nif: { count: 36, speed: '400G' },
                        fif: null,
                        vendor: 'UFI',
                        syncE: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCPL (SA-64X12C-S)', 
                        official: 'SA-64X12C-S', 
                        chip: 'J2C', 
                        hwModel: 'S9701-82DC',
                        nif: [
                            { count: 64, speed: '10G' },
                            { count: 12, speed: '100G' }
                        ],
                        fif: { count: 6, speed: '400G' },
                        vendor: 'UFI',
                        syncE: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCPL-SA (SA-64X8C-S)', 
                        official: 'SA-64X8C-S', 
                        chip: 'J2C', 
                        hwModel: 'S9600-72XC',
                        nif: [
                            { count: 64, speed: '10G' },
                            { count: 8, speed: '100G' }
                        ],
                        fif: null,
                        vendor: 'UFI',
                        syncE: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP5 (SA-38E)', 
                        official: 'SA-38E', 
                        chip: 'J3AI', 
                        hwModel: 'ASA926-18XKE',
                        nif: { count: 18, speed: '800G' },
                        fif: { count: 20, speed: '800G' },
                        vendor: 'ACCTON',
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP6 (SA-40C8CD)', 
                        official: 'SA-40C8CD', 
                        chip: 'Q2C+', 
                        hwModel: 'S9610-48DX',
                        nif: [
                            { count: 4, speed: '10G' },
                            { count: 40, speed: '100G' },
                            { count: 8, speed: '400G' }
                        ],
                        fif: null,
                        vendor: 'UFI',
                        gearbox: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP6-S (SA-40C6CD-S)', 
                        official: 'SA-40C6CD-S', 
                        chip: 'Q2C+', 
                        hwModel: 'S9610-46DX',
                        nif: [
                            { count: 4, speed: '10G' },
                            { count: 40, speed: '100G' },
                            { count: 6, speed: '400G' }
                        ],
                        fif: null,
                        vendor: 'UFI',
                        gearbox: true,
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP9-S (SA-96X6C-S)', 
                        official: 'SA-96X6C-S', 
                        chip: 'Q2C', 
                        hwModel: 'S9601-102XC-R',
                        nif: [
                            { count: 96, speed: '10G' },
                            { count: 6, speed: '100G' }
                        ],
                        fif: null,
                        vendor: 'UFI',
                        interfaces: null
                    },
                    { 
                        displayName: 'NCP10 (SA-32E-S)', 
                        official: 'SA-32E-S', 
                        chip: 'Q3D', 
                        hwModel: 'S9620-32E',
                        nif: { count: 32, speed: '800G' },
                        fif: null,
                        vendor: 'UFI',
                        interfaces: null
                    },
                    { 
                        displayName: 'CS1 (SA-32CD)', 
                        official: 'SA-32CD', 
                        chip: 'CS1', 
                        hwModel: 'AS9286-32D',
                        nif: { count: 32, speed: '400G' },
                        fif: null,
                        vendor: 'ACCTON',
                        interfaces: null
                    }
                ]
            },
            // CL (Cluster) Platforms - From Confluence
            CL: {
                category: 'CL',
                platforms: [
                    { displayName: 'CL-16', official: 'CL-16', nodes: 16, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-32', official: 'CL-32', nodes: 32, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-48', official: 'CL-48', nodes: 48, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-49', official: 'CL-49', nodes: 49, ncpType: 'SA-64X12C-S', interfaces: null },
                    { displayName: 'CL-51', official: 'CL-51', nodes: 51, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-64', official: 'CL-64', nodes: 64, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-76', official: 'CL-76', nodes: 76, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-86', official: 'CL-86', nodes: 86, ncpType: 'SA-64X12C-S', interfaces: null },
                    { displayName: 'CL-96', official: 'CL-96', nodes: 96, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-134', official: 'CL-134', nodes: 134, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-153', official: 'CL-153', nodes: 153, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-192', official: 'CL-192', nodes: 192, ncpType: 'SA-40C', interfaces: null },
                    { displayName: 'CL-409', official: 'CL-409', nodes: 409, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'CL-768', official: 'CL-768', nodes: 768, ncpType: 'SA-40C', interfaces: null }
                ]
            },
            // NC-AI (Network Cloud AI) Clusters - From Confluence NC-AI Architecture
            'NC-AI': {
                category: 'NC-AI',
                platforms: [
                    { displayName: 'AI-72-400G', official: 'AI-72-400G', nifCount: 72, nifSpeed: '400G', gen: 1, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-72-800G-2', official: 'AI-72-800G-2', nifCount: 72, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-216-800G-2', official: 'AI-216-800G-2', nifCount: 216, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-576-800G-2', official: 'AI-576-800G-2', nifCount: 576, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-768-400G-1', official: 'AI-768-400G-1', nifCount: 768, nifSpeed: '400G', gen: 1, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'AI-1152-800G-2', official: 'AI-1152-800G-2', nifCount: 1152, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-2016-800G-2', official: 'AI-2016-800G-2', nifCount: 2016, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-2304-800G-2', official: 'AI-2304-800G-2', nifCount: 2304, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null },
                    { displayName: 'AI-8192-400G-1', official: 'AI-8192-400G-1', nifCount: 8192, nifSpeed: '400G', gen: 1, ncpType: 'SA-36CD-S', interfaces: null },
                    { displayName: 'AI-8192-400G-2', official: 'AI-8192-800G-2', nifCount: 8192, nifSpeed: '800G', gen: 2, ncpType: 'SA-38E', interfaces: null }
                ]
            },
            // DNAAS (Disaggregated Network As A Service) - NCM Fabric Devices
            // NCM = Network Cloud Module - building blocks for DNAAS fabric
            DNAAS: {
                category: 'DNAAS',
                platforms: [
                    { 
                        displayName: 'NCM-1600', 
                        official: 'NCM-1600', 
                        description: 'High-capacity NCM for large DNAAS deployments',
                        chip: 'J2', 
                        nif: { count: 48, speed: '100G' },
                        fif: { count: 16, speed: '400G' },
                        interfaces: null
                    },
                    { 
                        displayName: 'NCM-460', 
                        official: 'NCM-460', 
                        description: 'Mid-range NCM for medium DNAAS deployments',
                        chip: 'J2', 
                        nif: { count: 24, speed: '100G' },
                        fif: { count: 8, speed: '400G' },
                        interfaces: null
                    },
                    { 
                        displayName: 'NCM-200', 
                        official: 'NCM-200', 
                        description: 'Entry-level NCM for small DNAAS deployments',
                        chip: 'J', 
                        nif: { count: 12, speed: '100G' },
                        fif: { count: 4, speed: '400G' },
                        interfaces: null
                    },
                    { 
                        displayName: 'NCC-2500', 
                        official: 'NCC-2500', 
                        description: 'Network Cloud Controller - Large',
                        chip: 'Controller',
                        interfaces: null
                    },
                    { 
                        displayName: 'NCC-1500', 
                        official: 'NCC-1500', 
                        description: 'Network Cloud Controller - Medium',
                        chip: 'Controller',
                        interfaces: null
                    }
                ]
            }
        };
        
        // ========== TRANSCEIVER DATABASE ==========
        // Source: Confluence DN Devices Transceiver Templates (page 5624528975)
        // Real transceivers with manufacturer, part numbers, and platform support
        this.transceivers = {
            // 1G Transceivers (SFP form factor)
            '1G': [
                { name: '1000BASE-EX SFP', manufacturer: 'Molex', partNumber: '1837024404', type: 'SFP', reach: '40km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-96X6C-S'] },
                { name: '1000BASE-ZX SFP', manufacturer: 'ProLabs', partNumber: 'SFP-1000Base-ZX-ATT', type: 'SFP', reach: '80km', media: 'SMF', wavelength: '1550nm', platforms: ['SA-96X6C-S'] },
                { name: '1000BASE-LX BiDi', manufacturer: 'Ciena', partNumber: 'XCVR-B10U31', type: 'SFP', reach: '10km', media: 'SMF', wavelength: '1310nm TX/1550nm RX', platforms: ['SA-96X6C-S'] },
                { name: '1000BASE-EX BiDi', manufacturer: 'Ciena', partNumber: 'XCVR-A40U31', type: 'SFP', reach: '40km', media: 'SMF', wavelength: '1310nm TX/1550nm RX', platforms: ['SA-96X6C-S'] }
            ],
            // 10G Transceivers (SFP+ form factor)
            '10G': [
                { name: '10GBASE-LR SFP+', manufacturer: 'Coherent', partNumber: 'FTLX1475D3BCL', type: 'SFP+', reach: '10km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S', 'SA-64X12C-S'] },
                { name: '10GBASE-ER SFP+', manufacturer: 'ProLabs', partNumber: 'SFP-10Gbase-ER-ATT', type: 'SFP+', reach: '40km', media: 'SMF', wavelength: '1550nm', platforms: ['SA-96X6C-S'] },
                { name: '10GBASE-ZR SFP+', manufacturer: 'ProLabs', partNumber: 'SFP-10Gbase-ZR-ATT', type: 'SFP+', reach: '80km', media: 'SMF', wavelength: '1550nm', platforms: ['SA-96X6C-S'] },
                { name: '10GBASE-LR BiDi', manufacturer: 'Ciena', partNumber: 'XCVR-S10U27', type: 'SFP+', reach: '10km', media: 'SMF', wavelength: '1270nm TX/1330nm RX', platforms: ['SA-96X6C-S'] },
                { name: '10GBASE-ER BiDi', manufacturer: 'Ciena', partNumber: 'XCVR-S40U27', type: 'SFP+', reach: '40km', media: 'SMF', wavelength: '1270nm TX/1330nm RX', platforms: ['SA-96X6C-S'] },
                { name: 'Rate Adapter 1G-10G', manufacturer: 'Arista', partNumber: 'SFP-10G-RA-1G-LX', type: 'SFP+', reach: '5km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-40C6CD-S'] }
            ],
            // 100G Transceivers (QSFP28 form factor)
            '100G': [
                { name: '100GBASE-LR QSFP28', manufacturer: 'Molex', partNumber: '1064273710', type: 'QSFP28', reach: '10km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S', 'SA-32E-S', 'SA-36CD-S-SA'] },
                { name: '100GBASE-LR4 QSFP28', manufacturer: 'Coherent', partNumber: 'FTLC1154RDPL', type: 'QSFP28', reach: '10km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-LR4 QSFP28 Gen3', manufacturer: 'Coherent', partNumber: 'FTLC1156RDPL', type: 'QSFP28', reach: '10km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-LR4 QSFP28', manufacturer: 'Molex', partNumber: '1837104011', type: 'QSFP28', reach: '10km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-ER4 QSFP28', manufacturer: 'Nokia', partNumber: '3HE11239AA', type: 'QSFP28', reach: '30km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-ZR4 QSFP28', manufacturer: 'Nokia', partNumber: '3HE19472AA', type: 'QSFP28', reach: '80km', media: 'SMF', wavelength: 'LAN-WDM 1310nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] },
                { name: '100GBASE-ZR DCO QSFP28', manufacturer: 'Coherent', partNumber: 'FTLC3353S3PL1', type: 'QSFP28', reach: '80km+', media: 'SMF', wavelength: 'C-band 1550nm', platforms: ['SA-96X6C-S', 'SA-40C6CD-S'] }
            ],
            // 400G Transceivers (QSFP-DD form factor)
            '400G': [
                { name: '400GBASE-LR4 QSFP-DD', manufacturer: 'Coherent', partNumber: 'FTCD4323E3PCL-1Y', type: 'QSFP-DD', reach: '10km', media: 'SMF', wavelength: 'CWDM4 1310nm', platforms: ['SA-40C6CD-S', 'SA-32E-S', 'SA-36CD-S-SA'] },
                { name: '4x100G-LR1 PSM QSFP-DD', manufacturer: 'Innolight', partNumber: 'T-DP4CNL-N00', type: 'QSFP-DD', reach: '10km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-36CD-S-SA'] },
                { name: '400GBASE-ZR+ DCO QSFP-DD', manufacturer: 'Ciena', partNumber: '176-3370-9P0', type: 'QSFP-DD', reach: '600km+', media: 'SMF', wavelength: 'C-band 1550nm', platforms: ['SA-40C6CD-S', 'SA-32E-S', 'SA-36CD-S-SA'] },
                { name: '400GBASE-ZR+ DCO QSFP-DD', manufacturer: 'Coherent', partNumber: 'FTCD3323R1PCL-1Y', type: 'QSFP-DD', reach: '600km', media: 'SMF', wavelength: 'C-band 1550nm', platforms: ['SA-40C6CD-S', 'SA-32E-S', 'SA-36CD-S-SA'] },
                { name: '400GBASE-DR4 QSFP-DD', manufacturer: 'Generic', partNumber: 'QSFP-DD-400G-DR4', type: 'QSFP-DD', reach: '500m', media: 'SMF', wavelength: '1310nm', platforms: ['SA-36CD-S', 'SA-36CD-S-SA', 'SA-40C6CD-S', 'SA-32CD'] },
                { name: '400GBASE-FR4 QSFP-DD', manufacturer: 'Generic', partNumber: 'QSFP-DD-400G-FR4', type: 'QSFP-DD', reach: '2km', media: 'SMF', wavelength: 'CWDM', platforms: ['SA-36CD-S', 'SA-36CD-S-SA', 'SA-40C6CD-S', 'SA-32CD'] }
            ],
            // 800G Transceivers (OSFP / QSFP-DD800 form factor)
            '800G': [
                { name: '8x100G-LR1 PSM OSFP', manufacturer: 'Innolight', partNumber: 'T-DP8CNL-N00', type: 'QSFP-DD', reach: '10km', media: 'SMF', wavelength: '1310nm', platforms: ['SA-32E-S'] },
                { name: '2x400G-LR4-10 OSFP', manufacturer: 'Innolight', partNumber: 'T-DL8CNL-N00', type: 'QSFP-DD', reach: '10km', media: 'SMF', wavelength: 'CWDM4', platforms: ['SA-32E-S'] },
                { name: '800GBASE-DR8 OSFP', manufacturer: 'Generic', partNumber: 'OSFP-800G-DR8', type: 'OSFP', reach: '500m', media: 'SMF', wavelength: '1310nm', platforms: ['SA-38E', 'SA-32E-S'] },
                { name: '800GBASE-2xFR4 OSFP', manufacturer: 'Generic', partNumber: 'OSFP-800G-2xFR4', type: 'OSFP', reach: '2km', media: 'SMF', wavelength: 'CWDM', platforms: ['SA-38E', 'SA-32E-S'] },
                { name: '800GBASE-2xLR4 OSFP', manufacturer: 'Generic', partNumber: 'OSFP-800G-2xLR4', type: 'OSFP', reach: '10km', media: 'SMF', wavelength: 'LAN-WDM', platforms: ['SA-38E', 'SA-32E-S'] }
            ],
            // Management/Copper
            'MGMT': [
                { name: 'RJ45-1G', manufacturer: 'Generic', partNumber: 'RJ45-1G', type: 'RJ45', reach: '100m', media: 'Copper Cat6', wavelength: 'N/A', platforms: ['all'] },
                { name: 'RJ45-10G', manufacturer: 'Generic', partNumber: 'RJ45-10G', type: 'RJ45', reach: '30m', media: 'Copper Cat6a', wavelength: 'N/A', platforms: ['all'] }
            ]
        };
        
        // Map interface prefix to transceiver speed category
        this.interfaceToTransceiverMap = {
            'ge10': '10G',      // 10G interfaces
            'ge25': '25G',      // 25G interfaces  
            'ge100': '100G',    // 100G interfaces
            'ge400': '400G',    // 400G interfaces
            'ge800': '800G',    // 800G interfaces
            'mgmt': 'MGMT',     // Management interfaces
            'Bundle': '100G',   // Bundle/LAG (default to 100G)
            'Loopback': null,   // Loopback - no transceiver
        };
        
        // Get transceivers valid for a specific platform
        this.getTransceiversForPlatform = (speed, platformOfficial) => {
            const speedTransceivers = this.transceivers[speed] || [];
            return speedTransceivers.filter(t => 
                t.platforms.includes('all') || t.platforms.includes(platformOfficial)
            );
        };
        
        // Scrollbar tracking
        this.draggingScrollbar = null; // 'vertical' or 'horizontal' or null
        this.scrollbarDragStart = null;
        
        // Auto-save debouncing
        this.autoSaveTimer = null;
        
        // Slider update optimization
        this.sliderUpdatePending = false;
        
        // Undo/Redo system - MUST initialize before saveState()
        this.history = []; // History stack
        this.historyIndex = -1; // Current position in history
        this.maxHistorySize = 50; // Maximum history entries
        
        // Double-tap detection for touch devices
        this.lastTouchTapTime = 0;
        this.lastTouchTapPos = null;
        this.doubleTapThreshold = 300; // ms
        this.doubleTapDistanceThreshold = 30; // pixels
        
        // Clipboard for copy/paste
        this.clipboard = [];
        this.clipboardCentroid = null;
        
        this.showAngleMeter = false; // Angle meter disabled by default
        this.autoCreateInterfaceTB = true; // Auto-create interface text boxes when saving link details
        
        this.setupCanvas();
        this.setupEventListeners();
        this.setupToolbar();
        
        // File/session state
        this.currentFile = null; // logical filename in localStorage namespace
        this.filesKey = 'topology_files_v1';
        this.recentKey = 'topology_recent_v1';

        // Try to load from autosave (file system disabled for now)
        console.log('=== INITIALIZATION START ===');
        console.log('BEFORE loadAutoSave, objects count:', this.objects.length);
        
        // TEMPORARILY DISABLED: File system functions not yet implemented
        // const recent = localStorage.getItem(this.recentKey);
        // if (recent) {
        //     const name = recent;
        //     const files = JSON.parse(localStorage.getItem(this.filesKey) || '{}');
        //     if (files[name]) {
        //         this.loadFromFileEntry(name, files[name]);
        //         this.currentFile = name;
        //     } else {
        //         this.loadAutoSave();
        //     }
        // } else {
        //     this.loadAutoSave();
        // }
        
        this.loadAutoSave();
        
        // ========== INITIALIZE MODULAR COMPONENTS ==========
        // These modules are loaded from separate files for better maintainability
        // All module initialization uses ErrorBoundary for graceful degradation
        
        // Safe module initializer with stats tracking
        const safeInit = (name, fn, fallback) => {
            const startTime = performance.now();
            try {
                const result = window.ErrorBoundary ? 
                    ErrorBoundary.safeModuleInit(name, fn, fallback) :
                    fn();
                    
                // Track successful load
                if (window.ModuleStats && result) {
                    ModuleStats.register(name, performance.now() - startTime);
                }
                return result;
            } catch(e) {
                console.error(`[${name}]`, e);
                if (window.ModuleStats) {
                    ModuleStats.markFailed(name, e.message);
                }
                return fallback ? fallback() : null;
            }
        };
        
        // Minimal event bus fallback
        const createFallbackEventBus = () => ({
            _listeners: {},
            on(e, cb) { if (!this._listeners[e]) this._listeners[e] = []; this._listeners[e].push(cb); return () => this.off(e, cb); },
            off(e, cb) { if (this._listeners[e]) this._listeners[e] = this._listeners[e].filter(c => c !== cb); },
            emit(e, d) { if (this._listeners[e]) this._listeners[e].forEach(cb => { try { cb(d); } catch(err) { console.error('Event handler error:', err); } }); },
            once(e, cb) { const wrapper = (d) => { this.off(e, wrapper); cb(d); }; this.on(e, wrapper); }
        });
        
        // Event bus for module-to-module communication
        this.events = safeInit('TopologyEventBus', 
            () => window.TopologyEventBus ? new TopologyEventBus() : createFallbackEventBus(),
            createFallbackEventBus
        );
        
        // Platform data (DriveNets platforms and transceivers)
        this.platformData = safeInit('PlatformData', () => {
            if (!window.PlatformData) {
                console.warn('PlatformData module not loaded - using empty data');
                return { platforms: {}, transceivers: {}, interfaceToTransceiverMap: {} };
            }
            const pd = new PlatformData();
            // Create aliases for backward compatibility with existing code
            this.driveNetsPlatforms = pd.platforms;
            this.transceivers = pd.transceivers;
            this.interfaceToTransceiverMap = pd.interfaceToTransceiverMap;
            this.getTransceiversForPlatform = (speed, platform) => pd.getTransceiversForPlatform(speed, platform);
            return pd;
        }, () => ({ platforms: {}, transceivers: {}, interfaceToTransceiverMap: {} }));
        
        // Geometry utilities are static (window.TopologyGeometry)
        if (window.TopologyGeometry) {
            console.log('[OK] TopologyGeometry module available');
        }
        
        // File manager (auto-save, save, load, export)
        this.files = safeInit('FileManager', () => {
            if (!window.FileManager) return null;
            return new FileManager(this);
        });
        
        // Drawing manager (canvas rendering)
        this.drawing = safeInit('DrawingManager', () => {
            if (!window.DrawingManager) return null;
            return new DrawingManager(this);
        });
        
        // Text manager (text creation, editing, styling)
        this.text = safeInit('TextManager', () => {
            if (!window.TextManager) return null;
            return new TextManager(this);
        });
        
        // Shape manager (shape creation, drawing, selection)
        this.shapes = safeInit('ShapeManager', () => {
            if (!window.ShapeManager) return null;
            return new ShapeManager(this);
        });
        
        // Device manager (device creation, selection, collision)
        this.devices = safeInit('DeviceManager', () => {
            if (!window.DeviceManager) return null;
            return new DeviceManager(this);
        });
        
        // Link manager (links, BUL chains, merging)
        this.links = safeInit('LinkManager', () => {
            if (!window.LinkManager) return null;
            return new LinkManager(this);
        });
        
        // UI manager (toolbars, panels)
        this.ui = safeInit('UIManager', () => {
            if (!window.UIManager) return null;
            return new UIManager(this);
        });
        
        // Menu manager (context menus)
        this.menus = safeInit('MenuManager', () => {
            if (!window.MenuManager) return null;
            return new MenuManager(this);
        });
        
        // Minimap manager (use minimapMgr to avoid conflict with this.minimap object)
        this.minimapMgr = safeInit('MinimapManager', () => {
            if (!window.MinimapManager) return null;
            return new MinimapManager(this);
        });
        
        // Initialize momentum engine (sliding/inertia system)
        this.momentum = safeInit('MomentumEngine', () => {
            if (!window.createMomentumEngine) return null;
            return window.createMomentumEngine(this);
        });
        
        // Initialize InputManager state machine
        // Store references to original handlers before InputManager wraps them
        this._originalHandleMouseDown = this.handleMouseDown?.bind(this);
        this._originalHandleMouseMove = this.handleMouseMove?.bind(this);
        this._originalHandleMouseUp = this.handleMouseUp?.bind(this);
        this._originalHandleKeyDown = this.handleKeyDown?.bind(this);
        this._originalHandleKeyUp = this.handleKeyUp?.bind(this);
        this._originalHandleWheel = this.handleWheel?.bind(this);
        this._originalHandleDoubleClick = this.handleDoubleClick?.bind(this);
        this._originalHandleContextMenu = this.handleContextMenu?.bind(this);
        
        this.input = safeInit('InputManager', () => {
            if (!window.InputManager) return null;
            return new InputManager(this);
        });
        
        // Link editor modal (link details panel)
        this.linkEditor = safeInit('LinkEditorModal', () => {
            if (!window.LinkEditorModal) return null;
            return new LinkEditorModal(this);
        });
        
        // Group manager (object grouping)
        this.groups = safeInit('GroupManager', () => {
            if (!window.GroupManager) return null;
            return new GroupManager(this);
        });
        
        // Toolbar manager (toolbar setup and handlers)
        this.toolbarMgr = safeInit('ToolbarManager', () => {
            if (!window.ToolbarManager) return null;
            return new ToolbarManager(this);
        });
        
        console.log('AFTER loadAutoSave, objects count:', this.objects.length);
        console.log('Current objects array:', this.objects);

        // Redraw after loading auto-save to show restored topology
        this.draw();

        // Remove splash screen immediately after first paint
        try {
            const splash = document.getElementById('app-splash');
            if (splash) {
                splash.style.opacity = '0';
                setTimeout(() => splash.remove(), 500);
            }
        } catch (_) {}

        // Defer non-critical managers to after first paint
        requestAnimationFrame(() => {
            this.dnaas = safeInit('DnaasManager', () => {
                if (!window.DnaasManager) return null;
                return new DnaasManager(this);
            });

            this.networkMapper = safeInit('NetworkMapperManager', () => {
                if (!window.NetworkMapperManager) return null;
                return new NetworkMapperManager(this);
            });
            if (this.networkMapper) {
                this.networkMapper.setupPanel();
            }
        });
        console.log('AFTER draw, objects count:', this.objects.length);

        // CRITICAL FIX: NEVER call saveState on initial load
        // Create history entry directly without triggering auto-save
        const state = {
            objects: JSON.parse(JSON.stringify(this.objects)),
            deviceIdCounter: this.deviceIdCounter,
            linkIdCounter: this.linkIdCounter,
            textIdCounter: this.textIdCounter,
            deviceCounters: { ...this.deviceCounters }
        };
        
        // Ensure history exists before pushing
        if (!this.history) {
            this.history = [];
        }
        if (this.historyIndex === undefined) {
            this.historyIndex = -1;
        }
        
        this.history.push(state);
        this.historyIndex = 0;
        console.log('Created initial history entry for', this.objects.length, 'objects (no auto-save triggered)');
        console.log('Initial history state - index:', this.historyIndex, 'length:', this.history.length);
        console.log('=== INITIALIZATION COMPLETE ===');
        
        this.updateUndoRedoButtons();
        this.updateStepCounter();
        this.updateModeIndicator(); // Show initial mode
        this.updateZoomIndicator();
        this.updateHud();
        
        // Apply dark mode if enabled
        if (this.darkMode) {
            document.body.classList.add('dark-mode');
        }
        
        this.initializing = false; // enable autosave after initial load completes (MUST be before debugger check)
        
        // Enable periodic auto-save and check for crash recovery
        if (this.files) {
            this.files.enableAutoSave();
            
            // Check for recovery after a short delay (let UI settle first)
            setTimeout(() => {
                this.files.checkForRecovery();
            }, 500);
        }
        
        // Sync ALL toggle buttons with their state (ensure button shows correct state)
        // This runs AFTER debugger is initialized
        setTimeout(() => {
            this.syncAllToggles();
            
            // Restore BD Panel if it was visible before refresh
            this.restoreBDPanelIfNeeded();
            
            // Sync slide distance control visibility with momentum state
            const slideControl = document.getElementById('slide-distance-control');
            if (slideControl && this.momentum) {
                slideControl.style.display = this.momentum.enabled ? 'block' : 'none';
            }
            
            // Run input diagnostics for trackpad/input troubleshooting
            this.runInputDiagnostics();
        }, 100); // Small delay to ensure debugger is ready
    }
    
    // ========== INTERFACE GENERATION HELPERS ==========
    // Generate interfaces based on NCP platform type
    // ========== INTERFACE GENERATION ==========
    // Naming convention from Confluence (L2 Resources Analysis - page 5948964869):
    // ge10-0/0/{port}   - 10G interfaces
    // ge100-0/0/{port}  - 100G interfaces
    // ge400-0/0/{port}  - 400G interfaces
    // ge800-0/0/{port}  - 800G interfaces
    // Breakout: ge{speed}-0/0/{parent}/{child}
    
    generateInterfaces(platformOfficial) {
        if (window.InterfaceGenerator) {
            return window.InterfaceGenerator.generateInterfaces(platformOfficial);
        }
        return ['ge100-0/0/0', 'ge100-0/0/1', 'mgmt0', 'Loopback0'];
    }
    
    generateClusterInterfaces(clusterPlatform) {
        if (window.InterfaceGenerator) {
            return window.InterfaceGenerator.generateClusterInterfaces(clusterPlatform);
        }
        return [];
    }
    
    generateAIInterfaces(aiPlatform) {
        if (window.InterfaceGenerator) {
            return window.InterfaceGenerator.generateAIInterfaces(aiPlatform);
        }
        return [];
    }
    
    getInterfacesForPlatform(platformOfficial, category) {
        if (window.InterfaceGenerator) {
            return window.InterfaceGenerator.getInterfacesForPlatform(this, platformOfficial, category);
        }
        return [];
    }
    
    generateDNAASInterfaces(platform) {
        if (window.InterfaceGenerator) {
            return window.InterfaceGenerator.generateDNAASInterfaces(platform);
        }
        return [];
    }
    
    // Get platform by official name
    getPlatformByOfficial(officialName) {
        // Use module if available (cleaner API)
        if (this.platformData) {
            const platform = this.platformData.getPlatform(officialName);
            if (platform) {
                // Find category for backward compatibility
                for (const [catName, catData] of Object.entries(this.platformData.platforms)) {
                    if (catData.platforms.some(p => p.official === officialName)) {
                        return { ...platform, category: catName };
                    }
                }
                return platform;
            }
        }
        // Fallback to inline data
        for (const category of Object.values(this.driveNetsPlatforms)) {
            for (const platform of category.platforms) {
                if (platform.official === officialName) {
                    return { ...platform, category: category.category };
                }
            }
        }
        return null;
    }
    
    // Get all platforms in a category
    getPlatformsByCategory(categoryName) {
        // Use module if available
        if (this.platformData) {
            return this.platformData.getPlatformsByCategory(categoryName);
        }
        // Fallback to inline data
        const category = this.driveNetsPlatforms[categoryName];
        return category ? category.platforms : [];
    }
    
    // Get transceivers for an interface name
    getTransceiversForInterface(interfaceName) {
        if (!interfaceName) return [];
        
        // Extract prefix from interface name (e.g., 'ge100' from 'ge100-0/0/0')
        // Handle various formats: ge100-0/0/0, lag-1, mgmt0, loopback-0, ai-eth-0/0/0
        const lowerName = interfaceName.toLowerCase();
        
        // Check each known prefix
        for (const [prefix, speedCategory] of Object.entries(this.interfaceToTransceiverMap)) {
            if (lowerName.startsWith(prefix)) {
                if (!speedCategory) return []; // e.g., loopback has no transceiver
                return this.transceivers[speedCategory] || [];
            }
        }
        
        // Fallback: try to extract speed from interface name
        if (lowerName.includes('100')) return this.transceivers['100G'] || [];
        if (lowerName.includes('400')) return this.transceivers['400G'] || [];
        if (lowerName.includes('800')) return this.transceivers['800G'] || [];
        if (lowerName.includes('25')) return this.transceivers['25G'] || [];
        if (lowerName.includes('10')) return this.transceivers['10G'] || [];
        
        return [];
    }
    
    // ═══════════════════════════════════════════════════════════════════
    // CONFIG PARSING - Parse device configs for interface auto-complete
    // ═══════════════════════════════════════════════════════════════════
    
    // Parse a device config file and extract interfaces with VLANs
    async parseDeviceConfig(deviceName) {
        if (!deviceName) return { interfaces: [], subInterfaces: [] };
        
        // Normalize device name (remove YOR_ prefix if present, handle common patterns)
        const normalizedName = deviceName.replace(/^YOR_/i, '').replace(/-/g, '-');
        
        // Use API endpoint to fetch device config
        const apiPath = `/api/config/${encodeURIComponent(normalizedName)}/running`;
        
        try {
            // Fetch config via API
            const response = await fetch(apiPath);
            if (!response.ok) {
                // Don't spam console for expected missing configs (DNAAS devices)
                if (response.status !== 404) {
                    console.warn(`Config API error for ${deviceName}: ${response.status}`);
                }
                return { interfaces: [], subInterfaces: [], error: 'Config not found' };
            }
            
            const data = await response.json();
            if (data.config) {
                return this.extractInterfacesFromConfig(data.config);
            } else if (data.error) {
                return { interfaces: [], subInterfaces: [], error: data.error };
            }
            return { interfaces: [], subInterfaces: [], error: 'No config in response' };
        } catch (error) {
            // Silently handle network errors for missing devices
            return { interfaces: [], subInterfaces: [], error: error.message };
        }
    }
    
    extractInterfacesFromConfig(configText) {
        if (window.InterfaceGenerator) {
            return window.InterfaceGenerator.extractInterfacesFromConfig(configText);
        }
        return { interfaces: [], subInterfaces: [] };
    }
    
    getSubInterfacesWithVlan(configData, vlanId) {
        if (window.InterfaceGenerator) {
            return window.InterfaceGenerator.getSubInterfacesWithVlan(configData, vlanId);
        }
        return [];
    }
    
    extractVlanFromSubInterface(subInterfaceName) {
        if (window.InterfaceGenerator) {
            return window.InterfaceGenerator.extractVlanFromSubInterface(subInterfaceName);
        }
        return null;
    }
    
    validateVlanMatch(subInterfaceA, subInterfaceB) {
        if (window.InterfaceGenerator) {
            return window.InterfaceGenerator.validateVlanMatch(subInterfaceA, subInterfaceB);
        }
        return { match: false, vlanA: null, vlanB: null, reason: 'Module not loaded' };
    }
    
    // Get transceiver names for dropdown
    getTransceiverOptionsForInterface(interfaceName) {
        const transceivers = this.getTransceiversForInterface(interfaceName);
        return transceivers.map(t => t.name);
    }
    
    setupCanvas() {
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // ResizeObserver catches layout changes from toolbar collapse/expand
        const container = this.canvas.parentElement;
        if (container && typeof ResizeObserver !== 'undefined') {
            this._canvasResizeObserver = new ResizeObserver(() => {
                this.resizeCanvas();
            });
            this._canvasResizeObserver.observe(container);
        }
    }
    
    resizeCanvas() {
        const container = this.canvas.parentElement;
        const dpr = window.devicePixelRatio || 1;
        this.dpr = dpr;
        const w = container.clientWidth;
        const h = container.clientHeight;
        this.canvas.width = Math.round(w * dpr);
        this.canvas.height = Math.round(h * dpr);
        this.canvas.style.width = w + 'px';
        this.canvas.style.height = h + 'px';
        this.draw();
    }

    get canvasW() { return this.canvas.width / (this.dpr || 1); }
    get canvasH() { return this.canvas.height / (this.dpr || 1); }
    
    // SMOOTH MOVEMENT: Linear interpolation for smooth position updates
    lerp(current, target, factor = 0.15) {
        if (window.MathUtils) {
            return window.MathUtils.lerp(current, target, factor);
        }
        const diff = target - current;
        if (Math.abs(diff) < 0.5) return target;
        return current + diff * factor;
    }
    
    // SMOOTH MOVEMENT: Interpolate a point (x, y) toward target
    lerpPoint(current, target, factor = 0.15) {
        if (window.MathUtils) {
            return window.MathUtils.lerpPoint(current, target, factor);
        }
        return { x: this.lerp(current.x, target.x, factor), y: this.lerp(current.y, target.y, factor) };
    }
    
    runInputDiagnostics() {
        // Comprehensive input system diagnostics for trackpad troubleshooting
        const diagnostics = [];
        
        // Check browser and OS
        const ua = navigator.userAgent;
        const isMac = /Mac|iPhone|iPod|iPad/.test(ua);
        const isSafari = /Safari/.test(ua) && !/Chrome/.test(ua);
        const isChrome = /Chrome/.test(ua);
        const isFirefox = /Firefox/.test(ua);
        
        diagnostics.push(`OS: ${isMac ? 'macOS' : 'Other'}`);
        diagnostics.push(`Browser: ${isSafari ? 'Safari' : isChrome ? 'Chrome' : isFirefox ? 'Firefox' : 'Other'}`);
        
        // Check Pointer Events support
        const hasPointerEvents = !!window.PointerEvent;
        diagnostics.push(`${hasPointerEvents ? '[+]' : '[-]'} Pointer Events API: ${hasPointerEvents ? 'Supported' : 'NOT supported'}`);
        
        // Check Touch Events support
        const hasTouchEvents = 'ontouchstart' in window;
        diagnostics.push(`${hasTouchEvents ? '[+]' : '[-]'} Touch Events: ${hasTouchEvents ? 'Supported' : 'NOT supported'}`);
        
        // Check canvas properties
        const canvasStyles = window.getComputedStyle(this.canvas);
        const touchAction = canvasStyles.touchAction;
        const pointerEvents = canvasStyles.pointerEvents;
        diagnostics.push(`🎨 Canvas touch-action: "${touchAction}"`);
        diagnostics.push(`🎨 Canvas pointer-events: "${pointerEvents}"`);
        
        // Check if canvas is receiving events
        const canvasRect = this.canvas.getBoundingClientRect();
        diagnostics.push(`Canvas size: ${canvasRect.width}x${canvasRect.height}`);
        
        // Log to debugger if available
        if (this.debugger) {
            this.debugger.logInfo('═══ INPUT SYSTEM DIAGNOSTICS ═══');
            diagnostics.forEach(msg => this.debugger.logInfo(msg));
            this.debugger.logInfo('═══════════════════════════════');
            
            if (isMac && hasPointerEvents) {
                this.debugger.logSuccess('[macOS] Pointer Events - Trackpad should work!');
                this.debugger.logInfo('👉 Try clicking on the canvas now - you should see events in the debugger');
            } else if (isMac && !hasPointerEvents) {
                this.debugger.logWarning('[WARN] macOS but no Pointer Events - using mouse events fallback');
            } else {
                this.debugger.logInfo('ℹ️ Input system initialized - click canvas to test');
            }
        }
        
        // Also log to console
        console.log('═══ INPUT SYSTEM DIAGNOSTICS ═══');
        diagnostics.forEach(msg => console.log(msg));
        console.log('═══════════════════════════════');
    }
    
    setupEventListeners() {
        // File menu removed — all operations in Topologies dropdown
        
        // ENHANCED: Pointer Events API + Mouse Events (both for maximum compatibility!)
        // macOS trackpads work better with BOTH event types active
        if (window.PointerEvent) {
            // Modern browsers support PointerEvents - better for touchpads
            // Wrap with ErrorBoundary for crash protection
            const safePointerDown = window.ErrorBoundary ? 
                ErrorBoundary.wrapEventHandler((e) => this.handlePointerDown(e), this, 'pointerdown') :
                (e) => this.handlePointerDown(e);
            const safePointerMove = window.ErrorBoundary ? 
                ErrorBoundary.wrapEventHandler((e) => this.handlePointerMove(e), this, 'pointermove') :
                (e) => this.handlePointerMove(e);
            const safePointerUp = window.ErrorBoundary ? 
                ErrorBoundary.wrapEventHandler((e) => this.handlePointerUp(e), this, 'pointerup') :
                (e) => this.handlePointerUp(e);
            
            this.canvas.addEventListener('pointerdown', safePointerDown);
            document.addEventListener('pointermove', safePointerMove);
            document.addEventListener('pointerup', safePointerUp);
            this.canvas.addEventListener('pointercancel', safePointerUp);
            console.log('[OK] Pointer Events API enabled (move/up on document for off-canvas drag)');
        }
        
        // ALWAYS add mouse events as well (macOS trackpads often use these!)
        // Wrap with ErrorBoundary for crash protection
        const safeMouseDown = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleMouseDown(e), this, 'mousedown') :
            (e) => this.handleMouseDown(e);
        const safeMouseMove = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleMouseMove(e), this, 'mousemove') :
            (e) => this.handleMouseMove(e);
        const safeMouseUp = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleMouseUp(e), this, 'mouseup') :
            (e) => this.handleMouseUp(e);
        
        this.canvas.addEventListener('mousedown', safeMouseDown);
        document.addEventListener('mousemove', safeMouseMove);
        document.addEventListener('mouseup', safeMouseUp);
        console.log('[OK] Mouse events enabled (move/up on document for off-canvas drag)');
        
        // ENHANCED: Global mouse tracking (works even over debugger!)
        document.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.lastMouseScreen = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
            
            // Also update world position if over canvas area (even if obscured by debugger)
            if (e.clientX >= rect.left && e.clientX <= rect.right && 
                e.clientY >= rect.top && e.clientY <= rect.bottom) {
                this.lastMousePos = this.getMousePos(e);
            }
        });
        console.log('[OK] Global mouse tracking enabled (works over debugger)');
        
        // Context menu, double-click, wheel - wrap with ErrorBoundary
        const safeContextMenu = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleContextMenu(e), this, 'contextmenu') :
            (e) => this.handleContextMenu(e);
        const safeDoubleClick = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleDoubleClick(e), this, 'dblclick') :
            (e) => this.handleDoubleClick(e);
        const safeWheel = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleWheel(e), this, 'wheel') :
            (e) => this.handleWheel(e);
        
        this.canvas.addEventListener('contextmenu', safeContextMenu);
        this.canvas.addEventListener('dblclick', safeDoubleClick);
        this.canvas.addEventListener('wheel', safeWheel, { passive: false });
        
        // Touch events for mobile devices (still needed for iOS/Android)
        // Wrap with ErrorBoundary for crash protection
        const safeTouchStart = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleTouchStart(e), this, 'touchstart') :
            (e) => this.handleTouchStart(e);
        const safeTouchMove = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleTouchMove(e), this, 'touchmove') :
            (e) => this.handleTouchMove(e);
        const safeTouchEnd = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleTouchEnd(e), this, 'touchend') :
            (e) => this.handleTouchEnd(e);
        
        this.canvas.addEventListener('touchstart', safeTouchStart, { passive: false });
        this.canvas.addEventListener('touchmove', safeTouchMove, { passive: false });
        this.canvas.addEventListener('touchend', safeTouchEnd);
        
        // Keyboard events — capture phase so R/Cmd+R refresh is handled before host (avoids Save As dialog)
        // Wrap with ErrorBoundary for crash protection
        const safeKeyDown = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleKeyDown(e), this, 'keydown') :
            (e) => this.handleKeyDown(e);
        const safeKeyUp = window.ErrorBoundary ? 
            ErrorBoundary.wrapEventHandler((e) => this.handleKeyUp(e), this, 'keyup') :
            (e) => this.handleKeyUp(e);
        
        document.addEventListener('keydown', safeKeyDown, true);
        document.addEventListener('keyup', safeKeyUp);
        
        // Note: Browser zoom is allowed - only canvas zoom is handled by the app
        
        // REMOVED: beforeunload handler - auto-save already handles all changes
        // No need to prompt user or force-save on refresh since changes are saved immediately
        
        // Scrollbar events
        this.setupScrollbars();
        
        // Minimap for navigation
        this.setupMinimap();
    }
    
    // ===== Minimap for Navigation (delegated to MinimapModule) =====
    setupMinimap() {
        if (window.MinimapModule) {
            return window.MinimapModule.setup(this);
        }
    }
    
    startMinimapDragLoop() {
        if (window.MinimapModule) {
            return window.MinimapModule.startDragLoop(this);
        }
    }
    
    stopMinimapDragLoop() {
        if (window.MinimapModule) {
            return window.MinimapModule.stopDragLoop(this);
        }
    }
    
    updateMinimapDragTarget(e) {
        if (window.MinimapModule) {
            return window.MinimapModule.updateDragTarget(this, e);
        }
    }
    
    navigateFromMinimapDrag(e) {
        if (window.MinimapModule) {
            return window.MinimapModule.navigateFromDrag(this, e);
        }
    }
    
    toggleMinimap() {
        if (window.MinimapModule) {
            return window.MinimapModule.toggle(this);
        }
    }
    
    getMinimapBounds() {
        if (window.MinimapModule) {
            return window.MinimapModule.getBounds(this);
        }
        return null;
    }
    
    navigateFromMinimap(e) {
        // Legacy method - redirects to new smooth drag system
        this.navigateFromMinimapDrag(e);
    }
    
    renderMinimap() {
        if (window.MinimapRender) {
            return window.MinimapRender.renderMinimap(this);
        }
    }
    
    getTopologyBounds() {
        if (window.MinimapModule) {
            return window.MinimapModule.getTopologyBounds(this);
        }
        return null;
    }
    
    // ===== Scrollbars (delegated to ScrollbarsModule) =====
    setupScrollbars() {
        if (window.ScrollbarsModule) {
            return window.ScrollbarsModule.setup(this);
        }
    }
    
    updateScrollbars() {
        if (window.ScrollbarsModule) {
            return window.ScrollbarsModule.update(this);
        }
    }
    
    setupToolbar() {
        if (window.ToolbarSetup) {
            window.ToolbarSetup.setupToolbar(this);
            window.ToolbarSetup.buildHelpersSection(this);
        }
    }
    
    getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        
        // Screen position in CSS/logical pixels
        const screenX = e.clientX - rect.left;
        const screenY = e.clientY - rect.top;
        
        // CRITICAL FIX: Account for the half-pixel offset added in draw()
        // Drawing does: translate(round(pan) + 0.5, round(pan) + 0.5)
        // So we need to subtract that 0.5 offset here
        const adjustedPanX = Math.round(this.panOffset.x) + 0.5;
        const adjustedPanY = Math.round(this.panOffset.y) + 0.5;
        
        // Transform: subtract adjusted pan offset, then divide by zoom
        const worldX = (screenX - adjustedPanX) / this.zoom;
        const worldY = (screenY - adjustedPanY) / this.zoom;
        
        // Debug: Log transform if values seem wrong
        if (this.debugger && this._debugTransform) {
            const mag = Math.sqrt(worldX * worldX + worldY * worldY);
            if (mag > 2000) {
                this.debugger.logError(`[WARN] getMousePos() returned huge value: (${worldX.toFixed(0)}, ${worldY.toFixed(0)})`);
                this.debugger.logInfo(`Screen: (${screenX}, ${screenY}), Pan: (${this.panOffset.x}, ${this.panOffset.y}), Zoom: ${this.zoom}`);
            }
        }
        
        return {
            x: worldX,
            y: worldY
        };
    }
    
    // Convert world coordinates to screen (CSS) coordinates
    worldToScreen(worldPos) {
        const rect = this.canvas.getBoundingClientRect();
        
        // Account for the half-pixel offset added in draw()
        const adjustedPanX = Math.round(this.panOffset.x) + 0.5;
        const adjustedPanY = Math.round(this.panOffset.y) + 0.5;
        
        // Transform: multiply by zoom, then add pan offset (logical pixels)
        const canvasX = worldPos.x * this.zoom + adjustedPanX;
        const canvasY = worldPos.y * this.zoom + adjustedPanY;
        
        // Convert logical canvas coordinates to screen (CSS) coordinates
        const screenX = canvasX + rect.left;
        const screenY = canvasY + rect.top;
        
        return { x: screenX, y: screenY };
    }
    
    // Create a custom cursor from an emoji
    createEmojiCursor(emoji, hotspotX = 0, hotspotY = 0) {
        const size = 32;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        
        // Draw emoji
        ctx.font = `${size - 4}px serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(emoji, size / 2, size / 2);
        
        // Convert to data URL and create cursor
        const dataUrl = canvas.toDataURL('image/png');
        return `url(${dataUrl}) ${hotspotX} ${hotspotY}, auto`;
    }
    
    getTouchPos(e) {
        const touch = e.touches[0] || e.changedTouches[0];
        const rect = this.canvas.getBoundingClientRect();
        
        const screenX = touch.clientX - rect.left;
        const screenY = touch.clientY - rect.top;
        
        // FIXED: Correct inverse of drawing transform
        return {
            x: (screenX - this.panOffset.x) / this.zoom,
            y: (screenY - this.panOffset.y) / this.zoom
        };
    }
    
    // ============================================================================
    // POINTER EVENT HANDLERS (for laptop touchpads and unified input)
    // ============================================================================
    
    handlePointerDown(e) {
        // Pointer events work for mouse, touchpad, and pen
        // ENHANCED: Detect input device type for better logging
        
        const inputType = this.detectInputType(e);
        
        // ENHANCED: Track multiple pointers for 3-finger tap detection
        this.activePointers.set(e.pointerId, {
            x: e.clientX,
            y: e.clientY,
            startX: e.clientX,
            startY: e.clientY,
            startTime: Date.now(),
            pressure: e.pressure
        });
        
        // Check for 3-finger gesture start
        if (this.activePointers.size === 3 && !this.threeFingerGesture.active) {
            this.threeFingerGesture.active = true;
            this.threeFingerGesture.startTime = Date.now();
            this.threeFingerGesture.moved = false;
            this.threeFingerGesture.startPositions = Array.from(this.activePointers.values()).map(p => ({
                x: p.x,
                y: p.y
            }));
            
            if (this.debugger) {
                this.debugger.logInfo(`3-FINGER gesture started (${this.activePointers.size} pointers active)`);
            }
        }
        
        // Reduced logging: Only log input type for specific debugging (disabled by default)
        // Uncomment below if you need to debug input detection issues
        // if (this.debugger && this.activePointers.size === 1) {
        //     if (inputType === 'trackpad') {
        //         this.debugger.logAction(`🖐️ TRACKPAD tap: pressure=${e.pressure.toFixed(2)}`);
        //     } else if (inputType === 'mouse') {
        //         this.debugger.logSuccess(`🖱️ MOUSE click: button=${e.button}`);
        //     }
        // }
        
        // Store input type for tracking
        this._lastInputType = inputType;
        
        // Delegate to mouse handler only for single pointer (not during multi-touch)
        if ((e.pointerType === 'mouse' || e.pointerType === 'touch' || e.pointerType === 'pen') && this.activePointers.size === 1) {
            // Set flag to prevent duplicate logging when mousedown event also fires
            this._skipMouseLog = true;
            this.handleMouseDown(e);
        }
    }
    
    handlePointerMove(e) {
        // Track pointer movement for gesture detection
        if (this.activePointers.has(e.pointerId)) {
            const pointer = this.activePointers.get(e.pointerId);
            pointer.x = e.clientX;
            pointer.y = e.clientY;
            
            // Check if 3-finger gesture has moved significantly
            if (this.threeFingerGesture.active && !this.threeFingerGesture.moved) {
                const dx = Math.abs(e.clientX - pointer.startX);
                const dy = Math.abs(e.clientY - pointer.startY);
                const moved = Math.max(dx, dy);
                
                if (moved > this.gestureState.moveThreshold) {
                    this.threeFingerGesture.moved = true;
                    if (this.debugger) {
                        this.debugger.logWarning(`3-finger gesture moved ${Math.round(moved)}px - not a tap`);
                    }
                }
            }
        }
    }
    
    handlePointerUp(e) {
        // Remove pointer from tracking
        if (this.activePointers.has(e.pointerId)) {
            this.activePointers.delete(e.pointerId);
            
            // DISABLED: 3-finger tap functionality - replaced with right-click on device and double-click on screen
            // Right-click on device → Enter link mode
            // Double-click on screen → Create unbound link
            if (this.threeFingerGesture.active && this.activePointers.size === 0) {
                // Reset 3-finger gesture state but don't process
                this.threeFingerGesture.active = false;
                this.threeFingerGesture.moved = false;
                this.threeFingerGesture.startPositions = [];
                
                if (this.debugger) {
                    this.debugger.logInfo(`3-finger gesture detected but disabled (use right-click on device or double-click on screen)`);
                }
            }
        }
    }
    
    detectInputType(e) {
        // Detect if input is from mouse, trackpad, or pen based on PointerEvent properties
        // macOS specific detection logic
        
        if (e.pointerType === 'pen') {
            return 'pen';
        }
        
        if (e.pointerType === 'touch') {
            return 'touch';
        }
        
        if (e.pointerType === 'mouse') {
            // On macOS, trackpad often reports as 'mouse' type
            // Use pressure and other hints to distinguish
            
            // Trackpad hints:
            // - Often has pressure = 0 or 0.5 (not 1.0)
            // - May have fractional pressure values
            // - Width/height may be present (finger contact area)
            
            const hasPressure = e.pressure > 0 && e.pressure < 1;
            const hasContactArea = (e.width && e.width > 1) || (e.height && e.height > 1);
            const hasButtons = e.buttons !== undefined;
            
            // Heuristic: if it has variable pressure or contact area, likely trackpad
            if (hasPressure || hasContactArea) {
                return 'trackpad';
            }
            
            return 'mouse';
        }
        
        return 'unknown';
    }
    
    handlePointerMove(e) {
        // Handle pointer movement (touchpad, mouse, pen)
        if (e.pointerType === 'mouse' || e.pointerType === 'touch' || e.pointerType === 'pen') {
            this.handleMouseMove(e);
        }
    }
    
    handlePointerUp(e) {
        // Handle pointer release (touchpad, mouse, pen)
        if (e.pointerType === 'mouse' || e.pointerType === 'touch' || e.pointerType === 'pen') {
            this.handleMouseUp(e);
        }
    }
    
    
    // ============================================================================
    // MOUSE EVENT HANDLERS - Delegated to topology-mouse.js module
    // ============================================================================
    
    handleMouseDown(e) {
        if (window.MouseHandler) {
            return window.MouseHandler.handleMouseDown(this, e);
        }
    }
    
    handleMouseMove(e) {
        if (window.MouseHandler) {
            return window.MouseHandler.handleMouseMove(this, e);
        }
    }
    
    handleMouseUp(e) {
        if (window.MouseHandler) {
            return window.MouseHandler.handleMouseUp(this, e);
        }
    }
    
    
    getNextDeviceLabel(deviceType) {
        // If numbering is disabled, always return base name
        if (!this.deviceNumbering) {
            return deviceType === 'router' ? 'NCP' : 'S';
        }
        
        // Numbering enabled - increment counter
        this.deviceCounters[deviceType] = (this.deviceCounters[deviceType] || 0) + 1;
        const count = this.deviceCounters[deviceType];
        
        if (count === 1) {
            return deviceType === 'router' ? 'NCP' : 'S';
        } else {
            return deviceType === 'router' ? `NCP-${count}` : `S${count}`;
        }
    }
    
    isDeviceNameUnique(name) {
        const existing = this.objects.find(obj => 
            obj.type === 'device' && obj.label === name
        );
        return !existing;
    }
    
    updateDeviceCounters() {
        // Recalculate device counters based on existing devices
        this.deviceCounters = { router: 0, switch: 0 };
        this.objects.forEach(obj => {
            if (obj.type === 'device') {
                const label = obj.label || '';
                if (obj.deviceType === 'router') {
                    if (label === 'NCP' || label === 'R') {
                        this.deviceCounters.router = Math.max(this.deviceCounters.router, 1);
                    } else {
                        // Match both NCP-2 format and old R2 format
                        const matchNCP = label.match(/^NCP-(\d+)$/);
                        const matchR = label.match(/^R(\d+)$/);
                        if (matchNCP) {
                            const num = parseInt(matchNCP[1]);
                            this.deviceCounters.router = Math.max(this.deviceCounters.router, num);
                        } else if (matchR) {
                            const num = parseInt(matchR[1]);
                            this.deviceCounters.router = Math.max(this.deviceCounters.router, num);
                        }
                    }
                } else if (obj.deviceType === 'switch') {
                    if (label === 'S') {
                        this.deviceCounters.switch = Math.max(this.deviceCounters.switch, 1);
                    } else {
                        const match = label.match(/^S(\d+)$/);
                        if (match) {
                            const num = parseInt(match[1]);
                            this.deviceCounters.switch = Math.max(this.deviceCounters.switch, num);
                        }
                    }
                }
            }
        });
    }
    
    handleContextMenu(e) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.handleContextMenu(this, e);
        }
    }
    
    // Helper to safely set element display
    safeSetDisplay(id, display) {
        const el = document.getElementById(id);
        if (el) el.style.display = display;
    }
    
    showBackgroundContextMenu(x, y) {
        if (window.ContextMenus) {
            return window.ContextMenus.showBackgroundContextMenu(this, x, y);
        }
    }
    
    showBulkContextMenu(x, y) {
        if (window.ContextMenus) {
            return window.ContextMenus.showBulkContextMenu(this, x, y);
        }
    }
    
    handleDoubleClick(e) {
        if (window.MouseHandler) {
            return window.MouseHandler.handleDoubleClick(this, e);
        }
    }
    
    handleWheel(e) {
        e.preventDefault();

        // Cache rect -- getBoundingClientRect triggers layout; reuse within burst
        if (!this._wheelRect || !this._wheelRectTs || performance.now() - this._wheelRectTs > 500) {
            this._wheelRect = this.canvas.getBoundingClientRect();
            this._wheelRectTs = performance.now();
        }
        const rect = this._wheelRect;
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        const isPinchZoom = e.ctrlKey || e.metaKey;

        if (isPinchZoom) {
            const worldX = (mouseX - this.panOffset.x) / this.zoom;
            const worldY = (mouseY - this.panOffset.y) / this.zoom;
            const scaleFactor = Math.exp(-e.deltaY * 0.004);
            this.zoom = Math.max(0.05, Math.min(3, this.zoom * scaleFactor));
            this.panOffset.x = mouseX - worldX * this.zoom;
            this.panOffset.y = mouseY - worldY * this.zoom;
        } else {
            this.panOffset.x -= e.deltaX;
            this.panOffset.y -= e.deltaY;
        }

        // Schedule a single rAF that draws AND updates lightweight UI.
        // _viewportOnly tells draw() to skip O(n^2) position recalc -- nothing moved in world space.
        this._viewportOnly = true;
        if (!this._wheelRafId) {
            this._wheelRafId = requestAnimationFrame(() => {
                this._wheelRafId = null;
                this.draw();
                this.updateZoomIndicator();
                this.updateScrollbars();
            });
        }

        // Debounce expensive / infrequent work (popups, HUD, localStorage, toolbar restore)
        if (this._wheelIdleTimer) clearTimeout(this._wheelIdleTimer);
        this._wheelIdleTimer = setTimeout(() => {
            this._wheelIdleTimer = null;
            this._wheelRect = null;
            this.hideAllPopups();
            this.savePanOffset();
            this.lastMousePos = this.getMousePos(e);
            this.updateHud();
            if (this.selectedObject) {
                if (this.selectedObject.type === 'device') {
                    this.showDeviceSelectionToolbar(this.selectedObject);
                } else if (this.selectedObject.type === 'link' || this.selectedObject.type === 'unbound') {
                    this.showLinkSelectionToolbar(this.selectedObject);
                } else if (this.selectedObject.type === 'text') {
                    this.showTextSelectionToolbar(this.selectedObject);
                }
            }
        }, 150);
    }
    
    updateZoomIndicator() {
        const zoomPercent = Math.round(this.zoom * 100);
        
        // Cache DOM references (queried once, reused across rapid zoom events)
        if (!this._zoomIndEl) this._zoomIndEl = document.getElementById('zoom-indicator');
        if (!this._zoomIndHudEl) this._zoomIndHudEl = document.getElementById('zoom-indicator-hud');

        if (this._zoomIndEl) this._zoomIndEl.textContent = `${zoomPercent}%`;
        if (this._zoomIndHudEl) this._zoomIndHudEl.textContent = `${zoomPercent}%`;
        
        // Throttle localStorage write -- no need for 60 writes/sec during zoom
        if (!this._zoomSaveTimer) {
            this._zoomSaveTimer = setTimeout(() => {
                this._zoomSaveTimer = null;
                localStorage.setItem('topology_zoom', this.zoom.toString());
            }, 300);
        }
    }
    
    savePanOffset() {
        // Save pan offset to localStorage for persistence across page refreshes
        // THROTTLED: Only save every 200ms to avoid excessive writes
        if (this._panSaveTimeout) {
            clearTimeout(this._panSaveTimeout);
        }
        
        this._panSaveTimeout = setTimeout(() => {
            const panData = {
                x: this.panOffset.x,
                y: this.panOffset.y
            };
            localStorage.setItem('topology_panOffset', JSON.stringify(panData));
            console.log('📍 Pan offset saved:', panData);
            this._panSaveTimeout = null;
        }, 200);
    }
    
    // ===== Smart Grid helpers and HUD =====
    worldToGrid(world) {
        const s = this.grid.size;
        return {
            x: (world.x - this.grid.origin.x) / s,
            y: (world.y - this.grid.origin.y) / s
        };
    }
    
    gridToWorld(grid) {
        const s = this.grid.size;
        return {
            x: grid.x * s + this.grid.origin.x,
            y: grid.y * s + this.grid.origin.y
        };
    }
    
    updateHud(mouseWorld) {
        if (!this.grid.showHud) return;
        const hud = document.getElementById('hud');
        if (!hud) return;
        const p = mouseWorld || this.lastMousePos;
        let text = '';
        if (p) {
            const g = this.worldToGrid(p);
            const gx = Math.round(g.x);
            const gy = Math.round(g.y);
            const dx = gx;
            const dy = gy;
            const r = Math.round(Math.sqrt(dx*dx + dy*dy));
            text = `Grid: (${gx}, ${gy}) | Δ: ${dx}, ${dy} | r: ${r}`;
            
            // Only run hit detection when idle (not during drag/resize/rotate)
            const busy = this.dragging || this.resizingDevice || this.rotatingDevice ||
                this.panning || this.isDrawingLink || this.draggingCurveHandle ||
                this.draggingAttachedText || this.draggingBULChain || this.selectionBox ||
                this.stretchingLink || this.rotatingShape || this.resizingText;
            if (!busy) {
                const hoveredObject = this.findObjectAt(p.x, p.y);
                if (hoveredObject && (hoveredObject.type === 'link' || hoveredObject.type === 'unbound')) {
                    const linkInfo = this.getLinkAttachmentInfo(hoveredObject);
                    if (linkInfo) {
                        text += ` | ${linkInfo}`;
                    }
                }
            }
        } else {
            text = 'Grid: (–, –)';
        }
        const modeText = (this.currentMode || 'base').toUpperCase();
        hud.textContent = `${text} | Mode: ${modeText}`;
    }
    
    // Get attachment information for a link to display in HUD
    getLinkAttachmentInfo(link) {
        if (!link) return null;
        
        let linkType = '';
        let attachments = [];
        
        // Determine link type
        if (link.type === 'link') {
            linkType = 'QL';
        } else if (link.type === 'unbound') {
            if (link.mergedWith || link.mergedInto) {
                linkType = 'BUL';
            } else {
                linkType = 'UL';
            }
        }
        
        // Check curve status
        const curveEnabled = link.curveOverride !== undefined ? link.curveOverride : this.linkCurveMode;
        if (curveEnabled && this.magneticFieldStrength > 0) {
            linkType += ' (Curved)';
        }
        
        // Get attachments for this link and entire chain if BUL
        if (link.type === 'unbound' && (link.mergedWith || link.mergedInto)) {
            // BUL - get all connected devices from entire chain
            const connectedInfo = this.getAllConnectedDevices(link);
            if (connectedInfo.devices.length > 0) {
                attachments = connectedInfo.devices.map(d => d.label || 'Device');
            }
            if (connectedInfo.devices.length < 2) {
                // Some endpoints are free TPs
                const freeCount = 2 - connectedInfo.devices.length;
                for (let i = 0; i < freeCount; i++) {
                    attachments.push('Free TP');
                }
            }
        } else {
            // Single link - check device1 and device2
            if (link.device1) {
                const d1 = this.objects.find(o => o.id === link.device1);
                attachments.push(d1 ? (d1.label || 'Device') : 'Device');
            } else if (link.type === 'unbound') {
                attachments.push('Free TP');
            }
            
            if (link.device2) {
                const d2 = this.objects.find(o => o.id === link.device2);
                attachments.push(d2 ? (d2.label || 'Device') : 'Device');
            } else if (link.type === 'unbound') {
                attachments.push('Free TP');
            }
        }
        
        if (attachments.length === 0) {
            return `${linkType}`;
        }
        
        return `${linkType}: ${attachments.join(' ↔ ')}`;
    }
    
    // Find attached text boxes that need a gap in the link line
    getAttachedTextGaps(link) {
        const gaps = [];
        
        // Find all text objects attached to this link with _onLinkLine flag
        const attachedTexts = this.objects.filter(obj => 
            obj.type === 'text' && 
            obj.linkId === link.id && 
            obj._onLinkLine === true
        );
        
        for (const textObj of attachedTexts) {
            // Calculate text dimensions
            this.ctx.save();
            this.ctx.font = `${textObj.fontSize}px Arial`;
            const metrics = this.ctx.measureText(textObj.text || 'Text');
            const textWidth = metrics.width;
            this.ctx.restore();
            
            // Get the t value for this text position
            const t = textObj.linkAttachT !== undefined ? textObj.linkAttachT : 0.5;
            
            // Calculate gap in terms of t (parametric position along link)
            // Add padding around text
            const padding = 6;
            
            // Get link length to convert pixel width to t-space
            let linkStart = link.start;
            let linkEnd = link.end;
            
            if (link.device1) {
                const d1 = this.objects.find(o => o.id === link.device1);
                if (d1) {
                    const targetX = link.device2 ? (this.objects.find(o => o.id === link.device2)?.x || link.end.x) : link.end.x;
                    const targetY = link.device2 ? (this.objects.find(o => o.id === link.device2)?.y || link.end.y) : link.end.y;
                    const angle = Math.atan2(targetY - d1.y, targetX - d1.x);
                    linkStart = this.getLinkConnectionPoint(d1, angle);
                }
            }
            if (link.device2) {
                const d2 = this.objects.find(o => o.id === link.device2);
                if (d2) {
                    const targetX = link.device1 ? (this.objects.find(o => o.id === link.device1)?.x || link.start.x) : link.start.x;
                    const targetY = link.device1 ? (this.objects.find(o => o.id === link.device1)?.y || link.start.y) : link.start.y;
                    const angle = Math.atan2(targetY - d2.y, targetX - d2.x);
                    linkEnd = this.getLinkConnectionPoint(d2, angle);
                }
            }
            
            const linkLength = Math.sqrt(
                Math.pow(linkEnd.x - linkStart.x, 2) + 
                Math.pow(linkEnd.y - linkStart.y, 2)
            );
            
            if (linkLength > 0) {
                const gapHalfWidth = (textWidth / 2 + padding) / linkLength;
                gaps.push({
                    tStart: Math.max(0, t - gapHalfWidth),
                    tEnd: Math.min(1, t + gapHalfWidth),
                    textObj: textObj
                });
            }
        }
        
        return gaps;
    }
    
    // Calculate maximum width for a link before it overlaps with neighbor links
    getMaxLinkWidth(link) {
        if (!link) return 12; // Default max
        
        // Get devices for this link
        let device1Id = link.device1;
        let device2Id = link.device2;
        
        // For unbound links, check if endpoints are attached
        if (link.type === 'unbound') {
            // If not connected to two devices, no overlap concern with parallel links
            if (!device1Id || !device2Id) {
                return 12; // Default max for unattached links
            }
        }
        
        if (!device1Id || !device2Id) return 12;
        
        // Find all links between these two devices
        const connectedLinks = this.objects.filter(obj => {
            if (obj.type === 'link' && obj.device1 && obj.device2) {
                return (obj.device1 === device1Id && obj.device2 === device2Id) ||
                       (obj.device1 === device2Id && obj.device2 === device1Id);
            }
            if (obj.type === 'unbound' && obj.device1 && obj.device2) {
                return (obj.device1 === device1Id && obj.device2 === device2Id) ||
                       (obj.device1 === device2Id && obj.device2 === device1Id);
            }
            return false;
        }).sort((a, b) => {
            const idA = parseInt(a.id.split('_')[1]) || 0;
            const idB = parseInt(b.id.split('_')[1]) || 0;
            return idA - idB;
        });
        
        // If only one link, no overlap concern
        if (connectedLinks.length <= 1) {
            return 12; // Default max
        }
        
        // Find this link's index in the sorted list
        const thisIndex = connectedLinks.findIndex(l => l.id === link.id);
        if (thisIndex === -1) return 12;
        
        // Calculate offset for this link
        const getOffset = (index) => {
            if (index === 0) return 0;
            const magnitude = Math.ceil(index / 2) * 20;
            const direction = (index % 2 === 1) ? 1 : -1;
            return magnitude * direction;
        };
        
        const thisOffset = getOffset(thisIndex);
        
        // Find the closest neighbor offset
        let minGap = Infinity;
        
        for (let i = 0; i < connectedLinks.length; i++) {
            if (i === thisIndex) continue;
            
            const neighborOffset = getOffset(i);
            const gap = Math.abs(thisOffset - neighborOffset);
            
            // Account for the neighbor's width too
            const neighborWidth = connectedLinks[i].width !== undefined ? 
                connectedLinks[i].width : this.currentLinkWidth;
            
            // The available gap is the offset distance minus half of neighbor's width
            const availableGap = gap - (neighborWidth / 2);
            
            if (availableGap < minGap) {
                minGap = availableGap;
            }
        }
        
        // Max width is twice the min gap (since our width extends half on each side)
        // Subtract a small buffer to ensure no overlap
        const maxWidth = Math.max(1, Math.floor((minGap * 2) - 2));
        
        // Cap at reasonable maximum (slider max is 12)
        return Math.min(maxWidth, 12);
    }
    
    getDistance(touch1, touch2) {
        if (window.MathUtils) {
            return window.MathUtils.getDistance(touch1, touch2);
        }
        const dx = touch2.clientX - touch1.clientX;
        const dy = touch2.clientY - touch1.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    // ===== Touch Handling (delegated to TouchHandler) =====
    handleTouchStart(e) {
        if (window.TouchHandler) {
            return window.TouchHandler.handleTouchStart(this, e);
        }
    }
    
    process3FingerTap() {
        if (window.TouchHandler) {
            return window.TouchHandler.process3FingerTap(this);
        }
    }
    
    handleTouchMove(e) {
        if (window.TouchHandler) {
            return window.TouchHandler.handleTouchMove(this, e);
        }
    }
    
    handleTouchEnd(e) {
        if (window.TouchHandler) {
            return window.TouchHandler.handleTouchEnd(this, e);
        }
    }
    
    toggle4FingerMode() {
        if (window.TouchHandler) {
            return window.TouchHandler.toggle4FingerMode(this);
        }
    }
    
    getTwoFingerCenter(touch1, touch2) {
        if (window.MathUtils) {
            return window.MathUtils.getTwoFingerCenter(touch1, touch2);
        }
        return {
            x: (touch1.clientX + touch2.clientX) / 2,
            y: (touch1.clientY + touch2.clientY) / 2
        };
    }
    
    zoomIn() {
        const cursorX = this.lastMouseScreen?.x || (this.canvasW / 2);
        const cursorY = this.lastMouseScreen?.y || (this.canvasH / 2);
        
        const S_old = this.zoom;
        const S_new = Math.max(0.05, Math.min(3, S_old * 1.10)); // 10% multiplicative step
        
        const worldX = (cursorX - this.panOffset.x) / S_old;
        const worldY = (cursorY - this.panOffset.y) / S_old;
        
        this.zoom = S_new;
        this.panOffset.x = cursorX - worldX * S_new;
        this.panOffset.y = cursorY - worldY * S_new;
        this.savePanOffset();
        
        this.updateZoomIndicator();
        this.updateScrollbars();
        this.requestDraw();
        this.updateHud();
    }
    
    zoomAtCursor(cursorScreen, zoomDelta) {
        // FIXED: Zoom at cursor position - keeps point under cursor fixed
        const k = 0.0015;                      // sensitivity
        const scaleFactor = Math.exp(zoomDelta * k);

        const S_old = this.zoom;
        const S_new = Math.max(0.05, Math.min(3, S_old * scaleFactor)); // Clamp zoom

        // Check if zoom was clamped
        const wasClamped = (S_old * scaleFactor < 0.05 || S_old * scaleFactor > 3);
        
        if (this.debugger && wasClamped) {
            if (S_new === 0.05) {
                this.debugger.logWarning('Zoom limit reached: 5% (min)');
            } else if (S_new === 3) {
                this.debugger.logWarning('Zoom limit reached: 300% (max)');
            }
        }

        // Get world position at cursor BEFORE zoom
        const worldX = (cursorScreen.x - this.panOffset.x) / S_old;
        const worldY = (cursorScreen.y - this.panOffset.y) / S_old;
        
        // Update zoom
        this.zoom = S_new;
        
        // Adjust pan so world position stays at cursor (zoom at cursor)
        this.panOffset.x = cursorScreen.x - worldX * S_new;
        this.panOffset.y = cursorScreen.y - worldY * S_new;
        this.savePanOffset();
    }
    
    zoomOut() {
        const cursorX = this.lastMouseScreen?.x || (this.canvasW / 2);
        const cursorY = this.lastMouseScreen?.y || (this.canvasH / 2);
        
        const S_old = this.zoom;
        const S_new = Math.max(0.05, Math.min(3, S_old / 1.10)); // 10% multiplicative step
        
        const worldX = (cursorX - this.panOffset.x) / S_old;
        const worldY = (cursorY - this.panOffset.y) / S_old;
        
        this.zoom = S_new;
        this.panOffset.x = cursorX - worldX * S_new;
        this.panOffset.y = cursorY - worldY * S_new;
        this.savePanOffset();
        
        this.updateZoomIndicator();
        this.updateScrollbars();
        this.requestDraw();
        this.updateHud();
    }
    
    resetZoom() {
        // Reset to default zoom and pan (original map location)
        this.zoom = this.defaultZoom;
        this.panOffset.x = this.defaultPanOffset.x;
        this.panOffset.y = this.defaultPanOffset.y;
        
        if (this.debugger) {
            const zoomPercent = Math.round(this.zoom * 100);
            this.debugger.logInfo(`Zoom reset to ${zoomPercent}%`);
        }
        
        this.updateZoomIndicator();
        this.savePanOffset();
        this.updateScrollbars();
        this.requestDraw();
        this.updateHud();
    }
    
    setDefaultView() {
        // Set current view as the default for reset button
        this.defaultZoom = this.zoom;
        this.defaultPanOffset = { x: this.panOffset.x, y: this.panOffset.y };
        
        if (this.debugger) {
            const zoomPercent = Math.round(this.zoom * 100);
            this.debugger.logSuccess(`📌 Default view set: ${zoomPercent}% at (${Math.round(this.panOffset.x)}, ${Math.round(this.panOffset.y)})`);
        }
    }
    
    // Center the view on all devices in the topology
    centerOnDevices() {
        // Find all devices
        const devices = this.objects.filter(obj => obj.type === 'device');
        
        if (devices.length === 0) {
            if (this.debugger) {
                this.debugger.logWarning('🎯 No devices to center on');
            }
            return;
        }
        
        // Calculate bounding box of all devices
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        for (const device of devices) {
            const x = device.x || 0;
            const y = device.y || 0;
            const size = device.size || 60;
            
            minX = Math.min(minX, x - size);
            minY = Math.min(minY, y - size);
            maxX = Math.max(maxX, x + size);
            maxY = Math.max(maxY, y + size);
        }
        
        // Calculate center of all devices
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        
        // Calculate the view center (canvas center in world coordinates)
        const canvasCenterX = this.canvasW / 2;
        const canvasCenterY = this.canvasH / 2;
        
        // Set pan offset to center the devices at CURRENT zoom level
        // Formula: screenPos = (worldPos * zoom) + panOffset
        // To center: panOffset = canvasCenter - (worldCenter * zoom)
        this.panOffset.x = canvasCenterX - (centerX * this.zoom);
        this.panOffset.y = canvasCenterY - (centerY * this.zoom);
        
        // Optionally fit to view if topology is larger than canvas
        const boundsWidth = maxX - minX;
        const boundsHeight = maxY - minY;
        const padding = 100; // Extra padding around devices
        
        const scaleX = (this.canvasW - padding * 2) / boundsWidth;
        const scaleY = (this.canvasH - padding * 2) / boundsHeight;
        const fitZoom = Math.min(scaleX, scaleY, 1.5); // Cap at 1.5x zoom
        
        // Only adjust zoom if topology doesn't fit at current zoom
        if (fitZoom < this.zoom && fitZoom > 0.05) {
            this.zoom = Math.max(0.05, fitZoom);
            // Recalculate pan after zoom change using correct formula
            this.panOffset.x = canvasCenterX - (centerX * this.zoom);
            this.panOffset.y = canvasCenterY - (centerY * this.zoom);
        }
        
        if (this.debugger) {
            this.debugger.logSuccess(`🎯 Centered on ${devices.length} device${devices.length > 1 ? 's' : ''}`);
        }
        
        this.updateZoomIndicator();
        this.savePanOffset();
        this.updateScrollbars();
        this.requestDraw();
        this.updateHud();
    }
    
    // ==================== KEYBOARD HANDLING ====================
    // Implementation moved to topology-keyboard.js (~315 lines extracted)
    
    handleKeyDown(e) {
        if (window.KeyboardHandler) {
            window.KeyboardHandler.handleKeyDown(this, e);
        }
    }
    
    handleKeyUp(e) {
        if (window.KeyboardHandler) {
            window.KeyboardHandler.handleKeyUp(this, e);
        }
    }
    
    updateCursor() {
        if (this.spacePressed) {
            this.canvas.style.cursor = 'move';
        } else if (this.pasteStyleMode && this.copiedStyle) {
            // FIXED: Keep copy cursor while in paste style mode (CS-MS)
            this.canvas.style.cursor = 'copy';
        } else if (this.placingDevice) {
            this.canvas.style.cursor = 'crosshair';
        } else if (this.currentTool === 'link') {
            this.canvas.style.cursor = 'crosshair';
        } else if (this.currentTool === 'text' && this.textPlacementPending) {
            this.canvas.style.cursor = 'text';
        } else {
            this.canvas.style.cursor = 'default';
        }
    }
    
    findObjectAt(x, y) {
        if (window.ObjectDetection) {
            return window.ObjectDetection.findObjectAt(this, x, y);
        }
    }
    
    findTextAt(x, y) {
        if (window.ObjectDetection) {
            return window.ObjectDetection.findTextAt(this, x, y);
        }
    }
    
    findRotationHandle(device, x, y) {
        if (window.ObjectDetection) {
            return window.ObjectDetection.findRotationHandle(this, device, x, y);
        }
    }
    
    findTextHandle(textObj, x, y) {
        if (window.ObjectDetection) {
            return window.ObjectDetection.findTextHandle(this, textObj, x, y);
        }
    }
    
    findTerminalButton(device, x, y) {
        if (window.ObjectDetection) {
            return window.ObjectDetection.findTerminalButton(this, device, x, y);
        }
    }
    
    // Open SSH terminal to device - delegated to ObjectDetection
    openTerminalToDevice(device) {
        if (window.ObjectDetection && window.ObjectDetection.openTerminalToDevice) {
            return window.ObjectDetection.openTerminalToDevice(this, device);
        }
    }
    
    // Open SSH URL - delegated to ObjectDetection
    _openSshUrl(url) {
        if (window.ObjectDetection && window.ObjectDetection._openSshUrl) {
            return window.ObjectDetection._openSshUrl(this, url);
        }
    }
    
    // Safe clipboard write - delegated to ObjectDetection
    _safeClipboardWrite(text) {
        if (window.ObjectDetection && window.ObjectDetection._safeClipboardWrite) {
            return window.ObjectDetection._safeClipboardWrite(text);
        }
        // Fallback (safeClipboardWrite works on HTTP; raw API requires HTTPS/localhost)
        return (window.safeClipboardWrite || (() => Promise.reject(new Error('Clipboard not available'))))(text).catch(() => {});
    }
    
    _checkLinkHit(x, y, obj) {
        if (window.LinkGeometry) {
            return window.LinkGeometry._checkLinkHit(this, x, y, obj);
        }
    }
    
    showSplitHelperHint() {
        if (window.NotificationManager) {
            return window.NotificationManager.showSplitHelperHint(this);
        }
    }
    
    showSplitPaneNotification(sshCommand, password) {
        if (window.NotificationManager) {
            return window.NotificationManager.showSplitPaneNotification(this, sshCommand, password);
        }
    }
    
    showItermSetupHint() {
        if (window.NotificationManager) {
            return window.NotificationManager.showItermSetupHint(this);
        }
    }
    
    // Show a temporary notification toast
    showNotification(message, type = 'info') {
        if (window.NotificationManager) {
            return window.NotificationManager.showNotification(this, message, type);
        }
    }
    
    findResizeHandle(device, x, y) {
        if (device.type !== 'device') return null;

        const deviceRotation = (device.rotation || 0) * Math.PI / 180;
        const hitboxSize = 14 / this.zoom;
        const handleOffset = 10 / this.zoom;

        const bounds = this.getDeviceBounds(device);
        const r = device.radius;

        // 4 cardinal resize handles only (N, E, S, W)
        const resizeHandles = [];
        switch (bounds.type) {
            case 'classic': {
                const top = bounds.top - handleOffset;
                const bottom = bounds.bottom + handleOffset;
                const cy = bounds.centerY;
                const hw = bounds.width / 2 + handleOffset;
                resizeHandles.push({ pos: { x: 0, y: top }, name: 'n' });
                resizeHandles.push({ pos: { x: hw, y: cy }, name: 'e' });
                resizeHandles.push({ pos: { x: 0, y: bottom }, name: 's' });
                resizeHandles.push({ pos: { x: -hw, y: cy }, name: 'w' });
                break;
            }
            case 'rectangle': {
                const hh = bounds.height / 2 + handleOffset;
                const hw = bounds.width / 2 + handleOffset;
                resizeHandles.push({ pos: { x: 0, y: -hh }, name: 'n' });
                resizeHandles.push({ pos: { x: hw, y: 0 }, name: 'e' });
                resizeHandles.push({ pos: { x: 0, y: hh }, name: 's' });
                resizeHandles.push({ pos: { x: -hw, y: 0 }, name: 'w' });
                break;
            }
            case 'hexagon': {
                const hexR = r * 0.65 + handleOffset;
                resizeHandles.push({ pos: { x: 0, y: -hexR }, name: 'n' });
                resizeHandles.push({ pos: { x: hexR, y: 0 }, name: 'e' });
                resizeHandles.push({ pos: { x: 0, y: hexR }, name: 's' });
                resizeHandles.push({ pos: { x: -hexR, y: 0 }, name: 'w' });
                break;
            }
            case 'circle':
            default: {
                const dist = r + handleOffset;
                resizeHandles.push({ pos: { x: 0, y: -dist }, name: 'n' });
                resizeHandles.push({ pos: { x: dist, y: 0 }, name: 'e' });
                resizeHandles.push({ pos: { x: 0, y: dist }, name: 's' });
                resizeHandles.push({ pos: { x: -dist, y: 0 }, name: 'w' });
                break;
            }
        }

        for (const handle of resizeHandles) {
            const rotatedX = handle.pos.x * Math.cos(deviceRotation) - handle.pos.y * Math.sin(deviceRotation);
            const rotatedY = handle.pos.x * Math.sin(deviceRotation) + handle.pos.y * Math.cos(deviceRotation);
            const handleX = device.x + rotatedX;
            const handleY = device.y + rotatedY;

            const dist = Math.sqrt(Math.pow(x - handleX, 2) + Math.pow(y - handleY, 2));

            if (dist < hitboxSize) {
                return handle.name;
            }
        }

        return null;
    }
    
    distanceToLine(px, py, lineStart, lineEnd) {
        if (window.LinkGeometry) {
            return window.LinkGeometry.distanceToLine(this, px, py, lineStart, lineEnd);
        }
    }
    
    // Check if two links already share an MP (connection point)
    linksAlreadyShareMP(link1, link2) {
        if (window.LinkGeometry) {
            return window.LinkGeometry.linksAlreadyShareMP(this, link1, link2);
        }
    }
    
    // Recursively find ALL merged links in the chain
    getAllMergedLinks(link) {
        if (window.BulUtils) {
            return window.BulUtils.getAllMergedLinks(this, link);
        }
        // Fallback - return just this link
        return [link];
    }
    
    getParentConnectionEndpoint(link) {
        if (window.BulUtils) {
            return window.BulUtils.getParentConnectionEndpoint(link);
        }
        if (!link?.mergedWith) return null;
        return link.mergedWith.connectionEndpoint || (link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start');
    }
    
    getChildConnectionEndpoint(link) {
        if (window.BulUtils) {
            return window.BulUtils.getChildConnectionEndpoint(this, link);
        }
        if (!link?.mergedInto) return null;
        return link.mergedInto.childEndpoint || null;
    }
    
    isEndpointConnectedToChild(link, endpoint) {
        const connection = this.getParentConnectionEndpoint(link);
        return connection ? connection === endpoint : false;
    }
    
    isEndpointConnectedToParent(link, endpoint) {
        const connection = this.getChildConnectionEndpoint(link);
        return connection ? connection === endpoint : false;
    }
    
    isEndpointConnected(link, endpoint) {
        if (!link) return false;
        if (this.isEndpointConnectedToChild(link, endpoint)) return true;
        if (this.isEndpointConnectedToParent(link, endpoint)) return true;
        return false;
    }
    
    getOppositeEndpoint(endpoint) {
        if (endpoint === 'start') return 'end';
        if (endpoint === 'end') return 'start';
        return null;
    }
    
    getLinkEndpointNearPoint(link, point, tolerance = 0.75) {
        if (!link || !point || !link.start || !link.end) return null;
        const distStart = Math.hypot(link.start.x - point.x, link.start.y - point.y);
        const distEnd = Math.hypot(link.end.x - point.x, link.end.y - point.y);
        
        if (!isFinite(distStart) || !isFinite(distEnd)) return null;
        
        if (distStart <= tolerance && distStart <= distEnd) return 'start';
        if (distEnd <= tolerance && distEnd < distStart) return 'end';
        
        // Fallback: return whichever endpoint is closer even if outside tolerance
        return distStart <= distEnd ? 'start' : 'end';
    }
    
    // NEW: Analyze BUL chain structure - count TPs and MPs
    analyzeBULChain(link) {
        if (window.LinkGeometry) {
            return window.LinkGeometry.analyzeBULChain(this, link);
        }
    }
    
    // NEW: Get ALL devices connected to TPs across the entire BUL chain
    getAllConnectedDevices(link) {
        const deviceIds = new Set();
        const deviceObjects = [];
        
        // Get all links in the merge chain
        const allMergedLinks = this.getAllMergedLinks(link);
        
        // Collect all devices from all links in the chain
        for (const chainLink of allMergedLinks) {
            // Check device1 (start endpoint)
            if (chainLink.device1 && !deviceIds.has(chainLink.device1)) {
                deviceIds.add(chainLink.device1);
                const device = this.objects.find(obj => obj.id === chainLink.device1);
                if (device) {
                    deviceObjects.push(device);
                }
            }
            
            // Check device2 (end endpoint)
            if (chainLink.device2 && !deviceIds.has(chainLink.device2)) {
                deviceIds.add(chainLink.device2);
                const device = this.objects.find(obj => obj.id === chainLink.device2);
                if (device) {
                    deviceObjects.push(device);
                }
            }
        }
        
        return {
            deviceIds: Array.from(deviceIds),
            devices: deviceObjects,
            count: deviceIds.size,
            links: allMergedLinks
        };
    }
    
    // Helper: Get ordinal suffix (1st, 2nd, 3rd, 4th, etc.)
    getOrdinalSuffix(num) {
        const j = num % 10;
        const k = num % 100;
        if (j === 1 && k !== 11) return 'st';
        if (j === 2 && k !== 12) return 'nd';
        if (j === 3 && k !== 13) return 'rd';
        return 'th';
    }
    
    // NEW: Get the two endpoint devices from a BUL chain (for linkIndex calculation)
    getBULEndpointDevices(link) {
        // PRIORITY: Check if link directly has both device1 and device2 (simple UL)
        if (link.device1 && link.device2) {
            const [dev1, dev2] = [link.device1, link.device2].sort();
            return { device1: dev1, device2: dev2, hasEndpoints: true };
        }
        
        // Otherwise, check the BUL chain for endpoint devices
        const connectedInfo = this.getAllConnectedDevices(link);
        
        // If exactly 2 devices, return them in a sorted order for consistent linkIndex
        if (connectedInfo.count === 2) {
            const [dev1, dev2] = connectedInfo.deviceIds.sort();
            return { device1: dev1, device2: dev2, hasEndpoints: true };
        }
        
        // If less than 2 devices, return what we have
        if (connectedInfo.count === 1) {
            return { device1: connectedInfo.deviceIds[0], device2: null, hasEndpoints: false };
        }
        
        // No devices or more than 2 devices
        return { device1: null, device2: null, hasEndpoints: false };
    }
    
    // NEW: Calculate linkIndex for any link based on its endpoint devices
    // CRITICAL: Must use EXACT same logic as drawLink() and SUL positioning for seamless integration
    calculateLinkIndex(link) {
        // Get the endpoint devices for this link/BUL
        const endpoints = this.getBULEndpointDevices(link);
        
        if (!endpoints.hasEndpoints || !endpoints.device1 || !endpoints.device2) {
            return 0; // Default to middle if no proper endpoints
        }
        
        // CRITICAL: Get ALL links (both QL and UL/SUL) between the same two devices
        // This must match EXACTLY the logic in drawLink() and SUL positioning
        const connectedLinks = this.objects.filter(obj => {
            // Count Quick Links (type: 'link')
            if (obj.type === 'link' && obj.device1 && obj.device2) {
                return (obj.device1 === endpoints.device1 && obj.device2 === endpoints.device2) ||
                       (obj.device1 === endpoints.device2 && obj.device2 === endpoints.device1);
            }
            
            // Count Unbound Links (type: 'unbound') with both endpoints attached
            if (obj.type === 'unbound' && obj.device1 && obj.device2) {
                // Direct device attachment (SUL)
                return (obj.device1 === endpoints.device1 && obj.device2 === endpoints.device2) ||
                       (obj.device1 === endpoints.device2 && obj.device2 === endpoints.device1);
            }
            
            // Count BUL chains with endpoints attached to devices
            if (obj.type === 'unbound' && (obj.mergedWith || obj.mergedInto)) {
            const objEndpoints = this.getBULEndpointDevices(obj);
            if (!objEndpoints.hasEndpoints) return false;
            
            return (objEndpoints.device1 === endpoints.device1 && objEndpoints.device2 === endpoints.device2) ||
                   (objEndpoints.device1 === endpoints.device2 && objEndpoints.device2 === endpoints.device1);
            }
            
            return false;
        }).sort((a, b) => {
            // CRITICAL: Sort by ID to ensure stable order - EXACTLY like drawLink()
            const idA = parseInt(a.id.split('_')[1]) || 0;
            const idB = parseInt(b.id.split('_')[1]) || 0;
            return idA - idB;
        });
        
        // Find this link's position in the sorted list - EXACTLY like drawLink()
        const linkIndex = connectedLinks.findIndex(l => l.id === link.id);
        return linkIndex >= 0 ? linkIndex : connectedLinks.length;
    }
    
    // NEW: Handle UL deletion in a BUL chain - reconfigure merge relationships
    handleULDeletionInBUL(deletedLink) {
        if (window.LinkGeometry) {
            return window.LinkGeometry.handleULDeletionInBUL(this, deletedLink);
        }
    }
    
    /**
     * Update curve control points for Quick Links (QL) when connected devices move.
     * QLs endpoints follow devices automatically, but curve CPs are in absolute coords.
     * This shifts the CP by the same delta as the device movement to keep curve shape.
     * 
     * Key: manualCurvePoint = permanent storage after curve drag ends (absolute position)
     *      manualControlPoint = temporary during active drag (will be cleared on mouse up)
     * 
     * @param {number} dx - Movement delta X
     * @param {number} dy - Movement delta Y
     * @param {string[]} movedDeviceIds - Array of device IDs that moved
     */
    updateQuickLinkControlPointsAfterDeviceMove(dx, dy, movedDeviceIds) {
        if (!movedDeviceIds || movedDeviceIds.length === 0) return;
        if (Math.abs(dx) < 0.001 && Math.abs(dy) < 0.001) return; // No significant movement
        
        // Find all Quick Links (type: 'link') connected to the moved devices
        const quickLinks = this.objects.filter(obj => 
            obj.type === 'link' && 
            (movedDeviceIds.includes(obj.device1) || movedDeviceIds.includes(obj.device2))
        );
        
        if (this.debugger && quickLinks.length > 0) {
            const curvedLinks = quickLinks.filter(ql => ql.manualCurvePoint || ql.manualControlPoint);
            if (curvedLinks.length > 0) {
                this.debugger.logInfo(`Updating ${curvedLinks.length} curved QL(s) for device move: dx=${dx.toFixed(1)}, dy=${dy.toFixed(1)}`);
            }
        }
        
        quickLinks.forEach(ql => {
            // Skip if no curve defined
            if (!ql.manualCurvePoint && !ql.manualControlPoint) return;
            
            // Check if BOTH endpoints moved (both devices in selection)
            const bothEndpointsMoved = movedDeviceIds.includes(ql.device1) && movedDeviceIds.includes(ql.device2);
            
            // Calculate shift amount: full delta if both moved, half if only one
            const shiftX = bothEndpointsMoved ? dx : dx / 2;
            const shiftY = bothEndpointsMoved ? dy : dy / 2;
            
            // Update permanent curve storage (manualCurvePoint)
            if (ql.manualCurvePoint) {
                ql.manualCurvePoint.x += shiftX;
                ql.manualCurvePoint.y += shiftY;
            }
            
            // Also update temporary drag position if active (manualControlPoint)
            if (ql.manualControlPoint) {
                ql.manualControlPoint.x += shiftX;
                ql.manualControlPoint.y += shiftY;
            }
        });
    }
    
    /**
     * Update unbound link curve control point after link movement.
     * PRESERVES the curve shape by shifting the CP by the midpoint delta.
     * This ensures the CP always stays on the curve body at the middle of the link.
     * 
     * @param {Object} link - The unbound link to update
     * @param {number} shiftX - Amount to shift X
     * @param {number} shiftY - Amount to shift Y
     */
    shiftUnboundLinkCP(link, shiftX, shiftY) {
        if (!link || link.type !== 'unbound' || !link.manualCurvePoint) return;
        if (Math.abs(shiftX) < 0.001 && Math.abs(shiftY) < 0.001) return;
        
        // Shift the curve point to maintain relative position to link midpoint
        link.manualCurvePoint.x += shiftX;
        link.manualCurvePoint.y += shiftY;
    }
    
    // NEW: Update ALL connection points in the entire merged chain
    updateAllConnectionPoints() {
        // Process all unbound links to update their connection points
        this.objects.forEach(link => {
            if (link.type === 'unbound') {
                // Update parent's connection point if this is a merged link
                if (link.mergedWith && link.mergedWith.connectionPoint) {
                    const parentConnectedEnd = this.getParentConnectionEndpoint(link) ||
                        (link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start');
                    const newConnectionX = parentConnectedEnd === 'start' ? link.start.x : link.end.x;
                    const newConnectionY = parentConnectedEnd === 'start' ? link.start.y : link.end.y;
                    
                    link.mergedWith.connectionPoint.x = newConnectionX;
                    link.mergedWith.connectionPoint.y = newConnectionY;
                    
                    // Also update child's connection point
                    const childLink = this.objects.find(o => o.id === link.mergedWith.linkId);
                    if (childLink && childLink.mergedInto) {
                        childLink.mergedInto.connectionPoint.x = newConnectionX;
                        childLink.mergedInto.connectionPoint.y = newConnectionY;
                    }
                }
                
                // Update child's connection point if this is a child link
                if (link.mergedInto && link.mergedInto.connectionPoint) {
                    const parentLink = this.objects.find(o => o.id === link.mergedInto.parentId);
                    if (parentLink && parentLink.mergedWith) {
                        // FIXED: childFreeEnd tells us which end IS FREE, connected end is opposite
                        const childConnectedEnd = parentLink.mergedWith.childConnectionEndpoint ||
                            (parentLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                        const newConnectionX = childConnectedEnd === 'start' ? link.start.x : link.end.x;
                        const newConnectionY = childConnectedEnd === 'start' ? link.start.y : link.end.y;
                        
                        link.mergedInto.connectionPoint.x = newConnectionX;
                        link.mergedInto.connectionPoint.y = newConnectionY;
                        
                        if (parentLink.mergedWith) {
                            parentLink.mergedWith.connectionPoint.x = newConnectionX;
                            parentLink.mergedWith.connectionPoint.y = newConnectionY;
                        }
                    }
                }
                
                // NOTE: CP shifting is handled by the caller with proper oldMidpoint tracking
                // updateAllConnectionPoints only syncs the merge connection points, not curve CPs
            }
        });
    }
    
    /**
     * REAL-TIME CP Update during stretch operations
     * In MANUAL mode: CP stays at its absolute position (curve adjusts to new endpoints)
     * Only shifts CP when dragging the BODY of a link (not TPs)
     * @param {Object} [link] - Optional link override (used after stretchingLink is cleared)
     */
    _updateCurvePointsDuringStretch(link = null) {
        // In manual curve mode, the CP should stay at its absolute position
        // The curve naturally adjusts to pass through the fixed CP as endpoints move
        // So we do NOT shift the CP during TP/MP stretching
        
        // This function is now a no-op for TP stretching
        // CP shifting for body dragging is handled separately in the drag code
        return;
    }
    
    distanceToCurvedLine(px, py, link, device1, device2) {
        if (window.LinkGeometry) {
            return window.LinkGeometry.distanceToCurvedLine(this, px, py, link, device1, device2);
        }
    }
    
    // ENHANCED: Calculate distance to curved line using pre-stored control points
    // This is used for ULs that don't have both devices attached but still have curved bodies
    distanceToCurvedLineWithControlPoints(px, py, start, end, cp1, cp2) {
        // Calculate curve length approximation for adaptive sampling
        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const straightLength = Math.sqrt(dx * dx + dy * dy);
        
        // Calculate curve magnitude (how much it bends)
        const midX = (start.x + end.x) / 2;
        const midY = (start.y + end.y) / 2;
        const curveMagnitude = Math.max(
            Math.sqrt(Math.pow(cp1.x - midX, 2) + Math.pow(cp1.y - midY, 2)),
            Math.sqrt(Math.pow(cp2.x - midX, 2) + Math.pow(cp2.y - midY, 2))
        );
        
        // FIXED: Use many more samples for accurate hit detection
        // Base samples on curve length + curvature - always at least 100 samples
        const lengthBasedSamples = Math.ceil(straightLength / 5); // One sample per 5 world units
        const curveBasedSamples = Math.ceil(curveMagnitude / 2);  // More samples for tighter curves
        const samples = Math.min(300, Math.max(100, lengthBasedSamples + curveBasedSamples));
        
        let minDist = Infinity;
        
        // Sample points along cubic Bezier curve
        for (let i = 0; i <= samples; i++) {
            const t = i / samples;
            const mt = 1 - t;
            
            // Cubic Bezier formula: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
            const curveX = mt * mt * mt * start.x + 
                          3 * mt * mt * t * cp1.x + 
                          3 * mt * t * t * cp2.x + 
                          t * t * t * end.x;
            const curveY = mt * mt * mt * start.y + 
                          3 * mt * mt * t * cp1.y + 
                          3 * mt * t * t * cp2.y + 
                          t * t * t * end.y;
            
            const dist = Math.sqrt(Math.pow(px - curveX, 2) + Math.pow(py - curveY, 2));
            if (dist < minDist) minDist = dist;
        }
        
        return minDist;
    }
    
    toggleTool(tool) {
        // If tool is already active, deactivate and return to base mode
        if (this.currentTool === tool && document.getElementById(`btn-${tool}`).classList.contains('active')) {
            this.setMode('base');
            if (this.debugger) {
                this.debugger.logInfo(`${tool.toUpperCase()} -> BASE (toggle off)`);
            }
        } else {
            // Seamless transition - preserve context when switching modes
            const oldMode = this.currentMode;
            this.currentMode = tool;
            this.currentTool = tool;
            
            // Clear ONLY conflicting states for seamless transitions
            if (tool === 'link') {
                this.linking = false;
                this.linkStart = null;
                this.placingDevice = null;
                // Keep selections - allows quick mode switching
            } else if (tool === 'text') {
                this.textPlaced = false;
                this.linking = false;
                this.linkStart = null;
                this.placingDevice = null;
            } else if (tool === 'select') {
                this.linking = false;
                this.linkStart = null;
                this.placingDevice = null;
            }
            
            // Update button states - with null checks
            const btnBase = document.getElementById('btn-base');
            const btnSelect = document.getElementById('btn-select');
            const btnLink = document.getElementById('btn-link');
            const btnText = document.getElementById('btn-text');
            const btnSwitch = document.getElementById('btn-switch');
            const btnActive = document.getElementById(`btn-${tool}`);
            
            if (btnBase) btnBase.classList.remove('active');
            if (btnSelect) btnSelect.classList.remove('active');
            if (btnLink) btnLink.classList.remove('active');
            if (btnText) btnText.classList.remove('active');
            if (btnSwitch) btnSwitch.classList.remove('active');
            if (btnActive) btnActive.classList.add('active');
            
            this.updateModeIndicator();
            
            if (this.debugger) {
                this.debugger.logSuccess(`Mode: ${(oldMode || 'BASE').toUpperCase()} -> ${tool.toUpperCase()}`);
            }
        }
    }
    
    /**
     * Enter text placement mode - like device placement, allows continuous text box placement
     * Each click places a new text box with current font/style settings until mode is exited
     */
    enterTextPlacementMode() {
        // Clear multi-select if active
        if (this.multiSelectMode) {
            this.multiSelectMode = false;
            this.selectedObjects = [];
        }
        
        // Clear device placement if active
        this.placingDevice = null;
        
        // Set text tool active
        this.currentTool = 'text';
        this.currentMode = 'text';
        this.canvas.style.cursor = 'text';
        
        // Update button states - with null checks
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
        const btnText = document.getElementById('btn-text');
        if (btnText) btnText.classList.add('active');
        
        // Update text section header to show active state
        const textSection = document.querySelector('.toolbar-section[data-section="text"]');
        if (textSection) {
            textSection.classList.add('tool-active');
            // Make sure section is expanded
            if (!textSection.classList.contains('expanded')) {
                textSection.classList.add('expanded');
            }
        }
        
        // Also deactivate link section if it was active
        const linkSection = document.querySelector('.toolbar-section[data-section="links"]');
        if (linkSection) {
            linkSection.classList.remove('tool-active');
        }
        
        this.updateModeIndicator();
        
        if (this.debugger) {
            this.debugger.logSuccess('Text placement mode - click to place text boxes');
        }
    }
    
    toggleDevicePlacementMode(deviceType) {
        // Clear multi-select if active
        if (this.multiSelectMode) {
            this.multiSelectMode = false;
            this.selectedObjects = [];
        }
        // Toggle: if already placing this device type, deactivate
        if (this.placingDevice === deviceType) {
            this.placingDevice = null;
            this.setMode('base');
        } else {
            this.setDevicePlacementMode(deviceType);
        }
    }
    
    /**
     * Toggle continuous text box placement mode
     * When enabled, user can place multiple TBs by clicking on the grid
     * Mode ends when: button is toggled off, user clicks an existing object, or right-clicks
     */
    toggleContinuousTextPlacement() {
        this.continuousTextPlacement = !this.continuousTextPlacement;
        
        const btn = document.getElementById('btn-place-tbs');
        const statusSpan = document.getElementById('place-tbs-status');
        
        if (this.continuousTextPlacement) {
            // Enable continuous text placement mode
            this.setMode('text'); // Enter text mode
            
            if (btn) {
                btn.classList.add('active');
            }
            if (statusSpan) {
                statusSpan.textContent = 'ON';
                statusSpan.style.background = 'rgba(74, 222, 128, 0.5)';
                statusSpan.style.color = '#fff';
            }
            
            if (this.debugger) {
                this.debugger.logSuccess('📝 Continuous TB placement ON - Click grid to place, right-click or select object to exit');
            }
        } else {
            // Disable continuous text placement mode
            this.exitContinuousTextPlacement();
        }
        
        this.draw();
    }
    
    /**
     * Exit continuous text placement mode (called by toggle, right-click, or object selection)
     */
    exitContinuousTextPlacement() {
        if (!this.continuousTextPlacement) return;
        
        this.continuousTextPlacement = false;
        
        const btn = document.getElementById('btn-place-tbs');
        const statusSpan = document.getElementById('place-tbs-status');
        
        if (btn) {
            btn.classList.remove('active');
        }
        if (statusSpan) {
            statusSpan.textContent = 'OFF';
            statusSpan.style.background = 'rgba(100, 100, 100, 0.4)';
            statusSpan.style.color = 'rgba(255, 255, 255, 0.6)';
        }
        
        // Return to base mode
        this.setMode('base');
        
        if (this.debugger) {
            this.debugger.logInfo('📝 Continuous TB placement OFF');
        }
    }
    
    // ========== SHAPE METHODS ==========
    
    setupShapeToolbar() {
        if (window.ShapeMethods) {
            return window.ShapeMethods.setupShapeToolbar(this);
        }
    }
    
    selectShapeType(shapeType) {
        if (window.ShapeMethods) {
            return window.ShapeMethods.selectShapeType(this, shapeType);
        }
    }
    
    enterShapePlacementMode(shapeType) {
        if (window.ShapeMethods) {
            return window.ShapeMethods.enterShapePlacementMode(this, shapeType);
        }
    }
    
    exitShapePlacementMode() {
        if (window.ShapeMethods) {
            return window.ShapeMethods.exitShapePlacementMode(this);
        }
    }
    
    createShape(x, y, shapeType) {
        if (window.ShapeMethods) {
            return window.ShapeMethods.createShape(this, x, y, shapeType);
        }
    }
    
    drawShape(shape) {
        if (window.ShapeDrawing) {
            return window.ShapeDrawing.drawShape(this, shape);
        }
    }
    
    drawShapeSelectionHandles(shape) {
        if (window.ShapeDrawing) {
            return window.ShapeDrawing.drawShapeSelectionHandles(this, shape);
        }
    }
    
    getShapeHandlePositions(shape) {
        if (window.ShapeMethods) {
            return window.ShapeMethods.getShapeHandlePositions(this, shape);
        }
    }
    
    findShapeAt(x, y) {
        if (window.ShapeMethods) {
            return window.ShapeMethods.findShapeAt(this, x, y);
        }
    }
    
    findShapeResizeHandle(shape, x, y) {
        if (window.ShapeMethods) {
            return window.ShapeMethods.findShapeResizeHandle(this, shape, x, y);
        }
    }
    
    updateSelectedShapeStyle() {
        if (this.selectedObject && this.selectedObject.type === 'shape') {
            this.selectedObject.fillColor = this.shapeFillColor;
            this.selectedObject.fillOpacity = this.shapeFillOpacity;
            this.selectedObject.fillEnabled = this.shapeFillEnabled;
            this.selectedObject.strokeColor = this.shapeStrokeColor;
            this.selectedObject.strokeWidth = this.shapeStrokeWidth;
            this.selectedObject.strokeEnabled = this.shapeStrokeEnabled;
            this.draw();
            this.scheduleAutoSave();
        }
    }
    
    hexToRgba(hex, alpha) {
        if (window.MathUtils) {
            return window.MathUtils.hexToRgba(hex, alpha);
        }
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    toggleAngleMeter() {
        this.showAngleMeter = !this.showAngleMeter;
        const btn = document.getElementById('btn-angle-meter');
        if (btn) {
            const statusText = btn.querySelector('.status-text');
            if (this.showAngleMeter) {
                btn.classList.add('active');
                if (statusText) statusText.textContent = 'Angle: ON';
                if (this.debugger) this.debugger.logSuccess('Angle meter enabled');
            } else {
                btn.classList.remove('active');
                if (statusText) statusText.textContent = 'Angle: OFF';
                if (this.debugger) this.debugger.logInfo('Angle meter disabled');
            }
        }
        this.draw();
        this.scheduleAutoSave();
    }
    
    toggleTBAttach() {
        this.autoCreateInterfaceTB = !this.autoCreateInterfaceTB;
        const btn = document.getElementById('btn-tb-attach');
        if (btn) {
            const statusText = btn.querySelector('.status-text');
            if (this.autoCreateInterfaceTB) {
                btn.classList.add('active');
                if (statusText) statusText.textContent = 'TB Attach: ON';
                if (this.debugger) this.debugger.logSuccess('Auto-create interface TB enabled');
            } else {
                btn.classList.remove('active');
                if (statusText) statusText.textContent = 'TB Attach: OFF';
                if (this.debugger) this.debugger.logInfo('Auto-create interface TB disabled');
            }
        }
        this.scheduleAutoSave();
    }
    
    toggleLinkCurveMode() {
        this.linkCurveMode = !this.linkCurveMode;
        const btn = document.getElementById('btn-link-curve');
        if (btn) {
        const statusText = btn.querySelector('.status-text');
        if (this.linkCurveMode) {
            btn.classList.add('active');
            btn.title = 'Curve Links ON - Magnetic Repulsion Enabled';
            if (statusText) statusText.textContent = 'Curve: ON';
        } else {
            btn.classList.remove('active');
            btn.title = 'Curve Links OFF - Straight Lines';
            if (statusText) statusText.textContent = 'Curve: OFF';
        }
        }
        
        // Show/hide curve magnitude slider based on curve mode
        const curveMagnitudeControl = document.getElementById('curve-magnitude-control');
        if (curveMagnitudeControl) {
            curveMagnitudeControl.style.display = this.linkCurveMode ? 'block' : 'none';
        }
        
        // Show/hide curve mode buttons (Auto/Manual) based on curve mode
        const curveModeButtons = document.getElementById('curve-mode-buttons');
        if (curveModeButtons) {
            curveModeButtons.style.display = this.linkCurveMode ? 'flex' : 'none';
        }
        
        this.draw(); // Redraw with new curve mode
        this.scheduleAutoSave(); // Save setting change
    }
    
    // Set global curve mode: 'auto' (magnetic repulsion), 'manual' (user-draggable)
    setGlobalCurveMode(mode) {
        if (window.CurveModeManager) {
            return window.CurveModeManager.setGlobalMode(this, mode);
        }
    }
    
    // Update UI to reflect current global curve mode
    updateGlobalCurveModeUI() {
        if (window.CurveModeManager) {
            return window.CurveModeManager.updateUI(this);
        }
    }
    
    // Get effective curve mode for a link (per-link override or global)
    getEffectiveCurveMode(link) {
        if (window.CurveModeManager) {
            return window.CurveModeManager.getEffectiveMode(this, link);
        }
        return this.globalCurveMode;
    }
    
    // Get the current endpoints of a link
    getLinkEndpoints(link) {
        if (window.CurveModeManager) {
            return window.CurveModeManager.getEndpoints(this, link);
        }
        return null;
    }
    
    // Get the visual midpoint ON the curve (at t=0.5)
    getLinkMidpoint(link, overrideEndpoints = null) {
        if (window.CurveModeManager) {
            return window.CurveModeManager.getMidpoint(this, link, overrideEndpoints);
        }
        return null;
    }
    
    // Get the current AUTO curve's visual midpoint position
    getAutoCurveMidpoint(link) {
        if (window.CurveModeManager) {
            return window.CurveModeManager.getAutoCurveMidpoint(this, link);
        }
        return null;
    }
    
    // Get the actual rendered endpoints of a link (device edges, not centers)
    // This matches what the drawing code uses
    getLinkRenderedEndpoints(link) {
        if (link.type === 'unbound') {
            // Unbound links use their stored start/end positions
            if (link.start && link.end) {
                return {
                    startX: link.start.x,
                    startY: link.start.y,
                    endX: link.end.x,
                    endY: link.end.y
                };
            }
            return null;
        }
        
        // For device-connected links, calculate edge positions
        const dev1 = this.objects.find(o => o.id === link.device1);
        const dev2 = this.objects.find(o => o.id === link.device2);
        if (!dev1 || !dev2) return null;
        
        // Calculate angle between devices
        const angle = Math.atan2(dev2.y - dev1.y, dev2.x - dev1.x);
        
        // Get connection points on device edges
        const start = this.getLinkConnectionPoint(dev1, angle);
        const end = this.getLinkConnectionPoint(dev2, angle + Math.PI);
        
        return {
            startX: start.x,
            startY: start.y,
            endX: end.x,
            endY: end.y
        };
    }
    
    // Check if a link has an attached text box at the MIDDLE position that should act as its curve control point
    // Returns the text object if found, null otherwise
    getAttachedTextAsCP(link) {
        // ENHANCED: In MANUAL curve mode, attached middle text acts as the curve control point
        // This allows users to drag the text label to curve the link
        const effectiveMode = this.getEffectiveCurveMode(link);
        if (effectiveMode !== 'manual') return null;
        
        // Find text attached to the middle of this link
        const attachedMiddleText = this.objects.find(obj => 
            obj.type === 'text' && 
            obj.linkId === link.id && 
            obj.position === 'middle'
        );
        
        return attachedMiddleText || null;
    }
    
    // Get the Bezier control point for a manual curve
    // The control point is calculated so the curve passes through the stored curve point at t=0.5
    // For CUBIC Bezier with cp1=cp2=C: point at t=0.5 is (P0 + 6*C + P3) / 8
    // To pass through M at t=0.5: C = (4*M - midpoint) / 3
    // Optional overrideEndpoints can be provided to use specific start/end positions
    getManualCurveBezierControlPoint(link, overrideEndpoints = null) {
        let startX, startY, endX, endY;
        
        if (overrideEndpoints) {
            startX = overrideEndpoints.startX;
            startY = overrideEndpoints.startY;
            endX = overrideEndpoints.endX;
            endY = overrideEndpoints.endY;
        } else {
            const renderedEndpoints = this.getLinkRenderedEndpoints(link);
            if (!renderedEndpoints) return null;
            startX = renderedEndpoints.startX;
            startY = renderedEndpoints.startY;
            endX = renderedEndpoints.endX;
            endY = renderedEndpoints.endY;
        }
        
        // Straight-line midpoint
        const straightMidX = (startX + endX) / 2;
        const straightMidY = (startY + endY) / 2;
        
        // Get the stored curve pass-through point (NOT getLinkMidpoint to avoid circular call)
        // PRIORITY: manualControlPoint > manualCurvePoint > attachedText > legacy offset
        let curvePassThrough = null;
        
        // Priority 1: During active drag (manualControlPoint)
        if (link.manualControlPoint) {
            curvePassThrough = { x: link.manualControlPoint.x, y: link.manualControlPoint.y };
        }
        // Priority 2: Stored manual curve point (absolute position, after release)
        else if (link.manualCurvePoint) {
            curvePassThrough = { x: link.manualCurvePoint.x, y: link.manualCurvePoint.y };
        }
        // Priority 3: Attached text at middle position
        else {
        const attachedText = this.getAttachedTextAsCP(link);
        if (attachedText) {
            curvePassThrough = { x: attachedText.x, y: attachedText.y };
        }
        }
        // Priority 4: Legacy offset format
        if (!curvePassThrough && link.manualCurveOffset) {
            const linkLength = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
            if (linkLength > 0) {
                const dx = endX - startX;
                const dy = endY - startY;
                const dirX = dx / linkLength;
                const dirY = dy / linkLength;
                const perpX = -dirY;
                const perpY = dirX;
                
                const perpRatio = link.manualCurveOffset.perpRatio ?? link.manualCurveOffset.perpDistance ?? 0;
                const alongRatio = link.manualCurveOffset.alongRatio ?? 0;
                
                curvePassThrough = {
                    x: straightMidX + (alongRatio * dirX + perpRatio * perpX) * linkLength,
                    y: straightMidY + (alongRatio * dirY + perpRatio * perpY) * linkLength
                };
            }
        }
        
        if (!curvePassThrough) {
            return { x: straightMidX, y: straightMidY };
        }
        
        // Calculate Bezier control point for CUBIC Bezier: C = (4*M - midpoint) / 3
        // This ensures the curve passes through curvePassThrough (M) at t=0.5
        return {
            x: (4 * curvePassThrough.x - straightMidX) / 3,
            y: (4 * curvePassThrough.y - straightMidY) / 3
        };
    }
    
    // Calculate where the visual center of a curved link is (at t=0.5 on the Bezier)
    // This is always ON the link body itself
    getVisualCurveMidpoint(link, bezierCP) {
        const endpoints = this.getLinkEndpoints(link);
        if (!endpoints) return null;
        
        const { startX, startY, endX, endY } = endpoints;
        
        // For CUBIC Bezier with cp1=cp2=C: B(0.5) = (P0 + 6*C + P3) / 8
        return {
            x: (startX + 6 * bezierCP.x + endX) / 8,
            y: (startY + 6 * bezierCP.y + endY) / 8
        };
    }
    
    // Check if a point is near a link's curve control handle (CP)
    // Returns { link, midpoint, isOnCP } if hovering close to the CP position
    // ENHANCED: CP only appears when mouse is near the link MIDDLE (CP location)
    // Not when hovering anywhere on the link body - this gives cleaner UX
    // NOTE: TB (text box) and CP (control point) are SEPARATE - this only handles CP detection
    findCurveHandleAt(x, y, handleRadius = 18) {
        // ENHANCED: Increased handle radius for better grab responsiveness
        
        // Check all links - manual mode links can be curved even without global toggle
        // Extended detection radius - show CP when mouse is "close" to the middle
        const cpProximityRadius = 50; // Pixels from CP center to trigger visibility (wider reveal distance)
        
        // Collect all candidate links with their distances
        const candidates = [];
        
        for (const obj of this.objects) {
            if (obj.type !== 'link' && obj.type !== 'unbound') continue;
            
            // Get effective mode for this link
            const linkMode = this.getEffectiveCurveMode(obj);
            const isManualMode = linkMode === 'manual';
            const isAutoMode = linkMode === 'auto';
            
            // For auto mode, require global curve toggle
            if (isAutoMode && !this.linkCurveMode) continue;
            
            // Only check manual mode links or already-curved links
            const hasManualCurve = obj.manualCurvePoint != null || obj.manualCurveOffset != null || obj.manualControlPoint != null;
            
            // ENHANCED: Also check for attached middle text as potential CP
            const attachedMiddleText = this.objects.find(t => 
                t.type === 'text' && t.linkId === obj.id && t.position === 'middle'
            );
            const hasTextCP = isManualMode && attachedMiddleText;
            
            if (!hasManualCurve && !isManualMode && !hasTextCP) continue;
            
            // Get the visual midpoint of this link (where CP would be displayed)
            const midpoint = this.getLinkMidpoint(obj);
            if (!midpoint) continue;
            
            // Check distance from mouse to CP position
            const dx = x - midpoint.x;
            const dy = y - midpoint.y;
            const distToCP = Math.sqrt(dx * dx + dy * dy);
            
            // Direct hit on CP handle (for drag initiation) - prioritize closest
            if (distToCP <= handleRadius) {
                candidates.push({ link: obj, midpoint, isOnCP: true, distance: distToCP, hasTextCP });
            }
            // Show CP when mouse is within proximity radius of the link middle
            else if (isManualMode && distToCP <= cpProximityRadius) {
                // Additional check: must also be near the actual link
                if (this.isPointNearLinkBody(x, y, obj, 25)) {
                    candidates.push({ link: obj, midpoint, isOnCP: false, distance: distToCP, hasTextCP });
                }
            }
        }
        
        // Return the closest candidate
        if (candidates.length === 0) return null;
        
        // Sort by distance, prioritize direct CP hits
        candidates.sort((a, b) => {
            // Direct hits first
            if (a.isOnCP && !b.isOnCP) return -1;
            if (!a.isOnCP && b.isOnCP) return 1;
            // Then by distance
            return a.distance - b.distance;
        });
        
        const best = candidates[0];
        return { link: best.link, midpoint: best.midpoint, isOnCP: best.isOnCP, hasTextCP: best.hasTextCP };
    }
    
    // Check if a point is near the link body (curved or straight line)
    // Excludes areas near TPs (endpoints) to avoid conflict with TP selection
    isPointNearLinkBody(x, y, link, threshold = 10) {
        // IMPROVED: Prioritize _renderedEndpoints for accurate hitbox
        let startX, startY, endX, endY;
        
        if (link._renderedEndpoints) {
            startX = link._renderedEndpoints.startX;
            startY = link._renderedEndpoints.startY;
            endX = link._renderedEndpoints.endX;
            endY = link._renderedEndpoints.endY;
        } else if (link.start && link.end) {
            startX = link.start.x;
            startY = link.start.y;
            endX = link.end.x;
            endY = link.end.y;
        } else {
        const endpoints = this.getLinkEndpoints(link);
        if (!endpoints) return false;
            startX = endpoints.startX;
            startY = endpoints.startY;
            endX = endpoints.endX;
            endY = endpoints.endY;
        }
        
        // PRIORITY: Exclude areas near TPs (Terminal Points) - TPs have priority over curve handles
        const tpExclusionRadius = 8 / this.zoom;
        const distToStart = Math.sqrt((x - startX) * (x - startX) + (y - startY) * (y - startY));
        const distToEnd = Math.sqrt((x - endX) * (x - endX) + (y - endY) * (y - endY));
        
        if (distToStart < tpExclusionRadius || distToEnd < tpExclusionRadius) {
            return false; // Near a TP, don't activate curve handle
        }
        
        // IMPROVED: Use stored control points for accurate curved link hitbox
        // Priority: _cp1/_cp2 (from drawing) > manualCurvePoint calculation > straight line
        if (link._cp1 && link._cp2) {
            // Use stored control points directly for exact match with rendered curve
            const dist = this.distanceToCurvedLineWithControlPoints(
                x, y,
                { x: startX, y: startY },
                { x: endX, y: endY },
                link._cp1, link._cp2
            );
            return dist <= threshold;
        } else if (link.manualCurvePoint || link.manualCurveOffset || link.manualControlPoint || this.getAttachedTextAsCP(link)) {
            // Fallback: Calculate bezier CP from manual curve data
            const straightMidX = (startX + endX) / 2;
            const straightMidY = (startY + endY) / 2;
            const bezierCP = link.manualControlPoint 
                ? { 
                    x: (4 * link.manualControlPoint.x - straightMidX) / 3,
                    y: (4 * link.manualControlPoint.y - straightMidY) / 3 
                }
                : this.getManualCurveBezierControlPoint(link);
            
            if (bezierCP) {
                return this.isPointNearCubicBezier(x, y, startX, startY, bezierCP.x, bezierCP.y, endX, endY, threshold);
            }
        }
        
        // For straight links, check distance to line segment
        return this.isPointNearLineSegment(x, y, startX, startY, endX, endY, threshold);
    }
    
    // Check if point is near a CUBIC Bezier curve with cp1=cp2=C (excluding endpoints)
    isPointNearCubicBezier(px, py, x0, y0, cx, cy, x1, y1, threshold) {
        // Sample points along the MIDDLE portion of the curve (skip near endpoints for TP priority)
        const samples = 20;
        const tStart = 0.15; // Skip first 15% (near start TP)
        const tEnd = 0.85;   // Skip last 15% (near end TP)
        
        for (let i = 0; i <= samples; i++) {
            const t = tStart + (i / samples) * (tEnd - tStart);
            const mt = 1 - t;
            // CUBIC Bezier with cp1=cp2=C: B(t) = (1-t)³P0 + 3(1-t)²tC + 3(1-t)t²C + t³P1
            // Simplified: B(t) = (1-t)³P0 + 3(1-t)t*C*((1-t) + t) + t³P1 = (1-t)³P0 + 3(1-t)t*C + t³P1
            const mt3 = mt * mt * mt;
            const t3 = t * t * t;
            const middle = 3 * mt * t; // 3(1-t)t for the control point
            const bx = mt3 * x0 + middle * cx + t3 * x1;
            const by = mt3 * y0 + middle * cy + t3 * y1;
            
            const dx = px - bx;
            const dy = py - by;
            if (dx * dx + dy * dy <= threshold * threshold) {
                return true;
            }
        }
        return false;
    }
    
    // Check if point is near a quadratic Bezier curve (excluding endpoints)
    isPointNearQuadraticBezier(px, py, x0, y0, cx, cy, x1, y1, threshold) {
        // Sample points along the MIDDLE portion of the curve (skip near endpoints for TP priority)
        const samples = 20;
        const tStart = 0.15; // Skip first 15% (near start TP)
        const tEnd = 0.85;   // Skip last 15% (near end TP)
        
        for (let i = 0; i <= samples; i++) {
            const t = tStart + (i / samples) * (tEnd - tStart);
            const mt = 1 - t;
            // Quadratic Bezier: B(t) = (1-t)²P0 + 2(1-t)tCP + t²P1
            const bx = mt * mt * x0 + 2 * mt * t * cx + t * t * x1;
            const by = mt * mt * y0 + 2 * mt * t * cy + t * t * y1;
            
            const dx = px - bx;
            const dy = py - by;
            if (dx * dx + dy * dy <= threshold * threshold) {
                return true;
            }
        }
        return false;
    }
    
    // Check if point is near a line segment (excluding endpoints for TP priority)
    isPointNearLineSegment(px, py, x1, y1, x2, y2, threshold) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const lengthSq = dx * dx + dy * dy;
        
        if (lengthSq === 0) {
            return false; // Line is a point, can't have a curve handle
        }
        
        // Project point onto line
        let t = ((px - x1) * dx + (py - y1) * dy) / lengthSq;
        
        // Only check the middle portion (15%-85%) to avoid conflict with TPs
        if (t < 0.15 || t > 0.85) {
            return false; // Near endpoints, let TPs have priority
        }
        
        const nearestX = x1 + t * dx;
        const nearestY = y1 + t * dy;
        
        const distSq = (px - nearestX) * (px - nearestX) + (py - nearestY) * (py - nearestY);
        return distSq <= threshold * threshold;
    }
    
    // Check if we should show the curve handle for a link
    shouldShowCurveHandle(link) {
        const linkMode = this.getEffectiveCurveMode(link);
        return linkMode === 'manual';
    }

    // Calculate a point along a cubic bezier curve at parameter t (0-1)
    getPointOnBezierCurve(startX, startY, cp1x, cp1y, cp2x, cp2y, endX, endY, t) {
        // Cubic bezier formula: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
        const t2 = t * t;
        const t3 = t2 * t;
        const mt = 1 - t;
        const mt2 = mt * mt;
        const mt3 = mt2 * mt;
        
        return {
            x: mt3 * startX + 3 * mt2 * t * cp1x + 3 * mt * t2 * cp2x + t3 * endX,
            y: mt3 * startY + 3 * mt2 * t * cp1y + 3 * mt * t2 * cp2y + t3 * endY
        };
    }
    
    toggleLinkContinuousMode() {
        this.linkContinuousMode = !this.linkContinuousMode;
        const btn = document.getElementById('btn-link-continuous');
        if (btn) {
        const statusText = btn.querySelector('.status-text');
        if (this.linkContinuousMode) {
            btn.classList.add('active');
            btn.title = 'Continuous Linking ON - Chain Links Together';
            if (statusText) statusText.textContent = 'Chain: ON';
        } else {
            btn.classList.remove('active');
            btn.title = 'Continuous Linking OFF - Single Links';
            if (statusText) statusText.textContent = 'Chain: OFF';
            // When turning off continuous mode, clear any active linking
            this.linking = false;
            this.linkStart = null;
            }
        } else {
            if (!this.linkContinuousMode) {
                this.linking = false;
                this.linkStart = null;
            }
        }
        this.draw();
        this.scheduleAutoSave(); // Save setting change
    }
    
    toggleLinkStickyMode() {
        this.linkStickyMode = !this.linkStickyMode;
        const btn = document.getElementById('btn-link-sticky');
        if (btn) {
        const statusText = btn.querySelector('.status-text');
        if (this.linkStickyMode) {
            btn.classList.add('active');
            btn.title = 'Sticky Links ON - Links Snap to Devices';
            if (statusText) statusText.textContent = 'Sticky: ON';
        } else {
            btn.classList.remove('active');
            btn.title = 'Sticky Links OFF - Links Don\'t Auto-Snap';
            if (statusText) statusText.textContent = 'Sticky: OFF';
            }
        }
        this.draw();
        this.scheduleAutoSave(); // Save setting change
    }
    
    toggleLinkULMode() {
        this.linkULEnabled = !this.linkULEnabled;
        const btn = document.getElementById('btn-link-ul');
        if (btn) {
        const statusText = btn.querySelector('.status-text');
        if (this.linkULEnabled) {
            btn.classList.add('active');
            btn.title = 'Unbound Links ON - Double Tap Screen to Create UL';
            if (statusText) statusText.textContent = 'Unbounded: ON';
        } else {
            btn.classList.remove('active');
            btn.title = 'Unbound Links OFF - Double Tap Disabled';
            if (statusText) statusText.textContent = 'Unbounded: OFF';
            }
        }
        this.draw();
        this.scheduleAutoSave(); // Save setting change
    }
    
    // Style variants for each button (4 variants each)
    getLinkStyleVariants(baseStyle) {
        const variants = {
            'solid': ['solid', 'solid', 'solid', 'solid'], // Solid has 1 variant but 4 dots
            'dashed': ['dashed', 'dashed-wide', 'dotted', 'dotted-wide'],
            'arrow': ['arrow', 'double-arrow', 'dashed-arrow', 'dashed-double-arrow']
        };
        return variants[baseStyle] || ['solid'];
    }
    
    // Get which base style group a style belongs to
    getBaseStyleGroup(style) {
        const dashedStyles = ['dashed', 'dashed-wide', 'dotted', 'dotted-wide'];
        const arrowStyles = ['arrow', 'double-arrow', 'dashed-arrow', 'dashed-double-arrow'];
        
        if (dashedStyles.includes(style)) return 'dashed';
        if (arrowStyles.includes(style)) return 'arrow';
        return 'solid';
    }
    
    // Set style by clicking a specific dot
    setLinkStyleByIndex(baseStyle, index) {
        const variants = this.getLinkStyleVariants(baseStyle);
        const style = variants[index] || variants[0];
        this.setLinkStyle(style);
    }
    
    // Cycle through style variants
    cycleLinkStyle(baseStyle) {
        const variants = this.getLinkStyleVariants(baseStyle);
        const currentGroup = this.getBaseStyleGroup(this.linkStyle);
        
        if (currentGroup === baseStyle) {
            // Already in this group - cycle to next variant
            const currentIndex = variants.indexOf(this.linkStyle);
            const nextIndex = (currentIndex + 1) % variants.length;
            this.setLinkStyle(variants[nextIndex]);
        } else {
            // Different group - switch to first variant of this group
            this.setLinkStyle(variants[0]);
        }
    }
    
    setLinkStyle(style) {
        this.linkStyle = style;
        
        // Update all three buttons
        const solidBtn = document.getElementById('btn-link-style-solid');
        const dashedBtn = document.getElementById('btn-link-style-dashed');
        const arrowBtn = document.getElementById('btn-link-style-arrow');
        
        // Remove active from all
        if (solidBtn) solidBtn.classList.remove('active');
        if (dashedBtn) dashedBtn.classList.remove('active');
        if (arrowBtn) arrowBtn.classList.remove('active');
        
        // Add active to selected style
        if (style === 'solid' && solidBtn) {
            solidBtn.classList.add('active');
        } else if ((style === 'dashed' || style === 'dashed-wide' || style === 'dotted') && dashedBtn) {
            dashedBtn.classList.add('active');
        } else if ((style === 'arrow' || style === 'double-arrow' || style === 'dashed-arrow' || style === 'dashed-double-arrow') && arrowBtn) {
            arrowBtn.classList.add('active');
        }
        
        // Update dashed button icon to show current state
        if (dashedBtn) {
            const svg = dashedBtn.querySelector('svg');
            if (svg) {
                if (style === 'dashed-wide') {
                    // Wide dashed icon (more separated)
                    svg.innerHTML = `
                        <path d="M2 6h6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M14 6h6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M26 6h6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                    `;
                } else if (style === 'dotted') {
                    // Dotted icon
                    svg.innerHTML = `
                        <circle cx="4" cy="6" r="2" fill="currentColor"/>
                        <circle cx="12" cy="6" r="2" fill="currentColor"/>
                        <circle cx="20" cy="6" r="2" fill="currentColor"/>
                        <circle cx="28" cy="6" r="2" fill="currentColor"/>
                    `;
                } else {
                    // Regular dashed icon (default)
                    svg.innerHTML = `
                        <path d="M2 6h8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M14 6h8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M26 6h4" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                    `;
                }
            }
        }
        
        // Update arrow button icon to show current state
        if (arrowBtn) {
            const svg = arrowBtn.querySelector('svg');
            if (svg) {
                if (style === 'double-arrow') {
                    // Double arrow icon
                    svg.innerHTML = `
                        <path d="M8 6h16" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M8 9l-6-3 6-3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                        <path d="M24 3l6 3-6 3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                    `;
                } else if (style === 'dashed-arrow') {
                    // Dashed single arrow icon
                    svg.innerHTML = `
                        <path d="M2 6h8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M14 6h8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M24 3l6 3-6 3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                    `;
                } else if (style === 'dashed-double-arrow') {
                    // Dashed double arrow icon
                    svg.innerHTML = `
                        <path d="M10 6h4" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M18 6h4" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M8 9l-6-3 6-3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                        <path d="M24 3l6 3-6 3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                    `;
                } else {
                    // Single arrow icon (default)
                    svg.innerHTML = `
                        <path d="M2 6h24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                        <path d="M24 3l6 3-6 3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                    `;
                }
            }
        }
        
        // Update ALL selected links (multi-select support)
        let updatedLinks = 0;
        if (this.selectedObjects && this.selectedObjects.length > 0) {
            this.selectedObjects.forEach(obj => {
                if (obj.type === 'link' || obj.type === 'unbound') {
                    obj.style = style;
                    updatedLinks++;
                }
            });
        }
        // Also update single selected link if not in multi-select
        if (updatedLinks === 0 && this.selectedObject && (this.selectedObject.type === 'link' || this.selectedObject.type === 'unbound')) {
            this.selectedObject.style = style;
            updatedLinks++;
        }
        
        // Update variant indicators on the style buttons
        this.updateLinkStyleVariantIndicators(style);
        
        if (this.debugger) {
            const styleNames = {
                'solid': 'SOLID',
                'dashed': 'DASHED',
                'dashed-wide': 'DASHED (WIDE)',
                'dotted': 'DOTTED',
                'arrow': 'ARROW →',
                'double-arrow': 'DOUBLE-ARROW ⟷',
                'dashed-arrow': 'DASHED ARROW →',
                'dashed-double-arrow': 'DASHED DOUBLE-ARROW ⟷'
            };
            if (updatedLinks > 0) {
                this.debugger.logSuccess(`🎨 Applied ${styleNames[style] || style.toUpperCase()} to ${updatedLinks} link(s)`);
            } else {
                this.debugger.logInfo(`🎨 Default link style set to: ${styleNames[style] || style.toUpperCase()}`);
            }
        }
        
        this.draw(); // Redraw with new style
        this.scheduleAutoSave(); // Save setting change
    }
    
    // Update the dot indicators on link style buttons
    updateLinkStyleVariantIndicators(currentStyle) {
        const baseStyle = this.getBaseStyleGroup(currentStyle);
        
        ['solid', 'dashed', 'arrow'].forEach(btnStyle => {
            const btn = document.getElementById(`btn-link-style-${btnStyle}`);
            if (!btn) return;
            
            const variants = this.getLinkStyleVariants(btnStyle);
            const dots = btn.querySelectorAll('.style-dot');
            
            // Find which variant index is active
            const activeIndex = btnStyle === baseStyle ? variants.indexOf(currentStyle) : -1;
            
            dots.forEach((dot, index) => {
                dot.classList.toggle('active', index === (activeIndex >= 0 ? activeIndex : 0));
            });
        });
    }
    
    toggleDeviceNumbering() {
        this.deviceNumbering = !this.deviceNumbering;
        const btn = document.getElementById('btn-device-numbering');
        const statusText = btn ? btn.querySelector('.status-text') : null;
        
        if (!btn) {
            console.error('Device numbering button not found!');
            if (this.debugger) {
                this.debugger.logError('BUG: Numbering button element missing in DOM');
                this.debugger.logInfo('Code: toggleDeviceNumbering() [topology.js:2760]');
            }
            return;
        }
        
        if (this.deviceNumbering) {
            btn.classList.add('active');
            btn.title = 'Device Numbering ON - Auto-increment names (NCP, NCP-2, NCP-3...)';
            if (statusText) statusText.textContent = 'Numbering';
        } else {
            btn.classList.remove('active');
            btn.title = 'Device Numbering OFF - All devices use base name (NCP, S)';
            if (statusText) statusText.textContent = 'Numbering';
        }
        
        // Verify sync
        const hasActive = btn.classList.contains('active');
        if (this.debugger) {
            if (hasActive === this.deviceNumbering) {
                this.debugger.logSuccess(`✓ Numbering: ${this.deviceNumbering ? 'ON' : 'OFF'}`);
            } else {
                this.debugger.logError(`❌ Numbering desync! Auto-fixing...`);
                this.syncAllToggles(); // Auto-fix if desync detected
            }
        }
        
        this.scheduleAutoSave(); // Save setting change
    }
    
    toggleDeviceCollision() {
        this.deviceCollision = !this.deviceCollision;
        const btn = document.getElementById('btn-device-collision');
        const statusText = btn.querySelector('.status-text');
        const svg = btn.querySelector('svg');
        
        if (this.debugger) {
            this.debugger.logStateChange('Collision', this.deviceCollision ? 'OFF' : 'ON', this.deviceCollision ? 'ON' : 'OFF');
        }
        
        if (this.deviceCollision) {
            btn.classList.add('active');
            btn.title = 'Collision ON - Devices Cannot Overlap';
            if (statusText) statusText.textContent = 'Collision';
            svg.innerHTML = `
                <circle cx="8" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
                <circle cx="16" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
            `;
            this.fixExistingOverlaps();
        } else {
            btn.classList.remove('active');
            btn.title = 'Collision OFF - Devices Can Overlap';
            if (statusText) statusText.textContent = 'Collision';
            svg.innerHTML = `
                <circle cx="9" cy="12" r="5" stroke="currentColor" stroke-width="2" fill="none"/>
                <circle cx="15" cy="12" r="5" stroke="currentColor" stroke-width="2" fill="none"/>
            `;
        }
        this.scheduleAutoSave(); // Save setting change
    }
    
    setDeviceStyle(style) {
        console.log(`🎨 setDeviceStyle called with: ${style}`);
        
        // Set the default device style for new devices
        this.defaultDeviceStyle = style;
        localStorage.setItem('defaultDeviceStyle', style);
        
        console.log(`🎨 defaultDeviceStyle is now: ${this.defaultDeviceStyle}`);
        console.log(`🎨 localStorage value: ${localStorage.getItem('defaultDeviceStyle')}`);
        
        // Update style button states
        const styleButtons = ['circle', 'classic', 'simple', 'hex', 'server'];
        styleButtons.forEach(s => {
            const btn = document.getElementById(`btn-style-${s}`);
            if (btn) {
                if (s === style) {
                    btn.classList.add('active');
                    btn.style.background = 'rgba(52, 152, 219, 0.3)';
                    btn.style.borderColor = '#3498db';
                    const label = btn.querySelector('span');
                    if (label) label.style.color = '#fff';
                } else {
                    btn.classList.remove('active');
                    btn.style.background = 'rgba(255,255,255,0.05)';
                    btn.style.borderColor = 'transparent';
                    const label = btn.querySelector('span');
                    if (label) label.style.color = '#888';
                }
            }
        });
        
        // Also apply to selected device if there is one
        if (this.selectedObject && this.selectedObject.type === 'device') {
            this.saveState();
            this.selectedObject.visualStyle = style;
            // Reconnect links to device after style change
            this.reconnectLinksToDevice(this.selectedObject);
            this.draw();
            
            if (this.debugger) {
                this.debugger.logSuccess(`🎨 Device style changed to: ${style.toUpperCase()}`);
            }
        } else {
            if (this.debugger) {
                this.debugger.logInfo(`🎨 Default device style set to: ${style.toUpperCase()}`);
            }
        }
        
        // Force a UI refresh to ensure button states are visible
        this.scheduleAutoSave();
    }
    
    toggleMovableDevices() {
        this.movableDevices = !this.movableDevices;
        const btn = document.getElementById('btn-movable');
        const statusText = btn?.querySelector('.status-text');
        
        if (this.debugger) {
            this.debugger.logStateChange('Movable Devices', this.movableDevices ? 'OFF' : 'ON', this.movableDevices ? 'ON' : 'OFF');
        }
        
        if (btn) {
            if (this.movableDevices) {
                btn.classList.add('active');
                btn.title = 'Movable ON — Devices push each other when moved';
                if (statusText) statusText.textContent = 'Movable';
            } else {
                btn.classList.remove('active');
                btn.title = 'Movable OFF — Only the dragged device moves';
                if (statusText) statusText.textContent = 'Movable';
            }
        }
        this.scheduleAutoSave();
    }
    
    toggleMomentum() {
        if (!this.momentum) {
            console.error('Momentum engine not initialized!');
            if (this.debugger) {
                this.debugger.logError('BUG: Momentum engine not found!');
                this.debugger.logInfo('Check: topology-momentum.js loaded? [index.html:524]');
            }
            return;
        }
        
        const isEnabled = this.momentum.toggle();
        const btn = document.getElementById('btn-momentum');
        const statusText = btn?.querySelector('.status-text');
        const slideControl = document.getElementById('slide-distance-control');
        
        if (btn) {
            if (isEnabled) {
                btn.classList.add('active');
                btn.title = 'Momentum/Sliding ON - Objects Slide After Release';
                if (statusText) statusText.textContent = 'Slide';
                if (slideControl) slideControl.style.display = 'block';
            } else {
                btn.classList.remove('active');
                btn.title = 'Momentum/Sliding OFF';
                if (statusText) statusText.textContent = 'Slide';
                if (slideControl) slideControl.style.display = 'none';
            }
        }
        
        if (this.debugger) {
            this.debugger.logSuccess(`🎯 Momentum/Sliding: ${isEnabled ? 'ON' : 'OFF'}`);
            this.debugger.logInfo(`Slide distance control: ${isEnabled ? 'visible' : 'hidden'}`);
        }
        
        this.scheduleAutoSave();
    }
    
    syncAllToggles() {
        // Comprehensive sync of ALL toggle button states with their actual values
        // Called on initialization and when needed to fix desync issues
        
        const toggles = [
            {
                id: 'btn-device-numbering',
                state: this.deviceNumbering,
                name: 'Device Numbering',
                onText: 'Numbering',
                offText: 'Numbering'
            },
            {
                id: 'btn-device-collision',
                state: this.deviceCollision,
                name: 'Device Collision',
                onText: 'Collision',
                offText: 'Collision'
            },
            {
                id: 'btn-link-curve',
                state: this.linkCurveMode,
                name: 'Link Curve',
                onText: 'Curve: ON',
                offText: 'Curve: OFF'
            },
            {
                id: 'btn-link-continuous',
                state: this.linkContinuousMode,
                name: 'Link Continuous',
                onText: 'Chain: ON',
                offText: 'Chain: OFF'
            },
            {
                id: 'btn-angle-meter',
                state: this.showAngleMeter,
                name: 'Angle Meter',
                onText: 'Angle: ON',
                offText: 'Angle: OFF'
            }
        ];
        
        // Add momentum if available
        if (this.momentum) {
            toggles.push({
                id: 'btn-momentum',
                state: this.momentum.enabled,
                name: 'Momentum/Sliding',
                onText: 'Slide',
                offText: 'Slide'
            });
        }
        
        let syncCount = 0;
        let errorCount = 0;
        
        toggles.forEach(toggle => {
            const btn = document.getElementById(toggle.id);
            if (!btn) return;
            
            const hadActive = btn.classList.contains('active');
            const statusText = btn.querySelector('.status-text');
            
            // Force sync
            if (toggle.state) {
                btn.classList.add('active');
                if (statusText) statusText.textContent = toggle.onText;
            } else {
                btn.classList.remove('active');
                if (statusText) statusText.textContent = toggle.offText;
            }
            
            // Verify sync
            const hasActive = btn.classList.contains('active');
            if (hasActive === toggle.state) {
                syncCount++;
                if (this.debugger && hadActive !== hasActive) {
                    this.debugger.logSuccess(`✓ Synced ${toggle.name}: ${toggle.state ? 'ON' : 'OFF'}`);
                }
            } else {
                errorCount++;
                if (this.debugger) {
                    this.debugger.logError(`❌ Failed to sync ${toggle.name}!`);
                    this.debugger.logInfo(`Expected: ${toggle.state}, Got: ${hasActive}`);
                }
            }
        });
        
        if (this.debugger) {
            this.debugger.logSuccess(`Toggle Sync Complete: ${syncCount}/${toggles.length} synced${errorCount > 0 ? `, ${errorCount} errors` : ''}`);
            this.debugger.logInfo(`Code: syncAllToggles() [topology.js:2910-2994]`);
        }
        
        // Sync dependent control visibility
        // Curve magnitude slider - only visible when curve mode is ON
        const curveMagnitudeControl = document.getElementById('curve-magnitude-control');
        if (curveMagnitudeControl) {
            curveMagnitudeControl.style.display = this.linkCurveMode ? 'block' : 'none';
        }
        
        // Movable button - always visible (independent of collision)
        const movableBtn = document.getElementById('btn-movable');
        if (movableBtn) {
            movableBtn.style.display = 'inline-flex';
        }
        
        // Sync device style buttons with current default style
        const styleButtonsList = ['circle', 'classic', 'simple', 'hex', 'server'];
        styleButtonsList.forEach(s => {
            const btn = document.getElementById(`btn-style-${s}`);
            if (btn) {
                if (s === this.defaultDeviceStyle) {
                    btn.classList.add('active');
                    btn.style.background = 'rgba(52, 152, 219, 0.3)';
                    btn.style.borderColor = '#3498db';
                    const label = btn.querySelector('span');
                    if (label) label.style.color = '#fff';
                } else {
                    btn.classList.remove('active');
                    btn.style.background = 'rgba(255,255,255,0.05)';
                    btn.style.borderColor = 'transparent';
                    const label = btn.querySelector('span');
                    if (label) label.style.color = '#888';
                }
            }
        });
    }
    
    fixExistingOverlaps() {
        console.log('fixExistingOverlaps() called');
        
        // Automatically separate overlapping devices when collision is turned ON
        const devices = this.objects.filter(o => o.type === 'device');
        
        if (devices.length === 0) {
            if (this.debugger) {
                this.debugger.logWarning('No devices to check for overlaps');
            }
            return;
        }
        
        console.log('Checking', devices.length, 'devices for overlaps...');
        
        // Count initial overlaps
        let initialOverlaps = 0;
        const overlappingPairs = [];
        for (let i = 0; i < devices.length; i++) {
            for (let j = i + 1; j < devices.length; j++) {
                const d1 = devices[i];
                const d2 = devices[j];
                const dx = d1.x - d2.x;
                const dy = d1.y - d2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                // Use shape-aware collision radius
                const minDist = this.getDeviceCollisionRadius(d1) + this.getDeviceCollisionRadius(d2) + 3;
                if (dist < minDist) {
                    initialOverlaps++;
                    overlappingPairs.push(`${d1.label}-${d2.label}`);
                }
            }
        }
        
        console.log('Initial overlaps found:', initialOverlaps, overlappingPairs);
        
        if (this.debugger) {
            this.debugger.logInfo(`🔍 Scanning ${devices.length} devices, found ${initialOverlaps} overlap(s): ${overlappingPairs.join(', ')}`);
        }
        
        if (initialOverlaps === 0) {
            if (this.debugger) {
                this.debugger.logSuccess(`✓ No overlaps detected - all devices properly separated`);
            }
            return;
        }
        
        let fixedCount = 0;
        const maxIterations = 20;
        
        for (let iter = 0; iter < maxIterations; iter++) {
            let adjusted = false;
            
            for (let i = 0; i < devices.length; i++) {
                for (let j = i + 1; j < devices.length; j++) {
                    const d1 = devices[i];
                    const d2 = devices[j];
                    
                    const dx = d1.x - d2.x;
                    const dy = d1.y - d2.y;
                    let dist = Math.sqrt(dx * dx + dy * dy);
                    
                    // Handle coincident centers first
                    let nx, ny, angle;
                    const epsilon = 0.01;
                    if (dist < epsilon) {
                        nx = 1; ny = 0; dist = epsilon; angle = 0;
                    } else {
                        nx = dx / dist; ny = dy / dist;
                        angle = Math.atan2(dy, dx);
                    }
                    
                    // SHAPE-ACCURATE COLLISION: Use direction-aware radii
                    const minDist = this.getDeviceCollisionRadiusInDirection(d1, angle) + 
                                   this.getDeviceCollisionRadiusInDirection(d2, angle + Math.PI) + 3;
                    
                    if (dist < minDist) {
                        // Push devices apart (split the push between both)
                        const push = (minDist - dist) / 2;
                        
                        // Apply push with extra margin for safety
                        const extraMargin = 1.1; // 10% extra to ensure separation
                        d1.x += nx * push * extraMargin;
                        d1.y += ny * push * extraMargin;
                        d2.x -= nx * push * extraMargin;
                        d2.y -= ny * push * extraMargin;
                        
                        adjusted = true;
                        fixedCount++;
                    }
                }
            }
            
            if (!adjusted) break; // No more overlaps
        }
        
        console.log('Fix iterations complete. Fixed count:', fixedCount);
        
        // Verify overlaps are actually fixed
        let remainingOverlaps = 0;
        for (let i = 0; i < devices.length; i++) {
            for (let j = i + 1; j < devices.length; j++) {
                const d1 = devices[i];
                const d2 = devices[j];
                const dx = d1.x - d2.x;
                const dy = d1.y - d2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                // SHAPE-ACCURATE COLLISION: Use direction-aware radii
                const angle = Math.atan2(dy, dx);
                const minDist = this.getDeviceCollisionRadiusInDirection(d1, angle) + 
                               this.getDeviceCollisionRadiusInDirection(d2, angle + Math.PI) + 3;
                if (dist < minDist) {
                    remainingOverlaps++;
                    console.warn('Still overlapping:', d1.label, d2.label, 'dist:', dist, 'minDist:', minDist);
                }
            }
        }
        
        if (fixedCount > 0) {
            this.draw();
            this.saveState();
            
            if (this.debugger) {
                if (remainingOverlaps > 0) {
                    this.debugger.logWarning(`⚠️ Partially fixed: ${initialOverlaps - remainingOverlaps}/${initialOverlaps} overlaps resolved`);
                    this.debugger.logWarning(`${remainingOverlaps} overlaps still remain - may need larger separation`);
                    this.debugger.logInfo(`Code: fixExistingOverlaps() [2782] - increase extraMargin?`);
                } else {
                    this.debugger.logSuccess(`✓ Fixed ${initialOverlaps} overlap(s) in ${fixedCount} pushes - ALL RESOLVED!`);
                }
            }
        } else if (initialOverlaps > 0) {
            if (this.debugger) {
                this.debugger.logError(`❌ BUG: ${initialOverlaps} overlaps detected but no fixes applied!`);
                this.debugger.logInfo(`Code: fixExistingOverlaps() [2782-2880] - check iteration logic`);
            }
        }
    }
    
    updateCurveMagnitude(value) {
        const oldValue = this.magneticFieldStrength;
        this.magneticFieldStrength = parseInt(value);
        const curveMagnitudeValue = document.getElementById('curve-magnitude-value');
        if (curveMagnitudeValue) curveMagnitudeValue.textContent = value;

        // Log to debugger (throttled)
        if (this.debugger && Math.abs(oldValue - this.magneticFieldStrength) >= 10) {
            this.debugger.logInfo(`〰️ Curve magnitude: ${this.magneticFieldStrength}/80`);
        }

        // ENHANCED: Immediate redraw for smooth real-time feedback
        // Use requestAnimationFrame for buttery smooth updates
        if (this.magneticFieldUpdateTimer) {
            cancelAnimationFrame(this.magneticFieldUpdateTimer);
        }
        this.magneticFieldUpdateTimer = requestAnimationFrame(() => {
            this.draw(); // Redraw links with new magnetic strength
            this.magneticFieldUpdateTimer = null;
        });
        
        // Throttle auto-save separately to avoid excessive saves
        if (this.magneticFieldSaveTimer) {
            clearTimeout(this.magneticFieldSaveTimer);
        }
        this.magneticFieldSaveTimer = setTimeout(() => {
            this.scheduleAutoSave();
            this.magneticFieldSaveTimer = null;
        }, 500); // Save after 500ms of no changes
    }
    
    updateFriction(value) {
        // ULTRA-ENHANCED: Slider 1-10 controls ALL sliding parameters dynamically
        // Lower slider value = MORE DRAMATIC sliding (faster, farther, bigger bounces)
        const sliderValue = parseInt(value);
        
        if (this.debugger) {
            this.debugger.logAction(`🎮 Slider moved to ${sliderValue}/10 - Updating ALL sliding parameters...`);
        }
        
        // Update momentum engine slider value
        if (this.momentum) {
            this.momentum.sliderValue = sliderValue;
            // Recalculate ALL dynamic parameters
            this.momentum.updateDynamicParameters();
        }
        
        // Update display to show slider value (1-10)
        const valueDisplay = document.getElementById('friction-value');
        if (valueDisplay) {
            valueDisplay.textContent = sliderValue;
        }
        
        // Log to debugger with ALL updated parameters (AFTER update)
        if (this.debugger && this.momentum) {
            const slideDescriptions = [
                'ULTRA-EXTREME (Ice Hockey)', 'Massive Slides', 'Very Far', 'Far', 'Medium',
                'Medium-Short', 'Short', 'Very Short', 'Minimal', 'Nearly Stops'
            ];
            const slideDistance = slideDescriptions[sliderValue - 1];
            
            this.debugger.logSuccess(`⚡ SLIDER ${sliderValue}/10: ${slideDistance}`);
            this.debugger.logInfo(`📊 ALL 8 Parameters Updated:`);
            this.debugger.logInfo(`   1️⃣ Friction: ${this.momentum.friction.toFixed(3)} (deceleration)`);
            this.debugger.logInfo(`   2️⃣ Velocity Multiplier: ${this.momentum.velocityMultiplier.toFixed(2)}x (launch boost)`);
            this.debugger.logInfo(`   3️⃣ Min Velocity: ${this.momentum.minVelocity.toFixed(2)} (stop threshold)`);
            this.debugger.logInfo(`   4️⃣ Max Speed: ${this.momentum.maxSpeed.toFixed(0)} px/frame (speed cap)`);
            this.debugger.logInfo(`   5️⃣ Collision Boost: ${this.momentum.collisionBoost.toFixed(2)}x (bump energy)`);
            this.debugger.logInfo(`   6️⃣ Restitution: ${(this.momentum.restitution * 100).toFixed(0)}% (elastic)`);
            this.debugger.logInfo(`   7️⃣ Momentum Transfer: ${(this.momentum.momentumTransferRatio * 100).toFixed(0)}% (chain reactions)`);
            this.debugger.logInfo(`   8️⃣ Rolling Friction: ${this.momentum.rollingFriction.toFixed(3)} (smoothness)`);
            this.debugger.logSuccess(`✅ SYNC CONFIRMED: All parameters active!`);
        }
        
        // Save to localStorage
        if (this.momentum) {
            localStorage.setItem('momentum_friction', this.momentum.friction);
            localStorage.setItem('momentum_slider', sliderValue);
        }
        
        this.scheduleAutoSave();
    }
    
    applyDeviceChainReaction(movingDevice, velocityX, velocityY, depth = 0, processedDevices = new Set()) {
        // Prevent infinite recursion and skip if no velocity
        if (depth > 8 || processedDevices.has(movingDevice.id)) return; // Increased from 5 to 8 for longer chains
        // CRITICAL: Very low threshold to ensure all collisions propagate (A→B→C→D...)
        const velocityMag = Math.sqrt(velocityX * velocityX + velocityY * velocityY);
        if (velocityMag < 0.01) return; // Check magnitude, not individual components
        
        processedDevices.add(movingDevice.id);
        
        // DEBUG: Log chain reaction entry
        if (this.debugger && depth > 0 && depth <= 3) {
            this.debugger.logInfo(`Chain reaction depth ${depth + 1}: ${movingDevice.label || 'Device'} (v=${velocityMag.toFixed(2)}px)`);
        }
        
        // Find all devices that this device is colliding with
        const otherDevices = this.objects.filter(obj => 
            obj.type === 'device' && 
            obj.id !== movingDevice.id && 
            !processedDevices.has(obj.id)
        );
        
        const pushedDevices = [];
        
        for (const targetDevice of otherDevices) {
            // Calculate distance between devices
            const dx = targetDevice.x - movingDevice.x;
            const dy = targetDevice.y - movingDevice.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            // Calculate angle for direction-aware collision
            const angle = Math.atan2(dy, dx);
            
            // SHAPE-ACCURATE COLLISION: Get radius in the exact direction of collision
            const movingRadius = this.getDeviceCollisionRadiusInDirection(movingDevice, angle);
            const targetRadius = this.getDeviceCollisionRadiusInDirection(targetDevice, angle + Math.PI);
            const minDist = movingRadius + targetRadius + 1;  // Minimal gap - shape-accurate
            
            // CRITICAL FIX: Trigger chain reaction when devices are CLOSE (not just overlapping)
            // Add a threshold zone where devices can push each other
            const proximityThreshold = 3; // Devices within 3px of touching can push each other
            const effectiveMinDist = minDist + proximityThreshold;
            
            // Check if devices are colliding, overlapping, or very close
            if (dist < effectiveMinDist && dist > 0.01) {
                // Calculate collision normal (direction from moving device to target)
                const nx = dx / dist;
                const ny = dy / dist;
                
                // Calculate velocity component in collision direction
                const velocityAlongNormal = velocityX * nx + velocityY * ny;
                
                // Store old position
                const oldX = targetDevice.x;
                const oldY = targetDevice.y;
                
                // ENHANCED: When collision is ON, always separate devices that overlap
                if (this.deviceCollision) {
                    // Calculate overlap amount (negative if not yet touching)
                    const overlap = minDist - dist;
                    
                    // ENHANCED: Better momentum transfer for chain reactions
                    const transferRatio = 0.85; // Increased from 0.7 for stronger transfer
                    const momentumPush = Math.max(0, velocityAlongNormal * transferRatio);
                    
                    // Separation push only applies if actually overlapping
                    const separationPush = overlap > 0 ? overlap * 1.5 : 0; // Increased from 1.2
                    
                    // Total push = momentum transfer + separation force
                    const totalPush = momentumPush + separationPush;
                    
                    // Only push if there's actual momentum or overlap
                    if (totalPush > 0.01) {
                        const pushX = nx * totalPush;
                        const pushY = ny * totalPush;
                        
                        // Apply push to target device
                        let newX = targetDevice.x + pushX;
                        let newY = targetDevice.y + pushY;
                        
                        // CRITICAL: Don't apply collision detection to pushed device during chain reaction
                        // This was preventing S from moving when S2 pushed it (infinite loop prevention)
                        // Just apply the push directly and let the next frame handle collisions
                        // const proposedPos = this.checkDeviceCollision(targetDevice, newX, newY);
                        // newX = proposedPos.x;
                        // newY = proposedPos.y;
                        
                        // CRITICAL: Also push back the moving device slightly to prevent overlap
                        // This creates a more realistic "bounce" effect
                        if (depth === 0 && overlap > 5) { // Only for direct hits with significant overlap
                            const pushBackRatio = 0.2; // Moving device gets pushed back 20% of the separation
                            movingDevice.x -= nx * overlap * pushBackRatio;
                            movingDevice.y -= ny * overlap * pushBackRatio;
                        }
                        
                        // Update target device position
                        targetDevice.x = newX;
                        targetDevice.y = newY;
                        
                        // Store for chain reaction
                        pushedDevices.push({
                            device: targetDevice,
                            velocityX: newX - oldX,
                            velocityY: newY - oldY
                        });
                        
                        // ENHANCED: Log collision with chain depth indicator
                        if (this.debugger && depth <= 3) { // Log first 4 levels
                            const pushMag = Math.sqrt(pushX*pushX + pushY*pushY);
                            const chainIndicator = depth > 0 ? ` [chain ${depth + 1}]` : '';
                            this.debugger.logInfo(`🎱 Push${chainIndicator}: ${movingDevice.label || 'Device'} → ${targetDevice.label || 'Device'} (${pushMag.toFixed(1)}px, overlap: ${overlap.toFixed(1)}px)`);
                        }
                    }
                } else {
                    // No collision mode - only push if moving towards the device
                    if (velocityAlongNormal > 0) {
                        // ENHANCED: Better momentum transfer for smooth chain reactions
                        const transferRatio = 0.85; // Increased from 0.7 for stronger propagation
                        const pushX = velocityAlongNormal * nx * transferRatio;
                        const pushY = velocityAlongNormal * ny * transferRatio;
                        
                        // Apply push to target device
                        let newX = targetDevice.x + pushX;
                        let newY = targetDevice.y + pushY;
                        
                        // Update target device position
                        targetDevice.x = newX;
                        targetDevice.y = newY;
                        
                        // Store for chain reaction
                        pushedDevices.push({
                            device: targetDevice,
                            velocityX: newX - oldX,
                            velocityY: newY - oldY
                        });
                        
                        // ENHANCED: Log chain reactions with depth indicator
                        if (this.debugger && depth <= 2) { // Log first 3 levels
                            const chainIndicator = depth > 0 ? ` (chain ${depth + 1})` : '';
                            this.debugger.logInfo(`🎱 Push${chainIndicator}: ${movingDevice.label || 'Device'} → ${targetDevice.label || 'Device'} (${Math.sqrt(pushX*pushX + pushY*pushY).toFixed(1)}px)`);
                        }
                    }
                }
            }
        }
        
        // Chain reaction: pushed devices may push other devices
        for (const { device, velocityX: vx, velocityY: vy } of pushedDevices) {
            this.applyDeviceChainReaction(device, vx, vy, depth + 1, processedDevices);
        }
    }
    
    /**
     * Get the effective collision radius for a device based on its visual style.
     * This ensures collision detection matches the actual visual surface of each device shape.
     * @param {Object} device - The device object
     * @returns {number} The effective collision radius
     */
    /**
     * Get the visual bounds of a device based on its style.
     * Returns dimensions that match the EXACT visual shape - no buffer.
     */
    getDeviceVisualBounds(device) {
        const r = device.radius || 30;
        const style = device.visualStyle || 'circle';
        const rotation = (device.rotation || 0) * Math.PI / 180;
        
        switch (style) {
            case 'circle':
            case 'simple':
                // Circle: symmetric in all directions - exact radius
                return { type: 'circle', radius: r };
                
            case 'server': {
                // Server Tower: width=r*0.9, height=r*1.6, 3D depth=r*0.4
                // The 3D effect makes the shape ASYMMETRIC relative to device center:
                // - Left edge at: -0.45r (half of front width)
                // - Right edge at: +0.73r (front + 3D depth*0.7)
                // - Top edge at: -0.8r
                // - Bottom edge at: +0.8r
                // 
                // For direction-aware collision, we store the actual extents
                return { 
                    type: 'server',  // Special type for asymmetric handling
                    leftExtent: 0.45 * r,   // Distance from center to left edge
                    rightExtent: 0.73 * r,  // Distance from center to right edge (with 3D)
                    topExtent: 0.8 * r,     // Distance from center to top edge
                    bottomExtent: 0.8 * r,  // Distance from center to bottom edge
                    rotation: rotation
                };
            }
                
            case 'hex':
                // Hexagon: hexRadius = r * 0.65, shadow offset = r * 0.08
                return { 
                    type: 'hexagon',
                    hexRadius: r * 0.65 + r * 0.08  // Exact hex + shadow
                };
                
            case 'classic':
                // Classic 3D Cylinder: width=r*1.6, height=r*1.0 (matches drawDeviceClassicRouter)
                // The cylinder is wide (1.6r) and not very tall (1.0r)
                return { 
                    type: 'ellipse',
                    width: r * 1.6,   // Matches actual drawing width
                    height: r * 1.0,  // topHeight + bodyHeight
                    rotation: rotation
                };
                
            default:
                return { type: 'circle', radius: r };
        }
    }
    
    /**
     * Check if two devices are colliding based on their visual shapes.
     * Returns true if shapes overlap, false otherwise.
     */
    checkShapeCollision(device1, x1, y1, device2, x2, y2) {
        const bounds1 = this.getDeviceVisualBounds(device1);
        const bounds2 = this.getDeviceVisualBounds(device2);
        
        // For simplicity, we'll use bounding circle approximation for mixed shapes
        // but with accurate radii based on actual visual dimensions
        const getEffectiveRadius = (bounds) => {
            switch (bounds.type) {
                case 'circle':
                    return bounds.radius;
                case 'rectangle':
                    // Half-diagonal for rotated rectangle
                    return Math.sqrt((bounds.width/2)**2 + (bounds.height/2)**2);
                case 'hexagon':
                    return bounds.hexRadius;
                case 'ellipse':
                    // Use the larger axis
                    return Math.max(bounds.width/2, bounds.height/2);
                default:
                    return 30;
            }
        };
        
        const r1 = getEffectiveRadius(bounds1);
        const r2 = getEffectiveRadius(bounds2);
        
        const dx = x1 - x2;
        const dy = y1 - y2;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        return dist < (r1 + r2);
    }
    
    /**
     * Get the minimum distance two devices should be apart based on their visual shapes.
     * This ensures 1:1 hitbox matching with visual appearance.
     */
    getMinimumSeparation(device1, device2) {
        const bounds1 = this.getDeviceVisualBounds(device1);
        const bounds2 = this.getDeviceVisualBounds(device2);
        
        // Calculate effective collision radius for each shape
        const getEffectiveRadius = (bounds) => {
            switch (bounds.type) {
                case 'circle':
                    return bounds.radius;
                case 'rectangle':
                    // For rectangle, use half-diagonal (bounding circle)
                    return Math.sqrt((bounds.width/2)**2 + (bounds.height/2)**2);
                case 'hexagon':
                    return bounds.hexRadius;
                case 'ellipse':
                    // Use the larger semi-axis
                    return Math.max(bounds.width/2, bounds.height/2);
                default:
                    return device1.radius || 30;
            }
        };
        
        return getEffectiveRadius(bounds1) + getEffectiveRadius(bounds2);
    }
    
    // Get collision radius in a specific direction (angle in radians)
    getDeviceCollisionRadiusInDirection(device, angle) {
        if (window.DevicePlacement) {
            return window.DevicePlacement.getCollisionRadiusInDirection(this, device, angle);
        }
        return device.radius || 30;
    }
    
    // Get collision radius using bounding circle
    getDeviceCollisionRadius(device) {
        if (window.DevicePlacement) {
            return window.DevicePlacement.getCollisionRadius(this, device);
        }
        return device.radius || 30;
    }
    
    checkDeviceCollision(movingDevice, proposedX, proposedY) {
        if (window.DevicePlacement) {
            return window.DevicePlacement.checkCollision(this, movingDevice, proposedX, proposedY);
        }
        return { x: proposedX, y: proposedY };
    }
    
    setTool(tool) {
        // Legacy function - now uses setMode()
        this.setMode(tool === 'select' ? 'base' : tool);
    }
    
    setDevicePlacementMode(deviceType) {
        this.multiSelectMode = false;
        this.selectedObjects = [];
        this.selectedObject = null;
        
        this.placingDevice = deviceType;
        this.currentTool = 'select';
        this.canvas.style.cursor = 'crosshair';
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
    }
    
    addDeviceAtPosition(type, x, y) {
        // Delegate to DeviceManager if available
        if (this.devices) {
            const device = this.devices.addAtPosition(type, x, y);
            if (device) {
                this.saveState();
                this.autoSave();
            }
            return device;
        }
        return null;
    }
    
    startMultiSelect(pos) {
        this.multiSelectMode = true;
        // CRITICAL: Clear tap tracking when long press is detected
        // This prevents long press from being mistaken for double-tap
        this.lastTapTime = 0;
        this._lastTapDevice = null;
        this._lastTapPos = null;
        this._lastTapStartTime = 0;
        
        const clickedObject = this.findObjectAt(pos.x, pos.y);
        if (clickedObject && !this.selectedObjects.includes(clickedObject)) {
            this.selectedObjects.push(clickedObject);
            this.selectedObject = clickedObject;
            
            // If Ctrl+clicking a UL that's part of a BUL, add the whole chain
            if (clickedObject.type === 'unbound' && (clickedObject.mergedWith || clickedObject.mergedInto)) {
                const chain = this.getAllMergedLinks(clickedObject);
                chain.forEach(link => {
                    if (!this.selectedObjects.includes(link)) {
                        this.selectedObjects.push(link);
                    }
                });
            }
        }
        this.draw();
    }
    
    // CS-MS MODE: Special marquee selection that pastes copied style to all selected objects
    // Triggered by clicking on empty space or long press while in paste style mode
    startCSMSMode(pos) {
        // Enter CS-MS mode
        this.csmsMode = true;
        this.marqueeActive = true;
        this.selectionRectStart = pos;
        this.selectionRectangle = null;
        this.selectedObjects = [];
        this.selectedObject = null;
        this.multiSelectMode = false;
        
        // Clear tap tracking
        this.lastTapTime = 0;
        this._lastTapDevice = null;
        this._lastTapPos = null;
        this._lastTapStartTime = 0;
        
        // Visual feedback - crosshair cursor for selection
        this.canvas.style.cursor = 'crosshair';
        
        if (this.debugger) {
            this.debugger.logSuccess(`CS-MS: Drag to select objects, release to apply style`);
        }
        
        this.draw();
    }
    
    startMarqueeSelection(pos) {
        // CRITICAL FIX: Don't start marquee if a double-click just happened (UL was created)
        const timeSinceDoubleClick = Date.now() - (this.lastDoubleClickTime || 0);
        if (timeSinceDoubleClick < 100) {
            // Double-click just happened - skip marquee to prevent UL + MS conflict
            if (this.debugger) {
                this.debugger.logInfo(`🚫 Marquee blocked - double-click was ${timeSinceDoubleClick}ms ago`);
            }
            return;
        }
        
        // Store the mode we came from for seamless transition back
        const previousMode = this.currentMode;
        
        this.marqueeActive = true;
        this.selectionRectStart = pos;
        this.selectionRectangle = null;
        this.selectedObjects = [];
        this.selectedObject = null;
        this.multiSelectMode = false; // Clear multi-select state
        this.resumeModeAfterMarquee = previousMode; // Store for transition back
        this.currentMode = 'select'; // Temporarily enter select mode for marquee
        
        if (this.debugger) {
            this.debugger.logInfo(`Marquee started from ${(previousMode || 'unknown').toUpperCase()} mode`);
            this.debugger.logInfo(`Code: startMarqueeSelection() [topology.js:2991]`);
        }
    }
    
    findObjectsInRectangle(rect) {
        const selected = [];
        // Scale tolerances so they are constant in screen pixels regardless of zoom
        const pixelScale = 1 / this.zoom;
        const thinLineTolerance = 3 * pixelScale; // ~3px in screen space
        
        // Detect if this is a thin line selection based on ~10px in screen space
        const isThinSelection = rect.width < 10 * pixelScale || rect.height < 10 * pixelScale;
        const tolerance = isThinSelection ? thinLineTolerance : 0;
        
        this.objects.forEach(obj => {
            // NOTE: Locked objects ARE selected via marquee, but they won't move when dragged
            // This allows bulk operations (color, delete, etc.) on locked objects
            
            let intersects = false;
            
            if (obj.type === 'device') {
                // Check if device circle overlaps with rectangle (any pixel overlap counts)
                const closestX = Math.max(rect.x - tolerance, Math.min(obj.x, rect.x + rect.width + tolerance));
                const closestY = Math.max(rect.y - tolerance, Math.min(obj.y, rect.y + rect.height + tolerance));
                    const dist = Math.sqrt(Math.pow(obj.x - closestX, 2) + Math.pow(obj.y - closestY, 2));
                
                // Select if ANY part of the circle touches the rectangle
                    intersects = dist <= obj.radius;
            } else if (obj.type === 'text') {
                // Check if text center is in rectangle
                intersects = obj.x >= rect.x - tolerance && obj.x <= rect.x + rect.width + tolerance &&
                            obj.y >= rect.y - tolerance && obj.y <= rect.y + rect.height + tolerance;
            } else if ((obj.type === 'link' || obj.type === 'unbound') && obj.start && obj.end) {
                // Enhanced link hitbox - detects any touch along the entire link path (includes unbound links)
                const linkHitboxTolerance = 8 * pixelScale; // ~8px in screen space
                
                // Check endpoints first
                const startInRect = obj.start.x >= rect.x - tolerance && obj.start.x <= rect.x + rect.width + tolerance &&
                                   obj.start.y >= rect.y - tolerance && obj.start.y <= rect.y + rect.height + tolerance;
                const endInRect = obj.end.x >= rect.x - tolerance && obj.end.x <= rect.x + rect.width + tolerance &&
                                 obj.end.y >= rect.y - tolerance && obj.end.y <= rect.y + rect.height + tolerance;
                
                if (startInRect || endInRect) {
                    intersects = true;
                } else {
                    // Sample many points along link path with wide hitbox tolerance
                    // FIXED: Calculate curve control points if not stored (for real-time MS)
                    const samples = 30;
                    let cp1x, cp1y, cp2x, cp2y;
                    let hasCurve = false;
                    
                    // Check if curve mode is enabled for this link
                    const curveEnabled = (obj.curveOverride !== undefined ? obj.curveOverride : this.linkCurveMode) && this.magneticFieldStrength > 0;
                    
                    if (curveEnabled) {
                        // Use stored control points if available
                        if (obj._cp1 && obj._cp2) {
                            cp1x = obj._cp1.x;
                            cp1y = obj._cp1.y;
                            cp2x = obj._cp2.x;
                            cp2y = obj._cp2.y;
                            hasCurve = true;
                        } else {
                            // Calculate control points on-the-fly (same algorithm as drawing)
                            const obstacles = this.findAllObstaclesOnPath(obj.start.x, obj.start.y, obj.end.x, obj.end.y, obj);
                            
                            if (obstacles.length > 0) {
                                const straightMidX = (obj.start.x + obj.end.x) / 2;
                                const straightMidY = (obj.start.y + obj.end.y) / 2;
                                const linkLength = Math.sqrt(Math.pow(obj.end.x - obj.start.x, 2) + Math.pow(obj.end.y - obj.start.y, 2));
                                
                                const linkDirX = (obj.end.x - obj.start.x) / linkLength;
                                const linkDirY = (obj.end.y - obj.start.y) / linkLength;
                                
                                let totalRepulsionX = 0;
                                let totalRepulsionY = 0;
                                let closestObstacleRadius = 0;
                                
                                obstacles.forEach((obstacleInfo) => {
                                    const obstacle = obstacleInfo.device;
                                    const toObstacleX = obstacle.x - obj.start.x;
                                    const toObstacleY = obstacle.y - obj.start.y;
                                    const projLength = toObstacleX * linkDirX + toObstacleY * linkDirY;
                                    const closestOnLineX = obj.start.x + linkDirX * projLength;
                                    const closestOnLineY = obj.start.y + linkDirY * projLength;
                                    const towardObstacleX = obstacle.x - closestOnLineX;
                                    const towardObstacleY = obstacle.y - closestOnLineY;
                                    const perpDist = Math.sqrt(towardObstacleX * towardObstacleX + towardObstacleY * towardObstacleY) || 0.1;
                                    const requiredClearance = obstacle.radius + 25;
                                    const neededDeflection = Math.max(0, requiredClearance - perpDist + 20);
                                    const awayFromObstacleX = -towardObstacleX / perpDist;
                                    const awayFromObstacleY = -towardObstacleY / perpDist;
                                    const proximityFactor = requiredClearance / (perpDist + 1);
                                    const repulsionStrength = neededDeflection * proximityFactor * this.magneticFieldStrength;
                                    totalRepulsionX += awayFromObstacleX * repulsionStrength;
                                    totalRepulsionY += awayFromObstacleY * repulsionStrength;
                                    closestObstacleRadius = Math.max(closestObstacleRadius, obstacle.radius);
                                });
                                
                                const deflectionMag = Math.sqrt(totalRepulsionX * totalRepulsionX + totalRepulsionY * totalRepulsionY);
                                const maxDeflection = Math.max(linkLength * 0.6, closestObstacleRadius * 3);
                                const actualDeflection = Math.min(deflectionMag, maxDeflection);
                                const normalizedRepulX = totalRepulsionX / (deflectionMag || 1);
                                const normalizedRepulY = totalRepulsionY / (deflectionMag || 1);
                                const deflectedMidX = straightMidX + normalizedRepulX * actualDeflection;
                                const deflectedMidY = straightMidY + normalizedRepulY * actualDeflection;
                                
                                const controlWeight = 0.7;
                                const midWeight = 1 - controlWeight;
                                cp1x = obj.start.x * midWeight + deflectedMidX * controlWeight;
                                cp1y = obj.start.y * midWeight + deflectedMidY * controlWeight;
                                cp2x = obj.end.x * midWeight + deflectedMidX * controlWeight;
                                cp2y = obj.end.y * midWeight + deflectedMidY * controlWeight;
                                hasCurve = true;
                            }
                        }
                    }
                    
                    for (let i = 0; i <= samples; i++) {
                        const t = i / samples;
                        let px, py;
                        
                        if (hasCurve) {
                            // Sample along Bezier curve
                            px = Math.pow(1-t, 3) * obj.start.x + 
                                 3 * Math.pow(1-t, 2) * t * cp1x + 
                                 3 * (1-t) * Math.pow(t, 2) * cp2x + 
                                 Math.pow(t, 3) * obj.end.x;
                            py = Math.pow(1-t, 3) * obj.start.y + 
                                 3 * Math.pow(1-t, 2) * t * cp1y + 
                                 3 * (1-t) * Math.pow(t, 2) * cp2y + 
                                 Math.pow(t, 3) * obj.end.y;
                        } else {
                            // Straight line sampling
                            px = obj.start.x + (obj.end.x - obj.start.x) * t;
                            py = obj.start.y + (obj.end.y - obj.start.y) * t;
                        }
                        
                        // Expand hitbox around each sampled point
                        if (px >= rect.x - linkHitboxTolerance && px <= rect.x + rect.width + linkHitboxTolerance &&
                            py >= rect.y - linkHitboxTolerance && py <= rect.y + rect.height + linkHitboxTolerance) {
                            intersects = true;
                            break;
                        }
                    }
                    
                    // Also check if link line intersects rectangle edges (for straight links)
                    if (!intersects && !hasCurve) {
                        intersects = this.lineIntersectsRect(obj.start, obj.end, rect);
                    }
                }
            } else if (obj.type === 'shape') {
                // Shape hit detection - check bounding box overlap
                const shapeLeft = obj.x - (obj.width || 50) / 2;
                const shapeRight = obj.x + (obj.width || 50) / 2;
                const shapeTop = obj.y - (obj.height || 50) / 2;
                const shapeBottom = obj.y + (obj.height || 50) / 2;
                
                // Check for any overlap between shape bounding box and selection rectangle
                const rectRight = rect.x + rect.width;
                const rectBottom = rect.y + rect.height;
                
                intersects = !(shapeRight < rect.x - tolerance || 
                              shapeLeft > rectRight + tolerance || 
                              shapeBottom < rect.y - tolerance || 
                              shapeTop > rectBottom + tolerance);
            }
            
            if (intersects) {
                selected.push(obj);
            }
        });
        
        return selected;
    }
    
    lineIntersectsRect(lineStart, lineEnd, rect) {
        // Check if line segment intersects with rectangle
        // Test all 4 edges of rectangle
        const rectEdges = [
            { start: { x: rect.x, y: rect.y }, end: { x: rect.x + rect.width, y: rect.y } }, // Top
            { start: { x: rect.x + rect.width, y: rect.y }, end: { x: rect.x + rect.width, y: rect.y + rect.height } }, // Right
            { start: { x: rect.x + rect.width, y: rect.y + rect.height }, end: { x: rect.x, y: rect.y + rect.height } }, // Bottom
            { start: { x: rect.x, y: rect.y + rect.height }, end: { x: rect.x, y: rect.y } } // Left
        ];
        
        for (const edge of rectEdges) {
            if (this.lineSegmentsIntersect(lineStart, lineEnd, edge.start, edge.end)) {
                return true;
            }
        }
        return false;
    }
    
    lineSegmentsIntersect(p1, p2, p3, p4) {
        // Check if line segment p1-p2 intersects with p3-p4
        const ccw = (A, B, C) => {
            return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x);
        };
        return ccw(p1, p3, p4) !== ccw(p2, p3, p4) && ccw(p1, p2, p3) !== ccw(p1, p2, p4);
    }
    
    showMarqueeContextMenu(x, y) {
        if (window.ContextMenus) {
            return window.ContextMenus.showMarqueeContextMenu(this, x, y);
        }
    }
    
    duplicateObject(obj, mirror = false) {
        this.saveState(); // Save before duplicating
        let duplicate;
        
        // ENHANCED: Calculate offset to place duplicate without overlap
        const offsetX = 80; // Horizontal offset
        const offsetY = 40; // Vertical offset
        
        if (obj.type === 'device') {
            const label = this.getNextDeviceLabel(obj.deviceType);
            duplicate = {
                id: `device_${this.deviceIdCounter++}`,
                type: 'device',
                deviceType: obj.deviceType,
                x: obj.x + offsetX,
                y: obj.y + offsetY,
                radius: obj.radius,
                rotation: obj.rotation || 0,
                color: obj.color,
                label: label,
                locked: false,
                visualStyle: obj.visualStyle || this.defaultDeviceStyle || 'circle',
                layer: obj.layer,
                fontFamily: obj.fontFamily,
                fontWeight: obj.fontWeight,
                labelColor: obj.labelColor,
                labelSize: obj.labelSize,
                labelOutlineColor: obj.labelOutlineColor
            };
        } else if (obj.type === 'text') {
            // ENHANCED: If text is attached to a link, duplicate the link with all its properties
            if (obj.linkId) {
                const sourceLink = this.objects.find(o => o.id === obj.linkId);
                if (sourceLink) {
                    // Check if it's part of a BUL chain
                    if (sourceLink.type === 'unbound' && (sourceLink.mergedWith || sourceLink.mergedInto)) {
                        // Duplicate the entire BUL chain with all attached TBs
                        this.duplicateBULChain(sourceLink, offsetX, offsetY);
                        return; // duplicateBULChain handles everything
                    }
                    
                    // Single link (unbound or regular link) - duplicate it with all properties
                    // Handle both 'link' and 'unbound' types
                    const linkType = (sourceLink.type === 'link' || sourceLink.type === 'unbound') ? sourceLink.type : 'unbound';
                    const newLink = {
                        id: linkType === 'link' ? `link_${this.linkIdCounter++}` : `unbound_${this.linkIdCounter++}`,
                        type: linkType,
                        start: { x: sourceLink.start.x + offsetX, y: sourceLink.start.y + offsetY },
                        end: { x: sourceLink.end.x + offsetX, y: sourceLink.end.y + offsetY },
                        device1: null, // Detached copy
                        device2: null,
                        color: sourceLink.color || '#888888',
                        width: sourceLink.width,
                        style: sourceLink.style || 'solid',
                        curveOverride: sourceLink.curveOverride,
                        curveMagnitude: sourceLink.curveMagnitude,
                        keepCurve: sourceLink.keepCurve,
                        savedCurveOffset: sourceLink.savedCurveOffset ? { ...sourceLink.savedCurveOffset } : undefined,
                        curveMode: sourceLink.curveMode,
                        manualCurvePoint: sourceLink.manualCurvePoint ? {
                            x: sourceLink.manualCurvePoint.x + offsetX,
                            y: sourceLink.manualCurvePoint.y + offsetY
                        } : undefined,
                        manualCurveOffset: sourceLink.manualCurveOffset ? { ...sourceLink.manualCurveOffset } : undefined,
                        layer: sourceLink.layer
                    };
                    
                    this.objects.push(newLink);
                    
                    // Duplicate the text box with all its properties (including font, style, etc.)
                    duplicate = {
                        id: `text_${this.textIdCounter++}`,
                        type: 'text',
                        x: obj.x + offsetX,
                        y: obj.y + offsetY,
                        text: obj.text,
                        fontSize: obj.fontSize,
                        fontFamily: obj.fontFamily,
                        fontWeight: obj.fontWeight,
                        fontStyle: obj.fontStyle,
                        color: obj.color,
                        backgroundColor: obj.backgroundColor,
                        bgColor: obj.bgColor,
                        showBackground: obj.showBackground,
                        backgroundOpacity: obj.backgroundOpacity,
                        backgroundPadding: obj.backgroundPadding,
                        borderColor: obj.borderColor,
                        showBorder: obj.showBorder,
                        rotation: mirror ? (obj.rotation + 180) % 360 : obj.rotation,
                        locked: false,
                        linkId: newLink.id, // Attach to new duplicated link
                        position: obj.position,
                        linkAttachT: obj.linkAttachT,
                        _onLinkLine: obj._onLinkLine,
                        layer: obj.layer
                    };
                    
                    // Also duplicate any OTHER attached text boxes from the source link
                    // (excluding the current one which was already duplicated above)
                    this.duplicateAttachedTexts(sourceLink, newLink, offsetX, offsetY, obj.id);
                    
                    this.objects.push(duplicate);
                    this.selectedObject = duplicate; // Select the duplicated TB
                    this.selectedObjects = [duplicate, newLink]; // Select both TB and link
                    
                    if (this.debugger) {
                        this.debugger.logSuccess(`📋 Duplicated TB with attached link: TB ${duplicate.id}, Link ${newLink.id}`);
                    }
                    
                    this.draw();
                    return; // Early return - already handled
                } else if (this.debugger) {
                    this.debugger.logWarning(`Text has linkId ${obj.linkId} but link not found - duplicating text only`);
                }
            }
            
            // Regular text box (not attached to link)
            duplicate = {
                id: `text_${this.textIdCounter++}`,
                type: 'text',
                x: obj.x + offsetX,
                y: obj.y + offsetY,
                text: obj.text,
                fontSize: obj.fontSize,
                fontFamily: obj.fontFamily,
                fontWeight: obj.fontWeight,
                fontStyle: obj.fontStyle,
                color: obj.color,
                backgroundColor: obj.backgroundColor,
                bgColor: obj.bgColor,
                showBackground: obj.showBackground,
                backgroundOpacity: obj.backgroundOpacity,
                backgroundPadding: obj.backgroundPadding,
                borderColor: obj.borderColor,
                showBorder: obj.showBorder,
                rotation: mirror ? (obj.rotation + 180) % 360 : obj.rotation,
                locked: false,
                layer: obj.layer // Inherit layer
            };
        } else if (obj.type === 'link' || obj.type === 'unbound') {
            // ENHANCED: For BUL chains, duplicate the ENTIRE chain with all attached TBs
            if (obj.type === 'unbound' && (obj.mergedWith || obj.mergedInto)) {
                // This is part of a BUL chain - duplicate the entire chain
                this.duplicateBULChain(obj, offsetX, offsetY);
                return; // duplicateBULChain handles everything
            }
            
            // Single unbound link (not part of BUL)
            if (obj.type === 'unbound') {
                duplicate = {
                    id: `unbound_${this.linkIdCounter++}`,
                    type: 'unbound',
                    start: { x: obj.start.x + offsetX, y: obj.start.y + offsetY },
                    end: { x: obj.end.x + offsetX, y: obj.end.y + offsetY },
                    device1: null, // Detached copy
                    device2: null,
                    color: obj.color || '#888888',
                    width: obj.width,
                    style: obj.style || 'solid',
                    curveOverride: obj.curveOverride,
                    curveMagnitude: obj.curveMagnitude,
                    keepCurve: obj.keepCurve,
                    savedCurveOffset: obj.savedCurveOffset ? { ...obj.savedCurveOffset } : undefined,
                    // Manual curve properties - preserve curve shape with offset
                    curveMode: obj.curveMode,
                    manualCurvePoint: obj.manualCurvePoint ? {
                        x: obj.manualCurvePoint.x + offsetX,
                        y: obj.manualCurvePoint.y + offsetY
                    } : undefined,
                    manualCurveOffset: obj.manualCurveOffset ? { ...obj.manualCurveOffset } : undefined,
                    layer: obj.layer
                };
                
                // Also duplicate any attached text boxes
                this.duplicateAttachedTexts(obj, duplicate, offsetX, offsetY);
            } else {
                // Quick Link - create as unbound link at same visual position
                const dev1 = this.objects.find(o => o.id === obj.device1);
                const dev2 = this.objects.find(o => o.id === obj.device2);
                if (dev1 && dev2) {
                    duplicate = {
                        id: `unbound_${this.linkIdCounter++}`,
                        type: 'unbound',
                        start: { x: dev1.x + offsetX, y: dev1.y + offsetY },
                        end: { x: dev2.x + offsetX, y: dev2.y + offsetY },
                        device1: null,
                        device2: null,
                        color: obj.color || dev1.color || '#888888',
                        width: obj.width,
                        style: obj.style || 'solid',
                        curveOverride: obj.curveOverride,
                        curveMagnitude: obj.curveMagnitude,
                        keepCurve: obj.keepCurve,
                        savedCurveOffset: obj.savedCurveOffset ? { ...obj.savedCurveOffset } : undefined,
                        // Manual curve properties - preserve curve shape with offset
                        curveMode: obj.curveMode,
                        manualCurvePoint: obj.manualCurvePoint ? {
                            x: obj.manualCurvePoint.x + offsetX,
                            y: obj.manualCurvePoint.y + offsetY
                        } : undefined,
                        manualCurveOffset: obj.manualCurveOffset ? { ...obj.manualCurveOffset } : undefined,
                        layer: obj.layer
                    };
                }
            }
        } else {
            return; // Unknown type
        }
        
        if (duplicate) {
            this.objects.push(duplicate);
            this.selectedObject = duplicate;
            this.selectedObjects = [duplicate];
            
            if (this.debugger) {
                this.debugger.logSuccess(`📋 Duplicated ${obj.type}: ${duplicate.id}`);
            }
        }
        this.draw();
    }
    
    // Duplicate an entire BUL chain with all properties and attached text boxes
    duplicateBULChain(sourceLink, offsetX, offsetY) {
        // Get all links in the chain
        const allLinksInChain = this.getAllMergedLinks(sourceLink);
        
        // Create ID mapping for old -> new link IDs
        const idMapping = {};
        const newLinks = [];
        
        // First pass: Create all duplicate links (without merge relationships)
        for (const link of allLinksInChain) {
            const newId = `unbound_${this.linkIdCounter++}`;
            idMapping[link.id] = newId;
            
            const newLink = {
                id: newId,
                type: 'unbound',
                start: { x: link.start.x + offsetX, y: link.start.y + offsetY },
                end: { x: link.end.x + offsetX, y: link.end.y + offsetY },
                device1: null, // Detached copy - no device attachments
                device2: null,
                color: link.color || '#888888',
                width: link.width,
                style: link.style || 'solid',
                curveOverride: link.curveOverride,
                curveMagnitude: link.curveMagnitude,
                keepCurve: link.keepCurve,
                savedCurveOffset: link.savedCurveOffset ? { ...link.savedCurveOffset } : undefined,
                // Manual curve properties - preserve curve shape with offset
                curveMode: link.curveMode,
                manualCurvePoint: link.manualCurvePoint ? {
                    x: link.manualCurvePoint.x + offsetX,
                    y: link.manualCurvePoint.y + offsetY
                } : undefined,
                manualCurveOffset: link.manualCurveOffset ? { ...link.manualCurveOffset } : undefined,
                layer: link.layer
            };
            
            newLinks.push(newLink);
            this.objects.push(newLink);
        }
        
        // Second pass: Recreate merge relationships using new IDs
        for (const link of allLinksInChain) {
            const newLink = this.objects.find(o => o.id === idMapping[link.id]);
            if (!newLink) continue;
            
            // Recreate mergedWith (parent -> child relationship)
            if (link.mergedWith) {
                const newChildId = idMapping[link.mergedWith.linkId];
                if (newChildId) {
                    newLink.mergedWith = {
                        linkId: newChildId,
                        connectionPoint: link.mergedWith.connectionPoint ? {
                            x: link.mergedWith.connectionPoint.x + offsetX,
                            y: link.mergedWith.connectionPoint.y + offsetY
                        } : undefined,
                        parentFreeEnd: link.mergedWith.parentFreeEnd,
                        childFreeEnd: link.mergedWith.childFreeEnd,
                        childStart: link.mergedWith.childStart ? {
                            x: link.mergedWith.childStart.x + offsetX,
                            y: link.mergedWith.childStart.y + offsetY
                        } : undefined,
                        childEnd: link.mergedWith.childEnd ? {
                            x: link.mergedWith.childEnd.x + offsetX,
                            y: link.mergedWith.childEnd.y + offsetY
                        } : undefined,
                        parentDevice: null, // No device attachments in duplicate
                        childDevice: null,
                        mpNumber: link.mergedWith.mpNumber,
                        connectionEndpoint: link.mergedWith.connectionEndpoint,
                        childConnectionEndpoint: link.mergedWith.childConnectionEndpoint
                    };
                }
            }
            
            // Recreate mergedInto (child -> parent relationship)
            if (link.mergedInto) {
                const newParentId = idMapping[link.mergedInto.parentId];
                if (newParentId) {
                    newLink.mergedInto = {
                        parentId: newParentId,
                        connectionPoint: link.mergedInto.connectionPoint ? {
                            x: link.mergedInto.connectionPoint.x + offsetX,
                            y: link.mergedInto.connectionPoint.y + offsetY
                        } : undefined
                    };
                }
            }
        }
        
        // Third pass: Duplicate all attached text boxes for all links in the chain
        const allLinkIds = allLinksInChain.map(l => l.id);
        const attachedTexts = this.objects.filter(obj => 
            obj.type === 'text' && obj.linkId && allLinkIds.includes(obj.linkId)
        );
        
        for (const textObj of attachedTexts) {
            const newLinkId = idMapping[textObj.linkId];
            if (!newLinkId) continue;
            
            const newText = {
                id: `text_${this.textIdCounter++}`,
                type: 'text',
                x: textObj.x + offsetX,
                y: textObj.y + offsetY,
                text: textObj.text,
                fontSize: textObj.fontSize,
                fontFamily: textObj.fontFamily,
                fontWeight: textObj.fontWeight,
                fontStyle: textObj.fontStyle,
                color: textObj.color,
                backgroundColor: textObj.backgroundColor,
                showBackground: textObj.showBackground,
                backgroundOpacity: textObj.backgroundOpacity,
                backgroundPadding: textObj.backgroundPadding,
                borderColor: textObj.borderColor,
                showBorder: textObj.showBorder,
                rotation: textObj.rotation || 0,
                locked: false,
                linkId: newLinkId, // Link to new duplicated link
                position: textObj.position,
                linkAttachT: textObj.linkAttachT,
                _onLinkLine: textObj._onLinkLine,
                layer: textObj.layer
            };
            
            this.objects.push(newText);
        }
        
        // Select all new links
        this.selectedObjects = [...newLinks];
        this.selectedObject = newLinks[0];
        
        if (this.debugger) {
            this.debugger.logSuccess(`📋 Duplicated BUL chain: ${newLinks.length} links, ${attachedTexts.length} attached texts`);
        }
        
        this.draw();
    }
    
    // Duplicate attached text boxes for a single link
    // Optional excludeId: skip this text ID (to avoid redundant duplication when called from TB duplicate)
    duplicateAttachedTexts(sourceLink, newLink, offsetX, offsetY, excludeId = null) {
        const attachedTexts = this.objects.filter(obj => 
            obj.type === 'text' && obj.linkId === sourceLink.id && obj.id !== excludeId
        );
        
        for (const textObj of attachedTexts) {
            const newText = {
                id: `text_${this.textIdCounter++}`,
                type: 'text',
                x: textObj.x + offsetX,
                y: textObj.y + offsetY,
                text: textObj.text,
                fontSize: textObj.fontSize,
                fontFamily: textObj.fontFamily,
                fontWeight: textObj.fontWeight,
                fontStyle: textObj.fontStyle,
                color: textObj.color,
                backgroundColor: textObj.backgroundColor,
                showBackground: textObj.showBackground,
                backgroundOpacity: textObj.backgroundOpacity,
                backgroundPadding: textObj.backgroundPadding,
                borderColor: textObj.borderColor,
                showBorder: textObj.showBorder,
                rotation: textObj.rotation || 0,
                locked: false,
                linkId: newLink.id,
                position: textObj.position,
                linkAttachT: textObj.linkAttachT,
                _onLinkLine: textObj._onLinkLine,
                layer: textObj.layer
            };
            
            this.objects.push(newText);
        }
    }
    
    updateDeviceRadius(radius) {
        // Device radius now controlled via device editor modal
        if (this.selectedObject && this.selectedObject.type === 'device') {
            this.saveState();
            this.selectedObject.radius = Math.min(500, Math.max(15, parseInt(radius)));
            this.draw();
        }
    }
    
    applyDeviceRadius() {
        // Device radius now controlled via device editor modal - kept for compatibility
    }
    
    updateDeviceLabel(label) {
        // Store pending value, don't apply yet
        // Note: This is now handled via device editor modal (editor-device-label)
        this.pendingLabel = label;
        const input = document.getElementById('editor-device-label');
        if (input) input.style.background = '#fffacd'; // Yellow background for pending
    }
    
    applyDeviceLabel() {
        if (this.selectedObject && this.selectedObject.type === 'device' && this.pendingLabel !== null) {
            const trimmedLabel = this.pendingLabel.trim() || (this.selectedObject.deviceType === 'router' ? 'NCP' : 'S');
            
            // Validate length (max 20 characters)
            const input = document.getElementById('editor-device-label');
            if (trimmedLabel.length > 20) {
                alert('Device label cannot exceed 20 characters');
                if (input) {
                    input.value = this.selectedObject.label;
                    input.style.background = '';
                }
                this.pendingLabel = null;
                return;
            }
            
            if (!this.isDeviceNameUnique(trimmedLabel) && trimmedLabel !== this.selectedObject.label) {
                alert(`Device name "${trimmedLabel}" already exists. Please choose a different name.`);
                if (input) {
                    input.value = this.selectedObject.label;
                    input.style.background = '';
                }
                this.pendingLabel = null;
                return;
            }
            
            this.saveState();
            this.selectedObject.label = trimmedLabel;
            if (input) input.style.background = '';
            this.pendingLabel = null;
            this.draw();
        }
    }
    
    showLinkInterfaceMenu(link) {
        // Use the same menu as right-click context menu
        this.showAdjacentTextMenu(link);
    }
    
    addAdjacentTextWithEditor(link, position, textContent) {
        this.addAdjacentText(link, position, textContent);
        const addedText = this.objects.find(obj => 
            obj.type === 'text' && obj.linkId === link.id && obj.position === position
        );
        if (addedText) {
            this.showTextEditor(addedText);
        }
    }
    
    showTextEditor(textObj) {
        if (window.TextEditorModule) {
            return window.TextEditorModule.show(this, textObj);
        }
    }
    
    hideTextEditor() {
        if (window.TextEditorModule) {
            return window.TextEditorModule.hide(this);
        }
    }
    
    // ==================== INLINE TEXT EDITOR ====================
    // Delegated to TextEditorModule
    
    showInlineTextEditor(textObj, event) {
        if (window.TextEditorModule) {
            return window.TextEditorModule.showInline(this, textObj, event);
        }
    }
    
    updateInlineTextEditorPosition() {
        if (window.TextEditorModule) {
            return window.TextEditorModule.updateInlinePosition(this);
        }
    }
    
    hideInlineTextEditor() {
        if (window.TextEditorModule) {
            return window.TextEditorModule.hideInline(this);
        }
    }
    
    // ==================== INLINE DEVICE RENAME EDITOR ====================
    // Delegated to TextEditorModule
    
    showInlineDeviceRename(device) {
        if (window.TextEditorModule) {
            return window.TextEditorModule.showDeviceRename(this, device);
        }
    }
    
    hideInlineDeviceRename() {
        if (window.TextEditorModule) {
            return window.TextEditorModule.hideDeviceRename(this);
        }
    }

    updateInlineDeviceRenamePosition() {
        if (window.TextEditorModule) {
            return window.TextEditorModule.updateDeviceRenamePosition(this);
        }
    }
    
    // ==================== TEXT SELECTION TOOLBAR ====================
    // Floating toolbar that appears below selected text with options
    // Contains: Rotation, Background, Detach, Delete, More options
    
    getEffectiveTextRotation(text) {
        if (!text) return 0;
        if (text.alwaysFaceUser === true) return 0;
        if (text.alwaysFaceUser === false) return text.rotation || 0;
        if (this.textAlwaysFaceUser) return 0;
        return text.rotation || 0;
    }
    
    _createIconSvg(iconId, size = 16, color = null) {
        const colorStyle = color ? `color: ${color};` : '';
        // pointer-events: none ensures clicks pass through to parent button
        return `<svg width="${size}" height="${size}" style="${colorStyle} pointer-events: none;"><use href="#ico-${iconId}"/></svg>`;
    }
    
    showTextSelectionToolbar(textObj) {
        // Delegate to external module (implementation moved to topology-text-toolbar.js)
        if (window.showTextSelectionToolbar) {
            window.showTextSelectionToolbar(this, textObj);
        }
    }
    
    hideTextSelectionToolbar() {
        // Delegate to external module
        if (window.hideTextSelectionToolbar) {
            window.hideTextSelectionToolbar(this);
        }
    }
    
    // ==================== SHAPE SELECTION TOOLBAR ====================
    // Floating toolbar for shapes - Implementation moved to topology-shape-toolbar.js
    
    showShapeSelectionToolbar(shape) {
        // Delegate to external module
        if (window.showShapeSelectionToolbar) {
            window.showShapeSelectionToolbar(this, shape);
        }
    }
    
    hideShapeSelectionToolbar() {
        // Delegate to external module
        if (window.hideShapeSelectionToolbar) {
            window.hideShapeSelectionToolbar(this);
        }
    }
    
    // Shared tooltip helpers for toolbars
    _showToolbarTooltip(btn, title) {
        if (window.SelectionPopups) {
            return window.SelectionPopups._showToolbarTooltip(this, btn, title);
        }
    }
    
    _hideToolbarTooltip() {
        if (window.SelectionPopups) {
            return window.SelectionPopups._hideToolbarTooltip(this);
        }
    }
    
    // LLDP inline submenu - appears below LLDP button with same toolbar styling
    _showLldpInlineSubmenu(lldpBtn, device, serial, sshConfig, toolbar, isDarkMode, iconColor, hoverBg) {
        if (window.SelectionPopups) {
            return window.SelectionPopups._showLldpInlineSubmenu(this, lldpBtn, device, serial, sshConfig, toolbar, isDarkMode, iconColor, hoverBg);
        }
    }

    // System Stack inline submenu - appears below System Stack button with Stack Table + Git Commit
    _showSystemStackInlineSubmenu(stackBtn, device, serial, sshConfig, toolbar, isDarkMode, iconColor, hoverBg) {
        if (window.SelectionPopups) {
            return window.SelectionPopups._showSystemStackInlineSubmenu(this, stackBtn, device, serial, sshConfig, toolbar, isDarkMode, iconColor, hoverBg);
        }
    }
    
    // ==================== DEVICE SELECTION TOOLBAR ====================
    // Implementation moved to topology-device-toolbar.js
    
    showDeviceSelectionToolbar(device) {
        if (window.showDeviceSelectionToolbar) {
            window.showDeviceSelectionToolbar(this, device);
        }
    }
    
    hideDeviceSelectionToolbar() {
        if (window.hideDeviceSelectionToolbar) {
            window.hideDeviceSelectionToolbar(this);
        }
    }
    
    // ==================== LINK SELECTION TOOLBAR ====================
    // Implementation moved to topology-link-toolbar.js
    
    showLinkSelectionToolbar(link, clickPos = null) {
        if (window.showLinkSelectionToolbar) {
            window.showLinkSelectionToolbar(this, link, clickPos);
        }
    }
    
    hideLinkSelectionToolbar() {
        if (window.hideLinkSelectionToolbar) {
            window.hideLinkSelectionToolbar(this);
        }
    }
    
    // Hide ALL selection toolbars (text, device, link)
    hideAllSelectionToolbars() {
        this.hideTextSelectionToolbar();
        this.hideDeviceSelectionToolbar();
        this.hideLinkSelectionToolbar();
        this.hideShapeSelectionToolbar();
        this.hideMultiSelectContextMenu();
    }
    
    // ==================== MULTI-SELECT CONTEXT MENU ====================
    // ==================== MULTI-SELECT CONTEXT MENU ====================
    // Implementation moved to topology-multiselect-menu.js (~875 lines extracted)
    
    showMultiSelectContextMenu(screenX, screenY) {
        // Delegate to external module
        if (window.showMultiSelectContextMenu) {
            window.showMultiSelectContextMenu(this, screenX, screenY);
        }
    }
    
    hideMultiSelectContextMenu() {
        // Delegate to external module
        if (window.hideMultiSelectContextMenu) {
            window.hideMultiSelectContextMenu(this);
        }
    }
    
    // Device Style Palette popup
    showDeviceStylePalette(device) {
        if (window.SelectionPopups) {
            return window.SelectionPopups.showDeviceStylePalette(this, device);
        }
    }
    
    // Device Label Style Menu popup (font, color, size, outline)
    showDeviceLabelStyleMenu(device, toolbar) {
        if (window.SelectionPopups) {
            return window.SelectionPopups.showDeviceLabelStyleMenu(this, device, toolbar);
        }
    }
    
    // Link Width Slider popup
    showLinkWidthSlider(link) {
        if (window.SelectionPopups) {
            return window.SelectionPopups.showLinkWidthSlider(this, link);
        }
    }
    
    // Link Style Options popup
    showLinkStyleOptions(link) {
        if (window.SelectionPopups) {
            return window.SelectionPopups.showLinkStyleOptions(this, link);
        }
    }
    
    // Link Curve Options popup
    showLinkCurveOptions(link) {
        if (window.SelectionPopups) {
            return window.SelectionPopups.showLinkCurveOptions(this, link);
        }
    }
    
    /**
     * Show a color palette popup for text objects
     * Delegated to topology-text-popups.js
     */
    showTextColorPalette(textObj) {
        if (typeof window.showTextColorPalette === 'function') {
            window.showTextColorPalette(this, textObj);
        }
    }
    
    /**
     * Show a font selector popup for text objects
     * Delegated to topology-text-popups.js
     */
    showTextFontSelector(textObj) {
        if (typeof window.showTextFontSelector === 'function') {
            window.showTextFontSelector(this, textObj);
        }
    }
    
    /**
     * Show background color palette for text objects
     * Delegated to topology-text-popups.js
     */
    showTextBgColorPalette(textObj) {
        if (typeof window.showTextBgColorPalette === 'function') {
            window.showTextBgColorPalette(this, textObj);
        }
    }
    
    // Update toolbar position when canvas pans/zooms (horizontal toolbar)
    // Delegated to topology-text-toolbar.js
    updateTextSelectionToolbarPosition() {
        if (typeof window.updateTextSelectionToolbarPosition === 'function') {
            window.updateTextSelectionToolbarPosition(this);
        }
    }
    
    // Link Editor Modal
    showLinkEditor(link) {
        if (window.LinkDetailsHandlers) {
            return window.LinkDetailsHandlers.showLinkEditor(this, link);
        }
    }
    
    hideLinkEditor() {
        const modal = document.getElementById('link-editor-modal');
        if (modal) modal.classList.remove('show');
        this.editingLink = null;
        this.editingBulLinks = null; // Clear BUL links reference
        this.draw();
    }
    
    updateLinkEditorProperty(property, value) {
        if (window.LinkDetailsHandlers) {
            return window.LinkDetailsHandlers.updateLinkEditorProperty(this, property, value);
        }
    }
    
    // Handle Keep Current Curve toggle for UL/BUL
    handleKeepCurveChange(enabled) {
        if (window.LinkDetailsHandlers) {
            return window.LinkDetailsHandlers.handleKeepCurveChange(this, enabled);
        }
    }
    
    // Device Editor Modal - Delegated to topology-device-editor.js
    showDeviceEditor(device) {
        if (typeof window.showDeviceEditorModal === 'function') {
            window.showDeviceEditorModal(this, device);
        }
    }
    
    hideDeviceEditor() {
        if (typeof window.hideDeviceEditorModal === 'function') {
            window.hideDeviceEditorModal(this);
        }
    }
    
    updateDeviceEditorProperty(property, value) {
        if (typeof window.updateDeviceEditorPropertyExt === 'function') {
            window.updateDeviceEditorPropertyExt(this, property, value);
        }
    }
    
    showLinkDetails(link) {
        if (window.LinkDetailsHandlers) {
            return window.LinkDetailsHandlers.showLinkDetails(this, link);
        }
    }
    
    // Set up modal dragging via header
    setupModalDragging(modalContent) {
        const header = modalContent.querySelector('.link-table-header');
        if (!header || header._dragSetup) return; // Avoid duplicate setup
        
        header._dragSetup = true;
        let isDragging = false;
        let startX, startY, initialX, initialY;
        
        const onMouseDown = (e) => {
            // Only drag on left mouse button and not on close button
            if (e.button !== 0 || e.target.closest('.link-table-close')) return;
            
            isDragging = true;
            
            // Get current position
            const rect = modalContent.getBoundingClientRect();
            startX = e.clientX;
            startY = e.clientY;
            initialX = rect.left;
            initialY = rect.top;
            
            // Switch to fixed positioning if not already
            if (modalContent.style.position !== 'fixed') {
                modalContent.style.position = 'fixed';
                modalContent.style.left = initialX + 'px';
                modalContent.style.top = initialY + 'px';
                modalContent.style.transform = 'none';
            }
            
            e.preventDefault();
        };
        
        const onMouseMove = (e) => {
            if (!isDragging) return;
            
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            
            let newX = initialX + dx;
            let newY = initialY + dy;
            
            // Keep modal within viewport
            const rect = modalContent.getBoundingClientRect();
            newX = Math.max(0, Math.min(window.innerWidth - rect.width, newX));
            newY = Math.max(0, Math.min(window.innerHeight - rect.height, newY));
            
            modalContent.style.left = newX + 'px';
            modalContent.style.top = newY + 'px';
        };
        
        const onMouseUp = () => {
            if (isDragging) {
                isDragging = false;
                
                // Save position
                const rect = modalContent.getBoundingClientRect();
                localStorage.setItem('link_table_modal_position', JSON.stringify({
                    x: rect.left,
                    y: rect.top
                }));
            }
        };
        
        header.addEventListener('mousedown', onMouseDown);
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        
        // Store cleanup function
        modalContent._cleanupDrag = () => {
            header.removeEventListener('mousedown', onMouseDown);
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };
    }
    
    // Set up modal edge/corner resizing
    setupModalResize(modalContent) {
        if (modalContent._resizeSetup) return; // Avoid duplicate setup
        modalContent._resizeSetup = true;
        
        // Create resize handles for all 4 corners and 4 edges
        const handles = [
            { class: 'resize-handle-se', cursor: 'se-resize', edges: ['right', 'bottom'] },
            { class: 'resize-handle-sw', cursor: 'sw-resize', edges: ['left', 'bottom'] },
            { class: 'resize-handle-ne', cursor: 'ne-resize', edges: ['right', 'top'] },
            { class: 'resize-handle-nw', cursor: 'nw-resize', edges: ['left', 'top'] },
            { class: 'resize-handle-n', cursor: 'n-resize', edges: ['top'] },
            { class: 'resize-handle-s', cursor: 's-resize', edges: ['bottom'] },
            { class: 'resize-handle-e', cursor: 'e-resize', edges: ['right'] },
            { class: 'resize-handle-w', cursor: 'w-resize', edges: ['left'] }
        ];
        
        handles.forEach(h => {
            // Check if handle already exists
            if (modalContent.querySelector(`.${h.class}`)) return;
            
            const handle = document.createElement('div');
            handle.className = `resize-handle ${h.class}`;
            handle.style.position = 'absolute';
            handle.style.zIndex = '101';
            handle.style.cursor = h.cursor;
            
            // Position the handle
            if (h.edges.includes('top')) handle.style.top = '0';
            if (h.edges.includes('bottom')) handle.style.bottom = '0';
            if (h.edges.includes('left')) handle.style.left = '0';
            if (h.edges.includes('right')) handle.style.right = '0';
            
            // Size the handle
            if (h.edges.length === 2) {
                // Corner handle - fixed size
                handle.style.width = '16px';
                handle.style.height = '16px';
            } else if (h.edges.includes('top') || h.edges.includes('bottom')) {
                // Horizontal edge - spans width (excluding corners)
                handle.style.left = '16px';
                handle.style.right = '16px';
                handle.style.width = 'auto'; // Override any fixed width
                handle.style.height = '8px';
            } else {
                // Vertical edge - spans height (excluding corners)
                handle.style.top = '16px';
                handle.style.bottom = '16px';
                handle.style.width = '8px';
                handle.style.height = 'auto'; // Override any fixed height
            }
            
            modalContent.appendChild(handle);
            
            // Add resize logic
            let isResizing = false;
            let startX, startY, startWidth, startHeight, startLeft, startTop;
            
            const onMouseDown = (e) => {
                e.preventDefault();
                e.stopPropagation();
                isResizing = true;
                
                const rect = modalContent.getBoundingClientRect();
                startX = e.clientX;
                startY = e.clientY;
                startWidth = rect.width;
                startHeight = rect.height;
                startLeft = rect.left;
                startTop = rect.top;
                
                // Ensure fixed positioning
                if (modalContent.style.position !== 'fixed') {
                    modalContent.style.position = 'fixed';
                    modalContent.style.left = startLeft + 'px';
                    modalContent.style.top = startTop + 'px';
                    modalContent.style.transform = 'none';
                }
                
                document.body.style.cursor = h.cursor;
                document.body.style.userSelect = 'none';
            };
            
            const onMouseMove = (e) => {
                if (!isResizing) return;
                
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                
                let newWidth = startWidth;
                let newHeight = startHeight;
                let newLeft = startLeft;
                let newTop = startTop;
                
                // Calculate new dimensions based on which edges are being dragged
                if (h.edges.includes('right')) {
                    newWidth = Math.max(400, startWidth + dx);
                }
                if (h.edges.includes('left')) {
                    const delta = Math.min(dx, startWidth - 400);
                    newWidth = startWidth - delta;
                    newLeft = startLeft + delta;
                }
                if (h.edges.includes('bottom')) {
                    newHeight = Math.max(300, startHeight + dy);
                }
                if (h.edges.includes('top')) {
                    const delta = Math.min(dy, startHeight - 300);
                    newHeight = startHeight - delta;
                    newTop = startTop + delta;
                }
                
                // Apply constraints
                newWidth = Math.min(newWidth, window.innerWidth * 0.95);
                newHeight = Math.min(newHeight, window.innerHeight * 0.95);
                
                modalContent.style.width = newWidth + 'px';
                modalContent.style.height = newHeight + 'px';
                modalContent.style.left = newLeft + 'px';
                modalContent.style.top = newTop + 'px';
            };
            
            const onMouseUp = () => {
                if (isResizing) {
                    isResizing = false;
                    document.body.style.cursor = '';
                    document.body.style.userSelect = '';
                    
                    // Save size and position
                    const rect = modalContent.getBoundingClientRect();
                    localStorage.setItem('link_table_modal_size', JSON.stringify({
                        width: rect.width,
                        height: rect.height
                    }));
                    localStorage.setItem('link_table_modal_position', JSON.stringify({
                        x: rect.left,
                        y: rect.top
                    }));
                }
            };
            
            handle.addEventListener('mousedown', onMouseDown);
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });
        
        // Set up ResizeObserver to toggle extra column visibility based on width
        if (this.linkEditor && typeof this.linkEditor.setupResponsiveColumns === 'function') {
            this.linkEditor.setupResponsiveColumns(modalContent);
        } else {
            this.setupLinkTableResponsiveColumns(modalContent);
        }
    }
    
    // Set up ResizeObserver to show/hide extra columns based on modal width
    setupLinkTableResponsiveColumns(modalContent) {
        if (window.LinkTableManager) {
            return window.LinkTableManager.setupResponsiveColumns(this, modalContent);
        }
    }
    
    // Populate the Link Table fields
    populateLinkTableFields(link, device1InterfaceName, device2InterfaceName) {
        if (window.LinkTableManager) {
            return window.LinkTableManager.populateFields(this, link, device1InterfaceName, device2InterfaceName);
        }
    }
    
    /**
     * Auto-fill Link Table fields from cached DNAAS discovery data.
     * Uses window._dnaasDiscoveryData set by multi-BD discovery.
     */
    autoFillFromDnaasDiscovery(link, device1InterfaceName, device2InterfaceName) {
        if (window.LinkTableManager) {
            return window.LinkTableManager.autoFillFromDnaasDiscovery(this, link, device1InterfaceName, device2InterfaceName);
        }
    }
    
    // Helper to set a field value (handles both input and select elements)
    setFieldValue(elementId, value) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.setFieldValue === 'function') {
            return this.linkEditor.setFieldValue(elementId, value);
        }
        
        // Fallback: basic implementation
        const el = document.getElementById(elementId);
        if (el) el.value = value || '';
    }
    
    // Show visual indicator that DNAAS data was auto-filled
    showDnaasAutoFillIndicator() {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.showDnaasAutoFillIndicator === 'function') {
            return this.linkEditor.showDnaasAutoFillIndicator();
        }
        // Fallback: no-op
    }
    
    // Update IP address field visibility based on IP type selection
    updateIpAddressFieldVisibility() {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.updateIpAddressFieldVisibility === 'function') {
            return this.linkEditor.updateIpAddressFieldVisibility();
        }
        // Fallback: no-op
    }
    
    // Set up real-time validation for Link Table fields
    setupLinkTableValidation() {
        if (window.LinkTableManager) {
            return window.LinkTableManager.setupValidation(this);
        }
    }
    
    // Set up VLAN matching validation for sub-interface fields
    setupSubInterfaceVlanValidation() {
        if (window.LinkTableManager) {
            return window.LinkTableManager.setupSubInterfaceVlanValidation(this);
        }
    }
    
    // Update VLAN fields visibility based on mode selection
    updateVlanFieldsVisibility() {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.updateVlanFieldsVisibility === 'function') {
            return this.linkEditor.updateVlanFieldsVisibility();
        }
        
        // Fallback: original implementation
        const modeA = document.getElementById('lt-vlan-mode-a')?.value || '';
        const modeB = document.getElementById('lt-vlan-mode-b')?.value || '';
        
        const vlanIdRow = document.getElementById('lt-vlan-id-row');
        const tpidRow = document.getElementById('lt-vlan-tpid-row');
        const outerTagRow = document.getElementById('lt-outer-tag-row');
        const innerTagRow = document.getElementById('lt-inner-tag-row');
        
        const showVlanId = modeA === 'vlan-id' || modeB === 'vlan-id';
        const showVlanTags = modeA === 'vlan-tags' || modeB === 'vlan-tags';
        
        if (vlanIdRow) vlanIdRow.style.display = showVlanId ? '' : 'none';
        if (tpidRow) tpidRow.style.display = showVlanTags ? '' : 'none';
        if (outerTagRow) outerTagRow.style.display = showVlanTags ? '' : 'none';
        if (innerTagRow) innerTagRow.style.display = showVlanTags ? '' : 'none';
        
        const vlanIdA = document.getElementById('lt-vlan-id-a');
        const tpidA = document.getElementById('lt-vlan-tpid-a');
        const outerA = document.getElementById('lt-outer-tag-a');
        const innerA = document.getElementById('lt-inner-tag-a');
        
        if (vlanIdA) vlanIdA.disabled = modeA !== 'vlan-id';
        if (tpidA) tpidA.disabled = modeA !== 'vlan-tags';
        if (outerA) outerA.disabled = modeA !== 'vlan-tags';
        if (innerA) innerA.disabled = modeA !== 'vlan-tags';
        
        const vlanIdB = document.getElementById('lt-vlan-id-b');
        const tpidB = document.getElementById('lt-vlan-tpid-b');
        const outerB = document.getElementById('lt-outer-tag-b');
        const innerB = document.getElementById('lt-inner-tag-b');
        
        if (vlanIdB) vlanIdB.disabled = modeB !== 'vlan-id';
        if (tpidB) tpidB.disabled = modeB !== 'vlan-tags';
        if (outerB) outerB.disabled = modeB !== 'vlan-tags';
        if (innerB) innerB.disabled = modeB !== 'vlan-tags';
    }
    
    // Populate platform models based on category selection
    populatePlatformModels(selectId, category) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        // Clear existing options
        select.innerHTML = '<option value="">--</option>';
        
        if (!category) return;
        
        // Get platforms from the driveNetsPlatforms database
        const categoryData = this.driveNetsPlatforms[category];
        if (!categoryData || !categoryData.platforms) return;
        
        categoryData.platforms.forEach(platform => {
            const option = document.createElement('option');
            option.value = platform.official;
            option.textContent = platform.displayName;
            select.appendChild(option);
        });
        
        // Auto-save after selection
        this.autoSaveLinkTable();
    }
    
    // Derive Category from Model prefix
    // Categories: DNAAS, NC-AI, SA, CL
    deriveCategoryFromModel(model) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.deriveCategoryFromModel === 'function') {
            return this.linkEditor.deriveCategoryFromModel(model);
        }
        
        // Fallback: original implementation
        if (!model) return '';
        const modelUpper = model.toUpperCase();
        
        if (modelUpper.startsWith('NCM') || modelUpper.startsWith('NCC')) return 'DNAAS';
        if (modelUpper.startsWith('AI-')) return 'NC-AI';
        if (modelUpper.startsWith('CL-')) return 'CL';
        if (modelUpper.startsWith('SA-')) return 'SA';
        if (modelUpper.startsWith('NCP')) return 'NC-AI';
        
        return '';
    }
    
    // Populate Models dropdown based on selected Category
    populateModelsForCategory(selectId, category) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.populateModelsForCategory === 'function') {
            return this.linkEditor.populateModelsForCategory(selectId, category);
        }
        
        // Fallback: basic implementation
        const select = document.getElementById(selectId);
        if (select) select.innerHTML = '<option value="">--</option>';
    }
    
    // Detect Model from device name (e.g., DNAAS-LEAF-B10 -> NCM-1600)
    detectModelFromDeviceName(deviceName) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.detectModelFromDeviceName === 'function') {
            return this.linkEditor.detectModelFromDeviceName(deviceName);
        }
        return ''; // Fallback: no detection
    }
    
    // Populate interfaces based on platform model selection
    populateInterfaces(selectId, platformModel) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.populateInterfacesForPlatform === 'function') {
            return this.linkEditor.populateInterfacesForPlatform(selectId, platformModel);
        }
        
        // Fallback: minimal implementation
        const select = document.getElementById(selectId);
        if (!select) return;
        select.innerHTML = '<option value="">--</option>';
    }
    
    // Handle custom interface input when "__custom__" is selected
    handleCustomInterfaceInput(selectId) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.handleCustomInterfaceInput === 'function') {
            return this.linkEditor.handleCustomInterfaceInput(selectId);
        }
        
        // Fallback: reset to empty
        const select = document.getElementById(selectId);
        if (select) select.value = '';
    }
    
    // Populate interfaces from device config file (async)
    async populateInterfacesFromConfig(deviceName, selectId, subInterfaceSelectId) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        // Try to parse device config
        const configData = await this.parseDeviceConfig(deviceName);
        if (!configData || configData.error || !configData.interfaces.length) {
            console.log(`No config found for ${deviceName}, using platform-based interfaces`);
            return;
        }
        
        // Add separator and config-based interfaces
        const separator = document.createElement('option');
        separator.disabled = true;
        separator.textContent = '── From Config ──';
        select.appendChild(separator);
        
        // Add physical interfaces from config
        configData.interfaces.forEach(intf => {
            const option = document.createElement('option');
            option.value = intf.name;
            option.textContent = intf.name;
            option.dataset.hasSubInterfaces = intf.subInterfaces.length > 0;
            select.appendChild(option);
        });
        
        // Store config data for sub-interface population
        select.dataset.configData = JSON.stringify(configData);
        
        if (this.debugger) {
            this.debugger.logInfo(`Loaded ${configData.interfaces.length} interfaces from ${deviceName} config`);
        }
    }
    
    // Trigger automatic interface loading when Link Table opens
    // For DNAAS devices: Fetch via SSH using the DNAAS API
    // For SCALER devices: Would use SCALER API (currently disabled due to 404s)
    async loadInterfacesFromDeviceConfigs() {
        if (!this.editingLink) return;
        
        const link = this.editingLink;
        const device1 = this.objects.find(d => d.id === link.device1);
        const device2 = this.objects.find(d => d.id === link.device2);

        // Try LLDP auto-fill first (fast, cross-references neighbors)
        if (!link.device1Interface || !link.device2Interface) {
            try {
                await window.LinkDetailsHandlers.autoFillFromLldp(this, link);
            } catch (e) { /* non-blocking */ }
        }
        
        // Check if devices are DNAAS (by label containing DNAAS keywords)
        const dnaasKeywords = ['DNAAS', 'LEAF', 'SPINE', 'FABRIC', 'TOR'];
        const isDnaas1 = device1?.label && dnaasKeywords.some(k => device1.label.toUpperCase().includes(k));
        const isDnaas2 = device2?.label && dnaasKeywords.some(k => device2.label.toUpperCase().includes(k));
        
        // If both devices are DNAAS and we have interfaces, auto-fetch
        if ((isDnaas1 || isDnaas2) && (link.device1Interface || link.device2Interface)) {
            console.log('DNAAS devices detected, auto-fetching interface details...');
            await this.autoFetchDnaasInterfaceDetails();
        }
    }
    
    /**
     * Automatically fetch interface details from DNAAS devices when Link Table opens.
     * Called when DNAAS devices are detected.
     */
    async autoFetchDnaasInterfaceDetails() {
        if (!this.editingLink) return;
        
        const link = this.editingLink;
        const device1 = this.objects.find(d => d.id === link.device1);
        const device2 = this.objects.find(d => d.id === link.device2);
        
        // Get interfaces from link or from saved data
        const interface1 = link.device1Interface || link.linkDetails?.interfaceA;
        const interface2 = link.device2Interface || link.linkDetails?.interfaceB;
        
        // Need at least one interface to fetch
        if (!interface1 && !interface2) {
            console.log('No interfaces defined, skipping auto-fetch');
            return;
        }
        
        const hostname1 = device1?.label;
        const hostname2 = device2?.label;
        
        // Show subtle loading indicator
        const fetchBtn = document.getElementById('lt-fetch-details-btn');
        if (fetchBtn) {
            fetchBtn.style.opacity = '0.6';
            fetchBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                    <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="12"/>
                </svg>
                Auto-fetching...
            `;
        }
        
        try {
            // Build request
            const requestBody = {};
            
            if (hostname1 && interface1) {
                requestBody.device_a = hostname1;
                requestBody.interface_a = interface1;
            }
            if (hostname2 && interface2) {
                if (!requestBody.device_a) {
                    requestBody.device_a = hostname2;
                    requestBody.interface_a = interface2;
                } else {
                    requestBody.device_b = hostname2;
                    requestBody.interface_b = interface2;
                }
            }
            
            if (!requestBody.device_a) return;
            
            console.log('Auto-fetching DNAAS interface details:', requestBody);
            
            const response = await fetch('/api/dnaas/interface-details', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                console.warn('Auto-fetch failed:', response.status);
                return;
            }
            
            const data = await response.json();
            console.log('Auto-fetch response:', data);
            
            let filledCount = 0;
            
            if (data.interfaces) {
                for (const iface of data.interfaces) {
                    if (iface.error) continue;
                    
                    const isDeviceA = iface.device === hostname1;
                    const suffix = isDeviceA ? 'a' : 'b';
                    
                    // Auto-fill transceiver
                    if (iface.transceiver_type) {
                        const select = document.getElementById(`lt-transceiver-${suffix}`);
                        if (select) {
                            // Add option if not exists
                            if (!Array.from(select.options).some(o => o.value.toUpperCase() === iface.transceiver_type.toUpperCase())) {
                                const opt = document.createElement('option');
                                opt.value = iface.transceiver_type;
                                opt.textContent = iface.transceiver_type;
                                select.appendChild(opt);
                            }
                            select.value = iface.transceiver_type;
                            select.style.background = 'rgba(155, 89, 182, 0.15)';
                            filledCount++;
                        }
                    }
                    
                    // Auto-fill VLAN ID
                    if (iface.vlan_config?.outer_vlan) {
                        const field = document.getElementById(`lt-vlan-id-${suffix}`);
                        if (field && !field.value) {
                            field.value = iface.vlan_config.outer_vlan;
                            field.style.background = 'rgba(155, 89, 182, 0.15)';
                            filledCount++;
                        }
                    }
                    
                    // Store in link for later save
                    if (!link.linkDetails) link.linkDetails = {};
                    if (isDeviceA) {
                        link.linkDetails.vlanConfigA = iface.vlan_config;
                        link.linkDetails.stateA = iface.interface_state;
                    } else {
                        link.linkDetails.vlanConfigB = iface.vlan_config;
                        link.linkDetails.stateB = iface.interface_state;
                    }
                }
            }
            
            if (filledCount > 0) {
                this.showDnaasAutoFillIndicator();
                this._hasUnsavedChanges = true;
            }
            
        } catch (error) {
            console.warn('Auto-fetch error:', error);
        } finally {
            // Restore button
            if (fetchBtn) {
                fetchBtn.style.opacity = '1';
                fetchBtn.innerHTML = `
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        <path d="M9 12l2 2 4-4"/>
                    </svg>
                    Fetch Details
                `;
            }
        }
    }
    
    // Auto-save link table when values change
    autoSaveLinkTable() {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.autoSave === 'function') {
            return this.linkEditor.autoSave();
        }
        
        // Fallback: original implementation
        if (!this.editingLink) return;
        
        if (this._autoSaveTimeout) {
            clearTimeout(this._autoSaveTimeout);
        }
        
        this._autoSaveTimeout = setTimeout(() => {
            this.saveLinkDetailsQuiet();
        }, 300);
    }
    
    // Save link details without showing toast (for auto-save)
    saveLinkDetailsQuiet() {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.saveQuietFull === 'function') {
            return this.linkEditor.saveQuietFull();
        }
        
        // Fallback: original implementation
        if (!this.editingLink) return;
        
        const link = this.editingLink;
        
        // Platform
        link.device1PlatformCategory = document.getElementById('lt-platform-cat-a')?.value || '';
        link.device2PlatformCategory = document.getElementById('lt-platform-cat-b')?.value || '';
        link.device1Platform = document.getElementById('lt-platform-model-a')?.value || '';
        link.device2Platform = document.getElementById('lt-platform-model-b')?.value || '';
        
        const newDevice1Interface = document.getElementById('lt-interface-a')?.value || '';
        const newDevice2Interface = document.getElementById('lt-interface-b')?.value || '';
        
        const interface1Changed = newDevice1Interface && newDevice1Interface !== link.device1Interface;
        const interface2Changed = newDevice2Interface && newDevice2Interface !== link.device2Interface;
        
        link.device1Interface = newDevice1Interface;
        link.device2Interface = newDevice2Interface;
        link.device1Transceiver = document.getElementById('lt-transceiver-a')?.value || '';
        link.device2Transceiver = document.getElementById('lt-transceiver-b')?.value || '';
        
        link.device1IpType = document.getElementById('lt-ip-type-a')?.value || '';
        link.device2IpType = document.getElementById('lt-ip-type-b')?.value || '';
        link.device1IpAddress = document.getElementById('lt-ip-addr-a')?.value || '';
        link.device2IpAddress = document.getElementById('lt-ip-addr-b')?.value || '';
        
        link.device1VlanMode = document.getElementById('lt-vlan-mode-a')?.value || '';
        link.device2VlanMode = document.getElementById('lt-vlan-mode-b')?.value || '';
        link.device1VlanId = document.getElementById('lt-vlan-id-a')?.value || '';
        link.device2VlanId = document.getElementById('lt-vlan-id-b')?.value || '';
        link.device1VlanTpid = document.getElementById('lt-vlan-tpid-a')?.value || '';
        link.device2VlanTpid = document.getElementById('lt-vlan-tpid-b')?.value || '';
        link.device1OuterTag = document.getElementById('lt-outer-tag-a')?.value || '';
        link.device2OuterTag = document.getElementById('lt-outer-tag-b')?.value || '';
        link.device1InnerTag = document.getElementById('lt-inner-tag-a')?.value || '';
        link.device2InnerTag = document.getElementById('lt-inner-tag-b')?.value || '';
        
        link.device1IngressAction = document.getElementById('lt-ingress-a')?.value || '';
        link.device2IngressAction = document.getElementById('lt-ingress-b')?.value || '';
        link.device1EgressAction = document.getElementById('lt-egress-a')?.value || '';
        link.device2EgressAction = document.getElementById('lt-egress-b')?.value || '';
        link.device1DnaasVlan = document.getElementById('lt-dnaas-vlan-a')?.value || '';
        link.device2DnaasVlan = document.getElementById('lt-dnaas-vlan-b')?.value || '';
        
        if (interface1Changed) this.createOrUpdateInterfaceTextBox(link, 'device1', newDevice1Interface);
        if (interface2Changed) this.createOrUpdateInterfaceTextBox(link, 'device2', newDevice2Interface);
        
        this.draw();
    }
    
    // Create or update interface text box attached to a link
    createOrUpdateInterfaceTextBox(link, deviceSide, interfaceName) {
        if (!link || !interfaceName) return;
        
        // Check if auto-create is disabled
        if (!this.autoCreateInterfaceTB) {
            if (this.debugger) this.debugger.logInfo('📝 TB Attach OFF - skipping text box creation');
            return;
        }
        
        // Find existing interface TB for this side of the link
        const existingTB = this.objects.find(obj => 
            obj.type === 'text' && 
            obj.linkId === link.id && 
            obj.position === deviceSide
        );
        
        // ENHANCED: Position text ON the link line, AFTER arrow tip
        // Calculate arrow length if link has arrow style
        const linkStyle = link.style || 'solid';
        const linkWidth = link.width || 2;
        const isArrowStyle = linkStyle === 'arrow' || linkStyle === 'double-arrow' || 
                            linkStyle === 'dashed-arrow' || linkStyle === 'dashed-double-arrow';
        const arrowLength = isArrowStyle ? (10 + linkWidth * 3) : 0;
        
        // Text offset = arrow length + generous gap to clear arrow body completely
        // Arrow tip is at device edge, body extends outward by arrowLength
        const textOffset = arrowLength + 35; // 35px gap after arrow body ends
        
        let x, y, linkAngle;
        
        if (link.type === 'unbound') {
            // For unbound links - use link start/end
            const startX = link.start?.x || link.startX;
            const startY = link.start?.y || link.startY;
            const endX = link.end?.x || link.endX;
            const endY = link.end?.y || link.endY;
            
            // Calculate link direction
            const dx = endX - startX;
            const dy = endY - startY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            linkAngle = Math.atan2(dy, dx);
            
            // Normalize direction
            const dirX = dist > 0 ? dx / dist : 0;
            const dirY = dist > 0 ? dy / dist : 0;
            
            // Get device info for proper positioning from device edge
            const device1 = link.device1 ? this.objects.find(obj => obj.id === link.device1) : null;
            const device2 = link.device2 ? this.objects.find(obj => obj.id === link.device2) : null;
            const radius1 = device1?.radius || 0;
            const radius2 = device2?.radius || 0;
            
            if (deviceSide === 'device1') {
                if (device1) {
                    // Position from device1 edge
                    const edgeX = device1.x + dirX * radius1;
                    const edgeY = device1.y + dirY * radius1;
                    x = edgeX + dirX * textOffset;
                    y = edgeY + dirY * textOffset;
            } else {
                    // No device - position from link start
                    x = startX + dirX * textOffset;
                    y = startY + dirY * textOffset;
                }
            } else {
                if (device2) {
                    // Position from device2 edge
                    const edgeX = device2.x - dirX * radius2;
                    const edgeY = device2.y - dirY * radius2;
                    x = edgeX - dirX * textOffset;
                    y = edgeY - dirY * textOffset;
                } else {
                    // No device - position from link end
                    x = endX - dirX * textOffset;
                    y = endY - dirY * textOffset;
                }
            }
            
        } else {
            // For quick links (connected to devices)
            const device1 = this.objects.find(obj => obj.id === link.device1);
            const device2 = this.objects.find(obj => obj.id === link.device2);
            
            if (device1 && device2) {
                    const dx = device2.x - device1.x;
                    const dy = device2.y - device1.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                linkAngle = Math.atan2(dy, dx);
                
                // Normalize direction
                const dirX = dx / dist;
                const dirY = dy / dist;
                
                // Get device radii/bounds for positioning
                const radius1 = device1.radius || 30;
                const radius2 = device2.radius || 30;
                
                // Calculate actual link endpoints (on device edges)
                const linkStartX = device1.x + dirX * radius1;
                const linkStartY = device1.y + dirY * radius1;
                const linkEndX = device2.x - dirX * radius2;
                const linkEndY = device2.y - dirY * radius2;
                
                if (deviceSide === 'device1') {
                    // Position on link, offset from device1 edge
                    x = linkStartX + dirX * textOffset;
                    y = linkStartY + dirY * textOffset;
                } else {
                    // Position on link, offset from device2 edge
                    x = linkEndX - dirX * textOffset;
                    y = linkEndY - dirY * textOffset;
                }
            }
        }
        
        if (existingTB) {
            // Update existing TB text and position
            existingTB.text = interfaceName;
            if (x !== undefined && y !== undefined) {
                existingTB.x = x;
                existingTB.y = y;
            }
            if (this.debugger) {
                this.debugger.logInfo(`📝 Updated interface TB: ${interfaceName}`);
            }
        } else if (x !== undefined && y !== undefined) {
            // Create new TB with transparent background - positioned ON the link
            const newTB = {
                id: `text_${this.textIdCounter++}`,
                type: 'text',
                text: interfaceName,
                x: x,
                y: y,
                fontSize: 11,
                color: this.darkMode ? '#ffffff' : '#333333',
                // Transparent background - semi-transparent for visibility over link
                backgroundColor: this.darkMode ? '#1a1a1a' : '#ffffff',
                showBackground: true,
                backgroundOpacity: 60, // 60% opacity (percentage 0-100)
                rotation: 0,
                locked: false,
                // Attach to link with position info
                linkId: link.id,
                position: deviceSide,
                _onLinkLine: true,
                _interfaceLabel: true // Mark as auto-generated interface label
            };
            
            this.objects.push(newTB);
            
            if (this.debugger) {
                this.debugger.logSuccess(`📝 Created interface TB: ${interfaceName} on link, outside ${deviceSide}`);
            }
        }
    }
    
    // Create text boxes at both ends of the link from link table data
    createLinkTextBoxes() {
        if (!this.editingLink) {
            this.showToast('No link selected', 'error');
            return;
        }
        
        const link = this.editingLink;
        
        // Get current values from the link table fields
        const interface1 = document.getElementById('lt-interface-a')?.value || link.device1Interface || '';
        const interface2 = document.getElementById('lt-interface-b')?.value || link.device2Interface || '';
        const ip1 = document.getElementById('lt-ip-addr-a')?.value || link.device1IpAddress || '';
        const ip2 = document.getElementById('lt-ip-addr-b')?.value || link.device2IpAddress || '';
        
        // Build text content for each end
        const buildTextContent = (interfaceName, ipAddress) => {
            const lines = [];
            if (interfaceName) lines.push(interfaceName);
            if (ipAddress) lines.push(ipAddress);
            return lines.join('\n');
        };
        
        const text1 = buildTextContent(interface1, ip1);
        const text2 = buildTextContent(interface2, ip2);
        
        if (!text1 && !text2) {
            this.showToast('No interface or IP data to create text', 'warning');
            return;
        }
        
        this.saveState(); // For undo
        
        // Create/update text boxes at each end
        if (text1) {
            this.createOrUpdateLinkTextBox(link, 'device1', text1);
        }
        if (text2) {
            this.createOrUpdateLinkTextBox(link, 'device2', text2);
        }
        
        this.draw();
        this.showToast('Text boxes created', 'success');
    }
    
    // Create or update a link text box (similar to interface TB but for full link data)
    createOrUpdateLinkTextBox(link, deviceSide, textContent) {
        if (!link || !textContent) return;
        
        // Find existing link data TB for this side
        const existingTB = this.objects.find(obj => 
            obj.type === 'text' && 
            obj.linkId === link.id && 
            obj.position === deviceSide &&
            obj._linkDataLabel === true
        );
        
        // Calculate position at ~15% from device end with gap
        const gapPercent = 0.15;
        const perpendicularOffset = 18; // Slightly more offset than interface labels
        
        let x, y, linkAngle;
        
        if (link.type === 'unbound') {
            const startX = link.startX;
            const startY = link.startY;
            const endX = link.endX;
            const endY = link.endY;
            
            linkAngle = Math.atan2(endY - startY, endX - startX);
            
            if (deviceSide === 'device1') {
                x = startX + (endX - startX) * gapPercent;
                y = startY + (endY - startY) * gapPercent;
            } else {
                x = endX - (endX - startX) * gapPercent;
                y = endY - (endY - startY) * gapPercent;
            }
            
            x += Math.sin(linkAngle) * perpendicularOffset;
            y -= Math.cos(linkAngle) * perpendicularOffset;
            
        } else {
            const device1 = this.objects.find(obj => obj.id === link.device1);
            const device2 = this.objects.find(obj => obj.id === link.device2);
            
            if (device1 && device2) {
                linkAngle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
                
                if (deviceSide === 'device1') {
                    const dx = device2.x - device1.x;
                    const dy = device2.y - device1.y;
                    x = device1.x + dx * gapPercent;
                    y = device1.y + dy * gapPercent;
                } else {
                    const dx = device1.x - device2.x;
                    const dy = device1.y - device2.y;
                    x = device2.x + dx * gapPercent;
                    y = device2.y + dy * gapPercent;
                }
                
                x += Math.sin(linkAngle) * perpendicularOffset;
                y -= Math.cos(linkAngle) * perpendicularOffset;
            }
        }
        
        if (existingTB) {
            existingTB.text = textContent;
            if (x !== undefined && y !== undefined) {
                existingTB.x = x;
                existingTB.y = y;
            }
            if (this.debugger) {
                this.debugger.logInfo(`📝 Updated link text box for ${deviceSide}`);
            }
        } else if (x !== undefined && y !== undefined) {
            const newTB = {
                id: `text_${this.textIdCounter++}`,
                type: 'text',
                text: textContent,
                x: x,
                y: y,
                fontSize: 11,
                color: this.darkMode ? '#e0e0e0' : '#333333',
                backgroundColor: this.darkMode ? '#1a1a1a' : '#ffffff',
                showBackground: true,
                backgroundOpacity: 0.95,
                rotation: 0,
                locked: false,
                linkId: link.id,
                position: deviceSide,
                _onLinkLine: true,
                _linkDataLabel: true // Mark as link data label (distinct from interface label)
            };
            
            this.objects.push(newTB);
            
            if (this.debugger) {
                this.debugger.logSuccess(`📝 Created link text box for ${deviceSide}`);
            }
        }
    }
    
    // Validate IP address field
    validateIpField(fieldId, ipType) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.validateIpField === 'function') {
            return this.linkEditor.validateIpField(fieldId, ipType);
        }
        return true; // Fallback: assume valid
    }
    
    // Validate VLAN field
    validateVlanField(fieldId) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.validateVlanField === 'function') {
            return this.linkEditor.validateVlanField(fieldId);
        }
        return true; // Fallback: assume valid
    }

    // Legacy table HTML code was removed - using new tabbed interface

    // Update the "To A/B" column headers with actual device names and interfaces
    updateStackColumnHeaders(device1Name, device1Interface, device2Name, device2Interface) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.updateStackColumnHeaders === 'function') {
            return this.linkEditor.updateStackColumnHeaders(device1Name, device1Interface, device2Name, device2Interface);
        }
        // Fallback: no-op
    }
    
    // Setup platform cascading dropdowns (category -> platform -> interface -> transceiver)
    setupPlatformCascading(side, link) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.setupPlatformCascading === 'function') {
            return this.linkEditor.setupPlatformCascading(side, link);
        }
        // Fallback: no-op
    }
    
    // Populate platform dropdown based on category
    populatePlatformDropdown(side, category) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.populatePlatformDropdown === 'function') {
            return this.linkEditor.populatePlatformDropdown(side, category);
        }
        // Fallback: no-op
    }
    
    // Populate interface dropdown based on platform
    populateInterfaceDropdown(side, platformOfficial) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.populateInterfaceDropdown === 'function') {
            return this.linkEditor.populateInterfaceDropdown(side, platformOfficial);
        }
        // Fallback: no-op
    }
    
    // Populate transceiver dropdown based on interface type
    populateTransceiverDropdown(side, interfaceName) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.populateTransceiverDropdown === 'function') {
            return this.linkEditor.populateTransceiverDropdown(side, interfaceName);
        }
        // Fallback: no-op
    }
    
    /**
     * Fetch interface details from DNAAS devices via SSH.
     * Uses the backend API to run 'show configure interface <interface>' commands.
     */
    async fetchDnaasInterfaceDetails() {
        if (!this.editingLink) {
            this.showToast('No link selected', 'error');
            return;
        }
        
        const link = this.editingLink;
        const fetchBtn = document.getElementById('lt-fetch-details-btn');
        
        // Get device labels/hostnames
        const device1 = this.objects.find(d => d.id === link.device1);
        const device2 = this.objects.find(d => d.id === link.device2);
        
        // Get selected interfaces from dropdowns
        const interface1 = document.getElementById('lt-interface-a')?.value;
        const interface2 = document.getElementById('lt-interface-b')?.value;
        
        // Get device hostnames - for DNAAS, the label IS the hostname
        const hostname1 = device1?.label || null;
        const hostname2 = device2?.label || null;
        
        // Validate we have at least one device and interface
        if ((!hostname1 || !interface1) && (!hostname2 || !interface2)) {
            this.showToast('Select at least one interface first', 'warning');
            return;
        }
        
        // Show loading state on button
        const originalBtnHTML = fetchBtn?.innerHTML;
        if (fetchBtn) {
            fetchBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                    <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="12"/>
                </svg>
                Fetching...
            `;
            fetchBtn.disabled = true;
            fetchBtn.style.opacity = '0.7';
        }
        
        try {
            // Build request - API expects device_a as required
            const requestBody = {
                device_a: hostname1 || hostname2,
                interface_a: interface1 || interface2
            };
            
            // Add side B if both sides have data
            if (hostname1 && interface1 && hostname2 && interface2) {
                requestBody.device_b = hostname2;
                requestBody.interface_b = interface2;
            }
            
            console.log('Fetching DNAAS interface details:', requestBody);
            
            // Call API
            const response = await fetch('/api/dnaas/interface-details', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `API error: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('DNAAS interface details response:', data);
            
            // Process results
            let filledCount = 0;
            const autoFilledFields = [];
            
            if (data.interfaces && data.interfaces.length > 0) {
                for (const iface of data.interfaces) {
                    if (iface.error) {
                        console.warn(`Interface fetch error for ${iface.device}: ${iface.error}`);
                        this.showToast(`Error for ${iface.device}: ${iface.error}`, 'warning');
                        continue;
                    }
                    
                    // Determine which side this is (A or B)
                    const isDeviceA = iface.device === hostname1 || iface.interface === interface1;
                    const suffix = isDeviceA ? 'a' : 'b';
                    
                    // Fill transceiver dropdown
                    if (iface.transceiver_type) {
                        const transceiverSelect = document.getElementById(`lt-transceiver-${suffix}`);
                        if (transceiverSelect) {
                            // Check if option exists, add if not
                            let optionExists = Array.from(transceiverSelect.options).some(
                                opt => opt.value.toUpperCase() === iface.transceiver_type.toUpperCase()
                            );
                            if (!optionExists) {
                                const newOption = document.createElement('option');
                                newOption.value = iface.transceiver_type;
                                newOption.textContent = iface.transceiver_type;
                                transceiverSelect.appendChild(newOption);
                            }
                            transceiverSelect.value = iface.transceiver_type;
                            autoFilledFields.push(transceiverSelect);
                            filledCount++;
                        }
                    }
                    
                    // Fill VLAN ID if available
                    if (iface.vlan_config?.outer_vlan) {
                        const vlanIdField = document.getElementById(`lt-vlan-id-${suffix}`);
                        if (vlanIdField) {
                            vlanIdField.value = iface.vlan_config.outer_vlan;
                            autoFilledFields.push(vlanIdField);
                            filledCount++;
                        }
                    }
                    
                    // Store full VLAN config and raw config in link.linkDetails for reference
                    if (!link.linkDetails) link.linkDetails = {};
                    if (isDeviceA) {
                        if (iface.vlan_config) link.linkDetails.vlanConfigA = iface.vlan_config;
                        if (iface.raw_config) link.linkDetails.rawConfigA = iface.raw_config;
                        if (iface.interface_state) link.linkDetails.stateA = iface.interface_state;
                    } else {
                        if (iface.vlan_config) link.linkDetails.vlanConfigB = iface.vlan_config;
                        if (iface.raw_config) link.linkDetails.rawConfigB = iface.raw_config;
                        if (iface.interface_state) link.linkDetails.stateB = iface.interface_state;
                    }
                }
            }
            
            // Visual feedback - highlight auto-filled fields
            autoFilledFields.forEach(field => {
                field.style.background = 'rgba(155, 89, 182, 0.3)';
                field.style.transition = 'background 0.3s ease';
                setTimeout(() => {
                    field.style.background = '';
                }, 2000);
            });
            
            if (filledCount > 0) {
                this.showToast(`✓ Filled ${filledCount} field(s) from DNAAS`, 'success');
                // Mark as having unsaved changes
                this._hasUnsavedChanges = true;
                const saveBtn = document.getElementById('btn-save-link-table');
                if (saveBtn) {
                    saveBtn.classList.add('link-table-btn-unsaved');
                    saveBtn.innerHTML = `${typeof appIcon === 'function' ? appIcon('save') : '💾'} Save Changes*`;
                }
            } else {
                this.showToast('No data found for interfaces', 'warning');
            }
            
        } catch (error) {
            console.error('Fetch DNAAS interface details error:', error);
            this.showToast(`Fetch failed: ${error.message}`, 'error');
        } finally {
            // Restore button
            if (fetchBtn) {
                fetchBtn.innerHTML = originalBtnHTML;
                fetchBtn.disabled = false;
                fetchBtn.style.opacity = '1';
            }
        }
    }
    
    saveLinkDetails() {
        if (!this.editingLink) return;
        
        // Check validity first - don't save if invalid
        const validity = this.checkLinkTableValidity();
        if (!validity.valid) {
            // Show detailed error toast
            this.showValidationErrorToast(validity.errors);
            
            // Also update save button
            const saveBtn = document.getElementById('btn-save-link-table');
            if (saveBtn) {
                const originalText = saveBtn.textContent;
                const originalBg = saveBtn.style.background;
                saveBtn.innerHTML = `${appIcon('warning')} ${validity.errors.length} Invalid Field(s)`;
                saveBtn.style.background = '#e74c3c';
                setTimeout(() => {
                    saveBtn.textContent = originalText;
                    saveBtn.style.background = originalBg;
                }, 3000);
            }
            return;
        }
        
        this.saveState(); // Save for undo
        
        // Use the same field IDs as saveLinkDetailsQuiet (the new table structure)
        const link = this.editingLink;
        
        // Platform
        link.device1PlatformCategory = document.getElementById('lt-platform-cat-a')?.value || '';
        link.device2PlatformCategory = document.getElementById('lt-platform-cat-b')?.value || '';
        link.device1Platform = document.getElementById('lt-platform-model-a')?.value || '';
        link.device2Platform = document.getElementById('lt-platform-model-b')?.value || '';
        
        // Interface
        link.device1Interface = document.getElementById('lt-interface-a')?.value || '';
        link.device2Interface = document.getElementById('lt-interface-b')?.value || '';
        link.device1Transceiver = document.getElementById('lt-transceiver-a')?.value || '';
        link.device2Transceiver = document.getElementById('lt-transceiver-b')?.value || '';
        
        // Network Layer
        link.device1IpType = document.getElementById('lt-ip-type-a')?.value || '';
        link.device2IpType = document.getElementById('lt-ip-type-b')?.value || '';
        link.device1IpAddress = document.getElementById('lt-ip-addr-a')?.value || '';
        link.device2IpAddress = document.getElementById('lt-ip-addr-b')?.value || '';
        
        // VLAN
        link.device1VlanMode = document.getElementById('lt-vlan-mode-a')?.value || '';
        link.device2VlanMode = document.getElementById('lt-vlan-mode-b')?.value || '';
        link.device1VlanId = document.getElementById('lt-vlan-id-a')?.value || '';
        link.device2VlanId = document.getElementById('lt-vlan-id-b')?.value || '';
        link.device1VlanTpid = document.getElementById('lt-vlan-tpid-a')?.value || '';
        link.device2VlanTpid = document.getElementById('lt-vlan-tpid-b')?.value || '';
        link.device1OuterTag = document.getElementById('lt-outer-tag-a')?.value || '';
        link.device2OuterTag = document.getElementById('lt-outer-tag-b')?.value || '';
        link.device1InnerTag = document.getElementById('lt-inner-tag-a')?.value || '';
        link.device2InnerTag = document.getElementById('lt-inner-tag-b')?.value || '';
        
        // Traffic Control
        link.device1IngressAction = document.getElementById('lt-ingress-a')?.value || '';
        link.device2IngressAction = document.getElementById('lt-ingress-b')?.value || '';
        link.device1EgressAction = document.getElementById('lt-egress-a')?.value || '';
        link.device2EgressAction = document.getElementById('lt-egress-b')?.value || '';
        link.device1DnaasVlan = document.getElementById('lt-dnaas-vlan-a')?.value || '';
        link.device2DnaasVlan = document.getElementById('lt-dnaas-vlan-b')?.value || '';
        
        // Redraw to show changes (link state is now updated)
        this.draw();
        
        // Show save confirmation with smooth animation
        const saveBtn = document.getElementById('btn-save-link-table');
        if (saveBtn) {
            const originalText = saveBtn.textContent;
            saveBtn.innerHTML = `${appIcon('check')} Saved!`;
            saveBtn.style.background = '#27ae60';
            setTimeout(() => {
                saveBtn.textContent = originalText;
                saveBtn.style.background = '';
            }, 1500);
        }
    }
    
    
    applyVlanManipulation(outerVlan, innerVlan, manipulation, manipValue) {
        // Parse manipulation value (can be single like "100" or double like "100.200")
        let newOuter = null;
        let newInner = null;
        
        if (manipValue && manipValue.includes('.')) {
            const parts = manipValue.split('.');
            newOuter = parts[0] || null;
            newInner = parts[1] || null;
        } else if (manipValue) {
            newOuter = manipValue;
        }
        
        // Apply DNOS manipulation operations
        switch(manipulation) {
            case 'pop':
                // Remove outer tag, inner becomes outer
                outerVlan = innerVlan;
                innerVlan = null;
                break;
                
            case 'pop-pop':
                // Remove both tags
                outerVlan = null;
                innerVlan = null;
                break;
                
            case 'swap':
                // Replace outer tag with new value
                if (newOuter) {
                    outerVlan = newOuter;
                }
                break;
                
            case 'swap-swap':
                // Replace both tags with new values
                if (newOuter) outerVlan = newOuter;
                if (newInner) innerVlan = newInner;
                break;
                
            case 'push':
                // Add new outer tag, existing becomes inner
                if (newOuter) {
                    innerVlan = outerVlan;
                    outerVlan = newOuter;
                }
                break;
                
            case 'push-push':
                // Add two new tags
                if (newOuter && newInner) {
                    outerVlan = newOuter;
                    innerVlan = newInner;
                } else if (newOuter) {
                    innerVlan = outerVlan;
                    outerVlan = newOuter;
                }
                break;
                
            case 'pop-swap':
                // Pop outer, then swap (inner becomes outer, replace with new)
                if (newOuter) {
                    outerVlan = newOuter;
                    innerVlan = null;
                }
                break;
                
            case 'swap-push':
                // Swap outer, then push new outer
                if (newOuter && newInner) {
                    innerVlan = newInner;
                    outerVlan = newOuter;
                }
                break;
                
            case 'pop-push':
                // Pop outer, then push new outer
                if (newOuter) {
                    outerVlan = newOuter;
                }
                break;
                
            case 'strip-all':
                // Remove all tags
                outerVlan = null;
                innerVlan = null;
                break;
                
            case 'transparent':
            case '':
                // No change
                break;
        }
        
        // Return formatted result
        if (outerVlan && innerVlan) {
            return `${outerVlan}.${innerVlan}`;
        } else if (outerVlan) {
            return outerVlan;
        } else if (innerVlan) {
            return innerVlan;
        } else {
            return '(empty)';
        }
    }
    
    // Calculate the VLAN stack egressing towards the other side after all manipulations
    // DNaaS has separate manipulation for Side A and Side B
    // Traffic flow for A→B: Side A VLAN → A Egress → DNaaS-A Ingress → DNaaS-B Egress → B Ingress = Final Stack at B
    // Traffic flow for B→A: Side B VLAN → B Egress → DNaaS-B Ingress → DNaaS-A Egress → A Ingress = Final Stack at A
    calculateEgressStack(direction) {
        const parseStack = (stack) => {
            if (!stack || stack === '(empty)') return ['', ''];
            return stack.includes('.') ? stack.split('.') : [stack, ''];
        };
        
        if (direction === 'toB') {
            // Traffic from A to B:
            // 1. Start with Side A VLAN
            let outer = document.getElementById('link-d1-vlan-outer')?.value.trim() || '';
            let inner = document.getElementById('link-d1-vlan-inner')?.value.trim() || '';
            
            // 2. Apply Side A device Egress manipulation (leaving device A)
            const d1EgressAction = document.getElementById('link-d1-egress-action')?.value || '';
            const d1EgressOuter = document.getElementById('link-d1-egress-outer')?.value.trim() || '';
            const d1EgressInner = document.getElementById('link-d1-egress-inner')?.value.trim() || '';
            let result = this.applyVlanManipulation(outer, inner, d1EgressAction, d1EgressInner ? `${d1EgressOuter}.${d1EgressInner}` : d1EgressOuter);
            [outer, inner] = parseStack(result);
            
            // 3. Apply DNaaS Side A Ingress manipulation (entering DNaaS from Side A)
            const dnaasAIngressAction = document.getElementById('link-dnaas-a-ingress-action')?.value || '';
            const dnaasAIngressOuter = document.getElementById('link-dnaas-a-ingress-outer')?.value.trim() || '';
            const dnaasAIngressInner = document.getElementById('link-dnaas-a-ingress-inner')?.value.trim() || '';
            result = this.applyVlanManipulation(outer, inner, dnaasAIngressAction, dnaasAIngressInner ? `${dnaasAIngressOuter}.${dnaasAIngressInner}` : dnaasAIngressOuter);
            [outer, inner] = parseStack(result);
            
            // 4. Apply DNaaS Side B Egress manipulation (leaving DNaaS to Side B)
            const dnaasBEgressAction = document.getElementById('link-dnaas-b-egress-action')?.value || '';
            const dnaasBEgressOuter = document.getElementById('link-dnaas-b-egress-outer')?.value.trim() || '';
            const dnaasBEgressInner = document.getElementById('link-dnaas-b-egress-inner')?.value.trim() || '';
            result = this.applyVlanManipulation(outer, inner, dnaasBEgressAction, dnaasBEgressInner ? `${dnaasBEgressOuter}.${dnaasBEgressInner}` : dnaasBEgressOuter);
            [outer, inner] = parseStack(result);
            
            // 5. Apply Side B device Ingress manipulation (entering device B)
            const d2IngressAction = document.getElementById('link-d2-ingress-action')?.value || '';
            const d2IngressOuter = document.getElementById('link-d2-ingress-outer')?.value.trim() || '';
            const d2IngressInner = document.getElementById('link-d2-ingress-inner')?.value.trim() || '';
            result = this.applyVlanManipulation(outer, inner, d2IngressAction, d2IngressInner ? `${d2IngressOuter}.${d2IngressInner}` : d2IngressOuter);
            
            return result;
        } else {
            // Traffic from B to A:
            // 1. Start with Side B VLAN
            let outer = document.getElementById('link-d2-vlan-outer')?.value.trim() || '';
            let inner = document.getElementById('link-d2-vlan-inner')?.value.trim() || '';
            
            // 2. Apply Side B device Egress manipulation (leaving device B)
            const d2EgressAction = document.getElementById('link-d2-egress-action')?.value || '';
            const d2EgressOuter = document.getElementById('link-d2-egress-outer')?.value.trim() || '';
            const d2EgressInner = document.getElementById('link-d2-egress-inner')?.value.trim() || '';
            let result = this.applyVlanManipulation(outer, inner, d2EgressAction, d2EgressInner ? `${d2EgressOuter}.${d2EgressInner}` : d2EgressOuter);
            [outer, inner] = parseStack(result);
            
            // 3. Apply DNaaS Side B Ingress manipulation (entering DNaaS from Side B)
            const dnaasBIngressAction = document.getElementById('link-dnaas-b-ingress-action')?.value || '';
            const dnaasBIngressOuter = document.getElementById('link-dnaas-b-ingress-outer')?.value.trim() || '';
            const dnaasBIngressInner = document.getElementById('link-dnaas-b-ingress-inner')?.value.trim() || '';
            result = this.applyVlanManipulation(outer, inner, dnaasBIngressAction, dnaasBIngressInner ? `${dnaasBIngressOuter}.${dnaasBIngressInner}` : dnaasBIngressOuter);
            [outer, inner] = parseStack(result);
            
            // 4. Apply DNaaS Side A Egress manipulation (leaving DNaaS to Side A)
            const dnaasAEgressAction = document.getElementById('link-dnaas-a-egress-action')?.value || '';
            const dnaasAEgressOuter = document.getElementById('link-dnaas-a-egress-outer')?.value.trim() || '';
            const dnaasAEgressInner = document.getElementById('link-dnaas-a-egress-inner')?.value.trim() || '';
            result = this.applyVlanManipulation(outer, inner, dnaasAEgressAction, dnaasAEgressInner ? `${dnaasAEgressOuter}.${dnaasAEgressInner}` : dnaasAEgressOuter);
            [outer, inner] = parseStack(result);
            
            // 5. Apply Side A device Ingress manipulation (entering device A)
            const d1IngressAction = document.getElementById('link-d1-ingress-action')?.value || '';
            const d1IngressOuter = document.getElementById('link-d1-ingress-outer')?.value.trim() || '';
            const d1IngressInner = document.getElementById('link-d1-ingress-inner')?.value.trim() || '';
            result = this.applyVlanManipulation(outer, inner, d1IngressAction, d1IngressInner ? `${d1IngressOuter}.${d1IngressInner}` : d1IngressOuter);
            
            return result;
        }
    }
    
    // Update calculated stack display fields
    updateCalculatedStacks() {
        const stackToB = document.getElementById('link-calc-stack-to-b');
        const stackToA = document.getElementById('link-calc-stack-to-a');
        
        if (stackToB) {
            stackToB.value = this.calculateEgressStack('toB');
        }
        if (stackToA) {
            stackToA.value = this.calculateEgressStack('toA');
        }
        
        // Run VLAN validation
        this.validateVlanConfiguration();
    }
    
    // ============================================================================
    // INPUT VALIDATION FUNCTIONS
    // ============================================================================
    
    // Validate VLAN input (1-4096, ranges with "-", multiples with ",")
    validateVlanInput(value) {
        if (window.LinkDetailsHandlers) {
            return window.LinkDetailsHandlers.validateVlanInput(this, value);
        }
    }
    
    // Validate IPv4 address (x.x.x.x where x is 0-255)
    validateIPv4(value) {
        if (window.LinkDetailsHandlers) {
            return window.LinkDetailsHandlers.validateIPv4(this, value);
        }
    }
    
    // Validate IPv6 address
    validateIPv6(value) {
        if (window.LinkDetailsHandlers) {
            return window.LinkDetailsHandlers.validateIPv6(this, value);
        }
    }
    
    // Validate IP address based on type
    validateIpAddress(value, type) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.validateIpAddress === 'function') {
            return this.linkEditor.validateIpAddress(value, type);
        }
        
        // Fallback
        if (type === 'IPv4') return this.validateIPv4(value);
        if (type === 'IPv6') return this.validateIPv6(value);
        return { valid: true, value: value }; // L2-Service doesn't need IP validation
    }
    
    // Check if all link table inputs are valid
    checkLinkTableValidity() {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.checkLinkTableValidity === 'function') {
            return this.linkEditor.checkLinkTableValidity();
        }
        
        // Fallback: minimal implementation
        return { valid: true, errors: [] };
    }
    
    // Format validation errors for display
    formatValidationErrors(errors) {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.formatValidationErrors === 'function') {
            return this.linkEditor.formatValidationErrors(errors);
        }
        
        // Fallback
        if (!errors || errors.length === 0) return '';
        return errors.map(e => `• ${e.fieldName}: "${e.value}" - ${e.error}`).join('\n');
    }
    
    // Show validation error toast/notification
    showValidationErrorToast(errors) {
        if (this.linkEditor && typeof this.linkEditor.showValidationErrorToast === 'function') {
            return this.linkEditor.showValidationErrorToast(errors);
        }
        if (window.NotificationManager) {
            return window.NotificationManager.showValidationErrorToast(this, errors);
        }
    }
    
    
    // Validate VLAN configuration - check if egress from DNaaS matches interface VLAN-ID/Tags
    validateVlanConfiguration() {
        if (window.LinkDetailsHandlers) {
            return window.LinkDetailsHandlers.validateVlanConfiguration(this);
        }
    }
    
    setupVlanCalculationListeners() {
        if (window.LinkDetailsHandlers) {
            return window.LinkDetailsHandlers.setupVlanCalculationListeners(this);
        }
    }
    
    updateDnaasVlanFields() {
        // This function now just calls updateCalculatedStacks
        // All calculation is done through the calculateEgressStack function
        this.updateCalculatedStacks();
    }
    
    hideLinkDetails() {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.hide === 'function') {
            return this.linkEditor.hide();
        }
        
        // Fallback: original implementation
        console.log('hideLinkDetails() called');
        
        // Auto-save before closing (if valid)
        if (this.editingLink) {
            const validity = this.checkLinkTableValidity();
            if (validity.valid) {
                this.saveLinkDetailsQuiet();
                console.log('Link details auto-saved before closing');
            } else {
                // Show error toast when trying to close with invalid fields
                this.showValidationErrorToast(validity.errors);
                console.log('Link details not saved (invalid inputs)', validity.errors);
                // Don't close modal - let user fix the errors
                return;
            }
        }
        
        const modal = document.getElementById('link-details-modal');
        if (!modal) {
            console.error('Link details modal element not found!');
            return;
        }
        console.log('Removing show class from link details modal');
        modal.classList.remove('show');
        this.editingLink = null;
        this.editingBulLinks = null;
        console.log('Link details modal closed successfully');
    }
    
    // Force close link details (ignore validation - for close button)
    forceHideLinkDetails() {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.forceHide === 'function') {
            return this.linkEditor.forceHide();
        }
        
        // Fallback: original implementation
        console.log('forceHideLinkDetails() called - ignoring validation');
        
        const modal = document.getElementById('link-details-modal');
        if (!modal) {
            console.error('Link details modal element not found!');
            return;
        }
        
        // Stop observing resize when modal closes
        const modalContent = modal.querySelector('.link-table-modal');
        if (modalContent && this._modalResizeObserver) {
            this._modalResizeObserver.unobserve(modalContent);
        }
        
        // Check if there are invalid fields and warn user
        if (this.editingLink) {
            const validity = this.checkLinkTableValidity();
            if (!validity.valid) {
                // Show brief warning that changes weren't saved
                this.showValidationErrorToast(validity.errors);
            } else {
                // Valid - save before closing
                this.saveLinkDetailsQuiet();
            }
        }
        
        modal.classList.remove('show');
        this.editingLink = null;
        this.editingBulLinks = null;
        console.log('Link details modal force closed');
    }
    
    // Initialize floating labels for Link Table inputs
    initLinkTableFloatingLabels() {
        // Delegate to linkEditor module if available
        if (this.linkEditor && typeof this.linkEditor.initFloatingLabels === 'function') {
            return this.linkEditor.initFloatingLabels();
        }
        
        // Fallback: original implementation
        const fields = document.querySelectorAll('.link-table-field');
        fields.forEach(field => {
            const input = field.querySelector('input, select');
            if (input) {
                // Check initial value
                if (input.value) {
                    field.classList.add('has-value');
                }
                
                // Focus event
                input.addEventListener('focus', () => {
                    field.classList.add('focused');
                });
                
                // Blur event
                input.addEventListener('blur', () => {
                    field.classList.remove('focused');
                    if (input.value) {
                        field.classList.add('has-value');
                    } else {
                        field.classList.remove('has-value');
                    }
                });
                
                // Change event (for selects)
                input.addEventListener('change', () => {
                    if (input.value) {
                        field.classList.add('has-value');
                        field.classList.add('value-changed');
                        setTimeout(() => field.classList.remove('value-changed'), 300);
                    } else {
                        field.classList.remove('has-value');
                    }
                    
                    // Auto-save changes
                    this.updateLinkTableValue(input.id, input.value);
                });
                
                // Input event (for text inputs)
                input.addEventListener('input', () => {
                    if (input.value) {
                        field.classList.add('has-value');
                    } else {
                        field.classList.remove('has-value');
                    }
                    
                    // Auto-save changes
                    this.updateLinkTableValue(input.id, input.value);
                });
            }
        });
    }
    
    // Update link property from the new table
    updateLinkTableValue(inputId, value) {
        if (window.LinkTableManager) {
            return window.LinkTableManager.updateValue(this, inputId, value);
        }
    }
    
    // Update calculated/readonly fields
    updateLinkTableCalculatedFields() {
        if (window.LinkTableManager) {
            return window.LinkTableManager.updateCalculatedFields(this);
        }
    }
    
    // Reset all Link Table fields to empty
    resetLinkTableFields() {
        if (window.LinkTableManager) {
            return window.LinkTableManager.resetFields(this);
        }
    }
    
    // Copy Link Table as Markdown
    copyLinkTableAsMarkdown() {
        if (window.LinkTableManager) {
            return window.LinkTableManager.copyAsMarkdown(this);
        }
    }
    
    // Simple toast notification
    showToast(message, type = 'info') {
        if (this.linkEditor && typeof this.linkEditor.showToast === 'function') {
            return this.linkEditor.showToast(message, type);
        }
        if (window.NotificationManager) {
            return window.NotificationManager.showNotification(this, message, type);
        }
    }
    
    addInterfaceLabelsFromModal() {
        if (!this.editingLink) return;
        
        // Close modal and show interface menu
        this.hideLinkDetails();
        this.showAdjacentTextMenu(this.editingLink);
    }
    
    applyTextEditor() {
        if (!this.editingText) return;
        
        // Changes already applied via live preview, just save state
        this.saveState();
        
        // Values are already set by live preview listeners
        // Just update properties panel and close
        this.updatePropertiesPanel();
        this.hideTextEditor();
    }
    
    updateDeviceProperties() {
        // Device properties now controlled via device editor modal (double-click to open)
        // Left toolbar properties section removed
    }
    
    setMode(mode) {
        const oldMode = this.currentMode;
        
        // Explicitly set mode and clear states
        this.currentMode = mode;
        this.currentTool = mode === 'base' ? 'select' : mode;
        
        if (this.debugger && oldMode !== mode) {
            this.debugger.logStateChange('Mode', oldMode || 'none', mode.toUpperCase());
        }
        
        if (mode === 'base') {
            // Clear all selections and states
            this.selectedObject = null;
            this.selectedObjects = [];
            this.linking = false;
            this.linkStart = null;
            this.placingDevice = null;
            this.multiSelectMode = false;
            // BUGFIX: Always hide ALL selection toolbars when returning to base mode
            this.hideAllSelectionToolbars();
            // Also hide inline text editor if open
            this.hideInlineTextEditor();
        }
        
        // Update all button states - use safe access pattern
        const buttonIds = ['btn-base', 'btn-select', 'btn-link', 'btn-text'];
        buttonIds.forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.classList.remove('active');
        });
        
        if (mode !== 'base') {
            const activeBtn = document.getElementById(`btn-${mode}`);
            if (activeBtn) activeBtn.classList.add('active');
        } else {
            const baseBtn = document.getElementById('btn-base');
            if (baseBtn) baseBtn.classList.add('active');
        }
        
        this.updateModeIndicator();
        this.updatePropertiesPanel();
        this.draw();
    }
    
    updateModeIndicator() {
        const modeText = document.getElementById('mode-text');
        const modeIndicator = document.getElementById('mode-indicator');
        
        if (!modeText || !modeIndicator) return;
        
        // Add transition animation
        modeIndicator.style.transition = 'all 0.3s ease';
        
        if (this.currentMode === 'base') {
            modeText.textContent = 'BASE MODE';
            modeIndicator.style.background = '#95a5a6'; // Gray
            modeIndicator.style.color = '#2c3e50';
            modeIndicator.style.borderLeft = '4px solid #95a5a6';
        } else if (this.currentMode === 'select') {
            modeText.textContent = 'SELECT MODE';
            modeIndicator.style.background = '#3498db'; // Blue
            modeIndicator.style.color = 'white';
            modeIndicator.style.borderLeft = '4px solid #2980b9';
        } else if (this.currentMode === 'text') {
            modeText.textContent = 'TEXT MODE';
            modeIndicator.style.background = '#FF5E1F'; // Orange (theme color)
            modeIndicator.style.color = 'white';
            modeIndicator.style.borderLeft = '4px solid #CC4A16';
        } else if (this.currentMode === 'link') {
            modeText.textContent = 'LINK MODE';
            modeIndicator.style.background = '#FF5E1F'; // Orange
            modeIndicator.style.color = 'white';
            modeIndicator.style.borderLeft = '4px solid #CC4A16';
        }
        
        // Brief highlight animation on mode change
        modeIndicator.style.transform = 'scale(1.05)';
        setTimeout(() => {
            modeIndicator.style.transform = 'scale(1)';
        }, 200);
    }
    
    updatePropertiesPanel() {
        // Hide properties panel in Base mode
        if (this.currentMode === 'base' || !this.selectedObject) {
            // Device properties now use editor modal - removed from toolbar
            const textProps = document.getElementById('text-props');
            const textRotationProps = document.getElementById('text-rotation-props');
            if (textProps) textProps.style.display = 'none';
            if (textRotationProps) textRotationProps.style.display = 'none';
            return;
        }
        
        // Show appropriate properties in Select mode
        this.updateTextProperties();
    }
    
    cycleTextSize() {
        if (this.selectedObject && this.selectedObject.type === 'text') {
            let currentSize = parseInt(this.selectedObject.fontSize) || 14;
            // Cycle through sizes 1-12, but map to reasonable pixel values
            const sizeMap = [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48];
            let currentIndex = sizeMap.findIndex(s => s >= currentSize);
            if (currentIndex === -1) currentIndex = sizeMap.length - 1;
            
            currentIndex = (currentIndex + 1) % sizeMap.length;
            this.selectedObject.fontSize = sizeMap[currentIndex];
            const fontSizeInput = document.getElementById('font-size');
            if (fontSizeInput) fontSizeInput.value = sizeMap[currentIndex];
            this.draw();
        }
    }
    
    showContextMenu(x, y, obj) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.showContextMenu(this, x, y, obj);
        }
    }
    
    /**
     * Helper to adjust menu position to keep it within viewport bounds
     */
    _adjustMenuPosition(x, y, menu) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers._adjustMenuPosition(this, x, y, menu);
        }
    }
    
    hideContextMenu() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.hideContextMenu(this);
        }
    }
    
    handleContextCopyStyle() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.handleContextCopyStyle(this);
        }
    }
    
    // Copy style from an object
    // ENHANCED: Stores ALL style properties from any object type for universal pasting
    copyObjectStyle(obj) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.copyObjectStyle(this, obj);
        }
    }
    
    // Internal helper: Apply style properties to a single object (no saveState)
    // Used by both pasteStyleToObject and CS-MS batch operations
    _applyStyleToObject(obj) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers._applyStyleToObject(this, obj);
        }
    }
    
    // Paste style to a target object
    // ENHANCED: Works universally between ALL object types - applies whatever properties are applicable
    pasteStyleToObject(targetObj) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.pasteStyleToObject(this, targetObj);
        }
    }
    
    // Exit paste style mode
    exitPasteStyleMode() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.exitPasteStyleMode(this);
        }
    }
    
    handleContextDuplicate() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.handleContextDuplicate(this);
        }
    }
    
    handleContextAddText() {
        if (this.selectedObject) {
            if (this.selectedObject.type === 'link' || this.selectedObject.type === 'unbound') {
                // Show menu to choose position
                this.showAdjacentTextMenu(this.selectedObject);
            } else if (this.selectedObject.type === 'device') {
                // Add text near device
                const text = this.createText(this.selectedObject.x + this.selectedObject.radius + 10, this.selectedObject.y);
                text.text = '';
                this.objects.push(text);
                this.selectedObject = text;
                this.selectedObjects = [text];
                this.updateTextProperties();
                this.draw();
            }
        }
        this.hideContextMenu();
    }
    
    handleContextToggleCurve() {
        // Get the target link - prioritize _curveSubmenuLink (from context menu), then selectedObjects, then selectedObject
        const targetLink = this._curveSubmenuLink || this.selectedObject;
        
        // Handle bulk curve toggle for multiple selected links
        const selectedLinks = this.selectedObjects.filter(obj => obj.type === 'link' || obj.type === 'unbound');
        
        if (selectedLinks.length > 0) {
            this.saveState();
            
            // Determine if we're enabling or disabling curves
            // Check first link to determine action
            const firstLink = selectedLinks[0];
            const currentCurveState = (firstLink.curveOverride !== undefined ? firstLink.curveOverride : this.linkCurveMode) && this.magneticFieldStrength > 0;
            const newCurveState = !currentCurveState;
            
            // Apply to all selected links
            selectedLinks.forEach(link => {
                link.curveOverride = newCurveState;
            });
            
            if (this.debugger) {
                this.debugger.logSuccess(`🌊 Curve ${newCurveState ? 'enabled' : 'disabled'} for ${selectedLinks.length} links`);
            }
            
            this.draw();
        } else if (targetLink && (targetLink.type === 'link' || targetLink.type === 'unbound')) {
            // Single link toggle
            this.saveState();
            if (this.magneticFieldStrength === 0) {
                // Can't enable curves when magnetic field is 0
                if (this.debugger) {
                    this.debugger.logError('🌊 Cannot enable curves: Magnetic field strength is 0');
                }
                return;
            }
            if (targetLink.curveOverride === undefined) {
                // No override set, use opposite of global
                targetLink.curveOverride = !this.linkCurveMode;
            } else {
                // Toggle the override
                targetLink.curveOverride = !targetLink.curveOverride;
            }
            
            if (this.debugger) {
                this.debugger.logSuccess(`🌊 Link curve ${targetLink.curveOverride ? 'enabled' : 'disabled'}`);
            }
            
            this.draw();
        }
        this.hideContextMenu();
    }
    
    // Toggle "Keep Current Curve" for UL/BUL from context menu
    handleContextKeepCurve() {
        // Get the target link - prioritize _curveSubmenuLink (from context menu), then selectedObject
        const targetLink = this._curveSubmenuLink || this.selectedObject;
        
        // Handle unbound links only
        const selectedLinks = this.selectedObjects.filter(obj => obj.type === 'unbound');
        
        if (selectedLinks.length > 0) {
            this.saveState();
            
            // Determine if we're enabling or disabling keep curve
            const firstLink = selectedLinks[0];
            const newKeepCurve = !firstLink.keepCurve;
            
            // Apply to all selected unbound links
            selectedLinks.forEach(link => {
                if (newKeepCurve) {
                    // Save current curve
                    link.keepCurve = true;
                    if (link._cp1 && link._cp2) {
                        const midX = (link.start.x + link.end.x) / 2;
                        const midY = (link.start.y + link.end.y) / 2;
                        const linkLength = Math.sqrt(
                            Math.pow(link.end.x - link.start.x, 2) + 
                            Math.pow(link.end.y - link.start.y, 2)
                        );
                        link.savedCurveOffset = {
                            cp1OffsetX: (link._cp1.x - midX) / (linkLength || 1),
                            cp1OffsetY: (link._cp1.y - midY) / (linkLength || 1),
                            cp2OffsetX: (link._cp2.x - midX) / (linkLength || 1),
                            cp2OffsetY: (link._cp2.y - midY) / (linkLength || 1)
                        };
                    }
                } else {
                    // Clear saved curve
                    link.keepCurve = false;
                    delete link.savedCurveOffset;
                    delete link.savedCp1;
                    delete link.savedCp2;
                }
            });
            
            if (this.debugger) {
                this.debugger.logSuccess(`🔒 Keep Curve ${newKeepCurve ? 'enabled' : 'disabled'} for ${selectedLinks.length} links`);
            }
            
            this.draw();
        } else if (targetLink && targetLink.type === 'unbound') {
            // Single link toggle
            this.saveState();
            const link = targetLink;
            
            // If part of BUL, apply to all links in chain
            const linksToUpdate = (link.mergedWith || link.mergedInto) 
                ? this.getAllMergedLinks(link) 
                : [link];
            
            const newKeepCurve = !link.keepCurve;
            
            linksToUpdate.forEach(l => {
                if (newKeepCurve) {
                    l.keepCurve = true;
                    if (l._cp1 && l._cp2) {
                        const midX = (l.start.x + l.end.x) / 2;
                        const midY = (l.start.y + l.end.y) / 2;
                        const linkLength = Math.sqrt(
                            Math.pow(l.end.x - l.start.x, 2) + 
                            Math.pow(l.end.y - l.start.y, 2)
                        );
                        l.savedCurveOffset = {
                            cp1OffsetX: (l._cp1.x - midX) / (linkLength || 1),
                            cp1OffsetY: (l._cp1.y - midY) / (linkLength || 1),
                            cp2OffsetX: (l._cp2.x - midX) / (linkLength || 1),
                            cp2OffsetY: (l._cp2.y - midY) / (linkLength || 1)
                        };
                    }
                } else {
                    l.keepCurve = false;
                    delete l.savedCurveOffset;
                    delete l.savedCp1;
                    delete l.savedCp2;
                }
            });
            
            this.draw();
        }
        this.hideContextMenu();
    }
    
    handleContextCurveMPs() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.handleContextCurveMPs(this);
        }
    }
    
    showAdjacentTextMenu(link) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.showAdjacentTextMenu(this, link);
        }
    }
    
    updateAdjacentTextPosition(textObj) {
        // Find the linked link
        const link = this.objects.find(obj => obj.id === textObj.linkId);
        if (!link) return;
        
        // Calculate current link positions (they should already be updated)
        let linkStart = link.start;
        let linkEnd = link.end;
        
        // DEFENSIVE: Ensure link has valid start/end positions
        if (!linkStart || !linkEnd || 
            linkStart.x === undefined || linkStart.y === undefined ||
            linkEnd.x === undefined || linkEnd.y === undefined ||
            isNaN(linkStart.x) || isNaN(linkStart.y) || isNaN(linkEnd.x) || isNaN(linkEnd.y)) {
            console.warn('updateAdjacentTextPosition: Invalid link positions for', link.id);
            return; // Don't update text position if link data is invalid
        }
        
        // For device links, recalculate positions if needed
        if (link.type === 'link' && link.device1 && link.device2) {
            const device1 = this.objects.find(o => o.id === link.device1);
            const device2 = this.objects.find(o => o.id === link.device2);
            if (device1 && device2) {
                const straightAngle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
                linkStart = {
                    x: device1.x + Math.cos(straightAngle) * device1.radius,
                    y: device1.y + Math.sin(straightAngle) * device1.radius
                };
                linkEnd = {
                    x: device2.x - Math.cos(straightAngle) * device2.radius,
                    y: device2.y - Math.sin(straightAngle) * device2.radius
                };
            }
        }
        
        // CRITICAL FIX (Dec 2025): Check if link is curved and use bezier curve position
        // Text boxes should follow the VISUAL curve, not the straight line
        // NOTE: _cp1/_cp2 are set during draw(), so we may need to calculate them here
        let curveControlPoints = null;
        
        // Check if we have stored control points from the last draw
        if (link._cp1 && link._cp2 && 
            link._cp1.x !== undefined && link._cp1.y !== undefined &&
            link._cp2.x !== undefined && link._cp2.y !== undefined) {
            curveControlPoints = { cp1: link._cp1, cp2: link._cp2 };
        } else {
            // Control points not yet set - calculate them on-the-fly if curve mode is enabled
            const curveEnabled = (link.curveOverride !== undefined ? link.curveOverride : this.linkCurveMode) && 
                                 this.magneticFieldStrength > 0;
            
            if (curveEnabled) {
                // Find obstacles that might cause curve deflection
                const obstacles = this.findAllObstaclesOnPath(linkStart.x, linkStart.y, linkEnd.x, linkEnd.y, link);
                
                if (obstacles.length > 0) {
                    // Calculate magnetic deflection (same algorithm as drawLink/drawUnboundLink)
                    const straightMidX = (linkStart.x + linkEnd.x) / 2;
                    const straightMidY = (linkStart.y + linkEnd.y) / 2;
                    const linkLength = Math.sqrt(Math.pow(linkEnd.x - linkStart.x, 2) + Math.pow(linkEnd.y - linkStart.y, 2));
                    
                    let totalRepulsionX = 0;
                    let totalRepulsionY = 0;
                    let closestObstacleRadius = 0;
                    
                    const effectiveMagnitude = link.curveMagnitude !== undefined ? link.curveMagnitude : this.magneticFieldStrength;
                    
                    obstacles.forEach((obstacleInfo) => {
                        const obstacle = obstacleInfo.device;
                        const dx = straightMidX - obstacle.x;
                        const dy = straightMidY - obstacle.y;
                        const distToMid = Math.sqrt(dx * dx + dy * dy) || 1;
                        const minClearance = obstacle.radius + 18;
                        const repelDirX = dx / distToMid;
                        const repelDirY = dy / distToMid;
                        const k = minClearance * minClearance * effectiveMagnitude * 2;
                        const repulsionStrength = k / Math.pow(distToMid, 0.8);
                        totalRepulsionX += repelDirX * repulsionStrength;
                        totalRepulsionY += repelDirY * repulsionStrength;
                        closestObstacleRadius = Math.max(closestObstacleRadius, obstacle.radius);
                    });
                    
                    const deflectionMag = Math.sqrt(totalRepulsionX * totalRepulsionX + totalRepulsionY * totalRepulsionY);
                    const maxDeflection = Math.min(linkLength * 0.45, closestObstacleRadius * 2.5);
                    const actualDeflection = Math.min(deflectionMag, maxDeflection);
                    const normalizedRepulX = totalRepulsionX / (deflectionMag || 1);
                    const normalizedRepulY = totalRepulsionY / (deflectionMag || 1);
                    const deflectedMidX = straightMidX + normalizedRepulX * actualDeflection;
                    const deflectedMidY = straightMidY + normalizedRepulY * actualDeflection;
                    
                    // Calculate control points
                    const controlWeight = 0.7;
                    const midWeight = 1 - controlWeight;
                    curveControlPoints = {
                        cp1: { 
                            x: linkStart.x * midWeight + deflectedMidX * controlWeight, 
                            y: linkStart.y * midWeight + deflectedMidY * controlWeight 
                        },
                        cp2: { 
                            x: linkEnd.x * midWeight + deflectedMidX * controlWeight, 
                            y: linkEnd.y * midWeight + deflectedMidY * controlWeight 
                        }
                    };
                }
            }
        }
        
        const hasCurve = curveControlPoints !== null;
        
        // Helper function to get point on curve at parameter t
        const getPointOnCurve = (t) => {
            if (hasCurve) {
                // Use bezier curve calculation with calculated control points
                const cp1 = curveControlPoints.cp1;
                const cp2 = curveControlPoints.cp2;
                const t2 = t * t;
                const t3 = t2 * t;
                const mt = 1 - t;
                const mt2 = mt * mt;
                const mt3 = mt2 * mt;
                return {
                    x: mt3 * linkStart.x + 3 * mt2 * t * cp1.x + 3 * mt * t2 * cp2.x + t3 * linkEnd.x,
                    y: mt3 * linkStart.y + 3 * mt2 * t * cp1.y + 3 * mt * t2 * cp2.y + t3 * linkEnd.y
                };
            } else {
                // Linear interpolation for straight links
                return {
                    x: linkStart.x + (linkEnd.x - linkStart.x) * t,
                    y: linkStart.y + (linkEnd.y - linkStart.y) * t
                };
            }
        };
        
        // Helper function to get tangent angle at parameter t (for perpendicular offset)
        const getTangentAngle = (t) => {
            if (hasCurve) {
                // Derivative of cubic bezier for tangent direction
                const cp1 = curveControlPoints.cp1;
                const cp2 = curveControlPoints.cp2;
                const mt = 1 - t;
                const mt2 = mt * mt;
                const t2 = t * t;
                // Derivative: B'(t) = 3(1-t)²(P1-P0) + 6(1-t)t(P2-P1) + 3t²(P3-P2)
                const dx = 3 * mt2 * (cp1.x - linkStart.x) + 
                           6 * mt * t * (cp2.x - cp1.x) + 
                           3 * t2 * (linkEnd.x - cp2.x);
                const dy = 3 * mt2 * (cp1.y - linkStart.y) + 
                           6 * mt * t * (cp2.y - cp1.y) + 
                           3 * t2 * (linkEnd.y - cp2.y);
                return Math.atan2(dy, dx);
            } else {
                // Straight line tangent
                return Math.atan2(linkEnd.y - linkStart.y, linkEnd.x - linkStart.x);
            }
        };
        
        // NORMALIZE perpendicular direction (match drawLink)
        const sortedIds = [link.device1, link.device2].sort();
        const isNormalDirection = link.device1 === sortedIds[0];
        
        // Calculate link offset based on linkIndex (to match the actual link position)
        // User requested logic: First (0) = Middle, Second (1) = Right (+), Third (2) = Left (-)
        const linkIndex = link.linkIndex || 0;
        let linkOffsetAmount = 0;
        let linkDirection = 0;
        if (linkIndex > 0) {
            const magnitude = Math.ceil(linkIndex / 2) * 20;
            linkDirection = (linkIndex % 2 === 1) ? 1 : -1; // Odd = Right (+), Even = Left (-)
            linkOffsetAmount = magnitude * linkDirection;
        }
        
        // Base offset for text from link (perpendicular distance)
        const baseTextOffset = 12;
        
        // Auto-determine side based on link offset direction
        const autoSide = linkDirection >= 0 ? -1 : 1;
        
        // Determine position based on stored position value
        // CRITICAL FIX (Jan 2026): Track the actual t value used for text positioning
        // so we can use the correct tangent angle for rotation on curved links
        let textX, textY;
        let attachmentT = 0.5; // Default to middle, will be updated per position
        
        if (textObj.position === 'device1-top' || textObj.position === 'device1-bottom') {
            // Legacy position with explicit top/bottom
            const side = textObj.position.includes('top') ? -1 : 1;
            attachmentT = 0.15;
            const curvePoint = getPointOnCurve(attachmentT);
            const localPerpAngle = getTangentAngle(attachmentT) + Math.PI / 2 + (isNormalDirection ? 0 : Math.PI);
            const totalOffset = linkOffsetAmount + (baseTextOffset * side);
            textX = curvePoint.x + Math.cos(localPerpAngle) * totalOffset;
            textY = curvePoint.y + Math.sin(localPerpAngle) * totalOffset;
        } else if (textObj.position === 'device2-top' || textObj.position === 'device2-bottom') {
            // Legacy position with explicit top/bottom
            const side = textObj.position.includes('top') ? -1 : 1;
            attachmentT = 0.85;
            const curvePoint = getPointOnCurve(attachmentT);
            const localPerpAngle = getTangentAngle(attachmentT) + Math.PI / 2 + (isNormalDirection ? 0 : Math.PI);
            const totalOffset = linkOffsetAmount + (baseTextOffset * side);
            textX = curvePoint.x + Math.cos(localPerpAngle) * totalOffset;
            textY = curvePoint.y + Math.sin(localPerpAngle) * totalOffset;
        } else if (textObj.position === 'device1') {
            // Simplified position - auto-determine side
            attachmentT = 0.15;
            const curvePoint = getPointOnCurve(attachmentT);
            const localPerpAngle = getTangentAngle(attachmentT) + Math.PI / 2 + (isNormalDirection ? 0 : Math.PI);
            
            // ENHANCED: Same seamless transparent behavior as middle position
            const hasNoBackground = textObj.showBackground === false;
            const bgOpacity = textObj.backgroundOpacity !== undefined ? textObj.backgroundOpacity : 95;
            const hasHighOpacityBackground = textObj.showBackground !== false && bgOpacity > 50;
            
            if (hasNoBackground || hasHighOpacityBackground) {
                // On-link: place directly on curve, create gap
                textX = curvePoint.x + Math.cos(localPerpAngle) * linkOffsetAmount;
                textY = curvePoint.y + Math.sin(localPerpAngle) * linkOffsetAmount;
                textObj._onLinkLine = true;
            } else {
                // Off-link: offset away from curve
                const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
                textX = curvePoint.x + Math.cos(localPerpAngle) * totalOffset;
                textY = curvePoint.y + Math.sin(localPerpAngle) * totalOffset;
                textObj._onLinkLine = false;
            }
        } else if (textObj.position === 'device2') {
            // Simplified position - auto-determine side
            attachmentT = 0.85;
            const curvePoint = getPointOnCurve(attachmentT);
            const localPerpAngle = getTangentAngle(attachmentT) + Math.PI / 2 + (isNormalDirection ? 0 : Math.PI);
            
            // ENHANCED: Same seamless transparent behavior as middle position
            const hasNoBackground = textObj.showBackground === false;
            const bgOpacity = textObj.backgroundOpacity !== undefined ? textObj.backgroundOpacity : 95;
            const hasHighOpacityBackground = textObj.showBackground !== false && bgOpacity > 50;
            
            if (hasNoBackground || hasHighOpacityBackground) {
                // On-link: place directly on curve, create gap
                textX = curvePoint.x + Math.cos(localPerpAngle) * linkOffsetAmount;
                textY = curvePoint.y + Math.sin(localPerpAngle) * linkOffsetAmount;
                textObj._onLinkLine = true;
            } else {
                // Off-link: offset away from curve
                const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
                textX = curvePoint.x + Math.cos(localPerpAngle) * totalOffset;
                textY = curvePoint.y + Math.sin(localPerpAngle) * totalOffset;
                textObj._onLinkLine = false;
            }
        } else if (textObj.position === 'middle') {
            // MIDDLE POSITION: Seamless transparent attachment at center of link
            // Text is placed DIRECTLY ON the curve at the middle point
            
            // CRITICAL FIX (Jan 2026): In MANUAL curve mode, TB and CP are synchronized
            const effectiveCurveMode = this.getEffectiveCurveMode(link);
            if (effectiveCurveMode === 'manual') {
                // Check if TB already has valid coordinates
                const tbHasValidPos = textObj.x !== undefined && textObj.y !== undefined && 
                                      !isNaN(textObj.x) && !isNaN(textObj.y);
                
                // If link has a manualCurvePoint and TB is being placed/attached, move TB to curve point
                if (link.manualCurvePoint && (!tbHasValidPos || textObj._justAttached)) {
                    // TB follows the existing curve point
                    textObj.x = link.manualCurvePoint.x;
                    textObj.y = link.manualCurvePoint.y;
                    textObj._onLinkLine = true;
                    delete textObj._justAttached;
                    return;
                }
                
                // TB already has valid position - it's the master, sync curve to TB
                if (tbHasValidPos) {
                    // Sync link's curve point to TB position (TB is the master)
                    if (!link.manualCurvePoint || 
                        link.manualCurvePoint.x !== textObj.x || 
                        link.manualCurvePoint.y !== textObj.y) {
                        link.manualCurvePoint = { x: textObj.x, y: textObj.y };
                        link.manualControlPoint = { x: textObj.x, y: textObj.y };
                    }
                    // TB stays in place - return early without recalculating position
                    textObj._onLinkLine = true;
                    return;
                }
            }
            
            // Auto mode or no existing position: calculate from curve
            attachmentT = textObj.linkAttachT !== undefined ? textObj.linkAttachT : 0.5;
            const curvePoint = getPointOnCurve(attachmentT);
            
            // For parallel links (linkIndex > 0), offset perpendicular to follow the offset link
            const localPerpAngle = getTangentAngle(attachmentT) + Math.PI / 2 + (isNormalDirection ? 0 : Math.PI);
            
            // Place DIRECTLY on the curve point (or on the offset line for parallel links)
            textX = curvePoint.x + Math.cos(localPerpAngle) * linkOffsetAmount;
            textY = curvePoint.y + Math.sin(localPerpAngle) * linkOffsetAmount;
            
            // Always create gap for middle position (seamless look)
            textObj._onLinkLine = true;
        } else if (textObj.position === 'custom') {
            // CUSTOM POSITION: Exact position from drag-and-drop attachment (non-middle)
            attachmentT = textObj.linkAttachT !== undefined ? textObj.linkAttachT : 0.5;
            const curvePoint = getPointOnCurve(attachmentT);
            const localPerpAngle = getTangentAngle(attachmentT) + Math.PI / 2 + (isNormalDirection ? 0 : Math.PI);
            
            // Custom positions: offset away from link (not on the link line)
                const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
                textX = curvePoint.x + Math.cos(localPerpAngle) * totalOffset;
                textY = curvePoint.y + Math.sin(localPerpAngle) * totalOffset;
                textObj._onLinkLine = false;
        } else {
            // Middle (default for unbound links)
            // CRITICAL FIX (Dec 2025): Use curve midpoint, not straight line midpoint
            attachmentT = 0.5;
            const curvePoint = getPointOnCurve(attachmentT);
            const localPerpAngle = getTangentAngle(attachmentT) + Math.PI / 2 + (isNormalDirection ? 0 : Math.PI);
            
            // SMART ATTACHMENT (Jan 2026): Behavior based on background and opacity
            // - No background: text overlays link directly (no gap)
            // - Background + high opacity (>50%): gap created in link
            // - Background + low opacity (<=50%): overlay with transparent background, no gap
            const hasNoBackground = textObj.showBackground === false;
            const bgOpacity = textObj.backgroundOpacity !== undefined ? textObj.backgroundOpacity : 95;
            const hasHighOpacityBackground = textObj.showBackground !== false && bgOpacity > 50;
            
            if (hasNoBackground) {
                // No background: place on curve AND create gap (link hidden, grid shows through letters)
                textX = curvePoint.x + Math.cos(localPerpAngle) * linkOffsetAmount;
                textY = curvePoint.y + Math.sin(localPerpAngle) * linkOffsetAmount;
                textObj._onLinkLine = true; // Create gap in link - grid shows through letter gaps
            } else if (hasHighOpacityBackground) {
                // High opacity background: place on curve AND create gap
                textX = curvePoint.x + Math.cos(localPerpAngle) * linkOffsetAmount;
                textY = curvePoint.y + Math.sin(localPerpAngle) * linkOffsetAmount;
                textObj._onLinkLine = true; // Flag for link drawing to create gap
            } else {
                // Low opacity background: overlay without gap
                textX = curvePoint.x + Math.cos(localPerpAngle) * linkOffsetAmount;
                textY = curvePoint.y + Math.sin(localPerpAngle) * linkOffsetAmount;
                textObj._onLinkLine = false; // No gap - semi-transparent overlay
            }
        }
        
        // Update text position and rotation
        // DEFENSIVE: Only update if coordinates are valid numbers
        if (typeof textX === 'number' && typeof textY === 'number' && 
            !isNaN(textX) && !isNaN(textY) && isFinite(textX) && isFinite(textY)) {
            textObj.x = textX;
            textObj.y = textY;
        } else {
            console.warn('updateAdjacentTextPosition: Invalid calculated position', textX, textY);
            return; // Don't update with invalid values
        }
        
        // Rotate text to follow link tangent — but skip when:
        // - alwaysFaceUser is true (user wants 0° horizontal)
        // - user is actively rotating this TB via drag handle
        const skipRotation = textObj.alwaysFaceUser === true ||
            (this.rotatingText && this.selectedObject === textObj);
        
        if (!skipRotation) {
            const localTangentAngle = getTangentAngle(attachmentT);
            let rotationDegrees = localTangentAngle * 180 / Math.PI;
            
            while (rotationDegrees > 180) rotationDegrees -= 360;
            while (rotationDegrees < -180) rotationDegrees += 360;
            
            if (rotationDegrees > 90 || rotationDegrees < -90) {
                rotationDegrees += 180;
                while (rotationDegrees > 180) rotationDegrees -= 360;
                while (rotationDegrees < -180) rotationDegrees += 360;
            }
            
            textObj.rotation = rotationDegrees;
        } else if (textObj.alwaysFaceUser === true) {
            textObj.rotation = 0;
        }
    }
    
    addAdjacentText(link, position = 'middle', textContent = 'Label') {
        if (window.TextAttachment) {
            return window.TextAttachment.addAdjacentText(this, link, position = 'middle', textContent = 'Label');
        }
    }
    
    findObstacleOnPath(startX, startY, endX, endY, link = null) {
        // Check for devices or other objects that intersect the link path
        const pathLength = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
        const pathAngle = Math.atan2(endY - startY, endX - startX);
        
        // Get connected devices to exclude them
        const connectedDeviceIds = [];
        if (link && link.device1) connectedDeviceIds.push(link.device1);
        if (link && link.device2) connectedDeviceIds.push(link.device2);
        
        for (const obj of this.objects) {
            if (obj.type === 'device' && !connectedDeviceIds.includes(obj.id)) {
                // Check if device is near the link path
                const dx = obj.x - startX;
                const dy = obj.y - startY;
                
                // Project device position onto link path
                const projLength = dx * Math.cos(pathAngle) + dy * Math.sin(pathAngle);
                const projX = startX + Math.cos(pathAngle) * projLength;
                const projY = startY + Math.sin(pathAngle) * projLength;
                
                // Distance from device to link path
                const distToPath = Math.sqrt(Math.pow(obj.x - projX, 2) + Math.pow(obj.y - projY, 2));
                
                // Check if device is within link path bounds and close enough
                // Leave some margin at start and end to avoid curving around connected devices
                const margin = 40;
                const detectionThreshold = obj.radius + 25; // Detection zone to trigger curve
                if (projLength > margin && projLength < pathLength - margin && distToPath < detectionThreshold) {
                    return obj;
                }
            }
        }
        return null;
    }
    
    findAllObstaclesOnPath(startX, startY, endX, endY, link = null) {
        // Find ALL devices that intersect the link path for multi-obstacle avoidance
        const obstacles = [];
        const pathLength = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
        const pathAngle = Math.atan2(endY - startY, endX - startX);
        
        // Get connected devices to exclude them
        const connectedDeviceIds = [];
        if (link && link.device1) connectedDeviceIds.push(link.device1);
        if (link && link.device2) connectedDeviceIds.push(link.device2);
        
        for (const obj of this.objects) {
            if (obj.type === 'device' && !connectedDeviceIds.includes(obj.id)) {
                // Check if device is near the link path
                const dx = obj.x - startX;
                const dy = obj.y - startY;
                
                // Project device position onto link path
                const projLength = dx * Math.cos(pathAngle) + dy * Math.sin(pathAngle);
                const projX = startX + Math.cos(pathAngle) * projLength;
                const projY = startY + Math.sin(pathAngle) * projLength;
                
                // Distance from device to link path
                const distToPath = Math.sqrt(Math.pow(obj.x - projX, 2) + Math.pow(obj.y - projY, 2));
                
                // Check if device is within link path bounds and close enough
                const margin = 40;
                const detectionThreshold = obj.radius + 25; // Detection zone - curve earlier for safety
                if (projLength > margin && projLength < pathLength - margin && distToPath < detectionThreshold) {
                    obstacles.push({
                        device: obj,
                        projLength: projLength,
                        distToPath: distToPath
                    });
                }
            }
        }
        
        // Sort obstacles by their position along the path
        obstacles.sort((a, b) => a.projLength - b.projLength);
        return obstacles;
    }
    
    handleContextColor() {
        // Show color palette next to context menu for quick color selection
        if (this.selectedObject) {
            if (this.selectedObject.type === 'text') {
                // For text boxes, open the text editor modal
        this.hideContextMenu();
                this.showTextEditor(this.selectedObject);
            } else if (this.selectedObject.type === 'device') {
                // For devices, show color palette adjacent to context menu
                this.showColorPalettePopup(this.selectedObject, 'device');
            } else if (this.selectedObject.type === 'link' || this.selectedObject.type === 'unbound') {
                // For links, show color palette adjacent to context menu
                this.showColorPalettePopup(this.selectedObject, 'link');
            }
        }
    }
    
    showColorPalettePopup(obj, objType) {
        if (window.ColorPopups) {
            return window.ColorPopups.showColorPalettePopup(this, obj, objType);
        }
    }
    
    applyColorToObject(obj, color) {
        this.saveState();
        
        // ENHANCED: For links in a BUL chain, apply color to ALL links in the chain
        if ((obj.type === 'link' || obj.type === 'unbound') && (obj.mergedWith || obj.mergedInto)) {
            const allLinksInChain = this.getAllMergedLinks(obj);
            for (const chainLink of allLinksInChain) {
                chainLink.color = color;
            }
        } else {
            obj.color = color;
        }
        
        this.addRecentColor(color);
        this.draw();
    }
    
    // Color palette popup positioned relative to a toolbar element
    showColorPalettePopupFromToolbar(obj, objType, toolbar) {
        if (window.ColorPopups) {
            return window.ColorPopups.showColorPalettePopupFromToolbar(this, obj, objType, toolbar);
        }
    }
    
    hideColorPalettePopup() {
        if (window.ColorPopups) {
            return window.ColorPopups.hideColorPalettePopup(this);
        }
        const popup = document.getElementById('color-palette-popup');
        if (popup) popup.remove();
        this._colorEditingLink = null;
        this.draw();
    }
    
    // Close all popups, toolbars, and menus - used when panning or other global actions
    hideAllPopups() {
        // Hide toolbars
        this.hideTextSelectionToolbar();
        this.hideDeviceSelectionToolbar();
        this.hideLinkSelectionToolbar();
        this.hideShapeSelectionToolbar();
        
        // Hide context menu
        this.hideContextMenu();
        
        // Hide LLDP inline submenu (but NOT the table dialog — it's a persistent window)
        const lldpSubmenu = document.getElementById('lldp-inline-submenu');
        if (lldpSubmenu) lldpSubmenu.remove();
        
        // Hide color palettes
        this.hideColorPalettePopup();
        const textColorPalette = document.getElementById('text-color-palette-popup');
        if (textColorPalette) textColorPalette.remove();
        const textBgColorPalette = document.getElementById('text-bg-color-palette-popup');
        if (textBgColorPalette) textBgColorPalette.remove();
        
        // Hide device style palette
        const deviceStylePalette = document.getElementById('device-style-palette-popup');
        if (deviceStylePalette) deviceStylePalette.remove();
        
        // Hide link style/curve options
        const linkStylePopup = document.getElementById('link-style-options-popup');
        if (linkStylePopup) linkStylePopup.remove();
        const linkCurvePopup = document.getElementById('link-curve-options-popup');
        if (linkCurvePopup) linkCurvePopup.remove();
        const linkWidthSlider = document.getElementById('link-width-slider-popup');
        if (linkWidthSlider) linkWidthSlider.remove();
        
        // Hide font selector
        const fontSelector = document.getElementById('text-font-selector-popup');
        if (fontSelector) fontSelector.remove();
        
        // Hide any other floating popups
        const adjacentTextMenu = document.getElementById('adjacent-text-menu');
        if (adjacentTextMenu) adjacentTextMenu.remove();
    }
    
    handleContextSize() {
        this.hideContextMenu();
        if (this.selectedObject) {
            if (this.selectedObject.type === 'device') {
                // Open device editor for full control
                this.showDeviceEditor(this.selectedObject);
            } else if (this.selectedObject.type === 'text') {
                // Open text editor for full control
                this.showTextEditor(this.selectedObject);
            } else if (this.selectedObject.type === 'link' || this.selectedObject.type === 'unbound') {
                // Open link editor for full control
                this.showLinkEditor(this.selectedObject);
            }
        }
    }
    
    handleContextWidth() {
        // Get the target link - prioritize _curveSubmenuLink (from context menu), then selectedObject
        const targetLink = this._curveSubmenuLink || this.selectedObject;
        
        // Show width slider popup next to context menu (like color palette)
        if (targetLink && (targetLink.type === 'link' || targetLink.type === 'unbound')) {
            this.showWidthSliderPopup(targetLink);
        }
    }
    
    showWidthSliderPopup(link) {
        if (window.LinkPopups) {
            return window.LinkPopups.showWidthSliderPopup(this, link);
        }
    }
    
    hideWidthSliderPopup() {
        if (window.LinkPopups) {
            return window.LinkPopups.hideWidthSliderPopup(this);
        }
        const popup = document.getElementById('width-slider-popup');
        if (popup) popup.remove();
        this._colorEditingLink = null;
    }
    
    handleContextStyle() {
        // Get the target link - prioritize _curveSubmenuLink (from context menu), then selectedObject
        const targetLink = this._curveSubmenuLink || this.selectedObject;
        
        // Show style options popup next to context menu (like color palette)
        if (targetLink && (targetLink.type === 'link' || targetLink.type === 'unbound')) {
            this.showStyleOptionsPopup(targetLink);
        }
    }
    
    showStyleOptionsPopup(link) {
        if (window.LinkPopups) {
            return window.LinkPopups.showStyleOptionsPopup(this, link);
        }
    }
    
    hideStyleOptionsPopup() {
        if (window.LinkPopups) {
            return window.LinkPopups.hideStyleOptionsPopup(this);
        }
        const popup = document.getElementById('style-options-popup');
        if (popup) popup.remove();
        this._colorEditingLink = null;
    }
    
    // ========================================
    // CURVE SUBMENU HANDLERS
    // ========================================
    
    showCurveSubmenu() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.showCurveSubmenu(this);
        }
    }
    
    updateCurveSubmenuItems() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.updateCurveSubmenuItems(this);
        }
    }
    
    hideCurveSubmenu() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.hideCurveSubmenu(this);
        }
    }
    
    hideCurveSubmenuIfNotHovered() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.hideCurveSubmenuIfNotHovered(this);
        }
    }
    
    /**
     * Show the curve mode submenu (per-link curve mode selection)
     */
    showCurveModeSubmenu() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.showCurveModeSubmenu(this);
        }
    }
    
    /**
     * Hide the curve mode submenu
     */
    hideCurveModeSubmenu() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.hideCurveModeSubmenu(this);
        }
    }
    
    /**
     * Hide curve mode submenu if not being hovered (delayed hide for better UX)
     */
    hideCurveModeSubmenuIfNotHovered() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.hideCurveModeSubmenuIfNotHovered(this);
        }
    }
    
    /**
     * Update curve mode submenu items with checkmarks
     */
    updateCurveModeSubmenuItems() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.updateCurveModeSubmenuItems(this);
        }
    }
    
    /**
     * Handle curve mode change from context menu
     * @param {string|null} mode - 'auto', 'manual', 'off', or null for global
     */
    handleContextCurveModeChange(mode) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.handleContextCurveModeChange(this, mode);
        }
    }
    
    handleContextCurveMagnitude() {
        // Get the target link - prioritize _curveSubmenuLink (from context menu), then selectedObject
        const targetLink = this._curveSubmenuLink || this.selectedObject;
        
        // Show curve magnitude slider popup next to context menu
        if (targetLink && (targetLink.type === 'link' || targetLink.type === 'unbound')) {
            this.showCurveMagnitudePopup(targetLink);
        }
    }
    
    showCurveMagnitudePopup(link) {
        if (window.LinkPopups) {
            return window.LinkPopups.showCurveMagnitudePopup(this, link);
        }
    }
    
    hideCurveMagnitudePopup() {
        if (window.LinkPopups) {
            return window.LinkPopups.hideCurveMagnitudePopup(this);
        }
        const popup = document.getElementById('curve-magnitude-popup');
        if (popup) popup.remove();
        this._colorEditingLink = null;
        this.draw();
    }
    
    // ========================================
    // LAYER SYSTEM - Like Canva's layering
    // =========================================================================
    // LAYERING SYSTEM - REFINED (Jan 2026)
    // =========================================================================
    // The layering system controls both VISUAL drawing order and HIT DETECTION.
    //
    // VISUAL ORDER (draw()):
    // - Objects are sorted by layer ASCENDING (lower layers drawn first, appear behind)
    // - Within same layer: links < devices < text
    //
    // HIT DETECTION (findObjectAt()):
    // - Objects are sorted by layer DESCENDING (higher layers checked first)
    // - This ensures clicking on overlapping objects selects the top-most one
    //
    // DEFAULT LAYERS (separated by type for intuitive stacking):
    // - Links: 10 (bottom layer)
    // - Devices: 20 (middle layer)
    // - Text: 30 (top layer)
    //
    // Layer increments/decrements are by 1, allowing fine-grained control.
    // Minimum layer is 0 (absolute background).
    //
    // DO NOT change the sorting order without updating BOTH draw() and findObjectAt()!
    // =========================================================================
    
    // Layer constants for default stacking - SINGLE SOURCE OF TRUTH
    // These are used throughout the system for consistency
    getDefaultLayerForType(type) {
        if (type === 'link' || type === 'unbound') return 10;  // Links at bottom
        if (type === 'device') return 20;  // Devices in middle
        if (type === 'text') return 30;    // Text on top
        return 20; // Fallback to device level
    }
    
    getObjectLayer(obj) {
        // Return object's explicit layer if set
        if (obj.layer !== undefined) return obj.layer;
        // Use centralized default layer lookup
        return this.getDefaultLayerForType(obj.type);
    }
    
    moveObjectForward(obj) {
        if (!obj) return;
        const currentLayer = this.getObjectLayer(obj);
        obj.layer = currentLayer + 1;
    }
    
    moveObjectBackward(obj) {
        if (!obj) return;
        const currentLayer = this.getObjectLayer(obj);
        obj.layer = Math.max(0, currentLayer - 1); // Allow going to layer 0
    }
    
    moveObjectToFront(obj) {
        if (!obj) return;
        // Find the maximum layer among all objects (excluding the object being moved)
        const otherObjects = this.objects.filter(o => o !== obj);
        const maxLayer = otherObjects.length > 0 
            ? Math.max(...otherObjects.map(o => this.getObjectLayer(o)))
            : this.getDefaultLayerForType('text'); // Default to text layer (highest default)
        obj.layer = maxLayer + 1;
    }
    
    moveObjectToBack(obj) {
        if (!obj) return;
        // Find the minimum layer among all objects (excluding the object being moved)
        const otherObjects = this.objects.filter(o => o !== obj);
        const minLayer = otherObjects.length > 0
            ? Math.min(...otherObjects.map(o => this.getObjectLayer(o)))
            : this.getDefaultLayerForType('link'); // Default to link layer (lowest default)
        obj.layer = Math.max(0, minLayer - 1); // Go below the lowest, but not below 0
    }
    
    // Get all unique layers currently in use
    getUsedLayers() {
        const layers = new Set();
        this.objects.forEach(obj => layers.add(this.getObjectLayer(obj)));
        return Array.from(layers).sort((a, b) => a - b);
    }
    
    // Move object to a specific layer
    setObjectLayer(obj, layer) {
        if (!obj) return;
        obj.layer = Math.max(0, layer);
    }
    
    // Reset object to its default layer (based on type)
    resetObjectLayer(obj) {
        if (!obj) return;
        delete obj.layer; // Remove explicit layer, will use default
    }
    
    handleContextLayerToFront() {
        // Store selection to preserve it
        const savedSelection = this.selectedObject;
        const savedSelections = [...this.selectedObjects];
        
        if (this.selectedObjects.length > 0) {
            this.saveState();
            // FIXED: Preserve relative layer order when moving multiple objects to front
            // Sort by current layer first, then move all together
            const sorted = [...this.selectedObjects].sort((a, b) => 
                this.getObjectLayer(a) - this.getObjectLayer(b)
            );
            const nonSelected = this.objects.filter(o => !this.selectedObjects.includes(o));
            const maxOtherLayer = nonSelected.length > 0
                ? Math.max(...nonSelected.map(o => this.getObjectLayer(o)))
                : this.getDefaultLayerForType('text');
            
            // Assign layers in sorted order, starting from maxOtherLayer + 1
            sorted.forEach((obj, index) => {
                obj.layer = maxOtherLayer + 1 + index;
            });
            
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Moved ${this.selectedObjects.length} objects to front (preserving order)`);
            }
        } else if (this.selectedObject) {
            this.saveState();
            this.moveObjectToFront(this.selectedObject);
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Moved ${this.selectedObject.id} to front (layer: ${this.getObjectLayer(this.selectedObject)})`);
            }
        }
        
        // Restore selection
        this.selectedObject = savedSelection;
        this.selectedObjects = savedSelections;
        
        this.hideContextMenu();
        this.hideLayersSubmenu();
        this.requestDraw();
    }
    
    handleContextLayerForward() {
        const savedSelection = this.selectedObject;
        const savedSelections = [...this.selectedObjects];
        
        if (this.selectedObjects.length > 0) {
            this.saveState();
            this.selectedObjects.forEach(obj => this.moveObjectForward(obj));
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Moved ${this.selectedObjects.length} objects forward`);
            }
        } else if (this.selectedObject) {
            this.saveState();
            this.moveObjectForward(this.selectedObject);
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Moved ${this.selectedObject.id} forward (layer: ${this.getObjectLayer(this.selectedObject)})`);
            }
        }
        
        this.selectedObject = savedSelection;
        this.selectedObjects = savedSelections;
        
        this.hideContextMenu();
        this.hideLayersSubmenu();
        this.requestDraw();
    }
    
    handleContextLayerBackward() {
        const savedSelection = this.selectedObject;
        const savedSelections = [...this.selectedObjects];
        
        if (this.selectedObjects.length > 0) {
            this.saveState();
            this.selectedObjects.forEach(obj => this.moveObjectBackward(obj));
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Moved ${this.selectedObjects.length} objects backward`);
            }
        } else if (this.selectedObject) {
            this.saveState();
            this.moveObjectBackward(this.selectedObject);
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Moved ${this.selectedObject.id} backward (layer: ${this.getObjectLayer(this.selectedObject)})`);
            }
        }
        
        this.selectedObject = savedSelection;
        this.selectedObjects = savedSelections;
        
        this.hideContextMenu();
        this.hideLayersSubmenu();
        this.requestDraw();
    }
    
    handleContextLayerToBack() {
        const savedSelection = this.selectedObject;
        const savedSelections = [...this.selectedObjects];
        
        if (this.selectedObjects.length > 0) {
            this.saveState();
            // FIXED: Preserve relative layer order when moving multiple objects to back
            // Sort by current layer (highest first), then assign from the bottom
            const sorted = [...this.selectedObjects].sort((a, b) => 
                this.getObjectLayer(b) - this.getObjectLayer(a) // Descending
            );
            const nonSelected = this.objects.filter(o => !this.selectedObjects.includes(o));
            const minOtherLayer = nonSelected.length > 0
                ? Math.min(...nonSelected.map(o => this.getObjectLayer(o)))
                : this.getDefaultLayerForType('link');
            
            // Calculate starting layer (go below the lowest, but leave room for all objects)
            const startLayer = Math.max(0, minOtherLayer - sorted.length);
            
            // Assign layers in reverse sorted order (highest original → highest in new range)
            sorted.forEach((obj, index) => {
                obj.layer = startLayer + (sorted.length - 1 - index);
            });
            
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Moved ${this.selectedObjects.length} objects to back (preserving order)`);
            }
        } else if (this.selectedObject) {
            this.saveState();
            this.moveObjectToBack(this.selectedObject);
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Moved ${this.selectedObject.id} to back (layer: ${this.getObjectLayer(this.selectedObject)})`);
            }
        }
        
        this.selectedObject = savedSelection;
        this.selectedObjects = savedSelections;
        
        this.hideContextMenu();
        this.hideLayersSubmenu();
        this.requestDraw();
    }
    
    handleContextLayerReset() {
        const savedSelection = this.selectedObject;
        const savedSelections = [...this.selectedObjects];
        
        if (this.selectedObjects.length > 0) {
            this.saveState();
            this.selectedObjects.forEach(obj => this.resetObjectLayer(obj));
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Reset ${this.selectedObjects.length} objects to default layers`);
            }
        } else if (this.selectedObject) {
            this.saveState();
            this.resetObjectLayer(this.selectedObject);
            if (this.debugger) {
                this.debugger.logSuccess(`📚 Reset ${this.selectedObject.id} to default layer (${this.getObjectLayer(this.selectedObject)})`);
            }
        }
        
        this.selectedObject = savedSelection;
        this.selectedObjects = savedSelections;
        
        this.hideContextMenu();
        this.hideLayersSubmenu();
        this.requestDraw();
    }
    
    // ==================== OBJECT GROUPING ====================
    // Delegated to GroupManager module (topology-groups.js)
    // These methods are kept for backward compatibility
    
    generateGroupId() {
        return this.groups ? this.groups.generateId() : 'group_' + Date.now();
    }
    
    findGroupLeader(objects) {
        return this.groups ? this.groups.findLeader(objects) : (objects?.[0] || null);
    }
    
    groupSelectedObjects() {
        if (this.groups) this.groups.groupSelected();
    }
    
    ungroupSelectedObjects() {
        if (this.groups) this.groups.ungroupSelected();
    }
    
    getGroupMembers(obj) {
        return this.groups ? this.groups.getMembers(obj) : [obj];
    }
    
    isObjectGrouped(obj) {
        return this.groups ? this.groups.isGrouped(obj) : false;
    }
    
    validateGroups() {
        if (this.groups) this.groups.validate();
    }
    
    expandSelectionToGroup(obj = null) {
        return this.groups ? this.groups.expandSelection(obj) : false;
    }
    
    setupGroupDrag(pos) {
        return this.groups ? this.groups.setupDrag(pos) : false;
    }
    
    // ==================== END OBJECT GROUPING ====================
    
    showLayersSubmenu() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.showLayersSubmenu(this);
        }
    }
    
    hideLayersSubmenu() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.hideLayersSubmenu(this);
        }
    }
    
    hideLayersSubmenuIfNotHovered() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.hideLayersSubmenuIfNotHovered(this);
        }
    }
    
    // ==================== DEVICE STYLE SUBMENU ====================
    
    showDeviceStyleSubmenu() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.showDeviceStyleSubmenu(this);
        }
    }
    
    hideDeviceStyleSubmenu() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.hideDeviceStyleSubmenu(this);
        }
    }
    
    hideDeviceStyleSubmenuIfNotHovered() {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.hideDeviceStyleSubmenuIfNotHovered(this);
        }
    }
    
    setDeviceVisualStyle(style) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.setDeviceVisualStyle(this, style);
        }
    }
    
    // Select a device style and enter router placement mode
    selectStyleAndEnterPlacementMode(style) {
        if (window.ContextMenuHandlers) {
            return window.ContextMenuHandlers.selectStyleAndEnterPlacementMode(this, style);
        }
    }
    
    // ==================== END DEVICE STYLE SUBMENU ====================
    
    handleContextLabel() {
        // Show inline rename editor for device
        if (this.selectedObject && this.selectedObject.type === 'device') {
            this.hideContextMenu();
            this.showInlineDeviceRename(this.selectedObject);
        } else {
            this.hideContextMenu();
        }
    }
    
    showRenamePopup(device) {
        // Delegate to external module (implementation moved to topology-rename-popup.js)
        if (window.showRenamePopup) {
            window.showRenamePopup(this, device);
        }
    }
    
    applyRename(device, newLabel, fontSettings = null) {
        // Delegate to external module
        if (window.applyRename) {
            window.applyRename(this, device, newLabel, fontSettings);
        }
    }
    
    hideRenamePopup() {
        // Delegate to external module
        if (window.hideRenamePopup) {
            window.hideRenamePopup();
        }
    }
    
    handleContextLock() {
        console.log('handleContextLock called');
        // Lock all selected objects
        if (this.selectedObjects.length > 0) {
            this.saveState();
            this.selectedObjects.forEach(obj => {
                if (obj.type === 'device' || obj.type === 'text') {
                    obj.locked = true;
                }
            });
            this.requestDraw();
        } else if (this.selectedObject && (this.selectedObject.type === 'device' || this.selectedObject.type === 'text')) {
            this.saveState();
            this.selectedObject.locked = true;
            this.requestDraw();
        }
        this.hideContextMenu();
    }
    
    handleContextUnlock() {
        // Unlock all selected objects
        if (this.selectedObjects.length > 0) {
            this.saveState();
            this.selectedObjects.forEach(obj => {
                if (obj.type === 'device' || obj.type === 'text') {
                    obj.locked = false;
                }
            });
            this.requestDraw();
        } else if (this.selectedObject && (this.selectedObject.type === 'device' || this.selectedObject.type === 'text')) {
            this.saveState();
            this.selectedObject.locked = false;
            this.requestDraw();
        }
        this.hideContextMenu();
    }
    
    handleContextSSHAddress() {
        this.hideContextMenu();
        
        // Get the device to set SSH address for
        const device = this.selectedObject;
        if (!device || device.type !== 'device') {
            if (this.debugger) {
                this.debugger.logWarning('No device selected for SSH address');
            }
            return;
        }
        
        // Show custom modal dialog for SSH address input
        this.showSSHAddressDialog(device);
    }
    
    /**
     * Handle context menu Enable LLDP click - shows menu with options
     */
    handleContextEnableLldp() {
        this.hideContextMenu();
        
        const device = this.selectedObject;
        if (!device || device.type !== 'device') {
            return;
        }
        
        // Get SSH address/serial for the device
        const serial = device.sshConfig?.host || device.deviceSerial || device.label || '';
        if (!serial) {
            this.showToast('No SSH address configured. Set SSH Address first.', 'error');
            return;
        }
        
        // Show LLDP menu near context menu position
        this.showLldpButtonMenu(device, this._contextMenuX || 200, this._contextMenuY || 200);
    }
    
    /**
     * Start topology discovery from the selected device (context menu action).
     * Only works for termination devices (PE/CE), not DNAAS routers.
     */
    handleContextStartDiscovery() {
        this.hideContextMenu();
        
        const device = this.selectedObject;
        if (!device || device.type !== 'device') {
            if (this.debugger) {
                this.debugger.logWarning('No device selected for discovery');
            }
            return;
        }
        
        // Check if this is a termination device
        if (!this.isTerminationDevice(device)) {
            this.showToast('Topology Discovery can only be started from Termination devices (PE/CE), not from DNAAS routers', 'error');
            return;
        }
        
        // Get the SSH address/serial to use for discovery
        const addr = device.sshConfig?.host || device.sshConfig?.hostBackup || device.deviceSerial || '';
        
        if (!addr) {
            this.showToast('No SSH address or serial configured for this device. Set SSH Address first.', 'error');
            return;
        }
        
        // Open the DNAAS panel and start discovery
        const dnaasPanel = document.getElementById('dnaas-panel');
        const serialInput = document.getElementById('dnaas-serial-input');
        
        if (dnaasPanel) {
            dnaasPanel.style.display = 'block';
            // Position panel in a visible location
            dnaasPanel.style.left = '50%';
            dnaasPanel.style.top = '50%';
            dnaasPanel.style.transform = 'translate(-50%, -50%)';
        }
        
        if (serialInput) {
            serialInput.value = addr;
        }
        
        // Start the discovery
        this.startDnaasDiscovery(addr);
        
        if (this.debugger) {
            this.debugger.logInfo(`Starting topology discovery from device: ${device.label || device.id} (${addr})`);
        }
    }
    
    showSSHAddressDialog(device) {
        // Delegate to external module (implementation moved to topology-ssh-dialog.js)
        if (window.showSSHAddressDialog) {
            window.showSSHAddressDialog(this, device);
        }
    }
    
    /**
     * Show LLDP button menu with options: Enable LLDP, LLDP Table
     * Delegated to topology-lldp-dialog.js
     */
    showLldpButtonMenu(device, x, y) {
        if (window.LldpDialog && window.LldpDialog.showLldpButtonMenu) {
            window.LldpDialog.showLldpButtonMenu(this, device, x, y);
        }
    }
    
    /**
     * Show LLDP neighbors table dialog - fetches from scaler-monitor cache
     * Delegated to topology-lldp-dialog.js
     */
    showLldpTableDialog(device, serial, options) {
        if (window.LldpDialog) {
            return window.LldpDialog.showLldpTableDialog(this, device, serial, options);
        }
    }
    
    showSystemStackDialog(device, serial) {
        if (window.StackDialog) {
            return window.StackDialog.showSystemStackDialog(this, device, serial);
        }
    }
    
    /**
     * Enable LLDP on device in background with visual feedback
     * Delegated to topology-dnaas-helpers.js
     */
    async enableLldpBackground(device, serial, sshConfig = {}) {
        if (window.DnaasHelpers && window.DnaasHelpers.enableLldpBackground) {
            return window.DnaasHelpers.enableLldpBackground(this, device, serial, sshConfig);
        }
    }
    
    // LLDP helper method delegations to topology-dnaas-helpers.js
    _startLldpAnimation(device, hasLinks) {
        if (window.DnaasHelpers && window.DnaasHelpers._startLldpAnimation) {
            return window.DnaasHelpers._startLldpAnimation(this, device, hasLinks);
        }
    }
    
    _startLldpAnimationTimer() {
        if (window.DnaasHelpers && window.DnaasHelpers._startLldpAnimationTimer) {
            return window.DnaasHelpers._startLldpAnimationTimer(this);
        }
    }
    
    _stopLldpAnimation(device) {
        if (window.DnaasHelpers && window.DnaasHelpers._stopLldpAnimation) {
            return window.DnaasHelpers._stopLldpAnimation(this, device);
        }
    }
    
    _clearDeviceLldpStatus(device) {
        if (window.DnaasHelpers && window.DnaasHelpers._clearDeviceLldpStatus) {
            return window.DnaasHelpers._clearDeviceLldpStatus(this, device);
        }
    }
    
    _removeSimpleLldpAnimation(device) {
        if (window.DnaasHelpers && window.DnaasHelpers._removeSimpleLldpAnimation) {
            return window.DnaasHelpers._removeSimpleLldpAnimation(this, device);
        }
    }
    
    _showLldpSuccessGlow(device) {
        if (window.DnaasHelpers && window.DnaasHelpers._showLldpSuccessGlow) {
            return window.DnaasHelpers._showLldpSuccessGlow(this, device);
        }
    }
    
    _showLldpFailureGlow(device) {
        if (window.DnaasHelpers && window.DnaasHelpers._showLldpFailureGlow) {
            return window.DnaasHelpers._showLldpFailureGlow(this, device);
        }
    }
    
    async _enableLldpOnDevice(serial, sshConfig = {}) {
        if (window.DnaasHelpers && window.DnaasHelpers._enableLldpOnDevice) {
            // Note: This function doesn't need editor as first param
            return window.DnaasHelpers._enableLldpOnDevice(serial, sshConfig);
        }
    }
    
    async _showNoLldpDialog(serial, outputDiv, progressSection) {
        if (window.DnaasHelpers && window.DnaasHelpers._showNoLldpDialog) {
            // Note: This function doesn't need editor as first param
            return window.DnaasHelpers._showNoLldpDialog(serial, outputDiv, progressSection);
        }
    }
    
    _drawLldpEffects(device) {
        if (window.DnaasHelpers && window.DnaasHelpers._drawLldpEffects) {
            return window.DnaasHelpers._drawLldpEffects(this, device);
        }
    }
    
    _drawCanvasWaveDots(device, phase) {
        if (window.DnaasHelpers && window.DnaasHelpers._drawCanvasWaveDots) {
            return window.DnaasHelpers._drawCanvasWaveDots(this, device, phase);
        }
    }
    
    _drawPulsingGlow(device, phase) {
        if (window.DnaasHelpers && window.DnaasHelpers._drawPulsingGlow) {
            return window.DnaasHelpers._drawPulsingGlow(this, device, phase);
        }
    }
    
    handleContextDetachFromLink() {
        // Detach text box from its attached link
        if (this.selectedObject && this.selectedObject.type === 'text' && this.selectedObject.linkId) {
            this.saveState();
            
            const linkId = this.selectedObject.linkId;
            const position = this.selectedObject.position;
            
            // Clear the link attachment properties
            delete this.selectedObject.linkId;
            delete this.selectedObject.position;
            delete this.selectedObject.linkAttachT; // Clear parametric position
            
            if (this.debugger) {
                this.debugger.logSuccess(`🔗 Text detached from link ${linkId} (was at position: ${position || 'middle'})`);
            }
            
            this.draw();
        }
        this.hideContextMenu();
    }
    
    handleContextDetachFromDevice() {
        // Detach link from device(s)
        const link = this._detachLink || this.selectedObject;
        if (link && (link.type === 'link' || link.type === 'unbound')) {
            this.saveState();
            
            const device1 = link.device1 ? this.objects.find(d => d.id === link.device1) : null;
            const device2 = link.device2 ? this.objects.find(d => d.id === link.device2) : null;
            
            // Detach from device1 if attached
            if (link.device1) {
                const dev1 = this.objects.find(d => d.id === link.device1);
                if (this.debugger && dev1) {
                    this.debugger.logSuccess(`🔗 Detached link from ${dev1.label || 'Device'} (start)`);
                }
                link.device1 = null;
                delete link.device1Angle;
            }
            
            // Detach from device2 if attached
            if (link.device2) {
                const dev2 = this.objects.find(d => d.id === link.device2);
                if (this.debugger && dev2) {
                    this.debugger.logSuccess(`🔗 Detached link from ${dev2.label || 'Device'} (end)`);
                }
                link.device2 = null;
                delete link.device2Angle;
            }
            
            // Recalculate link index since attachments changed
            if (link.linkIndex !== undefined) {
                delete link.linkIndex;
            }
            
            this.draw();
        }
        this.hideContextMenu();
    }
    
    handleContextToggleLock() {
        // Legacy toggle function - determine action and call appropriate handler
        if (this.selectedObjects.length > 0) {
            const allLocked = this.selectedObjects.filter(obj => obj.type === 'device' || obj.type === 'text').every(obj => obj.locked);
            if (allLocked) {
                this.handleContextUnlock();
            } else {
                this.handleContextLock();
            }
        } else if (this.selectedObject && (this.selectedObject.type === 'device' || this.selectedObject.type === 'text')) {
            if (this.selectedObject.locked) {
                this.handleContextUnlock();
            } else {
                this.handleContextLock();
            }
        }
    }
    
    handleContextDelete() {
        this.deleteSelected();
        this.hideContextMenu();
    }
    
    // ========================================
    // TEXT-TO-LINK ATTACHMENT SYSTEM
    // ========================================
    
    // Find the nearest link to a point (for text-to-link snapping)
    // ENHANCED: Properly handles curved links and multiple links between same devices
    findNearestLinkToPoint(x, y, maxDistance = 50) {
        if (window.TextAttachment) {
            return window.TextAttachment.findNearestLinkToPoint(this, x, y, maxDistance = 50);
        }
    }
    
    // Get closest point on a curved link by sampling along the bezier curve
    // CRITICAL FIX (Dec 2025): Use actual magnetic field deflection control points, not simplified perpendicular offset
    getClosestPointOnCurvedLink(px, py, link, linkStart, linkEnd) {
        if (window.TextAttachment) {
            return window.TextAttachment.getClosestPointOnCurvedLink(this, px, py, link, linkStart, linkEnd);
        }
    }
    
    // Get the closest point on a line segment from a point
    getClosestPointOnLineSegment(px, py, x1, y1, x2, y2) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const lengthSquared = dx * dx + dy * dy;
        
        if (lengthSquared === 0) {
            // Line segment is a point
            return {
                point: { x: x1, y: y1 },
                t: 0,
                distance: Math.sqrt((px - x1) * (px - x1) + (py - y1) * (py - y1))
            };
        }
        
        // Calculate parametric position
        let t = ((px - x1) * dx + (py - y1) * dy) / lengthSquared;
        t = Math.max(0, Math.min(1, t)); // Clamp to [0, 1]
        
        // Get closest point
        const closestX = x1 + t * dx;
        const closestY = y1 + t * dy;
        
        // Calculate distance
        const distance = Math.sqrt((px - closestX) * (px - closestX) + (py - closestY) * (py - closestY));
        
        return {
            point: { x: closestX, y: closestY },
            t: t,
            distance: distance
        };
    }
    
    // Convert parametric position (t) to attachment position name
    // UPDATED (Jan 2026): Only 'middle' zone (0.4-0.6) snaps to center
    // Other positions use exact t value stored in linkAttachT
    getAttachmentPositionFromT(t) {
        // Middle zone: snap to center (t=0.5)
        if (t >= 0.4 && t <= 0.6) return 'middle';
        // All other positions: use 'custom' to indicate exact t value should be used
        return 'custom';
    }
    
    // Attach text to a link at the specified position
    attachTextToLink(textObj, link, t) {
        // Prevent attaching to an occupied location
        const occupied = this.objects.some(obj =>
            obj.type === 'text' && obj.id !== textObj.id && obj.linkId === link.id
            && Math.abs((obj.linkAttachT !== undefined ? obj.linkAttachT : 0.5) - t) < 0.08
        );
        if (occupied) {
            if (this.showNotification) this.showNotification('This link location already has a text box attached', 'warning', 3000);
            return;
        }

        if (!this._attachingFromDrop) {
            this.saveState();
        }

        textObj.linkId = link.id;
        textObj.linkAttachT = t;
        
        // Determine position name based on t
        textObj.position = this.getAttachmentPositionFromT(t);
        
        // Mark as just attached so updateAdjacentTextPosition knows to
        // position the TB at the curve point (if link has manual curve)
        textObj._justAttached = true;
        
        // Update text position using the existing function (handles all position logic)
        this.updateAdjacentTextPosition(textObj);
        
        if (this.debugger) {
            this.debugger.logSuccess(`📎 Text "${textObj.text}" attached to ${link.id} at ${textObj.position} (t=${t.toFixed(2)})`);
        }
        
        this.draw();
    }
    
    // Check if a text box overlaps with a link (for snap detection during drag)
    checkTextLinkOverlap(textObj) {
        // Get text bounding box
        this.ctx.save();
        this.ctx.font = `${textObj.fontSize}px Arial`;
        const metrics = this.ctx.measureText(textObj.text || 'Text');
        const w = metrics.width;
        const h = parseInt(textObj.fontSize);
        this.ctx.restore();
        
        const padding = 8;
        const textBounds = {
            left: textObj.x - w/2 - padding,
            right: textObj.x + w/2 + padding,
            top: textObj.y - h/2 - padding,
            bottom: textObj.y + h/2 + padding
        };
        
        // Find nearest link considering text center
        const nearest = this.findNearestLinkToPoint(textObj.x, textObj.y, 60);
        
        if (nearest && nearest.distance < 40) {
            // Check if text bounding box actually overlaps with link
            return nearest;
        }
        
        return null;
    }
    
    showShortcuts() {
        const modal = document.getElementById('shortcuts-modal');
        modal.classList.add('show');
    }
    
    hideShortcuts() {
        console.log('hideShortcuts() called');
        const modal = document.getElementById('shortcuts-modal');
        if (!modal) {
            console.error('Shortcuts modal element not found!');
            return;
        }
        console.log('Modal found, removing show class');
        modal.classList.remove('show');
        // Return to home/base state
        this.setMode('base');
        this.draw();
        console.log('Shortcuts modal closed successfully');
    }
    
    addDevice(type) {
        const centerX = (this.canvasW / 2) / this.zoom - this.panOffset.x;
        const centerY = (this.canvasH / 2) / this.zoom - this.panOffset.y;
        
        const label = this.getNextDeviceLabel(type);
        
        // Validate device name uniqueness
        if (!this.isDeviceNameUnique(label)) {
            alert(`Device name "${label}" already exists. Please choose a different name.`);
            return;
        }
        
        this.saveState(); // Save before adding
        
        const colorPickerVal = document.getElementById('color-picker');
        const device = {
            id: `device_${this.deviceIdCounter++}`,
            type: 'device',
            deviceType: type,
            x: centerX,
            y: centerY,
            radius: 30,
            rotation: 0,
            color: colorPickerVal ? colorPickerVal.value : '#4CAF50',
            label: label,
            locked: false,
            visualStyle: this.defaultDeviceStyle || 'circle'
        };
        
        this.objects.push(device);
        this.selectedObject = device;
        this.selectedObjects = [device];
        this.setTool('select');
        this.updatePropertiesPanel();
        this.draw();
    }
    
    createLink(device1, device2) {
        this.saveState(); // Save before creating link
        
        // REVERTED: Create regular links for device-to-device connections
        // This ensures the multiple-link offset logic works correctly
        
        // Calculate device edge positions for initial TP placement (shape-aware)
        const angle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
        const startPt = this.getLinkConnectionPoint(device1, angle);
        const endPt = this.getLinkConnectionPoint(device2, angle + Math.PI);
        const startX = startPt.x;
        const startY = startPt.y;
        const endX = endPt.x;
        const endY = endPt.y;
        
        const link = {
            id: `link_${this.linkIdCounter++}`,
            type: 'link',  // Reverted to 'link' type for proper offset logic
            originType: 'QL', // PRESERVE: Original link type (QL = Quick Link)
            createdAt: Date.now(), // Creation timestamp for BUL order tracking
            device1: device1.id,
            device2: device2.id,
            color: this.defaultLinkColor || (this.darkMode ? '#ffffff' : '#666666'),
            start: { x: startX, y: startY },
            end: { x: endX, y: endY },
            connectedStart: null,
            connectedEnd: null,
            style: this.linkStyle || 'solid'  // Store the style when link is created
        };
        
        this.objects.push(link);
        
        // Calculate and assign linkIndex based on existing links between these devices
        // (Note: drawLink now calculates this dynamically, but we store it for reference)
        link.linkIndex = this.calculateLinkIndex(link);
        
        if (this.debugger) {
            const d1Label = device1.label || 'Device';
            const d2Label = device2.label || 'Device';
            this.debugger.logSuccess(`Link created: ${d1Label} → ${d2Label}`);
        }
        
        this.draw();
    }
    
    createUnboundLink() {
        this.saveState(); // Save before creating
        const centerX = (this.canvasW / 2) / this.zoom - this.panOffset.x;
        const centerY = (this.canvasH / 2) / this.zoom - this.panOffset.y;
        
        // Smart placement: find a Y offset that avoids overlapping existing links.
        // Check candidate positions and pick the first one that doesn't collide
        // with any existing link body within a proximity threshold.
        const halfLen = 50;
        const spacing = 40;
        const proximityThreshold = 15 / this.zoom;
        let bestY = centerY;
        
        for (let attempt = 0; attempt < 10; attempt++) {
            const candidateY = centerY + attempt * spacing;
            const midX = centerX;
            let collision = false;
            
            for (const obj of this.objects) {
                if (obj.type !== 'link' && obj.type !== 'unbound') continue;
                const dist = this._checkLinkHit(midX, candidateY, obj);
                if (dist >= 0 && dist < proximityThreshold) {
                    collision = true;
                    break;
                }
            }
            
            if (!collision) {
                bestY = candidateY;
                break;
            }
            bestY = candidateY; // fallback to last tried position
        }
        
        const link = {
            id: `link_${this.linkIdCounter++}`,
            type: 'unbound',
            originType: 'UL', // PRESERVE: Original link type (UL = Unbound Link)
            createdAt: Date.now(), // Creation timestamp for BUL order tracking
            _createdAt: Date.now(), // Selection priority: stronger stickiness for 2s after creation
            device1: null,
            device2: null,
            color: this.defaultLinkColor || (this.darkMode ? '#ffffff' : '#666666'),
            start: { x: centerX - halfLen, y: bestY },
            end: { x: centerX + halfLen, y: bestY },
            connectedStart: null,  // UL ID connected to start endpoint
            connectedEnd: null,     // UL ID connected to end endpoint
            style: this.linkStyle || 'solid'  // Store the style when link is created
        };
        
        this.objects.push(link);
        this.selectedObject = link;
        this.selectedObjects = [link];
        this.unboundLink = link;
        this.draw();
    }
    
    findUnboundLinkEndpoint(x, y) {
        // ENHANCED: Improved hitbox with better zoom handling and priority system
        // TPs have higher priority than MPs, and larger hitboxes for easier grabbing
        
        // First pass: Check FREE ENDPOINTS (TPs) - highest priority
        for (let i = this.objects.length - 1; i >= 0; i--) {
            const obj = this.objects[i];
            if (obj.type === 'unbound') {
                // Use unified isEndpointConnected to check if endpoints are TPs
                const startIsTP = !this.isEndpointConnected(obj, 'start') && 
                                 !(obj.device1 !== null && obj.device1 !== undefined);
                const endIsTP = !this.isEndpointConnected(obj, 'end') && 
                               !(obj.device2 !== null && obj.device2 !== undefined);
                
                // Hitbox for TPs: pixel-accurate triangle for arrow tips, tight circle for regular TPs
                const linkStyle = obj.style || 'solid';
                const isArrowStyle = linkStyle.includes('arrow');
                const linkWidth = obj.width || 2;
                
                // Regular TPs: match visual circle (radius ~4-5) tightly
                const circleHitRadius = 5 / this.zoom;
                
                // Get TP positions
                let startPosX, startPosY, endPosX, endPosY;
                
                if (startIsTP) {
                    startPosX = obj.start.x;
                    startPosY = obj.start.y;
                } else {
                    startPosX = obj._arrowTipStart ? obj._arrowTipStart.x : obj.start.x;
                    startPosY = obj._arrowTipStart ? obj._arrowTipStart.y : obj.start.y;
                }
                
                if (endIsTP) {
                    endPosX = obj.end.x;
                    endPosY = obj.end.y;
                } else {
                    endPosX = obj._arrowTipEnd ? obj._arrowTipEnd.x : obj.end.x;
                    endPosY = obj._arrowTipEnd ? obj._arrowTipEnd.y : obj.end.y;
                }
                
                // Arrow triangle collision data
                const hasTriangleData = isArrowStyle && window.MathUtils && window.MathUtils.isPointInTriangle;
                const arrowLength = obj._arrowLength || (10 + linkWidth * 3);
                const arrowAngleSpread = obj._arrowAngleSpread || (Math.PI / 5);
                
                if (startIsTP) {
                    let hit = false;
                    // Only use triangle collision if an arrow is actually drawn at start
                    if (obj._arrowAtStart && hasTriangleData && obj._arrowStartAngle !== undefined) {
                        const angle = obj._arrowStartAngle;
                        const leftX = startPosX + arrowLength * Math.cos(angle - arrowAngleSpread);
                        const leftY = startPosY + arrowLength * Math.sin(angle - arrowAngleSpread);
                        const rightX = startPosX + arrowLength * Math.cos(angle + arrowAngleSpread);
                        const rightY = startPosY + arrowLength * Math.sin(angle + arrowAngleSpread);
                        hit = window.MathUtils.isPointInTriangle(x, y, startPosX, startPosY, leftX, leftY, rightX, rightY);
                    }
                    // Non-arrow TP or no triangle data: tight circular hitbox
                    if (!hit) {
                        const distStart = Math.hypot(x - startPosX, y - startPosY);
                        hit = distStart < circleHitRadius;
                    }
                    if (hit) {
                        return { link: obj, endpoint: 'start', isConnectionPoint: false };
                    }
                }
                
                if (endIsTP) {
                    let hit = false;
                    // Only use triangle collision if an arrow is actually drawn at end
                    if (obj._arrowAtEnd && hasTriangleData && obj._arrowEndAngle !== undefined) {
                        const angle = obj._arrowEndAngle;
                        const leftX = endPosX - arrowLength * Math.cos(angle - arrowAngleSpread);
                        const leftY = endPosY - arrowLength * Math.sin(angle - arrowAngleSpread);
                        const rightX = endPosX - arrowLength * Math.cos(angle + arrowAngleSpread);
                        const rightY = endPosY - arrowLength * Math.sin(angle + arrowAngleSpread);
                        hit = window.MathUtils.isPointInTriangle(x, y, endPosX, endPosY, leftX, leftY, rightX, rightY);
                    }
                    // Non-arrow TP or no triangle data: tight circular hitbox
                    if (!hit) {
                        const distEnd = Math.hypot(x - endPosX, y - endPosY);
                        hit = distEnd < circleHitRadius;
                    }
                    if (hit) {
                        return { link: obj, endpoint: 'end', isConnectionPoint: false };
                    }
                }
            }
        }
        
        // Second pass: Check connection points (MPs) - lower priority
        // Only check if no TP was found above
        for (let i = this.objects.length - 1; i >= 0; i--) {
            const obj = this.objects[i];
            if (obj.type === 'unbound') {
                const mpHitRadius = 6 / this.zoom;
                
                // Get all links in the merge chain
                const allMergedLinks = this.getAllMergedLinks(obj);
                
                // Check all connection points in the chain
                for (const chainLink of allMergedLinks) {
                    // Check if this link is the parent in a merge (has mergedWith)
                    if (chainLink.mergedWith && chainLink.mergedWith.connectionPoint) {
                        const connPoint = chainLink.mergedWith.connectionPoint;
                        const distConn = Math.hypot(x - connPoint.x, y - connPoint.y);
                        if (distConn < mpHitRadius) {
                            // Return the connected endpoint as a Moving Point
                            const connectedEndpoint = chainLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                            return { link: chainLink, endpoint: connectedEndpoint, isConnectionPoint: true };
                        }
                    }
                    
                    // Check if this link is the child in a merge (has mergedInto)
                    if (chainLink.mergedInto && chainLink.mergedInto.connectionPoint) {
                        const connPoint = chainLink.mergedInto.connectionPoint;
                        const distConn = Math.hypot(x - connPoint.x, y - connPoint.y);
                        if (distConn < mpHitRadius) {
                            // Return the connected endpoint as a Moving Point
                            const parentLink = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                            if (parentLink && parentLink.mergedWith) {
                                const connectedEndpoint = parentLink.mergedWith.childConnectionEndpoint ||
                                    (parentLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                                return { link: chainLink, endpoint: connectedEndpoint, isConnectionPoint: true };
                            }
                        }
                    }
                }
            }
        }
        
        return null;
    }
    
    createText(x, y) {
        // Use default text color if set, otherwise fall back to mode-appropriate color
        const defaultTextColorEl = document.getElementById('default-text-color');
        const defaultBgColorEl = document.getElementById('default-text-bg-color');
        const defaultBgEnabledEl = document.getElementById('default-text-bg-enabled');
        
        // MODE-AWARE TEXT COLOR: White for dark mode, Black for light mode
        let textColor = this.darkMode ? '#ffffff' : '#000000';
        if (defaultTextColorEl && defaultTextColorEl.value) {
            const storedColor = defaultTextColorEl.value.toLowerCase();
            // Bypass old green default - use mode-appropriate default instead
            if (storedColor !== '#2ecc71') {
                textColor = defaultTextColorEl.value;
            }
        }
        
        // Get background color from UI or defaults
        const bgColorValue = defaultBgColorEl ? defaultBgColorEl.value : (this.darkMode ? '#1a1a1a' : '#f5f5f5');
        
        const text = {
            id: `text_${this.textIdCounter++}`,
            type: 'text',
            x: x,
            y: y,
            text: 'Text',
            // APPLY DEFAULT FONT SIZE from settings
            fontSize: this.defaultFontSize || 14,
            // APPLY SELECTED FONT FAMILY
            fontFamily: this.defaultFontFamily || 'Inter, sans-serif',
            // Default to white text with black stroke for visibility on any background
            color: textColor,
            rotation: 0,
            // Background settings
            backgroundColor: bgColorValue,
            bgColor: bgColorValue, // Also set bgColor for consistency
            showBackground: defaultBgEnabledEl ? defaultBgEnabledEl.checked : true,
            backgroundOpacity: this.defaultBgOpacity !== undefined ? this.defaultBgOpacity : 1, // 0-1 scale
            // Apply border settings from defaults
            showBorder: this.defaultBorderEnabled || false,
            borderColor: this.defaultBorderColor || '#0066FA',
            borderStyle: this.defaultBorderStyle || 'solid',
            borderWidth: this.defaultBorderWidth || 4,
            // Black stroke outline for readability on any background
            strokeColor: '#000000',
            strokeWidth: 2
        };
        
        return text;
    }
    
    drawLink(link) {
        if (window.LinkDrawing) {
            return window.LinkDrawing.drawLink(this, link);
        }
    }
    
    drawUnboundLink(link) {
        if (window.LinkDrawing) {
            return window.LinkDrawing.drawUnboundLink(this, link);
        }
    }
    
    drawLinkArrows(link) {
        if (window.LinkDrawing) {
            return window.LinkDrawing.drawLinkArrows(this, link);
        }
    }
    
    drawLinkPreview(startDevice, endPos) {
        if (!startDevice || !endPos) {
            console.warn('[drawLinkPreview] Missing startDevice or endPos');
            return;
        }
        
        this.ctx.save();
        this.ctx.translate(this.panOffset.x, this.panOffset.y);
        this.ctx.scale(this.zoom, this.zoom);
        
        // Use bright visible color for preview
        this.ctx.strokeStyle = '#00ff00'; // Bright green for visibility
        this.ctx.lineWidth = 4; // Thicker line
        this.ctx.setLineDash([10, 5]); // Longer dashes for better visibility
        
        const angle1 = Math.atan2(endPos.y - startDevice.y, endPos.x - startDevice.x);
        const startPt = this.getLinkConnectionPoint(startDevice, angle1);
        
        if (!startPt) {
            console.warn('[drawLinkPreview] Could not get start point');
            this.ctx.restore();
            return;
        }
        
        this.ctx.beginPath();
        this.ctx.moveTo(startPt.x, startPt.y);
        this.ctx.lineTo(endPos.x, endPos.y);
        this.ctx.stroke();
        
        // Also draw a circle at the cursor position for visibility
        this.ctx.fillStyle = '#00ff00';
        this.ctx.beginPath();
        this.ctx.arc(endPos.x, endPos.y, 8, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.restore();
    }
    
    // Draw preview line from a UL's TP to the mouse position
    drawTPLinkPreview(startPos, endPos) {
        this.ctx.save();
        this.ctx.translate(this.panOffset.x, this.panOffset.y);
        this.ctx.scale(this.zoom, this.zoom);
        
        // Use orange color for TP links (matches theme)
        this.ctx.strokeStyle = '#FF5E1F';
        this.ctx.lineWidth = 3;
        this.ctx.setLineDash([8, 4]);
        
        this.ctx.beginPath();
        this.ctx.moveTo(startPos.x, startPos.y);
        this.ctx.lineTo(endPos.x, endPos.y);
        this.ctx.stroke();
        
        // Draw a small circle at the start point (TP indicator) - Orange theme
        this.ctx.fillStyle = '#FF5E1F';
        this.ctx.beginPath();
        this.ctx.arc(startPos.x, startPos.y, 6, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 1.5;
        this.ctx.stroke();
        
        // Draw a small circle at the cursor position - Orange glow
        this.ctx.fillStyle = 'rgba(255, 94, 31, 0.5)';
        this.ctx.beginPath();
        this.ctx.arc(endPos.x, endPos.y, 8, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.restore();
    }
    
    brightenColor(hex, factor) {
        // Helper function to brighten hex colors for dark mode
        // factor > 1 = brighter, factor < 1 = darker
        
        // Handle shorthand hex (#RGB)
        if (hex.length === 4) {
            hex = '#' + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
        }
        
        // Parse hex to RGB
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        
        // Brighten by factor (clamp to 255)
        const newR = Math.min(255, Math.round(r * factor));
        const newG = Math.min(255, Math.round(g * factor));
        const newB = Math.min(255, Math.round(b * factor));
        
        // Convert back to hex
        const toHex = (val) => {
            const hex = val.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        };
        
        return '#' + toHex(newR) + toHex(newG) + toHex(newB);
    }
    
    // Calculate relative luminance of a color (0 = black, 1 = white)
    getColorLuminance(hex) {
        if (!hex || typeof hex !== 'string') return 0.5;
        
        // Handle shorthand hex (#RGB)
        if (hex.length === 4) {
            hex = '#' + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
        }
        
        // Parse hex to RGB
        const r = parseInt(hex.slice(1, 3), 16) / 255;
        const g = parseInt(hex.slice(3, 5), 16) / 255;
        const b = parseInt(hex.slice(5, 7), 16) / 255;
        
        // Calculate relative luminance (WCAG formula)
        const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        return luminance;
    }
    
    // Check if a color is "light" (better visible on dark backgrounds)
    isLightColor(hex) {
        return this.getColorLuminance(hex) > 0.5;
    }
    
    // Darken a color for light mode visibility
    darkenColor(hex, factor = 0.6) {
        if (!hex || typeof hex !== 'string') return hex;
        
        // Handle shorthand hex (#RGB)
        if (hex.length === 4) {
            hex = '#' + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
        }
        
        // Parse hex to RGB
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        
        // Darken by factor (multiply RGB values)
        const newR = Math.round(r * factor);
        const newG = Math.round(g * factor);
        const newB = Math.round(b * factor);
        
        // Convert back to hex
        const toHex = (val) => {
            const hex = val.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        };
        
        return '#' + toHex(newR) + toHex(newG) + toHex(newB);
    }
    
    // Adjust color for current mode - ONLY black and white swap; all other colors stay unchanged
    adjustColorForMode(hex) {
        if (!hex || typeof hex !== 'string') return hex;
        const n = this._normalizeHex(hex);
        if (!n) return hex;
        const isBlack = n === '#000000';
        const isWhite = n === '#ffffff';
        if (!isBlack && !isWhite) return hex; // Never change non-black/white colors
        return this.darkMode ? '#ffffff' : '#000000';
    }
    _normalizeHex(hex) {
        if (!hex || typeof hex !== 'string') return null;
        hex = hex.trim().toLowerCase();
        if (/^#([0-9a-f]{3})$/.test(hex)) {
            const r = hex[1] + hex[1], g = hex[2] + hex[2], b = hex[3] + hex[3];
            return '#' + r + g + b;
        }
        if (/^#([0-9a-f]{6})$/.test(hex)) return hex;
        return null;
    }
    
    // Track recently used colors (last 4)
    addRecentColor(color) {
        if (!color || typeof color !== 'string') return;
        
        // Remove if already in list
        this.recentColors = this.recentColors.filter(c => c.toLowerCase() !== color.toLowerCase());
        
        // Add to front
        this.recentColors.unshift(color);
        
        // Keep only 4 colors
        if (this.recentColors.length > 4) {
            this.recentColors = this.recentColors.slice(0, 4);
        }
        
        // Save to localStorage
        localStorage.setItem('recentColors', JSON.stringify(this.recentColors));
        
        // Update UI
        this.updateRecentColorsUI();
    }
    
    // Update recent colors display in all editor modals
    updateRecentColorsUI() {
        const containers = [
            'link-recent-colors',
            'device-recent-colors',
            'text-recent-colors'
        ];
        
        containers.forEach(containerId => {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            container.innerHTML = '';
            
            // Show placeholder if no recent colors
            if (this.recentColors.length === 0) {
                const placeholder = document.createElement('span');
                placeholder.style.cssText = 'color: #666; font-size: 10px; font-style: italic;';
                placeholder.textContent = 'Use colors to see history...';
                container.appendChild(placeholder);
                return;
            }
            
            this.recentColors.forEach(color => {
                const swatch = document.createElement('div');
                swatch.className = 'recent-color-swatch';
                swatch.style.cssText = `
                    width: 28px;
                    height: 28px;
                    border-radius: 4px;
                    background: ${color};
                    cursor: pointer;
                    border: 2px solid rgba(255,255,255,0.3);
                    transition: transform 0.1s, border-color 0.1s;
                `;
                swatch.title = `Click to use ${color}`;
                swatch.dataset.color = color;
                
                swatch.addEventListener('mouseenter', () => {
                    swatch.style.transform = 'scale(1.1)';
                    swatch.style.borderColor = 'rgba(255,255,255,0.8)';
                });
                swatch.addEventListener('mouseleave', () => {
                    swatch.style.transform = 'scale(1)';
                    swatch.style.borderColor = 'rgba(255,255,255,0.3)';
                });
                
                swatch.addEventListener('click', () => {
                    // Apply color based on which modal is open
                    // updateLinkEditorProperty and updateDeviceEditorProperty already call addRecentColor
                    if (containerId === 'link-recent-colors' && this.editingLink) {
                        this.updateLinkEditorProperty('color', color);
                        document.getElementById('editor-link-color').value = color;
                    } else if (containerId === 'device-recent-colors' && this.editingDevice) {
                        this.updateDeviceEditorProperty('color', color);
                        document.getElementById('editor-device-color').value = color;
                    } else if (containerId === 'text-recent-colors' && this.editingText) {
                        this.editingText.color = color;
                        document.getElementById('editor-text-color').value = color;
                        this.draw();
                    }
                });
                
                container.appendChild(swatch);
            });
        });
    }
    
    updateSelectedColor(color) {
        if (this.selectedObject) {
            if (this.selectedObject.type === 'text' || this.selectedObject.type === 'device') {
                this.saveState(); // Make color change undoable
                this.selectedObject.color = color;
                this.draw();
            } else if (this.selectedObject.type === 'link' || this.selectedObject.type === 'unbound') {
                this.saveState(); // Make color change undoable
                this.selectedObject.color = color;
                this.draw();
            }
        }
    }
    
    updateTextSize(size) {
        if (this.selectedObject && this.selectedObject.type === 'text') {
            this.selectedObject.fontSize = size;
            // Use requestAnimationFrame for smooth slider updates
            if (!this.sliderUpdatePending) {
                this.sliderUpdatePending = true;
                requestAnimationFrame(() => {
            this.draw();
                    this.sliderUpdatePending = false;
                });
            }
        }
    }
    
    updateRotation(angle) {
        if (this.selectedObject && this.selectedObject.type === 'text') {
            this.selectedObject.rotation = parseInt(angle);
            const rotationVal = document.getElementById('rotation-value');
            if (rotationVal) rotationVal.textContent = angle + '°';
            // Use requestAnimationFrame for smooth slider updates
            if (!this.sliderUpdatePending) {
                this.sliderUpdatePending = true;
                requestAnimationFrame(() => {
            this.draw();
                    this.sliderUpdatePending = false;
                });
            }
        }
    }
    
    updateTextProperties() {
        if (this.selectedObject && this.selectedObject.type === 'text') {
            const fontSizeEl = document.getElementById('font-size');
            const rotationSlider = document.getElementById('rotation-slider');
            const rotationVal = document.getElementById('rotation-value');
            const colorPickerEl = document.getElementById('color-picker');
            
            if (fontSizeEl) fontSizeEl.value = this.selectedObject.fontSize;
            if (rotationSlider) rotationSlider.value = this.selectedObject.rotation;
            
            // ENHANCED: Display +/- format (-180 to +180)
            let degrees = Math.round(this.selectedObject.rotation) % 360;
            if (degrees > 180) degrees -= 360;
            if (degrees < -180) degrees += 360;
            const displayText = degrees >= 0 ? `+${degrees}°` : `${degrees}°`;
            if (rotationVal) rotationVal.textContent = displayText;
            
            if (colorPickerEl) colorPickerEl.value = this.selectedObject.color;
        }
    }
    
    deleteSelected() {
        if (this.selectedObjects.length === 0 && !this.selectedObject) {
            if (this.debugger) {
                this.debugger.logInfo('No objects selected to delete');
            }
            return;
        }
        
        // BUGFIX: Hide text selection toolbar immediately when deleting
        this.hideTextSelectionToolbar();
        
        this.saveState(); // Save state before deletion
        
        const objectsToDelete = this.selectedObjects.length > 0 ? this.selectedObjects : [this.selectedObject];
        
        objectsToDelete.forEach(obj => {
            const index = this.objects.indexOf(obj);
            if (index > -1) {
                this.objects.splice(index, 1);
            }
        });
        
        // Clear selection
        this.selectedObject = null;
        this.selectedObjects = [];
        
        if (this.debugger) {
            this.debugger.logSuccess(`🗑️ Deleted ${objectsToDelete.length} object(s)`);
        }
        
        this.draw();
        this.updatePropertiesPanel();
    }
    
    copySelected() {
        if (this.selectedObjects.length === 0 && !this.selectedObject) {
            if (this.debugger) {
                this.debugger.logInfo('No objects selected to copy');
            }
            return;
        }
        
        const objectsToCopy = this.selectedObjects.length > 0 ? this.selectedObjects : [this.selectedObject];
        
        // Deep copy objects to clipboard
        this.clipboard = JSON.parse(JSON.stringify(objectsToCopy));
        
        // Calculate centroid for smart paste positioning
        let sumX = 0, sumY = 0, count = 0;
        this.clipboard.forEach(obj => {
            if (obj.x !== undefined && obj.y !== undefined) {
                sumX += obj.x;
                sumY += obj.y;
                count++;
            } else if (obj.type === 'unbound') {
                const centerX = (obj.start.x + obj.end.x) / 2;
                const centerY = (obj.start.y + obj.end.y) / 2;
                sumX += centerX;
                sumY += centerY;
                count++;
            }
        });
        
        if (count > 0) {
            this.clipboardCentroid = { x: sumX / count, y: sumY / count };
        }
        
        if (this.debugger) {
            this.debugger.logSuccess(`📋 Copied ${this.clipboard.length} object(s) to clipboard`);
            const types = this.clipboard.map(o => o.type).join(', ');
            this.debugger.logInfo(`   Types: ${types}`);
        }
    }
    
    pasteObjects() {
        if (!this.clipboard || this.clipboard.length === 0) {
            if (this.debugger) {
                this.debugger.logInfo('Clipboard is empty - nothing to paste');
            }
            return;
        }
        
        this.saveState(); // Save state before pasting
        
        // Paste at mouse position or with offset from original position
        const pastePos = this.lastMousePos || this.clipboardCentroid || { x: 0, y: 0 };
        
        // Calculate offset from clipboard centroid to paste position
        let offsetX = pastePos.x - (this.clipboardCentroid?.x || 0);
        let offsetY = pastePos.y - (this.clipboardCentroid?.y || 0);
        
        // ENHANCED: If offset is very small (pasting at same location), add default offset
        // This prevents pasted objects from perfectly overlapping with source
        const offsetMagnitude = Math.sqrt(offsetX * offsetX + offsetY * offsetY);
        if (offsetMagnitude < 20) { // If within 20px of source (essentially same position)
            offsetX += 30; // Offset by 30px right and down
            offsetY += 30;
            if (this.debugger) {
                this.debugger.logInfo('📋 Paste: Adding default offset to prevent overlap');
            }
        }
        
        const pastedObjects = [];
        const idMapping = {}; // Map old IDs to new IDs for link references
        
        this.clipboard.forEach(obj => {
            const newObj = JSON.parse(JSON.stringify(obj)); // Deep copy
            
            // Generate new ID
            const oldId = newObj.id;
            if (newObj.type === 'device') {
                newObj.id = `device_${this.deviceIdCounter++}`;
                // Update device counter for auto-numbering
                if (newObj.deviceType === 'router') {
                    this.deviceCounters.router++;
                    if (this.deviceNumbering) {
                        newObj.label = `R${this.deviceCounters.router}`;
                    }
                } else {
                    this.deviceCounters.switch++;
                    if (this.deviceNumbering) {
                        newObj.label = `S${this.deviceCounters.switch}`;
                    }
                }
            } else if (newObj.type === 'link') {
                newObj.id = `link_${this.linkIdCounter++}`;
            } else if (newObj.type === 'unbound') {
                newObj.id = `unbound_${this.linkIdCounter++}`;
            } else if (newObj.type === 'text') {
                newObj.id = `text_${this.textIdCounter++}`;
            }
            
            idMapping[oldId] = newObj.id;
            
            // Apply offset to position
            if (newObj.x !== undefined && newObj.y !== undefined) {
                newObj.x += offsetX;
                newObj.y += offsetY;
            }
            if (newObj.type === 'unbound') {
                newObj.start.x += offsetX;
                newObj.start.y += offsetY;
                newObj.end.x += offsetX;
                newObj.end.y += offsetY;
            }
            if (newObj.type === 'link') {
                // Skip pasting regular links - they depend on devices
                // We'll handle them separately if their devices are pasted
                return;
            }
            
            // Clear device references for unbound links (they'll be reattached manually)
            if (newObj.type === 'unbound') {
                newObj.device1 = null;
                newObj.device2 = null;
                // Clear merge relationships (can't preserve across paste)
                newObj.mergedWith = null;
                newObj.mergedInto = null;
                newObj.connectedTo = null;
            }
            
            // Update linkId for adjacent text
            if (newObj.type === 'text' && newObj.linkId) {
                newObj.linkId = idMapping[newObj.linkId] || null;
            }
            
            this.objects.push(newObj);
            pastedObjects.push(newObj);
        });
        
        // Select pasted objects
        this.selectedObjects = pastedObjects;
        this.selectedObject = pastedObjects[0] || null;
        
        if (this.debugger) {
            this.debugger.logSuccess(`📋 Pasted ${pastedObjects.length} object(s)`);
            this.debugger.logInfo(`   Position: Offset by (${Math.round(offsetX)}, ${Math.round(offsetY)})`);
        }
        
        this.draw();
        this.updatePropertiesPanel();
    }
    
    deleteSelected() {
        // Check if anything is actually selected
        if ((!this.selectedObject && (!this.selectedObjects || this.selectedObjects.length === 0)) || 
            (this.multiSelectMode && this.selectedObjects.length === 0)) {
            return;
        }
        
        // BUGFIX: Hide ALL selection toolbars immediately when deleting
        this.hideAllSelectionToolbars();
        
        // BUGFIX: Cancel link mode (QUL) if the link source device is being deleted
        if (this.linking && this.linkStart) {
            const deletingIds = this.selectedObjects.length > 0 
                ? new Set(this.selectedObjects.map(obj => obj.id))
                : new Set([this.selectedObject?.id]);
            
            if (deletingIds.has(this.linkStart.id)) {
                this.linking = false;
                this.linkStart = null;
                this.setMode('base');
                if (this.debugger) {
                    this.debugger.logInfo('Link mode cancelled - source device deleted');
                }
            }
        }
        
        // BUGFIX: Cancel "link from TP" mode (QUL) if the source UL is being deleted
        if (this._linkFromTP) {
            // Get IDs of objects being deleted BEFORE they're removed
            const deletingIds = this.selectedObjects.length > 0 
                ? new Set(this.selectedObjects.map(obj => obj.id))
                : (this.selectedObject ? new Set([this.selectedObject.id]) : new Set());
            
            if (deletingIds.has(this._linkFromTP.link.id)) {
                // Abort QUL creation - clear TP link mode
                this._linkFromTP = null;
                this.linking = false;
                this.setMode('base');
                
                if (this.debugger) {
                    this.debugger.logInfo('🔗 Link from TP: Aborted - source UL deleted');
                }
                
                // Continue with deletion - don't return early, just clear the QUL mode
            }
        }
        
        if (this.debugger) {
            const count = this.selectedObjects.length || 1;
            this.debugger.logAction(`Deleting ${count} object(s)`);
        }
        
        this.saveState(); // Save state before deleting
        
        const devicesToEvict = (this.selectedObjects && this.selectedObjects.length > 0
            ? this.selectedObjects
            : this.selectedObject ? [this.selectedObject] : []
        ).filter(o => o && o.type === 'device' && (o.sshConfig?.host || o.sshConfig?.hostBackup));
        devicesToEvict.forEach(d => {
            const ip = d.sshConfig?.host || d.sshConfig?.hostBackup;
            const did = d.label || d.deviceSerial || d.serial || '';
            if (ip && typeof ScalerAPI !== 'undefined' && ScalerAPI.evictSSHPoolConnection) {
                ScalerAPI.evictSSHPoolConnection(ip, did).catch(() => {});
            }
        });

        // Perform bulk delete whenever there are selectedObjects, regardless of multiSelectMode
        if (this.selectedObjects && this.selectedObjects.length > 0) {
            // ENHANCED: Handle UL deletion in BUL chains - reconfigure merge relationships
            const selectedIds = new Set(this.selectedObjects.map(obj => obj.id));
            const deviceIds = new Set(this.selectedObjects.filter(obj => obj.type === 'device').map(obj => obj.id));
            
            // Before deletion, fix merge relationships for ULs being deleted
            this.selectedObjects.forEach(obj => {
                if (obj.type === 'unbound' && (obj.mergedWith || obj.mergedInto)) {
                    this.handleULDeletionInBUL(obj);
                }
            });
            
            // Remove selected objects and their connected links in one operation
            this.objects = this.objects.filter(obj => {
                // Remove if object is selected
                if (selectedIds.has(obj.id)) return false;
                // Remove if link connected to deleted device
                if (obj.type === 'unbound' && (deviceIds.has(obj.device1) || deviceIds.has(obj.device2))) return false;
                // Keep everything else
                return true;
            });
            
            // GROUP CLEANUP: Validate groups after deletion
            if (this.groups) this.groups.validate();
            
            this.selectedObjects = [];
            this.selectedObject = null;
            this.multiSelectMode = false;
            // Recalculate device counters after deletion for proper numbering
            this.updateDeviceCounters();
            this.draw();
        } else if (this.selectedObject) {
            const index = this.objects.indexOf(this.selectedObject);
            if (index > -1) {
                // ENHANCED: Handle UL deletion in BUL chains
                if (this.selectedObject.type === 'unbound' && (this.selectedObject.mergedWith || this.selectedObject.mergedInto)) {
                    this.handleULDeletionInBUL(this.selectedObject);
                }
                
                // Also remove links connected to this device
                if (this.selectedObject.type === 'device') {
                    this.objects = this.objects.filter(obj => 
                        !(obj.type === 'unbound' && (obj.device1 === this.selectedObject.id || obj.device2 === this.selectedObject.id))
                    );
                }
                
                this.objects.splice(index, 1);
                
                // GROUP CLEANUP: Validate groups after single object deletion
                if (this.groups) this.groups.validate();
                
                this.selectedObject = null;
                this.selectedObjects = [];
                // Recalculate device counters after deletion for proper numbering
                this.updateDeviceCounters();
                this.draw();
            }
        }
    }
    
    saveState() {
        if (this.initializing) {
            return;
        }
        
        // DEBOUNCE: Prevent multiple saveState calls within 100ms
        // This fixes the issue where 1 action counts as multiple steps
        const now = Date.now();
        if (this._lastSaveStateTime && (now - this._lastSaveStateTime) < 100) {
            // Skip duplicate saveState call within debounce window
            return;
        }
        this._lastSaveStateTime = now;
        
        // Ensure history arrays exist
        if (!this.history) {
            this.history = [];
            this.historyIndex = -1;
        }
        
        try {
            
            // Create deep copy of current state, stripping transient monitor/display flags
            const objsCopy = JSON.parse(JSON.stringify(this.objects));
            for (const obj of objsCopy) {
                if ((obj.type === 'link' || obj.type === 'unbound') && obj._hidden) {
                    delete obj._hidden;
                }
                delete obj._badgeWorlds;
                delete obj._hostnameMismatch;
                delete obj._mismatchDismissed;
                delete obj._identity;
                delete obj._configHostname;
                delete obj._stackData;
                delete obj._stackCachedAt;
                delete obj._lldpData;
                delete obj._lldpCompletedAt;
                delete obj._gitCommit;
                delete obj._gitCommitFetchedAt;
                delete obj._gitCommitFailed;
                delete obj._renaming;
                delete obj._activeConfigJob;
                delete obj._activeUpgradeJob;
                delete obj._upgradeFailedJob;
                delete obj._upgradeInProgress;
                delete obj._mismatchRefreshPending;
                delete obj._sshReachable;
                delete obj._sshReachableAt;
                delete obj._deviceMode;
                delete obj._createdAt;
            }
            const state = {
                objects: objsCopy,
                deviceIdCounter: this.deviceIdCounter,
                linkIdCounter: this.linkIdCounter,
                textIdCounter: this.textIdCounter,
                deviceCounters: { ...this.deviceCounters }
            };
            
            // Remove any future history if we're not at the end
            if (this.historyIndex < this.history.length - 1) {
                this.history = this.history.slice(0, this.historyIndex + 1);
            }
            
            // Add to history
            this.history.push(state);
            this.historyIndex = this.history.length - 1;
            
            // Limit history size
            if (this.history.length > this.maxHistorySize) {
                this.history.shift();
                this.historyIndex--;
            }
            
            this.updateUndoRedoButtons();
            this.updateStepCounter();
            
            // Auto-save to localStorage with minimal debounce
            this.scheduleAutoSave();
        } catch (error) {
            console.error('ERROR in saveState():', error);
            console.error('Error stack:', error.stack);
            alert('Error saving state: ' + error.message);
        }
    }
    
    restoreState(state) {
        if (!state) return;
        
        // Hide all toolbars before restoring — object sizes/positions change
        this.hideAllSelectionToolbars();
        
        // Temporarily disable auto-save during restore to prevent triggering saveState
        const wasInitializing = this.initializing;
        this.initializing = true;
        
        this.objects = JSON.parse(JSON.stringify(state.objects));
        for (const obj of this.objects) {
            if ((obj.type === 'link' || obj.type === 'unbound') && obj._hidden) {
                delete obj._hidden;
            }
        }
        this.deviceIdCounter = state.deviceIdCounter;
        this.linkIdCounter = state.linkIdCounter;
        this.textIdCounter = state.textIdCounter;
        this.deviceCounters = { ...state.deviceCounters };
        
        this.selectedObject = null;
        this.selectedObjects = [];
        this.updatePropertiesPanel();
        this.requestDraw();
        
        // Restore initializing flag
        this.initializing = wasInitializing;
    }
    
    undo() {
        console.log('undo() called - historyIndex:', this.historyIndex, 'history.length:', this.history.length);
        
        if (this.debugger) {
            this.debugger.logAction('UNDO requested');
        }
        
        if (!this.history || this.history.length === 0) {
            console.warn('Cannot undo: history is empty');
            if (this.debugger) {
                this.debugger.logWarning('Cannot undo: history is empty');
            }
            return;
        }
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const state = this.history[this.historyIndex];
            console.log('Restoring state at index', this.historyIndex, 'with', state.objects.length, 'objects');
            if (state) {
                this.restoreState(state);
                this.updateUndoRedoButtons();
                this.updateStepCounter();
                // Recalculate device counters for proper numbering
                this.updateDeviceCounters();
                
                if (this.debugger) {
                    this.debugger.logSuccess(`Undone to step ${this.historyIndex + 1}`);
                }
            }
        } else {
            console.warn('Cannot undo: already at beginning of history');
            if (this.debugger) {
                this.debugger.logWarning('Already at beginning of history');
            }
        }
    }
    
    redo() {
        console.log('redo() called - historyIndex:', this.historyIndex, 'history.length:', this.history.length);
        
        if (this.debugger) {
            this.debugger.logAction('REDO requested');
        }
        
        if (!this.history || this.history.length === 0) {
            console.warn('Cannot redo: history is empty');
            if (this.debugger) {
                this.debugger.logWarning('Cannot redo: history is empty');
            }
            return;
        }
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            const state = this.history[this.historyIndex];
            console.log('Restoring state at index', this.historyIndex, 'with', state.objects.length, 'objects');
            if (state) {
                this.restoreState(state);
                this.updateUndoRedoButtons();
                this.updateStepCounter();
                // Recalculate device counters for proper numbering
                this.updateDeviceCounters();
                
                if (this.debugger) {
                    this.debugger.logSuccess(`Redone to step ${this.historyIndex + 1}`);
                }
            }
        } else {
            console.warn('Cannot redo: already at end of history');
            if (this.debugger) {
                this.debugger.logWarning('Already at end of history');
            }
        }
    }
    
    updateUndoRedoButtons() {
        const undoBtn = document.getElementById('btn-undo');
        const redoBtn = document.getElementById('btn-redo');
        
        if (!undoBtn || !redoBtn) {
            console.warn('Undo/Redo buttons not found in DOM');
            return;
        }
        
        // Ensure history exists
        if (!this.history || this.history.length === 0) {
            console.warn('History is empty, disabling undo/redo');
            undoBtn.disabled = true;
            redoBtn.disabled = true;
            undoBtn.style.opacity = '0.5';
            redoBtn.style.opacity = '0.5';
            return;
        }
        
        // Validate historyIndex
        if (this.historyIndex === undefined || this.historyIndex < 0) {
            this.historyIndex = this.history.length - 1;
        }
        
        const canUndo = this.historyIndex > 0;
        const canRedo = this.historyIndex < this.history.length - 1;
        
        undoBtn.disabled = !canUndo;
        redoBtn.disabled = !canRedo;
        
        undoBtn.style.opacity = canUndo ? '1' : '0.5';
        redoBtn.style.opacity = canRedo ? '1' : '0.5';
        
        console.log('updateUndoRedoButtons - canUndo:', canUndo, 'canRedo:', canRedo, 'index:', this.historyIndex, 'length:', this.history.length);
    }
    
    updateStepCounter() {
        const stepNumber = document.getElementById('step-number');
        if (stepNumber) {
            // Show current step (historyIndex + 1) and total steps
            const currentStep = this.historyIndex + 1;
            const totalSteps = this.history.length;
            stepNumber.textContent = `${currentStep}/${totalSteps}`;
        }
    }
    
    // confirmNewTopology, clearCanvas, showClearConfirmation, performClearCanvas
    // => moved to topology-file-ops.js (injected via FileOps.inject)
    
    toggleTheme() {
        const wasLight = !this.darkMode;
        this.darkMode = !this.darkMode;
        const body = document.body;
        
        if (this.darkMode) {
            body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'true');
            
            if (this.debugger) {
                this.debugger.logSuccess('🌙 Dark mode enabled');
            }
        } else {
            body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'false');
            
            if (this.debugger) {
                this.debugger.logSuccess('☀️ Light mode enabled');
            }
        }
        
        // Update link colors for seamless transition
        // Links with "default" colors should switch (black <-> white)
        const lightDefault = '#000000';
        const darkDefault = '#ffffff';
        const lightAlt = '#666666';
        const darkAlt = '#cccccc';
        
        this.objects.forEach(obj => {
            if (obj.type === 'link' || obj.type === 'unbound') {
                const color = (obj.color || '').toLowerCase();
                // If switching TO dark mode and link is black/grey -> make it white
                if (this.darkMode) {
                    if (color === lightDefault || color === '#000' || color === lightAlt || color === '#666') {
                        obj.color = darkDefault;
                    }
                } else {
                    // Switching TO light mode and link is white -> make it black
                    if (color === darkDefault || color === '#fff' || color === darkAlt || color === '#ccc') {
                        obj.color = lightDefault;
                    }
                }
            }
            
            // UPDATE TEXT COLORS for seamless transition (white <-> black)
            // BUT: Only for text WITHOUT custom backgrounds or with default backgrounds
            // If text has a custom background, preserve the color (user chose it for contrast)
            if (obj.type === 'text') {
                const hasBackground = obj.showBackground !== false;
                const hasCustomBackground = hasBackground && obj.backgroundColor && 
                    obj.backgroundColor !== '#1a1a1a' && // Not dark mode default
                    obj.backgroundColor !== '#f5f5f5' &&  // Not light mode default
                    obj.backgroundColor !== 'transparent';
                
                // Only transition colors for text without custom backgrounds
                if (!hasCustomBackground) {
                    const textColor = (obj.color || '').toLowerCase();
                    // Switching TO dark mode: black text -> white
                    if (this.darkMode) {
                        if (textColor === lightDefault || textColor === '#000' || textColor === lightAlt || textColor === '#666') {
                            obj.color = darkDefault; // White for dark mode
                        }
                    } else {
                        // Switching TO light mode: white text -> black
                        if (textColor === darkDefault || textColor === '#fff' || textColor === darkAlt || textColor === '#ccc' || textColor === '#gray' || textColor === 'gray') {
                            obj.color = lightDefault; // Black for light mode
                        }
                    }
                }
            }
        });
        
        // Update default link color setting
        this.defaultLinkColor = this.darkMode ? darkDefault : lightDefault;
        localStorage.setItem('defaultLinkColor', this.defaultLinkColor);
        
        // Update the link color picker UI
        const linkColorInput = document.getElementById('default-link-color');
        const linkColorHex = document.getElementById('default-link-color-hex');
        if (linkColorInput) linkColorInput.value = this.defaultLinkColor;
        if (linkColorHex) linkColorHex.textContent = this.defaultLinkColor.toUpperCase();
        
        this.requestDraw();
        this.scheduleAutoSave();
        
        this._updateBDPanelTheme();
        if (window.MinimapRender) window.MinimapRender.invalidateCache();
        // If topologies dropdown is open, smoothly transition inline styles in-place
        // and flag for full re-render next time it's toggled open
        const topoDropdown = document.getElementById('topologies-dropdown-menu');
        if (topoDropdown && topoDropdown.style.display !== 'none' && window.FileOps && window.FileOps._updateDropdownTheme) {
            window.FileOps._updateDropdownTheme(this);
            this._topoDropdownThemeDirty = true;
        } else if (window.FileOps && window.FileOps._renderCustomSectionsInDropdown) {
            window.FileOps._renderCustomSectionsInDropdown(this);
        }
    }
    
    // _updateBDPanelTheme => moved to topology-bd-legend.js (injected via BDLegend.inject)
    
    toggleGridLines() {
        this.gridZoomEnabled = !this.gridZoomEnabled;
        localStorage.setItem('gridZoomEnabled', this.gridZoomEnabled);
        
        // Update button appearance
        const gridBtn = document.getElementById('btn-grid-lines');
        if (gridBtn) {
            const statusText = gridBtn.querySelector('#grid-status-text');
            if (this.gridZoomEnabled) {
                gridBtn.classList.add('active', 'grid-on');
                if (statusText) statusText.textContent = 'Grid';
            } else {
                gridBtn.classList.remove('active', 'grid-on');
                if (statusText) statusText.textContent = 'Grid';
            }
        }
        
        if (this.debugger) {
            this.debugger.logInfo(this.gridZoomEnabled ? 'Grid enabled' : 'Grid disabled');
        }
        
        this.requestDraw();
        this.scheduleAutoSave();
    }
    
    drawGrid() {
        if (this.drawing && typeof this.drawing.drawGrid === 'function') {
            this.drawing.drawGrid();
            return;
        }
    }
    
    draw() {
        if (window.DrawModule) {
            return window.DrawModule.draw(this);
        }
    }

    scheduleDraw() {
        if (window.DrawModule) {
            window.DrawModule.scheduleDraw(this);
        }
    }

    requestDraw() {
        if (this._drawRafId) return;
        this._drawRafId = requestAnimationFrame(() => {
            this._drawRafId = null;
            this.draw();
        });
    }
    
    drawDeviceCircle(device, isSelected) {
        if (window.DeviceStyles) {
            window.DeviceStyles.drawDeviceCircle(this, device, isSelected);
        }
    }
    
    drawDeviceClassicRouter(device, isSelected) {
        if (window.DeviceStyles) {
            window.DeviceStyles.drawDeviceClassicRouter(this, device, isSelected);
        }
    }
    
    drawDeviceSimpleRouter(device, isSelected) {
        if (window.DeviceStyles) {
            window.DeviceStyles.drawDeviceSimpleRouter(this, device, isSelected);
        }
    }
    
    drawDeviceServerTower(device, isSelected) {
        if (window.DeviceStyles) {
            window.DeviceStyles.drawDeviceServerTower(this, device, isSelected);
        }
    }
    
    drawDeviceHexRouter(device, isSelected) {
        if (window.DeviceStyles) {
            window.DeviceStyles.drawDeviceHexRouter(this, device, isSelected);
        }
    }
    
    drawFourWayArrows(cx, cy, size, color) {
        if (window.DeviceStyles) {
            window.DeviceStyles.drawFourWayArrows(this, cx, cy, size, color);
        }
    }
    
    drawFourWayArrowsEllipse(cx, cy, radiusX, radiusY, color) {
        if (window.DeviceStyles) {
            window.DeviceStyles.drawFourWayArrowsEllipse(this, cx, cy, radiusX, radiusY, color);
        }
    }
    
    darkenColor(color, factor) {
        if (window.DeviceStyles) {
            return window.DeviceStyles.darkenColor(color, factor);
        }
        return color;
    }
    
    lightenColor(color, factor) {
        if (window.DeviceStyles) {
            return window.DeviceStyles.lightenColor(color, factor);
        }
        return color;
    }
    
    getLinkSelectionColors(linkColor) {
        if (window.DeviceStyles) {
            return window.DeviceStyles.getLinkSelectionColors(this, linkColor);
        }
        return { stroke: linkColor, glow: linkColor };
    }
    
    getDeviceBounds(device) {
        if (window.DeviceStyles) {
            return window.DeviceStyles.getDeviceBounds(device);
        }
        // Fallback
        return { type: 'circle', width: device.radius * 2, height: device.radius * 2, radius: device.radius };
    }
    
    isPointInDeviceBounds(x, y, device, tolerance = 0) {
        if (window.DeviceStyles) {
            return window.DeviceStyles.isPointInDeviceBounds(this, x, y, device, tolerance);
        }
        // Fallback - circular hit detection
        const dx = x - device.x;
        const dy = y - device.y;
        return Math.sqrt(dx * dx + dy * dy) <= device.radius + tolerance;
    }
    
    getLinkConnectionPoint(device, angle) {
        if (window.DeviceStyles) {
            return window.DeviceStyles.getLinkConnectionPoint(device, angle);
        }
        // Fallback - circle edge
        return {
            x: device.x + device.radius * Math.cos(angle),
            y: device.y + device.radius * Math.sin(angle)
        };
    }
    
    reconnectLinksToDevice(device) {
        if (window.DeviceStyles) {
            window.DeviceStyles.reconnectLinksToDevice(this, device);
        }
    }
    
    // ==================== END DEVICE VISUAL STYLES ====================
    
    drawDevice(device, unused = false, skipLabelArg = false) {
        if (window.CanvasDrawing) {
            return window.CanvasDrawing.drawDevice(this, device, unused, skipLabelArg);
        }
    }
    
    drawDeviceLabel(device) {
        if (window.CanvasDrawing) {
            return window.CanvasDrawing.drawDeviceLabel(this, device);
        }
    }
    
    drawText(text) {
        if (window.CanvasDrawing) {
            return window.CanvasDrawing.drawText(this, text);
        }
    }
    
    scheduleAutoSave() {
        if (this.initializing) return;
        // Debounce auto-save for better performance during rapid changes
        // Clear any pending auto-save
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        // Schedule auto-save with minimal delay (100ms feels instant but batches rapid changes)
        this.autoSaveTimer = setTimeout(() => {
            this.autoSave();
            this.autoSaveTimer = null;
            if (window.MinimapRender) window.MinimapRender.invalidateCache();
            this.renderMinimap();
        }, 100); // Very short delay - feels instant to user
    }
    
    // Save default text settings to localStorage AND apply to selected text objects
    saveDefaultTextSettings() {
        const defaultTextColor = document.getElementById('default-text-color');
        const defaultBgColor = document.getElementById('default-text-bg-color');
        const defaultBgEnabled = document.getElementById('default-text-bg-enabled');
        const bgOpacitySlider = document.getElementById('default-bg-opacity');
        const borderEnabled = document.getElementById('default-text-border-enabled');
        const borderColor = document.getElementById('default-text-border-color');
        const textSizeSlider = document.getElementById('default-text-size');
        const borderWidthSlider = document.getElementById('default-text-border-width');
        
        // Get active font button
        const activeFontBtn = document.querySelector('.font-btn.active');
        const fontFamily = activeFontBtn ? activeFontBtn.dataset.font : 'Inter, sans-serif';
        
        // Get active border style
        const activeBorderBtn = document.querySelector('.border-style-btn.active');
        const borderStyle = activeBorderBtn ? activeBorderBtn.dataset.style : 'solid';
        
        const settings = {
            textColor: defaultTextColor ? defaultTextColor.value : '#ffffff',
            bgColor: defaultBgColor ? defaultBgColor.value : '#1a1a2e',
            bgEnabled: defaultBgEnabled ? defaultBgEnabled.checked : true,
            bgOpacity: bgOpacitySlider ? parseInt(bgOpacitySlider.value) / 100 : 1,
            fontFamily: fontFamily,
            fontSize: textSizeSlider ? parseInt(textSizeSlider.value) : 14,
            borderEnabled: borderEnabled ? borderEnabled.checked : false,
            borderColor: borderColor ? borderColor.value : '#0066FA',
            borderStyle: borderStyle,
            borderWidth: borderWidthSlider ? parseFloat(borderWidthSlider.value) : 2
        };
        
        // Store in instance for quick access
        this.defaultFontFamily = settings.fontFamily;
        this.defaultFontSize = settings.fontSize;
        this.defaultBgOpacity = settings.bgOpacity;
        this.defaultBorderEnabled = settings.borderEnabled;
        this.defaultBorderColor = settings.borderColor;
        this.defaultBorderStyle = settings.borderStyle;
        this.defaultBorderWidth = settings.borderWidth;
        
        try {
            localStorage.setItem('topology_default_text_settings', JSON.stringify(settings));
            if (this.debugger) {
                this.debugger.logInfo(`Default text settings saved`);
            }
        } catch (e) {
            console.warn('Failed to save default text settings:', e);
        }
        
        // ENHANCED: Apply settings to selected text objects in real-time
        this.applyTextSettingsToSelected(settings);
    }
    
    // Apply current text settings from left toolbar to selected text objects
    // IMPORTANT: Font size and family are NOT applied here - they should only change 
    // when explicitly set via font controls to avoid text box resizing on color changes
    applyTextSettingsToSelected(settings, changedProperty = null) {
        // Get selected text objects
        const selectedTexts = [];
        
        // Check single selection
        if (this.selectedObject && this.selectedObject.type === 'text') {
            selectedTexts.push(this.selectedObject);
        }
        
        // Check multi-selection
        if (this.selectedObjects && this.selectedObjects.length > 0) {
            this.selectedObjects.forEach(obj => {
                if (obj.type === 'text' && !selectedTexts.includes(obj)) {
                    selectedTexts.push(obj);
                }
            });
        }
        
        // No text objects selected - nothing to do
        if (selectedTexts.length === 0) return;
        
        // Save state for undo before making changes
        let stateChanged = false;
        
        selectedTexts.forEach(textObj => {
            // Apply color based on active target
            if (this.activeColorTarget === 'text' && settings.textColor) {
                if (textObj.color !== settings.textColor) {
                    if (!stateChanged) { this.saveState(); stateChanged = true; }
                    textObj.color = settings.textColor;
                }
            } else if (this.activeColorTarget === 'background' && settings.bgColor) {
                if (textObj.bgColor !== settings.bgColor || textObj.backgroundColor !== settings.bgColor) {
                    if (!stateChanged) { this.saveState(); stateChanged = true; }
                    textObj.bgColor = settings.bgColor;
                    textObj.backgroundColor = settings.bgColor;
                }
            } else if (this.activeColorTarget === 'border' && settings.borderColor) {
                if (textObj.borderColor !== settings.borderColor) {
                    if (!stateChanged) { this.saveState(); stateChanged = true; }
                    textObj.borderColor = settings.borderColor;
                }
            }
            
            // Apply background enabled state
            if (settings.bgEnabled !== undefined && textObj.showBackground !== settings.bgEnabled) {
                if (!stateChanged) { this.saveState(); stateChanged = true; }
                textObj.showBackground = settings.bgEnabled;
            }
            
            // Apply background opacity
            if (settings.bgOpacity !== undefined && textObj.backgroundOpacity !== settings.bgOpacity) {
                if (!stateChanged) { this.saveState(); stateChanged = true; }
                textObj.backgroundOpacity = settings.bgOpacity;
            }
            
            // Apply border enabled state
            if (settings.borderEnabled !== undefined && textObj.showBorder !== settings.borderEnabled) {
                if (!stateChanged) { this.saveState(); stateChanged = true; }
                textObj.showBorder = settings.borderEnabled;
            }
            
            // Apply border style
            if (settings.borderStyle && textObj.borderStyle !== settings.borderStyle) {
                if (!stateChanged) { this.saveState(); stateChanged = true; }
                textObj.borderStyle = settings.borderStyle;
            }
            
            // Apply border width
            if (settings.borderWidth !== undefined && textObj.borderWidth !== settings.borderWidth) {
                if (!stateChanged) { this.saveState(); stateChanged = true; }
                textObj.borderWidth = settings.borderWidth;
            }
            
            // NOTE: Font family and size are intentionally NOT applied here
            // They are only applied via the dedicated font button/slider handlers
            // to prevent text boxes from resizing when changing colors
        });
        
        // Redraw if any changes were made
        if (stateChanged) {
            this.requestDraw();
            this.scheduleAutoSave();
            
            if (this.debugger) {
                this.debugger.logInfo(`Applied text settings to ${selectedTexts.length} selected text object(s)`);
            }
        }
    }
    
    // Apply font family and/or size to selected text objects
    // Called explicitly by font controls to avoid size changes when just changing colors
    applyFontToSelectedText(fontFamily, fontSize) {
        // Get selected text objects
        const selectedTexts = [];
        
        if (this.selectedObject && this.selectedObject.type === 'text') {
            selectedTexts.push(this.selectedObject);
        }
        
        if (this.selectedObjects && this.selectedObjects.length > 0) {
            this.selectedObjects.forEach(obj => {
                if (obj.type === 'text' && !selectedTexts.includes(obj)) {
                    selectedTexts.push(obj);
                }
            });
        }
        
        if (selectedTexts.length === 0) return;
        
        let stateChanged = false;
        
        selectedTexts.forEach(textObj => {
            if (fontFamily && textObj.fontFamily !== fontFamily) {
                if (!stateChanged) { this.saveState(); stateChanged = true; }
                textObj.fontFamily = fontFamily;
            }
            if (fontSize && textObj.fontSize !== fontSize) {
                if (!stateChanged) { this.saveState(); stateChanged = true; }
                textObj.fontSize = fontSize;
            }
        });
        
        if (stateChanged) {
            this.requestDraw();
            this.scheduleAutoSave();
            
            if (this.debugger) {
                const changes = [];
                if (fontFamily) changes.push(`font: ${fontFamily}`);
                if (fontSize) changes.push(`size: ${fontSize}px`);
                this.debugger.logInfo(`Applied ${changes.join(', ')} to ${selectedTexts.length} text object(s)`);
            }
        }
    }
    
    // Add color to synchronized last used colors (max 4 colors)
    addToLastUsedColors(color) {
        if (!color || color === 'transparent') return;
        
        // Normalize color to uppercase hex
        const normalizedColor = color.toUpperCase();
        
        // Remove if already exists (will be re-added at front)
        this.lastUsedColors = this.lastUsedColors.filter(c => c.toUpperCase() !== normalizedColor);
        
        // Add to front
        this.lastUsedColors.unshift(normalizedColor);
        
        // Keep only 4 colors
        if (this.lastUsedColors.length > 4) {
            this.lastUsedColors = this.lastUsedColors.slice(0, 4);
        }
        
        // Save to localStorage
        localStorage.setItem('syncedLastUsedColors', JSON.stringify(this.lastUsedColors));
        
        // Update all displays
        this.updateAllLastUsedColorDisplays();
    }
    
    // Update all last used color displays across all palettes
    updateAllLastUsedColorDisplays() {
        // Get all last used color containers
        const containers = [
            document.getElementById('unified-last-used-colors'),
            document.getElementById('link-last-used-colors')
        ].filter(Boolean);
        
        containers.forEach(container => {
            const swatches = container.querySelectorAll('div');
            swatches.forEach((swatch, index) => {
                const color = this.lastUsedColors[index] || '';
                swatch.dataset.color = color;
                if (color) {
                    swatch.style.background = color;
                    swatch.style.backgroundSize = '';
                    swatch.style.backgroundPosition = '';
                    swatch.style.cursor = 'pointer';
                } else {
                    // Empty slot - checkerboard pattern
                    swatch.style.background = `linear-gradient(45deg, 
                        rgba(255,255,255,0.1) 25%, transparent 25%,
                        transparent 75%, rgba(255,255,255,0.1) 75%),
                        linear-gradient(45deg, 
                        rgba(255,255,255,0.1) 25%, transparent 25%,
                        transparent 75%, rgba(255,255,255,0.1) 75%)`;
                    swatch.style.backgroundSize = '8px 8px';
                    swatch.style.backgroundPosition = '0 0, 4px 4px';
                    swatch.style.cursor = 'default';
                }
            });
        });
    }
    
    // Load default text settings from localStorage
    loadDefaultTextSettings() {
        try {
            const saved = localStorage.getItem('topology_default_text_settings');
            if (saved) {
                const settings = JSON.parse(saved);
                
                // MIGRATION: Convert old green default (#2ecc71) to white (#ffffff)
                if (settings.textColor && settings.textColor.toLowerCase() === '#2ecc71') {
                    console.log('Migrating old green default text color to white');
                    settings.textColor = '#ffffff';
                    // Save the migrated settings
                    localStorage.setItem('topology_default_text_settings', JSON.stringify(settings));
                }
                
                const defaultTextColor = document.getElementById('default-text-color');
                const defaultTextColorPreview = document.getElementById('default-text-color-preview');
                const defaultBgColor = document.getElementById('default-text-bg-color');
                const defaultBgEnabled = document.getElementById('default-text-bg-enabled');
                const bgOpacitySlider = document.getElementById('default-bg-opacity');
                const bgOpacityValue = document.getElementById('bg-opacity-value');
                const borderEnabled = document.getElementById('default-text-border-enabled');
                const borderColor = document.getElementById('default-text-border-color');
                
                if (defaultTextColor && settings.textColor) {
                    defaultTextColor.value = settings.textColor;
                    if (defaultTextColorPreview) {
                        defaultTextColorPreview.style.color = settings.textColor;
                        if (settings.fontFamily) {
                            defaultTextColorPreview.style.fontFamily = settings.fontFamily;
                        }
                    }
                    // Update palette selection
                    document.querySelectorAll('.default-text-palette-color').forEach(swatch => {
                        swatch.style.border = swatch.dataset.color.toLowerCase() === settings.textColor.toLowerCase() 
                            ? '2px solid #3498db' : '2px solid transparent';
                    });
                }
                
                if (defaultBgColor && settings.bgColor) {
                    defaultBgColor.value = settings.bgColor;
                    // Update palette selection
                    document.querySelectorAll('.default-bg-palette-color').forEach(swatch => {
                        swatch.style.border = swatch.dataset.color.toLowerCase() === settings.bgColor.toLowerCase() 
                            ? '2px solid #3498db' : '2px solid transparent';
                    });
                }
                
                if (defaultBgEnabled && settings.bgEnabled !== undefined) {
                    defaultBgEnabled.checked = settings.bgEnabled;
                }
                
                // Load new settings
                if (bgOpacitySlider && settings.bgOpacity !== undefined) {
                    const opacityPercent = Math.round(settings.bgOpacity * 100);
                    bgOpacitySlider.value = opacityPercent;
                    if (bgOpacityValue) bgOpacityValue.textContent = opacityPercent + '%';
                    this.defaultBgOpacity = settings.bgOpacity;
                }
                
                if (settings.fontFamily) {
                    this.defaultFontFamily = settings.fontFamily;
                    // Update font button selection
                    document.querySelectorAll('.font-btn').forEach(btn => {
                        if (btn.dataset.font === settings.fontFamily) {
                            btn.classList.add('active');
                        } else {
                            btn.classList.remove('active');
                        }
                    });
                }
                
                // Load font size
                if (settings.fontSize) {
                    this.defaultFontSize = settings.fontSize;
                    const textSizeSlider = document.getElementById('default-text-size');
                    const textSizeValue = document.getElementById('default-text-size-value');
                    if (textSizeSlider) textSizeSlider.value = settings.fontSize;
                    if (textSizeValue) textSizeValue.textContent = settings.fontSize + 'px';
                    // Update size preset button selection
                    document.querySelectorAll('.size-preset-btn').forEach(btn => {
                        if (parseInt(btn.dataset.size) === settings.fontSize) {
                            btn.classList.add('active');
                        } else {
                            btn.classList.remove('active');
                        }
                    });
                }
                
                if (borderEnabled && settings.borderEnabled !== undefined) {
                    borderEnabled.checked = settings.borderEnabled;
                    this.defaultBorderEnabled = settings.borderEnabled;
                }
                
                if (borderColor && settings.borderColor) {
                    borderColor.value = settings.borderColor;
                    this.defaultBorderColor = settings.borderColor;
                }
                
                if (settings.borderStyle) {
                    this.defaultBorderStyle = settings.borderStyle;
                    document.querySelectorAll('.border-style-btn').forEach(btn => {
                        if (btn.dataset.style === settings.borderStyle) {
                            btn.classList.add('active');
                            btn.style.background = 'rgba(0,102,250,0.25)';
                            btn.style.borderColor = '#0066FA';
                        } else {
                            btn.classList.remove('active');
                            btn.style.background = 'rgba(0,0,0,0.2)';
                            btn.style.borderColor = 'rgba(255,255,255,0.1)';
                        }
                    });
                }
                
                if (this.debugger) {
                    this.debugger.logInfo(`📂 Default text settings loaded`);
                }
            }
        } catch (e) {
            console.warn('Failed to load default text settings:', e);
        }
    }
    
    autoSave() {
        if (this.initializing) return;
        if (!Array.isArray(this.objects) || this.objects.length === 0) {
            console.warn('[AutoSave] Skipped: empty topology');
            return;
        }
        
        // Sanity check: refuse to overwrite a save that had significantly more
        // objects. This catches accidental mass-deletion (Ctrl+X, Delete key
        // while dialog open, etc.) and prevents the corrupted state from being
        // persisted. The user can still undo and the previous save survives.
        const prevCount = this._lastSavedObjectCount || 0;
        if (prevCount >= 5 && this.objects.length < Math.ceil(prevCount * 0.3)) {
            console.warn(`[AutoSave] BLOCKED: object count dropped from ${prevCount} to ${this.objects.length} (>70% loss). Previous save preserved.`);
            return;
        }
        
        try {
            const data = {
                version: '1.0',
                objects: this.objects.map(obj => {
                    const copy = { ...obj };
                    delete copy._badgeWorlds;
                    delete copy._hostnameMismatch;
                    delete copy._mismatchDismissed;
                    delete copy._identity;
                    delete copy._configHostname;
                    delete copy._stackData;
                    delete copy._stackCachedAt;
                    delete copy._lldpData;
                    delete copy._lldpCompletedAt;
                    delete copy._gitCommit;
                    delete copy._gitCommitFetchedAt;
                    delete copy._gitCommitFailed;
                    delete copy._renaming;
                    delete copy._activeConfigJob;
                    delete copy._activeUpgradeJob;
                    delete copy._upgradeFailedJob;
                    delete copy._upgradeInProgress;
                    delete copy._mismatchRefreshPending;
                    delete copy._sshReachable;
                    delete copy._sshReachableAt;
                    delete copy._deviceMode;
                    delete copy._createdAt;
                    if ((copy.type === 'link' || copy.type === 'unbound') && copy._hidden) {
                        delete copy._hidden;
                    }
                    return copy;
                }),
                metadata: {
                    deviceIdCounter: this.deviceIdCounter,
                    linkIdCounter: this.linkIdCounter,
                    textIdCounter: this.textIdCounter,
                    shapeIdCounter: this.shapeIdCounter,
                    deviceCounters: this.deviceCounters,
                    linkCurveMode: this.linkCurveMode,
                    globalCurveMode: this.globalCurveMode,
                    linkContinuousMode: this.linkContinuousMode,
                    linkStyle: this.linkStyle,
                    showLinkTypeLabels: this.showLinkTypeLabels,
                    deviceNumbering: this.deviceNumbering,
                    deviceCollision: this.deviceCollision,
                    movableDevices: this.movableDevices,
                    magneticFieldStrength: this.magneticFieldStrength,
                    gridZoomEnabled: this.gridZoomEnabled,
                    showAngleMeter: this.showAngleMeter
                },
                timestamp: Date.now()
            };

            const jsonData = JSON.stringify(data);
            
            // Rotating backup: preserve the previous good save before overwriting
            try {
                const prev = localStorage.getItem('topology_autosave');
                if (prev) {
                    localStorage.setItem('topology_autosave_backup', prev);
                }
            } catch (_) {}
            
            localStorage.setItem('topology_autosave', jsonData);
            this._lastSavedObjectCount = this.objects.length;
        } catch (error) {
            console.error('[AutoSave] Failed:', error);
        }
    }
    
    loadAutoSave() {
        try {
            console.log('=== LOAD AUTO-SAVE START ===');
            const saved = localStorage.getItem('topology_autosave');
            console.log('Raw saved data exists:', !!saved);
            console.log('Saved data length:', saved ? saved.length : 0);

            if (saved && saved.length > 0) {
                const data = JSON.parse(saved);
                console.log('Parsed data objects count:', data.objects?.length || 0);
                console.log('Parsed data metadata:', data.metadata);

                if (data.objects && Array.isArray(data.objects)) {
                    // Direct label repair: fix known corrupted names BEFORE
                    // anything else reads this.objects.  Runs synchronously.
                    const _labelFixes = { 'Bitch': 'RR-SA-2' };
                    for (const obj of data.objects) {
                        if (obj.type === 'device' && _labelFixes[obj.label]) {
                            console.warn(`[LabelRepair] "${obj.label}" -> "${_labelFixes[obj.label]}"`);
                            obj.label = _labelFixes[obj.label];
                        }
                    }
                    this.objects = data.objects;
                    this._lastSavedObjectCount = this.objects.length;
                    console.log('Successfully assigned objects array with', this.objects.length, 'items');
                } else {
                    console.warn('No valid objects array in saved data');
                    this.objects = [];
                }

                // Add missing properties for compatibility
                this.objects.forEach(obj => {
                    if (obj.type === 'device' && !obj.label) {
                        obj.label = obj.deviceType === 'router' ? 'NCP' : 'S';
                    }
                    // Ensure all links have a style property (backward compatibility)
                    if ((obj.type === 'link' || obj.type === 'unbound') && !obj.style) {
                        obj.style = 'solid'; // Default style for old links without style
                    }
                    // Add origin type and timestamp for backward compatibility
                    if ((obj.type === 'link' || obj.type === 'unbound') && !obj.originType) {
                        obj.originType = obj.type === 'link' ? 'QL' : 'UL';
                        obj.createdAt = Date.now() - (parseInt(obj.id.split('_')[1]) || 0) * 100; // Estimate
                    }
                    // CLEAR STALE LLDP RUNNING STATE on page refresh
                    // LLDP operations don't persist across page loads
                    if (obj.type === 'device') {
                        delete obj._lldpRunning;
                        delete obj._lldpAnimating;
                        delete obj._lldpAnimStart;
                        delete obj._lldpWavePhase;
                        delete obj._lldpHasLinks;
                        delete obj._lldpSuccessGlow;
                        delete obj._lldpFailureGlow;
                        delete obj._lldpJobId;
                        // Strip transient monitor state that should never persist.
                        // These are re-populated by DeviceMonitor on each session.
                        // Persisting them caused stale _configHostname to trigger
                        // false mismatch popups and silent label overwrites.
                        delete obj._badgeWorlds;
                        delete obj._hostnameMismatch;
                        delete obj._mismatchDismissed;
                        delete obj._identity;
                        delete obj._configHostname;
                        delete obj._stackData;
                        delete obj._stackCachedAt;
                        delete obj._lldpData;
                        delete obj._lldpCompletedAt;
                        delete obj._gitCommit;
                        delete obj._gitCommitFetchedAt;
                        delete obj._gitCommitFailed;
                        delete obj._renaming;
                        delete obj._activeConfigJob;
                        delete obj._activeUpgradeJob;
                        delete obj._upgradeFailedJob;
                        delete obj._upgradeInProgress;
                        delete obj._mismatchRefreshPending;
                        delete obj._sshReachable;
                        delete obj._sshReachableAt;
                        delete obj._deviceMode;
                        delete obj._createdAt;
                    }
                });
                
                // LABEL INTEGRITY CHECK: cross-ref SSH hosts against device inventory.
                // If a device's SSH target resolves to a known inventory hostname that
                // differs from the canvas label, warn and auto-fix so stale names from
                // accidental mismatch-popup renames don't persist across sessions.
                this._repairLabelsFromInventory();

                // AUTO-CORRECT CREDENTIALS for loaded devices
                this._correctDeviceCredentials();
                
                // AUTO-REPAIR corrupted links (if any)
                const repairedCount = this.repairCorruptedLinks();
                if (repairedCount > 0) {
                    console.log(`[LinkRepair] Auto-repaired ${repairedCount} corrupted links on load`);
                }

                // IMPORTANT: Link positions will be calculated dynamically by draw()
                // based on device positions and linkIndex - no need to set them here
                // This ensures links stay properly connected and offset even after refresh

                this.deviceIdCounter = data.metadata?.deviceIdCounter || 0;
                this.linkIdCounter = data.metadata?.linkIdCounter || 0;
                this.textIdCounter = data.metadata?.textIdCounter || 0;
                this.shapeIdCounter = data.metadata?.shapeIdCounter || 0;  // CRITICAL FIX: Restore shape ID counter
                this.deviceCounters = data.metadata?.deviceCounters || { router: 0, switch: 0 };
                
                // CRITICAL FIX: If shapeIdCounter wasn't saved before, calculate from existing shapes
                // This handles old saves that don't have shapeIdCounter in metadata
                if (!data.metadata?.shapeIdCounter && this.objects.length > 0) {
                    const shapes = this.objects.filter(o => o.type === 'shape');
                    if (shapes.length > 0) {
                        const maxShapeNum = Math.max(...shapes.map(s => {
                            const match = s.id?.match(/shape_(\d+)/);
                            return match ? parseInt(match[1], 10) : -1;
                        }));
                        this.shapeIdCounter = maxShapeNum + 1;
                        console.log(`[loadAutoSave] Calculated shapeIdCounter from existing shapes: ${this.shapeIdCounter}`);
                    }
                }

                // Restore additional settings
                if (data.metadata?.deviceNumbering !== undefined) {
                    this.deviceNumbering = data.metadata.deviceNumbering;
                    const btn = document.getElementById('btn-device-numbering');
                    if (btn) {
                        if (this.deviceNumbering) {
                            btn.classList.add('active');
                        } else {
                            btn.classList.remove('active');
                        }
                    }
                }
                if (data.metadata?.deviceCollision !== undefined) {
                    this.deviceCollision = data.metadata.deviceCollision;
                    const btn = document.getElementById('btn-device-collision');
                    const statusText = btn?.querySelector('.status-text');
                    const svg = btn?.querySelector('svg');
                    
                    if (btn) {
                        if (this.deviceCollision) {
                            btn.classList.add('active');
                            btn.title = 'Collision ON - Devices Cannot Overlap';
                            if (statusText) statusText.textContent = 'Collision';
                            if (svg) {
                                svg.innerHTML = `
                                    <circle cx="8" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
                                    <circle cx="16" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
                                `;
                            }
                        } else {
                            btn.classList.remove('active');
                            btn.title = 'Collision OFF - Devices Can Overlap';
                            if (statusText) statusText.textContent = 'Collision';
                            // Update icon to show overlapping circles
                            if (svg) {
                                svg.innerHTML = `
                                    <circle cx="9" cy="12" r="5" stroke="currentColor" stroke-width="2" fill="none"/>
                                    <circle cx="15" cy="12" r="5" stroke="currentColor" stroke-width="2" fill="none"/>
                                `;
                            }
                        }
                        
                        // Sync movable button state
                        const movableBtn = document.getElementById('btn-movable');
                        if (movableBtn) {
                            movableBtn.style.display = 'inline-flex';
                        }
                        
                        console.log('Collision state restored:', this.deviceCollision ? 'ON' : 'OFF');
                    }
                }
                if (data.metadata?.movableDevices !== undefined) {
                    this.movableDevices = data.metadata.movableDevices;
                    const btn = document.getElementById('btn-movable');
                    const statusText = btn?.querySelector('.status-text');
                    
                    if (btn) {
                        if (this.movableDevices) {
                            btn.classList.add('active');
                            btn.title = 'Movable ON - Devices Push Each Other on Collision';
                            if (statusText) statusText.textContent = 'Movable';
                        } else {
                            btn.classList.remove('active');
                            btn.title = 'Movable OFF - Devices Are Static';
                            if (statusText) statusText.textContent = 'Movable';
                        }
                    }
                }
                if (data.metadata?.magneticFieldStrength !== undefined) {
                    this.magneticFieldStrength = data.metadata.magneticFieldStrength;
                    document.getElementById('curve-magnitude-value').textContent = this.magneticFieldStrength;
                    document.getElementById('curve-magnitude-slider').value = this.magneticFieldStrength;
                }
                if (data.metadata?.gridZoomEnabled !== undefined) {
                    this.gridZoomEnabled = data.metadata.gridZoomEnabled;
                    // Update grid button appearance
                    const gridBtn = document.getElementById('btn-grid-lines');
                    if (gridBtn) {
                        if (this.gridZoomEnabled) {
                            gridBtn.classList.add('active', 'grid-on');
                        } else {
                            gridBtn.classList.remove('active', 'grid-on');
                        }
                    }
                }
                if (data.metadata?.showAngleMeter !== undefined) {
                    this.showAngleMeter = data.metadata.showAngleMeter;
                    const btn = document.getElementById('btn-angle-meter');
                    const statusText = btn?.querySelector('.status-text');
                    if (btn) {
                        if (this.showAngleMeter) {
                            btn.classList.add('active');
                            if (statusText) statusText.textContent = 'Angle: ON';
                        } else {
                            btn.classList.remove('active');
                            if (statusText) statusText.textContent = 'Angle: OFF';
                        }
                    }
                }

                // Restore link curve mode setting
                if (data.metadata?.linkCurveMode !== undefined) {
                    this.linkCurveMode = data.metadata.linkCurveMode;
                    // Update button to reflect loaded state
                    const btn = document.getElementById('btn-link-curve');
                    const statusText = btn?.querySelector('.status-text');
                    if (btn) {
                        if (this.linkCurveMode) {
                            btn.classList.add('active');
                            if (statusText) statusText.textContent = 'Curve: ON';
                        } else {
                            btn.classList.remove('active');
                            if (statusText) statusText.textContent = 'Curve: OFF';
                        }
                    }
                }
                
                // Restore global curve mode (auto/manual/off)
                if (data.metadata?.globalCurveMode !== undefined) {
                    this.globalCurveMode = data.metadata.globalCurveMode;
                    this.updateGlobalCurveModeUI();
                }

                // Restore continuous linking mode setting
                if (data.metadata?.linkContinuousMode !== undefined) {
                    this.linkContinuousMode = data.metadata.linkContinuousMode;
                    const btn = document.getElementById('btn-link-continuous');
                    const statusText = btn?.querySelector('.status-text');
                    if (btn) {
                        if (this.linkContinuousMode) {
                            btn.classList.add('active');
                            if (statusText) statusText.textContent = 'Chain: ON';
                        } else {
                            btn.classList.remove('active');
                            if (statusText) statusText.textContent = 'Chain: OFF';
                        }
                    }
                }
                
                // Restore link style setting
                if (data.metadata?.linkStyle !== undefined) {
                    this.linkStyle = data.metadata.linkStyle;
                    
                    // Update link style buttons to reflect loaded state
                    const solidBtn = document.getElementById('btn-link-style-solid');
                    const dashedBtn = document.getElementById('btn-link-style-dashed');
                    const arrowBtn = document.getElementById('btn-link-style-arrow');
                    
                    if (solidBtn && dashedBtn && arrowBtn) {
                        solidBtn.classList.remove('active');
                        dashedBtn.classList.remove('active');
                        arrowBtn.classList.remove('active');
                        
                        if (this.linkStyle === 'solid') {
                            solidBtn.classList.add('active');
                        } else if (this.linkStyle === 'dashed' || this.linkStyle === 'dashed-wide' || this.linkStyle === 'dotted') {
                            dashedBtn.classList.add('active');
                            // Update dashed icon based on style
                            const svg = dashedBtn.querySelector('svg');
                            if (svg) {
                                if (this.linkStyle === 'dashed-wide') {
                                    svg.innerHTML = `
                                        <path d="M2 6h6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                        <path d="M14 6h6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                        <path d="M26 6h6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                    `;
                                } else if (this.linkStyle === 'dotted') {
                                    svg.innerHTML = `
                                        <circle cx="4" cy="6" r="2" fill="currentColor"/>
                                        <circle cx="12" cy="6" r="2" fill="currentColor"/>
                                        <circle cx="20" cy="6" r="2" fill="currentColor"/>
                                        <circle cx="28" cy="6" r="2" fill="currentColor"/>
                                    `;
                                }
                            }
                        } else if (this.linkStyle === 'arrow' || this.linkStyle === 'double-arrow' || this.linkStyle === 'dashed-arrow' || this.linkStyle === 'dashed-double-arrow') {
                            arrowBtn.classList.add('active');
                            // Update arrow icon based on style
                            const svg = arrowBtn.querySelector('svg');
                            if (svg) {
                                if (this.linkStyle === 'double-arrow') {
                                    svg.innerHTML = `
                                        <path d="M8 6h16" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                        <path d="M8 9l-6-3 6-3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                                        <path d="M24 3l6 3-6 3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                                    `;
                                } else if (this.linkStyle === 'dashed-arrow') {
                                    svg.innerHTML = `
                                        <path d="M2 6h8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                        <path d="M14 6h8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                        <path d="M24 3l6 3-6 3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                                    `;
                                } else if (this.linkStyle === 'dashed-double-arrow') {
                                    svg.innerHTML = `
                                        <path d="M10 6h4" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                        <path d="M18 6h4" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                        <path d="M8 9l-6-3 6-3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                                        <path d="M24 3l6 3-6 3" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                                    `;
                                }
                            }
                        }
                    }
                }
                
                // Restore link type labels setting
                if (data.metadata?.showLinkTypeLabels !== undefined) {
                    this.showLinkTypeLabels = data.metadata.showLinkTypeLabels;
                    const btn = document.getElementById('btn-link-type-labels');
                    const statusText = btn?.querySelector('.status-text');
                    if (btn) {
                        if (this.showLinkTypeLabels) {
                            btn.classList.add('active');
                            if (statusText) statusText.textContent = 'Labels: ON';
                        } else {
                            btn.classList.remove('active');
                            if (statusText) statusText.textContent = 'Labels: OFF';
                        }
                    }
                }

                console.log('=== LOAD AUTO-SAVE COMPLETE ===');
                console.log('Auto-saved topology restored successfully');
                console.log('Final objects count:', this.objects.length);
                console.log('Objects details:', this.objects);
            } else {
                console.log('No auto-save data found in localStorage');
            }
        } catch (error) {
            console.error('=== LOAD AUTO-SAVE FAILED ===');
            console.error('Failed to load auto-save:', error);
            console.error('Error details:', error.stack);
            // Don't alert - just continue with empty canvas
        }
    }
    
    // generateTopologyData, quickSaveTopology, saveTopologyAs, exportTopologyJSON,
    // exportTopologyAsPNG, saveAsDnaasTopology, loadDnaasTopology, showDnaasTopologySelector,
    // saveBugTopology, showDebugDnosTopologiesSubmenu, showDebugDnosTopologySelector,
    // loadDebugDnosTopology, loadCustomSections, _renderCustomSectionsInDropdown,
    // saveToSection, loadFromSection, _showSectionTopologyPicker, showManageSections,
    // _sectionIcons, _sectionColors
    // => moved to topology-file-ops.js (injected via FileOps.inject)
    
    // Helper: Format time ago
    getTimeAgo(date) {
        const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
        if (seconds < 60) return 'just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    }
    
    // Load topology from data object
    loadTopologyFromData(data, opts) {
        this._clearBDState();
        this._loadDomain = opts?.domain || null;

        const wasPoolEnabled = localStorage.getItem('ssh_pool_enabled') === 'true';
        if (typeof ScalerAPI !== 'undefined' && ScalerAPI.toggleSSHPool) {
            ScalerAPI.toggleSSHPool(false).catch(() => {}).finally(() => {
                if (wasPoolEnabled) ScalerAPI.toggleSSHPool(true).catch(() => {});
            });
        }

        this.objects = data.objects || [];
        
        // Add missing properties for compatibility
        this.objects.forEach((obj, index) => {
            if (obj.type === 'device') {
                if (!obj.label) {
                    obj.label = obj.deviceType === 'router' ? 'NCP' : 'S';
                }
                if (obj.x === undefined || obj.y === undefined || isNaN(obj.x) || isNaN(obj.y)) {
                    obj.x = 200 + (index % 5) * 150;
                    obj.y = 200 + Math.floor(index / 5) * 150;
                }
                if (!obj.radius) {
                    obj.radius = 50;
                }
            }
            if ((obj.type === 'link' || obj.type === 'unbound') && !obj.style) {
                obj.style = 'solid';
            }
        });

        // Post-load link repair: fix orphaned device refs and missing start/end
        const deviceById = (id) => this.objects.find(o => o.type === 'device' && o.id === id);
        this.objects.forEach((obj) => {
            if (obj.type === 'link' && obj.device1 && obj.device2) {
                const d1 = deviceById(obj.device1);
                const d2 = deviceById(obj.device2);
                if (!d1 || !d2) {
                    console.warn('[loadTopology] Orphaned link', obj.id, '- device1:', obj.device1, 'device2:', obj.device2);
                }
            }
            if (obj.type === 'unbound') {
                if (!obj.start || typeof obj.start.x !== 'number' || typeof obj.start.y !== 'number') {
                    const d1 = obj.device1 ? deviceById(obj.device1) : null;
                    const d2 = obj.device2 ? deviceById(obj.device2) : null;
                    obj.start = d1 ? { x: d1.x, y: d1.y } : (obj.start || { x: 200, y: 200 });
                }
                if (!obj.end || typeof obj.end.x !== 'number' || typeof obj.end.y !== 'number') {
                    const d1 = obj.device1 ? deviceById(obj.device1) : null;
                    const d2 = obj.device2 ? deviceById(obj.device2) : null;
                    obj.end = d2 ? { x: d2.x, y: d2.y } : (d1 ? { x: d1.x + 150, y: d1.y } : { x: 350, y: 200 });
                }
            }
            if ((obj.type === 'link' || obj.type === 'unbound') && obj._hidden === true) {
                delete obj._hidden;
            }
        });

        // GROUP VALIDATION: Validate all groups after loading
        if (this.groups) this.groups.validate();
        
        this.deviceIdCounter = data.metadata?.deviceIdCounter || 0;
        this.linkIdCounter = data.metadata?.linkIdCounter || 0;
        this.textIdCounter = data.metadata?.textIdCounter || 0;
        
        // Restore settings
        if (data.metadata?.linkCurveMode !== undefined) {
            this.linkCurveMode = data.metadata.linkCurveMode;
        }
        if (data.metadata?.globalCurveMode !== undefined) {
            this.globalCurveMode = data.metadata.globalCurveMode;
        }
        if (window.CurveModeManager) {
            window.CurveModeManager.updateUI(this);
        }
        
        this.selectedObject = null;
        this.selectedObjects = [];
        
        this.draw();
        this.saveState();

        this._detectAndRestoreBDState(data.metadata);

        this.events?.emit('topology:loaded', {});
        setTimeout(() => this.centerOnDevices(), 50);
    }

    _clearBDState() {
        this.hideBDLegend();
        this._multiBDMetadata = null;
        this._bdVisibility = {};
        this._bdPanelOpen = false;
        this.updateBDHierarchyButton();
        try { localStorage.removeItem('bd_panel_state'); } catch (_) {}
        try { localStorage.removeItem('topology_bd_panel_state'); } catch (_) {}
    }

    _detectAndRestoreBDState(metadata) {
        const domainIsDnaas = this._loadDomain && this._loadDomain.toLowerCase().includes('dnaas');
        const metaIsDnaas = metadata?.isDnaas === true;
        if (!domainIsDnaas && !metaIsDnaas) {
            this.updateBDHierarchyButton();
            return;
        }

        if (metadata?.bridge_domains?.length > 0) {
            this._multiBDMetadata = metadata;
        } else {
            this._reconstructBDMetadataFromCanvas();
        }

        if (this._multiBDMetadata?.bridge_domains?.length > 0) {
            this.showBDLegend(this._multiBDMetadata.bridge_domains);
        }
        this.updateBDHierarchyButton();
    }
    
    // saveTopology, loadTopology => moved to topology-file-ops.js
    
    // Load predefined DNAAS example topologies
    loadPredefinedDnaasTopology(topologyType) {
        if (window.DnaasHelpers && window.DnaasHelpers.loadPredefinedDnaasTopology) {
            return window.DnaasHelpers.loadPredefinedDnaasTopology(this, topologyType);
        }
    }
    
    // Show custom input dialog (replacement for prompt())
    showInputDialog(title, placeholder, callback, defaultValue = '') {
        if (window.DialogManager) {
            return window.DialogManager.showInputDialog(this, title, placeholder, callback, defaultValue);
        }
    }
    
    // Show info dialog (replacement for alert())
    showInfoDialog(title, message) {
        if (window.DialogManager) {
            return window.DialogManager.showInfoDialog(this, title, message);
        }
    }
    
    /**
     * Populate the DNAAS panel suggestions with devices on grid that have SSH config or SN attached
     */
    /**
     * Check if a device label/hostname indicates it's a DNAAS router (LEAF, SPINE, FABRIC, TOR, etc.)
     * These devices are part of the DNAAS fabric and should NOT be used to start topology discovery.
     * @param {string} labelOrAddr - Device label, hostname, or address to check
     * @returns {boolean} True if this is a DNAAS router
     */
    isDnaasRouter(labelOrAddr) {
        // Delegate to DNAAS module
        return this.dnaas ? this.dnaas.isRouter(labelOrAddr) : false;
    }
    
    /**
     * Check if a device is a termination device (PE/CE) that can start topology discovery.
     * Termination devices are the customer-edge devices that connect to the DNAAS fabric.
     * @param {Object} device - Device object to check
     * @returns {boolean} True if this is a termination device
     */
    isTerminationDevice(device) {
        if (!device) return false;
        
        const label = device.label || '';
        const addr = device.sshConfig?.host || device.sshConfig?.hostBackup || device.deviceSerial || '';
        
        // If it's a DNAAS router, it's NOT a termination device
        if (this.isDnaasRouter(label) || this.isDnaasRouter(addr)) {
            return false;
        }
        
        // Otherwise, if it has an SSH address or serial, it's a potential termination device
        const hasSSH = device.sshConfig && (device.sshConfig.host || device.sshConfig.hostBackup);
        const hasSN = device.deviceSerial && device.deviceSerial.trim() !== '';
        
        return hasSSH || hasSN;
    }
    
    populateDnaasSuggestions() {
        if (window.DnaasHelpers) {
            return window.DnaasHelpers.populateDnaasSuggestions(this);
        }
    }
    
    dismissDnaasResult() {
        if (window.DnaasHelpers) {
            return window.DnaasHelpers.dismissDnaasResult(this);
        }
    }
    
    async startMultiBDDiscovery(serial) {
        if (window.DnaasHelpers && window.DnaasHelpers.startMultiBDDiscovery) {
            window.DnaasHelpers._editor = this;
            return window.DnaasHelpers.startMultiBDDiscovery(serial);
        }
    }
    
    async cancelDnaasDiscovery() {
        if (window.DnaasHelpers && window.DnaasHelpers.cancelDnaasDiscovery) {
            window.DnaasHelpers._editor = this;
            return window.DnaasHelpers.cancelDnaasDiscovery();
        }
    }
    
    showEnableLldpDialog(serial, sshConfig = {}) {
        if (window.LldpDialog && window.LldpDialog.showEnableLldpDialog) {
            return window.LldpDialog.showEnableLldpDialog(this, serial, sshConfig);
        }
    }
    
    // Show dialog for tracing path by serial number
    showDnaasTraceDialog() {
        if (window.DnaasHelpers) {
            return window.DnaasHelpers.showTraceDialog(this);
        }
    }
    
    // Show dialog for finding Bridge Domains
    showDnaasFindBDsDialog() {
        if (window.DnaasHelpers) {
            return window.DnaasHelpers.showFindBDsDialog(this);
        }
    }
    
    // Show device inventory dialog
    showDnaasInventoryDialog() {
        if (window.DnaasHelpers && window.DnaasHelpers.showInventoryDialog) {
            return window.DnaasHelpers.showInventoryDialog(this);
        }
    }
    
    showDnaasPathDevicesDialog() {
        if (window.DnaasHelpers && window.DnaasHelpers.showPathDevicesDialog) {
            return window.DnaasHelpers.showPathDevicesDialog(this);
        }
    }
    
    // Load DNAAS discovery data directly (from API result)
    /**
     * Enrich termination devices in discovery data with SSH config from managed devices.
     * When discovery reaches the edge of the DNAAS network and finds termination devices,
     * check if their LLDP neighbors (the PE/CE devices) are already registered in the
     * managed devices (SCALER config). If so, copy the SSH credentials.
     * 
     * @param {Object} data - Discovery result data with objects array
     * @returns {Object} - Enriched data with SSH configs from managed devices
     */
    async enrichTerminationDevicesWithManagedConfig(data) {
        if (window.DnaasHelpers && window.DnaasHelpers.enrichTerminationDevicesWithManagedConfig) {
            return window.DnaasHelpers.enrichTerminationDevicesWithManagedConfig(this, data);
        }
        return data;
    }
    
    // ===== Layout Helpers (delegated to DnaasOperations) =====
    calculateLabelWidth(label) {
        if (window.DnaasOperations) {
            return window.DnaasOperations.calculateLabelWidth(label);
        }
        return 100;
    }
    
    calculateRowSpacing(devices, minSpacing = 160) {
        if (window.DnaasOperations) {
            return window.DnaasOperations.calculateRowSpacing(this, devices, minSpacing);
        }
        return minSpacing;
    }
    
    sortDevicesByLabel(devices) {
        if (window.DnaasOperations) {
            return window.DnaasOperations.sortDevicesByLabel(devices);
        }
        return devices;
    }
    
    /**
     * Auto-correct device credentials based on device type
     * Called when loading topologies to ensure correct SSH credentials
     * 
     * Credential mapping:
     * - DNAAS fabric (LEAF, SPINE, SUPERSPINE in name): sisaev / Drive1234!
     * - Interop at SuperSpine (non-DNAAS at top tier, ONLY if topology has DNAAS devices): dn / drive1234!
     * - PE/DUT devices (all others): dnroot / dnroot (DEFAULT)
     * 
     * FIX: Only apply DNAAS/interop logic if the topology actually contains DNAAS devices.
     * Regular topologies without DNAAS devices keep dnroot/dnroot for all devices.
     */
    _correctDeviceCredentials() {
        if (window.DnaasHelpers && window.DnaasHelpers.correctDeviceCredentials) {
            return window.DnaasHelpers.correctDeviceCredentials(this);
        }
    }

    _repairLabelsFromInventory() {
        // Inventory is loaded async, so schedule a deferred check.
        // Try immediately (in case already cached), then retry after 4s.
        this._doLabelRepair();
        setTimeout(() => this._doLabelRepairAsync(), 4000);
    }

    async _doLabelRepairAsync() {
        let inv = window._deviceInventory || window.deviceInventory;
        if (!inv?.devices && typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceInventory) {
            try { inv = await ScalerAPI.getDeviceInventory(); } catch (_) {}
        }
        if (!inv?.devices) return;
        this._runLabelRepair(inv);
    }

    _doLabelRepair() {
        const inv = window._deviceInventory || window.deviceInventory;
        if (!inv?.devices) return;
        this._runLabelRepair(inv);
    }

    _runLabelRepair(inv) {
        if (this._labelRepairDone) return;
        const ipToHostname = {};
        for (const [key, info] of Object.entries(inv.devices)) {
            const ip = info.mgmt_ip || key;
            if (ip && info.hostname) ipToHostname[ip] = info.hostname;
            if (key && info.hostname) ipToHostname[key] = info.hostname;
        }
        if (Object.keys(ipToHostname).length === 0) return;

        const allHostnames = new Set(Object.values(ipToHostname));
        const devices = this.objects.filter(o => o.type === 'device');
        const repaired = [];
        for (const dev of devices) {
            const sshHost = dev.sshConfig?.host || dev.sshConfig?.hostBackup || '';
            if (!sshHost) continue;
            const inventoryName = ipToHostname[sshHost];
            if (!inventoryName) continue;
            const label = (dev.label || '').trim();
            if (label === inventoryName) continue;
            // Only auto-fix if label is clearly NOT any known device name
            if (allHostnames.has(label)) continue;
            const oldLabel = label;
            dev.label = inventoryName;
            repaired.push({ oldLabel, newLabel: inventoryName, ip: sshHost });
        }
        if (repaired.length > 0) {
            this._labelRepairDone = true;
            console.warn('[LabelRepair] Fixed corrupted device labels from inventory:', repaired);
            for (const r of repaired) {
                console.warn(`  "${r.oldLabel}" -> "${r.newLabel}" (SSH: ${r.ip})`);
            }
            this.autoSave();
            this.draw();
            if (typeof this.showNotification === 'function') {
                const names = repaired.map(r => `"${r.oldLabel}" -> "${r.newLabel}"`).join(', ');
                this.showNotification(
                    `[INFO] Auto-repaired device labels: ${names}`,
                    'info', 8000
                );
            }
        } else {
            this._labelRepairDone = true;
        }
    }

    applyDnaasHierarchicalLayout(objects) {
        if (window.DnaasOperations && window.DnaasOperations.applyDnaasHierarchicalLayout) {
            return window.DnaasOperations.applyDnaasHierarchicalLayout(this, objects);
        }
    }
    
    loadDnaasData(data) {
        if (window.DnaasOperations && window.DnaasOperations.loadDnaasData) {
            return window.DnaasOperations.loadDnaasData(this, data);
        }
    }
    
    // showBDLegend, hideBDLegend, toggleBDVisibility, setBDVisibilityAll,
    // toggleBDLegendPanel, updateBDHierarchyButton, _saveBDPanelState, _loadBDPanelState,
    // restoreBDPanelIfNeeded, _updateBDPanelTheme, _reconstructBDMetadataFromCanvas,
    // toggleBDLinkView, applyBDViewMode, highlightBDPath, createBDTextBox
    // => moved to topology-bd-legend.js (injected via BDLegend.inject)
    
    // Load topology from discovery output file
    loadDnaasFromFile() {
        // Create a file input to select JSON file
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (event) => {
                try {
                    const data = JSON.parse(event.target.result);
                    
                    // Check if canvas has objects and confirm
                    const doLoad = () => {
                        this.saveState();
                        this.objects = data.objects || [];
                        
                        // Apply hierarchical layout if this looks like a DNAAS topology
                        const hasDnaasDevices = this.objects.some(o => 
                            o.type === 'device' && (o.label || '').toUpperCase().includes('DNAAS')
                        );
                        if (hasDnaasDevices) {
                            this.applyDnaasHierarchicalLayout(this.objects);
                        }
                        
                        // AUTO-CORRECT CREDENTIALS based on device type
                        // This ensures loaded topologies get the right credentials
                        this._correctDeviceCredentials();
                        
                        // Reset counters based on loaded objects
                        const deviceIds = this.objects.filter(o => o.type === 'device').map(o => parseInt(o.id.replace(/\D/g, '')) || 0);
                        const linkIds = this.objects.filter(o => o.type === 'link').map(o => parseInt(o.id.replace(/\D/g, '')) || 0);
                        this.deviceIdCounter = deviceIds.length > 0 ? Math.max(...deviceIds) + 1 : 0;
                        this.linkIdCounter = linkIds.length > 0 ? Math.max(...linkIds) + 1 : 0;
                        
                        this.selectedObject = null;
                        this.selectedObjects = [];
                        
                        // Smart zoom-to-fit
                        const devices = this.objects.filter(o => o.type === 'device');
                        if (devices.length > 0) {
                            const labelBuffer = 100;
                            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                            
                            devices.forEach(device => {
                                const radius = device.radius || 50;
                                minX = Math.min(minX, device.x - radius - labelBuffer);
                                maxX = Math.max(maxX, device.x + radius + labelBuffer);
                                minY = Math.min(minY, device.y - radius - 30);
                                maxY = Math.max(maxY, device.y + radius + 50);
                            });
                            
                            const topologyWidth = maxX - minX;
                            const topologyHeight = maxY - minY;
                            const padding = 80;
                            
                            const availableWidth = this.canvasW - padding * 2;
                            const availableHeight = this.canvasH - padding * 2;
                            
                            const zoomX = availableWidth / topologyWidth;
                            const zoomY = availableHeight / topologyHeight;
                            
                            this.zoom = Math.min(1.0, Math.min(zoomX, zoomY));
                            this.zoom = Math.max(0.4, this.zoom);
                            
                            const centerX = (minX + maxX) / 2;
                            const centerY = (minY + maxY) / 2;
                            this.panOffset = {
                                x: (this.canvasW / 2) - centerX * this.zoom,
                                y: (this.canvasH / 2) - centerY * this.zoom
                            };
                        }
                        
                        this.draw();
                        this.showToast(`Loaded ${this.objects.length} objects from ${file.name}`, 'success');
                        
                        if (this.debugger) {
                            this.debugger.logSuccess(`DNAAS discovery loaded: ${file.name} (${this.objects.length} objects)`);
                        }
                    };
                    
                    // Confirm before replacing if canvas has objects
                    if (this.objects.length > 0) {
                        this.showConfirmDialog(
                            'Replace Current Canvas?',
                            `This will replace the current canvas (${this.objects.length} objects) with the loaded topology. Continue?`,
                            doLoad
                        );
                    } else {
                        doLoad();
                    }
                } catch (err) {
                    this.showInfoDialog('Error Loading File', 'Failed to parse JSON file:\n\n' + err.message);
                }
            };
            reader.readAsText(file);
        };
        
        input.click();
    }
    
    // Show confirmation dialog (replacement for confirm())
    showConfirmDialog(title, message, onConfirm, onCancel = null, options = {}) {
        if (window.DialogManager) {
            return window.DialogManager.showConfirmDialog(this, title, message, onConfirm, onCancel, options);
        }
    }
    
    // LOGICAL VIEW: Sub-interface labels attached to link
    getDnaasLogicalBD210Topology() {
        if (window.SampleTopologyData) {
            return window.SampleTopologyData.getDnaasLogicalBD210Topology();
        }
        return { version: "1.0", objects: [], metadata: {} };
    }
    
    // PHYSICAL VIEW: Full hierarchical path with DNAAS leaf switches and fabric
    getDnaasBD210Topology() {
        if (window.SampleTopologyData) {
            return window.SampleTopologyData.getDnaasBD210Topology();
        }
        return { version: "1.0", objects: [], metadata: {} };
    }
    
    // Repair corrupted links - delegates to LinkUtils
    repairCorruptedLinks() {
        if (window.LinkUtils && window.LinkUtils.repairCorruptedLinks) {
            return window.LinkUtils.repairCorruptedLinks(this);
        }
        return 0;
    }
    
}

// Initialize animated smoke sliders
function initSmokeSliders() {
    document.querySelectorAll('.smoke-slider-wrapper').forEach(wrapper => {
        // Already initialized
        if (wrapper.dataset.initialized) return;
        wrapper.dataset.initialized = 'true';
        
        const input = wrapper.querySelector('input[type="range"]');
        const fill = wrapper.querySelector('.smoke-slider-fill');
        const edge = wrapper.querySelector('.smoke-slider-edge');
        
        if (!input || !fill) return;
        
        const updateFill = () => {
            const min = parseFloat(input.min) || 0;
            const max = parseFloat(input.max) || 100;
            const value = parseFloat(input.value) || 0;
            const percent = ((value - min) / (max - min)) * 100;
            fill.style.width = percent + '%';
            if (edge) {
                edge.style.left = `calc(${percent}% - 8px)`;
            }
        };
        
        input.addEventListener('input', updateFill);
        updateFill(); // Initial update
    });
}

// Wrap existing sliders with smoke effect
function wrapSlidersWithSmoke() {
    const sliderIds = ['default-text-size', 'default-bg-opacity', 'link-width-slider'];
    
    sliderIds.forEach(id => {
        const slider = document.getElementById(id);
        if (!slider || slider.parentElement.classList.contains('smoke-slider-wrapper')) return;
        
        // Create wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'smoke-slider-wrapper';
        
        // Create track background
        const track = document.createElement('div');
        track.className = 'smoke-slider-track';
        
        // Create animated fill
        const fill = document.createElement('div');
        fill.className = 'smoke-slider-fill';
        
        // Create wispy edge
        const edge = document.createElement('div');
        edge.className = 'smoke-slider-edge';
        fill.appendChild(edge);
        
        // Wrap slider
        slider.parentNode.insertBefore(wrapper, slider);
        wrapper.appendChild(track);
        wrapper.appendChild(fill);
        wrapper.appendChild(slider);
    });
    
    // Initialize after wrapping
    initSmokeSliders();
}

// Initialize the editor when page loads
window.addEventListener('DOMContentLoaded', () => {
    try {
    const canvas = document.getElementById('topology-canvas');
        if (!canvas) {
            console.error('❌ CRITICAL: topology-canvas element not found!');
            document.body.innerHTML = '<h1 style="color:red;padding:20px;">Error: Canvas element not found!</h1><p>Please check that index.html contains: &lt;canvas id="topology-canvas"&gt;&lt;/canvas&gt;</p>';
            return;
        }
    const editor = new TopologyEditor(canvas);
    
    canvas.focus();
    
    if (window.DeviceMonitor) DeviceMonitor.init(editor);

    // Initialize smoke sliders after editor loads
    setTimeout(wrapSlidersWithSmoke, 200);
    
    // Make editor globally accessible for debugging
    window.topologyEditor = editor;
    
    // AUTO-REPAIR: Fix any corrupted links immediately after load
    setTimeout(() => {
        console.log('[LinkRepair] Running auto-repair check...');
        const repaired = editor.repairCorruptedLinks();
        if (repaired > 0) {
            console.log(`[LinkRepair] Auto-repaired ${repaired} corrupted links on startup`);
        }
    }, 500);
    
    // Initialize visual debugger
    if (window.createDebugger) {
        window.debugger = window.createDebugger(editor);
        editor.debugger = window.debugger;
        
        // Show welcome message
        if (editor.debugger.enabled) {
            console.log('✅ Visual debugger initialized! Panel visible in top-right corner.');
            setTimeout(() => {
                editor.debugger.logSuccess('🎉 Debugger initialized! Drag header to move, D to toggle');
                editor.debugger.logInfo('Close with ✕ button, reopen with D key or Debug button');
            }, 500);
        }
    }
    
    // Debug function to check localStorage - call from browser console
    window.checkAutoSave = () => {
        const keys = ['topology_autosave', 'topology_autosave_backup', 'topology_recovery', 'topology_current'];
        console.log('=== TOPOLOGY BACKUP STATUS ===');
        console.log('Current editor objects:', editor.objects.length);
        for (const key of keys) {
            const raw = localStorage.getItem(key);
            if (!raw) { console.log(`  ${key}: [empty]`); continue; }
            try {
                const data = JSON.parse(raw);
                const objs = data.objects || [];
                const ts = data.timestamp ? new Date(data.timestamp).toLocaleString() : 'N/A';
                console.log(`  ${key}: ${objs.length} objects, saved ${ts}, ${(raw.length / 1024).toFixed(1)}KB`);
            } catch (e) { console.log(`  ${key}: parse error`); }
        }
    };
    
    // Recovery: restore from best available backup source
    window.recoverTopology = (source) => {
        const keys = ['topology_autosave', 'topology_autosave_backup', 'topology_recovery', 'topology_current'];
        if (source && typeof source === 'string') {
            keys.unshift(source);
        }
        let best = null;
        let bestKey = null;
        for (const key of keys) {
            try {
                const raw = localStorage.getItem(key);
                if (!raw) continue;
                const data = JSON.parse(raw);
                const objs = data.objects || [];
                if (objs.length > 0 && (!best || objs.length > best.objects.length)) {
                    best = data;
                    bestKey = key;
                }
            } catch (_) {}
        }
        if (!best) {
            console.error('No backup found with objects. Try loading from server: Topologies menu -> domain -> file');
            return false;
        }
        console.log(`Recovering from ${bestKey}: ${best.objects.length} objects`);
        editor.objects = best.objects;
        if (best.metadata || best.counters) {
            const m = best.metadata || best.counters || {};
            editor.deviceIdCounter = m.deviceIdCounter || m.device || 0;
            editor.linkIdCounter = m.linkIdCounter || m.link || 0;
            editor.textIdCounter = m.textIdCounter || m.text || 0;
        }
        editor.draw();
        editor.saveState();
        console.log('Recovery complete. Objects:', editor.objects.length);
        return true;
    };
    
    // Debug helper to check history state
    window.checkHistory = () => {
        console.log('=== HISTORY CHECK ===');
        console.log('historyIndex:', editor.historyIndex);
        console.log('history.length:', editor.history?.length || 0);
        console.log('Can undo:', editor.historyIndex > 0);
        console.log('Can redo:', editor.historyIndex < (editor.history?.length || 0) - 1);
        if (editor.history && editor.history.length > 0) {
            console.log('Current state objects:', editor.history[editor.historyIndex]?.objects.length || 0);
        }
        return { index: editor.historyIndex, length: editor.history?.length || 0 };
    };
    
    // Fix a corrupted device label and persist the change.
    // Usage from browser console: fixDeviceLabel('Bitch', 'RR-SA-2')
    window.fixDeviceLabel = (oldName, newName) => {
        if (!oldName || !newName) {
            console.error('Usage: fixDeviceLabel("oldLabel", "newLabel")');
            return false;
        }
        const device = editor.objects.find(
            o => o.type === 'device' && (o.label || '').trim() === oldName.trim()
        );
        if (!device) {
            console.error(`No device found with label "${oldName}"`);
            const labels = editor.objects.filter(o => o.type === 'device').map(o => o.label);
            console.log('Current device labels:', labels);
            return false;
        }
        if (editor.saveState) editor.saveState();
        device.label = newName.trim();
        editor.autoSave();
        editor.draw();
        console.log(`[fixDeviceLabel] Renamed "${oldName}" -> "${newName}" and saved.`);
        // Also clear the backup so recovery won't bring back the bad label
        try {
            const backup = localStorage.getItem('topology_autosave_backup');
            if (backup && backup.includes(oldName)) {
                const bdata = JSON.parse(backup);
                (bdata.objects || []).forEach(o => {
                    if (o.type === 'device' && (o.label || '').trim() === oldName.trim()) {
                        o.label = newName.trim();
                    }
                });
                localStorage.setItem('topology_autosave_backup', JSON.stringify(bdata));
                console.log('[fixDeviceLabel] Also fixed backup autosave.');
            }
        } catch (_) {}
        return true;
    };

    // Helper to manually sync all toggle buttons if they get out of sync
    window.syncToggles = () => {
        console.log('Syncing all toggle buttons...');
        editor.syncAllToggles();
        console.log('✓ Sync complete! Check debugger for details.');
    };
    
    // Helper to check mode and toggle states
    window.checkModes = () => {
        console.log('=== MODE & TOGGLE STATUS ===');
        console.log('Current Mode:', editor.currentMode);
        console.log('Current Tool:', editor.currentTool);
        console.log('Device Numbering:', editor.deviceNumbering);
        console.log('Device Collision:', editor.deviceCollision);
        console.log('Link Curve Mode:', editor.linkCurveMode);
        console.log('Link Continuous:', editor.linkContinuousMode);
        if (editor.momentum) console.log('Momentum/Sliding:', editor.momentum.enabled, `| Friction: ${editor.momentum.friction}`);
        console.log('========================');
    };
    
    // Inject file operations from topology-file-ops.js
    if (window.FileOps) {
        window.FileOps.inject(editor);
        window.FileOps.restoreTopologyIndicator();
    }

    // Inject BD legend methods from topology-bd-legend.js
    if (window.BDLegend) {
        window.BDLegend.inject(editor);
    }
    
    // Auto-create built-in sections (Bugs, DNAAS) then load all into dropdown
    window.FileOps._ensureBugsSection().catch(() => {}).then(() => editor.loadCustomSections());
    
    console.log('Topology Editor initialized.');
    console.log('Commands: checkAutoSave() | recoverTopology() | checkHistory() | syncToggles() | checkModes()');
    console.log('Recovery: recoverTopology() restores from best backup. checkAutoSave() shows all backup sources.');
    
    // ============================================================================
    // TOPOLOGIES BUTTON & DROPDOWN - Wire up events
    // ============================================================================
    
    const btnTopologies = document.getElementById('btn-topologies');
    const topologiesDropdown = document.getElementById('topologies-dropdown-menu');
    const fileInput = document.getElementById('file-input');
    const btnClearTop = document.getElementById('btn-clear-top');
    
    // Toggle topologies dropdown + close any open sub-panels
    if (btnTopologies && topologiesDropdown) {
        btnTopologies.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = topologiesDropdown.style.display === 'block';
            
            // Close Debug-DNOS and DNAAS sub-panels if open
            const debugPanel = document.getElementById('debug-dnos-topo-selector');
            if (debugPanel) debugPanel.remove();
            const dnaasDialog = document.getElementById('dnaas-topology-dialog');
            if (dnaasDialog) dnaasDialog.remove();
            
            // Close DNAAS and Network Mapper panels if opening Topologies
            if (!isVisible) {
                const dp = document.getElementById('dnaas-panel');
                const db = document.getElementById('btn-dnaas');
                if (dp && dp.style.display === 'block') {
                    dp.style.display = 'none';
                    if (db) db.classList.remove('dnaas-panel-open');
                }
                const nmPanel = document.getElementById('network-mapper-panel');
                const nmBtn = document.getElementById('btn-network-mapper');
                if (nmPanel && nmPanel.style.display === 'block') {
                    nmPanel.style.display = 'none';
                    if (nmBtn) nmBtn.classList.remove('nm-panel-open');
                }
            }
            
            topologiesDropdown.style.display = isVisible ? 'none' : 'block';
            btnTopologies.classList.toggle('topologies-open', !isVisible);
            
            if (!isVisible) {
                // Always re-render sections when opening to ensure consistency
                if (window.FileOps && window.FileOps._renderCustomSectionsInDropdown) {
                    window.FileOps._renderCustomSectionsInDropdown(editor);
                }
                editor._topoDropdownThemeDirty = false;
                const rect = btnTopologies.getBoundingClientRect();
                topologiesDropdown.style.position = 'fixed';
                topologiesDropdown.style.left = rect.left + 'px';
                topologiesDropdown.style.top = (rect.bottom + 4) + 'px';
            }
        });
        console.log('✓ Topologies button wired');
    }
    
    // Close dropdown when clicking outside (skip during topology file drag)
    document.addEventListener('click', (e) => {
        if (editor._topoDragActive) return;
        if (topologiesDropdown && topologiesDropdown.style.display === 'block') {
            if (!topologiesDropdown.contains(e.target) && e.target !== btnTopologies) {
                topologiesDropdown.style.display = 'none';
                if (btnTopologies) btnTopologies.classList.remove('topologies-open');
            }
        }
    });
    
    // Wire up file input for loading
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            editor.loadTopology(e);
        });
        console.log('✓ File input wired');
    }
    
    // Wire up clear button
    if (btnClearTop) {
        btnClearTop.addEventListener('click', () => {
            editor.confirmNewTopology();
        });
        console.log('✓ Clear button wired');
    }
    
    // Keyboard shortcut: Ctrl+S for quick save
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            if (editor && editor.quickSaveToDomain) {
                editor.quickSaveToDomain();
            }
        }
    });
    console.log('✓ Keyboard shortcuts wired (Ctrl+S for quick save)');
    
    // ============================================================================
    // DRAGGABLE MODALS - Use ModalUtils module
    // ============================================================================
    if (window.ModalUtils) {
        window.ModalUtils.initAllModals();
    }
    
    // ============================================================================
    // COPY TABLE FUNCTIONALITY - Copy link details table to clipboard
    // ============================================================================
    
    const copyLinkTableBtn = document.getElementById('copy-link-table');
    if (copyLinkTableBtn) {
        copyLinkTableBtn.addEventListener('click', () => {
            const table = document.getElementById('link-details-table');
            if (!table || table.rows.length === 0) {
                alert('No link data to copy!');
                return;
            }
            
            // Extract table data
            let tableText = '═══ LINK CONNECTION TABLE ═══\n\n';
            tableText += 'Device 1 | Interface | VLAN | Transceiver | ↔ | Transceiver | VLAN | Interface | Device 2\n';
            tableText += '─'.repeat(120) + '\n';
            
            for (let i = 0; i < table.rows.length; i++) {
                const row = table.rows[i];
                const cells = [];
                for (let j = 0; j < row.cells.length; j++) {
                    const cell = row.cells[j];
                    // Get input value if it's an input field, otherwise get text
                    const input = cell.querySelector('input');
                    const value = input ? input.value : cell.textContent.trim();
                    cells.push(value);
                }
                tableText += cells.join(' | ') + '\n';
            }
            
            tableText += '\n═══ Total Connections: ' + table.rows.length + ' ═══';
            
            // Copy to clipboard
            window.safeClipboardWrite(tableText).then(() => {
                // Visual feedback
                const original = copyLinkTableBtn.innerHTML;
                const originalBg = copyLinkTableBtn.style.background;
                
                copyLinkTableBtn.innerHTML = '✓ Copied!';
                copyLinkTableBtn.style.background = '#27ae60';
                
                setTimeout(() => {
                    copyLinkTableBtn.innerHTML = original;
                    copyLinkTableBtn.style.background = originalBg;
                }, 1500);
                
                console.log('Link table copied to clipboard:', table.rows.length, 'rows');
            }).catch(err => {
                alert(`Failed to copy table. Error: ${err.message}\n\nTable Data:\n${tableText}`);
            });
        });
    }
    
    console.log('✓ Link table copy button initialized');
    } catch (error) {
        console.error('❌ CRITICAL ERROR during initialization:', error);
        document.body.innerHTML = '<div style="padding: 40px; font-family: monospace; background: #1e1e1e; color: #ff6b6b; min-height: 100vh;">' +
            '<h1 style="color: #ff6b6b;">❌ Application Failed to Load</h1>' +
            '<h2>Error Details:</h2>' +
            '<pre style="background: #2d2d2d; padding: 20px; border-radius: 8px; overflow: auto;">' +
            error.toString() + '\\n\\n' +
            (error.stack || 'No stack trace available') +
            '</pre>' +
            '<p style="margin-top: 20px;">Please check the browser console for more details.</p>' +
            '<p>Common causes:</p>' +
            '<ul>' +
            '<li>Missing HTML elements referenced in JavaScript</li>' +
            '<li>Syntax errors in JavaScript files</li>' +
            '<li>Browser compatibility issues</li>' +
            '</ul>' +
            '</div>';
    }
});

