// Network Topology Creator - Main Application Logic

class TopologyEditor {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
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
        this.zoom = (savedZoom && savedZoom >= 0.25 && savedZoom <= 3) ? savedZoom : 1;
        
        const savedPanOffset = JSON.parse(localStorage.getItem('topology_panOffset') || '{"x":0,"y":0}');
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
        this.unboundLink = null; // Current unbound link being created
        this.stretchingLink = null; // Link endpoint being stretched
        this.stretchingEndpoint = null; // 'start' or 'end'
        this.stretchingConnectionPoint = false; // Whether stretching a connection point (merged ULs)
        this.textPlaced = false; // Track if text has been placed
        this.lastMousePos = null; // Last mouse position for drag detection
        this.deviceCounters = { router: 0, switch: 0 }; // Track device numbering
        this.resumePlacementAfterMarquee = null; // Store device type to resume after MS
        this.placementPending = null; // Track pending device placement
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
        this.linkContinuousMode = true; // Continuous linking mode - chain links together (ON by default)
        this.linkStickyMode = true; // Sticky links - links snap/attach to devices automatically (ON by default)
        this.linkULEnabled = true; // Unbound Links - allow double tap on screen to create UL (ON by default)
        this.linkStyle = 'solid'; // Link style: 'solid', 'dashed', 'arrow' (default: solid)
        this.ulSnapDistance = 15; // Distance for UL endpoints to snap together (pixels)
        this.deviceNumbering = true; // Auto-number devices (NCP, NCP-2, etc. or just NCP for all)
        this.deviceCollision = false; // Prevent devices from overlapping (OFF by default)
        this.movableDevices = true; // Chain reaction - devices push each other on collision (ON by default)
        this.magneticFieldStrength = 40; // Magnetic repulsion strength (1-80)
        this.magneticFieldUpdateTimer = null; // Throttle magnetic field updates
        this.gridZoomEnabled = true; // Grid adjusts size with zoom for distance tracking
        this.lastTwoFingerCenter = null; // Track two-finger gesture center
        this.altPressed = false; // Track Alt/Option key for quick link start
        this.backgroundClickCount = 0; // Track background clicks in multi-select mode
        this.darkMode = localStorage.getItem('darkMode') === 'true'; // Dark mode state
        this.lastTapTime = 0; // Track last tap/click time for double-tap detection
        this._lastTapDevice = null; // Track last device tapped for double-tap detection
        this._lastTapPos = null; // Track last tap position for double-tap detection (handles slight movement)
        this._lastTapStartTime = 0; // Track when first tap started (to detect long press)
        this.doubleTapDelay = 350; // Max delay between taps (ms)
        this.doubleTapTolerance = 50; // Max distance between taps for double-tap (px) - accounts for slight movement
        this.maxTapDuration = 200; // Max duration for a tap to be considered for double-tap (ms) - prevents long press from being a tap
        this.lastBackgroundClickTime = 0; // Track background clicks for fast double-click UL placement
        this.fastDoubleClickDelay = 250; // Fast double-click must be < 250ms to place UL (prevents accidents)
        this.resumeModeAfterMarquee = null; // Store mode to return to after marquee selection
        this.showLinkTypeLabels = false; // Debug view: Show link type labels (QL/UL/BUL) above each link
        this.hoveredLink = null; // Track link under cursor for hover highlight
        
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
        
        // Initialize momentum engine (sliding/inertia system)
        if (window.createMomentumEngine) {
            this.momentum = window.createMomentumEngine(this);
            console.log('Momentum engine initialized');
        }
        
        console.log('AFTER loadAutoSave, objects count:', this.objects.length);
        console.log('Current objects array:', this.objects);

        // Redraw after loading auto-save to show restored topology
        this.draw();
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
        
        // Sync ALL toggle buttons with their state (ensure button shows correct state)
        // This runs AFTER debugger is initialized
        setTimeout(() => {
            this.syncAllToggles();
            
            // Sync slide distance control visibility with momentum state
            const slideControl = document.getElementById('slide-distance-control');
            if (slideControl && this.momentum) {
                slideControl.style.display = this.momentum.enabled ? 'block' : 'none';
            }
            
            // Run input diagnostics for trackpad/input troubleshooting
            this.runInputDiagnostics();
        }, 100); // Small delay to ensure debugger is ready
    }
    
    setupCanvas() {
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }
    
    resizeCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        this.draw();
    }
    
    // SMOOTH MOVEMENT: Linear interpolation for smooth position updates
    lerp(current, target, factor = 0.15) {
        // Factor: 0.1 = very smooth, 0.3 = responsive, 0.5 = quick
        const diff = target - current;
        // Snap to target if very close (avoid endless tiny movements)
        if (Math.abs(diff) < 0.5) {
            return target;
        }
        return current + diff * factor;
    }
    
    // SMOOTH MOVEMENT: Interpolate a point (x, y) toward target
    lerpPoint(current, target, factor = 0.15) {
        return {
            x: this.lerp(current.x, target.x, factor),
            y: this.lerp(current.y, target.y, factor)
        };
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
        
        diagnostics.push(`🖥️ OS: ${isMac ? 'macOS' : 'Other'}`);
        diagnostics.push(`🌐 Browser: ${isSafari ? 'Safari' : isChrome ? 'Chrome' : isFirefox ? 'Firefox' : 'Other'}`);
        
        // Check Pointer Events support
        const hasPointerEvents = !!window.PointerEvent;
        diagnostics.push(`${hasPointerEvents ? '✅' : '❌'} Pointer Events API: ${hasPointerEvents ? 'Supported' : 'NOT supported'}`);
        
        // Check Touch Events support
        const hasTouchEvents = 'ontouchstart' in window;
        diagnostics.push(`${hasTouchEvents ? '✅' : '❌'} Touch Events: ${hasTouchEvents ? 'Supported' : 'NOT supported'}`);
        
        // Check canvas properties
        const canvasStyles = window.getComputedStyle(this.canvas);
        const touchAction = canvasStyles.touchAction;
        const pointerEvents = canvasStyles.pointerEvents;
        diagnostics.push(`🎨 Canvas touch-action: "${touchAction}"`);
        diagnostics.push(`🎨 Canvas pointer-events: "${pointerEvents}"`);
        
        // Check if canvas is receiving events
        const canvasRect = this.canvas.getBoundingClientRect();
        diagnostics.push(`📐 Canvas size: ${canvasRect.width}x${canvasRect.height}`);
        
        // Log to debugger if available
        if (this.debugger) {
            this.debugger.logInfo('═══ INPUT SYSTEM DIAGNOSTICS ═══');
            diagnostics.forEach(msg => this.debugger.logInfo(msg));
            this.debugger.logInfo('═══════════════════════════════');
            
            if (isMac && hasPointerEvents) {
                this.debugger.logSuccess('💻 macOS with Pointer Events - Trackpad should work!');
                this.debugger.logInfo('👉 Try clicking on the canvas now - you should see events in the debugger');
            } else if (isMac && !hasPointerEvents) {
                this.debugger.logWarning('⚠️ macOS but no Pointer Events - using mouse events fallback');
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
        // File menu events - TEMPORARILY DISABLED (functions not implemented yet)
        // const fileBtn = document.getElementById('btn-file-menu');
        // if (fileBtn) fileBtn.addEventListener('click', () => this.showFileMenu());
        // const closeFile = document.getElementById('close-file-menu');
        // if (closeFile) closeFile.addEventListener('click', () => this.hideFileMenu());
        // const btnNew = document.getElementById('btn-new-topology');
        // if (btnNew) btnNew.addEventListener('click', () => this.newTopology());
        // const btnOpen = document.getElementById('btn-open-topology');
        // if (btnOpen) btnOpen.addEventListener('click', () => this.promptOpenTopology());
        // const btnSave = document.getElementById('btn-save-topology');
        // if (btnSave) btnSave.addEventListener('click', () => this.saveToCurrentFile());
        // const btnSaveAs = document.getElementById('btn-save-as-topology');
        // if (btnSaveAs) btnSaveAs.addEventListener('click', () => this.saveAsTopology());
        
        // ENHANCED: Pointer Events API + Mouse Events (both for maximum compatibility!)
        // macOS trackpads work better with BOTH event types active
        if (window.PointerEvent) {
            // Modern browsers support PointerEvents - better for touchpads
            this.canvas.addEventListener('pointerdown', (e) => this.handlePointerDown(e));
            this.canvas.addEventListener('pointermove', (e) => this.handlePointerMove(e));
            this.canvas.addEventListener('pointerup', (e) => this.handlePointerUp(e));
            this.canvas.addEventListener('pointercancel', (e) => this.handlePointerUp(e));
            console.log('✓ Pointer Events API enabled - touchpad gestures supported');
        }
        
        // ALWAYS add mouse events as well (macOS trackpads often use these!)
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        console.log('✓ Mouse events enabled (ensures macOS trackpad compatibility)');
        
        // ENHANCED: Global mouse tracking (works even over debugger!)
        document.addEventListener('mousemove', (e) => {
            // Update mouse screen coordinates globally
            const rect = this.canvas.getBoundingClientRect();
            const scaleX = this.canvas.width / rect.width;
            const scaleY = this.canvas.height / rect.height;
            this.lastMouseScreen = {
                x: (e.clientX - rect.left) * scaleX,
                y: (e.clientY - rect.top) * scaleY
            };
            
            // Also update world position if over canvas area (even if obscured by debugger)
            if (e.clientX >= rect.left && e.clientX <= rect.right && 
                e.clientY >= rect.top && e.clientY <= rect.bottom) {
                this.lastMousePos = this.getMousePos(e);
            }
        });
        console.log('✓ Global mouse tracking enabled (works over debugger)');
        
        this.canvas.addEventListener('contextmenu', (e) => this.handleContextMenu(e));
        this.canvas.addEventListener('dblclick', (e) => this.handleDoubleClick(e));
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
        
        // Touch events for mobile devices (still needed for iOS/Android)
        this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
        this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        this.canvas.addEventListener('touchend', (e) => this.handleTouchEnd(e));
        
        // Keyboard events
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('keyup', (e) => this.handleKeyUp(e));
        
        // Save before page unload/refresh
        window.addEventListener('beforeunload', (e) => {
            console.log('=== BEFORE UNLOAD TRIGGERED ===');
            console.log('Page unloading, force auto-save with', this.objects.length, 'objects');
            console.log('Objects array:', this.objects);
            
            // Force immediate save, bypass all debouncing
            if (this.autoSaveTimer) {
                clearTimeout(this.autoSaveTimer);
                this.autoSaveTimer = null;
            }
            
            // CRITICAL: Force immediate pan offset save (bypass throttle)
            if (this._panSaveTimeout) {
                clearTimeout(this._panSaveTimeout);
                this._panSaveTimeout = null;
            }
            localStorage.setItem('topology_panOffset', JSON.stringify({
                x: this.panOffset.x,
                y: this.panOffset.y
            }));
            
            this.autoSave(); // Force immediate save, no debounce
            console.log('=== BEFORE UNLOAD SAVE COMPLETE ===');
        });
        
        // Scrollbar events
        this.setupScrollbars();
    }
    
    setupScrollbars() {
        const vScrollbar = document.getElementById('vertical-scrollbar');
        const hScrollbar = document.getElementById('horizontal-scrollbar');
        const vThumb = document.getElementById('vertical-thumb');
        const hThumb = document.getElementById('horizontal-thumb');
        
        // Vertical scrollbar (with touchpad support)
        const vThumbDown = (e) => {
            e.stopPropagation();
            this.draggingScrollbar = 'vertical';
            this.scrollbarDragStart = {
                y: e.clientY,
                panOffset: this.panOffset.y
            };
        };
        vThumb.addEventListener('mousedown', vThumbDown);
        if (window.PointerEvent) {
            vThumb.addEventListener('pointerdown', vThumbDown);
        }
        
        // Horizontal scrollbar (with touchpad support)
        const hThumbDown = (e) => {
            e.stopPropagation();
            this.draggingScrollbar = 'horizontal';
            this.scrollbarDragStart = {
                x: e.clientX,
                panOffset: this.panOffset.x
            };
        };
        hThumb.addEventListener('mousedown', hThumbDown);
        if (window.PointerEvent) {
            hThumb.addEventListener('pointerdown', hThumbDown);
        }
        
        // Global mouse/pointer events for scrollbar dragging
        const handleScrollbarMove = (e) => {
            if (this.draggingScrollbar === 'vertical') {
                const deltaY = e.clientY - this.scrollbarDragStart.y;
                const scrollbarHeight = vScrollbar.clientHeight;
                const thumbHeight = vThumb.clientHeight;
                const maxScroll = scrollbarHeight - thumbHeight;
                const scrollRatio = deltaY / maxScroll;
                // Use same dynamic range as updateScrollbars
                const baseRange = 2000;
                const zoomFactor = Math.max(1, this.zoom);
                const panRange = baseRange * zoomFactor;
                this.panOffset.y = this.scrollbarDragStart.panOffset + (scrollRatio * panRange * 2);
                this.savePanOffset();
                this.updateScrollbars();
                this.draw();
            } else if (this.draggingScrollbar === 'horizontal') {
                const deltaX = e.clientX - this.scrollbarDragStart.x;
                const scrollbarWidth = hScrollbar.clientWidth;
                const thumbWidth = hThumb.clientWidth;
                const maxScroll = scrollbarWidth - thumbWidth;
                const scrollRatio = deltaX / maxScroll;
                // Use same dynamic range as updateScrollbars
                const baseRange = 2000;
                const zoomFactor = Math.max(1, this.zoom);
                const panRange = baseRange * zoomFactor;
                this.panOffset.x = this.scrollbarDragStart.panOffset + (scrollRatio * panRange * 2);
                this.savePanOffset();
                this.updateScrollbars();
                this.draw();
            }
        };
        
        document.addEventListener('mousemove', handleScrollbarMove);
        if (window.PointerEvent) {
            document.addEventListener('pointermove', handleScrollbarMove);
        }
        
        // Mouse alignment: Click scrollbar track to jump thumb to mouse position
        vScrollbar.addEventListener('click', (e) => {
            if (e.target === vScrollbar) { // Clicked track, not thumb
                const rect = vScrollbar.getBoundingClientRect();
                const clickY = e.clientY - rect.top;
                const scrollbarHeight = vScrollbar.clientHeight;
                const thumbHeight = vThumb.clientHeight;
                
                // Center thumb at click position
                const newThumbTop = clickY - thumbHeight / 2;
                const maxScroll = scrollbarHeight - thumbHeight;
                const scrollRatio = (newThumbTop / maxScroll) * 2 - 1; // -1 to 1
                
                // Use same dynamic range as updateScrollbars
                const baseRange = 2000;
                const zoomFactor = Math.max(1, this.zoom);
                const panRange = baseRange * zoomFactor;
                this.panOffset.y = scrollRatio * panRange;
                this.savePanOffset();
                this.updateScrollbars();
                this.draw();
                this.updateHud();
            }
        });
        
        hScrollbar.addEventListener('click', (e) => {
            if (e.target === hScrollbar) { // Clicked track, not thumb
                const rect = hScrollbar.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const scrollbarWidth = hScrollbar.clientWidth;
                const thumbWidth = hThumb.clientWidth;
                
                // Center thumb at click position
                const newThumbLeft = clickX - thumbWidth / 2;
                const maxScroll = scrollbarWidth - thumbWidth;
                const scrollRatio = (newThumbLeft / maxScroll) * 2 - 1; // -1 to 1
                
                // Use same dynamic range as updateScrollbars
                const baseRange = 2000;
                const zoomFactor = Math.max(1, this.zoom);
                const panRange = baseRange * zoomFactor;
                this.panOffset.x = scrollRatio * panRange;
                this.savePanOffset();
                this.updateScrollbars();
                this.draw();
                this.updateHud();
            }
        });
        
        const handleScrollbarUp = () => {
            this.draggingScrollbar = null;
            this.scrollbarDragStart = null;
        };
        
        document.addEventListener('mouseup', handleScrollbarUp);
        if (window.PointerEvent) {
            document.addEventListener('pointerup', handleScrollbarUp);
        }
    }
    
    updateScrollbars() {
        const vThumb = document.getElementById('vertical-thumb');
        const hThumb = document.getElementById('horizontal-thumb');
        const vScrollbar = document.getElementById('vertical-scrollbar');
        const hScrollbar = document.getElementById('horizontal-scrollbar');
        
        if (!vThumb || !hThumb || !vScrollbar || !hScrollbar) return;
        
        // ENHANCED: Dynamic range based on zoom for better representation
        // At higher zoom, you can pan further, scrollbar should reflect this
        const baseRange = 2000;
        const zoomFactor = Math.max(1, this.zoom); // Scale range with zoom
        const panRange = baseRange * zoomFactor;
        
        // Vertical scrollbar - smooth position calculation
        const vMax = vScrollbar.clientHeight - vThumb.clientHeight;
        const vRatio = Math.max(-1, Math.min(1, this.panOffset.y / panRange));
        const vPos = (vRatio + 1) / 2 * vMax;
        const vPosClamped = Math.max(0, Math.min(vMax, vPos));
        
        // SMOOTH: Use transform for GPU acceleration instead of top/left
        vThumb.style.transform = `translateY(${vPosClamped}px)`;
        vThumb.style.top = '0';
        
        // Horizontal scrollbar - smooth position calculation
        const hMax = hScrollbar.clientWidth - hThumb.clientWidth;
        const hRatio = Math.max(-1, Math.min(1, this.panOffset.x / panRange));
        const hPos = (hRatio + 1) / 2 * hMax;
        const hPosClamped = Math.max(0, Math.min(hMax, hPos));
        
        // SMOOTH: Use transform for GPU acceleration instead of left
        hThumb.style.transform = `translateX(${hPosClamped}px)`;
        hThumb.style.left = '0';
    }
    
    setupToolbar() {
        document.getElementById('btn-base').addEventListener('click', () => this.setMode('base'));
        document.getElementById('btn-select').addEventListener('click', () => this.toggleTool('select'));
        document.getElementById('btn-link').addEventListener('click', () => this.toggleTool('link'));
        document.getElementById('btn-link-curve').addEventListener('click', () => this.toggleLinkCurveMode());
        document.getElementById('btn-link-continuous').addEventListener('click', () => this.toggleLinkContinuousMode());
        document.getElementById('btn-link-sticky').addEventListener('click', () => this.toggleLinkStickyMode());
        document.getElementById('btn-link-ul').addEventListener('click', () => this.toggleLinkULMode());
        document.getElementById('btn-link-style-solid').addEventListener('click', () => this.setLinkStyle('solid'));
        document.getElementById('btn-link-style-dashed').addEventListener('click', () => this.setLinkStyle('dashed'));
        document.getElementById('btn-link-style-arrow').addEventListener('click', () => this.setLinkStyle('arrow'));
        document.getElementById('btn-device-numbering').addEventListener('click', () => this.toggleDeviceNumbering());
        document.getElementById('btn-device-collision').addEventListener('click', () => this.toggleDeviceCollision());
        
        // Momentum button (optional)
        const momentumBtn = document.getElementById('btn-momentum');
        if (momentumBtn) {
            momentumBtn.addEventListener('click', () => this.toggleMomentum());
        }
        
        // Movable devices button
        const movableBtn = document.getElementById('btn-movable');
        if (movableBtn) {
            movableBtn.addEventListener('click', () => this.toggleMovableDevices());
        }
        
        document.getElementById('magnetic-field-slider').addEventListener('input', (e) => this.updateMagneticField(e.target.value));
        document.getElementById('friction-slider').addEventListener('input', (e) => this.updateFriction(e.target.value));
        document.getElementById('btn-router').addEventListener('click', () => this.toggleDevicePlacementMode('router'));
        document.getElementById('btn-switch').addEventListener('click', () => this.toggleDevicePlacementMode('switch'));
        // Text tool button (existing)
        document.getElementById('btn-text').addEventListener('click', () => this.toggleTool('text'));
        
        // NEW: Angle meter toggle button
        const angleMeterBtn = document.getElementById('btn-angle-meter');
        if (angleMeterBtn) {
            angleMeterBtn.addEventListener('click', () => this.toggleAngleMeter());
        }
        document.getElementById('btn-undo').addEventListener('click', () => this.undo());
        document.getElementById('btn-redo').addEventListener('click', () => this.redo());
        // Top bar buttons
        document.getElementById('btn-delete-top').addEventListener('click', () => this.deleteSelected());
        document.getElementById('btn-clear-top').addEventListener('click', () => this.clearCanvas());
        document.getElementById('btn-save-top').addEventListener('click', () => this.saveTopology());
        document.getElementById('btn-load-top').addEventListener('click', () => document.getElementById('file-input').click());
        document.getElementById('btn-shortcuts-top').addEventListener('click', () => this.showShortcuts());
        
        // Debugger toggle button
        const debuggerBtn = document.getElementById('btn-debugger-top');
        if (debuggerBtn) {
            debuggerBtn.addEventListener('click', () => {
                if (this.debugger) {
                    this.debugger.toggle();
                }
            });
        }
        
        // Link type labels toggle button (debug view)
        const linkTypeLabelsBtn = document.getElementById('btn-link-type-labels');
        if (linkTypeLabelsBtn) {
            linkTypeLabelsBtn.addEventListener('click', () => {
                this.showLinkTypeLabels = !this.showLinkTypeLabels;
                const statusText = linkTypeLabelsBtn.querySelector('.status-text');
                
                if (this.showLinkTypeLabels) {
                    linkTypeLabelsBtn.classList.add('active');
                    if (statusText) statusText.textContent = 'Labels: ON';
                    if (this.debugger) {
                        this.debugger.logSuccess('🏷️ Link type labels enabled');
                    }
                } else {
                    linkTypeLabelsBtn.classList.remove('active');
                    if (statusText) statusText.textContent = 'Labels: OFF';
                    if (this.debugger) {
                        this.debugger.logInfo('🏷️ Link type labels disabled');
                    }
                }
                
                this.draw();
            });
        }
        
        // Theme toggle button
        const themeBtn = document.getElementById('btn-theme-toggle');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => this.toggleTheme());
        }
        
        // Left Toolbar toggle
        const toolbarToggle = document.getElementById('toolbar-toggle');
        if (toolbarToggle) {
            toolbarToggle.addEventListener('click', () => {
                const toolbar = document.getElementById('left-toolbar');
                if (toolbar) {
                    toolbar.classList.toggle('collapsed');
                    // Resize canvas after animation completes
                    setTimeout(() => {
                        this.resizeCanvas();
                        this.draw();
                    }, 300);
                }
            });
        }
        
        // Top Bar toggle
        const topBarToggle = document.getElementById('top-bar-toggle');
        if (topBarToggle) {
            topBarToggle.addEventListener('click', () => {
                const topBar = document.querySelector('.top-bar');
                if (topBar) {
                    topBar.classList.toggle('collapsed');
                    // Resize canvas after animation completes
                    setTimeout(() => {
                        this.resizeCanvas();
                        this.draw();
                    }, 300);
                }
            });
        }
        
        document.getElementById('file-input').addEventListener('change', (e) => this.loadTopology(e));
        document.getElementById('color-picker').addEventListener('change', (e) => this.updateSelectedColor(e.target.value));
        document.getElementById('color-picker').addEventListener('focus', () => {
            if (this.selectedObject && this.selectedObject.type === 'device') {
                this.canvas.style.cursor = 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'24\' height=\'24\' viewBox=\'0 0 24 24\'%3E%3Cpath d=\'M20.71 5.63l-1.34-1.34c-.39-.39-1.02-.39-1.41 0L9 12.25 11.75 15l8.96-8.96c.39-.39.39-1.02 0-1.41zM7 14a3 3 0 0 0-3 3c0 1.31-1.16 2-2 2 .92 1.22 2.49 2 4 2a4 4 0 0 0 4-4c0-1.66-1.34-3-3-3z\' fill=\'%23000\'/%3E%3C/svg%3E") 12 12, auto';
            }
        });
        document.getElementById('color-picker').addEventListener('blur', () => {
            this.updateCursor();
        });
        document.getElementById('font-size').addEventListener('input', (e) => this.updateTextSize(e.target.value));
        document.getElementById('font-size').addEventListener('change', (e) => this.saveState()); // Save when slider released
        
        document.getElementById('device-label').addEventListener('input', (e) => this.updateDeviceLabel(e.target.value));
        document.getElementById('device-label').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.applyDeviceLabel();
            }
        });
        document.getElementById('device-label').addEventListener('blur', () => this.applyDeviceLabel());
        
        // Shortcuts button is in top bar, not toolbar
        const shortcutsBtn = document.getElementById('btn-shortcuts');
        if (shortcutsBtn) {
            shortcutsBtn.addEventListener('click', () => this.showShortcuts());
        }
        const closeShortcutsBtn = document.getElementById('close-shortcuts');
        if (closeShortcutsBtn) {
            closeShortcutsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.hideShortcuts();
            });
        }
        
        // Zoom buttons with hold-to-repeat functionality
        const zoomInBtn = document.getElementById('btn-zoom-in');
        if (zoomInBtn) {
            let zoomInInterval = null;
            zoomInBtn.addEventListener('mousedown', () => {
                this.zoomIn(); // Immediate first zoom
                zoomInInterval = setInterval(() => this.zoomIn(), 150); // Repeat every 150ms
            });
            zoomInBtn.addEventListener('mouseup', () => {
                if (zoomInInterval) clearInterval(zoomInInterval);
            });
            zoomInBtn.addEventListener('mouseleave', () => {
                if (zoomInInterval) clearInterval(zoomInInterval);
            });
        }
        
        const zoomOutBtn = document.getElementById('btn-zoom-out');
        if (zoomOutBtn) {
            let zoomOutInterval = null;
            zoomOutBtn.addEventListener('mousedown', () => {
                this.zoomOut(); // Immediate first zoom
                zoomOutInterval = setInterval(() => this.zoomOut(), 150); // Repeat every 150ms
            });
            zoomOutBtn.addEventListener('mouseup', () => {
                if (zoomOutInterval) clearInterval(zoomOutInterval);
            });
            zoomOutBtn.addEventListener('mouseleave', () => {
                if (zoomOutInterval) clearInterval(zoomOutInterval);
            });
        }
        
        const zoomResetBtn = document.getElementById('btn-zoom-reset');
        if (zoomResetBtn) {
            zoomResetBtn.addEventListener('click', () => this.resetZoom());
        }
        
        // Context menu handlers
        document.getElementById('ctx-duplicate').addEventListener('click', () => this.handleContextDuplicate());
        document.getElementById('ctx-add-text').addEventListener('click', () => this.handleContextAddText());
        document.getElementById('ctx-toggle-curve').addEventListener('click', () => this.handleContextToggleCurve());
        document.getElementById('ctx-change-color').addEventListener('click', () => this.handleContextColor());
        document.getElementById('ctx-change-size').addEventListener('click', () => this.handleContextSize());
        document.getElementById('ctx-change-label').addEventListener('click', () => this.handleContextLabel());
        document.getElementById('ctx-lock').addEventListener('click', () => this.handleContextLock());
        document.getElementById('ctx-unlock').addEventListener('click', () => this.handleContextUnlock());
        document.getElementById('ctx-delete').addEventListener('click', () => this.handleContextDelete());
        
        // Close context menu on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#context-menu')) {
                this.hideContextMenu();
            }
        });
        
        // Close shortcuts modal on backdrop click
        document.getElementById('shortcuts-modal').addEventListener('click', (e) => {
            if (e.target.id === 'shortcuts-modal') {
                this.hideShortcuts();
            }
        });

        // Close shortcuts modal on Escape key
        document.addEventListener('keydown', (e) => {
            const shortcutsModal = document.getElementById('shortcuts-modal');
            const textEditorModal = document.getElementById('text-editor-modal');
            const linkDetailsModal = document.getElementById('link-details-modal');
            
            if (e.key === 'Escape') {
                if (shortcutsModal && shortcutsModal.classList.contains('show')) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.hideShortcuts();
                } else if (textEditorModal && textEditorModal.classList.contains('show')) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.hideTextEditor();
                } else if (linkDetailsModal && linkDetailsModal.classList.contains('show')) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.hideLinkDetails();
                }
            }
        });
        
        // Close text editor modal on backdrop click
        const textEditorModal = document.getElementById('text-editor-modal');
        if (textEditorModal) {
            textEditorModal.addEventListener('click', (e) => {
                if (e.target.id === 'text-editor-modal') {
                    // CRITICAL FIX: Don't close if we just finished dragging
                    const modalContent = textEditorModal.querySelector('.draggable-modal');
                    if (modalContent && modalContent.dataset.justDragged === 'true') {
                        return; // Ignore backdrop click after drag
                    }
                    this.hideTextEditor();
                }
            });
        }
        
        // Close link details modal on backdrop click ONLY
        // ENHANCED: Prevent closing during drag/resize operations
        const linkDetailsModal = document.getElementById('link-details-modal');
        if (linkDetailsModal) {
            // Make these accessible from makeDraggableModal/makeResizableModal
            window._linkModalDragging = false;
            window._linkModalResizing = false;
            let lastInteractionTime = 0;
            
            // Track interaction state
            const modalContent = linkDetailsModal.querySelector('.modal-content');
            if (modalContent) {
                // Track all mousedown events on modal
                modalContent.addEventListener('mousedown', (e) => {
                    lastInteractionTime = Date.now();
                    console.log('📌 Modal content mousedown');
                });
                
                // Only stop click propagation on modal body/content (not handles/header)
                const modalBody = modalContent.querySelector('.modal-body');
                if (modalBody) {
                    modalBody.addEventListener('click', (e) => {
                        e.stopPropagation();
                    });
                }
            }
            
            // Only close on backdrop click (with multiple safety checks)
            linkDetailsModal.addEventListener('click', (e) => {
                const timeSinceInteraction = Date.now() - lastInteractionTime;
                
                console.log('🎯 Modal backdrop clicked:', {
                    target: e.target.id,
                    dragging: window._linkModalDragging,
                    resizing: window._linkModalResizing,
                    timeSince: timeSinceInteraction
                });
                
                // Only close if:
                // 1. Clicking directly on backdrop
                // 2. Not currently dragging or resizing
                // 3. At least 500ms since last interaction (prevents close after drag/resize)
                if (e.target.id === 'link-details-modal' && 
                    !window._linkModalDragging && 
                    !window._linkModalResizing &&
                    timeSinceInteraction > 500) {
                    console.log('✅ Closing modal (intentional backdrop click)');
                    this.hideLinkDetails();
                } else {
                    console.log('❌ Modal close blocked (safety check)');
                }
            });
        }
        
        // Text editor modal handlers
        const closeTextEditorBtn = document.getElementById('close-text-editor');
        if (closeTextEditorBtn) {
            closeTextEditorBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Close text editor button clicked');
                this.hideTextEditor();
            });
        } else {
            console.warn('Close text editor button not found during setup');
        }
        const applyTextEditorBtn = document.getElementById('btn-text-editor-apply');
        if (applyTextEditorBtn) {
            applyTextEditorBtn.addEventListener('click', () => this.applyTextEditor());
        }
        const cancelTextEditorBtn = document.getElementById('btn-text-editor-cancel');
        if (cancelTextEditorBtn) {
            cancelTextEditorBtn.addEventListener('click', () => this.hideTextEditor());
        }

        // Link details modal handlers
        const closeLinkDetailsBtn = document.getElementById('close-link-details');
        if (closeLinkDetailsBtn) {
            closeLinkDetailsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Close link details button clicked');
                this.hideLinkDetails();
            });
        } else {
            console.warn('Close link details button not found during setup');
        }
        const closeLinkDetailsBtn2 = document.getElementById('btn-close-link-details');
        if (closeLinkDetailsBtn2) {
            closeLinkDetailsBtn2.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Close link details button 2 clicked');
                this.hideLinkDetails();
            });
        } else {
            console.warn('Close link details button 2 not found during setup');
        }
        const saveLinkDetailsBtn = document.getElementById('btn-save-link-details');
        if (saveLinkDetailsBtn) {
            saveLinkDetailsBtn.addEventListener('click', () => this.saveLinkDetails());
        }
        const addInterfaceLabelsBtn = document.getElementById('btn-add-interface-labels');
        if (addInterfaceLabelsBtn) {
            addInterfaceLabelsBtn.addEventListener('click', () => this.addInterfaceLabelsFromModal());
        }
        document.getElementById('editor-rotation').addEventListener('input', (e) => {
            document.getElementById('editor-rotation-value').textContent = e.target.value + '°';
        });
    }
    
    // LAYER SYSTEM COMPLETELY REMOVED
    
    getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        
        // Get screen position (accounting for CSS scaling)
        const screenX = (e.clientX - rect.left) * scaleX;
        const screenY = (e.clientY - rect.top) * scaleY;
        
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
                this.debugger.logError(`⚠️ getMousePos() returned huge value: (${worldX.toFixed(0)}, ${worldY.toFixed(0)})`);
                this.debugger.logInfo(`Screen: (${screenX}, ${screenY}), Pan: (${this.panOffset.x}, ${this.panOffset.y}), Zoom: ${this.zoom}`);
            }
        }
        
        return {
            x: worldX,
            y: worldY
        };
    }
    
    getTouchPos(e) {
        const touch = e.touches[0] || e.changedTouches[0];
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        
        // Get screen position (accounting for CSS scaling)
        const screenX = (touch.clientX - rect.left) * scaleX;
        const screenY = (touch.clientY - rect.top) * scaleY;
        
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
                this.debugger.logInfo(`👆👆👆 3-FINGER gesture started (${this.activePointers.size} pointers active)`);
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
                        this.debugger.logWarning(`👆 3-finger gesture moved ${Math.round(moved)}px - not a tap`);
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
                    this.debugger.logInfo(`👆 3-finger gesture detected but disabled (use right-click on device or double-click on screen instead)`);
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
    // MOUSE EVENT HANDLERS (original handlers, now also called by pointer events)
    // ============================================================================
    
    handleMouseDown(e) {
        // CRITICAL FIX: Removed duplicate prevention - it was blocking ALL clicks!
        // Let both pointer and mouse events work - any duplicates are harmless
        
        // ENHANCED: Log with input device type differentiation
        // FIXED: Prevent duplicate logging when both pointer and mouse events fire
        if (this.debugger && !this._skipMouseLog) {
            // Reduced logging: Don't log every click (too verbose)
            // Uncomment if debugging click detection:
            // const inputSource = this._lastInputType || 'mouse';
            // const icon = inputSource === 'trackpad' ? '🖐️' : '🖱️';
            // this.debugger.logAction(`${icon} Click: button=${e.button}`);
        }
        
        // Clear the skip flag for next event
        this._skipMouseLog = false;
        
        // Hide context menu on any click
        this.hideContextMenu();
        
        const pos = this.getMousePos(e);
        
        // CRITICAL: Check for double-tap BEFORE any other logic (handles slight movement)
        // This prevents background click detection when double-tapping with slight movement
        // Note: If first tap was a long press, tap tracking is already cleared in mouseup
        if (this._lastTapDevice && this._lastTapPos) {
            const now = Date.now();
            const timeSinceLastTap = now - this.lastTapTime;
            const clickedObject = this.findObjectAt(pos.x, pos.y);
            
            // Check if this is a double-tap on the same device (or near it)
            const isSameDevice = clickedObject && clickedObject === this._lastTapDevice;
            const isNearLastTap = this._lastTapPos && 
                Math.sqrt(Math.pow(pos.x - this._lastTapPos.x, 2) + Math.pow(pos.y - this._lastTapPos.y, 2)) <= this.doubleTapTolerance;
            
            // If it's a quick second tap on the same device OR near the first tap position, enter link mode
            // Note: Long presses are already filtered out in mouseup, so we only get here for quick taps
            if (timeSinceLastTap < this.doubleTapDelay && (isSameDevice || isNearLastTap)) {
                // Cancel any device placement
                if (this.placingDevice) {
                    this.placingDevice = null;
                }
                
                // Enter link mode with the device from first tap
                this.setMode('link');
                this.linking = true;
                this.linkStart = this._lastTapDevice;
                
                if (this.debugger) {
                    const gridPos = this.worldToGrid({ x: this._lastTapDevice.x, y: this._lastTapDevice.y });
                    this.debugger.logSuccess(`👆👆 Double-tap detected: LINK mode from ${this._lastTapDevice.label || 'Device'}`);
                    this.debugger.logInfo(`Device: ${this._lastTapDevice.label} at Grid(${Math.round(gridPos.x)}, ${Math.round(gridPos.y)})`);
                    this.debugger.logInfo(`Time between taps: ${timeSinceLastTap}ms`);
                    if (!isSameDevice && isNearLastTap) {
                        const dist = Math.sqrt(Math.pow(pos.x - this._lastTapPos.x, 2) + Math.pow(pos.y - this._lastTapPos.y, 2));
                        this.debugger.logInfo(`Movement detected: ${dist.toFixed(1)}px (within ${this.doubleTapTolerance}px tolerance)`);
                    }
                }
                
                this.lastTapTime = 0; // Reset
                this._lastTapDevice = null;
                this._lastTapPos = null;
                this._lastTapStartTime = 0; // Reset
                this.draw();
                return;
            }
        }
        
        // Track background clicks for fast double-click UL placement
        const clickedObj = this.findObjectAt(pos.x, pos.y);
        if (!clickedObj) {
            // Clicked on background - track timing
            const now = Date.now();
            const timeSinceLastClick = now - this.lastBackgroundClickTime;
            this.lastBackgroundClickTime = now;
            
            // Reduced logging: Don't log every background click
            // Uncomment if debugging double-click UL creation:
            // if (this.debugger && timeSinceLastClick < this.fastDoubleClickDelay && timeSinceLastClick > 0) {
            //     this.debugger.logInfo(`⏱️ Background click #2: ${timeSinceLastClick}ms`);
            // }
        }
        
        // Alt/Option + Click on device → Quick link start (from ANY mode)
        if ((this.altPressed || e.altKey) && e.button === 0) {
            const clickedDevice = this.findObjectAt(pos.x, pos.y);
            if (clickedDevice && clickedDevice.type === 'device') {
                // Cancel any device placement
                if (this.placingDevice) {
                    this.placingDevice = null;
                }
                // Enter link mode with this device as start
                this.setMode('link');
                this.linking = true;
                this.linkStart = clickedDevice;
                this.draw();
                return;
            }
        }
        
        // Pan with middle mouse button or space + left click
        if (e.button === 1 || this.spacePressed) {
            this.panning = true;
            this.panStart = {
                x: e.clientX - this.panOffset.x,
                y: e.clientY - this.panOffset.y
            };
            this.canvas.style.cursor = 'move';
            e.preventDefault();
            return;
        }
        
        // Check for link endpoint stretching (unbound links) - check before other object detection
        if (!this.stretchingLink && this.currentTool === 'select') {
            const clickedLink = this.findUnboundLinkEndpoint(pos.x, pos.y);
            if (clickedLink && clickedLink.link.type === 'unbound') {
                this.stretchingLink = clickedLink.link;
                this.stretchingEndpoint = clickedLink.endpoint;
                this.stretchingConnectionPoint = clickedLink.isConnectionPoint || false; // Track if dragging connection point
                this.selectedObject = clickedLink.link;
                this.selectedObjects = [clickedLink.link];
                
                // TRACKING: Store initial positions of ALL links in the BUL chain for jump detection
                const allMergedLinks = this.getAllMergedLinks(clickedLink.link);
                this._bulTrackingData = {
                    startTime: Date.now(),
                    links: allMergedLinks.map(link => ({
                        id: link.id,
                        type: link.type,
                        startPos: { x: link.start.x, y: link.start.y },
                        endPos: { x: link.end.x, y: link.end.y },
                        device1: link.device1,
                        device2: link.device2,
                        lastPos: { 
                            start: { x: link.start.x, y: link.start.y },
                            end: { x: link.end.x, y: link.end.y }
                        }
                    })),
                    grabPoint: this.stretchingEndpoint,
                    isConnectionPoint: this.stretchingConnectionPoint,
                    totalJumps: 0
                };
                
                if (this.debugger) {
                    // Calculate UL number in chain
                    const ulNumber = allMergedLinks.findIndex(l => l.id === clickedLink.link.id) + 1;
                    
                    this.debugger.logInfo(`🎯 UL Grabbed: ${clickedLink.link.id} (U${ulNumber}) at ${this.stretchingEndpoint}`);
                    this.debugger.logInfo(`   Chain size: ${allMergedLinks.length} link(s)`);
                    
                    if (this.stretchingConnectionPoint) {
                        // Find partner link for MP drag and get MP number
                        let partnerLinkId = null;
                        let mpNumber = 0;
                        
                        if (clickedLink.link.mergedWith) {
                            partnerLinkId = clickedLink.link.mergedWith.linkId;
                            mpNumber = clickedLink.link.mergedWith.mpNumber || 0;
                        } else if (clickedLink.link.mergedInto) {
                            partnerLinkId = clickedLink.link.mergedInto.parentId;
                            const parent = this.objects.find(o => o.id === partnerLinkId);
                            if (parent?.mergedWith) {
                                mpNumber = parent.mergedWith.mpNumber || 0;
                            }
                        }
                        
                        this.debugger.logInfo(`   Point type: 🟣 MP-${mpNumber} (Connection Point)`);
                        
                        if (partnerLinkId) {
                            const partnerUL = allMergedLinks.findIndex(l => l.id === partnerLinkId) + 1;
                            this.debugger.logInfo(`   🟣 MP-${mpNumber} connects U${ulNumber} ↔ U${partnerUL}`);
                            this.debugger.logInfo(`   🔒 Other ${allMergedLinks.length - 2} link(s) in chain will stay fixed`);
                        }
                    } else {
                        // It's a TP - find which TP number it is
                        // FIXED: Use clearer logic - endpoint is TP if NOT connected
                        const tpsInBUL = [];
                        allMergedLinks.forEach(chainLink => {
                            if (!this.isEndpointConnected(chainLink, 'start')) {
                                tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start' });
                            }
                            
                            if (!this.isEndpointConnected(chainLink, 'end')) {
                                tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end' });
                            }
                        });
                        
                        // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                        tpsInBUL.sort((a, b) => {
                            const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                            const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                            return ulNumA - ulNumB;
                        });
                        
                        const tpIndex = tpsInBUL.findIndex(tp => tp.linkId === clickedLink.link.id && tp.endpoint === this.stretchingEndpoint);
                        const tpNumber = (tpIndex >= 0) ? tpIndex + 1 : 0;
                        
                        this.debugger.logInfo(`   Point type: ⚪ TP-${tpNumber} (Free Endpoint) on U${ulNumber}-${this.stretchingEndpoint}`);
                    }
                }
                
                this.draw();
                return;
            }
        }
        
        // Handle device placement mode
        if (this.placingDevice) {
            // Only respond to left-click (button 0); defer placement until mouseup so we can detect drag for MS
            if (e.button === 0) {
                this.placementPending = {
                    type: this.placingDevice,
                    startPos: { x: pos.x, y: pos.y },
                    clickTime: Date.now()
                };
                // Prepare potential marquee selection if user drags
                this.selectionRectStart = { x: pos.x, y: pos.y };
                
                if (this.debugger) {
                    this.debugger.logInfo(`📍 Device placement pending (${this.placingDevice})`);
                }
            }
            // Right-click will be handled by contextmenu event (exits to base mode)
            return;
        }
        
        // Check for handles ONLY on SELECTED text object
        let handleFound = false;
        if (this.selectedObject && this.selectedObject.type === 'text' && e.button === 0) {
            const textObj = this.selectedObject;
            // Temporarily set font to measure text
            this.ctx.save();
                this.ctx.font = `${textObj.fontSize}px Arial`;
                const metrics = this.ctx.measureText(textObj.text || 'Text');
            const textWidth = metrics.width;
                const textHeight = parseInt(textObj.fontSize);
            this.ctx.restore();
            
                const angle = textObj.rotation * Math.PI / 180;
                
                // Define all corner handles
                const corners = [
                    { x: -textWidth/2 - 5, y: -textHeight/2 - 5, type: 'resize' },  // Top-left
                    { x: textWidth/2 + 5, y: -textHeight/2 - 5, type: 'rotation' },  // Top-right
                    { x: textWidth/2 + 5, y: textHeight/2 + 5, type: 'resize' },     // Bottom-right
                    { x: -textWidth/2 - 5, y: textHeight/2 + 5, type: 'resize' }     // Bottom-left
                ];
                
                // Check each corner handle with HUGE hitbox
                for (const corner of corners) {
                    // Transform corner to world coordinates (accounting for text rotation)
                    const rotatedX = corner.x * Math.cos(angle) - corner.y * Math.sin(angle);
                    const rotatedY = corner.x * Math.sin(angle) + corner.y * Math.cos(angle);
                    const handleWorldX = textObj.x + rotatedX;
                    const handleWorldY = textObj.y + rotatedY;
                    
                    const dx = pos.x - handleWorldX;
                    const dy = pos.y - handleWorldY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
                    // Balanced hitbox: 20px radius (2x the visual size) - precise but easy to click
                    if (dist < 20) {
                        this.selectedObject = textObj;
                        this.selectedObjects = [textObj];
                        
                    if (corner.type === 'rotation') {
                // Start text rotation
                        this.saveState(); // Make text rotation undoable
                this.rotatingText = true;
                        const mouseAngle = Math.atan2(pos.y - textObj.y, pos.x - textObj.x);
                this.textRotationStartAngle = mouseAngle;
                        this.textRotationStartRot = textObj.rotation;
                    } else {
                        // Start text resize - drag away from center = bigger, toward center = smaller
                        this.saveState(); // Make text resize undoable
                        this.resizingText = true;
                        this.textResizeStartSize = textObj.fontSize;
                        this.textResizeStartDist = Math.sqrt(
                            Math.pow(pos.x - textObj.x, 2) + 
                            Math.pow(pos.y - textObj.y, 2)
                        );
                    }
                        handleFound = true;
                e.preventDefault();
                return;
                    }
            }
        }
        
        // Find clicked object if we didn't click text handles
        let clickedObject = null;
        if (!this.rotatingText && !this.resizingText) {
            clickedObject = this.findObjectAt(pos.x, pos.y);
        }
        
        // Check for device rotation handle (only on selected devices)
        // CRITICAL: Only allow rotation AFTER device is selected AND mouse is released
        // This prevents race conditions with collision detection and drag offset calculation
        if (clickedObject && clickedObject.type === 'device' && 
            this.selectedObject === clickedObject && 
            this.currentMode === 'select' && 
            e.button === 0 &&
            clickedObject._mouseReleasedAfterSelection === true) { // Must release mouse after selection first
            if (this.findRotationHandle(clickedObject, pos.x, pos.y)) {
                // Start device rotation
                this.saveState();
                this.rotatingDevice = clickedObject;
                this.rotationStartAngle = Math.atan2(pos.y - clickedObject.y, pos.x - clickedObject.x);
                this.rotationStartValue = clickedObject.rotation || 0;
                this.dragging = false; // Ensure dragging is false for rotation
                
                // Stop momentum if active
                if (this.momentum) {
                    if (this.momentum.activeSlides.has(clickedObject.id)) {
                        this.momentum.activeSlides.delete(clickedObject.id);
                    }
                    this.momentum.reset();
                }
                
                if (this.debugger) {
                    this.debugger.logSuccess(`🔄 Device rotation started: ${clickedObject.label || 'Device'}`);
                    this.debugger.logInfo(`   Rotation enabled after mouse release - prevents race conditions`);
                }
                
                this.draw();
                e.preventDefault();
                return;
            }
        }
        
        // Long press detection for multi-select
        // CRITICAL FIX: Skip long press timer if a double-click happened recently (prevents MS after UL)
        const timeSinceDoubleClick = Date.now() - this.lastDoubleClickTime;
        if (timeSinceDoubleClick > 500) { // Only set timer if > 500ms since last double-click
        this.longPressTimer = setTimeout(() => {
            this.startMultiSelect(pos);
        }, this.longPressDelay);
        }
        
        if (!clickedObject) {
            clickedObject = this.findObjectAt(pos.x, pos.y);
        }
        
        if (this.currentTool === 'select') {
            // Check if there are multiple selected objects OR multiSelectMode is active
            if (this.selectedObjects.length > 1 || this.multiSelectMode) {
                // Multi-select mode from marquee
                if (clickedObject) {
                    if (this.selectedObjects.includes(clickedObject)) {
                        // Clicked on a selected object - drag ALL selected objects
                        // CRITICAL FIX: Stop ALL momentum/slides FIRST before capturing positions!
                        if (this.momentum) {
                            this.momentum.stopAll(); // Stop active slides
                            this.momentum.reset();   // Clear velocity history
                        }
                        
                        this.saveState(); // Save before moving
                        // CRITICAL FIX: Calculate all positions BEFORE setting dragging=true!
                        // For multi-select drag, store ABSOLUTE mouse position (not offset)
                        // This is used in handleMouseMove to calculate delta: dx = pos.x - dragStart.x
                        this.dragStart = { x: pos.x, y: pos.y };
                        this.dragStartTime = Date.now(); // Track drag start time for momentum
                        this.multiSelectInitialPositions = this.selectedObjects
                            // No need to filter links - all links are now unbound with TPs
                            .map(obj => {
                                const pos = {
                                    id: obj.id,
                                    x: obj.x, 
                                    y: obj.y
                                };
                                // For unbound links, also store endpoints
                                if (obj.type === 'unbound') {
                                    pos.startX = obj.start.x;
                                    pos.startY = obj.start.y;
                                    pos.endX = obj.end.x;
                                    pos.endY = obj.end.y;
                                }
                                return pos;
                            });
                        
                        // NOW set dragging=true AFTER all positions are safely captured
                        // CRITICAL: Clear tap tracking when dragging starts to prevent drag-release from being mistaken for double-tap
                        this.lastTapTime = 0;
                        this._lastTapDevice = null;
                        this._lastTapPos = null;
                        this._lastTapStartTime = 0;
                        this.dragging = true;
                        
                        // Track starting position for tap vs drag detection (momentum fix)
                        this.dragStartPos = null; // Multi-select uses different tracking
                        
                        this.updatePropertiesPanel();
                    } else {
                        // Clicked on an unselected object - select only this object
                        // CRITICAL FIX: Stop ALL momentum/slides FIRST before capturing positions!
                        if (this.momentum) {
                            this.momentum.stopAll(); // Stop active slides
                            this.momentum.reset();   // Clear velocity history
                        }
                        this._jumpDetectedThisDrag = false; // Reset jump detection for this drag
                        
                        this.selectedObject = clickedObject;
                        this.selectedObjects = [clickedObject];
                        
                        // ENHANCED: If selecting a merged UL, add ALL links in the merge chain to selection
                        if (clickedObject.type === 'unbound' && (clickedObject.mergedWith || clickedObject.mergedInto)) {
                            const allMergedLinks = this.getAllMergedLinks(clickedObject);
                            allMergedLinks.forEach(link => {
                                if (!this.selectedObjects.includes(link)) {
                                    this.selectedObjects.push(link);
                                }
                            });
                        }
                        
                        this.multiSelectMode = false;
                        this.currentMode = 'select';
                        this.updateModeIndicator();
                        
                        // INSTANT FEEDBACK: Draw immediately for link selection
                        if (clickedObject.type === 'link' || clickedObject.type === 'unbound') {
                            this.draw();
                        }
                        // All links are now unbound with TPs - they can be dragged
                        {
                            // CRITICAL FIX: Don't set dragging=true until AFTER offset is calculated!
                            // Collision detection and momentum might check this.dragging flag
                            
                            // FIXED: Handle unbound links specially (they don't have x,y)
                            if (clickedObject.type === 'unbound') {
                                // Momentum already stopped above - safe to proceed
                                // Calculate offset from center point
                                const centerX = (clickedObject.start.x + clickedObject.end.x) / 2;
                                const centerY = (clickedObject.start.y + clickedObject.end.y) / 2;
                                this.dragStart = { x: pos.x - centerX, y: pos.y - centerY };
                                this.unboundLinkInitialPos = {
                                    startX: clickedObject.start.x,
                                    startY: clickedObject.start.y,
                                    endX: clickedObject.end.x,
                                    endY: clickedObject.end.y
                                };
                            } else {
                                // For devices and text objects (they have x/y properties)
                                // Capture position immediately while momentum is stopped
                                const objX = clickedObject.x;
                                const objY = clickedObject.y;
                                
                                // CRITICAL: Calculate offset from click point to object center
                                // This ensures the object doesn't jump when dragging starts
                                this.dragStart = { x: pos.x - objX, y: pos.y - objY };
                                this.unboundLinkInitialPos = null;
                                
                                // Store initial position for text objects (helps with rotation transform issues)
                                if (clickedObject.type === 'text') {
                                    this.textDragInitialPos = {
                                        textX: objX,
                                        textY: objY,
                                        mouseX: pos.x,
                                        mouseY: pos.y,
                                        offsetX: this.dragStart.x,
                                        offsetY: this.dragStart.y
                                    };
                                }
                                
                                // CRITICAL FIX: Update placement tracking for SELECT mode too!
                                if (this.debugger) {
                                    const offsetMag = Math.sqrt(this.dragStart.x * this.dragStart.x + this.dragStart.y * this.dragStart.y);
                                    const deviceRadius = clickedObject.radius || 30;
                                    const maxOffset = deviceRadius + 50;
                                    const deviceGrid = this.worldToGrid({ x: objX, y: objY });
                                    const mouseGrid = this.worldToGrid(pos);
                                    const inputSource = this._lastInputType || 'mouse';
                                    const icon = inputSource === 'trackpad' ? '🖐️' : inputSource === 'mouse' ? '🖱️' : '👆';
                                    
                                    const clickTrackDiv = document.getElementById('debug-click-track');
                                    if (clickTrackDiv) {
                                        const objLabel = clickedObject.type === 'text' ? `Text: "${clickedObject.text}"` : (clickedObject.label || 'Device');
                                        clickTrackDiv.innerHTML = `
                                            <span style="color: #9b59b6; font-weight: bold;">${icon} ${clickedObject.type.toUpperCase()} GRABBED (SELECT MODE):</span><br>
                                            <span style="color: #ffd700; font-weight: bold;">${objLabel}</span><br>
                                            <br>
                                            <span style="color: #64c8ff; font-weight: bold;">📸 OBJECT POSITION:</span><br>
                                            World: <span style="color: #0ff;">(${objX.toFixed(1)}, ${objY.toFixed(1)})</span><br>
                                            Grid: <span style="color: #0ff;">(${Math.round(deviceGrid.x)}, ${Math.round(deviceGrid.y)})</span><br>
                                            <br>
                                            <span style="color: #fa0; font-weight: bold;">🖱️ MOUSE POSITION:</span><br>
                                            World: <span style="color: #fa0;">(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)})</span><br>
                                            Grid: <span style="color: #fa0;">(${Math.round(mouseGrid.x)}, ${Math.round(mouseGrid.y)})</span><br>
                                            <br>
                                            <span style="color: #667eea; font-weight: bold;">📏 DRAG OFFSET:</span><br>
                                            Offset: <span style="color: ${offsetMag > maxOffset ? '#f00' : '#0f0'};">(${this.dragStart.x.toFixed(1)}, ${this.dragStart.y.toFixed(1)})</span><br>
                                            Magnitude: <span style="color: ${offsetMag > maxOffset ? '#f00' : '#0f0'};">${offsetMag.toFixed(1)}px</span><br>
                                            ${offsetMag > maxOffset ? `<span style="color: #f00;">🚨 OFFSET TOO LARGE!</span><br>` : ''}
                                            <br>
                                            <span style="color: #888; font-size: 9px;">
                                                Input: ${inputSource.toUpperCase()}<br>
                                                Code: handleMouseDown() [SELECT mode]
                                            </span>
                                        `;
                                    }
                                }
                            }
                            
                            // NOW set dragging=true AFTER offset is safely calculated
                            // CRITICAL: Clear tap tracking when dragging starts to prevent drag-release from being mistaken for double-tap
                            this.lastTapTime = 0;
                            this._lastTapDevice = null;
                            this._lastTapPos = null;
                            this._lastTapStartTime = 0;
                            
                            // Track starting position for tap vs drag detection (momentum fix)
                            if (clickedObject.x !== undefined && clickedObject.y !== undefined) {
                                this.dragStartPos = { x: clickedObject.x, y: clickedObject.y };
                            } else {
                                this.dragStartPos = null;
                            }
                            
                            // DELAY setting dragging=true to prevent race condition with collision physics
                            // The physics loop might move the object before this function finishes
                            // By delaying, we ensure we have a clean state
                            requestAnimationFrame(() => {
                            this.dragging = true;
                            });
                        }
                        
                        this.updatePropertiesPanel();
                        this.draw();
                    }
                } else {
                    // Clicked on empty space while items are selected
                    // Check if this is a tap or drag - set up timer and start position
                    this.selectionRectStart = pos;
                    this.marqueeTimer = setTimeout(() => {
                        // Timer expired - it was a tap, not a drag
                        // Clear selection and go to base mode
                        this.selectedObjects = [];
                        this.selectedObject = null;
                        this.multiSelectMode = false;
                        this.backgroundClickCount = 0;
                        this.setMode('base');
                        this.updatePropertiesPanel();
                        this.draw();
                    }, 10); // 10ms to detect if it's a drag
                    return;
                }
            } else {
                // Single select mode OR base mode with selected items
                // Check if clicking on one of the already selected objects
                if (clickedObject && this.selectedObjects.length > 1 && this.selectedObjects.includes(clickedObject)) {
                    // Clicked on a selected object - drag ALL selected objects
                    // CRITICAL FIX: Stop ALL momentum/slides FIRST before capturing positions!
                    if (this.momentum) {
                        this.momentum.stopAll(); // Stop active slides
                        this.momentum.reset();   // Clear velocity history
                    }
                    this._jumpDetectedThisDrag = false; // Reset jump detection for this drag
                    
                    this.saveState(); // Save before moving
                    // CRITICAL FIX: Calculate all positions BEFORE setting dragging=true!
                    // For multi-select drag, store ABSOLUTE mouse position (not offset)
                    // This is used in handleMouseMove to calculate delta: dx = pos.x - dragStart.x
                    this.dragStart = { x: pos.x, y: pos.y };
                    this.multiSelectInitialPositions = this.selectedObjects
                        // No need to filter links - all links are now unbound with TPs
                        .map(obj => {
                            const pos = {
                                id: obj.id,
                                x: obj.x, 
                                y: obj.y
                            };
                            // For unbound links, also store endpoints
                            if (obj.type === 'unbound') {
                                pos.startX = obj.start.x;
                                pos.startY = obj.start.y;
                                pos.endX = obj.end.x;
                                pos.endY = obj.end.y;
                            }
                            return pos;
                        });
                    
                    // NOW set dragging=true AFTER all positions are safely captured
                    // Track starting position for tap vs drag detection (momentum fix)
                    this.dragStartPos = null; // Background drag uses different tracking
                    
                    this.dragging = true;
                    this.updatePropertiesPanel();
                    return;
                }

                // Normal selection - clicking device enters Select mode
                if (clickedObject) {
                    // Check if clicking on ALREADY SELECTED device
                    const alreadySelected = this.selectedObject === clickedObject && this.selectedObjects.includes(clickedObject);
                    
                    // ULTRA-CRITICAL: Stop ALL momentum immediately AND lock position!
                    if (this.momentum) {
                        this.momentum.stopAll(); // Stop all active slides
                        this.momentum.reset();
                    }
                    
                    // Set a flag to prevent ANY momentum/collision from modifying this device
                    this._lockingDeviceForGrab = true;
                    this._lockedDevice = clickedObject;
                    this._jumpDetectedThisDrag = false; // Reset jump detection for this drag
                    
                    // CRITICAL: Capture object position NOW, before any modifications
                    // Handle different object types (devices/text have x,y; unbound links have start/end)
                    let devicePosSnapshot;
                    
                    if (clickedObject.x !== undefined && clickedObject.y !== undefined) {
                        // Device or text - store as primitive values
                        devicePosSnapshot = {
                            x: Number(clickedObject.x),
                            y: Number(clickedObject.y)
                        };
                    } else if (clickedObject.type === 'unbound') {
                        // Unbound link - use center point
                        const centerX = (clickedObject.start.x + clickedObject.end.x) / 2;
                        const centerY = (clickedObject.start.y + clickedObject.end.y) / 2;
                        devicePosSnapshot = {
                            x: Number(centerX),
                            y: Number(centerY)
                        };
                    }
                    
                    // PARANOID CHECK: Verify position is valid
                    if (this.debugger && devicePosSnapshot) {
                        if (isNaN(devicePosSnapshot.x) || isNaN(devicePosSnapshot.y)) {
                            this.debugger.logError(`🚨 CRITICAL: Object position is NaN!`);
                            this.debugger.logError(`   Object type: ${clickedObject.type}`);
                        } else {
                            this.debugger.logInfo(`✓ Initial snapshot: ${clickedObject.type} at (${devicePosSnapshot.x.toFixed(2)}, ${devicePosSnapshot.y.toFixed(2)})`);
                        }
                    }
                    
                    if (!alreadySelected) {
                        // DOUBLE-TAP DETECTION: Check if this is a double-tap on a device
                        if (clickedObject.type === 'device') {
                            const now = Date.now();
                            const timeSinceLastTap = now - this.lastTapTime;
                            const lastTapWasOnDevice = this._lastTapDevice && this._lastTapDevice === clickedObject;
                            
                            // If this is a quick double-tap on the same device, enter link mode
                            if (lastTapWasOnDevice && timeSinceLastTap < this.doubleTapDelay) {
                                // Cancel any device placement
                                if (this.placingDevice) {
                                    this.placingDevice = null;
                                }
                                
                                // Enter link mode with this device
                                this.setMode('link');
                                this.linking = true;
                                this.linkStart = clickedObject;
                                
                                if (this.debugger) {
                                    const gridPos = this.worldToGrid({ x: clickedObject.x, y: clickedObject.y });
                                    this.debugger.logSuccess(`👆👆 Double-tap on device: LINK mode from ${clickedObject.label || 'Device'}`);
                                    this.debugger.logInfo(`Device: ${clickedObject.label} at Grid(${Math.round(gridPos.x)}, ${Math.round(gridPos.y)})`);
                                    this.debugger.logInfo(`Time between taps: ${timeSinceLastTap}ms`);
                                }
                                
                                this.lastTapTime = 0; // Reset
                                this._lastTapDevice = null;
                                this._lastTapPos = null; // Reset position
                                this._lastTapStartTime = 0; // Reset
                                this.draw();
                                return;
                            }
                            
                            // Store this tap for potential double-tap detection (including position for movement tolerance)
                            const tapNow = Date.now();
                            this.lastTapTime = tapNow;
                            this._lastTapStartTime = tapNow; // Track when this tap started
                            this._lastTapDevice = clickedObject;
                            this._lastTapPos = { x: pos.x, y: pos.y }; // Store position to handle slight movement
                        }
                        
                        // New selection - Enter Select mode and select this device
                        this.currentMode = 'select';
                        this.updateModeIndicator(); // Show SELECT MODE
                        this.selectedObject = clickedObject;
                        this.selectedObjects = [clickedObject];
                        
                        // ENHANCED: If selecting a merged UL, add ALL links in the merge chain to selection
                        if (clickedObject.type === 'unbound' && (clickedObject.mergedWith || clickedObject.mergedInto)) {
                            const allMergedLinks = this.getAllMergedLinks(clickedObject);
                            allMergedLinks.forEach(link => {
                                if (!this.selectedObjects.includes(link)) {
                                    this.selectedObjects.push(link);
                                }
                            });
                        }
                        
                        // ENHANCED: For Quick Links, add to selection immediately
                        if (clickedObject.type === 'link') {
                            // Quick Links are simple - just select immediately
                        }
                        
                        // DIAGNOSTIC: Log selection time for comparing with handle operations
                        if (this.debugger) {
                            const selectionTime = Date.now();
                            const objType = clickedObject.type === 'device' ? 'DEVICE' : 
                                          clickedObject.type === 'link' ? 'QUICK LINK' : 
                                          clickedObject.type === 'unbound' ? 'UL/BUL' : 'OBJECT';
                            this.debugger.logInfo(`🎯 ${objType} SELECTED at ${selectionTime}: ${clickedObject.label || clickedObject.id}`);
                            this.debugger.logInfo(`   Selection timestamp: ${new Date(selectionTime).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 })}`);
                            this.debugger.logInfo(`   Mode: ${this.currentMode}, Tool: ${this.currentTool}`);
                            if (clickedObject.type === 'device') {
                            this.debugger.logInfo(`   Handles WILL be visible on next draw`);
                            this.debugger.logInfo(`   ⚠️ Handles NOT functional yet - release mouse first!`);
                            }
                            // Store for comparison
                            clickedObject._selectionTime = selectionTime;
                            clickedObject._lastDrawTime = null; // Mark that we need a draw to show handles
                            clickedObject._mouseReleasedAfterSelection = false; // NOT released yet - block handles until mouseup
                        }
                        
                        // CRITICAL: INSTANT draw for immediate visual feedback (especially for links)
                        this.draw();
                        
                        // ENHANCED: For links, force immediate second draw to ensure highlight is visible
                        if (clickedObject.type === 'link' || clickedObject.type === 'unbound') {
                            requestAnimationFrame(() => this.draw());
                        }
                        
                        // Move selected object to top layer (last in array = drawn last = on top)
                        if (clickedObject.type === 'device' || clickedObject.type === 'text') {
                            const index = this.objects.indexOf(clickedObject);
                            if (index > -1) {
                                this.objects.splice(index, 1);
                                this.objects.push(clickedObject);
                            }
                        }
                        
                        // Save state AFTER momentum reset
                        this.saveState();
                        
                        // RE-CAPTURE: Position might have changed during saveState
                        const beforeRecapture = `(${devicePosSnapshot.x.toFixed(2)}, ${devicePosSnapshot.y.toFixed(2)})`;
                        const beforeX = devicePosSnapshot.x;
                        const beforeY = devicePosSnapshot.y;
                        
                        // Recalculate position based on object type
                        if (clickedObject.x !== undefined && clickedObject.y !== undefined) {
                            devicePosSnapshot.x = clickedObject.x;
                            devicePosSnapshot.y = clickedObject.y;
                        } else if (clickedObject.type === 'unbound') {
                            const centerX = (clickedObject.start.x + clickedObject.end.x) / 2;
                            const centerY = (clickedObject.start.y + clickedObject.end.y) / 2;
                            devicePosSnapshot.x = centerX;
                            devicePosSnapshot.y = centerY;
                        }
                        
                        const afterRecapture = `(${devicePosSnapshot.x.toFixed(2)}, ${devicePosSnapshot.y.toFixed(2)})`;
                        
                        // Compare BEFORE vs AFTER
                        if (this.debugger && (Math.abs(devicePosSnapshot.x - beforeX) > 0.1 || Math.abs(devicePosSnapshot.y - beforeY) > 0.1)) {
                            this.debugger.logWarning(`🔄 Position changed during saveState: ${beforeRecapture} → ${afterRecapture}`);
                        }
                    } else {
                        // CRITICAL: For re-grab, detect if object moved since release!
                        const beforeSave = devicePosSnapshot ? `(${devicePosSnapshot.x.toFixed(2)}, ${devicePosSnapshot.y.toFixed(2)})` : 'N/A';
                        
                        // Store pre-grab position for jump detection (handle all object types)
                        let preGrabPos;
                        if (clickedObject.x !== undefined && clickedObject.y !== undefined) {
                            preGrabPos = { x: clickedObject.x, y: clickedObject.y };
                        } else if (clickedObject.type === 'unbound') {
                            const centerX = (clickedObject.start.x + clickedObject.end.x) / 2;
                            const centerY = (clickedObject.start.y + clickedObject.end.y) / 2;
                            preGrabPos = { x: centerX, y: centerY };
                        }
                        
                        this.saveState();
                        
                        // Recalculate after saveState
                        let afterGrabPos;
                        if (clickedObject.x !== undefined && clickedObject.y !== undefined) {
                            afterGrabPos = { x: clickedObject.x, y: clickedObject.y };
                        } else if (clickedObject.type === 'unbound') {
                            const centerX = (clickedObject.start.x + clickedObject.end.x) / 2;
                            const centerY = (clickedObject.start.y + clickedObject.end.y) / 2;
                            afterGrabPos = { x: centerX, y: centerY };
                        }
                        
                        const afterSave = afterGrabPos ? `(${afterGrabPos.x.toFixed(2)}, ${afterGrabPos.y.toFixed(2)})` : 'N/A';
                        
                        // Update snapshot if we have values
                        if (afterGrabPos && devicePosSnapshot) {
                            devicePosSnapshot.x = afterGrabPos.x;
                            devicePosSnapshot.y = afterGrabPos.y;
                        }
                        
                        if (this.debugger) {
                            if (preGrabPos && afterGrabPos && beforeSave !== afterSave) {
                                this.debugger.logWarning(`🔄 RE-GRAB: Position changed during saveState: ${beforeSave} → ${afterSave}`);
                            }
                            
                            // Log re-grab event with position comparison
                            const objLabel = clickedObject.label || (clickedObject.type === 'unbound' ? 'Unbound Link' : 'Object');
                            this.debugger.logSuccess(`🔄 RE-GRAB: ${objLabel} clicked again (already selected)`);
                            if (preGrabPos) {
                                this.debugger.logInfo(`   Pre-grab: (${preGrabPos.x.toFixed(2)}, ${preGrabPos.y.toFixed(2)})`);
                            }
                            this.debugger.logInfo(`   Mouse: (${pos.x.toFixed(2)}, ${pos.y.toFixed(2)})`);
                        }
                    }
                    
                    // Update properties panel but DON'T set dragging=true yet!
                    this.updatePropertiesPanel();
                    
                    // ENHANCED: For unbound links, store initial endpoint positions for body dragging
                    if (clickedObject.type === 'unbound' && !this.stretchingLink) {
                        // Momentum already stopped at top of BASE mode section - safe to capture positions
                        this.unboundLinkInitialPos = {
                            startX: clickedObject.start.x,
                            startY: clickedObject.start.y,
                            endX: clickedObject.end.x,
                            endY: clickedObject.end.y
                        };
                        
                        // ENHANCED: Also store initial position for merged child link
                        if (clickedObject.mergedWith) {
                            const childLink = this.objects.find(o => o.id === clickedObject.mergedWith.linkId);
                            if (childLink) {
                                this._mergedChildInitialPos = {
                                    startX: childLink.start.x,
                                    startY: childLink.start.y,
                                    endX: childLink.end.x,
                                    endY: childLink.end.y,
                                    connectionX: clickedObject.mergedWith.connectionPoint.x,
                                    connectionY: clickedObject.mergedWith.connectionPoint.y
                                };
                            }
                        } else if (clickedObject.mergedInto) {
                            const parentLink = this.objects.find(o => o.id === clickedObject.mergedInto.parentId);
                            if (parentLink) {
                                this._mergedParentInitialPos = {
                                    startX: parentLink.start.x,
                                    startY: parentLink.start.y,
                                    endX: parentLink.end.x,
                                    endY: parentLink.end.y,
                                    connectionX: clickedObject.mergedInto.connectionPoint.x,
                                    connectionY: clickedObject.mergedInto.connectionPoint.y
                                };
                            }
                        }
                        
                        this._unboundBodyDragLogged = false; // Reset log flag
                        
                        // For unbound links, dragStart stores the initial MOUSE position (not offset)
                        // This is used differently in handleMouseMove for UL body dragging
                        this.dragStart = { x: pos.x, y: pos.y };
                        this.dragStartTime = Date.now();
                        this.lastDragPos = { x: pos.x, y: pos.y };
                        this.lastDragTime = Date.now();
                        
                        // Track starting position for tap vs drag detection (momentum fix)
                        this.dragStartPos = { x: (clickedObject.start.x + clickedObject.end.x) / 2, 
                                             y: (clickedObject.start.y + clickedObject.end.y) / 2 };
                        
                        // NOW set dragging=true AFTER offset is calculated
                        this.dragging = true;
                        
                        if (this.debugger) {
                            const inputSource = this._lastInputType || 'mouse';
                            const icon = inputSource === 'trackpad' ? '🖐️' : inputSource === 'mouse' ? '🖱️' : '👆';
                            this.debugger.logSuccess(`${icon} Unbound link grabbed for body dragging via ${inputSource.toUpperCase()}`);
                            this.debugger.logInfo(`📍 Start: (${clickedObject.start.x.toFixed(1)}, ${clickedObject.start.y.toFixed(1)}), End: (${clickedObject.end.x.toFixed(1)}, ${clickedObject.end.y.toFixed(1)})`);
                            this.debugger.logInfo(`📍 Mouse: (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}) - dragStart stores POSITION, not offset`);
                        }
                        
                        // Skip the rest - body dragging uses different logic
                        this.draw();
                        return;
                    } // Removed old check for type === 'link' - all links are now unbound with TPs
                    
                    if (false) { // Disabled block
                        this.dragging = false;
                        this.unboundLinkInitialPos = null;
                        
                        if (this.debugger) {
                            this.debugger.logInfo(`📍 Regular link selected - not draggable (bound to devices)`);
                        }
                        
                        this.draw();
                        return;
                    } else {
                        this.unboundLinkInitialPos = null;
                        
                        // ULTRA-CRITICAL: FINAL position re-capture right before offset calculation!
                        // Use the MOST RECENT position possible to minimize race window
                        const finalPosBeforeOffset = {
                            x: clickedObject.x,
                            y: clickedObject.y
                        };
                        
                        // Update snapshot to final position
                        devicePosSnapshot.x = finalPosBeforeOffset.x;
                        devicePosSnapshot.y = finalPosBeforeOffset.y;
                        
                        // Safety check for devicePosSnapshot
                        if (!devicePosSnapshot) {
                            console.error('devicePosSnapshot is undefined!');
                            devicePosSnapshot = { x: clickedObject.x || 0, y: clickedObject.y || 0 };
                        }
                        
                        const objStartX = devicePosSnapshot.x;
                        const objStartY = devicePosSnapshot.y;
                        
                        // Verify snapshot is valid
                        if (this.debugger && objStartX !== undefined && objStartY !== undefined) {
                            this.debugger.logSuccess(`✓ Using FINAL snapshot for offset calculation`);
                            this.debugger.logInfo(`   Snapshot: (${objStartX.toFixed(2)}, ${objStartY.toFixed(2)})`);
                            this.debugger.logInfo(`   Mouse: (${pos.x.toFixed(2)}, ${pos.y.toFixed(2)})`);
                        }
                        
                        // CRITICAL: Calculate offset from SNAPSHOT position (objStartX/Y), NOT current position
                        // This prevents race condition where collision detection modifies device position during setup
                        // The snapshot was taken BEFORE any physics could run, so it's stable
                        let calculatedOffsetX = pos.x - objStartX;
                        let calculatedOffsetY = pos.y - objStartY;
                        
                        // CRITICAL VALIDATION: Offset should be reasonable (within device radius + some margin)
                        const offsetMag = Math.sqrt(calculatedOffsetX * calculatedOffsetX + calculatedOffsetY * calculatedOffsetY);
                        const deviceRadius = clickedObject.radius || 50; // Default to 50 for unbound links
                        const maxReasonableOffset = deviceRadius + 100; // Device radius + 100px margin
                        
                        if (offsetMag > maxReasonableOffset) {
                            // Offset is unreasonable - likely coordinate space mismatch or bug
                            if (this.debugger) {
                                // Get current position safely (handle unbound links)
                                let currentPosStr;
                                if (clickedObject.type === 'unbound') {
                                    const cx = (clickedObject.start.x + clickedObject.end.x) / 2;
                                    const cy = (clickedObject.start.y + clickedObject.end.y) / 2;
                                    currentPosStr = `(${cx.toFixed(2)}, ${cy.toFixed(2)})`;
                                } else {
                                    currentPosStr = `(${clickedObject.x.toFixed(2)}, ${clickedObject.y.toFixed(2)})`;
                                }
                                
                                this.debugger.logError(`🚨 CATASTROPHIC: Invalid offset detected!`);
                                this.debugger.logError(`   Offset magnitude: ${offsetMag.toFixed(0)}px (max should be ${maxReasonableOffset}px)`);
                                this.debugger.logError(`   Snapshot: (${objStartX.toFixed(2)}, ${objStartY.toFixed(2)})`);
                                this.debugger.logError(`   Current: ${currentPosStr}`);
                                this.debugger.logError(`   Mouse: (${pos.x.toFixed(2)}, ${pos.y.toFixed(2)})`);
                                this.debugger.logError(`   Calculated offset: (${calculatedOffsetX.toFixed(2)}, ${calculatedOffsetY.toFixed(2)})`);
                                this.debugger.logWarning(`   → Clamping offset to prevent jump`);
                            }
                            
                            // Clamp the offset to a reasonable maximum but keep the direction
                            const maxOffset = deviceRadius + 50;
                            const scale = maxOffset / offsetMag;
                            calculatedOffsetX = calculatedOffsetX * scale;
                            calculatedOffsetY = calculatedOffsetY * scale;
                            
                            if (this.debugger) {
                                this.debugger.logWarning(`   → Clamped offset to (${calculatedOffsetX.toFixed(2)}, ${calculatedOffsetY.toFixed(2)}) to prevent jump`);
                            }
                        }
                        
                        // CRITICAL: Always store as OFFSET from snapshot position, never as mouse position!
                        // This ensures offset is calculated from stable snapshot, not potentially moved current position
                        this.dragStart = { 
                            x: calculatedOffsetX,  // Offset from SNAPSHOT position (stable, prevents race condition)
                            y: calculatedOffsetY
                        };
                        this.dragStartTime = Date.now();
                        this.lastDragPos = { x: objStartX, y: objStartY };
                        this.lastDragTime = Date.now();
                        
                        // Debug: Log grab details with ENHANCED diagnostics
                        if (this.debugger) {
                        const grabType = alreadySelected ? 're-grabbed (already selected)' : 'grabbed (new selection)';
                        const inputSource = this._lastInputType || 'mouse';
                        const icon = inputSource === 'trackpad' ? '🖐️' : inputSource === 'mouse' ? '🖱️' : '👆';
                        
                        // Get current position safely (handle unbound links)
                        let currentX, currentY;
                        if (clickedObject.type === 'unbound') {
                            currentX = (clickedObject.start.x + clickedObject.end.x) / 2;
                            currentY = (clickedObject.start.y + clickedObject.end.y) / 2;
                        } else {
                            currentX = clickedObject.x;
                            currentY = clickedObject.y;
                        }
                        
                        const objLabel = clickedObject.label || (clickedObject.type === 'unbound' ? 'Unbound Link' : 'Device');
                        this.debugger.logInfo(`${icon} ${objLabel} ${grabType} via ${inputSource.toUpperCase()}`);
                        this.debugger.logInfo(`📍 SNAPSHOT: (${objStartX.toFixed(2)}, ${objStartY.toFixed(2)})`);
                        this.debugger.logInfo(`📍 CURRENT:  (${currentX.toFixed(2)}, ${currentY.toFixed(2)})`);
                        this.debugger.logInfo(`📍 MOUSE:    (${pos.x.toFixed(2)}, ${pos.y.toFixed(2)})`);
                        this.debugger.logInfo(`📍 OFFSET:   (${this.dragStart.x.toFixed(2)}, ${this.dragStart.y.toFixed(2)})`);
                        const finalOffsetMag = Math.sqrt(this.dragStart.x * this.dragStart.x + this.dragStart.y * this.dragStart.y);
                        this.debugger.logInfo(`📍 OFFSET MAG: ${finalOffsetMag.toFixed(1)}px (max: ${maxReasonableOffset}px)`);
                        this.debugger.logInfo(`📍 SELECTED OBJECTS COUNT: ${this.selectedObjects.length}`);
                        
                        // CRITICAL: Check if object moved after snapshot
                        const movedX = Math.abs(currentX - objStartX);
                        const movedY = Math.abs(currentY - objStartY);
                        const movedMag = Math.sqrt(movedX * movedX + movedY * movedY);
                        
                        if (movedMag > 0.5) {
                            this.debugger.logWarning(`⚠️ Device moved ${movedMag.toFixed(1)}px after snapshot (using snapshot to prevent jump)`);
                            this.debugger.logInfo(`   Movement: Δx=${movedX.toFixed(2)}, Δy=${movedY.toFixed(2)}`);
                            this.debugger.logInfo(`   ✓ Offset calculated from SNAPSHOT (not current position) to prevent race condition`);
                        }
                            
                            // CRITICAL FIX: Update PLACEMENT TRACKING panel with grab details!
                            const clickTrackDiv = document.getElementById('debug-click-track');
                            if (clickTrackDiv) {
                                const deviceGrid = this.worldToGrid({ x: objStartX, y: objStartY });
                                const mouseGrid = this.worldToGrid(pos);
                                const currentGrid = this.worldToGrid({ x: clickedObject.x, y: clickedObject.y });
                                
                                // Calculate initial relative position
                                const initialRelative = { x: pos.x - objStartX, y: pos.y - objStartY };
                                const initialRelMag = Math.sqrt(initialRelative.x * initialRelative.x + initialRelative.y * initialRelative.y);
                                
                                clickTrackDiv.innerHTML = `
                                    <span style="color: ${alreadySelected ? '#f39c12' : '#0f0'}; font-weight: bold;">${icon} ${alreadySelected ? '🔄 RE-GRABBED' : 'GRABBED'}:</span><br>
                                    <span style="color: #ffd700; font-weight: bold;">${clickedObject.label || 'Device'}</span> (${clickedObject.deviceType || 'device'})<br>
                                    ${alreadySelected ? `<span style="color: #fa0; font-size: 10px;">⚠️ Device was already selected - testing re-grab</span><br>` : ''}
                                    <br>
                                    <span style="color: #64c8ff; font-weight: bold;">📸 SNAPSHOT POSITION:</span><br>
                                    World: <span style="color: #0ff;">(${objStartX.toFixed(1)}, ${objStartY.toFixed(1)})</span><br>
                                    Grid: <span style="color: #0ff;">(${Math.round(deviceGrid.x)}, ${Math.round(deviceGrid.y)})</span><br>
                                    <br>
                                    <span style="color: #fa0; font-weight: bold;">🖱️ MOUSE POSITION:</span><br>
                                    World: <span style="color: #fa0;">(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)})</span><br>
                                    Grid: <span style="color: #fa0;">(${Math.round(mouseGrid.x)}, ${Math.round(mouseGrid.y)})</span><br>
                                    <br>
                                    <span style="color: #667eea; font-weight: bold;">📏 RELATIVE (Mouse - Device):</span><br>
                                    Delta: <span style="color: #667eea; font-weight: bold;">(${initialRelative.x.toFixed(1)}, ${initialRelative.y.toFixed(1)})</span><br>
                                    Distance: <span style="color: #667eea;">${initialRelMag.toFixed(1)}px</span><br>
                                    <br>
                                    <span style="color: ${movedMag > 0.5 ? '#f00' : '#0f0'}; font-weight: bold;">📍 CURRENT DEVICE:</span><br>
                                    World: <span style="color: ${movedMag > 0.5 ? '#f00' : '#0f0'};">(${clickedObject.x.toFixed(1)}, ${clickedObject.y.toFixed(1)})</span><br>
                                    Grid: <span style="color: ${movedMag > 0.5 ? '#f00' : '#0f0'};">(${Math.round(currentGrid.x)}, ${Math.round(currentGrid.y)})</span><br>
                                    ${movedMag > 0.5 ? `<span style="color: #f00;">⚠️ Moved ${movedMag.toFixed(1)}px from snapshot!</span><br>` : ''}
                                    <br>
                                    <span style="color: ${offsetMag > maxReasonableOffset ? '#f00' : '#0f0'}; font-weight: bold;">📐 CALCULATED OFFSET:</span><br>
                                    Offset: <span style="color: ${offsetMag > maxReasonableOffset ? '#f00' : '#0f0'};">(${this.dragStart.x.toFixed(1)}, ${this.dragStart.y.toFixed(1)})</span><br>
                                    Magnitude: <span style="color: ${offsetMag > maxReasonableOffset ? '#f00' : '#0f0'};">${offsetMag.toFixed(1)}px</span> (max: ${maxReasonableOffset}px)<br>
                                    <div style="padding: 4px; background: ${offsetMag > maxReasonableOffset ? 'rgba(231, 76, 60, 0.3)' : 'rgba(39, 174, 96, 0.2)'}; border-radius: 3px; border-left: 3px solid ${offsetMag > maxReasonableOffset ? '#e74c3c' : '#27ae60'}; margin-top: 4px;">
                                        <span style="color: ${offsetMag > maxReasonableOffset ? '#f00' : '#0f0'}; font-weight: bold;">
                                            ${offsetMag > maxReasonableOffset ? '🚨 OFFSET TOO LARGE - JUMP WILL OCCUR!' : '✓ Offset Valid - Drag will be smooth'}
                                        </span><br>
                                        ${offsetMag > maxReasonableOffset ? `
                                        <span style="color: #f00; font-size: 9px;">This means the snapshot position is WRONG!</span><br>
                                        <span style="color: #f00; font-size: 9px;">Device was probably at (0, 0) when captured</span><br>
                                        ` : ''}
                                    </div>
                                    <br>
                                    <span style="color: #888; font-size: 9px;">
                                        Grab Type: ${grabType}<br>
                                        Input: ${inputSource.toUpperCase()}<br>
                                        ${alreadySelected ? 'Test: RE-GRAB scenario (watch for jump!)<br>' : ''}
                                        Code: handleMouseDown() [BASE mode]
                                    </span>
                                `;
                            }
                        }
                        
                        // FINAL STEP: Set dragging=true AFTER all calculations are complete
                        // This prevents momentum/collision from running between offset calculation and first move
                        // CRITICAL: Clear tap tracking when dragging starts to prevent drag-release from being mistaken for double-tap
                        this.lastTapTime = 0;
                        this._lastTapDevice = null;
                        this._lastTapPos = null;
                        this._lastTapStartTime = 0;
                        
                        // Track starting position for tap vs drag detection (momentum fix)
                        if (clickedObject.x !== undefined && clickedObject.y !== undefined) {
                            this.dragStartPos = { x: clickedObject.x, y: clickedObject.y };
                        } else {
                            this.dragStartPos = null;
                        }
                        
                        this.dragging = true;
                        
                        if (this.debugger) {
                            this.debugger.logSuccess(`✓ Drag initialized - dragging flag set AFTER offset calculation`);
                            
                            // RESET placement tracking data on new grab
                            const grabGrid = this.worldToGrid({ x: objStartX, y: objStartY });
                            const mouseGrid = this.worldToGrid(pos);
                            
                            // Clear old data and start fresh
                            this.debugger.placementData = {
                                deviceLabel: clickedObject.label || 'Device',
                                deviceType: clickedObject.deviceType || 'device',
                                grabPosition: {
                                    x: objStartX,
                                    y: objStartY,
                                    gridX: Math.round(grabGrid.x),
                                    gridY: Math.round(grabGrid.y)
                                },
                                mouseGrab: { x: pos.x, y: pos.y },
                                offset: { ...this.dragStart },
                                timestamp: new Date().toLocaleTimeString(),
                                inputType: this._lastInputType || 'mouse',
                                releasePosition: null, // Will be filled on mouseUp
                                mouseRelease: null,
                                distance: null
                            };
                        }
                    }
                    
                    // Clear the position lock flag - drag setup is complete
                    this._lockingDeviceForGrab = false;
                    this._lockedDevice = null;
                    
                    this.draw();
                } else {
                    // Clicking empty space / background
                    
                    // Log background click to debugger
                    if (this.debugger) {
                        const gridPos = this.worldToGrid(pos);
                        const clickTrackDiv = document.getElementById('debug-click-track');
                        if (clickTrackDiv) {
                            clickTrackDiv.innerHTML = `
                                <span style="color: #0ff;">🖱️ Background Click:</span><br>
                                World: (${Math.round(pos.x)}, ${Math.round(pos.y)})<br>
                                Grid: (${Math.round(gridPos.x)}, ${Math.round(gridPos.y)})<br>
                                Zoom: ${Math.round(this.zoom * 100)}%<br>
                                <span style="color: #888; font-size: 9px;">Code: handleMouseDown() [964]</span>
                            `;
                        }
                        // Reduced logging: Don't log every background click
                        // this.debugger.logInfo(`🖱️ Background click at Grid(${Math.round(gridPos.x)}, ${Math.round(gridPos.y)})`);
                    }
                    
                    // DOUBLE-TAP detection in link mode → return to base mode
                    if (this.currentMode === 'link') {
                        const now = Date.now();
                        const timeSinceLastTap = now - this.lastTapTime;
                        
                        if (timeSinceLastTap < this.doubleTapDelay) {
                            // Double-tap detected! Exit link mode
                            this.linking = false;
                            this.linkStart = null;
                            this.setMode('base');
                            
                            if (this.debugger) {
                                this.debugger.logSuccess(`👆👆 Double-tap detected: LINK → BASE (${timeSinceLastTap}ms)`);
                                this.debugger.logInfo(`Code: handleMouseDown() [1033-1056] - double-tap detection`);
                            }
                            
                            this.lastTapTime = 0; // Reset
                            this._lastTapDevice = null;
                            this._lastTapPos = null; // Reset position
                            this._lastTapStartTime = 0; // Reset
                            return;
                        }
                        
                        this.lastTapTime = now;
                    }
                    
                    // If marquee is active, cancel it and go to base mode on background click
                    if (this.marqueeActive) {
                        this.marqueeActive = false;
                        this.selectionRectStart = null;
                        this.selectionRectangle = null;
                        this.setMode('base');
                        return;
                    }

                    // If there are selected objects, one tap clears selection and goes to base mode
                    if (this.selectedObjects.length > 0) {
                        // Check if this is a drag (will be detected in handleMouseMove)
                        this.selectionRectStart = pos;
                        this.marqueeTimer = setTimeout(() => {
                            // Timer expired - it was a tap, not a drag
                            // Clear selection and go to base mode
                            this.selectedObjects = [];
                            this.selectedObject = null;
                        this.multiSelectMode = false;
                        this.setMode('base');
                            this.draw();
                        }, 10); // Very fast start (10ms instead of 50ms)
                        return;
                    }
                    
                    // MARQUEE SELECTION: Quick drag-to-select for smooth selection
                        this.selectionRectStart = pos;
                        this.marqueeTimer = setTimeout(() => {
                            // CRITICAL FIX: Don't start marquee if a double-click just happened (UL was created)
                            const timeSinceDoubleClick = Date.now() - (this.lastDoubleClickTime || 0);
                            if (timeSinceDoubleClick < 100) {
                                // Double-click just happened - skip marquee
                                return;
                            }
                            this.startMarqueeSelection(pos);
                    }, 10); // Very fast start (10ms instead of 50ms)
                        
                        // Also enter Base mode
                        this.setMode('base');
                }
            }
        } else if (this.currentTool === 'link') {
            // Link tool mode - stays active until right-click or mode change
            if (!clickedObject) {
                // Clicking background in link mode
                // Allow Ctrl+Drag or drag for marquee selection
                if (this.ctrlPressed) {
                    // Ctrl+click background → instant marquee (same as select mode)
                    this.startMarqueeSelection(pos);
                    
                    if (this.debugger) {
                        this.debugger.logInfo(`🔄 LINK mode: Ctrl+drag → MS (will return to LINK after)`);
                    }
                    return;
                } else {
                    // Regular background click → prepare for potential drag or double-tap
                    this.selectionRectStart = pos;
                    // Set timer for drag-to-marquee (if user drags, start marquee)
                    this.marqueeTimer = setTimeout(() => {
                        this.marqueeTimer = null;
                    }, 50);
                    return;
                }
            } else if (clickedObject.type === 'link') {
                // Clicking on a link while in link tool - just select it, stay in link mode
                this.selectedObject = clickedObject;
                this.selectedObjects = [clickedObject];
                
                // ENHANCED: If selecting a merged UL, also add the partner to selection
                if (clickedObject.type === 'unbound' && clickedObject.mergedWith) {
                    const childLink = this.objects.find(o => o.id === clickedObject.mergedWith.linkId);
                    if (childLink && !this.selectedObjects.includes(childLink)) {
                        this.selectedObjects.push(childLink);
                    }
                } else if (clickedObject.type === 'unbound' && clickedObject.mergedInto) {
                    const parentLink = this.objects.find(o => o.id === clickedObject.mergedInto.parentId);
                    if (parentLink && !this.selectedObjects.includes(parentLink)) {
                        this.selectedObjects.push(parentLink);
                    }
                }
                
                this.updatePropertiesPanel();
                // Stay in link mode, don't exit
            } else if (clickedObject.type === 'device') {
                if (!this.linking) {
                    this.linking = true;
                    this.linkStart = clickedObject;
                } else {
                    if (clickedObject !== this.linkStart) {
                        this.createLink(this.linkStart, clickedObject);
                        
                        // Continuous linking mode - chain links together
                        if (this.linkContinuousMode) {
                            // Keep linking active, use clicked device as new start
                            this.linking = true;
                            this.linkStart = clickedObject;
                        } else {
                            // Normal mode - stop linking
                    this.linking = false;
                    this.linkStart = null;
                        }
                    }
                }
            } else if (clickedObject.type === 'unbound') {
                // ENHANCED: Create a new UL and merge it with the clicked UL/BUL at the TP
                if (this.linking && this.linkStart && this.linkStart.type === 'device') {
                    // Check which endpoint was clicked
                    const clickedEndpoint = this.findUnboundLinkEndpoint(pos.x, pos.y);
                    
                    if (clickedEndpoint && !clickedEndpoint.isConnectionPoint) {
                        // This is a free TP - create new UL and merge
                        const targetUL = clickedEndpoint.link;
                        const targetEndpoint = clickedEndpoint.endpoint;
                        
                        // Check if this TP is already attached to a device
                        const alreadyAttached = (targetEndpoint === 'start' && targetUL.device1) || 
                                               (targetEndpoint === 'end' && targetUL.device2);
                        
                        if (!alreadyAttached) {
                            this.saveState(); // Save before creating
                            
                            // Get TP position
                            const tpPos = targetEndpoint === 'start' ? targetUL.start : targetUL.end;
                            
                            // Calculate device edge position
                            const angle = Math.atan2(tpPos.y - this.linkStart.y, tpPos.x - this.linkStart.x);
                            const deviceEdgeX = this.linkStart.x + Math.cos(angle) * this.linkStart.radius;
                            const deviceEdgeY = this.linkStart.y + Math.sin(angle) * this.linkStart.radius;
                            
                            // Create NEW UL from device to TP
                            const newUL = {
                                id: `link_${this.linkIdCounter++}`,
                                type: 'unbound',
                                originType: 'UL', // PRESERVE: Original link type
                                createdAt: Date.now(), // Creation timestamp for BUL order tracking
                                device1: this.linkStart.id,  // Attached to device at start
                                device2: null,  // Free at end (will merge with target TP)
                                color: '#666',
                                start: { x: deviceEdgeX, y: deviceEdgeY },
                                end: { x: tpPos.x, y: tpPos.y },  // At the TP location
                                connectedStart: null,
                                connectedEnd: null,
                                style: this.linkStyle || 'solid'
                            };
                            
                            this.objects.push(newUL);
                            
                            // Now MERGE the new UL with the target UL at the TP
                            const connectionPoint = { x: tpPos.x, y: tpPos.y };
                            
                            // Determine correct merge relationship based on existing chain
                            let parentLink = newUL;
                            let childLink = targetUL;
                            let parentFreeEndpoint = 'start'; // newUL's free end is at device (start)
                            let childFreeEndpoint = targetEndpoint === 'start' ? 'end' : 'start'; // targetUL's free end is opposite
                            
                            // Handle existing merge chains properly
                            // If targetUL is already a parent, we need to handle it specially
                            if (targetUL.mergedWith) {
                                // Target is already a parent - check if we're connecting to its free end
                                const targetFreeEnd = targetUL.mergedWith.parentFreeEnd;
                                if (targetEndpoint === targetFreeEnd) {
                                    // Connecting to target's free end - target becomes parent
                                    parentLink = targetUL;
                                    childLink = newUL;
                                    parentFreeEndpoint = targetFreeEnd === 'start' ? 'end' : 'start';
                                    childFreeEndpoint = 'start'; // newUL's start points to device after merge
                                }
                            } else if (targetUL.mergedInto) {
                                // Target is a child - we can extend from its free end
                                const targetParent = this.objects.find(o => o.id === targetUL.mergedInto.parentId);
                                if (targetParent && targetParent.mergedWith) {
                                    const targetChildFreeEnd = targetParent.mergedWith.childFreeEnd;
                                    if (targetEndpoint === targetChildFreeEnd) {
                                        // Connecting to target's free end - target becomes parent
                                        parentLink = targetUL;
                                        childLink = newUL;
                                        parentFreeEndpoint = targetChildFreeEnd === 'start' ? 'end' : 'start';
                                        childFreeEndpoint = 'start'; // newUL's start remains toward device
                                    }
                                }
                            }
                            
                            // Calculate MP number for THIS BUL (per-BUL numbering, not global)
                            // Count existing MPs in the chain this link belongs to
                            const existingChain = this.getAllMergedLinks(parentLink);
                            let existingMPCount = 0;
                            existingChain.forEach(link => {
                                if (link.mergedWith) existingMPCount++;
                            });
                            const mpNumber = existingMPCount + 1; // This is MP number 1, 2, 3... for THIS BUL
                            
                            let parentConnectionEndpoint = parentFreeEndpoint === 'start' ? 'end' : 'start';
                            let childConnectionEndpoint = childFreeEndpoint === 'start' ? 'end' : 'start';
                            
                            const detectedParentConnection = this.getLinkEndpointNearPoint(parentLink, connectionPoint);
                            const detectedChildConnection = this.getLinkEndpointNearPoint(childLink, connectionPoint);
                            
                            if (detectedParentConnection) {
                                parentConnectionEndpoint = detectedParentConnection;
                                const resolvedParentFree = this.getOppositeEndpoint(parentConnectionEndpoint);
                                if (resolvedParentFree) parentFreeEndpoint = resolvedParentFree;
                            }
                            
                            if (detectedChildConnection) {
                                childConnectionEndpoint = detectedChildConnection;
                                const resolvedChildFree = this.getOppositeEndpoint(childConnectionEndpoint);
                                if (resolvedChildFree) childFreeEndpoint = resolvedChildFree;
                            }
                            
                            // Create merge relationship - CLONE connectionPoint to avoid shared references!
                            parentLink.mergedWith = {
                                linkId: childLink.id,
                                connectionPoint: { x: connectionPoint.x, y: connectionPoint.y },
                                parentFreeEnd: parentFreeEndpoint,
                                childFreeEnd: childFreeEndpoint,
                                childStart: { x: childLink.start.x, y: childLink.start.y },
                                childEnd: { x: childLink.end.x, y: childLink.end.y },
                                parentDevice: parentFreeEndpoint === 'start' ? parentLink.device1 : parentLink.device2,
                                childDevice: childFreeEndpoint === 'start' ? childLink.device1 : childLink.device2,
                                mpCreatedAt: Date.now(), // Track MP creation time
                                mpNumber: mpNumber, // ENHANCED: Per-BUL MP numbering (1, 2, 3...)
                                connectionEndpoint: parentConnectionEndpoint,
                                childConnectionEndpoint: childConnectionEndpoint
                            };
                            
                            childLink.mergedInto = {
                                parentId: parentLink.id,
                                connectionPoint: { x: connectionPoint.x, y: connectionPoint.y }, // Clone!
                                childEndpoint: childConnectionEndpoint,
                                parentEndpoint: parentConnectionEndpoint
                            };
                            
                            // CRITICAL: Change originType to UL when links are merged
                            if (parentLink.originType === 'QL') {
                                parentLink.originType = 'UL';
                            }
                            if (childLink.originType === 'QL') {
                                childLink.originType = 'UL';
                            }
                            
                            if (this.debugger) {
                                const connectedDevices = this.getAllConnectedDevices(parentLink);
                                const allLinks = this.getAllMergedLinks(parentLink);
                                const parentUL = allLinks.findIndex(l => l.id === parentLink.id) + 1;
                                const childUL = allLinks.findIndex(l => l.id === childLink.id) + 1;
                                
                                // Determine which TP each link used for this merge (opposite of its remaining free end)
                                const mergeInfo = parentLink.mergedWith || {};
                                const parentTPUsed = mergeInfo.parentFreeEnd === 'start' ? 'end' : 'start';
                                const childTPUsed = mergeInfo.childFreeEnd === 'start' ? 'end' : 'start';
                                
                                // Calculate TP numbers before merge
                                // FIXED: Use clearer logic - endpoint is TP if NOT connected
                                const tpsInBUL = [];
                                allLinks.forEach(chainLink => {
                                    if (!this.isEndpointConnected(chainLink, 'start')) {
                                        tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start' });
                                    }
                                    
                                    if (!this.isEndpointConnected(chainLink, 'end')) {
                                        tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end' });
                                    }
                                });
                                
                                // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                                tpsInBUL.sort((a, b) => {
                                    const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                                    const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                                    return ulNumA - ulNumB;
                                });
                                
                                const tpLabels = tpsInBUL.map((tp, idx) => {
                                    const ulNum = allLinks.findIndex(l => l.id === tp.linkId) + 1;
                                    return `TP-${idx + 1}(U${ulNum}-${tp.endpoint})`;
                                }).join(', ');
                                
                                this.debugger.logSuccess(`🔗 New UL created and merged with existing UL/BUL`);
                                this.debugger.logInfo(`   Device: ${this.linkStart.label} → U${parentUL}-TP(${parentTPUsed})`);
                                this.debugger.logInfo(`   🔗 Merge: U${parentUL}-TP(${parentTPUsed}) + U${childUL}-TP(${childTPUsed}) → MP`);
                                const mpNum = parentLink.mergedWith?.mpNumber || 0;
                                this.debugger.logInfo(`   MP-${mpNum} created at (${connectionPoint.x.toFixed(1)}, ${connectionPoint.y.toFixed(1)})`);
                                this.debugger.logInfo(`   BUL now: ${connectedDevices.links.length} link(s) | TPs: ${tpLabels}`);
                            }
                            
                            // Exit link mode
                            this.linking = false;
                            this.linkStart = null;
                            this.setMode('base');
                            this.draw();
                        } else {
                            if (this.debugger) {
                                this.debugger.logInfo(`🚫 TP already attached to a device - cannot connect`);
                            }
                        }
                    } else {
                        if (this.debugger) {
                            this.debugger.logInfo(`🚫 Cannot connect to MP (connection point) - use free TP instead`);
                        }
                    }
                }
            }
        } else if (this.currentTool === 'text') {
            // ENHANCED: Continuous text placement - place multiple texts without switching back to select
                this.saveState(); // Save before creating
                const text = this.createText(pos.x, pos.y);
                this.objects.push(text);
                this.selectedObject = text;
                this.selectedObjects = [text];
                this.updateTextProperties();
            
            if (this.debugger) {
                this.debugger.logSuccess(`📝 Text placed at (${Math.round(pos.x)}, ${Math.round(pos.y)})`);
                this.debugger.logInfo(`   Text tool remains active - click to place more texts`);
            }
            
            // DON'T return to select tool - stay in text mode for continuous placement
        }
        
        this.draw();
    }
    
    handleMouseMove(e) {
        // Store screen coordinates (canvas backing store pixels) for zoom operations
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        this.lastMouseScreen = {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY
        };
        
        // Cancel long press if mouse moves
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
        
        // Cancel move long-press if mouse moves before timer completes
        if (this.moveLongPressTimer && !this.dragging) {
            const pos = this.getMousePos(e);
            const dx = pos.x - this.lastMousePos?.x || 0;
            const dy = pos.y - this.lastMousePos?.y || 0;
            const moveDist = Math.sqrt(dx * dx + dy * dy);
            
            // If moved more than 5 pixels, cancel long-press timer
            if (moveDist > 5) {
                clearTimeout(this.moveLongPressTimer);
                this.moveLongPressTimer = null;
            }
        }
        
        // Cancel resize long-press if mouse moves away from handle
        if (this.resizeLongPressTimer && !this.resizingDevice) {
            const pos = this.getMousePos(e);
            const clickedObject = this.findObjectAt(pos.x, pos.y);
            if (!clickedObject || clickedObject.type !== 'device') {
                clearTimeout(this.resizeLongPressTimer);
                this.resizeLongPressTimer = null;
                this.resizeHandle = null;
            }
        }
        
        if (this.panning) {
            this.panOffset.x = e.clientX - this.panStart.x;
            this.panOffset.y = e.clientY - this.panStart.y;
            this.savePanOffset();
            this.updateScrollbars();
            this.draw();
            this.updateHud();
            return;
        }
        
        const pos = this.getMousePos(e);
        
        // Store world position for debugger and HUD
        this.lastMousePos = pos;
        
        // Update cursor if hovering over rotation handle
        if (this.selectedObject && this.selectedObject.type === 'device' && 
            this.currentMode === 'select' && !this.rotatingDevice) {
            if (this.findRotationHandle(this.selectedObject, pos.x, pos.y)) {
                this.canvas.style.cursor = 'grab';
            } else if (!this.dragging && !this.panning) {
                this.updateCursor();
            }
        }

        // If in device placement with a pending click and the user drags, start marquee selection instead of placing
        if (this.placingDevice && this.placementPending && this.selectionRectStart) {
            const dx = Math.abs(pos.x - this.placementPending.startPos.x);
            const dy = Math.abs(pos.y - this.placementPending.startPos.y);
            if (dx > 3 || dy > 3) {
                // Cancel pending placement and start marquee selection - SEAMLESS TRANSITION
                const deviceType = this.placingDevice;
                this.placementPending = null;
                this.placingDevice = null; // Temporarily exit placement mode
                this.startMarqueeSelection(this.selectionRectStart);
                
                // Store device type to resume after marquee
                this.resumePlacementAfterMarquee = deviceType;
                
                if (this.debugger) {
                    this.debugger.logInfo(`🔄 Seamless transition: Device placement → MS mode (drag detected)`);
                }
            }
        }
        
        // Handle link stretching (unbound links)
        // CRITICAL: Only process if stretching flags are set (safety check)
        if (this.stretchingLink && this.stretchingEndpoint) {
            // ENHANCED: Special handling for connection point dragging (MPs)
            if (this.stretchingConnectionPoint) {
                // Dragging an MP - ONLY move the MP endpoint itself!
                // CRITICAL FIX: Don't translate the whole link, just move the grabbed endpoint
                const newX = pos.x;
                const newY = pos.y;
                
                // DEBUG: Log initial state
                if (this.debugger) {
                    this.debugger.logInfo(`━━━ MP DRAG: ${this.stretchingLink.id}.${this.stretchingEndpoint} ━━━`);
                    this.debugger.logInfo(`   Start: (${this.stretchingLink.start.x.toFixed(1)}, ${this.stretchingLink.start.y.toFixed(1)})`);
                    this.debugger.logInfo(`   End: (${this.stretchingLink.end.x.toFixed(1)}, ${this.stretchingLink.end.y.toFixed(1)})`);
                    this.debugger.logInfo(`   Moving to: (${newX.toFixed(1)}, ${newY.toFixed(1)})`);
                }
                
                // Move ONLY the endpoint we're dragging (the MP), NOT the entire link
                if (this.stretchingEndpoint === 'start') {
                    // Only move start if it's NOT a TP (not attached to device)
                    if (!this.stretchingLink.device1) {
                        this.stretchingLink.start.x = newX;
                        this.stretchingLink.start.y = newY;
                    }
                } else {
                    // Only move end if it's NOT a TP (not attached to device)
                    if (!this.stretchingLink.device2) {
                        this.stretchingLink.end.x = newX;
                        this.stretchingLink.end.y = newY;
                    }
                }
                
                // Find the partner link and update its connected endpoint
                // CRITICAL FIX: For middle links (both mergedWith and mergedInto), determine partner based on grabbed endpoint
                let partnerLink = null;
                let partnerEndpoint = null;
                
                // Determine which endpoint was grabbed and find the corresponding partner
                const isMiddleLink = this.stretchingLink.mergedWith && this.stretchingLink.mergedInto;
                
                if (this.debugger && isMiddleLink) {
                    this.debugger.logInfo(`🔍 Dragging MP on MIDDLE LINK ${this.stretchingLink.id}`);
                    this.debugger.logInfo(`   Grabbed endpoint: ${this.stretchingEndpoint}`);
                    this.debugger.logInfo(`   mergedInto: ${this.stretchingLink.mergedInto.parentId}`);
                    this.debugger.logInfo(`   mergedWith: ${this.stretchingLink.mergedWith.linkId}`);
                }
                
                if (isMiddleLink) {
                    // Middle link - need to determine partner based on grabbed endpoint
                    // CRITICAL FIX: Check actual endpoint metadata, NOT assume start=parent and end=child!
                    // The mergedInto.childEndpoint tells us which end connects to parent
                    // The mergedWith.connectionEndpoint tells us which end connects to child
                    
                    const parentConnectionEndpoint = this.stretchingLink.mergedInto.childEndpoint;
                    const childConnectionEndpoint = this.stretchingLink.mergedWith.connectionEndpoint;
                    
                    if (this.debugger) {
                        this.debugger.logInfo(`   Parent connects at: ${parentConnectionEndpoint}`);
                        this.debugger.logInfo(`   Child connects at: ${childConnectionEndpoint}`);
                    }
                    
                    // Determine which connection the grabbed endpoint belongs to
                    const grabbedIsParentConnection = (this.stretchingEndpoint === parentConnectionEndpoint);
                    const grabbedIsChildConnection = (this.stretchingEndpoint === childConnectionEndpoint);
                    
                    if (grabbedIsParentConnection) {
                        // Grabbed the endpoint that connects to parent
                        partnerLink = this.objects.find(o => o.id === this.stretchingLink.mergedInto.parentId);
                        if (partnerLink && partnerLink.mergedWith) {
                            partnerEndpoint = partnerLink.mergedWith.connectionEndpoint || 
                                            partnerLink.mergedWith.parentEndpoint ||
                                            (partnerLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start');
                        }
                        
                        if (this.debugger) {
                            this.debugger.logInfo(`   → Partner: ${partnerLink?.id} (parent), endpoint: ${partnerEndpoint}`);
                        }
                        
                        // Update connection point in metadata
                        if (this.stretchingLink.mergedInto.connectionPoint) {
                            this.stretchingLink.mergedInto.connectionPoint.x = newX;
                            this.stretchingLink.mergedInto.connectionPoint.y = newY;
                        }
                    } else if (grabbedIsChildConnection) {
                        // Grabbed the endpoint that connects to child
                        partnerLink = this.objects.find(o => o.id === this.stretchingLink.mergedWith.linkId);
                        partnerEndpoint = this.stretchingLink.mergedWith.childConnectionEndpoint ||
                            (this.stretchingLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                        
                        if (this.debugger) {
                            this.debugger.logInfo(`   → Partner: ${partnerLink?.id} (child), endpoint: ${partnerEndpoint}`);
                        }
                        
                        // Update connection point in metadata
                        if (this.stretchingLink.mergedWith.connectionPoint) {
                            this.stretchingLink.mergedWith.connectionPoint.x = newX;
                            this.stretchingLink.mergedWith.connectionPoint.y = newY;
                        }
                    } else {
                        // ERROR: Grabbed endpoint doesn't match either connection!
                        if (this.debugger) {
                            this.debugger.logError(`🚨 MIDDLE LINK ERROR: Grabbed ${this.stretchingEndpoint} but parent connects at ${parentConnectionEndpoint}, child at ${childConnectionEndpoint}`);
                        }
                    }
                } else if (this.stretchingLink.mergedWith) {
                    // Only has child (mergedWith) - this is a head link
                    partnerLink = this.objects.find(o => o.id === this.stretchingLink.mergedWith.linkId);
                    // FIXED: childFreeEnd tells us which end IS FREE, connected end is the opposite
                    partnerEndpoint = this.stretchingLink.mergedWith.childConnectionEndpoint ||
                        (this.stretchingLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                    
                    // Update connection point in metadata
                    if (this.stretchingLink.mergedWith.connectionPoint) {
                        this.stretchingLink.mergedWith.connectionPoint.x = newX;
                        this.stretchingLink.mergedWith.connectionPoint.y = newY;
                    }
                } else if (this.stretchingLink.mergedInto) {
                    // Only has parent (mergedInto) - this is a tail link
                    partnerLink = this.objects.find(o => o.id === this.stretchingLink.mergedInto.parentId);
                    if (partnerLink && partnerLink.mergedWith) {
                        // Determine which endpoint of the parent is connected to this MP
                        partnerEndpoint = partnerLink.mergedWith.connectionEndpoint || 
                                        partnerLink.mergedWith.parentEndpoint ||
                                        (partnerLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start');
                    }
                    
                    // Update connection point in metadata
                    if (this.stretchingLink.mergedInto.connectionPoint) {
                    this.stretchingLink.mergedInto.connectionPoint.x = newX;
                    this.stretchingLink.mergedInto.connectionPoint.y = newY;
                    }
                }
                
                // Update partner link's endpoint
                // FIXED: Only update if NOT attached to a device (i.e., NOT a TP)
                if (partnerLink && partnerEndpoint) {
                    if (this.debugger) {
                        this.debugger.logInfo(`   Updating partner ${partnerLink.id}.${partnerEndpoint} to (${newX.toFixed(1)}, ${newY.toFixed(1)})`);
                        this.debugger.logInfo(`   Stretching ${this.stretchingLink.id}.${this.stretchingEndpoint} to (${newX.toFixed(1)}, ${newY.toFixed(1)})`);
                    }
                    
                    if (partnerEndpoint === 'start' && !partnerLink.device1) {
                        // Only move start if NOT attached to device
                        partnerLink.start.x = newX;
                        partnerLink.start.y = newY;
                    } else if (partnerEndpoint === 'end' && !partnerLink.device2) {
                        // Only move end if NOT attached to device
                        partnerLink.end.x = newX;
                        partnerLink.end.y = newY;
                    }
                    
                    // CRITICAL: Update partner's connection point metadata bidirectionally
                    // Both mergedWith and mergedInto must stay synchronized
                    if (partnerLink.mergedWith && this.stretchingLink.mergedInto) {
                        // Partner is parent, stretching link is child
                        if (partnerLink.mergedWith.connectionPoint) {
                            partnerLink.mergedWith.connectionPoint.x = newX;
                            partnerLink.mergedWith.connectionPoint.y = newY;
                        }
                    } else if (partnerLink.mergedInto && this.stretchingLink.mergedWith) {
                        // Partner is child, stretching link is parent
                        if (partnerLink.mergedInto.connectionPoint) {
                            partnerLink.mergedInto.connectionPoint.x = newX;
                            partnerLink.mergedInto.connectionPoint.y = newY;
                        }
                    }
                }
                
                // CRITICAL FIX: DO NOT call updateAllConnectionPoints() here!
                // That function updates ALL connection points in ALL links, causing other MPs to jump
                // We already manually updated the relevant connection points above (lines 2779-2827)
                // Only those two connection points (on the stretching link and its partner) should move
                // Other MPs in the chain should stay in place!
                // this.updateAllConnectionPoints(); // REMOVED - causes MP-2 to jump when dragging MP-1
                
                // REAL-TIME FEEDBACK: Draw immediately to show link movement during drag
                this.draw();
                return;
            }
            
            // ENHANCED: TP stretching with BUL chain support and real-time tracking
            // Find nearby device for visual feedback and magnetic snap
            const endpointPos = this.stretchingEndpoint === 'start' 
                ? this.stretchingLink.start 
                : this.stretchingLink.end;
            
            // AI DEBUGGER: Real-time TP/MP tracking during stretch
            if (this.debugger && this._bulTrackingData) {
                const allLinks = this.getAllMergedLinks(this.stretchingLink);
                const currentPos = { x: pos.x, y: pos.y };
                const startPos = this._bulTrackingData.links.find(l => l.id === this.stretchingLink.id);
                
                if (startPos) {
                    const startEndpointPos = this.stretchingEndpoint === 'start' ? startPos.startPos : startPos.endPos;
                    const distance = Math.hypot(currentPos.x - startEndpointPos.x, currentPos.y - startEndpointPos.y);
                    
                    // Update tracking data
                    const trackData = this._bulTrackingData.links.find(l => l.id === this.stretchingLink.id);
                    if (trackData) {
                        trackData.currentPos = currentPos;
                        trackData.distance = distance;
                    }
                    
                    // Log movement every 50px or on significant changes
                    if (!this._lastTrackingLog || (Date.now() - this._lastTrackingLog) > 200) {
                        const ulNum = allLinks.findIndex(l => l.id === this.stretchingLink.id) + 1;
                        
                        // Determine if it's a TP or MP
                        if (!this.stretchingConnectionPoint) {
                            // It's a TP - find TP number
                            const tpsInBUL = [];
                            allLinks.forEach(chainLink => {
                                if (!this.isEndpointConnected(chainLink, 'start')) {
                                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start' });
                                }
                                if (!this.isEndpointConnected(chainLink, 'end')) {
                                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end' });
                                }
                            });
                            tpsInBUL.sort((a, b) => {
                                const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                                const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                                return ulNumA - ulNumB;
                            });
                            const tpIdx = tpsInBUL.findIndex(tp => tp.linkId === this.stretchingLink.id && tp.endpoint === this.stretchingEndpoint);
                            const tpNum = (tpIdx >= 0) ? tpIdx + 1 : '?';
                            
                            this.debugger.logInfo(`⚪ TP-${tpNum}(U${ulNum}) moving: ${Math.round(distance)}px from start`);
                        } else {
                            // It's an MP - find MP number
                            let mpNumber = 0;
                            if (this.stretchingLink.mergedWith) {
                                mpNumber = this.stretchingLink.mergedWith.mpNumber || 0;
                            } else if (this.stretchingLink.mergedInto) {
                                const parent = this.objects.find(o => o.id === this.stretchingLink.mergedInto.parentId);
                                if (parent?.mergedWith) {
                                    mpNumber = parent.mergedWith.mpNumber || 0;
                                }
                            }
                            this.debugger.logInfo(`🟣 MP-${mpNumber}(U${ulNum}) moving: ${Math.round(distance)}px from start`);
                        }
                        this._lastTrackingLog = Date.now();
                    }
                }
            }
            
            let nearbyDevice = null;
            let snapDistance = Infinity;
            let snapAngle = 0;
            
            // ENHANCED: Check all devices for the closest one within attachment range
            this.objects.forEach(obj => {
                if (obj.type === 'device') {
                    const dx = pos.x - obj.x;
                    const dy = pos.y - obj.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    const attachmentRange = obj.radius + 25; // Increased from 15 for easier attachment
                    
                    if (distance <= attachmentRange && distance < snapDistance) {
                        nearbyDevice = obj;
                        snapDistance = distance;
                        snapAngle = Math.atan2(dy, dx);
                    }
                }
            });

            // ENHANCED: Check for nearby UL endpoints (TPs) for link-to-link snapping
            let nearbyULEndpoint = null;
            let ulSnapDistance = Infinity;
            
            // Only search for merge targets if the stretching endpoint is a FREE TP
            // Check if stretchingEndpointIsFree logic (replicated from onMouseUp logic)
            let stretchingEndpointIsFree = true;
            if (this.stretchingConnectionPoint) stretchingEndpointIsFree = false;
            if (this.stretchingLink.mergedWith && this.stretchingEndpoint !== this.stretchingLink.mergedWith.parentFreeEnd) stretchingEndpointIsFree = false;
            if (this.stretchingLink.mergedInto) {
                const parent = this.objects.find(o => o.id === this.stretchingLink.mergedInto.parentId);
                if (parent && parent.mergedWith && this.stretchingEndpoint !== parent.mergedWith.childFreeEnd) stretchingEndpointIsFree = false;
            }

            if (stretchingEndpointIsFree) {
                this.objects.forEach(obj => {
                    if (obj.type === 'unbound' && obj.id !== this.stretchingLink.id) {
                         // Skip middle links
                         if (obj.mergedInto && obj.mergedWith) return;

                         // Check start
                         let startIsConnectionPoint = false;
                         if (obj.connectedTo && obj.connectedTo.thisEndpoint === 'start') startIsConnectionPoint = true;
                         else if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'start') startIsConnectionPoint = true;
                         else if (obj.mergedInto) {
                             const p = this.objects.find(o => o.id === obj.mergedInto.parentId);
                             if (p && p.mergedWith && p.mergedWith.childFreeEnd !== 'start') startIsConnectionPoint = true;
                         }

                         if (!obj.device1 && !startIsConnectionPoint) {
                             const dist = Math.sqrt(Math.pow(pos.x - obj.start.x, 2) + Math.pow(pos.y - obj.start.y, 2));
                             if (dist < this.ulSnapDistance && dist < ulSnapDistance) {
                                 nearbyULEndpoint = obj.start;
                                 ulSnapDistance = dist;
                             }
                         }

                         // Check end
                         let endIsConnectionPoint = false;
                         if (obj.connectedTo && obj.connectedTo.thisEndpoint === 'end') endIsConnectionPoint = true;
                         else if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'end') endIsConnectionPoint = true;
                         else if (obj.mergedInto) {
                             const p = this.objects.find(o => o.id === obj.mergedInto.parentId);
                             if (p && p.mergedWith && p.mergedWith.childFreeEnd !== 'end') endIsConnectionPoint = true;
                         }

                         if (!obj.device2 && !endIsConnectionPoint) {
                             const dist = Math.sqrt(Math.pow(pos.x - obj.end.x, 2) + Math.pow(pos.y - obj.end.y, 2));
                             if (dist < this.ulSnapDistance && dist < ulSnapDistance) {
                                 nearbyULEndpoint = obj.end;
                                 ulSnapDistance = dist;
                             }
                         }
                    }
                });
            }
            
            // Store nearby device for visual feedback during draw (only if sticky links enabled)
            this._stretchingNearDevice = this.linkStickyMode ? nearbyDevice : null;
            this._stretchingSnapAngle = (this.linkStickyMode && nearbyDevice) ? snapAngle : null;
            this._stretchingNearUL = (this.linkStickyMode && nearbyULEndpoint) ? nearbyULEndpoint : null;
            
            // ENHANCED: Multi-stage magnetic snap for smoother attachment
            let finalX = pos.x;
            let finalY = pos.y;
            
            if (this.linkStickyMode) {
                if (nearbyDevice) {
                const targetX = nearbyDevice.x + Math.cos(snapAngle) * nearbyDevice.radius;
                const targetY = nearbyDevice.y + Math.sin(snapAngle) * nearbyDevice.radius;
                
                if (snapDistance < (nearbyDevice.radius + 8)) {
                    // Very close - strong snap (90%)
                    const pullStrength = 0.9;
                finalX = pos.x + (targetX - pos.x) * pullStrength;
                finalY = pos.y + (targetY - pos.y) * pullStrength;
                    this.canvas.style.cursor = 'crosshair'; // Ready to attach
                } else if (snapDistance < (nearbyDevice.radius + 15)) {
                    // Close - medium snap (50%)
                    const pullStrength = 0.5;
                    finalX = pos.x + (targetX - pos.x) * pullStrength;
                    finalY = pos.y + (targetY - pos.y) * pullStrength;
                    this.canvas.style.cursor = 'crosshair'; // Approaching
                } else {
                    // In range - gentle pull (20%)
                    const pullStrength = 0.2;
                    finalX = pos.x + (targetX - pos.x) * pullStrength;
                    finalY = pos.y + (targetY - pos.y) * pullStrength;
                    this.canvas.style.cursor = 'move'; // Getting closer
                    }
                } else if (nearbyULEndpoint) {
                    // UL Snap Logic - IMMEDIATE STICKY SNAP
                     const targetX = nearbyULEndpoint.x;
                    const targetY = nearbyULEndpoint.y;
                    
                    if (ulSnapDistance < 5) {
                        // INSTANT snap when very close
                        finalX = targetX;
                        finalY = targetY;
                        this.canvas.style.cursor = 'copy'; 
                    } else if (ulSnapDistance < 15) {
                        // Very strong pull
                        const pullStrength = 0.95;
                        finalX = pos.x + (targetX - pos.x) * pullStrength;
                        finalY = pos.y + (targetY - pos.y) * pullStrength;
                        this.canvas.style.cursor = 'copy';
                    } else if (ulSnapDistance < 25) {
                        // Medium pull
                        const pullStrength = 0.6;
                        finalX = pos.x + (targetX - pos.x) * pullStrength;
                        finalY = pos.y + (targetY - pos.y) * pullStrength;
                        this.canvas.style.cursor = 'copy';
                    } else {
                        // Gentle attraction
                        const pullStrength = 0.25;
                        finalX = pos.x + (targetX - pos.x) * pullStrength;
                        finalY = pos.y + (targetY - pos.y) * pullStrength;
                        this.canvas.style.cursor = 'move';
                    }
                } else {
                    this.canvas.style.cursor = 'grab';
                }
            } else {
                this.canvas.style.cursor = 'grab'; // Normal cursor
            }
            
            // If endpoint is attached to a device and user moves it away, detach it
            if (this.stretchingEndpoint === 'start') {
                if (this.stretchingLink.device1) {
                    const device1 = this.objects.find(obj => obj.id === this.stretchingLink.device1);
                    if (device1) {
                        const dx = finalX - device1.x;
                        const dy = finalY - device1.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        // Detach if moved more than device radius + 30px away (more forgiving)
                        if (distance > (device1.radius + 30)) {
                            const detachedFrom = device1.label || device1.id;
                            this.stretchingLink.device1 = null;
                            delete this.stretchingLink.device1Angle; // Clear stored angle on detach
                            
                            // CRITICAL: Change originType from QL to UL when link is detached
                            if (this.stretchingLink.originType === 'QL') {
                                this.stretchingLink.originType = 'UL';
                            }
                            
                            // TRACKING: Log detachment
                            if (this._bulTrackingData) {
                                const trackData = this._bulTrackingData.links.find(l => l.id === this.stretchingLink.id);
                                if (trackData) {
                                    trackData.detachments = (trackData.detachments || 0) + 1;
                                }
                            }
                            
                            if (this.debugger) {
                                // Calculate UL and TP numbers
                                const allLinks = this.getAllMergedLinks(this.stretchingLink);
                                const ulNum = allLinks.findIndex(l => l.id === this.stretchingLink.id) + 1;
                                
                                // Find TP number for start endpoint
                                // FIXED: Use clearer logic - endpoint is TP if NOT connected
                                const tpsInBUL = [];
                                allLinks.forEach(chainLink => {
                                    let sIsConnected = false;
                                    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') sIsConnected = true;
                                    if (chainLink.mergedInto) {
                                        const prnt = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'end') sIsConnected = true;
                                    }
                                    if (!sIsConnected) tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start' });
                                    
                                    let eIsConnected = false;
                                    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') eIsConnected = true;
                                    if (chainLink.mergedInto) {
                                        const prnt = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'start') eIsConnected = true;
                                    }
                                    if (!eIsConnected) tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end' });
                                });
                                
                                // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                                tpsInBUL.sort((a, b) => {
                                    const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                                    const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                                    return ulNumA - ulNumB;
                                });
                                
                                const tpIdx = tpsInBUL.findIndex(tp => tp.linkId === this.stretchingLink.id && tp.endpoint === 'start');
                                const tpNum = (tpIdx >= 0) ? tpIdx + 1 : '?';
                                
                                this.debugger.logInfo(`🔓 Detached: U${ulNum}-TP-${tpNum}(start) from ${detachedFrom}`);
                            }
                        } else {
                            // Keep attached - snap to device edge
                            const angle = Math.atan2(finalY - device1.y, finalX - device1.x);
                            finalX = device1.x + Math.cos(angle) * device1.radius;
                            finalY = device1.y + Math.sin(angle) * device1.radius;
                        }
                    }
                }
                
                this.stretchingLink.start = { x: finalX, y: finalY };
                
                // TRACKING: Detect position jumps for this endpoint
                if (this._bulTrackingData) {
                    const trackData = this._bulTrackingData.links.find(l => l.id === this.stretchingLink.id);
                    if (trackData) {
                        const lastStart = trackData.lastPos.start;
                        const jump = Math.sqrt(
                            Math.pow(finalX - lastStart.x, 2) + 
                            Math.pow(finalY - lastStart.y, 2)
                        );
                        
                        // Detect jumps > 50px (indicates bug)
                        if (jump > 50) {
                            this._bulTrackingData.totalJumps++;
                            if (this.debugger) {
                                this.debugger.logError(`🚨 JUMP DETECTED: ${this.stretchingLink.id} START moved ${jump.toFixed(1)}px!`);
                                this.debugger.logInfo(`   Last: (${lastStart.x.toFixed(1)}, ${lastStart.y.toFixed(1)})`);
                                this.debugger.logInfo(`   Now: (${finalX.toFixed(1)}, ${finalY.toFixed(1)})`);
                            }
                        }
                        
                        // Update tracking
                        trackData.lastPos.start = { x: finalX, y: finalY };
                    }
                }
                
                // ENHANCED: TP stretching in BUL chains - only update THIS link's endpoint
                // TPs are free endpoints and don't affect other links in the chain
                // Only MPs (connection points) move multiple links together
                
                // CRITICAL: When stretching a TP (not MP), we only move this link's endpoint
                // The connection points (MPs) stay fixed - they only move when explicitly dragged
                // This ensures fluid, independent TP movement in BUL chains
                
                // Update connection point metadata if this endpoint is part of a merge
                // But only update metadata, don't move other links (they stay fixed)
                if (this.stretchingLink.mergedWith) {
                    const parentFreeEnd = this.stretchingLink.mergedWith.parentFreeEnd;
                    const parentConnectedEnd = parentFreeEnd === 'start' ? 'end' : 'start';
                    
                    // If we're stretching the connected end (MP), update connection point
                    if (this.stretchingEndpoint === parentConnectedEnd && this.stretchingConnectionPoint) {
                        const newConnectionX = finalX;
                        const newConnectionY = finalY;
                        
                        // Update connection point in metadata
                        if (this.stretchingLink.mergedWith.connectionPoint) {
                            this.stretchingLink.mergedWith.connectionPoint.x = newConnectionX;
                            this.stretchingLink.mergedWith.connectionPoint.y = newConnectionY;
                        }
                        
                        // Also update child link's endpoint if it's connected here
                        const childLink = this.objects.find(o => o.id === this.stretchingLink.mergedWith.linkId);
                        if (childLink && childLink.mergedInto) {
                        const childConnectedEnd = this.stretchingLink.mergedWith.childConnectionEndpoint ||
                            (this.stretchingLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                            
                        if (childConnectedEnd === 'start') {
                            childLink.start.x = newConnectionX;
                            childLink.start.y = newConnectionY;
                        } else {
                            childLink.end.x = newConnectionX;
                            childLink.end.y = newConnectionY;
                        }
                        
                            if (childLink.mergedInto.connectionPoint) {
                            childLink.mergedInto.connectionPoint.x = newConnectionX;
                            childLink.mergedInto.connectionPoint.y = newConnectionY;
                        }
                    }
                    }
                } else if (this.stretchingLink.mergedInto) {
                    // This is a child link - update parent's connection point if we're dragging the connected end
                    const parentLink = this.objects.find(o => o.id === this.stretchingLink.mergedInto.parentId);
                    if (parentLink && parentLink.mergedWith) {
                        const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                        const childConnectedEnd = childFreeEnd === 'start' ? 'end' : 'start';
                        
                        // If stretching the connected end (MP), update connection point
                        if (this.stretchingEndpoint === childConnectedEnd && this.stretchingConnectionPoint) {
                            const newConnectionX = finalX;
                            const newConnectionY = finalY;
                            
                            // Update parent's endpoint
                            const parentConnectedEnd = parentLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                        if (parentConnectedEnd === 'start') {
                            parentLink.start.x = newConnectionX;
                            parentLink.start.y = newConnectionY;
                        } else {
                            parentLink.end.x = newConnectionX;
                            parentLink.end.y = newConnectionY;
                        }
                        
                            // Update connection point metadata
                            if (parentLink.mergedWith.connectionPoint) {
                            parentLink.mergedWith.connectionPoint.x = newConnectionX;
                            parentLink.mergedWith.connectionPoint.y = newConnectionY;
                        }
                            if (this.stretchingLink.mergedInto.connectionPoint) {
                        this.stretchingLink.mergedInto.connectionPoint.x = newConnectionX;
                        this.stretchingLink.mergedInto.connectionPoint.y = newConnectionY;
                    }
                }
                    }
                }
                
                // CRITICAL: Update all connection points after any movement to keep chain synced
                this.updateAllConnectionPoints();
            } else {
                if (this.stretchingLink.device2) {
                    const device2 = this.objects.find(obj => obj.id === this.stretchingLink.device2);
                    if (device2) {
                        const dx = finalX - device2.x;
                        const dy = finalY - device2.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        // Detach if moved more than device radius + 30px away (more forgiving)
                        if (distance > (device2.radius + 30)) {
                            const detachedFrom = device2.label || device2.id;
                            this.stretchingLink.device2 = null;
                            delete this.stretchingLink.device2Angle; // Clear stored angle on detach
                            
                            // CRITICAL: Change originType from QL to UL when link is detached
                            if (this.stretchingLink.originType === 'QL') {
                                this.stretchingLink.originType = 'UL';
                            }
                            
                            // TRACKING: Log detachment
                            if (this._bulTrackingData) {
                                const trackData = this._bulTrackingData.links.find(l => l.id === this.stretchingLink.id);
                                if (trackData) {
                                    trackData.detachments = (trackData.detachments || 0) + 1;
                                }
                            }
                            
                            if (this.debugger) {
                                // Calculate UL and TP numbers
                                const allLinks = this.getAllMergedLinks(this.stretchingLink);
                                const ulNum = allLinks.findIndex(l => l.id === this.stretchingLink.id) + 1;
                                
                                // Find TP number for end endpoint
                                // FIXED: Use clearer logic - endpoint is TP if NOT connected
                                const tpsInBUL = [];
                                allLinks.forEach(chainLink => {
                                    let sIsConnected = false;
                                    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') sIsConnected = true;
                                    if (chainLink.mergedInto) {
                                        const prnt = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'end') sIsConnected = true;
                                    }
                                    if (!sIsConnected) tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start' });
                                    
                                    let eIsConnected = false;
                                    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') eIsConnected = true;
                                    if (chainLink.mergedInto) {
                                        const prnt = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'start') eIsConnected = true;
                                    }
                                    if (!eIsConnected) tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end' });
                                });
                                
                                // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                                tpsInBUL.sort((a, b) => {
                                    const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                                    const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                                    return ulNumA - ulNumB;
                                });
                                
                                const tpIdx = tpsInBUL.findIndex(tp => tp.linkId === this.stretchingLink.id && tp.endpoint === 'end');
                                const tpNum = (tpIdx >= 0) ? tpIdx + 1 : '?';
                                
                                this.debugger.logInfo(`🔓 Detached: U${ulNum}-TP-${tpNum}(end) from ${detachedFrom}`);
                            }
                        } else {
                            // Keep attached - snap to device edge
                            const angle = Math.atan2(finalY - device2.y, finalX - device2.x);
                            finalX = device2.x + Math.cos(angle) * device2.radius;
                            finalY = device2.y + Math.sin(angle) * device2.radius;
                        }
                    }
                }
                this.stretchingLink.end = { x: finalX, y: finalY };
                
                // TRACKING: Detect position jumps for this endpoint
                if (this._bulTrackingData) {
                    const trackData = this._bulTrackingData.links.find(l => l.id === this.stretchingLink.id);
                    if (trackData) {
                        const lastEnd = trackData.lastPos.end;
                        const jump = Math.sqrt(
                            Math.pow(finalX - lastEnd.x, 2) + 
                            Math.pow(finalY - lastEnd.y, 2)
                        );
                        
                        // Detect jumps > 50px (indicates bug)
                        if (jump > 50) {
                            this._bulTrackingData.totalJumps++;
                            if (this.debugger) {
                                this.debugger.logError(`🚨 JUMP DETECTED: ${this.stretchingLink.id} END moved ${jump.toFixed(1)}px!`);
                                this.debugger.logInfo(`   Last: (${lastEnd.x.toFixed(1)}, ${lastEnd.y.toFixed(1)})`);
                                this.debugger.logInfo(`   Now: (${finalX.toFixed(1)}, ${finalY.toFixed(1)})`);
                            }
                        }
                        
                        // Update tracking
                        trackData.lastPos.end = { x: finalX, y: finalY };
                    }
                }
                
                // ENHANCED: TP stretching in BUL chains - only update THIS link's endpoint
                // TPs are free endpoints and don't affect other links in the chain
                // Only MPs (connection points) move multiple links together
                
                // CRITICAL: When stretching a TP (not MP), we only move this link's endpoint
                // The connection points (MPs) stay fixed - they only move when explicitly dragged
                // This ensures fluid, independent TP movement in BUL chains
                
                // Update connection point metadata if this endpoint is part of a merge
                // But only update metadata, don't move other links (they stay fixed)
                if (this.stretchingLink.mergedWith) {
                    const parentFreeEnd = this.stretchingLink.mergedWith.parentFreeEnd;
                    const parentConnectedEnd = parentFreeEnd === 'start' ? 'end' : 'start';
                    
                    // If we're stretching the connected end (MP), update connection point
                    if (this.stretchingEndpoint === parentConnectedEnd && this.stretchingConnectionPoint) {
                        const newConnectionX = finalX;
                        const newConnectionY = finalY;
                        
                        // Update connection point in metadata
                        if (this.stretchingLink.mergedWith.connectionPoint) {
                            this.stretchingLink.mergedWith.connectionPoint.x = newConnectionX;
                            this.stretchingLink.mergedWith.connectionPoint.y = newConnectionY;
                        }
                        
                        // Also update child link's endpoint if it's connected here
                        const childLink = this.objects.find(o => o.id === this.stretchingLink.mergedWith.linkId);
                        if (childLink && childLink.mergedInto) {
                        const childConnectedEnd = this.stretchingLink.mergedWith.childConnectionEndpoint ||
                            (this.stretchingLink.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                            
                        if (childConnectedEnd === 'start') {
                            childLink.start.x = newConnectionX;
                            childLink.start.y = newConnectionY;
                        } else {
                            childLink.end.x = newConnectionX;
                            childLink.end.y = newConnectionY;
                        }
                        
                            if (childLink.mergedInto.connectionPoint) {
                            childLink.mergedInto.connectionPoint.x = newConnectionX;
                            childLink.mergedInto.connectionPoint.y = newConnectionY;
                            }
                        }
                    }
                } else if (this.stretchingLink.mergedInto) {
                    // This is a child link - update parent's connection point if we're dragging the connected end
                    const parentLink = this.objects.find(o => o.id === this.stretchingLink.mergedInto.parentId);
                    if (parentLink && parentLink.mergedWith) {
                        const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                        const childConnectedEnd = childFreeEnd === 'start' ? 'end' : 'start';
                        
                        // If stretching the connected end (MP), update connection point
                        if (this.stretchingEndpoint === childConnectedEnd && this.stretchingConnectionPoint) {
                            const newConnectionX = finalX;
                            const newConnectionY = finalY;
                            
                            // Update parent's endpoint
                            const parentConnectedEnd = parentLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                        if (parentConnectedEnd === 'start') {
                            parentLink.start.x = newConnectionX;
                            parentLink.start.y = newConnectionY;
                        } else {
                            parentLink.end.x = newConnectionX;
                            parentLink.end.y = newConnectionY;
                        }
                        
                            // Update connection point metadata
                            if (parentLink.mergedWith.connectionPoint) {
                            parentLink.mergedWith.connectionPoint.x = newConnectionX;
                            parentLink.mergedWith.connectionPoint.y = newConnectionY;
                        }
                            if (this.stretchingLink.mergedInto.connectionPoint) {
                        this.stretchingLink.mergedInto.connectionPoint.x = newConnectionX;
                        this.stretchingLink.mergedInto.connectionPoint.y = newConnectionY;
                            }
                    }
                }
                }
                
                // CRITICAL: Update all connection points after any movement to keep chain synced
                this.updateAllConnectionPoints();
            }
            
            // TRACKING: Check ALL links in BUL chain for unexpected jumps
            if (this._bulTrackingData) {
                const allMergedLinks = this.getAllMergedLinks(this.stretchingLink);
                allMergedLinks.forEach(link => {
                    const trackData = this._bulTrackingData.links.find(l => l.id === link.id);
                    if (trackData) {
                        // Check start position
                        const startJump = Math.sqrt(
                            Math.pow(link.start.x - trackData.lastPos.start.x, 2) + 
                            Math.pow(link.start.y - trackData.lastPos.start.y, 2)
                        );
                        
                        if (startJump > 50 && link.id !== this.stretchingLink.id) {
                            this._bulTrackingData.totalJumps++;
                            if (this.debugger) {
                                this.debugger.logError(`🚨 CHAIN JUMP: ${link.id} START moved ${startJump.toFixed(1)}px unexpectedly!`);
                                this.debugger.logInfo(`   This link was NOT being dragged - BUG DETECTED!`);
                            }
                        }
                        
                        // Check end position
                        const endJump = Math.sqrt(
                            Math.pow(link.end.x - trackData.lastPos.end.x, 2) + 
                            Math.pow(link.end.y - trackData.lastPos.end.y, 2)
                        );
                        
                        if (endJump > 50 && link.id !== this.stretchingLink.id) {
                            this._bulTrackingData.totalJumps++;
                            if (this.debugger) {
                                this.debugger.logError(`🚨 CHAIN JUMP: ${link.id} END moved ${endJump.toFixed(1)}px unexpectedly!`);
                                this.debugger.logInfo(`   This link was NOT being dragged - BUG DETECTED!`);
                            }
                        }
                        
                        // Update positions for next frame
                        trackData.lastPos.start = { x: link.start.x, y: link.start.y };
                        trackData.lastPos.end = { x: link.end.x, y: link.end.y };
                    }
                });
            }
            
            this.draw();
            this.updateHud(pos);
            return;
        }
        
        // Handle device rotation
        if (this.rotatingDevice) {
            this.canvas.style.cursor = 'grabbing'; // Show grabbing cursor during rotation
            const currentAngle = Math.atan2(pos.y - this.rotatingDevice.y, pos.x - this.rotatingDevice.x);
            const angleDiff = (currentAngle - this.rotationStartAngle) * 180 / Math.PI;
            let newRotation = (this.rotationStartValue + angleDiff + 360) % 360;
            if (newRotation < 0) newRotation += 360;
            
            this.rotatingDevice.rotation = newRotation;
            
            this.draw();
            this.updateHud(pos);
            return;
        }
        
        // Handle text rotation
        if (this.rotatingText && this.selectedObject && this.selectedObject.type === 'text') {
            const mouseAngle = Math.atan2(pos.y - this.selectedObject.y, pos.x - this.selectedObject.x);
            const angleDiff = (mouseAngle - this.textRotationStartAngle) * 180 / Math.PI;
            let newRotation = (this.textRotationStartRot + angleDiff) % 360;
            if (newRotation < 0) newRotation += 360;
            
            this.selectedObject.rotation = newRotation;
            
            // Update UI elements if they exist
            const slider = document.getElementById('rotation-slider');
            const value = document.getElementById('rotation-value');
            if (slider) slider.value = Math.round(newRotation);
            if (value) value.textContent = Math.round(newRotation) + '°';
            
            this.draw();
            this.updateHud(pos);
            return;
        }
        
        // Handle text resizing
        if (this.resizingText && this.selectedObject) {
            const currentDist = Math.sqrt(
                Math.pow(pos.x - this.selectedObject.x, 2) + 
                Math.pow(pos.y - this.selectedObject.y, 2)
            );
            const distRatio = currentDist / this.textResizeStartDist;
            const newSize = Math.max(8, Math.min(72, this.textResizeStartSize * distRatio));
            this.selectedObject.fontSize = Math.round(newSize);
            document.getElementById('font-size').value = Math.round(newSize);
            this.draw();
            this.updateHud(pos);
            return;
        }
        
        // Handle multi-select drag
        // Handle multi-select drag (from marquee selection)
        if (this.dragging && this.selectedObjects.length > 1 && this.multiSelectInitialPositions) {
            // Calculate simple mouse movement delta (works even after MS exits to base mode)
            const dx = pos.x - this.dragStart.x;
            const dy = pos.y - this.dragStart.y;
            
            // COLLISION FIX: For multi-device drag, we need to resolve collisions iteratively
            // First pass: calculate proposed positions for all devices
            const proposedPositions = new Map();
            
            // Get all unlocked device objects (check collision only if deviceCollision is ON)
            const deviceObjects = this.selectedObjects.filter(obj => 
                obj.type === 'device' && !obj.locked
            );
            
            // Only calculate collision if deviceCollision is enabled
            if (this.deviceCollision) {
                deviceObjects.forEach(obj => {
                    const initialPos = this.multiSelectInitialPositions.find(p => p.id === obj.id);
                    if (initialPos) {
                        let newX = initialPos.x + dx;
                        let newY = initialPos.y + dy;
                        
                        // First collision check against non-moving devices
                        const proposedPos = this.checkDeviceCollision(obj, newX, newY);
                        proposedPositions.set(obj.id, { x: proposedPos.x, y: proposedPos.y });
                    }
                });
            }
            
            // Second pass: resolve collisions between moving devices themselves
            if (deviceObjects.length > 1 && this.deviceCollision) {
                const maxIterations = 5;
                for (let iter = 0; iter < maxIterations; iter++) {
                    let adjusted = false;
                    for (let i = 0; i < deviceObjects.length; i++) {
                        const obj1 = deviceObjects[i];
                        const pos1 = proposedPositions.get(obj1.id);
                        if (!pos1) continue;
                        
                        for (let j = i + 1; j < deviceObjects.length; j++) {
                            const obj2 = deviceObjects[j];
                            const pos2 = proposedPositions.get(obj2.id);
                            if (!pos2) continue;
                            
                            const dx_coll = pos1.x - pos2.x;
                            const dy_coll = pos1.y - pos2.y;
                            let dist = Math.sqrt(dx_coll * dx_coll + dy_coll * dy_coll);
                            const minDist = (obj1.radius || 30) + (obj2.radius || 30) + 3;
                            
                            if (dist < minDist && dist > 0.01) {
                                const push = (minDist - dist) / 2; // Split push between both devices
                                const nx = dx_coll / dist;
                                const ny = dy_coll / dist;
                                
                                pos1.x += nx * push;
                                pos1.y += ny * push;
                                pos2.x -= nx * push;
                                pos2.y -= ny * push;
                                adjusted = true;
                            }
                        }
                    }
                    if (!adjusted) break;
                }
            }
            
            // Move ALL selected objects by the same offset from their initial positions
            this.selectedObjects.forEach(obj => {
                    // Skip locked objects
                    if (obj.locked) return;
                    
                    // Skip adjacent text (glued to links)
                    if (obj.type === 'text' && obj.linkId && obj.position) return;
                    
                    // No need to skip device-connected links - all links are now unbound with TPs
                    // (Removed old type === 'link' check)
                    
                    // Handle unbound links - they CAN be moved!
                    if (obj.type === 'unbound') {
                        const initialPos = this.multiSelectInitialPositions.find(p => p.id === obj.id);
                        if (initialPos && initialPos.startX !== undefined) {
                            // Move both endpoints by the same offset (translate the entire link)
                            obj.start.x = initialPos.startX + dx;
                            obj.start.y = initialPos.startY + dy;
                            obj.end.x = initialPos.endX + dx;
                            obj.end.y = initialPos.endY + dy;
                            
                            // CRITICAL FIX: Only move partner links if they're NOT already in selection
                            // If all links in BUL are selected, they move together naturally
                            // Connection points will be updated by updateAllConnectionPoints() after drag ends
                            // This prevents conflicting updates and jumps in 3+ link BULs
                            
                            // Check if partner is in selection first
                            let partnerInSelection = false;
                            if (obj.mergedWith) {
                                const childLink = this.objects.find(o => o.id === obj.mergedWith.linkId);
                                partnerInSelection = childLink && this.selectedObjects.includes(childLink);
                            } else if (obj.mergedInto) {
                                const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
                                partnerInSelection = parentLink && this.selectedObjects.includes(parentLink);
                            }
                            
                            // Only do partner dragging if partner is NOT selected
                            if (!partnerInSelection) {
                            // ENHANCED: If this UL is merged, move the connected UL as one unit
                            if (obj.mergedWith) {
                                const childLink = this.objects.find(o => o.id === obj.mergedWith.linkId);
                                    if (childLink) {
                                    // Move child link's free endpoint (keep connection point synced)
                                    const childFreeEnd = obj.mergedWith.childFreeEnd;
                                    const connectionPoint = obj.mergedWith.connectionPoint;
                                    
                                    // Calculate new connection point position after parent move
                                    const parentConnectedEnd = obj.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                                    const newConnectionX = parentConnectedEnd === 'start' ? obj.start.x : obj.end.x;
                                    const newConnectionY = parentConnectedEnd === 'start' ? obj.start.y : obj.end.y;
                                    
                                    // Calculate offset from old connection point to new
                                    const connDx = newConnectionX - connectionPoint.x;
                                    const connDy = newConnectionY - connectionPoint.y;
                                    
                                    // Move child link maintaining its shape relative to connection
                                    childLink.start.x += connDx;
                                    childLink.start.y += connDy;
                                    childLink.end.x += connDx;
                                    childLink.end.y += connDy;
                                    
                                    // Update connection point
                                    obj.mergedWith.connectionPoint.x = newConnectionX;
                                    obj.mergedWith.connectionPoint.y = newConnectionY;
                                    childLink.mergedInto.connectionPoint.x = newConnectionX;
                                    childLink.mergedInto.connectionPoint.y = newConnectionY;
                                }
                            } else if (obj.mergedInto) {
                                // This is a child link - also move parent
                                const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
                                    if (parentLink) {
                                    const connectionPoint = obj.mergedInto.connectionPoint;
                                    
                                    // Find which endpoint of child is connected
                                        const parentFreeEnd = parentLink.mergedWith ? parentLink.mergedWith.parentFreeEnd : 'end';
                                        const childConnectedEnd = parentFreeEnd === 'start' ? 'end' : 'start';
                                    const newConnectionX = childConnectedEnd === 'start' ? obj.start.x : obj.end.x;
                                    const newConnectionY = childConnectedEnd === 'start' ? obj.start.y : obj.end.y;
                                    
                                    // Calculate offset
                                    const connDx = newConnectionX - connectionPoint.x;
                                    const connDy = newConnectionY - connectionPoint.y;
                                    
                                    // Move parent link
                                    parentLink.start.x += connDx;
                                    parentLink.start.y += connDy;
                                    parentLink.end.x += connDx;
                                    parentLink.end.y += connDy;
                                    
                                    // Update connection points
                                    if (parentLink.mergedWith) {
                                        parentLink.mergedWith.connectionPoint.x = newConnectionX;
                                        parentLink.mergedWith.connectionPoint.y = newConnectionY;
                                    }
                                    obj.mergedInto.connectionPoint.x = newConnectionX;
                                    obj.mergedInto.connectionPoint.y = newConnectionY;
                                }
                            }
                            }
                            // If partner IS in selection, connection points will be updated by updateAllConnectionPoints() at the end
                            
                            // Log to debugger (only once per drag, not every frame)
                            if (this.debugger && !this._unboundLinkMoveLogged) {
                                this._unboundLinkMoveLogged = true;
                                const mergedInfo = obj.mergedWith ? ' (merged unit)' : obj.mergedInto ? ' (merged unit)' : '';
                                this.debugger.logSuccess(`↔️ Unbound link moved in MS mode${mergedInfo}`);
                            }
                        }
                        return;
                    }
                    
                    // Use proposed position if collision was calculated, otherwise use simple offset
                    if (this.deviceCollision && obj.type === 'device') {
                        const proposedPos = proposedPositions.get(obj.id);
                        if (proposedPos) {
                            const oldX = obj.x;
                            const oldY = obj.y;
                            obj.x = proposedPos.x;
                            obj.y = proposedPos.y;
                            
                            // Apply movable device chain reaction
                            if (this.movableDevices) {
                                // Amplify velocity during multi-select drag for better chain reactions
                                const dragAmplification = 2.0;
                                const velocityX = (proposedPos.x - oldX) * dragAmplification;
                                const velocityY = (proposedPos.y - oldY) * dragAmplification;
                                this.applyDeviceChainReaction(obj, velocityX, velocityY);
                            }
                            return;
                        }
                    }
                    
                    const initialPos = this.multiSelectInitialPositions.find(p => p.id === obj.id);
                    if (initialPos) {
                        const oldX = obj.x;
                        const oldY = obj.y;
                        const newX = initialPos.x + dx;
                        const newY = initialPos.y + dy;
                        
                        obj.x = newX;
                        obj.y = newY;
                        
                        // Apply movable device chain reaction for non-collision mode
                        if (this.movableDevices && obj.type === 'device') {
                            // Amplify velocity during multi-select drag for better chain reactions
                            const dragAmplification = 2.0;
                            const velocityX = (newX - oldX) * dragAmplification;
                            const velocityY = (newY - oldY) * dragAmplification;
                            this.applyDeviceChainReaction(obj, velocityX, velocityY);
                        }
                    }
                }
            );
            
            // CRITICAL: Update all connection points after multi-select dragging
            // This ensures MPs stay synchronized when dragging 3+ link BULs
            this.updateAllConnectionPoints();
            
            this.draw();
            return;
        }

        // Instant marquee activation on drag - smooth and fast like Ctrl+drag
        if (!this.marqueeActive && this.selectionRectStart && this.marqueeTimer) {
            const dx = Math.abs(pos.x - this.selectionRectStart.x);
            const dy = Math.abs(pos.y - this.selectionRectStart.y);

            // If mouse moves more than 3 pixels, immediately start marquee (very fast response)
            if (dx > 3 || dy > 3) {
                clearTimeout(this.marqueeTimer);
                this.marqueeTimer = null;
                this.startMarqueeSelection(this.selectionRectStart);
            }
        }
        
        // Handle marquee selection rectangle drawing
        if (this.marqueeActive && this.selectionRectStart) {
            const start = this.selectionRectStart;
            this.selectionRectangle = {
                x: Math.min(start.x, pos.x),
                y: Math.min(start.y, pos.y),
                width: Math.abs(pos.x - start.x),
                height: Math.abs(pos.y - start.y)
            };
            
            // Find all objects that intersect with rectangle
            this.selectedObjects = this.findObjectsInRectangle(this.selectionRectangle);
            if (this.selectedObjects.length > 0) {
                this.selectedObject = this.selectedObjects[0];
            }
            
            this.draw();
            return;
        }
        
        if (this.dragging && this.selectedObject) {
            // Don't allow dragging locked objects
            if (this.selectedObject.locked) {
                return;
            }
            
            // CRITICAL FIX: Regular links (bound to devices) are NOT draggable!
            if (this.selectedObject.type === 'link') {
                // Regular links can't be moved - they follow their connected devices
                return;
            }
            
            // Don't allow dragging adjacent text (text glued to links)
            if (this.selectedObject.type === 'text' && this.selectedObject.linkId && this.selectedObject.position) {
                // Text is glued to a link, don't allow manual movement
                return;
            }
            
            // ENHANCED: Special handling for unbound links - move entire link body
            if (this.selectedObject.type === 'unbound' && !this.stretchingLink) {
                // User is dragging the link body (not stretching an endpoint)
                const dx = pos.x - this.dragStart.x;
                const dy = pos.y - this.dragStart.y;
                
                // Move both endpoints by the same offset (translate the entire link)
                if (this.unboundLinkInitialPos) {
                    this.selectedObject.start.x = this.unboundLinkInitialPos.startX + dx;
                    this.selectedObject.start.y = this.unboundLinkInitialPos.startY + dy;
                    this.selectedObject.end.x = this.unboundLinkInitialPos.endX + dx;
                    this.selectedObject.end.y = this.unboundLinkInitialPos.endY + dy;
                    
                    // ENHANCED: Move ENTIRE BUL chain as one unit
                    // Helper function to recursively move neighbors
                    const propagateMovement = (link, diffX, diffY, direction) => {
                         if (!link) return;
                         
                         // Move link body
                         link.start.x += diffX;
                         link.start.y += diffY;
                         link.end.x += diffY;
                         link.end.y += diffY; // Wait, mistake in copy-paste? No, logic is complex below.
                         // Let's rewrite simple propagation based on diffs from previous frame? 
                         // No, we are setting absolute position based on initial + total delta (dx/dy).
                         // We must do the same for all links in chain.
                    };

                    // Correct logic:
                    // 1. Identify all links in the chain.
                    // 2. We don't have their initial positions stored in `unboundLinkInitialPos` (only for selected).
                    // 3. BUT we know relative positions must be preserved.
                    // 4. So we can just move all other links by the DELTA from the LAST frame?
                    //    No, `pos` is absolute mouse pos. `dx` is total drag distance.
                    //    If we use `dx`, we need initial positions.
                    
                    // Hack: Calculate the delta for *this* frame by comparing current pos to (initial + dx).
                    // Actually, `this.selectedObject` was already at `initial + previous_dx`.
                    // Now we set it to `initial + dx`.
                    // The difference `(initial + dx) - current_pos` is the delta for this frame.
                    // Wait, we just set `this.selectedObject` above.
                    // So the delta is `(this.selectedObject.start.x) - (old_x)`.
                    // But we overwrote `old_x`.
                    
                    // Let's use `this.lastDragPos` to track frame-to-frame delta!
                    let frameDx = 0;
                    let frameDy = 0;
                    
                    if (this.lastDragPos && this.lastDragPos.id === this.selectedObject.id) {
                         frameDx = pos.x - this.lastDragPos.x;
                         frameDy = pos.y - this.lastDragPos.y;
                    } else {
                         // First frame of drag
                         frameDx = dx; // Approximate? No, dx is total. 
                         // If first frame, initial is start. dx is correct delta.
                         // Check if `dx` is large?
                         frameDx = dx; 
                         frameDy = dy;
                         // Wait, if it's not first frame, dx is total. We need delta.
                         // We can't rely on `dx` if we don't have previous `dx`.
                         // `this.unboundLinkInitialPos` is set on MouseDown.
                         // `this.dragStart` is mouse offset from object origin.
                         
                         // Let's calculate frame delta using `this.lastMousePos` (world coords) vs `pos`?
                         // `pos` is current mouse pos. `this.lastMousePos` was stored at start of handleMouseMove.
                         // But handleMouseMove overwrites it at the top!
                         // `this.lastMousePos` is updated to `pos` at line 2666.
                         // So we can't use it for delta unless we access it BEFORE update.
                    }
                    
                    // BETTER APPROACH: Traverse the chain and maintain connection point constraints.
                    // We moved `this.selectedObject`. Its connection points moved.
                    // Any link connected to it MUST align its connection endpoint to the new position.
                    // Then propagate.
                    
                    // Propagate Up (Parents)
                    let current = this.selectedObject;
                    const visitedLinks = new Set(); // Prevent infinite loops
                    
                    while (current.mergedInto) {
                        if (visitedLinks.has(current.id)) {
                            if (this.debugger) {
                                this.debugger.logError(`🚨 LOOP DETECTED in propagate up: ${current.id} already visited!`);
                            }
                            break;
                        }
                        visitedLinks.add(current.id);
                        
                        const parent = this.objects.find(o => o.id === current.mergedInto.parentId);
                        if (!parent) {
                            if (this.debugger) {
                                this.debugger.logError(`🚨 MP DRAG ERROR: Parent not found for ${current.id}`);
                                this.debugger.logError(`   mergedInto.parentId: ${current.mergedInto.parentId}`);
                            }
                            break;
                        }
                        
                        if (this.debugger) {
                            this.debugger.logInfo(`   ⬆️ Propagating to parent: ${parent.id}`);
                        }
                        
                        // Get which endpoint of Parent is connected to Child
                        const parentEndType = current.mergedInto.parentEndpoint;
                        if (!parentEndType) {
                            if (this.debugger) {
                                this.debugger.logError(`🚨 MP DRAG ERROR: parentEndpoint missing on ${current.id}`);
                            }
                            break;
                        }
                        const parentPoint = parentEndType === 'start' ? parent.start : parent.end;
                        
                        // Target point on Child (where Parent connects)
                        const childEndType = current.mergedInto.childEndpoint;
                        if (!childEndType) {
                            if (this.debugger) {
                                this.debugger.logError(`🚨 MP DRAG ERROR: childEndpoint missing on ${current.id}`);
                            }
                            break;
                        }
                        const targetPoint = childEndType === 'start' ? current.start : current.end;
                        
                        const diffX = targetPoint.x - parentPoint.x;
                        const diffY = targetPoint.y - parentPoint.y;
                        
                        if (Math.abs(diffX) > 0.01 || Math.abs(diffY) > 0.01) {
                            if (this.debugger) {
                                this.debugger.logInfo(`      Moving ${parent.id} by (${diffX.toFixed(1)}, ${diffY.toFixed(1)})`);
                            }
                            
                            parent.start.x += diffX;
                            parent.start.y += diffY;
                            parent.end.x += diffX;
                            parent.end.y += diffY;
                            
                            // Update MP metadata
                            if (parent.mergedInto) {
                                parent.mergedInto.connectionPoint.x += diffX;
                                parent.mergedInto.connectionPoint.y += diffY;
                            }
                            if (parent.mergedWith) {
                                parent.mergedWith.connectionPoint.x += diffX;
                                parent.mergedWith.connectionPoint.y += diffY;
                            }
                            
                            current = parent;
                        } else {
                            break; // Chain stable
                        }
                    }
                    
                    // Propagate Down (Children)
                    current = this.selectedObject;
                    visitedLinks.clear(); // Reuse set for down propagation
                    
                    while (current.mergedWith) {
                        if (visitedLinks.has(current.id)) {
                            if (this.debugger) {
                                this.debugger.logError(`🚨 LOOP DETECTED in propagate down: ${current.id} already visited!`);
                            }
                            break;
                        }
                        visitedLinks.add(current.id);
                        
                        const child = this.objects.find(o => o.id === current.mergedWith.linkId);
                        if (!child) break;
                        
                        if (this.debugger) {
                            this.debugger.logInfo(`   ⬇️ Propagating to child: ${child.id}`);
                        }
                        
                        // Parent (current) moved. Child must move to match.
                        
                        const parentEndType = current.mergedWith.connectionEndpoint; // Parent's end
                        const targetPoint = parentEndType === 'start' ? current.start : current.end;
                        
                        const childEndType = current.mergedWith.childConnectionEndpoint; // Child's end
                        const childPoint = childEndType === 'start' ? child.start : child.end;
                        
                        const diffX = targetPoint.x - childPoint.x;
                        const diffY = targetPoint.y - childPoint.y;
                        
                        if (Math.abs(diffX) > 0.01 || Math.abs(diffY) > 0.01) {
                            if (this.debugger) {
                                this.debugger.logInfo(`      Moving ${child.id} by (${diffX.toFixed(1)}, ${diffY.toFixed(1)})`);
                            }
                            
                            child.start.x += diffX;
                            child.start.y += diffY;
                            child.end.x += diffX;
                            child.end.y += diffY;
                            
                             // Update MP metadata
                            if (child.mergedInto) {
                                child.mergedInto.connectionPoint.x += diffX;
                                child.mergedInto.connectionPoint.y += diffY;
                            }
                            if (child.mergedWith) {
                                child.mergedWith.connectionPoint.x += diffX;
                                child.mergedWith.connectionPoint.y += diffY;
                            }
                            
                            current = child;
                        } else {
                            break;
                        }
                    }
                    
                    // Update connection points for the selected object itself
                    if (this.selectedObject.mergedWith) {
                        // The connection point is shared with child
                         const child = this.objects.find(o => o.id === this.selectedObject.mergedWith.linkId);
                         // We already moved child above. Just sync metadata.
                         const pEnd = this.selectedObject.mergedWith.connectionEndpoint === 'start' ? this.selectedObject.start : this.selectedObject.end;
                         this.selectedObject.mergedWith.connectionPoint.x = pEnd.x;
                         this.selectedObject.mergedWith.connectionPoint.y = pEnd.y;
                    }
                    if (this.selectedObject.mergedInto) {
                        const pEnd = this.selectedObject.mergedInto.childEndpoint === 'start' ? this.selectedObject.start : this.selectedObject.end;
                         this.selectedObject.mergedInto.connectionPoint.x = pEnd.x;
                         this.selectedObject.mergedInto.connectionPoint.y = pEnd.y;
                    }
                    
                    if (this.debugger && !this._unboundBodyDragLogged) {
                        this._unboundBodyDragLogged = true;
                        this.debugger.logSuccess(`↔️ BUL Chain moved: All linked ULs moved as unit`);
                    }
                    
                    this.draw();
                    this.updateHud(pos);
                    return;
                } else {
                    // CRITICAL FIX: If unboundLinkInitialPos is missing, initialize it now!
                    if (this.debugger) {
                        this.debugger.logWarning(`⚠️ Unbound link missing initial position - reinitializing`);
                    }
                    this.unboundLinkInitialPos = {
                        startX: this.selectedObject.start.x - dx,
                        startY: this.selectedObject.start.y - dy,
                        endX: this.selectedObject.end.x - dx,
                        endY: this.selectedObject.end.y - dy
                    };
                    this.draw();
                    this.updateHud(pos);
                    return;
                }
            }
            
            // ULTRA-FIXED: Calculate new position maintaining grab offset
            // CRITICAL: Validate dragStart is an offset, not mouse position
            // If dragStart looks like a mouse position (large values), recalculate offset
            const dragStartMag = Math.sqrt(this.dragStart.x * this.dragStart.x + this.dragStart.y * this.dragStart.y);
            
            // ENHANCED: Better heuristic - only validate for devices, not text
            // Text objects can have larger offsets if text is positioned far from origin
            const isDragStartMousePos = this.selectedObject.type !== 'text' && dragStartMag > 100;
            
            let actualOffsetX = this.dragStart.x;
            let actualOffsetY = this.dragStart.y;
            
            // CRITICAL FIX: If dragStart looks like mouse position, recalculate offset
            if (isDragStartMousePos && this.selectedObject.x !== undefined && this.selectedObject.y !== undefined) {
                // dragStart is incorrectly set to mouse position - recalculate offset
                actualOffsetX = pos.x - this.selectedObject.x;
                actualOffsetY = pos.y - this.selectedObject.y;
                
                // Update dragStart with correct offset
                this.dragStart = { x: actualOffsetX, y: actualOffsetY };
            }
            
            // Calculate new position
            let newX, newY;
            
            // For text objects, use stored initial positions for extra stability
            if (this.selectedObject.type === 'text' && this.textDragInitialPos) {
                // Calculate based on stored initial offset
                const mouseDx = pos.x - this.textDragInitialPos.mouseX;
                const mouseDy = pos.y - this.textDragInitialPos.mouseY;
                
                newX = this.textDragInitialPos.textX + mouseDx;
                newY = this.textDragInitialPos.textY + mouseDy;
            } else {
                // Standard position calculation for devices and other objects
                newX = pos.x - actualOffsetX;
                newY = pos.y - actualOffsetY;
            }
            
            // ENHANCED: Detailed jump detection and diagnostics
            // CRITICAL FIX: Only check for jumps on objects with x/y properties (devices, text)
            if (this.debugger && this.selectedObject.x !== undefined && this.selectedObject.y !== undefined) {
                const jumpX = Math.abs(newX - this.selectedObject.x);
                const jumpY = Math.abs(newY - this.selectedObject.y);
                if (jumpX > 50 || jumpY > 50) {
                    // CRITICAL FIX: Only log jump ONCE per drag session, not every frame!
                    if (!this._jumpDetectedThisDrag) {
                        this._jumpDetectedThisDrag = true; // Set flag to prevent spam
                        
                        // Log comprehensive jump diagnostic (single logError call with all info)
                        const jumpDiagnostics = `🚨 JUMP DETECTED! Delta: (${Math.round(jumpX)}, ${Math.round(jumpY)})
═══ JUMP DIAGNOSTICS ═══
Current obj pos: (${this.selectedObject.x.toFixed(2)}, ${this.selectedObject.y.toFixed(2)})
Calculated new pos: (${newX.toFixed(2)}, ${newY.toFixed(2)})
Mouse world pos: (${pos.x.toFixed(2)}, ${pos.y.toFixed(2)})
Drag offset: (${this.dragStart.x.toFixed(2)}, ${this.dragStart.y.toFixed(2)})
Actual offset used: (${actualOffsetX.toFixed(2)}, ${actualOffsetY.toFixed(2)})
Zoom: ${this.zoom.toFixed(3)}, Pan: (${this.panOffset.x.toFixed(2)}, ${this.panOffset.y.toFixed(2)})`;
                        
                        this.debugger.logError(jumpDiagnostics);
                        
                        // Copy this to the bug alert automatically
                        const bugDetails = `Jump: (${Math.round(jumpX)}, ${Math.round(jumpY)})px | Obj: (${this.selectedObject.x.toFixed(0)}, ${this.selectedObject.y.toFixed(0)}) → (${newX.toFixed(0)}, ${newY.toFixed(0)}) | Offset: (${this.dragStart.x.toFixed(0)}, ${this.dragStart.y.toFixed(0)}) | Zoom: ${(this.zoom * 100).toFixed(0)}%`;
                        this.latestJumpDetails = bugDetails;
                    }
                }
            }
            
            // Track velocity for momentum (only for objects with x/y properties)
            if (this.momentum && this.lastDragPos && this.lastDragTime && 
                this.selectedObject.x !== undefined && this.selectedObject.y !== undefined) {
                const now = Date.now();
                const dt = now - this.lastDragTime;
                if (dt > 0) {
                    const dx = newX - this.selectedObject.x;
                    const dy = newY - this.selectedObject.y;
                    this.momentum.trackVelocity(dx, dy, dt);
                }
                this.lastDragPos = { x: this.selectedObject.x, y: this.selectedObject.y };
                this.lastDragTime = now;
            }
            
            // Apply collision detection if enabled (devices only)
            let finalX = newX;
            let finalY = newY;
            if (this.deviceCollision && this.selectedObject.type === 'device') {
                const proposedPos = this.checkDeviceCollision(this.selectedObject, newX, newY);
                finalX = proposedPos.x;
                finalY = proposedPos.y;
            }
            
            // CRITICAL FIX: Only set x/y if object has those properties
            if (this.selectedObject.x !== undefined && this.selectedObject.y !== undefined) {
                // Store old position for momentum transfer
                const oldX = this.selectedObject.x;
                const oldY = this.selectedObject.y;
                
                this.selectedObject.x = finalX;
                this.selectedObject.y = finalY;
                
                // Apply movable device chain reaction (push other devices on collision)
                // CRITICAL: Use actual mouse movement velocity, not just incremental position change
                if (this.movableDevices && this.selectedObject.type === 'device') {
                    // Calculate velocity from last drag position for more accurate momentum transfer
                    let velocityX = finalX - oldX;
                    let velocityY = finalY - oldY;
                    
                    // Amplify velocity during drag to make chain reactions more noticeable
                    const dragAmplification = 2.0; // Make dragging push stronger
                    velocityX *= dragAmplification;
                    velocityY *= dragAmplification;
                    
                    this.applyDeviceChainReaction(this.selectedObject, velocityX, velocityY);
                }
            }
            this.draw();
            this.updateHud(pos);
            
            // CRITICAL: Update PLACEMENT TRACKING in real-time during drag!
            if (this.debugger && this.selectedObject.x !== undefined && this.selectedObject.y !== undefined) {
                const clickTrackDiv = document.getElementById('debug-click-track');
                if (clickTrackDiv) {
                    const devicePos = { x: this.selectedObject.x, y: this.selectedObject.y };
                    const deviceGrid = this.worldToGrid(devicePos);
                    const mouseGrid = this.worldToGrid(pos);
                    
                    // Calculate relative position (mouse - device)
                    const relativePos = { x: pos.x - devicePos.x, y: pos.y - devicePos.y };
                    const relativeMag = Math.sqrt(relativePos.x * relativePos.x + relativePos.y * relativePos.y);
                    
                    // Calculate offset mismatch
                    const offsetDiffX = relativePos.x - this.dragStart.x;
                    const offsetDiffY = relativePos.y - this.dragStart.y;
                    const offsetMismatch = Math.sqrt(offsetDiffX * offsetDiffX + offsetDiffY * offsetDiffY);
                    
                    const inputSource = this._lastInputType || 'mouse';
                    const icon = inputSource === 'trackpad' ? '🖐️' : inputSource === 'mouse' ? '🖱️' : '👆';
                    
                    clickTrackDiv.innerHTML = `
                        <span style="color: #f39c12; font-weight: bold; font-size: 11px;">${icon} DRAGGING: ${this.selectedObject.label || 'Device'}</span><br>
                        <br>
                        <span style="color: #0ff; font-weight: bold;">📍 DEVICE POSITION:</span><br>
                        World: <span style="color: #0ff;">(${devicePos.x.toFixed(1)}, ${devicePos.y.toFixed(1)})</span><br>
                        Grid: <span style="color: #0ff;">(${Math.round(deviceGrid.x)}, ${Math.round(deviceGrid.y)})</span><br>
                        <br>
                        <span style="color: #fa0; font-weight: bold;">🖱️ MOUSE POSITION:</span><br>
                        World: <span style="color: #fa0;">(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)})</span><br>
                        Grid: <span style="color: #fa0;">(${Math.round(mouseGrid.x)}, ${Math.round(mouseGrid.y)})</span><br>
                        <br>
                        <span style="color: #667eea; font-weight: bold;">📏 RELATIVE (Mouse - Device):</span><br>
                        Delta: <span style="color: #667eea; font-weight: bold;">(${relativePos.x.toFixed(1)}, ${relativePos.y.toFixed(1)})</span><br>
                        Distance: <span style="color: #667eea;">${relativeMag.toFixed(1)}px</span><br>
                        <br>
                        <span style="color: #0f0; font-weight: bold;">📐 EXPECTED OFFSET:</span><br>
                        Stored: <span style="color: #0f0;">(${this.dragStart.x.toFixed(1)}, ${this.dragStart.y.toFixed(1)})</span><br>
                        <br>
                        <div style="padding: 4px; background: ${offsetMismatch > 1 ? 'rgba(231, 76, 60, 0.2)' : 'rgba(39, 174, 96, 0.2)'}; border-radius: 3px; border-left: 3px solid ${offsetMismatch > 1 ? '#e74c3c' : '#27ae60'}; margin-bottom: 6px;">
                            <span style="color: ${offsetMismatch > 1 ? '#f00' : '#0f0'}; font-weight: bold;">
                                ${offsetMismatch > 1 ? '🚨 OFFSET DRIFT DETECTED!' : '✓ Offset Stable'}
                            </span><br>
                            ${offsetMismatch > 1 ? `
                            <span style="color: #fff; font-size: 9px;">Expected relative: (${this.dragStart.x.toFixed(1)}, ${this.dragStart.y.toFixed(1)})</span><br>
                            <span style="color: #fff; font-size: 9px;">Actual relative: (${relativePos.x.toFixed(1)}, ${relativePos.y.toFixed(1)})</span><br>
                            <span style="color: #f00; font-size: 9px;">Drift: (${offsetDiffX.toFixed(1)}, ${offsetDiffY.toFixed(1)}) = ${offsetMismatch.toFixed(1)}px</span><br>
                            ` : `<span style="color: #0f0; font-size: 9px;">Offset maintaining correctly</span><br>`}
                        </div>
                        <span style="color: #888; font-size: 9px;">
                            State: ACTIVE DRAG<br>
                            Updates: Real-time (every frame)
                        </span>
                    `;
                }
            }
        } else if (this.currentTool === 'link' && this.linking && this.linkStart) {
            this.draw();
            this.drawLinkPreview(this.linkStart, pos);
        }
    }
    
    handleMouseUp(e) {
        // Device placement is now handled immediately in handleMouseDown
        
        // Get mouse position first - needed by multiple code paths
        const pos = this.getMousePos(e);
        
        // CRITICAL: Update tap duration when mouse is released
        // This allows us to detect if the first tap was a long press (which should not trigger double-tap)
        if (this._lastTapStartTime > 0) {
            const tapDuration = Date.now() - this._lastTapStartTime;
            // If tap was too long (long press), clear tap tracking to prevent double-tap
            if (tapDuration >= this.maxTapDuration) {
                this.lastTapTime = 0;
                this._lastTapDevice = null;
                this._lastTapPos = null;
                this._lastTapStartTime = 0;
            }
        }
        
        // Clear all timers
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
        if (this.marqueeTimer) {
            clearTimeout(this.marqueeTimer);
            this.marqueeTimer = null;
        }
        
        if (this.panning) {
            this.panning = false;
            this.updateCursor();
            return;
        }
        
        // If we deferred placement and did not start marquee selection, perform placement now
        if (this.placingDevice && this.placementPending && !this.marqueeActive) {
            const typeToPlace = this.placementPending.type;
            const clickDuration = Date.now() - this.placementPending.clickTime;
            const clickedPos = this.placementPending.startPos; // Where mouse actually clicked
            this.placementPending = null;
            
            // CRITICAL: Check if clicking on an existing device - prevent placement on top of devices!
            // This check works regardless of collision detection setting
            const clickedOnDevice = this.objects.find(obj => {
                if (obj.type === 'device') {
                    const dx = clickedPos.x - obj.x;
                    const dy = clickedPos.y - obj.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    // Use device radius + small tolerance for hitbox
                    return dist <= obj.radius + 5;
                }
                return false;
            });
            
            if (clickedOnDevice) {
                // Clicked on an existing device - cancel placement
                if (this.debugger) {
                    this.debugger.logWarning(`📍 Device placement cancelled - clicked on existing device: ${clickedOnDevice.label || clickedOnDevice.id}`);
                    this.debugger.logInfo(`   Use empty space to place new devices`);
                }
                return;
            }
            
            // Only place if it was a quick tap (< 200ms) - prevents accidental placement
            if (clickDuration < 200) {
                // CRITICAL FIX: Always use the CLICKED position, not the mouseup position
                // This ensures devices are placed exactly where clicked, even during rapid placement
                this.lastClickPos = clickedPos;
                // Pass clicked position directly to ensure accurate placement
                this.addDeviceAtPosition(typeToPlace, clickedPos.x, clickedPos.y);
                // Deselect the newly placed device
                this.selectedObject = null;
                this.selectedObjects = [];
                this.updatePropertiesPanel();
                this.draw();
                
                if (this.debugger) {
                    this.debugger.logInfo(`📍 Quick tap: Device placed (${clickDuration}ms) at clicked position`);
                }
            } else {
                if (this.debugger) {
                    this.debugger.logWarning(`📍 Long press detected (${clickDuration}ms) - placement cancelled`);
                }
            }
            
            return;
        }

        // Handle marquee selection release
        if (this.marqueeActive) {
            // Save start position before clearing
            const startPos = this.selectionRectStart;

            // Clear marquee visuals immediately
            this.marqueeActive = false;
            this.selectionRectangle = null; // Rectangle disappears immediately
            this.selectionRectStart = null;
            
            // Check if this was a very small drag (essentially a click) - cancel selection
            if (startPos && pos) {
                const dx = Math.abs(pos.x - startPos.x);
                const dy = Math.abs(pos.y - startPos.y);
                if (dx < 5 && dy < 5) {
                    // Very small movement - treat as click, cancel marquee
                    this.selectedObjects = [];
                    this.selectedObject = null;
                    
                    // SEAMLESS: Resume device placement if came from there
                    if (this.resumePlacementAfterMarquee) {
                        this.setDevicePlacementMode(this.resumePlacementAfterMarquee);
                        this.resumePlacementAfterMarquee = null;
                        
                        if (this.debugger) {
                            this.debugger.logInfo(`🔄 Seamless transition: MS cancelled → Device placement resumed`);
                        }
                    } else {
                        this.setMode('base');
                    }
                    
                    this.draw();
                    return;
                }
            }

            // After MS release, keep items selected; enable multi-select drag semantics
            if (this.selectedObjects.length > 0) {
                this.multiSelectMode = true; // Allow group drag on next mousedown
                
                // SEAMLESS: Resume link mode if came from there, otherwise stay in select
                if (this.resumeModeAfterMarquee === 'link') {
                    this.currentMode = 'link';
                    this.currentTool = 'link';
                    // Update UI to show link mode
                    document.getElementById('btn-base').classList.remove('active');
                    document.getElementById('btn-select').classList.remove('active');
                    document.getElementById('btn-link').classList.add('active');
                    this.updateModeIndicator();
                    
                    if (this.debugger) {
                        this.debugger.logSuccess(`👆 MS → LINK mode: ${this.selectedObjects.length} objects selected`);
                        this.debugger.logInfo(`Seamless transition back to LINK mode`);
                    }
                } else {
                    this.currentMode = 'select'; // Stay in select mode to handle multi-select
                    this.currentTool = 'select';
                    // Update UI to show select mode
                    document.getElementById('btn-base').classList.remove('active');
                    document.getElementById('btn-select').classList.add('active');
                    this.updateModeIndicator();
                    
                    if (this.debugger) {
                        this.debugger.logSuccess(`👆 MS mode: ${this.selectedObjects.length} objects selected`);
                    }
                }
                
                this.backgroundClickCount = 0; // Reset counter for new selection
                this.resumePlacementAfterMarquee = null;
                this.resumeModeAfterMarquee = null;
            } else {
                // No objects selected - SEAMLESS: Resume previous mode
                if (this.resumePlacementAfterMarquee) {
                    this.setDevicePlacementMode(this.resumePlacementAfterMarquee);
                    this.resumePlacementAfterMarquee = null;
                    
                    if (this.debugger) {
                        this.debugger.logInfo(`🔄 Seamless transition: MS empty → Device placement resumed`);
                    }
                } else if (this.resumeModeAfterMarquee) {
                    const modeToResume = this.resumeModeAfterMarquee;
                    this.setMode(modeToResume);
                    this.resumeModeAfterMarquee = null;
                    
                    if (this.debugger) {
                        this.debugger.logInfo(`🔄 Seamless transition: MS empty → ${modeToResume.toUpperCase()} resumed`);
                    }
                } else {
                    this.setMode('base');
                }
            }
            
            this.draw(); // Redraw without rectangle
            return;
        }
        
        // Apply momentum/sliding if dragging ended
        // CRITICAL: Don't apply momentum if we were resizing or rotating (interferes with handles)
        // CRITICAL FIX: Don't apply momentum if there was no significant movement (just a tap/click)
        if (this.dragging && this.momentum && this.momentum.enabled && this.selectedObject &&
            !this.resizingDevice && !this.rotatingDevice) {
            
            // Check if there was actual movement (not just a tap)
            let actuallyMoved = false;
            const minDragDistance = 3; // Minimum pixels of movement to be considered a drag
            
            if (this.dragStartPos) {
                if (this.selectedObject.type === 'unbound') {
                    // For unbound links, check center position movement
                    const currentCenterX = (this.selectedObject.start.x + this.selectedObject.end.x) / 2;
                    const currentCenterY = (this.selectedObject.start.y + this.selectedObject.end.y) / 2;
                    const dx = currentCenterX - this.dragStartPos.x;
                    const dy = currentCenterY - this.dragStartPos.y;
                    const dragDistance = Math.sqrt(dx * dx + dy * dy);
                    actuallyMoved = dragDistance > minDragDistance;
                } else if (this.selectedObject.x !== undefined && this.selectedObject.y !== undefined) {
                    // For devices and text objects
                    const dx = this.selectedObject.x - this.dragStartPos.x;
                    const dy = this.selectedObject.y - this.dragStartPos.y;
                    const dragDistance = Math.sqrt(dx * dx + dy * dy);
                    actuallyMoved = dragDistance > minDragDistance;
                } else {
                    // Fallback: check velocity history
                    actuallyMoved = this.momentum.velocityHistory.length > 2;
                }
            } else {
                // For objects without stored start position, check velocity history
                actuallyMoved = this.momentum.velocityHistory.length > 2;
            }
            
            // Only apply momentum if there was actual dragging movement
            if (actuallyMoved) {
            const velocity = this.momentum.calculateReleaseVelocity();
            const speed = Math.sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy);
            
            if (speed > this.momentum.minVelocity) {
                // Start sliding for this object
                this.momentum.startSlide(this.selectedObject, velocity.vx, velocity.vy);
                }
            } else {
                // No movement detected - this was just a tap/click, not a drag
                // Reduced logging: Don't log every tap
                // if (this.debugger) {
                //     this.debugger.logInfo(`✓ Tap detected (no drag)`);
                // }
            }
        }
        
        // Save state after any operation completes (before clearing flags)
        // This captures the FINAL state after drag/resize/rotate/text operations
        if (this.dragging || this.resizingText || this.rotatingText || this.rotatingDevice || this.stretchingLink) {
            console.log('Saving final state after operation');
            // Don't save immediately if momentum slide is starting (it will save when slide ends)
            if (!(this.momentum && this.momentum.activeSlides.size > 0)) {
                this.saveState(); // Capture final state and trigger auto-save
            }
        }
        
        this.rotatingText = false;
        this.resizingText = false;
        if (this.rotatingDevice) {
            this.rotatingDevice = null; // Clear device rotation state
            this.updateCursor(); // Reset cursor after rotation
        }
        
        // CRITICAL: Check if stretching link endpoint should attach to a device OR another UL endpoint
        // Only attach if sticky links mode is enabled
        if (this.stretchingLink && this.stretchingEndpoint && this.linkStickyMode) {
            const endpointPos = this.stretchingEndpoint === 'start' 
                ? this.stretchingLink.start 
                : this.stretchingLink.end;
            
            // CRITICAL FIX: Check if the stretching endpoint is a FREE TP (not an MP)
            // Only FREE TPs can merge with other FREE TPs to create new MPs
            let stretchingEndpointIsFree = true;
            
            // If we're dragging a connection point (MP), it's not free
            if (this.stretchingConnectionPoint) {
                stretchingEndpointIsFree = false;
            }
            
            // Check if stretchingLink is part of a BUL and if the stretchingEndpoint is an MP
            if (this.stretchingLink.mergedWith) {
                // This link is a parent in a BUL
                // parentFreeEnd tells us which end IS FREE, the opposite is an MP
                const parentFreeEnd = this.stretchingLink.mergedWith.parentFreeEnd;
                if (this.stretchingEndpoint !== parentFreeEnd) {
                    // We're dragging the connected end (MP), not the free end
                    stretchingEndpointIsFree = false;
                }
            }
            
            if (this.stretchingLink.mergedInto) {
                // This link is a child in a BUL
                const parentLink = this.objects.find(o => o.id === this.stretchingLink.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    // childFreeEnd tells us which end of this child IS FREE
                    const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                    if (this.stretchingEndpoint !== childFreeEnd) {
                        // We're dragging the connected end (MP), not the free end
                        stretchingEndpointIsFree = false;
                    }
                }
            }
            
            // ENHANCED: First check for nearby UL endpoints to snap together
            // CRITICAL: Only look for merge candidates if the stretching endpoint is FREE
            let nearbyULEndpoint = null;
            let nearbyULLink = null;
            let nearbyULEndpointType = null;
            let ulSnapDistance = Infinity;
            
            // Only search for merge targets if the stretching endpoint is a FREE TP
            if (!stretchingEndpointIsFree) {
                if (this.debugger) {
                    this.debugger.logInfo(`🚫 Dragging MP, not TP - skipping merge search`);
                }
                // Skip to device attachment logic (MPs don't merge but TPs do)
            } else {
            this.objects.forEach(obj => {
                if (obj.type === 'unbound' && obj.id !== this.stretchingLink.id) {
                    // CRITICAL: Skip middle links entirely - they have NO free ends!
                    // If a link has BOTH mergedInto AND mergedWith, both ends are MPs
                    if (obj.mergedInto && obj.mergedWith) {
                        return; // Skip this link completely - it's in the middle of a chain
                    }
                    
                    // ENHANCED: Skip endpoints that are:
                    // 1. Attached to devices (they're not available for merging)
                    // 2. Connection points (endpoints that are already merged)
                    
                    // Check if start endpoint is a connection point (MP)
                    let startIsConnectionPoint = false;
                    if (obj.connectedTo && obj.connectedTo.thisEndpoint === 'start') {
                        startIsConnectionPoint = true;
                    } else if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'start') {
                        // This is a parent link, and start is the connected end (not free)
                        startIsConnectionPoint = true;
                    } else if (obj.mergedInto) {
                        // This is a child link - check which end is connected
                        const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
                        if (parentLink && parentLink.mergedWith) {
                            // Child's connected end is opposite of child's free end
                            const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                            startIsConnectionPoint = (childFreeEnd !== 'start'); // Start is connected if it's NOT the free end
                        }
                    }
                    
                    // CRITICAL ADDITIONAL CHECK: If this link has BOTH parent and child,
                    // it's in the MIDDLE of a chain and BOTH ends are MPs!
                    if (!startIsConnectionPoint && obj.mergedInto && obj.mergedWith) {
                        // Link in middle - both ends are connection points (MPs)
                        // Neither end is available for merging
                        startIsConnectionPoint = true;
                    }
                    
                    // Check start endpoint (only if not attached to device AND not a connection point)
                    if (!obj.device1 && !startIsConnectionPoint) {
                    const distStart = Math.sqrt(
                        Math.pow(endpointPos.x - obj.start.x, 2) + 
                        Math.pow(endpointPos.y - obj.start.y, 2)
                    );
                    if (distStart < this.ulSnapDistance && distStart < ulSnapDistance) {
                        nearbyULEndpoint = obj.start;
                        nearbyULLink = obj;
                        nearbyULEndpointType = 'start';
                        ulSnapDistance = distStart;
                        }
                    }
                    
                    // Check if end endpoint is a connection point (MP)
                    let endIsConnectionPoint = false;
                    if (obj.connectedTo && obj.connectedTo.thisEndpoint === 'end') {
                        endIsConnectionPoint = true;
                    } else if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'end') {
                        // This is a parent link, and end is the connected end (not free)
                        endIsConnectionPoint = true;
                    } else if (obj.mergedInto) {
                        // This is a child link - check which end is connected
                        const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
                        if (parentLink && parentLink.mergedWith) {
                            // Child's connected end is opposite of child's free end
                            const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                            endIsConnectionPoint = (childFreeEnd !== 'end'); // End is connected if it's NOT the free end
                        }
                    }
                    
                    // CRITICAL ADDITIONAL CHECK: If this link has BOTH parent and child,
                    // it's in the MIDDLE of a chain and BOTH ends are MPs!
                    if (!endIsConnectionPoint && obj.mergedInto && obj.mergedWith) {
                        // Link in middle - both ends are connection points (MPs)
                        // Neither end is available for merging
                        endIsConnectionPoint = true;
                    }
                    
                    // Check end endpoint (only if not attached to device AND not a connection point)
                    if (!obj.device2 && !endIsConnectionPoint) {
                    const distEnd = Math.sqrt(
                        Math.pow(endpointPos.x - obj.end.x, 2) + 
                        Math.pow(endpointPos.y - obj.end.y, 2)
                    );
                    if (distEnd < this.ulSnapDistance && distEnd < ulSnapDistance) {
                        nearbyULEndpoint = obj.end;
                        nearbyULLink = obj;
                        nearbyULEndpointType = 'end';
                        ulSnapDistance = distEnd;
                        }
                    }
                }
            });
            } // Close the else block for stretchingEndpointIsFree check
            
            // If found nearby UL endpoint, snap and merge the links into one logical link
            if (nearbyULLink && nearbyULEndpoint) {
                // CRITICAL: Check if these two links already share an MP (connection point)
                // If they do, prevent creating another connection between their free TPs
                const alreadyShareMP = this.linksAlreadyShareMP(this.stretchingLink, nearbyULLink);
                
                if (alreadyShareMP) {
                    // These links already have an MP together - don't allow another connection
                    if (this.debugger) {
                        this.debugger.logInfo(`🚫 Cannot merge: Links already share an MP`);
                    }
                    // Don't merge - just return without creating new connection
                    return;
                }
                
                // CRITICAL: Snap the NEW link's endpoint to the EXISTING link's endpoint
                // The existing link stays in place - only the new link moves to connect
                // This ensures links keep their position when merging
                if (this.stretchingEndpoint === 'start') {
                    this.stretchingLink.start.x = nearbyULEndpoint.x;
                    this.stretchingLink.start.y = nearbyULEndpoint.y;
                } else {
                    this.stretchingLink.end.x = nearbyULEndpoint.x;
                    this.stretchingLink.end.y = nearbyULEndpoint.y;
                }
                
                // UNIFIED TP MERGE: Simplified, geometry-based merge logic
                const connectionPoint = { x: nearbyULEndpoint.x, y: nearbyULEndpoint.y };
                
                // Helper: Find the actual chain end (not middle links)
                const findChainEnd = (link, direction) => {
                    if (!link) return null;
                    let current = link;
                    if (direction === 'parent') {
                        while (current.mergedInto) {
                            const parent = this.objects.find(o => o.id === current.mergedInto.parentId);
                            if (!parent) break;
                            current = parent;
                        }
                    } else {
                        while (current.mergedWith) {
                            const child = this.objects.find(o => o.id === current.mergedWith.linkId);
                            if (!child) break;
                            current = child;
                        }
                    }
                    return current;
                };
                
                // Step 1: Find actual chain ends (never merge to middle links)
                let targetLink = nearbyULLink;
                let targetEndpoint = nearbyULEndpointType;
                
                // If target is a middle link (both mergedInto and mergedWith), find the chain end
                if (targetLink.mergedInto && targetLink.mergedWith) {
                    // Determine which side we're closer to
                    const parentEnd = findChainEnd(targetLink, 'parent');
                    const childEnd = findChainEnd(targetLink, 'child');
                    
                    const parentDist = parentEnd ? Math.hypot(
                        (parentEnd[parentEnd.mergedWith?.parentFreeEnd || 'start']?.x || 0) - connectionPoint.x,
                        (parentEnd[parentEnd.mergedWith?.parentFreeEnd || 'start']?.y || 0) - connectionPoint.y
                    ) : Infinity;
                    
                    const childDist = childEnd ? Math.hypot(
                        (childEnd[childEnd.mergedInto ? (this.objects.find(o => o.id === childEnd.mergedInto.parentId)?.mergedWith?.childFreeEnd || 'start') : 'start']?.x || 0) - connectionPoint.x,
                        (childEnd[childEnd.mergedInto ? (this.objects.find(o => o.id === childEnd.mergedInto.parentId)?.mergedWith?.childFreeEnd || 'start') : 'start']?.y || 0) - connectionPoint.y
                    ) : Infinity;
                    
                    if (parentDist < childDist && parentEnd) {
                        targetLink = parentEnd;
                        targetEndpoint = parentEnd.mergedWith?.parentFreeEnd || 'start';
                    } else if (childEnd) {
                        targetLink = childEnd;
                        const childParent = this.objects.find(o => o.id === childEnd.mergedInto?.parentId);
                        targetEndpoint = childParent?.mergedWith?.childFreeEnd || 'end';
                    }
                } else if (targetLink.mergedWith && !targetLink.mergedInto) {
                    // Target is a parent - if connecting to occupied end, find chain end
                    const targetFreeEnd = targetLink.mergedWith.parentFreeEnd;
                    if (targetEndpoint !== targetFreeEnd) {
                        const chainEnd = findChainEnd(targetLink, 'child');
                        if (chainEnd) {
                            targetLink = chainEnd;
                            const chainParent = this.objects.find(o => o.id === chainEnd.mergedInto?.parentId);
                            targetEndpoint = chainParent?.mergedWith?.childFreeEnd || 'end';
                        }
                    }
                } else if (targetLink.mergedInto && !targetLink.mergedWith) {
                    // Target is a TAIL (child with no children of its own)
                    // CRITICAL FIX: Don't redirect to head! Keep the tail and use its free end
                    // The tail's free end is stored in its parent's mergedWith metadata
                    const tailParent = this.objects.find(o => o.id === targetLink.mergedInto.parentId);
                    if (tailParent?.mergedWith) {
                        targetEndpoint = tailParent.mergedWith.childFreeEnd;
                    }
                    // Keep targetLink as-is (the tail) - don't redirect to head!
                }
                
                // Step 2: Determine parent/child relationship
                // ENHANCED: Unified logic for all merge scenarios
                
                let parentLink = targetLink;
                let childLink = this.stretchingLink;
                
                // Check if links are in BULs
                const stretchingIsInBUL = childLink.mergedWith || childLink.mergedInto;
                const targetIsInBUL = parentLink.mergedWith || parentLink.mergedInto;
                
                // Helper to renumber MPs in a chain
                const renumberChainMPs = (startLink) => {
                    let current = findChainEnd(startLink, 'parent') || startLink;
                    let count = 0;
                    const chainLinks = [];
                    
                    // First pass: collect all links
                    let temp = current;
                    while (temp) {
                        chainLinks.push(temp);
                        if (!temp.mergedWith) break;
                        const nextId = temp.mergedWith.linkId;
                        temp = this.objects.find(o => o.id === nextId);
                    }
                    
                    // Second pass: assign MP numbers
                    // MP-1 is between Link 1 and Link 2
                    for (let i = 0; i < chainLinks.length - 1; i++) {
                        const link = chainLinks[i];
                        if (link.mergedWith) {
                            link.mergedWith.mpNumber = i + 1;
                        }
                    }
                };

                // CRITICAL CASE: Standalone UL joining BUL (or vice versa)
                if (!stretchingIsInBUL && targetIsInBUL) {
                    // Standalone UL (childLink) -> BUL (parentLink)
                    
                    const chainHead = findChainEnd(parentLink, 'parent') || parentLink;
                    const chainTail = findChainEnd(parentLink, 'child') || parentLink;
                    
                    // CRITICAL FIX: Check BOTH the link AND the endpoint to determine head/tail
                    // Get the free endpoint of head and tail
                    const headFreeEnd = chainHead.mergedWith ? chainHead.mergedWith.parentFreeEnd : null;
                    const tailFreeEnd = chainTail.mergedInto ? (() => {
                        const tailParent = this.objects.find(o => o.id === chainTail.mergedInto.parentId);
                        return tailParent?.mergedWith?.childFreeEnd || null;
                    })() : null;
                    
                    // FIXED: Check BOTH link match AND endpoint match
                    const detectIsHead = nearbyULLink.id === chainHead.id && 
                                        (headFreeEnd === null || nearbyULEndpointType === headFreeEnd);
                    const detectIsTail = nearbyULLink.id === chainTail.id && 
                                        (tailFreeEnd === null || nearbyULEndpointType === tailFreeEnd);
                    
                    if (this.debugger) {
                        this.debugger.logInfo(`🔍 BUL Extension Detection:`);
                        this.debugger.logInfo(`   Nearby link: ${nearbyULLink.id}, endpoint: ${nearbyULEndpointType}`);
                        this.debugger.logInfo(`   Chain head: ${chainHead.id}, free end: ${headFreeEnd}`);
                        this.debugger.logInfo(`   Chain tail: ${chainTail.id}, free end: ${tailFreeEnd}`);
                        this.debugger.logInfo(`   detectIsHead: ${detectIsHead}, detectIsTail: ${detectIsTail}`);
                    }
                    
                    if (detectIsHead) {
                        // PREPEND: Connecting to HEAD
                        // Set parentLink to head and get its free end
                        parentLink = chainHead;
                        if (chainHead.mergedWith) {
                            targetEndpoint = chainHead.mergedWith.parentFreeEnd;
                        }
                        
                        // SWAP: Standalone becomes parent
                        [parentLink, childLink] = [childLink, parentLink];
                        
                        if (this.debugger) this.debugger.logInfo('   🔄 PREPEND to HEAD: Standalone→Parent, Head→Child');
                        
                    } else if (detectIsTail) {
                        // APPEND: Connecting to TAIL  
                        // Set parentLink to tail and get its free end
                        parentLink = chainTail;
                        if (chainTail.mergedInto) {
                            const tailParent = this.objects.find(o => o.id === chainTail.mergedInto.parentId);
                            if (tailParent?.mergedWith) {
                                targetEndpoint = tailParent.mergedWith.childFreeEnd;
                            }
                        }
                        
                        // NO SWAP: Tail stays as parent, Standalone is child
                        // parentLink = UL-2, childLink = UL-3
                        
                        if (this.debugger) this.debugger.logInfo('   🔄 APPEND to TAIL: Tail→Parent, Standalone→Child');
                    } else {
                        // FALLBACK: Neither head nor tail detected (shouldn't happen if targetIsInBUL)
                        if (this.debugger) {
                            this.debugger.logWarning(`⚠️ Neither HEAD nor TAIL detected for BUL extension!`);
                            this.debugger.logWarning(`   This may indicate wrong endpoint selected or middle link clicked`);
                        }
                    }

                } else if (stretchingIsInBUL && !targetIsInBUL) {
                    // BUL (childLink) -> Standalone (parentLink)
                    
                    const chainHead = findChainEnd(childLink, 'parent') || childLink;
                    const chainTail = findChainEnd(childLink, 'child') || childLink;
                    
                    // FIXED: Check BOTH link and endpoint to determine if dragging from head or tail
                    const isHead = childLink.id === chainHead.id;
                    const isTail = childLink.id === chainTail.id;
                    
                    // Get free endpoints
                    const headFreeEnd = isHead && chainHead.mergedWith ? chainHead.mergedWith.parentFreeEnd : null;
                    const tailFreeEnd = isTail && chainTail.mergedInto ? (() => {
                        const tailParent = this.objects.find(o => o.id === chainTail.mergedInto.parentId);
                        return tailParent?.mergedWith?.childFreeEnd || null;
                    })() : null;
                    
                    // Check if dragging Head's free end (Prepend)
                    let isPrepend = false;
                    let isAppend = false;
                    
                    if (isHead && headFreeEnd && this.stretchingEndpoint === headFreeEnd) {
                        isPrepend = true;
                    } else if (isTail && tailFreeEnd && this.stretchingEndpoint === tailFreeEnd) {
                        isAppend = true;
                    } else if (!isHead && !isTail) {
                        // Dragging middle link - determine which end based on stretching endpoint
                        // If can't determine, default to append
                        isAppend = true;
                    }
                    
                    if (this.debugger) {
                        this.debugger.logInfo(`🔍 BUL→Standalone Detection:`);
                        this.debugger.logInfo(`   Stretching link: ${childLink.id}, endpoint: ${this.stretchingEndpoint}`);
                        this.debugger.logInfo(`   Chain head: ${chainHead.id}, free end: ${headFreeEnd}`);
                        this.debugger.logInfo(`   Chain tail: ${chainTail.id}, free end: ${tailFreeEnd}`);
                        this.debugger.logInfo(`   isPrepend: ${isPrepend}, isAppend: ${isAppend}`);
                    }

                    if (isPrepend) {
                        // Standalone -> Head. Standalone is Parent.
                        // No swap needed (parentLink is already Standalone)
                        // Make sure we're using the head as childLink
                        childLink = chainHead;
                        if (this.debugger) this.debugger.logInfo('   🔄 Dragged HEAD to Standalone (Prepend)');
                    } else {
                        // Tail -> Standalone (Append) or Middle link -> Standalone
                        // Tail becomes Parent, Standalone becomes Child
                        // Make sure we're using the tail
                        if (!isTail) {
                            childLink = chainTail;
                        }
                        [parentLink, childLink] = [childLink, parentLink];
                        if (this.debugger) this.debugger.logInfo('   🔄 Dragged TAIL to Standalone (Append)');
                    }
                } else if (stretchingIsInBUL && targetIsInBUL) {
                    // Both in BULs - join two chains
                    // Always append stretching chain to target chain (simplified)
                    
                    const targetChainTail = findChainEnd(parentLink, 'child') || parentLink;
                    const stretchingChainHead = findChainEnd(childLink, 'parent') || childLink;
                    
                    parentLink = targetChainTail;
                    childLink = stretchingChainHead;
                    
                    // FIXED: Get tail's free end directly from parent metadata (don't use getOppositeEndpoint)
                    if (targetChainTail.mergedInto) {
                        const tailParent = this.objects.find(o => o.id === targetChainTail.mergedInto.parentId);
                        if (tailParent?.mergedWith) {
                            targetEndpoint = tailParent.mergedWith.childFreeEnd;
                        }
                    } else {
                         targetEndpoint = targetChainTail.mergedWith ? targetChainTail.mergedWith.childFreeEnd : 'end';
                    }
                }

                // Step 3: Use geometry to detect actual connecting endpoints
                let parentConnectingEnd, childConnectingEnd;
                
                // Determine endpoints based on CURRENT roles (swapped or not)
                // We use the original stretching/target identifiers to map back to endpoints
                
                const isParentStretching = (parentLink.id === this.stretchingLink.id);
                const isChildStretching = (childLink.id === this.stretchingLink.id);
                
                if (isParentStretching) {
                    parentConnectingEnd = this.stretchingEndpoint; 
                } else {
                    // If parent was target, use targetEndpoint (already calculated above)
                    // FIXED: Don't recalculate with getOppositeEndpoint - use the targetEndpoint we already determined
                    parentConnectingEnd = targetEndpoint;
                }
                
                if (isChildStretching) {
                    childConnectingEnd = this.stretchingEndpoint;
                        } else {
                    // If child was target (e.g. dragging Head to Standalone -> Prepend)
                     if (childLink.mergedWith) {
                        childConnectingEnd = childLink.mergedWith.parentFreeEnd;
                    } else {
                        childConnectingEnd = this.getLinkEndpointNearPoint(childLink, connectionPoint) || (targetEndpoint === 'start' ? 'start' : 'end');
                    }
                }
                
                // Step 4: Calculate free ends
                // CRITICAL: For middle links (has both mergedInto and mergedWith), there is NO free end!
                // But we still need to store which end is "free" in the context of THIS merge
                let parentFreeEnd, childFreeEnd;
                
                // Check if parent will become middle link (already has mergedInto)
                if (parentLink.mergedInto) {
                    // Parent is/will be middle link - its "free" end is the one NOT connecting to child
                    parentFreeEnd = this.getOppositeEndpoint(parentConnectingEnd);
                    // This end is NOT actually free (it's connected to another link), but we need to store it
                    if (this.debugger) {
                        this.debugger.logWarning(`⚠️ ${parentLink.id} will be MIDDLE LINK - no truly free ends`);
                    }
                } else {
                    // Parent is head or standalone - free end is opposite of connecting end
                    parentFreeEnd = this.getOppositeEndpoint(parentConnectingEnd);
                }
                
                // Check if child will become middle link (already has mergedWith)  
                if (childLink.mergedWith) {
                    // Child is/will be middle link
                    childFreeEnd = this.getOppositeEndpoint(childConnectingEnd);
                    if (this.debugger) {
                        this.debugger.logWarning(`⚠️ ${childLink.id} will be MIDDLE LINK - no truly free ends`);
                    }
                } else {
                    // Child is tail or standalone
                    childFreeEnd = this.getOppositeEndpoint(childConnectingEnd);
                }
                
                if (this.debugger) {
                    this.debugger.logInfo(`   Calculated parentFreeEnd: ${parentFreeEnd} (opposite of ${parentConnectingEnd})`);
                    this.debugger.logInfo(`   Calculated childFreeEnd: ${childFreeEnd} (opposite of ${childConnectingEnd})`);
                }
                
                // Step 5: Merge
                if (!parentLink.mergedWith || parentLink.mergedWith.linkId !== childLink.id) {
                    // DEBUG: Log COMPLETE chain state before merge
                    if (this.debugger) {
                        this.debugger.logInfo(`━━━━━━━━━ BEFORE MERGE ━━━━━━━━━`);
                        
                        // Show entire existing chain if any
                        if (parentLink.mergedInto || parentLink.mergedWith) {
                            const existingChain = this.getAllMergedLinks(parentLink);
                            this.debugger.logInfo(`   Existing chain: ${existingChain.length} links`);
                            existingChain.forEach((link, i) => {
                                this.debugger.logInfo(`     U${i+1}: ${link.id} | ↑${link.mergedInto?.parentId || 'none'} | ↓${link.mergedWith?.linkId || 'none'}`);
                            });
                        }
                        
                        this.debugger.logInfo(`📝 Creating Merge Metadata:`);
                        this.debugger.logInfo(`   Parent: ${parentLink.id}`);
                        this.debugger.logInfo(`   Child: ${childLink.id}`);
                        this.debugger.logInfo(`   Parent state: mergedInto=${parentLink.mergedInto ? parentLink.mergedInto.parentId : 'none'}, mergedWith=${parentLink.mergedWith ? parentLink.mergedWith.linkId : 'none'}`);
                        this.debugger.logInfo(`   Child state: mergedInto=${childLink.mergedInto ? childLink.mergedInto.parentId : 'none'}, mergedWith=${childLink.mergedWith ? childLink.mergedWith.linkId : 'none'}`);
                        this.debugger.logInfo(`   Endpoints: parent-${parentConnectingEnd}, child-${childConnectingEnd}`);
                        this.debugger.logInfo(`   Free ends: parent-${parentFreeEnd}, child-${childFreeEnd}`);
                    }
                    
                    // Create merge
                // CRITICAL: Check if we're OVERWRITING existing connections before creating new ones
                const parentHadMergedWith = !!parentLink.mergedWith;
                const childHadMergedInto = !!childLink.mergedInto;
                
                parentLink.mergedWith = {
                    linkId: childLink.id,
                    connectionPoint: { x: connectionPoint.x, y: connectionPoint.y }, // Clone to avoid shared references!
                        parentFreeEnd: parentFreeEnd,
                        childFreeEnd: childFreeEnd,
                    childStart: { x: childLink.start.x, y: childLink.start.y },
                    childEnd: { x: childLink.end.x, y: childLink.end.y },
                        parentDevice: parentFreeEnd === 'start' ? parentLink.device1 : parentLink.device2,
                        childDevice: childFreeEnd === 'start' ? childLink.device1 : childLink.device2,
                    mpCreatedAt: Date.now(),
                        mpNumber: 0, // Will be updated by renumberChainMPs
                        connectionEndpoint: parentConnectingEnd,
                        childConnectionEndpoint: childConnectingEnd
                };
                
                // CRITICAL FIX: ALWAYS create/update childLink.mergedInto, even if it exists!
                // This is needed for prepend scenarios where childLink (after swap) already has mergedInto
                // But we need to ADD a new parent connection (the one we're creating now)
                // WAIT - a link can only have ONE parent! If childLink already has mergedInto, something is wrong!
                
                if (childHadMergedInto) {
                    if (this.debugger) {
                        this.debugger.logError(`🚨 CRITICAL: ${childLink.id} already has mergedInto! This means it's a middle/tail link being used as child.`);
                        this.debugger.logError(`   This is WRONG - child should only have mergedWith (be a parent), not mergedInto!`);
                        this.debugger.logError(`   Role swap may have failed!`);
                    }
                }
                
                childLink.mergedInto = {
                    parentId: parentLink.id,
                    connectionPoint: { x: connectionPoint.x, y: connectionPoint.y }, // Clone to avoid shared references
                            childEndpoint: childConnectingEnd,
                            parentEndpoint: parentConnectingEnd
                };
                
                // CRITICAL FIX: Ensure both links' endpoints are actually at the connection point
                // This fixes issues where TP combinations cause endpoints to be misaligned
                const cpX = connectionPoint.x;
                const cpY = connectionPoint.y;
                
                if (parentConnectingEnd === 'start') {
                    parentLink.start.x = cpX;
                    parentLink.start.y = cpY;
                } else {
                    parentLink.end.x = cpX;
                    parentLink.end.y = cpY;
                }
                
                if (childConnectingEnd === 'start') {
                    childLink.start.x = cpX;
                    childLink.start.y = cpY;
                } else {
                    childLink.end.x = cpX;
                    childLink.end.y = cpY;
                }
                
                // CRITICAL VALIDATION: Verify endpoints make sense
                if (this.debugger) {
                    // Check if stored endpoints match actual connection geometry
                    const parentActualEnd = parentConnectingEnd === 'start' ? parentLink.start : parentLink.end;
                    const childActualEnd = childConnectingEnd === 'start' ? childLink.start : childLink.end;
                    const dist = Math.hypot(
                        parentActualEnd.x - childActualEnd.x,
                        parentActualEnd.y - childActualEnd.y
                    );
                    
                    if (dist > 5) {
                        this.debugger.logError(`🚨 ENDPOINT MISMATCH: Stored endpoints don't connect!`);
                        this.debugger.logError(`   ${parentLink.id}[${parentConnectingEnd}] at (${parentActualEnd.x.toFixed(1)}, ${parentActualEnd.y.toFixed(1)})`);
                        this.debugger.logError(`   ${childLink.id}[${childConnectingEnd}] at (${childActualEnd.x.toFixed(1)}, ${childActualEnd.y.toFixed(1)})`);
                        this.debugger.logError(`   Distance: ${dist.toFixed(1)}px (should be ~0)`);
                    } else {
                        this.debugger.logSuccess(`✅ Endpoints validated: distance=${dist.toFixed(2)}px`);
                    }
                }
                
                    // DEBUG: Verify what was created
                    if (this.debugger) {
                        this.debugger.logSuccess(`✅ Merge Created Successfully`);
                        this.debugger.logInfo(`   ${parentLink.id}.mergedWith → ${childLink.id}`);
                        this.debugger.logInfo(`   ${childLink.id}.mergedInto → ${parentLink.id}`);
                        this.debugger.logInfo(`   Parent AFTER: mergedInto=${parentLink.mergedInto ? parentLink.mergedInto.parentId : 'none'}, mergedWith=${parentLink.mergedWith.linkId}`);
                        this.debugger.logInfo(`   Child AFTER: mergedInto=${childLink.mergedInto.parentId}, mergedWith=${childLink.mergedWith ? childLink.mergedWith.linkId : 'none'}`);
                        
                        // CRITICAL CHECK: If parent is UL-2 (middle link), verify both connections intact
                        if (parentLink.mergedInto && parentLink.mergedWith) {
                            this.debugger.logWarning(`⚠️ MIDDLE LINK: ${parentLink.id} now has BOTH connections`);
                            this.debugger.logInfo(`   UP to: ${parentLink.mergedInto.parentId} (should be UL-1)`);
                            this.debugger.logInfo(`   DOWN to: ${parentLink.mergedWith.linkId} (should be UL-3)`);
                            this.debugger.logInfo(`   Check MP-1 metadata in UL-1.mergedWith:`);
                            const ul1 = this.objects.find(o => o.id === parentLink.mergedInto.parentId);
                            if (ul1?.mergedWith) {
                                this.debugger.logInfo(`   UL-1.mergedWith.linkId: ${ul1.mergedWith.linkId}`);
                                this.debugger.logInfo(`   UL-1.mergedWith.parentEndpoint: ${ul1.mergedWith.connectionEndpoint}`);
                                this.debugger.logInfo(`   UL-1.mergedWith.childEndpoint: ${ul1.mergedWith.childConnectionEndpoint}`);
                            }
                        }
                    }

                    // CRITICAL FIX: When creating a middle link, DON'T update parent's metadata!
                    // The parent's childFreeEnd/childConnectionEndpoint should STAY THE SAME
                    // because they describe how the parent connects to THIS child, not what the child does elsewhere
                    //
                    // KEY INSIGHT: childFreeEnd means "child's end that is NOT connecting to parent"
                    // When child was tail: end was free (not connecting to parent = start connects)
                    // When child is middle: end connects to grandchild (still not connecting to parent!)
                    // So childFreeEnd should NOT change! It's still the "other" end.
                    //
                    // The metadata is RELATIVE to the parent-child relationship, not absolute!
                    
                    // DEBUG ONLY: Verify grandparent metadata is still correct
                    if (this.debugger && parentLink.mergedInto) {
                        const grandparent = this.objects.find(o => o.id === parentLink.mergedInto.parentId);
                        if (grandparent?.mergedWith && grandparent.mergedWith.linkId === parentLink.id) {
                            this.debugger.logInfo(`🔍 ${grandparent.id}.mergedWith (MP-1) metadata unchanged:`);
                            this.debugger.logInfo(`   childFreeEnd: ${grandparent.mergedWith.childFreeEnd} (other end from connection)`);
                            this.debugger.logInfo(`   childConnectionEnd: ${grandparent.mergedWith.childConnectionEndpoint} (connects to ${grandparent.id})`);
                        }
                    }
                    
                    // Renumber MPs for the entire chain
                    renumberChainMPs(parentLink);
                    
                    // CRITICAL VERIFICATION: Check entire chain metadata integrity
                    if (this.debugger) {
                        const allLinks = this.getAllMergedLinks(parentLink);
                        this.debugger.logInfo(`🔍 VERIFICATION: Checking all ${allLinks.length} links in chain...`);
                        
                        allLinks.forEach((link, idx) => {
                            const hasParent = link.mergedInto ? '✓' : '✗';
                            const hasChild = link.mergedWith ? '✓' : '✗';
                            const parentId = link.mergedInto?.parentId || 'none';
                            const childId = link.mergedWith?.linkId || 'none';
                            
                            this.debugger.logInfo(`   U${idx+1} (${link.id}): ↑${hasParent} parent=${parentId}, ↓${hasChild} child=${childId}`);
                            
                            // Verify endpoints exist and are consistent
                            if (link.mergedWith) {
                                const cep = link.mergedWith.connectionEndpoint;
                                const ccep = link.mergedWith.childConnectionEndpoint;
                                const pfe = link.mergedWith.parentFreeEnd;
                                const cfe = link.mergedWith.childFreeEnd;
                                const cp = link.mergedWith.connectionPoint;
                                
                                if (!cep || !ccep || !pfe || !cfe) {
                                    this.debugger.logError(`🚨 MISSING ENDPOINTS in ${link.id}.mergedWith: cep=${cep}, ccep=${ccep}, pfe=${pfe}, cfe=${cfe}`);
                                } else {
                                    // Verify connection point matches actual endpoint
                                    const actualEndpoint = cep === 'start' ? link.start : link.end;
                                    if (cp && (Math.abs(cp.x - actualEndpoint.x) > 1 || Math.abs(cp.y - actualEndpoint.y) > 1)) {
                                        this.debugger.logWarning(`⚠️ CONNECTION POINT MISMATCH in ${link.id}.mergedWith:`);
                                        this.debugger.logWarning(`   connectionPoint: (${cp.x.toFixed(1)}, ${cp.y.toFixed(1)})`);
                                        this.debugger.logWarning(`   actual ${cep}: (${actualEndpoint.x.toFixed(1)}, ${actualEndpoint.y.toFixed(1)})`);
                                        // AUTO-FIX: Update connection point to match actual endpoint
                                        link.mergedWith.connectionPoint.x = actualEndpoint.x;
                                        link.mergedWith.connectionPoint.y = actualEndpoint.y;
                                        this.debugger.logSuccess(`   ✅ AUTO-FIXED connection point`);
                                    }
                                }
                            }
                            if (link.mergedInto) {
                                const pe = link.mergedInto.parentEndpoint;
                                const ce = link.mergedInto.childEndpoint;
                                const cp = link.mergedInto.connectionPoint;
                                
                                if (!pe || !ce) {
                                    this.debugger.logError(`🚨 MISSING ENDPOINTS in ${link.id}.mergedInto: pe=${pe}, ce=${ce}`);
                                } else {
                                    // Verify connection point matches actual child endpoint
                                    const actualEndpoint = ce === 'start' ? link.start : link.end;
                                    if (cp && (Math.abs(cp.x - actualEndpoint.x) > 1 || Math.abs(cp.y - actualEndpoint.y) > 1)) {
                                        this.debugger.logWarning(`⚠️ CONNECTION POINT MISMATCH in ${link.id}.mergedInto:`);
                                        this.debugger.logWarning(`   connectionPoint: (${cp.x.toFixed(1)}, ${cp.y.toFixed(1)})`);
                                        this.debugger.logWarning(`   actual ${ce}: (${actualEndpoint.x.toFixed(1)}, ${actualEndpoint.y.toFixed(1)})`);
                                        // AUTO-FIX: Update connection point to match actual endpoint
                                        link.mergedInto.connectionPoint.x = actualEndpoint.x;
                                        link.mergedInto.connectionPoint.y = actualEndpoint.y;
                                        this.debugger.logSuccess(`   ✅ AUTO-FIXED connection point`);
                                    }
                                }
                            }
                            
                            // CRITICAL: Verify middle links have consistent connections
                            if (link.mergedInto && link.mergedWith) {
                                this.debugger.logInfo(`      📍 MIDDLE LINK: ${link.id}`);
                                // The mergedInto.childEndpoint and mergedWith.connectionEndpoint should be DIFFERENT
                                // (one connects up, one connects down - they can't be the same endpoint!)
                                const upEndpoint = link.mergedInto.childEndpoint;
                                const downEndpoint = link.mergedWith.connectionEndpoint;
                                if (upEndpoint === downEndpoint) {
                                    this.debugger.logError(`🚨 INVALID MIDDLE LINK: ${link.id} uses same endpoint (${upEndpoint}) for both connections!`);
                                }
                            }
                        });
                    }
                        
                        // CRITICAL: Change originType to UL when links are merged
                    if (parentLink.originType === 'QL') parentLink.originType = 'UL';
                    if (childLink.originType === 'QL') childLink.originType = 'UL';
                    
                    // DEBUG: Log merge creation
                        if (this.debugger) {
                            const allLinks = this.getAllMergedLinks(parentLink);
                        const isExtending = allLinks.length > 2;
                        if (isExtending) {
                            this.debugger.logInfo(`🔗 Extending ${allLinks.length}-link BUL chain`);
                                } else {
                            this.debugger.logInfo(`🔗 Creating new 2-link BUL`);
                        }
                        this.debugger.logInfo(`   New link: ${this.stretchingLink.id}, connecting via ${this.stretchingEndpoint}`);
                        this.debugger.logInfo(`   Target link: ${nearbyULLink.id}, connecting to ${nearbyULEndpointType}`);
                        this.debugger.logSuccess(`✅ BUL ${isExtending ? 'extended' : 'created'}! Now ${allLinks.length} links in chain`);
                        
                        const parentUL = allLinks.findIndex(l => l.id === parentLink.id) + 1;
                        const childUL = allLinks.findIndex(l => l.id === childLink.id) + 1;
                        const parentTPUsed = parentFreeEnd === 'start' ? 'end' : 'start';
                        const childTPUsed = childFreeEnd === 'start' ? 'end' : 'start';
                        // Get MP number from the merge metadata (set by renumberChainMPs)
                        const mpNumber = parentLink.mergedWith?.mpNumber || 0;
                        this.debugger.logInfo(`   🔗 Merge: U${parentUL}-TP(${parentTPUsed}) + U${childUL}-TP(${childTPUsed}) → MP-${mpNumber}`);
                }
                
                // Copy device attachments from child to parent if needed
                    const finalChildFreeEnd = childFreeEnd;
                    const finalParentFreeEnd = parentFreeEnd;
                
                let deviceToCopy = null;
                
                if (finalChildFreeEnd === 'start' && childLink.device1) {
                    deviceToCopy = childLink.device1;
                } else if (finalChildFreeEnd === 'end' && childLink.device2) {
                    deviceToCopy = childLink.device2;
                } else if (childLink.mergedWith) {
                    // Child is also a parent - check its child's device
                    const grandchildLink = this.objects.find(o => o.id === childLink.mergedWith.linkId);
                    if (grandchildLink) {
                        const grandchildFreeEnd = childLink.mergedWith.childFreeEnd;
                        if (grandchildFreeEnd === 'start' && grandchildLink.device1) {
                            deviceToCopy = grandchildLink.device1;
                        } else if (grandchildFreeEnd === 'end' && grandchildLink.device2) {
                            deviceToCopy = grandchildLink.device2;
                        }
                    }
                    } else if (childLink.mergedInto) {
                        // Child is also a child (middle link) - we can't easily trace through parents
                        // But we can check its free end if it's directly attached
                        if (finalChildFreeEnd === 'start' && childLink.device1) deviceToCopy = childLink.device1;
                        if (finalChildFreeEnd === 'end' && childLink.device2) deviceToCopy = childLink.device2;
                }
                
                if (deviceToCopy) {
                    if (finalParentFreeEnd === 'start') {
                        parentLink.device1 = deviceToCopy;
                            // Clear from child to avoid duplication
                            if (finalChildFreeEnd === 'start') childLink.device1 = null;
                            else if (finalChildFreeEnd === 'end') childLink.device2 = null;
                    } else {
                        parentLink.device2 = deviceToCopy;
                            // Clear from child to avoid duplication
                            if (finalChildFreeEnd === 'start') childLink.device1 = null;
                            else if (finalChildFreeEnd === 'end') childLink.device2 = null;
                        }
                        if (this.debugger) {
                            this.debugger.logInfo(`   Moved device attachment: ${deviceToCopy} to parent free end`);
                    }
                }
                
                // Keep the connection tracking for rendering
                // CRITICAL: Use FINAL endpoints after role swapping, not original ones
                parentLink.connectedTo = {
                    linkId: childLink.id,
                    thisEndpoint: parentConnectingEnd,
                    otherEndpoint: childConnectingEnd
                };
                
                childLink.connectedTo = {
                    linkId: parentLink.id,
                    thisEndpoint: childConnectingEnd,
                    otherEndpoint: parentConnectingEnd
                };
                
                // CRITICAL: Update all connection points after merge to ensure chain is synced
                this.updateAllConnectionPoints();
                
                if (this.debugger) {
                    // Get all devices connected across the entire BUL chain
                    const connectedDevicesInfo = this.getAllConnectedDevices(parentLink);
                    const allLinksInChain = connectedDevicesInfo.links;
                    const deviceLabels = connectedDevicesInfo.devices.map(d => d.label || d.id).join(' ↔ ');
                    
                    // ENHANCED: Analyze BUL chain structure
                    const chainAnalysis = this.analyzeBULChain(parentLink);
                    
                    // Determine which link is new (the one being stretched)
                    const newLinkId = this.stretchingLink.id;
                    const isExtendingChain = allLinksInChain.length > 2;
                    
                    if (isExtendingChain) {
                        // Find which TPs were merged
                        const stretchingUL = allLinksInChain.findIndex(l => l.id === this.stretchingLink.id) + 1;
                        const targetUL = allLinksInChain.findIndex(l => l.id === nearbyULLink.id) + 1;
                        const stretchingTPUsed = this.stretchingEndpoint;
                        const targetTPUsed = nearbyULEndpointType;
                        
                        this.debugger.logSuccess(`🔗 BUL Extended: ${newLinkId} (U${stretchingUL}) added to chain`);
                        this.debugger.logInfo(`   🔗 Merge: U${stretchingUL}-TP(${stretchingTPUsed}) + U${targetUL}-TP(${targetTPUsed}) → MP`);
                        
                        // Collect TPs for numbering
                        // FIXED: Use clearer logic - endpoint is TP if NOT connected
                        const tpsInChain = [];
                        allLinksInChain.forEach(chainLink => {
                            let startIsConnected = false;
                            if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') startIsConnected = true;
                            if (chainLink.mergedInto) {
                                const parent = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'end') startIsConnected = true;
                            }
                            if (!startIsConnected) tpsInChain.push({ link: chainLink, endpoint: 'start' });
                            
                            let endIsConnected = false;
                            if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') endIsConnected = true;
                            if (chainLink.mergedInto) {
                                const parent = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'start') endIsConnected = true;
                            }
                            if (!endIsConnected) tpsInChain.push({ link: chainLink, endpoint: 'end' });
                        });
                        
                        // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                        tpsInChain.sort((a, b) => {
                            const ulNumA = parseInt(a.link.id.split('_')[1]) || 0;
                            const ulNumB = parseInt(b.link.id.split('_')[1]) || 0;
                            return ulNumA - ulNumB;
                        });
                        
                        // Build TP labels with detailed info
                        const tpLabels = tpsInChain.map((tp, idx) => {
                            const ulNum = allLinksInChain.findIndex(l => l.id === tp.link.id) + 1;
                            const endpointLabel = tp.endpoint === 'start' ? 'start' : 'end';
                            return `TP-${idx + 1}(U${ulNum}-${endpointLabel})`;
                        }).join(', ');
                        
                        // Build MP labels (per-BUL numbering)
                        const mps = [];
                        allLinksInChain.forEach(link => {
                            if (link.mergedWith?.mpNumber) {
                                const ulNum = allLinksInChain.findIndex(l => l.id === link.id) + 1;
                                mps.push({ num: link.mergedWith.mpNumber, ul: ulNum });
                            }
                        });
                        mps.sort((a, b) => a.num - b.num);
                        const mpLabels = mps.map(mp => `MP-${mp.num}(U${mp.ul})`).join(', ');
                        
                        this.debugger.logInfo(`   📊 Structure: ${chainAnalysis.linkCount} links | ${chainAnalysis.tpCount} TPs | ${chainAnalysis.mpCount} MPs`);
                        this.debugger.logInfo(`   🔸 TPs: ${tpLabels}`);
                        this.debugger.logInfo(`   🔸 MPs: ${mpLabels}`);
                        
                        // Show creation order for all links
                        const sortedLinks = allLinksInChain.sort((a, b) => (a.createdAt || 0) - (b.createdAt || 0));
                        const linkLabels = sortedLinks.map((l, i) => `${l.originType || 'UL'}${i + 1}`).join('--🟣--');
                        this.debugger.logInfo(`   📝 Chain: TP--${linkLabels}--TP`);
                        
                        this.debugger.logInfo(`   ${chainAnalysis.isValid ? '✅ Valid: 2 TPs at ends + ' + chainAnalysis.mpCount + ' MPs between' : '⚠️ Invalid structure detected!'}`);
                    } else {
                        // BUL Created (first merge of 2 ULs)
                        const parentUL = allLinksInChain.findIndex(l => l.id === parentLink.id) + 1;
                        const childUL = allLinksInChain.findIndex(l => l.id === childLink.id) + 1;
                        
                        // Calculate which TPs were used for merge
                        const parentTPUsed = parentFreeEnd === 'start' ? 'end' : 'start';
                        const childTPUsed = childFreeEnd === 'start' ? 'end' : 'start';
                        
                        this.debugger.logSuccess(`🔗 BUL Created: ${parentLink.id} (U${parentUL}) + ${childLink.id} (U${childUL})`);
                        this.debugger.logInfo(`   🔗 Merge: U${parentUL}-TP(${parentTPUsed}) + U${childUL}-TP(${childTPUsed}) → MP-1`);
                        
                        // Collect TPs for the new BUL
                        // FIXED: Use clearer logic - endpoint is TP if NOT connected
                        const tpsInChain = [];
                        allLinksInChain.forEach(chainLink => {
                            let startIsConnected = false;
                            if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') startIsConnected = true;
                            if (chainLink.mergedInto) {
                                const parent = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'end') startIsConnected = true;
                            }
                            if (!startIsConnected) tpsInChain.push({ link: chainLink, endpoint: 'start' });
                            
                            let endIsConnected = false;
                            if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') endIsConnected = true;
                            if (chainLink.mergedInto) {
                                const parent = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                                if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'start') endIsConnected = true;
                            }
                            if (!endIsConnected) tpsInChain.push({ link: chainLink, endpoint: 'end' });
                        });
                        
                        // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
                        tpsInChain.sort((a, b) => {
                            const ulNumA = parseInt(a.link.id.split('_')[1]) || 0;
                            const ulNumB = parseInt(b.link.id.split('_')[1]) || 0;
                            return ulNumA - ulNumB;
                        });
                        
                        const tpLabels = tpsInChain.map((tp, idx) => {
                            const ulNum = allLinksInChain.findIndex(l => l.id === tp.link.id) + 1;
                            const endpointLabel = tp.endpoint === 'start' ? 'start' : 'end';
                            return `TP-${idx + 1}(U${ulNum}-${endpointLabel})`;
                        }).join(', ');
                        
                        const mpNum = parentLink.mergedWith?.mpNumber || 1;
                        const mpUL = allLinksInChain.findIndex(l => l.id === parentLink.id) + 1;
                        
                        this.debugger.logInfo(`   📊 Structure: ${chainAnalysis.linkCount} links | ${chainAnalysis.tpCount} TPs | ${chainAnalysis.mpCount} MPs`);
                        this.debugger.logInfo(`   🔸 TPs: ${tpLabels}`);
                        this.debugger.logInfo(`   🔸 MPs: MP-${mpNum}(U${mpUL})`);
                        this.debugger.logInfo(`   📝 Chain: TP--${parentLink.originType || 'UL'}1--🟣--${childLink.originType || 'UL'}2--TP`);
                    }
                    
                    if (connectedDevicesInfo.count > 0) {
                        this.debugger.logInfo(`   Devices: ${deviceLabels}`);
                    }
                    }
                }
                
                // Force immediate draw to update labels
                this.draw();
            } else {
                // No UL snap, check for device attachment
                // CRITICAL: MPs (connection points) should NOT stick to devices!
                // Only TPs (free endpoints) can attach to devices
                if (!this.stretchingConnectionPoint) {
                    // This is a TP - allow device attachment
            let nearbyDevice = null;
            let snapDistance = Infinity;
            let snapAngle = 0;
            
            // ENHANCED: Larger attachment range for easier UL-to-device connection
            this.objects.forEach(obj => {
                if (obj.type === 'device') {
                    const dx = endpointPos.x - obj.x;
                    const dy = endpointPos.y - obj.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    const attachmentRange = obj.radius + 20; // Increased from 15 for better UX
                    
                    if (distance <= attachmentRange && distance < snapDistance) {
                        nearbyDevice = obj;
                        snapDistance = distance;
                        snapAngle = Math.atan2(dy, dx);
                    }
                }
            });
            
            if (nearbyDevice) {
                // Attach endpoint to device
                const wasAttached = (this.stretchingEndpoint === 'start' && this.stretchingLink.device1) ||
                                   (this.stretchingEndpoint === 'end' && this.stretchingLink.device2);
                
                if (this.stretchingEndpoint === 'start') {
                    this.stretchingLink.device1 = nearbyDevice.id;
                    // CRITICAL: Store the attachment angle to preserve connection location
                    this.stretchingLink.device1Angle = snapAngle;
                    // ENHANCED: Smooth snap to device edge
                    this.stretchingLink.start.x = nearbyDevice.x + Math.cos(snapAngle) * nearbyDevice.radius;
                    this.stretchingLink.start.y = nearbyDevice.y + Math.sin(snapAngle) * nearbyDevice.radius;
                    
                    // Reduced logging: Angle storage is automatic, don't log it
                    // if (this.debugger && !wasAttached) {
                    //     const angleDegrees = (snapAngle * 180 / Math.PI).toFixed(1);
                    //     this.debugger.logInfo(`📐 Attachment angle: ${angleDegrees}°`);
                    // }
                } else {
                    this.stretchingLink.device2 = nearbyDevice.id;
                    // CRITICAL: Store the attachment angle to preserve connection location
                    this.stretchingLink.device2Angle = snapAngle;
                    // ENHANCED: Smooth snap to device edge
                    this.stretchingLink.end.x = nearbyDevice.x + Math.cos(snapAngle) * nearbyDevice.radius;
                    this.stretchingLink.end.y = nearbyDevice.y + Math.sin(snapAngle) * nearbyDevice.radius;
                    
                    // Reduced logging: Angle storage is automatic, don't log it
                    // if (this.debugger && !wasAttached) {
                    //     const angleDegrees = (snapAngle * 180 / Math.PI).toFixed(1);
                    //     this.debugger.logInfo(`📐 Attachment angle: ${angleDegrees}°`);
                    // }
                }
                
                // ENHANCED: Recalculate linkIndex after attaching to device
                // This ensures proper offset for multiple links between same devices (QL + UL combined)
                const endpoints = this.getBULEndpointDevices(this.stretchingLink);
                if (endpoints.hasEndpoints) {
                    const oldIndex = this.stretchingLink.linkIndex || 0;
                    const newIndex = this.calculateLinkIndex(this.stretchingLink);
                    this.stretchingLink.linkIndex = newIndex;
                    
                    // Count all links between these devices for context
                    const allLinksBetween = this.objects.filter(obj => {
                        if (obj.type === 'link' && obj.device1 && obj.device2) {
                            return (obj.device1 === endpoints.device1 && obj.device2 === endpoints.device2) ||
                                   (obj.device1 === endpoints.device2 && obj.device2 === endpoints.device1);
                        }
                        if (obj.type === 'unbound') {
                            const objEnd = this.getBULEndpointDevices(obj);
                            if (objEnd.hasEndpoints) {
                                return (objEnd.device1 === endpoints.device1 && objEnd.device2 === endpoints.device2) ||
                                       (objEnd.device1 === endpoints.device2 && objEnd.device2 === endpoints.device1);
                            }
                        }
                        return false;
                    });
                    
                    if (this.debugger) {
                        const position = this.stretchingLink.linkIndex === 0 ? 'Middle' :
                                       this.stretchingLink.linkIndex % 2 === 1 ? 'Right' : 'Left';
                        const device1Name = this.objects.find(d => d.id === endpoints.device1)?.label || endpoints.device1;
                        const device2Name = this.objects.find(d => d.id === endpoints.device2)?.label || endpoints.device2;
                        
                        this.debugger.logSuccess(`📊 UL positioned: #${this.stretchingLink.linkIndex + 1} of ${allLinksBetween.length} (${position} side)`);
                        this.debugger.logInfo(`   Between: ${device1Name} ↔ ${device2Name}`);
                        this.debugger.logInfo(`   Link type: ${this.stretchingLink.originType || 'UL'} | Index: ${this.stretchingLink.linkIndex}`);
                        
                        // Show breakdown if multiple links
                        if (allLinksBetween.length > 1) {
                            const qlCount = allLinksBetween.filter(l => l.type === 'link').length;
                            const ulCount = allLinksBetween.filter(l => l.type === 'unbound').length;
                            this.debugger.logInfo(`   Mix: ${qlCount} QL + ${ulCount} UL = ${allLinksBetween.length} total`);
                            
                            // Log all links with their positions for debugging
                            const linkDetails = allLinksBetween.map((l, idx) => {
                                const type = l.type === 'link' ? 'QL' : 'UL';
                                const side = idx === 0 ? 'M' : (idx % 2 === 1 ? 'R' : 'L');
                                return `${type}${idx}(${side})`;
                            }).join(', ');
                            this.debugger.logInfo(`   Layout: ${linkDetails}`);
                        }
                    }
                }
                
                // DISABLED: No longer convert to regular link - keep as unbound link with TPs
                // This ensures all links always have 2 TPs at their ends
                // if (this.stretchingLink.device1 && this.stretchingLink.device2) {
                //     // Conversion logic disabled - links remain as 'unbound' type with start/end TPs
                // }
                
                if (!wasAttached) {
                    // Only log if this is a new attachment (not re-attaching)
                    if (this.debugger) {
                        // Check if this link is part of a BUL chain and show all connected devices
                        const connectedDevicesInfo = this.getAllConnectedDevices(this.stretchingLink);
                        const deviceLabels = connectedDevicesInfo.devices.map(d => d.label || d.id).join(', ');
                        
                        if (connectedDevicesInfo.count > 1) {
                            this.debugger.logSuccess(`🔗 Connected: ${deviceLabels}`);
                        } else {
                            this.debugger.logSuccess(`🔗 Attached to ${nearbyDevice.label || nearbyDevice.id}`);
                        }
                        
                        // Show link index if multiple links between same devices
                        if (this.stretchingLink.linkIndex > 0) {
                            const totalLinks = this.stretchingLink.linkIndex + 1;
                            this.debugger.logInfo(`   Position: ${totalLinks}${this.getOrdinalSuffix(totalLinks)} link between these devices`);
                        }
                    }
                }
                
                // Update link details table if it's open for this link
                if (this.editingLink && this.editingLink.id === this.stretchingLink.id) {
                    this.showLinkDetails(this.stretchingLink);
                }
                
                this.draw();
                }
                } else {
                    // This is an MP (connection point) - don't attach to devices
                    if (this.debugger) {
                        this.debugger.logInfo(`🟣 MP is free-floating - does not attach to devices (routing only)`);
                    }
                }
            }
        }
        
        // Clear visual feedback state
        this._stretchingNearDevice = null;
        this._stretchingSnapAngle = null;
        
        // TRACKING: Generate final report for UL/BUL stretch operation
        if (this._bulTrackingData && this.debugger) {
            const duration = Date.now() - this._bulTrackingData.startTime;
            const chainSize = this._bulTrackingData.links.length;
            
            // Calculate total movement and detachments
            let totalMovement = 0;
            let maxJumpPerLink = 0;
            let linkWithMaxJump = null;
            let totalDetachments = 0;
            
            this._bulTrackingData.links.forEach(trackData => {
                const link = this.objects.find(l => l.id === trackData.id);
                if (link) {
                    const startMove = Math.sqrt(
                        Math.pow(link.start.x - trackData.startPos.x, 2) + 
                        Math.pow(link.start.y - trackData.startPos.y, 2)
                    );
                    const endMove = Math.sqrt(
                        Math.pow(link.end.x - trackData.endPos.x, 2) + 
                        Math.pow(link.end.y - trackData.endPos.y, 2)
                    );
                    
                    const maxMove = Math.max(startMove, endMove);
                    totalMovement += maxMove;
                    totalDetachments += (trackData.detachments || 0);
                    
                    if (maxMove > maxJumpPerLink) {
                        maxJumpPerLink = maxMove;
                        linkWithMaxJump = trackData.id;
                    }
                }
            });
            
            // Generate report ONLY if there were issues (jumps detected)
            if (this._bulTrackingData.totalJumps > 0) {
                this.debugger.logError(`⚠️ UL/BUL STRETCH - BUGS DETECTED`);
                this.debugger.logError(`   🚨 Total Jumps: ${this._bulTrackingData.totalJumps}`);
                
                this.debugger.logInfo(`📊 Debug Info:`);
                this.debugger.logInfo(`   Duration: ${duration}ms`);
                this.debugger.logInfo(`   Chain size: ${chainSize} link(s)`);
                this.debugger.logInfo(`   Max jump: ${maxJumpPerLink.toFixed(1)}px (${linkWithMaxJump})`);
                
                // Per-link breakdown
                this.debugger.logInfo(`🔍 Per-Link Movement:`);
                this._bulTrackingData.links.forEach(trackData => {
                    const link = this.objects.find(l => l.id === trackData.id);
                    if (link) {
                        const startMove = Math.sqrt(
                            Math.pow(link.start.x - trackData.startPos.x, 2) + 
                            Math.pow(link.start.y - trackData.startPos.y, 2)
                        );
                        const endMove = Math.sqrt(
                            Math.pow(link.end.x - trackData.endPos.x, 2) + 
                            Math.pow(link.end.y - trackData.endPos.y, 2)
                        );
                        
                        this.debugger.logInfo(`   ${trackData.id}: START ${startMove.toFixed(1)}px, END ${endMove.toFixed(1)}px`);
                    }
                });
            }
            // Reduced logging: Don't show success message every time (too verbose)
            
            // Clear tracking data
            this._bulTrackingData = null;
        }
        
        // CRITICAL: Always clear stretching flags to prevent "sticking"
        // This fixes the issue where MP continues to follow mouse after release
        const wasStretching = this.stretchingLink !== null;
        this.stretchingLink = null;
        this.stretchingEndpoint = null;
        this.stretchingConnectionPoint = false; // Clear connection point dragging flag
        
        // If we were stretching, update all connection points in the chain
        if (wasStretching) {
            this.updateAllConnectionPoints();
        }
        
        // Reset cursor
        this.updateCursor();
        if (this.moveLongPressTimer) {
            clearTimeout(this.moveLongPressTimer);
            this.moveLongPressTimer = null;
        }
        
        // CRITICAL: Update PLACEMENT TRACKING on drag release BEFORE clearing flags!
        if (this.dragging && this.selectedObject && this.debugger) {
            // Handle devices/text (have x,y) and unbound links (have start/end) differently
            let objPos, objGrid;
            
            if (this.selectedObject.x !== undefined && this.selectedObject.y !== undefined) {
                // Device or text object
                objPos = { x: this.selectedObject.x, y: this.selectedObject.y };
                objGrid = this.worldToGrid(objPos);
            } else if (this.selectedObject.type === 'unbound') {
                // Unbound link - use center point
                const centerX = (this.selectedObject.start.x + this.selectedObject.end.x) / 2;
                const centerY = (this.selectedObject.start.y + this.selectedObject.end.y) / 2;
                objPos = { x: centerX, y: centerY };
                objGrid = this.worldToGrid(objPos);
            }
            
            if (objPos) {
                const clickTrackDiv = document.getElementById('debug-click-track');
                if (clickTrackDiv) {
                    const mousePos = this.lastMousePos || pos;
                    const mouseGrid = this.worldToGrid(mousePos);
                    const relativePos = { x: mousePos.x - objPos.x, y: mousePos.y - objPos.y };
                    const relativeMag = Math.sqrt(relativePos.x * relativePos.x + relativePos.y * relativePos.y);
                    const inputSource = this._lastInputType || 'mouse';
                    const icon = inputSource === 'trackpad' ? '🖐️' : inputSource === 'mouse' ? '🖱️' : '👆';
                    
                    // Update placement data with release information
                    if (this.debugger.placementData && this.debugger.placementData.grabPosition) {
                        this.debugger.placementData.releasePosition = {
                            x: objPos.x,
                            y: objPos.y,
                            gridX: Math.round(objGrid.x),
                            gridY: Math.round(objGrid.y)
                        };
                        this.debugger.placementData.mouseRelease = { x: mousePos.x, y: mousePos.y };
                        
                        // Calculate distance moved
                        const dx = objPos.x - this.debugger.placementData.grabPosition.x;
                        const dy = objPos.y - this.debugger.placementData.grabPosition.y;
                        this.debugger.placementData.distance = Math.sqrt(dx * dx + dy * dy);
                    }
                
                    const objLabel = this.selectedObject.label || 
                                     (this.selectedObject.type === 'unbound' ? 'Unbound Link' : 'Device');
                    
                    clickTrackDiv.innerHTML = `
                        <span style="color: #27ae60; font-weight: bold; font-size: 11px;">${icon} DRAG RELEASED: ${objLabel}</span><br>
                        <span style="color: #0f0; font-size: 10px;">✓ Object still selected - ready for re-grab</span><br>
                        <br>
                        <span style="color: #0ff; font-weight: bold;">📍 FINAL POSITION:</span><br>
                        World: <span style="color: #0ff;">(${objPos.x.toFixed(1)}, ${objPos.y.toFixed(1)})</span><br>
                        Grid: <span style="color: #0ff;">(${Math.round(objGrid.x)}, ${Math.round(objGrid.y)})</span><br>
                        <br>
                        <span style="color: #fa0; font-weight: bold;">🖱️ RELEASE MOUSE POSITION:</span><br>
                        World: <span style="color: #fa0;">(${mousePos.x.toFixed(1)}, ${mousePos.y.toFixed(1)})</span><br>
                        Grid: <span style="color: #fa0;">(${Math.round(mouseGrid.x)}, ${Math.round(mouseGrid.y)})</span><br>
                        <br>
                        <span style="color: #667eea; font-weight: bold;">📏 RELATIVE AT RELEASE:</span><br>
                        Delta: <span style="color: #667eea;">(${relativePos.x.toFixed(1)}, ${relativePos.y.toFixed(1)})</span><br>
                        Distance: <span style="color: #667eea;">${relativeMag.toFixed(1)}px</span><br>
                        <br>
                        <div style="padding: 4px; background: rgba(155, 89, 182, 0.2); border-radius: 3px; border-left: 3px solid #9b59b6; margin-bottom: 6px;">
                            <span style="color: #9b59b6; font-weight: bold;">⏭️ NEXT: Re-Grab Test</span><br>
                            <span style="color: #fff; font-size: 9px;">
                                Click this object again to test re-grab!<br>
                                • Watch for offset changes<br>
                                • Monitor for position jumps<br>
                                • Compare relative position
                            </span>
                        </div>
                        <span style="color: #888; font-size: 9px;">
                            State: RELEASED - STILL SELECTED<br>
                            Type: ${this.selectedObject.type.toUpperCase()}<br>
                            Input: ${inputSource.toUpperCase()}<br>
                            Code: handleMouseUp()
                        </span>
                    `;
                }
            }
        }
        
        // CRITICAL: Set flag that mouse was released after selection
        // This enables handle operations (resize/rotate) on next click
        if (this.selectedObject && this.selectedObject.type === 'device' && !this.dragging) {
            // Mouse released without dragging - this completes the selection
            this.selectedObject._mouseReleasedAfterSelection = true;
            
            if (this.debugger) {
                this.debugger.logSuccess(`✓ Mouse released - handles now ENABLED for ${this.selectedObject.label || 'Device'}`);
                this.debugger.logInfo(`   Selection complete - resize/rotate available on next click`);
            }
        }
        
        // CRITICAL: Clear dragging flag and notify debugger
        const wasDragging = this.dragging;
        this.dragging = false;
        
        // CRITICAL: Update all connection points after dragging/moving merged links
        if (wasDragging) {
            this.updateAllConnectionPoints();
        }
        
        // CRITICAL: Clear tap tracking after drag ends to prevent drag-release from being mistaken for double-tap
        // This ensures that only intentional double-taps (not drag-release) can enter link mode
        if (wasDragging) {
            this.lastTapTime = 0;
            this._lastTapDevice = null;
            this._lastTapPos = null;
            this._lastTapStartTime = 0;
        }
        
        // Clear drag bug buffer on mouse up (prevents spam during drag)
        if (wasDragging && this.debugger) {
            if (this.debugger._dragBugBuffer && this.debugger._dragBugBuffer.length > 1) {
                const bufferedBugs = this.debugger._dragBugBuffer.length;
                console.log(`✓ Drag complete - suppressed ${bufferedBugs - 1} duplicate bugs during drag`);
                this.debugger.log(`🔄 Drag ended - ${bufferedBugs - 1} duplicate bugs suppressed`, 'info');
            }
            // Clear buffer
            if (this.debugger._dragBugBuffer) {
                this.debugger._dragBugBuffer = [];
            }
        }
        
        this.multiSelectInitialPositions = null;
        this.unboundLinkInitialPos = null; // Clear UL body drag position
        this.textDragInitialPos = null; // Clear text drag position
        this.dragStartPos = null; // Clear starting position for tap vs drag detection
        this.lastMousePos = null; // Clear last mouse position
        this._unboundLinkMoveLogged = false; // Reset UL move log flag
        this._unboundBodyDragLogged = false; // Reset UL body drag log flag
        this.lastDragPos = null; // Clear drag position tracking
        this._jumpDetectedThisDrag = false; // Reset jump detection flag for next drag
        this.lastDragTime = null;
        if (this.currentTool !== 'link') {
            this.linking = false;
            this.linkStart = null;
        }

        // If we temporarily exited placement to drag the newly placed device,
        // restore device placement mode after releasing the mouse
        if (this.tempPlacementResumeType) {
            this.setDevicePlacementMode(this.tempPlacementResumeType);
            this.tempPlacementResumeType = null;
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
        e.preventDefault();
        
        // If in device placement mode, right-click exits to base mode
        if (this.placingDevice) {
            this.placingDevice = null;
            this.setMode('base');
            return;
        }
        
        // If in link mode, right-click exits to base mode
        if (this.currentTool === 'link') {
            this.linking = false;
            this.linkStart = null;
            this.setMode('base');
            return;
        }
        
        const pos = this.getMousePos(e);
        const clickedObject = this.findObjectAt(pos.x, pos.y);
        
        // ✨ Right-click on device → Show context menu
        if (clickedObject && clickedObject.type === 'device') {
            // Cancel any device placement
            if (this.placingDevice) {
                this.placingDevice = null;
            }
            
            // Select the device if not already selected
            if (!this.selectedObjects.includes(clickedObject)) {
                this.selectedObject = clickedObject;
                this.selectedObjects = [clickedObject];
                
                // ENHANCED: If selecting a merged UL, also add the partner to selection
                if (clickedObject.type === 'unbound' && clickedObject.mergedWith) {
                    const childLink = this.objects.find(o => o.id === clickedObject.mergedWith.linkId);
                    if (childLink && !this.selectedObjects.includes(childLink)) {
                        this.selectedObjects.push(childLink);
                    }
                } else if (clickedObject.type === 'unbound' && clickedObject.mergedInto) {
                    const parentLink = this.objects.find(o => o.id === clickedObject.mergedInto.parentId);
                    if (parentLink && !this.selectedObjects.includes(parentLink)) {
                        this.selectedObjects.push(parentLink);
                    }
                }
            }
            
            // Show context menu for this device
            this.showContextMenu(e.clientX, e.clientY, clickedObject);
            
            if (this.debugger) {
                const gridPos = this.worldToGrid({ x: clickedObject.x, y: clickedObject.y });
                this.debugger.logSuccess(`🖱️ Right-click on device: Context menu for ${clickedObject.label || 'Device'}`);
                this.debugger.logInfo(`Device: ${clickedObject.label} at Grid(${Math.round(gridPos.x)}, ${Math.round(gridPos.y)})`);
            }
            
            this.draw();
            return;
        }
        
        // For other objects (links, unbound), show context menu as before
        if (clickedObject && (clickedObject.type === 'link' || clickedObject.type === 'unbound')) {
            // If clicking on an already-selected object in multi-select, keep the selection
            if (this.selectedObjects.length > 1 && this.selectedObjects.includes(clickedObject)) {
                // Keep current multi-selection, show bulk operations menu
                this.showBulkContextMenu(e.clientX, e.clientY);
            } else {
                // Single selection - replace selection with clicked object
                this.selectedObject = clickedObject;
                this.selectedObjects = [clickedObject];
                
                // ENHANCED: If selecting a merged UL, also add the partner to selection
                if (clickedObject.type === 'unbound' && clickedObject.mergedWith) {
                    const childLink = this.objects.find(o => o.id === clickedObject.mergedWith.linkId);
                    if (childLink && !this.selectedObjects.includes(childLink)) {
                        this.selectedObjects.push(childLink);
                    }
                } else if (clickedObject.type === 'unbound' && clickedObject.mergedInto) {
                    const parentLink = this.objects.find(o => o.id === clickedObject.mergedInto.parentId);
                    if (parentLink && !this.selectedObjects.includes(parentLink)) {
                        this.selectedObjects.push(parentLink);
                    }
                }
                
                this.showContextMenu(e.clientX, e.clientY, clickedObject);
            }
        } else {
            // Right-clicked on empty space
            if (this.currentMode === 'select' && (this.selectedObjects.length > 0 || this.selectedObject)) {
                // Silently transition to base mode without showing menu
                this.setMode('base');
            }
        }
    }
    
    showBackgroundContextMenu(x, y) {
        const menu = document.getElementById('context-menu');
        menu.style.display = 'block';
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
        this.contextMenuVisible = true;
        
        // Hide all standard menu items
        document.getElementById('ctx-duplicate').style.display = 'none';
        document.getElementById('ctx-add-text').style.display = 'none';
        document.getElementById('ctx-toggle-curve').style.display = 'none';
        document.getElementById('ctx-change-color').style.display = 'none';
        document.getElementById('ctx-change-size').style.display = 'none';
        document.getElementById('ctx-change-label').style.display = 'none';
        document.getElementById('ctx-lock').style.display = 'none';
        document.getElementById('ctx-unlock').style.display = 'none';
        document.getElementById('ctx-delete').style.display = 'none';
        
        // Create temporary menu item for base mode
        const existingBaseModeItem = document.getElementById('ctx-base-mode');
        if (existingBaseModeItem) {
            existingBaseModeItem.style.display = 'block';
        } else {
            const baseModeItem = document.createElement('div');
            baseModeItem.id = 'ctx-base-mode';
            baseModeItem.className = 'context-menu-item';
            baseModeItem.textContent = '← Return to Base Mode';
            baseModeItem.addEventListener('click', () => {
                this.setMode('base');
                this.hideContextMenu();
            });
            menu.insertBefore(baseModeItem, menu.firstChild);
        }
    }
    
    showBulkContextMenu(x, y) {
        // Show context menu for multiple selected objects
        const menu = document.getElementById('context-menu');
        menu.style.display = 'block';
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
        this.contextMenuVisible = true;
        
        // Hide background-specific items
        const baseModeItem = document.getElementById('ctx-base-mode');
        if (baseModeItem) baseModeItem.style.display = 'none';
        
        // Check what types of objects are selected
        const hasDevices = this.selectedObjects.some(obj => obj.type === 'device');
        const hasLinks = this.selectedObjects.some(obj => obj.type === 'link' || obj.type === 'unbound');
        const hasText = this.selectedObjects.some(obj => obj.type === 'text');
        const hasLockable = this.selectedObjects.some(obj => obj.type === 'device' || obj.type === 'text');
        
        // Show appropriate bulk operations
        document.getElementById('ctx-duplicate').style.display = 'none';
        document.getElementById('ctx-add-text').style.display = 'none';
        document.getElementById('ctx-change-color').style.display = (hasDevices || hasText) ? 'block' : 'none';
        document.getElementById('ctx-change-size').style.display = 'none';
        document.getElementById('ctx-change-label').style.display = 'none';
        
        // Show curve toggle for bulk link operations
        const toggleCurveItem = document.getElementById('ctx-toggle-curve');
        if (hasLinks) {
            toggleCurveItem.style.display = 'block';
            const firstLink = this.selectedObjects.find(obj => obj.type === 'link' || obj.type === 'unbound');
            const curveEnabled = firstLink && (firstLink.curveOverride !== undefined ? firstLink.curveOverride : this.linkCurveMode) && this.magneticFieldStrength > 0;
            const linkCount = this.selectedObjects.filter(obj => obj.type === 'link' || obj.type === 'unbound').length;
            const status = this.magneticFieldStrength === 0 ? 'DISABLED (Magnetic Field = 0)' :
                          curveEnabled ? `ON (${linkCount} Link${linkCount > 1 ? 's' : ''})` :
                          `OFF (${linkCount} Link${linkCount > 1 ? 's' : ''})`;
            toggleCurveItem.textContent = `Curve: ${status}`;
        } else {
            toggleCurveItem.style.display = 'none';
        }
        
        // Show lock/unlock based on current state
        const lockItem = document.getElementById('ctx-lock');
        const unlockItem = document.getElementById('ctx-unlock');
        
        if (hasLockable) {
            const lockableObjects = this.selectedObjects.filter(obj => obj.type === 'device' || obj.type === 'text');
            const anyLocked = lockableObjects.some(obj => obj.locked);
            const anyUnlocked = lockableObjects.some(obj => !obj.locked);
            const lockCount = lockableObjects.length;
            const unlockedCount = lockableObjects.filter(obj => !obj.locked).length;
            const lockedCount = lockableObjects.filter(obj => obj.locked).length;
            
            // Show both options if mixed state, otherwise show relevant one
            if (anyUnlocked) {
                lockItem.style.display = 'block';
                lockItem.textContent = unlockedCount === lockCount ? 
                    `🔒 Lock ${lockCount} Object(s)` : 
                    `🔒 Lock ${unlockedCount} Object(s)`;
            } else {
                lockItem.style.display = 'none';
            }
            
            if (anyLocked) {
                unlockItem.style.display = 'block';
                unlockItem.textContent = lockedCount === lockCount ? 
                    `🔓 Unlock ${lockCount} Object(s)` : 
                    `🔓 Unlock ${lockedCount} Object(s)`;
            } else {
                unlockItem.style.display = 'none';
            }
        } else {
            lockItem.style.display = 'none';
            unlockItem.style.display = 'none';
        }
        
        document.getElementById('ctx-delete').style.display = 'block';
    }
    
    handleDoubleClick(e) {
        // Cancel long press
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
        
        // CRITICAL FIX: Cancel marquee timer to prevent MS from starting after UL placement
        if (this.marqueeTimer) {
            clearTimeout(this.marqueeTimer);
            this.marqueeTimer = null;
        }
        
        // Also clear marquee selection state
        this.selectionRectStart = null;
        this.marqueeActive = false;
        
        // Track double-click time to prevent accidental MS mode after UL placement
        this.lastDoubleClickTime = Date.now();
        
        const pos = this.getMousePos(e);
        let clickedObject = this.findObjectAt(pos.x, pos.y);
        
        // ENHANCED: Check if clicking inside rotated bounding box of ANY text object
        if (!clickedObject || clickedObject.type !== 'text') {
            // Check all text objects for hitbox
            const textInHitbox = this.objects.find(obj => {
                if (obj.type !== 'text') return false;
                
                // Calculate rotated rectangle hitbox
                this.ctx.save();
                this.ctx.font = `${obj.fontSize}px Arial`;
                const metrics = this.ctx.measureText(obj.text || 'Text');
                const w = metrics.width;
                const h = parseInt(obj.fontSize);
                this.ctx.restore();
                
                // Rectangle bounds (with padding for handles)
                const rectW = w + 10;
                const rectH = h + 10;
                
                // Transform click point to text's local space (unrotate)
                const angle = obj.rotation * Math.PI / 180;
                const dx = pos.x - obj.x;
                const dy = pos.y - obj.y;
                
                // Rotate point back to unrotated space
                const localX = dx * Math.cos(-angle) - dy * Math.sin(-angle);
                const localY = dx * Math.sin(-angle) + dy * Math.cos(-angle);
                
                // Check if inside rectangle
                return Math.abs(localX) <= rectW/2 && Math.abs(localY) <= rectH/2;
            });
            
            if (textInHitbox) clickedObject = textInHitbox;
        }
        
        // ✨ FAST Double-click on background → Create unbound link OR exit text mode
        if (!clickedObject) {
            const now = Date.now();
            const timeSinceLastClick = now - this.lastBackgroundClickTime;
            
            // ENHANCED: If in text mode, double-click exits to base mode
            if (this.currentTool === 'text') {
                this.setMode('base');
                if (this.debugger) {
                    this.debugger.logSuccess(`🖱️🖱️ Double-click on background: Exiting TEXT mode → BASE mode`);
                }
                return;
            }
            
            // Check if this is a FAST double-click (< 250ms) AND UL is enabled
            // Note: lastBackgroundClickTime is updated in handleMouseDown
            if (this.linkULEnabled && timeSinceLastClick > 0 && timeSinceLastClick < this.fastDoubleClickDelay) {
                const gridPos = this.worldToGrid(pos);
                
                // Cancel any device placement
                if (this.placingDevice) {
                    this.placingDevice = null;
                }
                
                this.saveState();
                
                // Create horizontal unbound link centered at double-click position
                const linkLength = 100; // Default length
                const link = {
                    id: `unbound_${this.linkIdCounter++}`,
                    type: 'unbound',
                    originType: 'UL', // PRESERVE: Original link type
                    createdAt: Date.now(), // Creation timestamp for BUL order tracking
                    device1: null,
                    device2: null,
                    color: '#666',
                    start: { x: pos.x - linkLength/2, y: pos.y },
                    end: { x: pos.x + linkLength/2, y: pos.y },
                    connectedStart: null,  // UL ID connected to start endpoint
                    connectedEnd: null,     // UL ID connected to end endpoint
                    style: this.linkStyle || 'solid'  // CRITICAL: Store the style when link is created
                };
                
                this.objects.push(link);
                this.selectedObject = link;
                this.selectedObjects = [link];
                this.unboundLink = link;
                
                if (this.debugger) {
                    this.debugger.logSuccess(`🖱️🖱️ FAST Double-click on screen (${timeSinceLastClick}ms): Unbound link created`);
                    this.debugger.logInfo(`Position: Grid(${Math.round(gridPos.x)}, ${Math.round(gridPos.y)}), World(${Math.round(pos.x)}, ${Math.round(pos.y)})`);
                    this.debugger.logInfo(`Length: ${linkLength}px | Color: ${link.color}`);
                }
                
                // PLACEMENT TRACKING: Initialize placement data for UL
                if (this.debugger) {
                    this.debugger.placementData = {
                        deviceLabel: 'Unbound Link',
                        deviceType: 'unbound',
                        grabPosition: {
                            x: pos.x,
                            y: pos.y,
                            gridX: Math.round(gridPos.x),
                            gridY: Math.round(gridPos.y)
                        },
                        releasePosition: {
                            x: pos.x,
                            y: pos.y,
                            gridX: Math.round(gridPos.x),
                            gridY: Math.round(gridPos.y)
                        },
                        mouseGrab: { x: pos.x, y: pos.y },
                        mouseRelease: { x: pos.x, y: pos.y },
                        offset: { x: 0, y: 0 },
                        distance: 0,
                        timestamp: new Date().toLocaleTimeString(),
                        inputType: this._lastInputType || 'mouse'
                    };
                }
                
                this.draw();
                this.lastBackgroundClickTime = 0; // Reset after successful UL creation
                
                // CRITICAL FIX: Clear long press timer after UL placement to prevent accidental MS mode
                if (this.longPressTimer) {
                    clearTimeout(this.longPressTimer);
                    this.longPressTimer = null;
                }
                
                // CRITICAL FIX: Clear tap tracking to prevent light double-tap after UL from entering MS
                this.lastTapTime = 0;
                this._lastTapDevice = null;
                this._lastTapPos = null;
                this._lastTapStartTime = 0;
            } else {
                // Too slow for UL placement - double-click event fired but timing was off
                if (this.debugger && timeSinceLastClick > this.fastDoubleClickDelay && timeSinceLastClick < 1000) {
                    this.debugger.logInfo(`⏱️ Double-click too slow (${timeSinceLastClick}ms) - needs < ${this.fastDoubleClickDelay}ms for UL`);
                }
            }
            return;
        }
        
        // Double-click on object behavior
        if (clickedObject) {
            // ✨ Double-click device → Always enter link mode (regardless of whether it has links)
            if (clickedObject.type === 'device') {
                // Cancel any device placement
                if (this.placingDevice) {
                    this.placingDevice = null;
                }
                
                // Always enter link mode with this device
                this.setMode('link');
                this.linking = true;
                this.linkStart = clickedObject;
                
                // Check if device has any links (for logging)
                const deviceLinks = this.objects.filter(obj => 
                    obj.type === 'unbound' && (obj.device1 === clickedObject.id || obj.device2 === clickedObject.id)
                );
                
                if (this.debugger) {
                    const gridPos = this.worldToGrid({ x: clickedObject.x, y: clickedObject.y });
                    this.debugger.logSuccess(`🖱️🖱️ Double-click on device: LINK mode from ${clickedObject.label || 'Device'}${deviceLinks.length > 0 ? ` (${deviceLinks.length} links)` : ' (no links yet)'}`);
                    this.debugger.logInfo(`Device: ${clickedObject.label} at Grid(${Math.round(gridPos.x)}, ${Math.round(gridPos.y)})`);
                }
                
                this.draw();
            } else if (clickedObject.type === 'link' || clickedObject.type === 'unbound') {
                // Double-click link to show connection details table
                this.showLinkDetails(clickedObject);
            } else if (clickedObject.type === 'text') {
                // ENHANCED: Select text first, THEN open editor
                this.selectedObject = clickedObject;
                this.selectedObjects = [clickedObject];
                this.draw(); // Show selection
                
                // Short delay to show selection before opening editor
                setTimeout(() => {
                this.showTextEditor(clickedObject);
                }, 50);
                
                if (this.debugger) {
                    this.debugger.logSuccess(`🖱️🖱️ Double-click on text: Selected and opening editor for "${clickedObject.text}"`);
                }
            }
        }
    }
    
    handleWheel(e) {
        e.preventDefault();
        
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        
        // Convert CSS pixels to canvas backing store pixels
        const mouseX = (e.clientX - rect.left) * scaleX;
        const mouseY = (e.clientY - rect.top) * scaleY;
        this.lastMousePos = this.getMousePos(e); // keep world pos fresh for HUD
        
        // FIXED: Strict detection - ONLY Ctrl/Cmd key triggers zoom
        // This prevents scroll/pan from accidentally triggering zoom
        const isPinchZoom = e.ctrlKey || e.metaKey;
        
        if (isPinchZoom) {
            // PINCH-TO-ZOOM with Ctrl/Cmd key - zooms at cursor position
            const oldZoom = this.zoom;
            const zoomSensitivity = 0.01; // Smooth zoom sensitivity
            const zoomDelta = -e.deltaY * zoomSensitivity;

            // Get world position at cursor BEFORE zoom
            const worldX = (mouseX - this.panOffset.x) / this.zoom;
            const worldY = (mouseY - this.panOffset.y) / this.zoom;
            
            // Calculate new zoom
            const scaleFactor = 1 + zoomDelta;
            const newZoom = Math.max(0.25, Math.min(3, this.zoom * scaleFactor));
            
            // Update zoom
            this.zoom = newZoom;
            
            // Adjust pan so world position stays at cursor (zoom at cursor)
            this.panOffset.x = mouseX - worldX * this.zoom;
            this.panOffset.y = mouseY - worldY * this.zoom;
            this.savePanOffset();
        
            // Log zoom change (only if significant change)
            if (this.debugger && Math.abs(this.zoom - oldZoom) > 0.01) {
                const zoomPercent = Math.round(this.zoom * 100);
                const direction = this.zoom > oldZoom ? '🔍+' : '🔍-';
                this.debugger.logInfo(`${direction} Ctrl+Wheel: ${zoomPercent}% at cursor position`);
            }
        
            this.updateZoomIndicator();
            this.updateScrollbars();
            this.draw();
            this.updateHud();
        } else {
            // TWO-FINGER SCROLL/PAN on trackpad - INDEPENDENT of zoom
            const oldPanX = this.panOffset.x;
            const oldPanY = this.panOffset.y;
            
            // Direct 1:1 panning for natural trackpad feel
            const panSensitivity = 1.0;
            
            // Pan in both directions - zoom stays UNCHANGED
            this.panOffset.x -= e.deltaX * panSensitivity;
            this.panOffset.y -= e.deltaY * panSensitivity;
            this.savePanOffset();
            
            // Log pan (throttled - only log significant movements)
            if (this.debugger && (Math.abs(e.deltaX) > 20 || Math.abs(e.deltaY) > 20)) {
                const panDx = Math.round(this.panOffset.x - oldPanX);
                const panDy = Math.round(this.panOffset.y - oldPanY);
                this.debugger.logInfo(`↔️ Scroll/Pan: Δx=${panDx}, Δy=${panDy}`);
            }
            
            this.updateScrollbars();
            this.draw();
            this.updateHud();
        }
    }
    
    updateZoomIndicator() {
        const zoomPercent = Math.round(this.zoom * 100);
        const indicator = document.getElementById('zoom-indicator');
        if (indicator) {
            indicator.textContent = `${zoomPercent}%`;
        }
        
        // Save zoom to localStorage for persistence across page refreshes
        localStorage.setItem('topology_zoom', this.zoom.toString());
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
            const dx = gx; // since origin is 0,0 in grid units
            const dy = gy;
            const r = Math.round(Math.sqrt(dx*dx + dy*dy));
            text = `Grid: (${gx}, ${gy}) | Δ: ${dx}, ${dy} | r: ${r}`;
        } else {
            text = 'Grid: (–, –)';
        }
        const modeText = (this.currentMode || 'base').toUpperCase();
        hud.textContent = `${text} | Mode: ${modeText}`;
    }
    
    getDistance(touch1, touch2) {
        const dx = touch2.clientX - touch1.clientX;
        const dy = touch2.clientY - touch1.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    handleTouchStart(e) {
        e.preventDefault();
        
        // ENHANCED: Track gesture state
        this.gestureState.fingerCount = e.touches.length;
        this.gestureState.gestureStartTime = Date.now();
        this.gestureState.gestureMoved = false;
        
        if (e.touches.length > 0) {
            const pos = this.getTouchPos(e.touches[0]);
            this.gestureState.gestureStartPos = { x: pos.x, y: pos.y };
        }
        
        // Log gesture start to debugger
        if (this.debugger && e.touches.length > 1) {
            this.debugger.logInfo(`👆 ${e.touches.length}-finger gesture started`);
        }
        
        if (e.touches.length === 1) {
            // Single finger - normal touch/tap/drag
            const pos = this.getTouchPos(e);
            this.handleMouseDown({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
        } else if (e.touches.length === 2) {
            // Two-finger gesture - prepare for pinch or pan
            this.pinching = true;
            this.lastPinchDistance = this.getDistance(e.touches[0], e.touches[1]);
            this.lastTwoFingerCenter = this.getTwoFingerCenter(e.touches[0], e.touches[1]);
            this.gestureState.lastGestureType = '2-finger-pinch';
        } else if (e.touches.length === 3) {
            // ENHANCED: Three-finger gesture - store position and process on release
            const pos = this.getTouchPos(e.touches[0]);
            this.gestureState.lastGestureType = '3-finger-tap';
            this.gestureState.stored3FingerPos = pos; // Store for processing on release
            // Wait for touchEnd to distinguish tap vs swipe
            return;
        } else if (e.touches.length === 4) {
            // ✨ NEW: Four-finger gesture - toggle fullscreen/presentation mode
            this.gestureState.lastGestureType = '4-finger-swipe';
            
            if (this.debugger) {
                this.debugger.logInfo(`👆👆👆👆 4-finger gesture: detected`);
            }
            return;
        }
    }
    
    process3FingerTap() {
        // DISABLED: 3-finger tap functionality - replaced with right-click on device and double-click on screen
        // Right-click on device → Enter link mode
        // Double-click on screen → Create unbound link
        // This function is kept for backward compatibility but does nothing
        if (this.debugger) {
            this.debugger.logInfo(`👆 3-finger tap detected but disabled (use right-click on device or double-click on screen instead)`);
        }
        
        // Clear stored position
        this.gestureState.stored3FingerPos = null;
    }
    
    handleTouchMove(e) {
        e.preventDefault();
        
        // ENHANCED: Track if gesture has moved (for tap vs swipe detection)
        if (!this.gestureState.gestureMoved && this.gestureState.gestureStartPos && e.touches.length > 0) {
            const currentPos = this.getTouchPos(e.touches[0]);
            const dx = Math.abs(currentPos.x - this.gestureState.gestureStartPos.x);
            const dy = Math.abs(currentPos.y - this.gestureState.gestureStartPos.y);
            
            if (dx > this.gestureState.moveThreshold || dy > this.gestureState.moveThreshold) {
                this.gestureState.gestureMoved = true;
                
                // Log swipe detection
                if (this.debugger && e.touches.length >= 3) {
                    this.debugger.logInfo(`👆 ${e.touches.length}-finger SWIPE detected (moved ${Math.round(Math.max(dx, dy))}px)`);
                }
            }
        }
        
        if (e.touches.length === 1) {
            // Single finger - normal touch/drag
            this.handleMouseMove({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
        } else if (e.touches.length === 2 && this.pinching) {
            // Two fingers - handle both pinch zoom and panning
            const currentDistance = this.getDistance(e.touches[0], e.touches[1]);
            const currentCenter = this.getTwoFingerCenter(e.touches[0], e.touches[1]);
            
            // ENHANCED: Pinch zoom with improved sensitivity
            if (this.lastPinchDistance) {
                const delta = currentDistance - this.lastPinchDistance;
                // ENHANCED: Lower threshold (2px instead of 5px) for better sensitivity
                if (Math.abs(delta) > 2) {
                    const zoomFactor = currentDistance / this.lastPinchDistance;
                    const oldZoom = this.zoom;
                    const newZoom = Math.max(0.25, Math.min(3, this.zoom * zoomFactor));
                    
                    // Get pinch center in screen coordinates
                    const rect = this.canvas.getBoundingClientRect();
                    const scaleX = this.canvas.width / rect.width;
                    const scaleY = this.canvas.height / rect.height;
                    const centerX = (currentCenter.x - rect.left) * scaleX;
                    const centerY = (currentCenter.y - rect.top) * scaleY;
                    
                    // Get world position at pinch center BEFORE zoom
                    const worldX = (centerX - this.panOffset.x) / oldZoom;
                    const worldY = (centerY - this.panOffset.y) / oldZoom;
                    
                    // Update zoom
                    this.zoom = newZoom;
                    
                    // Adjust pan so world position stays at pinch center (zoom at fingers)
                    this.panOffset.x = centerX - worldX * newZoom;
                    this.panOffset.y = centerY - worldY * newZoom;
                    this.savePanOffset();
                    
                    this.lastPinchDistance = currentDistance;
                    this.updateZoomIndicator();
                    this.draw();
                }
            }
            
            // ENHANCED: Two-finger panning with improved sensitivity
            if (this.lastTwoFingerCenter) {
                const deltaX = currentCenter.x - this.lastTwoFingerCenter.x;
                const deltaY = currentCenter.y - this.lastTwoFingerCenter.y;
                
                // ENHANCED: Lower threshold (1px instead of 2px) for smoother panning
                if (Math.abs(deltaX) > 1 || Math.abs(deltaY) > 1) {
                    // Apply pan directly (1:1 sensitivity for natural feel)
                    this.panOffset.x += deltaX;
                    this.panOffset.y += deltaY;
                    this.savePanOffset();
                    this.updateScrollbars();
                    this.draw();
                }
            }
            
            this.lastTwoFingerCenter = currentCenter;
        }
    }
    
    handleTouchEnd(e) {
        e.preventDefault();
        
        // ENHANCED: Detect tap vs swipe gestures
        const gestureDuration = Date.now() - this.gestureState.gestureStartTime;
        const wasTap = !this.gestureState.gestureMoved && gestureDuration < this.gestureState.tapThreshold;
        const lastFingerCount = this.gestureState.fingerCount;
        
        // ENHANCED: Double-tap detection for single-finger taps
        if (wasTap && lastFingerCount === 1 && e.changedTouches.length > 0) {
            const now = Date.now();
            const pos = this.getTouchPos(e.changedTouches[0]);
            
            // Check if this is a double-tap
            if (this.lastTouchTapTime && this.lastTouchTapPos) {
                const timeDiff = now - this.lastTouchTapTime;
                const dx = pos.x - this.lastTouchTapPos.x;
                const dy = pos.y - this.lastTouchTapPos.y;
                const dist = Math.sqrt(dx*dx + dy*dy);
                
                if (timeDiff < this.doubleTapThreshold && dist < this.doubleTapDistanceThreshold) {
                    // Double-tap detected!
                    let clickedObject = this.findObjectAt(pos.x, pos.y);
                    
                    // ENHANCED: Check if inside rotated bounding box of ANY text object
                    if (!clickedObject || clickedObject.type !== 'text') {
                        const textInHitbox = this.objects.find(obj => {
                            if (obj.type !== 'text') return false;
                            
                            // Calculate rotated rectangle hitbox
                            this.ctx.save();
                            this.ctx.font = `${obj.fontSize}px Arial`;
                            const metrics = this.ctx.measureText(obj.text || 'Text');
                            const w = metrics.width;
                            const h = parseInt(obj.fontSize);
                            this.ctx.restore();
                            
                            // Rectangle bounds (with padding for handles)
                            const rectW = w + 10;
                            const rectH = h + 10;
                            
                            // Transform click point to text's local space (unrotate)
                            const angle = obj.rotation * Math.PI / 180;
                            const tdx = pos.x - obj.x;
                            const tdy = pos.y - obj.y;
                            
                            // Rotate point back to unrotated space
                            const localX = tdx * Math.cos(-angle) - tdy * Math.sin(-angle);
                            const localY = tdx * Math.sin(-angle) + tdy * Math.cos(-angle);
                            
                            // Check if inside rectangle
                            return Math.abs(localX) <= rectW/2 && Math.abs(localY) <= rectH/2;
                        });
                        
                        if (textInHitbox) clickedObject = textInHitbox;
                    }
                    
                    if (clickedObject && clickedObject.type === 'text') {
                        // ENHANCED: Select text first, THEN open editor
                        this.selectedObject = clickedObject;
                        this.selectedObjects = [clickedObject];
                        this.draw(); // Show selection
                        
                        // Short delay to show selection before opening editor
                        setTimeout(() => {
                            this.showTextEditor(clickedObject);
                        }, 50);
                        
                        if (this.debugger) {
                            this.debugger.logSuccess(`👆👆 Double-tap on text: Selected and opening editor for "${clickedObject.text}"`);
                        }
                        // Reset tap tracking
                        this.lastTouchTapTime = 0;
                        this.lastTouchTapPos = null;
                        return;
                    } else if (clickedObject && clickedObject.type === 'device') {
                        // Double-tap on device -> Enter link mode
                        this.setMode('link');
                        this.linking = true;
                        this.linkStart = clickedObject;
                        if (this.debugger) {
                            this.debugger.logSuccess(`👆👆 Double-tap on device: LINK mode from ${clickedObject.label}`);
                        }
                        this.lastTouchTapTime = 0;
                        this.lastTouchTapPos = null;
                        this.draw();
                        return;
                    } else if (!clickedObject) {
                        // Double-tap on background
                        // If in text mode, exit to base mode
                        if (this.currentTool === 'text') {
                            this.setMode('base');
                            if (this.debugger) {
                                this.debugger.logSuccess(`👆👆 Double-tap on background: Exiting TEXT mode → BASE mode`);
                            }
                            this.lastTouchTapTime = 0;
                            this.lastTouchTapPos = null;
                            return;
                        }
                        // Otherwise, if UL is enabled, create UL (handled by handleDoubleClick)
                        // Reset for potential triple-tap
                        this.lastTouchTapTime = now;
                        this.lastTouchTapPos = pos;
                    } else {
                        // Reset tap tracking
                        this.lastTouchTapTime = 0;
                        this.lastTouchTapPos = null;
                    }
                } else {
                    // Too far apart or too slow - this is a new first tap
                    this.lastTouchTapTime = now;
                    this.lastTouchTapPos = pos;
                }
            } else {
                // First tap - record it
                this.lastTouchTapTime = now;
                this.lastTouchTapPos = pos;
            }
        }
        
        // DISABLED: 3-finger tap - replaced with right-click on device and double-click on screen
        // Right-click on device → Enter link mode
        // Double-click on screen → Create unbound link
        if (wasTap && lastFingerCount === 3 && this.gestureState.lastGestureType === '3-finger-tap') {
            // 3-finger tap detected but disabled
            if (this.debugger) {
                this.debugger.logInfo(`👆 3-finger tap detected but disabled (use right-click on device or double-click on screen instead)`);
            }
            // Don't process - functionality replaced with mouse gestures
        } else if (wasTap && lastFingerCount === 4 && this.gestureState.lastGestureType === '4-finger-swipe') {
            // ✨ NEW: 4-FINGER TAP → Toggle all UI (presentation mode)
            this.toggle4FingerMode();
            
            if (this.debugger) {
                this.debugger.logSuccess(`✓ 4-finger TAP confirmed: UI toggle`);
            }
        } else if (this.gestureState.gestureMoved && lastFingerCount >= 3) {
            // Multi-finger SWIPE (not tap)
            if (this.debugger) {
                this.debugger.logInfo(`👆 ${lastFingerCount}-finger SWIPE completed`);
            }
        }
        
        // Standard touch cleanup
        if (e.touches.length === 0) {
            // All touches ended
            this.pinching = false;
            this.lastPinchDistance = null;
            this.lastTwoFingerCenter = null;
            this.gestureState.fingerCount = 0;
            this.handleMouseUp(e);
        } else if (e.touches.length === 1) {
            // One finger remaining
            this.pinching = false;
            this.lastPinchDistance = null;
            this.lastTwoFingerCenter = null;
            this.gestureState.fingerCount = e.touches.length;
        } else {
            // Multiple fingers remaining
            this.gestureState.fingerCount = e.touches.length;
        }
    }
    
    toggle4FingerMode() {
        // 4-finger tap toggles BOTH top bar and left toolbar for presentation mode
        const topBar = document.querySelector('.top-bar');
        const leftToolbar = document.getElementById('left-toolbar');
        
        // Check current state
        const topBarHidden = topBar && topBar.classList.contains('collapsed');
        const leftToolbarHidden = leftToolbar && leftToolbar.classList.contains('collapsed');
        
        // Toggle both
        if (topBarHidden || leftToolbarHidden) {
            // Show all UI
            if (topBar) topBar.classList.remove('collapsed');
            if (leftToolbar) leftToolbar.classList.remove('collapsed');
            
            if (this.debugger) {
                this.debugger.logSuccess(`👆👆👆👆 4-finger tap: SHOW all UI (exit presentation mode)`);
            }
        } else {
            // Hide all UI (presentation mode)
            if (topBar) topBar.classList.add('collapsed');
            if (leftToolbar) leftToolbar.classList.add('collapsed');
            
            if (this.debugger) {
                this.debugger.logSuccess(`👆👆👆👆 4-finger tap: HIDE all UI (presentation mode)`);
            }
        }
        
        // Resize canvas after animation
        setTimeout(() => {
            this.resizeCanvas();
            this.draw();
        }, 300);
    }
    
    getTwoFingerCenter(touch1, touch2) {
        return {
            x: (touch1.clientX + touch2.clientX) / 2,
            y: (touch1.clientY + touch2.clientY) / 2
        };
    }
    
    zoomIn() {
        console.log('zoomIn called');
        
        // FIXED: Zoom at cursor position - keeps point under cursor fixed
        const cursorX = this.lastMouseScreen?.x || (this.canvas.width / 2);
        const cursorY = this.lastMouseScreen?.y || (this.canvas.height / 2);
        
        const S_old = this.zoom;
        const S_new = Math.max(0.25, Math.min(3, S_old + 0.05)); // Clamp to 25%-300%
        
        // Get world position at cursor BEFORE zoom
        const worldX = (cursorX - this.panOffset.x) / S_old;
        const worldY = (cursorY - this.panOffset.y) / S_old;
        
        // Update zoom
        this.zoom = S_new;
        
        // Adjust pan so world position stays at cursor (zoom at cursor)
        this.panOffset.x = cursorX - worldX * S_new;
        this.panOffset.y = cursorY - worldY * S_new;
        this.savePanOffset();
        
        if (this.debugger) {
            const newZoomPercent = Math.round(this.zoom * 100);
            this.debugger.logAction(`🔍+ Zoom In: ${newZoomPercent}% (+5%) at cursor`);
        }
        
        this.updateZoomIndicator();
        this.updateScrollbars();
        this.draw();
        this.updateHud();
    }
    
    zoomAtCursor(cursorScreen, zoomDelta) {
        // FIXED: Zoom at cursor position - keeps point under cursor fixed
        const k = 0.0015;                      // sensitivity
        const scaleFactor = Math.exp(zoomDelta * k);

        const S_old = this.zoom;
        const S_new = Math.max(0.25, Math.min(3, S_old * scaleFactor)); // Clamp zoom

        // Check if zoom was clamped
        const wasClamped = (S_old * scaleFactor < 0.25 || S_old * scaleFactor > 3);
        
        if (this.debugger && wasClamped) {
            if (S_new === 0.25) {
                this.debugger.logWarning('Zoom limit reached: 25% (min)');
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
        console.log('zoomOut called');
        
        // FIXED: Zoom at cursor position - keeps point under cursor fixed
        const cursorX = this.lastMouseScreen?.x || (this.canvas.width / 2);
        const cursorY = this.lastMouseScreen?.y || (this.canvas.height / 2);
        
        const S_old = this.zoom;
        const S_new = Math.max(0.25, Math.min(3, S_old - 0.05)); // Clamp to 25%-300%
        
        // Get world position at cursor BEFORE zoom
        const worldX = (cursorX - this.panOffset.x) / S_old;
        const worldY = (cursorY - this.panOffset.y) / S_old;
        
        // Update zoom
        this.zoom = S_new;
        
        // Adjust pan so world position stays at cursor (zoom at cursor)
        this.panOffset.x = cursorX - worldX * S_new;
        this.panOffset.y = cursorY - worldY * S_new;
        this.savePanOffset();
        
        if (this.debugger) {
            const newZoomPercent = Math.round(this.zoom * 100);
            this.debugger.logAction(`🔍- Zoom Out: ${newZoomPercent}% (-5%) at cursor`);
        }
        
        this.updateZoomIndicator();
        this.updateScrollbars();
        this.draw();
        this.updateHud();
    }
    
    resetZoom() {
        // Reset to default zoom and pan (original map location)
        this.zoom = this.defaultZoom;
        this.panOffset.x = this.defaultPanOffset.x;
        this.panOffset.y = this.defaultPanOffset.y;
        
        if (this.debugger) {
            const zoomPercent = Math.round(this.zoom * 100);
            this.debugger.logInfo(`🔄 Zoom reset to ${zoomPercent}%`);
        }
        
        this.updateZoomIndicator();
        this.savePanOffset();
        this.updateScrollbars();
        this.draw();
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
    
    handleKeyDown(e) {
        // Track Ctrl/Cmd for marquee selection
        if (e.key === 'Control' || e.key === 'Meta') {
            this.ctrlPressed = true;
        }
        
        // Track Alt/Option for quick link start
        if (e.key === 'Alt') {
            this.altPressed = true;
        }
        
        // Check if focus is on input/textarea to avoid conflicts
        const isInputFocused = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable;
        
        // Toggle debugger with 'D' key (when no input is focused)
        if (e.key.toLowerCase() === 'd' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
            if (this.debugger) {
                this.debugger.toggle();
                console.log('Debugger toggled:', this.debugger.enabled ? 'ON' : 'OFF');
            }
            return;
        }
        
        // Toggle left toolbar with '[' key (when no input is focused)
        if (e.key === '[' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
            const toolbar = document.getElementById('left-toolbar');
            if (toolbar) {
                toolbar.classList.toggle('collapsed');
                setTimeout(() => {
                    this.resizeCanvas();
                    this.draw();
                }, 300);
                if (this.debugger) {
                    this.debugger.logInfo(`🔧 Left toolbar ${toolbar.classList.contains('collapsed') ? 'hidden' : 'shown'}`);
                }
            }
            return;
        }
        
        // Toggle top bar with ']' key (when no input is focused)
        if (e.key === ']' && !isInputFocused && !e.metaKey && !e.ctrlKey) {
            const topBar = document.querySelector('.top-bar');
            if (topBar) {
                topBar.classList.toggle('collapsed');
                setTimeout(() => {
                    this.resizeCanvas();
                    this.draw();
                }, 300);
                if (this.debugger) {
                    this.debugger.logInfo(`🔝 Top bar ${topBar.classList.contains('collapsed') ? 'hidden' : 'shown'}`);
                }
            }
            return;
        }
        
        // Cmd/Ctrl + S for save
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
            if (!isInputFocused) {
                e.preventDefault();
                this.saveTopology();
            }
            return;
        }
        
        // Cmd/Ctrl + T for text size (only when text is selected)
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 't') {
            if (!isInputFocused) {
                e.preventDefault();
                if (this.selectedObject && this.selectedObject.type === 'text') {
                    this.cycleTextSize();
                }
            }
            return;
        }
        
        // ⌘ + L (Mac) or Ctrl + L (Windows/Linux) for unbound link
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'l') {
            if (!isInputFocused) {
                e.preventDefault();
                this.createUnboundLink();
            }
            return;
        }
        
        // Cmd/Ctrl + Shift + D to set current view as default
        if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'd') {
            if (!isInputFocused) {
                e.preventDefault();
                this.setDefaultView();
                // Show brief confirmation
                const indicator = document.getElementById('mode-indicator');
                if (indicator) {
                    const modeText = indicator.querySelector('#mode-text');
                    const originalText = modeText.textContent;
                    modeText.textContent = 'DEFAULT VIEW SET';
                    setTimeout(() => {
                        modeText.textContent = originalText;
                    }, 1000);
                }
            }
            return;
        }
        
        // Cmd/Ctrl + X to clear entire canvas (IMMEDIATE CLEAR - no confirmation)
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'x') {
            if (!isInputFocused) {
                e.preventDefault();
                this.performClearCanvas();
                if (this.debugger) {
                    this.debugger.logSuccess('🗑️ Canvas cleared (Cmd+X) - ALL objects deleted');
                }
            }
            return;
        }
        
        // Cmd/Ctrl + Z for undo
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
            if (!isInputFocused) {
                e.preventDefault();
                this.undo();
            }
            return;
        }
        
        // Cmd/Ctrl + C for copy
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'c') {
            if (!isInputFocused) {
                e.preventDefault();
                this.copySelected();
            }
            return;
        }
        
        // Cmd/Ctrl + V for paste
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'v') {
            if (!isInputFocused) {
                e.preventDefault();
                this.pasteObjects();
            }
            return;
        }
        
        // Cmd/Ctrl + Y or Cmd/Ctrl + Shift + Z for redo
        if (((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'y') ||
            ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z' && e.shiftKey)) {
            if (!isInputFocused) {
                e.preventDefault();
                this.redo();
            }
            return;
        }
        
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (!isInputFocused) {
                e.preventDefault();
                this.deleteSelected();
                return; // Only return if we handled the delete
            }
            // If input is focused, let browser handle it naturally (don't return, don't prevent)
        }
        
        if (e.key === 'Escape') {
            // Exit device placement mode, multi-select mode or hide context menu
            if (this.contextMenuVisible) {
                this.hideContextMenu();
            } else if (this.placingDevice) {
                // Exit device placement mode
                this.placingDevice = null;
                this.setMode('base');
            } else if (this.multiSelectMode) {
                this.multiSelectMode = false;
                this.selectedObjects = [];
                if (this.selectedObject) {
                    this.selectedObjects = [this.selectedObject];
                }
                this.draw();
            }
        } else if (e.key === ' ') {
            this.spacePressed = true;
            this.updateCursor();
            // Prevent space from scrolling the page
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
            }
        }
    }
    
    handleKeyUp(e) {
        if (e.key === ' ') {
            this.spacePressed = false;
            this.updateCursor();
        }
        
        // Track Ctrl/Cmd release
        if (e.key === 'Control' || e.key === 'Meta') {
            this.ctrlPressed = false;
        }
        
        // Track Alt/Option release
        if (e.key === 'Alt') {
            this.altPressed = false;
        }
    }
    
    updateCursor() {
        if (this.spacePressed) {
            this.canvas.style.cursor = 'move';
        } else if (this.placingDevice) {
            this.canvas.style.cursor = 'crosshair';
        } else if (this.currentTool === 'link') {
            this.canvas.style.cursor = 'crosshair';
        } else {
            this.canvas.style.cursor = 'default';
        }
    }
    
    findObjectAt(x, y) {
        // ENHANCED: Multi-pass detection with priority order
        // Pass 1: Devices have HIGHEST priority (always select device over links)
        for (let i = this.objects.length - 1; i >= 0; i--) {
            const obj = this.objects[i];
            
            if (obj.type === 'device') {
                // Enhanced hitbox: Add tolerance for easier clicking
                // CRITICAL: Hitbox must scale with zoom for consistent screen-space size
                const isSelected = this.selectedObject === obj;
                
                // Base tolerance in screen pixels, divide by zoom to get world coordinates
                // Selected devices: larger hitbox to include handle area
                // Unselected devices: balanced clickable area
                const screenTolerance = isSelected ? 35 : 10; // Balanced for easy clicking
                const hitboxTolerance = screenTolerance / this.zoom; // Convert to world coordinates
                
                const distance = Math.sqrt(Math.pow(x - obj.x, 2) + Math.pow(y - obj.y, 2));
                if (distance <= obj.radius + hitboxTolerance) return obj;
            }
        }
        
        // Pass 2: Check text objects (after devices, before links)
        for (let i = this.objects.length - 1; i >= 0; i--) {
            const obj = this.objects[i];
            
            if (obj.type === 'text') {
                // CRITICAL: Set font BEFORE measuring text
                this.ctx.save();
                this.ctx.font = `${obj.fontSize}px Arial`;
                const metrics = this.ctx.measureText(obj.text || 'Text');
                const w = metrics.width;
                const h = parseInt(obj.fontSize) || 14;
                this.ctx.restore();
                
                // Rotate point to check if it's in bounding box
                const dx = x - obj.x;
                const dy = y - obj.y;
                const angle = -obj.rotation * Math.PI / 180;
                const rx = dx * Math.cos(angle) - dy * Math.sin(angle);
                const ry = dx * Math.sin(angle) + dy * Math.cos(angle);
                
                // ENHANCED: Use actual bounding box between the dots (with padding)
                const padding = 5; // Match the padding used in drawText
                if (Math.abs(rx) <= (w/2 + padding) && Math.abs(ry) <= (h/2 + padding)) return obj;
            }
        }
        
        // Pass 3: Check links and unbound links (LOWEST priority)
        // ULTIMATE PRECISION: Calculate exact distance to EVERY link, then pick the absolute closest
        
        // Step 1: Build array of all links with their exact distances
        const linkDistances = [];
        
        for (let i = this.objects.length - 1; i >= 0; i--) {
            const obj = this.objects[i];
            
            // Check both 'link' and 'unbound' type links
            if (obj.type === 'unbound' || obj.type === 'link') {
                // Skip child links in BUL chains - they're handled via parent
                if (obj.type === 'unbound' && obj.mergedInto) {
                    continue;
                }
                
                let linkStart = obj.start;
                let linkEnd = obj.end;
                let minDistToLink = Infinity;
                
                // Calculate linkIndex for proper offset
                if (obj.device1 && obj.device2) {
                    const d1 = this.objects.find(o => o.id === obj.device1);
                    const d2 = this.objects.find(o => o.id === obj.device2);
                    
                    if (d1 && d2) {
                        // Get linkIndex for proper offset calculation
                        const connectedLinks = this.objects.filter(o => 
                            (o.type === 'link' || (o.type === 'unbound' && o.device1 && o.device2)) &&
                            ((o.device1 === obj.device1 && o.device2 === obj.device2) ||
                             (o.device1 === obj.device2 && o.device2 === obj.device1))
                        ).sort((a, b) => {
                            const idA = parseInt(a.id.split('_')[1]) || 0;
                            const idB = parseInt(b.id.split('_')[1]) || 0;
                            return idA - idB;
                        });
                        
                        const linkIndex = connectedLinks.findIndex(l => l.id === obj.id);
                        obj.linkIndex = linkIndex >= 0 ? linkIndex : 0;
                        
                        // Use accurate curved distance calculation
                        minDistToLink = this.distanceToCurvedLine(x, y, obj, d1, d2);
                        
                        // Calculate offset positions for endpoint checks
                        const angle = Math.atan2(d2.y - d1.y, d2.x - d1.x);
                        const sortedIds = [obj.device1, obj.device2].sort();
                        const isNormalDirection = obj.device1 === sortedIds[0];
                        
                        let offsetAmount = 0;
                        if (obj.linkIndex > 0) {
                            const magnitude = Math.ceil(obj.linkIndex / 2) * 20;
                            const direction = (obj.linkIndex % 2 === 1) ? 1 : -1;
                            offsetAmount = magnitude * direction;
                        }
                        
                        let perpAngle = angle + Math.PI / 2;
                        if (!isNormalDirection) perpAngle += Math.PI;
                        
                        const offsetX = Math.cos(perpAngle) * offsetAmount;
                        const offsetY = Math.sin(perpAngle) * offsetAmount;
                        
                        linkStart = {
                            x: d1.x + Math.cos(angle) * d1.radius + offsetX,
                            y: d1.y + Math.sin(angle) * d1.radius + offsetY
                        };
                        linkEnd = {
                            x: d2.x - Math.cos(angle) * d2.radius + offsetX,
                            y: d2.y - Math.sin(angle) * d2.radius + offsetY
                        };
                    } else if (linkStart && linkEnd) {
                        minDistToLink = this.distanceToLine(x, y, linkStart, linkEnd);
                    }
                } else if (linkStart && linkEnd) {
                    // UL without devices - use straight line distance
                    minDistToLink = this.distanceToLine(x, y, linkStart, linkEnd);
                }
                
                if (!linkStart || !linkEnd) continue;
                if (minDistToLink === Infinity) continue;
                
                // Also check distance to merged child links (BUL)
                if (obj.type === 'unbound' && obj.mergedWith) {
                    const childLink = this.objects.find(o => o.id === obj.mergedWith.linkId);
                    if (childLink && childLink.start && childLink.end) {
                        let minDistToChild = Infinity;
                        
                        if (childLink.device1 && childLink.device2) {
                            const d1 = this.objects.find(o => o.id === childLink.device1);
                            const d2 = this.objects.find(o => o.id === childLink.device2);
                            if (d1 && d2) {
                                minDistToChild = this.distanceToCurvedLine(x, y, childLink, d1, d2);
                            } else {
                                minDistToChild = this.distanceToLine(x, y, childLink.start, childLink.end);
                            }
                        } else {
                            minDistToChild = this.distanceToLine(x, y, childLink.start, childLink.end);
                        }
                        
                        // Use whichever is closer (parent or child)
                        minDistToLink = Math.min(minDistToLink, minDistToChild);
                    }
                }
                
                // Check if click is on device center (exclude if so)
                let onDeviceCenter = false;
                for (const otherObj of this.objects) {
                    if (otherObj.type === 'device') {
                        const deviceDist = Math.sqrt(Math.pow(x - otherObj.x, 2) + Math.pow(y - otherObj.y, 2));
                        if (deviceDist <= (otherObj.radius * 0.5)) {
                            onDeviceCenter = true;
                            break;
                        }
                    }
                }
                
                if (!onDeviceCenter) {
                    linkDistances.push({
                        link: obj,
                        distance: minDistToLink,
                        linkStart: linkStart,
                        linkEnd: linkEnd
                    });
                }
            }
        }
        
        // Step 2: Sort by distance (closest first)
        linkDistances.sort((a, b) => a.distance - b.distance);
        
        // Step 3: Return the absolute closest link if within max clickable distance
        if (linkDistances.length > 0) {
            const closest = linkDistances[0];
            
            // ULTRA-PRECISE: Tight hitbox exactly on the link line
            // 8px screen-space = must click very close to the actual link
            const maxScreenDistance = 8;
            const maxDistance = maxScreenDistance / this.zoom;
            
            if (closest.distance <= maxDistance) {
                return closest.link;
            }
        }
        
        return null; // No link within clickable distance
    }
    
    findRotationHandle(device, x, y) {
        // Check if click is on the rotation handle at bottom-right corner
        // Bottom-right corner angle: -Math.PI/4 (or 315 degrees, -45 degrees)
        const deviceRotation = (device.rotation || 0) * Math.PI / 180;
        
        // Handle logic for Text objects vs Devices
        let handleX, handleY;
        
        if (device.type === 'text') {
            // Text objects: rotation handle is top-right corner of bounding box
            // We need to calculate the bounding box based on text content
            this.ctx.font = `${device.fontSize}px Arial`;
            const metrics = this.ctx.measureText(device.text || 'Text');
            const w = metrics.width;
            const h = parseInt(device.fontSize);
            
            // Unrotated top-right corner relative to center
            const localX = w/2 + 5;
            const localY = -h/2 - 5;
            
            // Rotate the point
            handleX = device.x + (localX * Math.cos(deviceRotation) - localY * Math.sin(deviceRotation));
            handleY = device.y + (localX * Math.sin(deviceRotation) + localY * Math.cos(deviceRotation));
        } else {
            // Devices (circles): bottom-right corner
        const baseAngle = -Math.PI / 4; // Bottom-right corner
        const rotatedAngle = baseAngle + deviceRotation;
        const handleDist = device.radius + 12; // 12px offset from device edge
            handleX = device.x + Math.cos(rotatedAngle) * handleDist;
            handleY = device.y + Math.sin(rotatedAngle) * handleDist;
        }
        
        // Check if click is within hitbox (scaled with zoom for consistent screen size)
        const hitboxSize = 15 / this.zoom; // 15px in screen space
        const dist = Math.sqrt(Math.pow(x - handleX, 2) + Math.pow(y - handleY, 2));
        
        if (dist < hitboxSize) {
            return true;
        }
        return false;
    }
    
    distanceToLine(px, py, lineStart, lineEnd) {
        const A = px - lineStart.x;
        const B = py - lineStart.y;
        const C = lineEnd.x - lineStart.x;
        const D = lineEnd.y - lineStart.y;
        
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = -1;
        
        if (lenSq !== 0) param = dot / lenSq;
        
        let xx, yy;
        if (param < 0) {
            xx = lineStart.x;
            yy = lineStart.y;
        } else if (param > 1) {
            xx = lineEnd.x;
            yy = lineEnd.y;
        } else {
            xx = lineStart.x + param * C;
            yy = lineStart.y + param * D;
        }
        
        const dx = px - xx;
        const dy = py - yy;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    // NEW: Check if two links already share an MP (connection point)
    linksAlreadyShareMP(link1, link2) {
        // Direct parent-child relationship
        if (link1.mergedWith && link1.mergedWith.linkId === link2.id) {
            return true; // link1 is parent of link2
        }
        if (link2.mergedWith && link2.mergedWith.linkId === link1.id) {
            return true; // link2 is parent of link1
        }
        if (link1.mergedInto && link1.mergedInto.parentId === link2.id) {
            return true; // link1 is child of link2
        }
        if (link2.mergedInto && link2.mergedInto.parentId === link1.id) {
            return true; // link2 is child of link1
        }
        
        // Check if they're both in the same merge chain (indirect connection)
        const link1Chain = this.getAllMergedLinks(link1);
        const link2Chain = this.getAllMergedLinks(link2);
        
        // If they share any link in their chains, they're already connected
        for (const chainLink1 of link1Chain) {
            for (const chainLink2 of link2Chain) {
                if (chainLink1.id === chainLink2.id) {
                    return true; // They're in the same merge chain
                }
            }
        }
        
        return false; // No shared MP found
    }
    
    // ENHANCED: Recursively find ALL merged links in the chain
    getAllMergedLinks(link) {
        const mergedSet = new Set();
        const toProcess = [link];
        const processed = new Set();
        
        while (toProcess.length > 0) {
            const currentLink = toProcess.pop();
            
            // Skip if already processed
            if (processed.has(currentLink.id)) continue;
            processed.add(currentLink.id);
            
            // Add to result set
            mergedSet.add(currentLink);
            
            // Check for merged partner (parent)
            if (currentLink.mergedWith) {
                const childLink = this.objects.find(o => o.id === currentLink.mergedWith.linkId);
                if (childLink && !processed.has(childLink.id)) {
                    toProcess.push(childLink);
                }
            }
            
            // Check for merged parent (if this is a child)
            if (currentLink.mergedInto) {
                const parentLink = this.objects.find(o => o.id === currentLink.mergedInto.parentId);
                if (parentLink && !processed.has(parentLink.id)) {
                    toProcess.push(parentLink);
                }
            }
            
            // ENHANCED: Also check if any OTHER links are merged with this one
            this.objects.forEach(obj => {
                if (obj.type === 'unbound' && !processed.has(obj.id)) {
                    // Check if obj is merged with currentLink
                    if (obj.mergedWith && obj.mergedWith.linkId === currentLink.id) {
                        toProcess.push(obj);
                    } else if (obj.mergedInto && obj.mergedInto.parentId === currentLink.id) {
                        toProcess.push(obj);
                    }
                }
            });
        }
        
        return Array.from(mergedSet);
    }
    
    getParentConnectionEndpoint(link) {
        if (!link?.mergedWith) return null;
        if (link.mergedWith.connectionEndpoint) return link.mergedWith.connectionEndpoint;
        return link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
    }
    
    getChildConnectionEndpoint(link) {
        if (!link?.mergedInto) return null;
        if (link.mergedInto.childEndpoint) return link.mergedInto.childEndpoint;
        const parentLink = this.objects.find(o => o.id === link.mergedInto.parentId);
        if (parentLink?.mergedWith) {
            const childFreeEnd = parentLink.mergedWith.childFreeEnd;
            return childFreeEnd === 'start' ? 'end' : 'start';
        }
        return null;
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
        const allLinks = this.getAllMergedLinks(link);
        let tpCount = 0;
        let mpCount = 0;
        
        // Count MPs (merge points) - each mergedWith relationship creates one MP
        allLinks.forEach(chainLink => {
            if (chainLink.mergedWith) {
                mpCount++;
            }
        });
        
        // FIXED: Count actual free TPs by checking BOTH mergedWith AND mergedInto
        // An endpoint is a TP if it's NOT connected to another link
        allLinks.forEach(chainLink => {
            // Check start endpoint
            let startIsConnected = false;
            
            // Check if THIS link's start is the connection point (via mergedWith)
            if (chainLink.mergedWith) {
                // parentFreeEnd tells us which end is FREE, so the OTHER end is connected
                if (chainLink.mergedWith.parentFreeEnd === 'end') {
                    startIsConnected = true; // Start is the MP (connected to child)
                }
            }
            // Check if THIS link's start is connected via mergedInto (this link is a child)
            if (chainLink.mergedInto) {
                const parentLink = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    // childFreeEnd tells us which end of the CHILD is free
                    if (parentLink.mergedWith.childFreeEnd === 'end') {
                        startIsConnected = true; // Start is connected to parent
                    }
                }
            }
            if (!startIsConnected) tpCount++;
            
            // Check end endpoint
            let endIsConnected = false;
            
            // Check if THIS link's end is the connection point (via mergedWith)
            if (chainLink.mergedWith) {
                // parentFreeEnd tells us which end is FREE, so the OTHER end is connected
                if (chainLink.mergedWith.parentFreeEnd === 'start') {
                    endIsConnected = true; // End is the MP (connected to child)
                }
            }
            // Check if THIS link's end is connected via mergedInto (this link is a child)
            if (chainLink.mergedInto) {
                const parentLink = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    // childFreeEnd tells us which end of the CHILD is free
                    if (parentLink.mergedWith.childFreeEnd === 'start') {
                        endIsConnected = true; // End is connected to parent
                    }
                }
            }
            if (!endIsConnected) tpCount++;
        });
        
        return {
            linkCount: allLinks.length,
            tpCount,
            mpCount,
            links: allLinks,
            isValid: (tpCount === 2 && mpCount === allLinks.length - 1) // Valid: 2 TPs, N-1 MPs for N links
        };
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
    calculateLinkIndex(link) {
        // Get the endpoint devices for this link/BUL
        const endpoints = this.getBULEndpointDevices(link);
        
        if (!endpoints.hasEndpoints || !endpoints.device1 || !endpoints.device2) {
            return 0; // Default to middle if no proper endpoints
        }
        
        // ENHANCED: Count ALL existing links (both QL and UL) between the same two devices
        const existingLinks = this.objects.filter(obj => {
            if (obj.id === link.id) return false; // Skip self
            
            // Count Quick Links (type: 'link')
            if (obj.type === 'link' && obj.device1 && obj.device2) {
                return (obj.device1 === endpoints.device1 && obj.device2 === endpoints.device2) ||
                       (obj.device1 === endpoints.device2 && obj.device2 === endpoints.device1);
            }
            
            // Count Unbound Links (type: 'unbound') with both endpoints attached
            if (obj.type === 'unbound') {
            const objEndpoints = this.getBULEndpointDevices(obj);
            if (!objEndpoints.hasEndpoints) return false;
            
            // Check if connecting the same two devices (bidirectional)
            return (objEndpoints.device1 === endpoints.device1 && objEndpoints.device2 === endpoints.device2) ||
                   (objEndpoints.device1 === endpoints.device2 && objEndpoints.device2 === endpoints.device1);
            }
            
            return false;
        });
        
        return existingLinks.length;
    }
    
    // NEW: Handle UL deletion in a BUL chain - reconfigure merge relationships
    handleULDeletionInBUL(deletedLink) {
        // When a UL in a BUL chain is deleted, we need to:
        // 1. Disconnect it from parent and child
        // 2. Optionally reconnect parent and child directly (if both exist)
        // 3. Clean up merge metadata
        
        const parentLink = deletedLink.mergedInto ? this.objects.find(o => o.id === deletedLink.mergedInto.parentId) : null;
        const childLink = deletedLink.mergedWith ? this.objects.find(o => o.id === deletedLink.mergedWith.linkId) : null;
        
        if (this.debugger) {
            this.debugger.logInfo(`🔗 Removing UL from BUL chain: ${deletedLink.id}`);
            if (parentLink) this.debugger.logInfo(`   Parent: ${parentLink.id}`);
            if (childLink) this.debugger.logInfo(`   Child: ${childLink.id}`);
        }
        
        // Case 1: Link has both parent and child (middle of chain)
        if (parentLink && childLink) {
            // Remove child's connection to deleted link
            if (childLink.mergedInto && childLink.mergedInto.parentId === deletedLink.id) {
                delete childLink.mergedInto;
            }
            
            // Remove parent's connection to deleted link
            if (parentLink.mergedWith && parentLink.mergedWith.linkId === deletedLink.id) {
                delete parentLink.mergedWith;
            }
            
            // Note: We don't auto-reconnect parent to child because they may be too far apart
            // The user can manually reconnect if desired
            if (this.debugger) {
                this.debugger.logInfo(`   ✂️ Chain split: ${parentLink.id} and ${childLink.id} are now separate`);
            }
        }
        // Case 2: Link has only parent (end of chain)
        else if (parentLink && !childLink) {
            // Remove parent's connection to deleted link
            if (parentLink.mergedWith && parentLink.mergedWith.linkId === deletedLink.id) {
                delete parentLink.mergedWith;
                if (this.debugger) {
                    this.debugger.logInfo(`   ✂️ ${parentLink.id} is now free at its former connection point`);
                }
            }
        }
        // Case 3: Link has only child (start of chain)
        else if (childLink && !parentLink) {
            // Remove child's connection to deleted link
            if (childLink.mergedInto && childLink.mergedInto.parentId === deletedLink.id) {
                delete childLink.mergedInto;
                if (this.debugger) {
                    this.debugger.logInfo(`   ✂️ ${childLink.id} is now free at its former connection point`);
                }
            }
        }
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
            }
        });
    }
    
    distanceToCurvedLine(px, py, link, device1, device2) {
        // Check distance to line (curved or straight based on curve mode)
        // FIXED: Don't require link.start/end - we calculate from device positions anyway
        if (!device1 || !device2) return Infinity;
        
        // Determine if curve mode is enabled for this link
        // Magnetic field must be > 0 for curves to work
        const curveEnabled = (link.curveOverride !== undefined ? link.curveOverride : this.linkCurveMode) && this.magneticFieldStrength > 0;
        
        const linkIndex = link.linkIndex || 0;
        const angle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
        
        // NORMALIZE perpendicular direction for true bidirectional behavior (same as drawLink)
        const sortedIds = [link.device1, link.device2].sort();
        const isNormalDirection = link.device1 === sortedIds[0];
        
        // Calculate offset (same as in drawLink)
        // User requested logic: First (0) = Middle, Second (1) = Right (+), Third (2) = Left (-)
        let offsetAmount = 0;
        let direction = 0;
        if (linkIndex > 0) {
            const magnitude = Math.ceil(linkIndex / 2) * 20;
            direction = (linkIndex % 2 === 1) ? 1 : -1; // Odd = Right (+), Even = Left (-)
            offsetAmount = magnitude * direction;
        }
        
        // Calculate perpendicular offset with normalized direction
        let perpAngle = angle + Math.PI / 2;
        if (!isNormalDirection) {
            perpAngle += Math.PI; // Flip 180 degrees for consistent sides
        }
        
        const offsetX = Math.cos(perpAngle) * offsetAmount;
        const offsetY = Math.sin(perpAngle) * offsetAmount;
        
        const startX = device1.x + Math.cos(angle) * device1.radius;
        const startY = device1.y + Math.sin(angle) * device1.radius;
        const endX = device2.x - Math.cos(angle) * device2.radius;
        const endY = device2.y - Math.sin(angle) * device2.radius;
        
        const offsetStartX = startX + offsetX;
        const offsetStartY = startY + offsetY;
        const offsetEndX = endX + offsetX;
        const offsetEndY = endY + offsetY;
        
        if (!curveEnabled) {
            // Curve mode disabled - calculate distance to straight line
            return this.distanceToLine(px, py, 
                { x: offsetStartX, y: offsetStartY }, 
                { x: offsetEndX, y: offsetEndY }
            );
        }
        
        // Curve mode enabled - check for obstacles and calculate distance to curved line
        const obstacles = this.findAllObstaclesOnPath(offsetStartX, offsetStartY, offsetEndX, offsetEndY, link);
        
        let minDist = Infinity;
        // ULTIMATE PRECISION: Maximum samples for pixel-perfect hitbox accuracy
        const samples = 100; // High precision for exact curve matching
        let cp1x, cp1y, cp2x, cp2y;
        
        if (obstacles.length > 0) {
            // Gentle magnetic repulsion (same algorithm as drawLink for consistency)
            const straightMidX = (offsetStartX + offsetEndX) / 2;
            const straightMidY = (offsetStartY + offsetEndY) / 2;
            const linkLength = Math.sqrt(Math.pow(offsetEndX - offsetStartX, 2) + Math.pow(offsetEndY - offsetStartY, 2));
            
            let totalRepulsionX = 0;
            let totalRepulsionY = 0;
            let closestObstacleRadius = 0;
            
            obstacles.forEach((obstacleInfo) => {
                const obstacle = obstacleInfo.device;
                const dx = straightMidX - obstacle.x;
                const dy = straightMidY - obstacle.y;
                const distToMid = Math.sqrt(dx * dx + dy * dy) || 1;
                const minClearance = obstacle.radius + 18;
                const repelDirX = dx / distToMid;
                const repelDirY = dy / distToMid;
                const k = minClearance * minClearance * this.magneticFieldStrength * 2; // Increased strength
                const repulsionStrength = k / Math.pow(distToMid, 0.8); // Stronger magnetic repulsion falloff
                totalRepulsionX += repelDirX * repulsionStrength;
                totalRepulsionY += repelDirY * repulsionStrength;
                closestObstacleRadius = Math.max(closestObstacleRadius, obstacle.radius);
            });
            
            const deflectionMag = Math.sqrt(totalRepulsionX * totalRepulsionX + totalRepulsionY * totalRepulsionY);
            const maxDeflection = Math.min(linkLength * 0.45, closestObstacleRadius * 2.5); // Match drawing
            const actualDeflection = Math.min(deflectionMag, maxDeflection);
            const normalizedRepulX = totalRepulsionX / (deflectionMag || 1);
            const normalizedRepulY = totalRepulsionY / (deflectionMag || 1);
            const deflectedMidX = straightMidX + normalizedRepulX * actualDeflection;
            const deflectedMidY = straightMidY + normalizedRepulY * actualDeflection;
            
            // Curvier control points (same as drawing)
            const controlWeight = 0.7; // Match drawing for consistency
            const midWeight = 1 - controlWeight;
            cp1x = offsetStartX * midWeight + deflectedMidX * controlWeight;
            cp1y = offsetStartY * midWeight + deflectedMidY * controlWeight;
            cp2x = offsetEndX * midWeight + deflectedMidX * controlWeight;
            cp2y = offsetEndY * midWeight + deflectedMidY * controlWeight;
        } else {
            // No obstacles - simple curve for multi-link separation
            const curveOffset = linkIndex > 0 ? Math.ceil(linkIndex / 2) * 10 * direction : 0;
            cp1x = offsetStartX + Math.cos(perpAngle) * curveOffset;
            cp1y = offsetStartY + Math.sin(perpAngle) * curveOffset;
            cp2x = offsetEndX + Math.cos(perpAngle) * curveOffset;
            cp2y = offsetEndY + Math.sin(perpAngle) * curveOffset;
        }
        
        // Sample points along Bezier curve
        for (let i = 0; i <= samples; i++) {
            const t = i / samples;
            const curveX = Math.pow(1-t, 3) * offsetStartX + 3 * Math.pow(1-t, 2) * t * cp1x + 3 * (1-t) * Math.pow(t, 2) * cp2x + Math.pow(t, 3) * offsetEndX;
            const curveY = Math.pow(1-t, 3) * offsetStartY + 3 * Math.pow(1-t, 2) * t * cp1y + 3 * (1-t) * Math.pow(t, 2) * cp2y + Math.pow(t, 3) * offsetEndY;
            
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
                this.debugger.logInfo(`🔄 ${tool.toUpperCase()} → BASE (toggle off)`);
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
            
            // Update button states
            document.getElementById('btn-base').classList.remove('active');
            document.getElementById('btn-select').classList.remove('active');
            document.getElementById('btn-link').classList.remove('active');
            document.getElementById('btn-text').classList.remove('active');
            document.getElementById('btn-router').classList.remove('active');
            document.getElementById('btn-switch').classList.remove('active');
            document.getElementById(`btn-${tool}`).classList.add('active');
            
            this.updateModeIndicator();
            
            if (this.debugger) {
                this.debugger.logSuccess(`🔄 ${(oldMode || 'BASE').toUpperCase()} → ${tool.toUpperCase()} (seamless)`);
            }
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
    
    toggleAngleMeter() {
        this.showAngleMeter = !this.showAngleMeter;
        const btn = document.getElementById('btn-angle-meter');
        if (btn) {
            const statusText = btn.querySelector('.status-text');
            if (this.showAngleMeter) {
                btn.classList.add('active');
                if (statusText) statusText.textContent = 'Angle: ON';
                if (this.debugger) this.debugger.logSuccess('📐 Angle meter enabled');
            } else {
                btn.classList.remove('active');
                if (statusText) statusText.textContent = 'Angle: OFF';
                if (this.debugger) this.debugger.logInfo('📐 Angle meter disabled');
            }
        }
        this.draw();
        this.scheduleAutoSave();
    }
    
    toggleLinkCurveMode() {
        this.linkCurveMode = !this.linkCurveMode;
        const btn = document.getElementById('btn-link-curve');
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
        this.draw(); // Redraw with new curve mode
        this.scheduleAutoSave(); // Save setting change
    }
    
    toggleLinkContinuousMode() {
        this.linkContinuousMode = !this.linkContinuousMode;
        const btn = document.getElementById('btn-link-continuous');
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
        this.draw();
        this.scheduleAutoSave(); // Save setting change
    }
    
    toggleLinkStickyMode() {
        this.linkStickyMode = !this.linkStickyMode;
        const btn = document.getElementById('btn-link-sticky');
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
        this.draw();
        this.scheduleAutoSave(); // Save setting change
    }
    
    toggleLinkULMode() {
        this.linkULEnabled = !this.linkULEnabled;
        const btn = document.getElementById('btn-link-ul');
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
        this.draw();
        this.scheduleAutoSave(); // Save setting change
    }
    
    setLinkStyle(style) {
        this.linkStyle = style; // 'solid', 'dashed', or 'arrow'
        
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
        } else if (style === 'dashed' && dashedBtn) {
            dashedBtn.classList.add('active');
        } else if (style === 'arrow' && arrowBtn) {
            arrowBtn.classList.add('active');
        }
        
        if (this.debugger) {
            this.debugger.logInfo(`🎨 Link style changed to: ${style.toUpperCase()}`);
        }
        
        this.draw(); // Redraw with new style
        this.scheduleAutoSave(); // Save setting change
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
            if (statusText) statusText.textContent = 'Numbering: ON';
        } else {
            btn.classList.remove('active');
            btn.title = 'Device Numbering OFF - All devices use base name (NCP, S)';
            if (statusText) statusText.textContent = 'Numbering: OFF';
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
            if (statusText) statusText.textContent = 'Collision: ON';
            // Update icon to show separated circles
            svg.innerHTML = `
                <circle cx="8" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
                <circle cx="16" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
            `;
            
            // AUTO-FIX: Separate any existing overlapping devices
            this.fixExistingOverlaps();
        } else {
            btn.classList.remove('active');
            btn.title = 'Collision OFF - Devices Can Overlap';
            if (statusText) statusText.textContent = 'Collision: OFF';
            // Update icon to show overlapping circles
            svg.innerHTML = `
                <circle cx="9" cy="12" r="5" stroke="currentColor" stroke-width="2" fill="none"/>
                <circle cx="15" cy="12" r="5" stroke="currentColor" stroke-width="2" fill="none"/>
            `;
        }
        this.scheduleAutoSave(); // Save setting change
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
                btn.title = 'Movable ON - Devices Push Each Other on Collision';
                if (statusText) statusText.textContent = 'Movable: ON';
            } else {
                btn.classList.remove('active');
                btn.title = 'Movable OFF - Devices Are Static';
                if (statusText) statusText.textContent = 'Movable: OFF';
            }
        }
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
                if (statusText) statusText.textContent = 'Slide: ON';
                // Show slide distance slider
                if (slideControl) slideControl.style.display = 'block';
            } else {
                btn.classList.remove('active');
                btn.title = 'Momentum/Sliding OFF';
                if (statusText) statusText.textContent = 'Slide: OFF';
                // Hide slide distance slider
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
                onText: 'Numbering: ON',
                offText: 'Numbering: OFF'
            },
            {
                id: 'btn-device-collision',
                state: this.deviceCollision,
                name: 'Device Collision',
                onText: 'Collision: ON',
                offText: 'Collision: OFF'
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
                onText: 'Slide: ON',
                offText: 'Slide: OFF'
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
            this.debugger.logSuccess(`🔄 Toggle Sync Complete: ${syncCount}/${toggles.length} synced${errorCount > 0 ? `, ${errorCount} errors` : ''}`);
            this.debugger.logInfo(`Code: syncAllToggles() [topology.js:2910-2994]`);
        }
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
                const minDist = (d1.radius || 30) + (d2.radius || 30) + 3;
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
                    const minDist = (d1.radius || 30) + (d2.radius || 30) + 3;
                    
                    if (dist < minDist) {
                        // Push devices apart (split the push between both)
                        const push = (minDist - dist) / 2;
                        const epsilon = 0.01;
                        
                        let nx, ny;
                        if (dist < epsilon) {
                            // Coincident - push in arbitrary direction
                            nx = 1;
                            ny = 0;
                            dist = epsilon;
                        } else {
                            nx = dx / dist;
                            ny = dy / dist;
                        }
                        
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
                const minDist = (d1.radius || 30) + (d2.radius || 30) + 3;
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
    
    updateMagneticField(value) {
        const oldValue = this.magneticFieldStrength;
        this.magneticFieldStrength = parseInt(value);
        document.getElementById('magnetic-field-value').textContent = value;

        // Log to debugger (throttled)
        if (this.debugger && Math.abs(oldValue - this.magneticFieldStrength) >= 5) {
            this.debugger.logInfo(`🧲 Magnetic field: ${this.magneticFieldStrength}/80`);
        }

        // Throttle redraws to prevent interference with other interactions
        if (this.magneticFieldUpdateTimer) {
            clearTimeout(this.magneticFieldUpdateTimer);
        }
        this.magneticFieldUpdateTimer = setTimeout(() => {
            this.draw(); // Redraw links with new magnetic strength
            this.scheduleAutoSave(); // Save setting change
            this.magneticFieldUpdateTimer = null;
        }, 16); // ~60fps
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
            this.debugger.logInfo(`🔄 Chain reaction depth ${depth + 1}: ${movingDevice.label || 'Device'} (v=${velocityMag.toFixed(2)}px)`);
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
            const minDist = (movingDevice.radius || 30) + (targetDevice.radius || 30);
            
            // CRITICAL FIX: Trigger chain reaction when devices are CLOSE (not just overlapping)
            // Add a threshold zone where devices can push each other
            const proximityThreshold = 5; // Devices within 5px of touching can push each other
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
    
    checkDeviceCollision(movingDevice, proposedX, proposedY) {
        // CRITICAL FIX: Don't apply collision if device is being locked for grab setup
        if (this._lockingDeviceForGrab && this._lockedDevice === movingDevice) {
            // Return original position - don't modify anything during grab
            return { x: proposedX, y: proposedY };
        }
        
        // Get list of ALL devices that are currently being dragged (including the moving device)
        const movingDevices = new Set();
        movingDevices.add(movingDevice.id);
        
        // If we're in multi-select drag, include all selected devices
        if (this.selectedObjects && this.selectedObjects.length > 1 && this.multiSelectInitialPositions) {
            this.selectedObjects.forEach(obj => {
                if (obj.type === 'device' && obj.id !== movingDevice.id) {
                    movingDevices.add(obj.id);
                }
            });
        }
        
        // Get other devices for collision detection
        const otherDevices = this.objects.filter(obj => 
            obj.type === 'device' && !movingDevices.has(obj.id) && 
            !(this._lockingDeviceForGrab && this._lockedDevice === obj) // Skip locked device
        );
        
        // Standard collision (equal push) - original code
        let x = proposedX;
        let y = proposedY;
        const maxIterations = 8;
        const epsilon = 0.01;
        let collisionDetected = false;
        const collisionSet = new Set(); // Use Set to track unique collisions
        
        for (let iter = 0; iter < maxIterations; iter++) {
            let adjusted = false;
            for (const obj of otherDevices) {
                // Calculate distance from proposed position
                const dx = x - obj.x;
                const dy = y - obj.y;
                let dist = Math.sqrt(dx * dx + dy * dy);
                const minDist = (movingDevice.radius || 30) + (obj.radius || 30) + 3;
                
                // Handle coincident centers
                let nx, ny;
                if (dist < epsilon) {
                    // Choose a small arbitrary direction away from the other device
                    nx = 1; ny = 0; dist = epsilon;
                } else {
                    nx = dx / dist; ny = dy / dist;
                }
                
                if (dist < minDist) {
                    const push = minDist - dist;
                    x += nx * push;
                    y += ny * push;
                    adjusted = true;
                    collisionDetected = true;
                    
                    // Track unique collision for debugger
                    collisionSet.add(obj.label || obj.id);
                }
            }
            if (!adjusted) break;
        }
        
        // Throttled logging - only log once per 500ms to avoid spam
        const now = Date.now();
        if (this.debugger && collisionDetected) {
            if (!this._lastCollisionLog || now - this._lastCollisionLog > 500) {
                this._lastCollisionLog = now;
                const movingLabel = movingDevice.label || 'Device';
                const uniqueCollisions = Array.from(collisionSet);
                const summary = uniqueCollisions.length > 3 
                    ? `${uniqueCollisions.slice(0, 3).join(', ')} +${uniqueCollisions.length - 3} more`
                    : uniqueCollisions.join(', ');
                
                this.debugger.logWarning(`⚠️ Collision: ${movingLabel} vs ${summary}`);
            }
        }
        
        return { x, y };
    }
    
    setTool(tool) {
        // Legacy function - now uses setMode()
        this.setMode(tool === 'select' ? 'base' : tool);
    }
    
    setDevicePlacementMode(deviceType) {
        // Clear multi-select state when entering device placement
        this.multiSelectMode = false;
        this.selectedObjects = [];
        this.selectedObject = null;
        
        this.placingDevice = deviceType;
        this.currentTool = 'select'; // Use select tool but we'll override click behavior
        this.canvas.style.cursor = 'crosshair';
        // Highlight the button
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
        if (deviceType === 'router') {
            document.getElementById('btn-router').classList.add('active');
        } else {
            document.getElementById('btn-switch').classList.add('active');
        }
    }
    
    addDeviceAtPosition(type, x, y) {
        // CRITICAL FIX: Always use the passed position (which should be the clicked position)
        // Don't rely on lastClickPos as it might be stale from previous rapid placements
        const clickedWorld = { x, y };
        const clickedGrid = this.worldToGrid(clickedWorld);
        
        // CRITICAL FIX: Snap position to grid for accurate placement
        // Convert clicked position to grid, round to nearest integer, then convert back to world
        // This ensures devices are ALWAYS placed exactly on grid cells, even during rapid placement
        const snappedGrid = {
            x: Math.round(clickedGrid.x),
            y: Math.round(clickedGrid.y)
        };
        const snappedWorld = this.gridToWorld(snappedGrid);
        
        // Validate that snapped position is valid (not NaN or Infinity)
        if (!isFinite(snappedWorld.x) || !isFinite(snappedWorld.y)) {
            console.error('Invalid snapped position:', snappedWorld, 'from grid:', snappedGrid, 'clicked:', clickedWorld);
            // Fallback to original position if snapping fails
            snappedWorld.x = x;
            snappedWorld.y = y;
        }
        
        const label = this.getNextDeviceLabel(type);
        
        // Validate device name uniqueness only when numbering is enabled
        if (this.deviceNumbering && !this.isDeviceNameUnique(label)) {
            alert(`Device name "${label}" already exists. Please choose a different name.`);
            return;
        }

        // Default colors: Muted blue for routers (NCP), current picker color for switches
        const defaultColor = type === 'router' ? '#5B9BD5' : document.getElementById('color-picker').value;
        
        const device = {
            id: `device_${this.deviceIdCounter++}`,
            type: 'device',
            deviceType: type,
            x: snappedWorld.x,  // Use snapped position instead of raw coordinates
            y: snappedWorld.y,  // Use snapped position instead of raw coordinates
            radius: 50,
            rotation: 0,
            color: defaultColor,
            label: label,
            locked: false
        };
        
        this.saveState(); // Save before adding device for undo
        this.objects.push(device);
        this.selectedObject = device;
        this.selectedObjects = [device];
        this.updateDeviceProperties();
        this.draw();
        
        // CRITICAL: Clear lastClickPos immediately after use to prevent reuse in quick successive placements
        // This prevents stale click positions from affecting subsequent rapid placements
        this.lastClickPos = null;
        
        // Verify device is actually on grid (for debugging)
        const verifyGrid = this.worldToGrid({ x: device.x, y: device.y });
        if (Math.abs(verifyGrid.x - Math.round(verifyGrid.x)) > 0.01 || 
            Math.abs(verifyGrid.y - Math.round(verifyGrid.y)) > 0.01) {
            console.warn('Device not properly snapped to grid:', {
                device: { x: device.x, y: device.y },
                grid: verifyGrid,
                expectedGrid: snappedGrid
            });
        }
        
        this.draw();

        // Debugger tracking with position verification
        // Compare MOUSE CLICK position vs DEVICE FINAL position
        if (this.debugger) {
            const placedWorld = { x: device.x, y: device.y };
            const placedGrid = this.worldToGrid(placedWorld);
            // Calculate deltas from original clicked position to final placed position
            const worldDeltaX = Math.abs(clickedWorld.x - placedWorld.x);
            const worldDeltaY = Math.abs(clickedWorld.y - placedWorld.y);
            // After grid snapping, device should be exactly on the snapped grid cell
            // Check if placed grid matches the snapped grid (should be identical)
            const gridDeltaX = Math.abs(snappedGrid.x - placedGrid.x);
            const gridDeltaY = Math.abs(snappedGrid.y - placedGrid.y);
            // After grid snapping, device should be exactly on grid - check grid alignment instead
            // Small world differences are expected due to grid snapping, but grid should match exactly
            const hasMismatch = gridDeltaX > 0.1 || gridDeltaY > 0.1; // Should be exactly on grid now
            
            // Update placement tracking display
            const clickTrackDiv = document.getElementById('debug-click-track');
            if (clickTrackDiv) {
                clickTrackDiv.innerHTML = `
                    <span style="color: #0ff; font-weight: bold;">🖱️ Mouse Click:</span><br>
                    World: (${Math.round(clickedWorld.x)}, ${Math.round(clickedWorld.y)})<br>
                    Grid: (${Math.round(clickedGrid.x)}, ${Math.round(clickedGrid.y)})<br>
                    <span style="color: ${hasMismatch ? '#f00' : '#0f0'}; font-weight: bold;">📦 Device Placed:</span><br>
                    World: (${Math.round(placedWorld.x)}, ${Math.round(placedWorld.y)})<br>
                    Grid: (${Math.round(placedGrid.x)}, ${Math.round(placedGrid.y)})<br>
                    <span style="color: #fa0;">Zoom:</span> ${Math.round(this.zoom * 100)}%<br>
                    ${hasMismatch ? `<span style="color: #f00; font-weight: bold;">⚠️ MISMATCH!</span><br>
                    <span style="color: #f00;">ΔWorld: (${Math.round(worldDeltaX)}, ${Math.round(worldDeltaY)})</span><br>
                    <span style="color: #f00;">ΔGrid: (${gridDeltaX.toFixed(2)}, ${gridDeltaY.toFixed(2)})</span><br>
                    <span style="color: #888; font-size: 9px;">
                    Possible causes:<br>
                    - Mouse moved between click & place<br>
                    - Coordinate transform issue<br>
                    Code: addDeviceAtPosition() [3123]<br>
                    getMousePos() [664]<br>
                    handleMouseUp() [1461-1471]
                    </span>` : '<span style="color: #0f0; font-weight: bold;">✓ ACCURATE PLACEMENT</span>'}
                `;
            }
            
            this.debugger.logSuccess(`📍 Device placed: ${label} at Grid(${Math.round(placedGrid.x)}, ${Math.round(placedGrid.y)})`);
            
            if (hasMismatch) {
                // Only log as error if mismatch is truly significant (>30px), otherwise just warn
                // Increased threshold because placement offsets can be normal due to:
                // - Grid snapping rounding
                // - Coordinate transforms (screen → world → grid)
                // - Mouse movement between click and placement
                const worldDelta = Math.sqrt(worldDeltaX * worldDeltaX + worldDeltaY * worldDeltaY);
                if (worldDelta > 30) {
                    // Significant mismatch - might be a real issue
                    this.debugger.logWarning(`⚠️ SIGNIFICANT placement offset detected (${Math.round(worldDelta)}px)`);
                    this.debugger.logError(`ΔWorld: (${Math.round(worldDeltaX)}, ${Math.round(worldDeltaY)}) | ΔGrid: (${gridDeltaX.toFixed(2)}, ${gridDeltaY.toFixed(2)})`);
                } else {
                    // Small/medium mismatch - normal due to grid snapping, just log as info (no bug alert)
                    this.debugger.logInfo(`📍 Placement offset: ΔWorld(${Math.round(worldDeltaX)}, ${Math.round(worldDeltaY)}) | ΔGrid(${gridDeltaX.toFixed(2)}, ${gridDeltaY.toFixed(2)}) - Normal due to grid snapping`);
                }
                this.debugger.logInfo(`Clicked: World(${Math.round(clickedWorld.x)}, ${Math.round(clickedWorld.y)}) → Placed: World(${Math.round(placedWorld.x)}, ${Math.round(placedWorld.y)})`);
                this.debugger.logInfo(`Code: handleMouseUp() [1461-1471] → addDeviceAtPosition() [3380] → getMousePos() [678]`);
                this.debugger.logInfo(`Tolerance: ±5px | Check coordinate transforms if this persists`);
            } else {
                // No mismatch - clear any stale bug states from previous placements
                if (this.debugger && this.debugger.latestBug && 
                    (this.debugger.latestBug.includes('placement offset') || 
                     this.debugger.latestBug.includes('ΔWorld'))) {
                    // Clear stale placement-related bug states after successful accurate placement
                    this.debugger.latestBug = null;
                }
            }
        }

        // Save state AFTER adding device - each device placement creates one distinct step
        this.saveState();

        // Immediate auto-save for device placement
        this.autoSave();
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
            this.debugger.logInfo(`🔄 Marquee started from ${previousMode.toUpperCase()} mode`);
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
            // Skip locked objects - they cannot be selected via marquee
            if (obj.locked) return;
            
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
                    const samples = 30; // Many samples for accurate detection
                    for (let i = 0; i <= samples; i++) {
                        const t = i / samples;
                        const px = obj.start.x + (obj.end.x - obj.start.x) * t;
                        const py = obj.start.y + (obj.end.y - obj.start.y) * t;
                        
                        // Expand hitbox around each sampled point
                        if (px >= rect.x - linkHitboxTolerance && px <= rect.x + rect.width + linkHitboxTolerance &&
                            py >= rect.y - linkHitboxTolerance && py <= rect.y + rect.height + linkHitboxTolerance) {
                            intersects = true;
                            break;
                        }
                    }
                    
                    // Also check if link line intersects rectangle edges
                    if (!intersects) {
                        intersects = this.lineIntersectsRect(obj.start, obj.end, rect);
                    }
                }
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
        const menu = document.getElementById('context-menu');
        menu.style.display = 'block';
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
        this.contextMenuVisible = true;
        
        // Check what types of objects are selected
        const hasDevices = this.selectedObjects.some(obj => obj.type === 'device');
        const hasLinks = this.selectedObjects.some(obj => obj.type === 'link' || obj.type === 'unbound');
        const hasText = this.selectedObjects.some(obj => obj.type === 'text');
        const hasLockable = this.selectedObjects.some(obj => obj.type === 'device' || obj.type === 'text');
        
        // Show appropriate bulk operations
        document.getElementById('ctx-duplicate').style.display = 'none';
        document.getElementById('ctx-add-text').style.display = 'none';
        document.getElementById('ctx-change-color').style.display = (hasDevices || hasText) ? 'block' : 'none';
        document.getElementById('ctx-change-size').style.display = 'none';
        document.getElementById('ctx-change-label').style.display = 'none';
        
        // Show curve toggle only if links are selected
        const toggleCurveItem = document.getElementById('ctx-toggle-curve');
        if (hasLinks) {
            toggleCurveItem.style.display = 'block';
            // Show status for first link in selection
            const firstLink = this.selectedObjects.find(obj => obj.type === 'link' || obj.type === 'unbound');
            const curveEnabled = firstLink && (firstLink.curveOverride !== undefined ? firstLink.curveOverride : this.linkCurveMode);
            const linkCount = this.selectedObjects.filter(obj => obj.type === 'link' || obj.type === 'unbound').length;
            toggleCurveItem.textContent = curveEnabled ? 
                `Curve: ON (${linkCount} Link${linkCount > 1 ? 's' : ''})` : 
                `Curve: OFF (${linkCount} Link${linkCount > 1 ? 's' : ''})`;
        } else {
            toggleCurveItem.style.display = 'none';
        }
        
        document.getElementById('ctx-toggle-lock').style.display = hasLockable ? 'block' : 'none';
        document.getElementById('ctx-delete').style.display = 'block';
        
        // Update lock text based on selection
        if (hasLockable) {
            const allLocked = this.selectedObjects.filter(obj => obj.type === 'device' || obj.type === 'text').every(obj => obj.locked);
        document.getElementById('ctx-toggle-lock').textContent = allLocked ? 'Unlock All' : 'Lock All';
        }
    }
    
    duplicateObject(obj, mirror = false) {
        this.saveState(); // Save before duplicating
        let duplicate;
        
        if (obj.type === 'device') {
            const label = this.getNextDeviceLabel(obj.deviceType);
            duplicate = {
                id: `device_${this.deviceIdCounter++}`,
                type: 'device',
                deviceType: obj.deviceType,
                x: obj.x + 60,
                y: obj.y + 60,
                radius: obj.radius,
                rotation: obj.rotation || 0,
                color: obj.color,
                label: label,
                locked: false
            };
        } else if (obj.type === 'text') {
            duplicate = {
                id: `text_${this.textIdCounter++}`,
                type: 'text',
                x: obj.x + 50,
                y: obj.y + 50,
                text: obj.text,
                fontSize: obj.fontSize,
                color: obj.color,
                rotation: mirror ? (obj.rotation + 180) % 360 : obj.rotation,
                locked: false
            };
        } else {
            return; // Links can't be directly duplicated
        }
        
        this.objects.push(duplicate);
        this.selectedObject = duplicate;
        this.selectedObjects = [duplicate];
        this.draw();
    }
    
    updateDeviceRadius(radius) {
        // Store pending value, don't apply yet
        this.pendingRadius = parseInt(radius);
        const input = document.getElementById('device-radius');
        input.style.background = '#fffacd'; // Yellow background for pending
    }
    
    applyDeviceRadius() {
        if (this.selectedObject && this.selectedObject.type === 'device' && this.pendingRadius !== null) {
            // Validate max 100
            const validRadius = Math.min(100, Math.max(10, this.pendingRadius));
            this.saveState();
            this.selectedObject.radius = validRadius;
            document.getElementById('device-radius').value = validRadius;
            document.getElementById('device-radius').style.background = '';
            this.pendingRadius = null;
            this.draw();
        }
    }
    
    updateDeviceLabel(label) {
        // Store pending value, don't apply yet
        this.pendingLabel = label;
        const input = document.getElementById('device-label');
        input.style.background = '#fffacd'; // Yellow background for pending
    }
    
    applyDeviceLabel() {
        if (this.selectedObject && this.selectedObject.type === 'device' && this.pendingLabel !== null) {
            const trimmedLabel = this.pendingLabel.trim() || (this.selectedObject.deviceType === 'router' ? 'NCP' : 'S');
            
            // Validate length (max 20 characters)
            if (trimmedLabel.length > 20) {
                alert('Device label cannot exceed 20 characters');
                document.getElementById('device-label').value = this.selectedObject.label;
                document.getElementById('device-label').style.background = '';
                this.pendingLabel = null;
                return;
            }
            
            if (!this.isDeviceNameUnique(trimmedLabel) && trimmedLabel !== this.selectedObject.label) {
                alert(`Device name "${trimmedLabel}" already exists. Please choose a different name.`);
                document.getElementById('device-label').value = this.selectedObject.label;
                document.getElementById('device-label').style.background = '';
                this.pendingLabel = null;
                return;
            }
            
            this.saveState();
            this.selectedObject.label = trimmedLabel;
            document.getElementById('device-label').style.background = '';
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
        if (!textObj) textObj = this.selectedObject;
        if (!textObj || textObj.type !== 'text') return;
        
        this.editingText = textObj;
        
        document.getElementById('editor-text-content').value = textObj.text || '';
        document.getElementById('editor-font-size').value = textObj.fontSize || 14;
        document.getElementById('editor-text-color').value = textObj.color || '#333333';
        document.getElementById('editor-rotation').value = textObj.rotation || 0;
        document.getElementById('editor-rotation-value').textContent = (textObj.rotation || 0) + '°';
        document.getElementById('editor-text-align').value = textObj.textAlign || 'center';
        
        // Add live preview event listeners
        const textContent = document.getElementById('editor-text-content');
        const fontSize = document.getElementById('editor-font-size');
        const textColor = document.getElementById('editor-text-color');
        const rotation = document.getElementById('editor-rotation');
        
        // Remove old listeners
        textContent.removeEventListener('input', this.livePreviewText);
        fontSize.removeEventListener('input', this.livePreviewFontSize);
        textColor.removeEventListener('input', this.livePreviewColor);
        rotation.removeEventListener('input', this.livePreviewRotation);
        
        // Add new listeners with live preview
        this.livePreviewText = (e) => {
            if (this.editingText) {
                this.editingText.text = e.target.value;
                this.draw();
            }
        };
        this.livePreviewFontSize = (e) => {
            if (this.editingText) {
                this.editingText.fontSize = parseInt(e.target.value) || 14;
                this.draw();
            }
        };
        this.livePreviewColor = (e) => {
            if (this.editingText) {
                this.editingText.color = e.target.value;
                this.draw();
            }
        };
        this.livePreviewRotation = (e) => {
            if (this.editingText) {
                this.editingText.rotation = parseInt(e.target.value) || 0;
                this.draw();
            }
        };
        
        textContent.addEventListener('input', this.livePreviewText);
        fontSize.addEventListener('input', this.livePreviewFontSize);
        textColor.addEventListener('input', this.livePreviewColor);
        rotation.addEventListener('input', this.livePreviewRotation);
        
        const modal = document.getElementById('text-editor-modal');
        modal.classList.add('show');
    }
    
    hideTextEditor() {
        console.log('hideTextEditor() called');
        // Remove live preview listeners
        const textContent = document.getElementById('editor-text-content');
        const fontSize = document.getElementById('editor-font-size');
        const textColor = document.getElementById('editor-text-color');
        const rotation = document.getElementById('editor-rotation');
        
        if (textContent && this.livePreviewText) textContent.removeEventListener('input', this.livePreviewText);
        if (fontSize && this.livePreviewFontSize) fontSize.removeEventListener('input', this.livePreviewFontSize);
        if (textColor && this.livePreviewColor) textColor.removeEventListener('input', this.livePreviewColor);
        if (rotation && this.livePreviewRotation) rotation.removeEventListener('input', this.livePreviewRotation);
        
        const modal = document.getElementById('text-editor-modal');
        if (!modal) {
            console.error('Text editor modal element not found!');
            return;
        }
        console.log('Removing show class from text editor modal');
        modal.classList.remove('show');
        
        // CRITICAL FIX: Keep text selected and redraw to show it
        // DON'T clear editingText until after we redraw
        const textObj = this.editingText;
        this.editingText = null;
        
        // Ensure text remains selected and visible
        if (textObj) {
            this.selectedObject = textObj;
            this.selectedObjects = [textObj];
        }
        
        this.draw(); // Redraw to show the text
        console.log('Text editor modal closed successfully');
    }
    
    showLinkDetails(link) {
        if (!link || (link.type !== 'link' && link.type !== 'unbound')) return;
        
        this.editingLink = link;
        
        // Initialize link properties if they don't exist
        if (!link.device1Vlan) link.device1Vlan = '';
        if (!link.device2Vlan) link.device2Vlan = '';
        if (!link.device1Transceiver) link.device1Transceiver = '';
        if (!link.device2Transceiver) link.device2Transceiver = '';
        if (!link.device1VlanManipulation) link.device1VlanManipulation = '';
        if (!link.device1ManipValue) link.device1ManipValue = '';
        if (!link.device2VlanManipulation) link.device2VlanManipulation = '';
        if (!link.device2ManipValue) link.device2ManipValue = '';
        
        // ENHANCED: For BUL chains, get ALL devices from the entire chain
        let device1, device2;
        let linkInfo = '';
        
        // Get all connected devices across the entire BUL chain
        const connectedDevicesInfo = this.getAllConnectedDevices(link);
        
        if (connectedDevicesInfo.count === 2) {
            // Exactly 2 devices - show them as device1 and device2
            device1 = connectedDevicesInfo.devices[0];
            device2 = connectedDevicesInfo.devices[1];
            
            if (link.mergedWith || link.mergedInto) {
                linkInfo = `<strong style="color: #9b59b6;">🔗 BUL CHAIN:</strong> ${connectedDevicesInfo.links.length} link(s)`;
            }
        } else if (connectedDevicesInfo.count === 1) {
            // Only 1 device connected
            device1 = connectedDevicesInfo.devices[0];
            device2 = null;
            
            if (link.mergedWith || link.mergedInto) {
                linkInfo = `<strong style="color: #9b59b6;">🔗 BUL CHAIN:</strong> ${connectedDevicesInfo.links.length} link(s), 1 device`;
            }
        } else if (connectedDevicesInfo.count > 2) {
            // More than 2 devices - show first and last
            device1 = connectedDevicesInfo.devices[0];
            device2 = connectedDevicesInfo.devices[connectedDevicesInfo.count - 1];
            
            linkInfo = `<strong style="color: #9b59b6;">🔗 BUL CHAIN:</strong> ${connectedDevicesInfo.links.length} link(s), ${connectedDevicesInfo.count} devices`;
        } else {
            // No devices - unmerged UL with no attachments
            device1 = link.device1 ? this.objects.find(obj => obj.id === link.device1) : null;
            device2 = link.device2 ? this.objects.find(obj => obj.id === link.device2) : null;
        }
        
        // Find interface labels for this link or BUL chain
        // Check all links in the BUL chain for interface labels
        const allLinksInChain = this.getAllMergedLinks(link);
        const allLinkIds = allLinksInChain.map(l => l.id);
        
        const interfaceTexts = this.objects.filter(obj => 
            obj.type === 'text' && obj.linkId && allLinkIds.includes(obj.linkId)
        );
        
        // Find interfaces that match the actual devices we're showing
        let device1Interface = null;
        let device2Interface = null;
        
        if (device1) {
            // Find interface text attached to device1
            device1Interface = interfaceTexts.find(t => {
                if (!t.position) return false;
                // Check if this text is on a link that connects to device1
                const textLink = this.objects.find(l => l.id === t.linkId);
                if (textLink) {
                    return (textLink.device1 === device1.id && t.position.startsWith('device1')) ||
                           (textLink.device2 === device1.id && t.position.startsWith('device2'));
                }
                return false;
            });
        }
        
        if (device2) {
            // Find interface text attached to device2
            device2Interface = interfaceTexts.find(t => {
                if (!t.position) return false;
                // Check if this text is on a link that connects to device2
                const textLink = this.objects.find(l => l.id === t.linkId);
                if (textLink) {
                    return (textLink.device1 === device2.id && t.position.startsWith('device1')) ||
                           (textLink.device2 === device2.id && t.position.startsWith('device2'));
                }
                return false;
            });
        }
        
        // Populate table with editable fields
        const tableBody = document.getElementById('link-details-table');
        const device1Name = device1 ? (device1.label || 'Device 1') : 'Unbound';
        const device2Name = device2 ? (device2.label || 'Device 2') : 'Unbound';
        const device1InterfaceName = device1Interface ? device1Interface.text : '(none)';
        const device2InterfaceName = device2Interface ? device2Interface.text : '(none)';
        
        tableBody.innerHTML = `
            <tr>
                <td class="link-table-device">${device1Name}</td>
                <td class="link-table-interface ${device1Interface ? 'link-table-interface-active' : 'link-table-interface-empty'}">
                    ${device1InterfaceName}
                </td>
                <td class="link-table-input-cell">
                    <input type="text" id="link-d1-vlan" value="${link.device1Vlan || ''}" 
                           placeholder="100.200" 
                           class="link-table-input"
                           title="Enter VLAN Stack (e.g., 100.200 for double tag, 100 for single)">
                </td>
                <td class="link-table-input-cell">
                    <select id="link-d1-transceiver" class="link-table-select" title="Select transceiver type for Device 1">
                        <option value="">-- Select Transceiver --</option>
                        <optgroup label="800G Transceivers">
                            <option value="800G-OSFP-DR8">800G OSFP DR8 (500m SMF)</option>
                            <option value="800G-OSFP-SR8">800G OSFP SR8 (100m MMF)</option>
                            <option value="800G-OSFP-2FR4">800G OSFP 2FR4 (2km SMF)</option>
                            <option value="800G-QSFP-DD-DR8">800G QSFP-DD DR8 (500m SMF)</option>
                            <option value="800G-QSFP-DD-SR8">800G QSFP-DD SR8 (100m MMF)</option>
                            <option value="800G-QSFP-DD-FR8">800G QSFP-DD FR8 (2km SMF)</option>
                        </optgroup>
                        <optgroup label="400G Transceivers">
                            <option value="400G-QSFP-DD-DR4">400G QSFP-DD DR4 (500m SMF)</option>
                            <option value="400G-QSFP-DD-SR8">400G QSFP-DD SR8 (100m MMF)</option>
                            <option value="400G-QSFP-DD-FR4">400G QSFP-DD FR4 (2km SMF)</option>
                            <option value="400G-QSFP-DD-LR4">400G QSFP-DD LR4 (10km SMF)</option>
                            <option value="400G-OSFP-DR4">400G OSFP DR4 (500m SMF)</option>
                            <option value="400G-OSFP-SR8">400G OSFP SR8 (100m MMF)</option>
                        </optgroup>
                        <optgroup label="200G Transceivers">
                            <option value="200G-QSFP-DD-DR4">200G QSFP-DD DR4 (500m SMF)</option>
                            <option value="200G-QSFP-DD-SR4">200G QSFP-DD SR4 (100m MMF)</option>
                            <option value="200G-QSFP-DD-FR4">200G QSFP-DD FR4 (2km SMF)</option>
                        </optgroup>
                        <optgroup label="100G Transceivers">
                            <option value="100G-QSFP28-SR4">100G QSFP28 SR4 (100m MMF)</option>
                            <option value="100G-QSFP28-DR">100G QSFP28 DR (500m SMF)</option>
                            <option value="100G-QSFP28-FR">100G QSFP28 FR (2km SMF)</option>
                            <option value="100G-QSFP28-LR4">100G QSFP28 LR4 (10km SMF)</option>
                            <option value="100G-QSFP28-ER4">100G QSFP28 ER4 (40km SMF)</option>
                        </optgroup>
                        <optgroup label="40G/10G Transceivers">
                            <option value="40G-QSFP+-SR4">40G QSFP+ SR4 (100m MMF)</option>
                            <option value="40G-QSFP+-LR4">40G QSFP+ LR4 (10km SMF)</option>
                            <option value="10G-SFP+-SR">10G SFP+ SR (300m MMF)</option>
                            <option value="10G-SFP+-LR">10G SFP+ LR (10km SMF)</option>
                        </optgroup>
                    </select>
                </td>
                <td class="link-table-input-cell" style="background: linear-gradient(to right, rgba(255,255,255,0), rgba(22, 160, 133, 0.08));">
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                        <select id="link-d1-vlan-manipulation" class="link-table-select" title="Select VLAN manipulation for Device 1" style="font-size: 11px;">
                            <option value="">-- No Change --</option>
                            <optgroup label="🔧 DNOS Pop Operations">
                                <option value="pop">pop (Remove 1 tag)</option>
                                <option value="pop-pop">pop-pop (Remove 2 tags)</option>
                            </optgroup>
                            <optgroup label="🔄 DNOS Swap Operations">
                                <option value="swap">swap (Replace 1 tag)</option>
                                <option value="swap-swap">swap-swap (Replace 2 tags)</option>
                            </optgroup>
                            <optgroup label="➕ DNOS Push Operations">
                                <option value="push">push (Add 1 tag)</option>
                                <option value="push-push">push-push (Add 2 tags)</option>
                            </optgroup>
                            <optgroup label="🔀 Combined Operations">
                                <option value="pop-swap">pop-swap</option>
                                <option value="swap-push">swap-push</option>
                                <option value="pop-push">pop-push</option>
                            </optgroup>
                            <optgroup label="⚙️ Other">
                                <option value="transparent">transparent (No Change)</option>
                                <option value="strip-all">strip-all (Remove All Tags)</option>
                            </optgroup>
                        </select>
                        <input type="text" id="link-d1-vlan-manip-value" value="${link.device1ManipValue || ''}" 
                               placeholder="Value (e.g., 100)" 
                               class="link-table-input"
                               style="font-size: 11px; padding: 4px;"
                               title="VLAN value for manipulation (e.g., 100 or 100.200)">
                    </div>
                </td>
                <td class="link-table-input-cell" style="background: linear-gradient(to right, rgba(22, 160, 133, 0.08), rgba(230, 126, 34, 0.12));">
                    <input type="text" id="link-dnaas-vlan-ingress" value="" 
                           placeholder="(auto)" 
                           class="link-table-input"
                           style="font-size: 11px; background: rgba(230, 126, 34, 0.1); font-weight: bold; color: #d35400;"
                           title="DNaaS Ingress VLAN (Auto-calculated from Device 1 VLAN + Manipulation)"
                           readonly>
                </td>
                <td class="link-table-connector">↔</td>
                <td class="link-table-input-cell" style="background: linear-gradient(to left, rgba(22, 160, 133, 0.08), rgba(230, 126, 34, 0.12));">
                    <input type="text" id="link-dnaas-vlan-egress" value="" 
                           placeholder="(auto)" 
                           class="link-table-input"
                           style="font-size: 11px; background: rgba(230, 126, 34, 0.1); font-weight: bold; color: #d35400;"
                           title="DNaaS Egress VLAN (Auto-calculated from DNaaS Ingress + Device 2 Manipulation)"
                           readonly>
                </td>
                <td class="link-table-input-cell" style="background: linear-gradient(to left, rgba(255,255,255,0), rgba(22, 160, 133, 0.08));">
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                        <select id="link-d2-vlan-manipulation" class="link-table-select" title="Select VLAN manipulation for Device 2" style="font-size: 11px;">
                            <option value="">-- No Change --</option>
                            <optgroup label="🔧 DNOS Pop Operations">
                                <option value="pop">pop (Remove 1 tag)</option>
                                <option value="pop-pop">pop-pop (Remove 2 tags)</option>
                            </optgroup>
                            <optgroup label="🔄 DNOS Swap Operations">
                                <option value="swap">swap (Replace 1 tag)</option>
                                <option value="swap-swap">swap-swap (Replace 2 tags)</option>
                            </optgroup>
                            <optgroup label="➕ DNOS Push Operations">
                                <option value="push">push (Add 1 tag)</option>
                                <option value="push-push">push-push (Add 2 tags)</option>
                            </optgroup>
                            <optgroup label="🔀 Combined Operations">
                                <option value="pop-swap">pop-swap</option>
                                <option value="swap-push">swap-push</option>
                                <option value="pop-push">pop-push</option>
                            </optgroup>
                            <optgroup label="⚙️ Other">
                                <option value="transparent">transparent (No Change)</option>
                                <option value="strip-all">strip-all (Remove All Tags)</option>
                            </optgroup>
                        </select>
                        <input type="text" id="link-d2-vlan-manip-value" value="${link.device2ManipValue || ''}" 
                               placeholder="Value (e.g., 100)" 
                               class="link-table-input"
                               style="font-size: 11px; padding: 4px;"
                               title="VLAN value for manipulation (e.g., 100 or 100.200)">
                    </div>
                </td>
                <td class="link-table-input-cell">
                    <select id="link-d2-transceiver" class="link-table-select" title="Select transceiver type for Device 2">
                        <option value="">-- Select Transceiver --</option>
                        <optgroup label="800G Transceivers">
                            <option value="800G-OSFP-DR8">800G OSFP DR8 (500m SMF)</option>
                            <option value="800G-OSFP-SR8">800G OSFP SR8 (100m MMF)</option>
                            <option value="800G-OSFP-2FR4">800G OSFP 2FR4 (2km SMF)</option>
                            <option value="800G-QSFP-DD-DR8">800G QSFP-DD DR8 (500m SMF)</option>
                            <option value="800G-QSFP-DD-SR8">800G QSFP-DD SR8 (100m MMF)</option>
                            <option value="800G-QSFP-DD-FR8">800G QSFP-DD FR8 (2km SMF)</option>
                        </optgroup>
                        <optgroup label="400G Transceivers">
                            <option value="400G-QSFP-DD-DR4">400G QSFP-DD DR4 (500m SMF)</option>
                            <option value="400G-QSFP-DD-SR8">400G QSFP-DD SR8 (100m MMF)</option>
                            <option value="400G-QSFP-DD-FR4">400G QSFP-DD FR4 (2km SMF)</option>
                            <option value="400G-QSFP-DD-LR4">400G QSFP-DD LR4 (10km SMF)</option>
                            <option value="400G-OSFP-DR4">400G OSFP DR4 (500m SMF)</option>
                            <option value="400G-OSFP-SR8">400G OSFP SR8 (100m MMF)</option>
                        </optgroup>
                        <optgroup label="200G Transceivers">
                            <option value="200G-QSFP-DD-DR4">200G QSFP-DD DR4 (500m SMF)</option>
                            <option value="200G-QSFP-DD-SR4">200G QSFP-DD SR4 (100m MMF)</option>
                            <option value="200G-QSFP-DD-FR4">200G QSFP-DD FR4 (2km SMF)</option>
                        </optgroup>
                        <optgroup label="100G Transceivers">
                            <option value="100G-QSFP28-SR4">100G QSFP28 SR4 (100m MMF)</option>
                            <option value="100G-QSFP28-DR">100G QSFP28 DR (500m SMF)</option>
                            <option value="100G-QSFP28-FR">100G QSFP28 FR (2km SMF)</option>
                            <option value="100G-QSFP28-LR4">100G QSFP28 LR4 (10km SMF)</option>
                            <option value="100G-QSFP28-ER4">100G QSFP28 ER4 (40km SMF)</option>
                        </optgroup>
                        <optgroup label="40G/10G Transceivers">
                            <option value="40G-QSFP+-SR4">40G QSFP+ SR4 (100m MMF)</option>
                            <option value="40G-QSFP+-LR4">40G QSFP+ LR4 (10km SMF)</option>
                            <option value="10G-SFP+-SR">10G SFP+ SR (300m MMF)</option>
                            <option value="10G-SFP+-LR">10G SFP+ LR (10km SMF)</option>
                        </optgroup>
                    </select>
                </td>
                <td class="link-table-input-cell">
                    <input type="text" id="link-d2-vlan" value="${link.device2Vlan || ''}" 
                           placeholder="100.200" 
                           class="link-table-input"
                           title="Enter VLAN Stack (e.g., 100.200 for double tag, 100 for single)">
                </td>
                <td class="link-table-interface ${device2Interface ? 'link-table-interface-active' : 'link-table-interface-empty'}">
                    ${device2InterfaceName}
                </td>
                <td class="link-table-device">${device2Name}</td>
            </tr>
            <tr class="link-info-row">
                <td colspan="13" class="link-info-cell">
                    ${linkInfo ? '<div class="link-info-section">' + linkInfo + '</div>' : ''}
                    <div class="link-info-section">
                        <span class="link-info-label">Link ID:</span><span class="link-info-value">${link.id}</span><br>
                        <span class="link-info-label">Curve Mode:</span><span class="link-info-value">${link.curveOverride !== undefined ? (link.curveOverride ? 'Enabled (Override)' : 'Disabled (Override)') : 'Global (' + (this.linkCurveMode ? 'ON' : 'OFF') + ')'}</span><br>
                        <span class="link-info-label">Link Position:</span><span class="link-info-value">${link.linkIndex === 0 ? 'Center' : (link.linkIndex || 0) % 2 === 1 ? 'Bottom' : 'Top'} (Index: ${link.linkIndex || 0})</span>
                    </div>
                    ${(() => {
                        const connectedInfo = this.getAllConnectedDevices(link);
                        const allLinks = this.getAllMergedLinks(link);
                        const isBUL = allLinks.length > 1;
                        
                        if (isBUL) {
                            // ENHANCED: Comprehensive BUL information
                            const mpCount = allLinks.length - 1; // N links create N-1 MPs
                            const tpCount = 2; // Always 2 TPs at BUL ends
                            
                            // Build BUL chain visualization
                            let bulStructure = '';
                            const sortedLinks = allLinks.sort((a, b) => (a.createdAt || 0) - (b.createdAt || 0));
                            
                            // Find endpoint devices
                            let leftDevice = null;
                            let rightDevice = null;
                            
                            // Check first link for left device
                            const firstLink = sortedLinks[0];
                            if (firstLink.mergedWith) {
                                const parentFreeEnd = firstLink.mergedWith.parentFreeEnd;
                                if (parentFreeEnd === 'start' && firstLink.device1) {
                                    leftDevice = this.objects.find(d => d.id === firstLink.device1);
                                } else if (parentFreeEnd === 'end' && firstLink.device2) {
                                    leftDevice = this.objects.find(d => d.id === firstLink.device2);
                                }
                            } else if (firstLink.mergedInto) {
                                // This is a child, find parent
                                const parent = this.objects.find(l => l.id === firstLink.mergedInto.parentId);
                                if (parent && parent.mergedWith) {
                                    const childFreeEnd = parent.mergedWith.childFreeEnd;
                                    if (childFreeEnd === 'start' && firstLink.device1) {
                                        leftDevice = this.objects.find(d => d.id === firstLink.device1);
                                    } else if (childFreeEnd === 'end' && firstLink.device2) {
                                        leftDevice = this.objects.find(d => d.id === firstLink.device2);
                                    }
                                }
                            } else {
                                // Standalone link
                                if (firstLink.device1) leftDevice = this.objects.find(d => d.id === firstLink.device1);
                                if (firstLink.device2 && !leftDevice) leftDevice = this.objects.find(d => d.id === firstLink.device2);
                            }
                            
                            // Check last link for right device
                            const lastLink = sortedLinks[sortedLinks.length - 1];
                            if (lastLink.mergedWith) {
                                const parentFreeEnd = lastLink.mergedWith.parentFreeEnd;
                                if (parentFreeEnd === 'end' && lastLink.device2) {
                                    rightDevice = this.objects.find(d => d.id === lastLink.device2);
                                } else if (parentFreeEnd === 'start' && lastLink.device1) {
                                    rightDevice = this.objects.find(d => d.id === lastLink.device1);
                                }
                            } else if (lastLink.mergedInto) {
                                // This is a child, check its free end
                                const parent = this.objects.find(l => l.id === lastLink.mergedInto.parentId);
                                if (parent && parent.mergedWith) {
                                    const childFreeEnd = parent.mergedWith.childFreeEnd;
                                    if (childFreeEnd === 'end' && lastLink.device2) {
                                        rightDevice = this.objects.find(d => d.id === lastLink.device2);
                                    } else if (childFreeEnd === 'start' && lastLink.device1) {
                                        rightDevice = this.objects.find(d => d.id === lastLink.device1);
                                    }
                                }
                            } else {
                                if (lastLink.device2) rightDevice = this.objects.find(d => d.id === lastLink.device2);
                                if (lastLink.device1 && !rightDevice) rightDevice = this.objects.find(d => d.id === lastLink.device1);
                            }
                            
                            // Build structure string
                            const leftLabel = leftDevice ? (leftDevice.label || leftDevice.id) : 'TP';
                            const rightLabel = rightDevice ? (rightDevice.label || rightDevice.id) : 'TP';
                            
                            // Build chain visualization: Device/TP -- UL -- MP -- UL -- MP -- UL -- Device/TP
                            bulStructure = leftDevice ? 
                                '<span style="color: #27ae60; font-weight: bold;">🟢 ' + leftLabel + '</span>' : 
                                '<span style="color: #666; font-weight: bold;">⚪ Free TP</span>';
                            
                            for (let i = 0; i < sortedLinks.length; i++) {
                                const linkType = sortedLinks[i].originType || 'UL';
                                bulStructure += ' ━━ <span style="color: #3498db;">' + linkType + (i+1) + '</span> ━━';
                                
                                if (i < sortedLinks.length - 1) {
                                    bulStructure += ' <span style="color: #9b59b6; font-weight: bold;">🟣 MP</span> ━━';
                                }
                            }
                            
                            bulStructure += rightDevice ? 
                                ' <span style="color: #27ae60; font-weight: bold;">🟢 ' + rightLabel + '</span>' : 
                                ' <span style="color: #666; font-weight: bold;">⚪ Free TP</span>';
                            
                            return '<div class="bul-structure-card">' +
                                    '<div class="bul-structure-title">🔗 BUL STRUCTURE</div>' +
                                    '<div class="bul-structure-info">' +
                                        '<span class="link-info-label">Chain Length:</span> ' + allLinks.length + ' UL(s) • ' + mpCount + ' MP(s) • ' + tpCount + ' TP(s)<br>' +
                                        '<span class="link-info-label">Endpoints:</span> ' + (connectedInfo.count > 0 ? connectedInfo.count + ' device(s) connected' : 'All TPs free') +
                                        '<div class="bul-structure-chain">' +
                                            bulStructure +
                                        '</div>' +
                                    '</div>' +
                                '</div>';
                        } else if (connectedInfo.count > 0) {
                            const deviceLabels = connectedInfo.devices.map(d => d.label || d.id).join(' ↔ ');
                            return '<div class="connected-devices-badge">📍 Connected: ' + deviceLabels + '</div>';
                        }
                        return '';
                    })()}
                </td>
            </tr>
        `;
        
        const modal = document.getElementById('link-details-modal');
        modal.classList.add('show');
        
        // Set selected transceiver and manipulation values after modal is displayed
        setTimeout(() => {
            const d1Select = document.getElementById('link-d1-transceiver');
            const d2Select = document.getElementById('link-d2-transceiver');
            const d1ManipSelect = document.getElementById('link-d1-vlan-manipulation');
            const d2ManipSelect = document.getElementById('link-d2-vlan-manipulation');
            
            if (d1Select && link.device1Transceiver) {
                d1Select.value = link.device1Transceiver;
            }
            if (d2Select && link.device2Transceiver) {
                d2Select.value = link.device2Transceiver;
            }
            if (d1ManipSelect && link.device1VlanManipulation) {
                d1ManipSelect.value = link.device1VlanManipulation;
            }
            if (d2ManipSelect && link.device2VlanManipulation) {
                d2ManipSelect.value = link.device2VlanManipulation;
            }
            
            // Attach event listeners for real-time VLAN calculation
            this.setupVlanCalculationListeners();
            
            // Initial calculation
            this.updateDnaasVlanFields();
        }, 10);
    }
    
    saveLinkDetails() {
        if (!this.editingLink) return;
        
        this.saveState(); // Save for undo
        
        // Get values from input fields
        const d1Vlan = document.getElementById('link-d1-vlan').value.trim();
        const d2Vlan = document.getElementById('link-d2-vlan').value.trim();
        const d1Transceiver = document.getElementById('link-d1-transceiver').value.trim();
        const d2Transceiver = document.getElementById('link-d2-transceiver').value.trim();
        const d1VlanManip = document.getElementById('link-d1-vlan-manipulation').value.trim();
        const d1ManipValue = document.getElementById('link-d1-vlan-manip-value').value.trim();
        const d2VlanManip = document.getElementById('link-d2-vlan-manipulation').value.trim();
        const d2ManipValue = document.getElementById('link-d2-vlan-manip-value').value.trim();
        
        // Update link properties
        this.editingLink.device1Vlan = d1Vlan;
        this.editingLink.device2Vlan = d2Vlan;
        this.editingLink.device1Transceiver = d1Transceiver;
        this.editingLink.device2Transceiver = d2Transceiver;
        this.editingLink.device1VlanManipulation = d1VlanManip;
        this.editingLink.device1ManipValue = d1ManipValue;
        this.editingLink.device2VlanManipulation = d2VlanManip;
        this.editingLink.device2ManipValue = d2ManipValue;
        
        this.draw();
        alert('Link details saved successfully!');
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
    
    setupVlanCalculationListeners() {
        // Get all input fields
        const d1VlanInput = document.getElementById('link-d1-vlan');
        const d1ManipSelect = document.getElementById('link-d1-vlan-manipulation');
        const d1ManipValueInput = document.getElementById('link-d1-vlan-manip-value');
        const d2ManipSelect = document.getElementById('link-d2-vlan-manipulation');
        const d2ManipValueInput = document.getElementById('link-d2-vlan-manip-value');
        
        // Attach listeners to all relevant fields
        const updateFn = () => this.updateDnaasVlanFields();
        
        if (d1VlanInput) d1VlanInput.addEventListener('input', updateFn);
        if (d1ManipSelect) d1ManipSelect.addEventListener('change', updateFn);
        if (d1ManipValueInput) d1ManipValueInput.addEventListener('input', updateFn);
        if (d2ManipSelect) d2ManipSelect.addEventListener('change', updateFn);
        if (d2ManipValueInput) d2ManipValueInput.addEventListener('input', updateFn);
    }
    
    updateDnaasVlanFields() {
        // Get input values
        const d1VlanInput = document.getElementById('link-d1-vlan');
        const d1ManipSelect = document.getElementById('link-d1-vlan-manipulation');
        const d1ManipValueInput = document.getElementById('link-d1-vlan-manip-value');
        const d2ManipSelect = document.getElementById('link-d2-vlan-manipulation');
        const d2ManipValueInput = document.getElementById('link-d2-vlan-manip-value');
        const ingressField = document.getElementById('link-dnaas-vlan-ingress');
        const egressField = document.getElementById('link-dnaas-vlan-egress');
        
        if (!d1VlanInput || !ingressField || !egressField) return;
        
        // Parse Device 1 VLAN (format: "100" or "100.200")
        const d1VlanValue = d1VlanInput.value.trim();
        let d1Outer = null;
        let d1Inner = null;
        
        if (d1VlanValue) {
            if (d1VlanValue.includes('.')) {
                const parts = d1VlanValue.split('.');
                d1Outer = parts[0] || null;
                d1Inner = parts[1] || null;
            } else {
                d1Outer = d1VlanValue;
            }
        }
        
        // Calculate DNaaS Ingress (Device 1 → DNaaS)
        const d1Manipulation = d1ManipSelect ? d1ManipSelect.value : '';
        const d1ManipValue = d1ManipValueInput ? d1ManipValueInput.value.trim() : '';
        const ingressVlan = this.applyVlanManipulation(d1Outer, d1Inner, d1Manipulation, d1ManipValue);
        ingressField.value = ingressVlan;
        
        // Parse ingress VLAN for Device 2 calculation
        let ingressOuter = null;
        let ingressInner = null;
        
        if (ingressVlan && ingressVlan !== '(empty)') {
            if (ingressVlan.includes('.')) {
                const parts = ingressVlan.split('.');
                ingressOuter = parts[0] || null;
                ingressInner = parts[1] || null;
            } else {
                ingressOuter = ingressVlan;
            }
        }
        
        // Calculate DNaaS Egress (DNaaS → Device 2)
        const d2Manipulation = d2ManipSelect ? d2ManipSelect.value : '';
        const d2ManipValue = d2ManipValueInput ? d2ManipValueInput.value.trim() : '';
        const egressVlan = this.applyVlanManipulation(ingressOuter, ingressInner, d2Manipulation, d2ManipValue);
        egressField.value = egressVlan;
    }
    
    hideLinkDetails() {
        console.log('hideLinkDetails() called');
        const modal = document.getElementById('link-details-modal');
        if (!modal) {
            console.error('Link details modal element not found!');
            return;
        }
        console.log('Removing show class from link details modal');
        modal.classList.remove('show');
        this.editingLink = null;
        console.log('Link details modal closed successfully');
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
        if (this.selectedObject && this.selectedObject.type === 'device') {
            document.getElementById('device-radius').value = this.selectedObject.radius;
            document.getElementById('device-label').value = this.selectedObject.label || (this.selectedObject.deviceType === 'router' ? 'NCP' : 'S');
            document.getElementById('device-props').style.display = 'block';
            document.getElementById('device-label-props').style.display = 'block';
        } else {
            document.getElementById('device-props').style.display = 'none';
            document.getElementById('device-label-props').style.display = 'none';
        }
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
        }
        
        // Update all button states
        document.getElementById('btn-base').classList.remove('active');
        document.getElementById('btn-select').classList.remove('active');
        document.getElementById('btn-link').classList.remove('active');
        document.getElementById('btn-text').classList.remove('active');
        document.getElementById('btn-router').classList.remove('active');
        document.getElementById('btn-switch').classList.remove('active');
        
        if (mode !== 'base') {
            document.getElementById(`btn-${mode}`).classList.add('active');
        } else {
            document.getElementById('btn-base').classList.add('active');
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
            modeIndicator.style.background = '#9b59b6'; // Purple
            modeIndicator.style.color = 'white';
            modeIndicator.style.borderLeft = '4px solid #8e44ad';
        } else if (this.currentMode === 'link') {
            modeText.textContent = 'LINK MODE';
            modeIndicator.style.background = '#e67e22'; // Orange
            modeIndicator.style.color = 'white';
            modeIndicator.style.borderLeft = '4px solid #d35400';
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
            document.getElementById('device-props').style.display = 'none';
            document.getElementById('device-label-props').style.display = 'none';
            document.getElementById('text-props').style.display = 'none';
            document.getElementById('text-rotation-props').style.display = 'none';
            return;
        }
        
        // Show appropriate properties in Select mode
        this.updateDeviceProperties();
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
            document.getElementById('font-size').value = sizeMap[currentIndex];
            this.draw();
        }
    }
    
    showContextMenu(x, y, obj) {
        const menu = document.getElementById('context-menu');
        menu.style.display = 'block';
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
        this.contextMenuVisible = true;
        
        // Hide background-specific items
        const baseModeItem = document.getElementById('ctx-base-mode');
        if (baseModeItem) baseModeItem.style.display = 'none';
        
        // Show/hide items based on object type
        const addTextItem = document.getElementById('ctx-add-text');
        const changeLabelItem = document.getElementById('ctx-change-label');
        const toggleCurveItem = document.getElementById('ctx-toggle-curve');
        
        // Lock/Unlock options
        const lockItem = document.getElementById('ctx-lock');
        const unlockItem = document.getElementById('ctx-unlock');
        
        if (obj.type === 'link' || obj.type === 'unbound') {
            addTextItem.style.display = 'block';
            changeLabelItem.style.display = 'none';
            toggleCurveItem.style.display = 'block';
            lockItem.style.display = 'none';
            unlockItem.style.display = 'none';
            // Update text to show current state
            const curveEnabled = obj.curveOverride !== undefined ? obj.curveOverride : this.linkCurveMode;
            toggleCurveItem.textContent = curveEnabled ? '✓ Curve Enabled (This Link)' : '✗ Curve Disabled (This Link)';
        } else if (obj.type === 'device' || obj.type === 'text') {
            addTextItem.style.display = obj.type === 'device' ? 'block' : 'none';
            changeLabelItem.style.display = obj.type === 'device' ? 'block' : 'none';
            toggleCurveItem.style.display = 'none';
            // Show lock or unlock based on current state
            if (obj.locked) {
                lockItem.style.display = 'none';
                unlockItem.style.display = 'block';
            } else {
                lockItem.style.display = 'block';
                unlockItem.style.display = 'none';
            }
        }
    }
    
    hideContextMenu() {
        const menu = document.getElementById('context-menu');
        menu.style.display = 'none';
        this.contextMenuVisible = false;
    }
    
    handleContextDuplicate() {
        if (this.selectedObject) {
            this.duplicateObject(this.selectedObject, false);
        }
        this.hideContextMenu();
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
            
            this.draw();
        } else if (this.selectedObject && (this.selectedObject.type === 'link' || this.selectedObject.type === 'unbound')) {
            // Single link toggle
            this.saveState();
            if (this.magneticFieldStrength === 0) {
                // Can't enable curves when magnetic field is 0
                return;
            }
            if (this.selectedObject.curveOverride === undefined) {
                // No override set, use opposite of global
                this.selectedObject.curveOverride = !this.linkCurveMode;
            } else {
                // Toggle the override
                this.selectedObject.curveOverride = !this.selectedObject.curveOverride;
            }
            this.draw();
        }
        this.hideContextMenu();
    }
    
    showAdjacentTextMenu(link) {
        const device1 = link.device1 ? this.objects.find(obj => obj.id === link.device1) : null;
        const device2 = link.device2 ? this.objects.find(obj => obj.id === link.device2) : null;
        
        if (!device1 && !device2) {
            // Unbound link - just add text in middle
            const text = prompt('Enter text label:', 'Label');
            if (text !== null && text.trim() !== '') {
                this.addAdjacentText(link, 'middle', text.trim());
            }
            return;
        }
        
        // Check existing texts for this link
        const existingTexts = this.objects.filter(obj => 
            obj.type === 'text' && obj.linkId === link.id
        );
        const existingPositions = existingTexts.map(t => t.position);
        
        // Get mouse position for menu placement
        const mouseX = event.clientX || window.innerWidth / 2;
        const mouseY = event.clientY || window.innerHeight / 2;
        
        // Create styled menu dynamically
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.id = 'adjacent-text-menu';
        menu.style.display = 'block';
        menu.style.position = 'fixed';
        menu.style.left = mouseX + 'px';
        menu.style.top = mouseY + 'px';
        menu.style.zIndex = '10001';
        menu.style.minWidth = '200px';
        
        const device1Name = device1 ? (device1.label || 'Device 1') : 'Start';
        const device2Name = device2 ? (device2.label || 'Device 2') : 'End';
        
        // Check if positions already exist (simplified to 2 per link)
        const hasDevice1 = existingPositions.some(p => p && p.startsWith('device1'));
        const hasDevice2 = existingPositions.some(p => p && p.startsWith('device2'));
        
        menu.innerHTML = `
            <div style="padding: 10px 16px; font-weight: bold; border-bottom: 2px solid #3498db; color: #2c3e50; background: #ecf0f1;">
                📝 Add Interface Label
            </div>
            <div class="context-menu-item ${hasDevice1 ? 'disabled' : ''}" data-position="device1" style="${hasDevice1 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                📍 Near ${device1Name} ${hasDevice1 ? '✓' : ''}
            </div>
            ${device2 ? `
            <div class="context-menu-item ${hasDevice2 ? 'disabled' : ''}" data-position="device2" style="${hasDevice2 ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                📍 Near ${device2Name} ${hasDevice2 ? '✓' : ''}
            </div>
            ` : ''}
        `;
        
        document.body.appendChild(menu);
        
        // Add click handlers
        menu.querySelectorAll('.context-menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const position = e.target.getAttribute('data-position');
                if (position && !e.target.textContent.includes('✓')) {
                    // Prompt for text input
                    const deviceName = position === 'device1' ? device1Name : device2Name;
                    const text = prompt(`Enter label near ${deviceName}:`, '');
                    if (text !== null && text.trim() !== '') {
                        this.addAdjacentText(link, position, text.trim());
                        if (document.body.contains(menu)) {
                            document.body.removeChild(menu);
                        }
                        this.draw();
                    }
                }
            });
        });
        
        // Close menu on outside click
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!menu.contains(e.target)) {
                    if (document.body.contains(menu)) {
                        document.body.removeChild(menu);
                    }
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 100);
    }
    
    updateAdjacentTextPosition(textObj) {
        // Find the linked link
        const link = this.objects.find(obj => obj.id === textObj.linkId);
        if (!link) return;
        
        // Calculate current link positions (they should already be updated)
        let linkStart = link.start;
        let linkEnd = link.end;
        
        // For device links, recalculate positions if needed
        if (link.type === 'link' && link.device1 && link.device2) {
            const device1 = this.objects.find(o => o.id === link.device1);
            const device2 = this.objects.find(o => o.id === link.device2);
            if (device1 && device2) {
                const angle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
                linkStart = {
                    x: device1.x + Math.cos(angle) * device1.radius,
                    y: device1.y + Math.sin(angle) * device1.radius
                };
                linkEnd = {
                    x: device2.x - Math.cos(angle) * device2.radius,
                    y: device2.y - Math.sin(angle) * device2.radius
                };
            }
        }
        
        // Calculate link angle
        const angle = Math.atan2(linkEnd.y - linkStart.y, linkEnd.x - linkStart.x);
        
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
        
        // Calculate perpendicular with normalized direction
        let perpAngle = angle + Math.PI / 2;
        if (!isNormalDirection) {
            perpAngle += Math.PI; // Flip to match drawLink
        }
        
        // Base offset for text from link (perpendicular distance)
        const baseTextOffset = 12;
        
        // Auto-determine side based on link offset direction
        const autoSide = linkDirection >= 0 ? -1 : 1;
        
        // Determine position based on stored position value
        let textX, textY;
        
        if (textObj.position === 'device1-top' || textObj.position === 'device1-bottom') {
            // Legacy position with explicit top/bottom
            const side = textObj.position.includes('top') ? -1 : 1;
            const posAlongLink = 0.15;
            const alongX = linkStart.x + (linkEnd.x - linkStart.x) * posAlongLink;
            const alongY = linkStart.y + (linkEnd.y - linkStart.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * side);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else if (textObj.position === 'device2-top' || textObj.position === 'device2-bottom') {
            // Legacy position with explicit top/bottom
            const side = textObj.position.includes('top') ? -1 : 1;
            const posAlongLink = 0.85;
            const alongX = linkStart.x + (linkEnd.x - linkStart.x) * posAlongLink;
            const alongY = linkStart.y + (linkEnd.y - linkStart.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * side);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else if (textObj.position === 'device1') {
            // Simplified position - auto-determine side
            const posAlongLink = 0.15;
            const alongX = linkStart.x + (linkEnd.x - linkStart.x) * posAlongLink;
            const alongY = linkStart.y + (linkEnd.y - linkStart.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else if (textObj.position === 'device2') {
            // Simplified position - auto-determine side
            const posAlongLink = 0.85;
            const alongX = linkStart.x + (linkEnd.x - linkStart.x) * posAlongLink;
            const alongY = linkStart.y + (linkEnd.y - linkStart.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else {
            // Middle (default for unbound links)
            const midX = (linkStart.x + linkEnd.x) / 2;
            const midY = (linkStart.y + linkEnd.y) / 2;
            const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
            textX = midX + Math.cos(perpAngle) * totalOffset;
            textY = midY + Math.sin(perpAngle) * totalOffset;
        }
        
        // Update text position and rotation
        textObj.x = textX;
        textObj.y = textY;
        
        // Rotate text with link and flip when upside down
        let rotationDegrees = angle * 180 / Math.PI;
        
        // Normalize angle to -180 to 180 range
        while (rotationDegrees > 180) rotationDegrees -= 360;
        while (rotationDegrees < -180) rotationDegrees += 360;
        
        // Flip text if it's upside down (angle between 90° and 270°)
        if (rotationDegrees > 90 || rotationDegrees < -90) {
            rotationDegrees += 180; // Flip 180 degrees
            // Normalize again after flip
            while (rotationDegrees > 180) rotationDegrees -= 360;
            while (rotationDegrees < -180) rotationDegrees += 360;
        }
        
        textObj.rotation = rotationDegrees;
    }
    
    addAdjacentText(link, position = 'middle', textContent = 'Label') {
        this.saveState(); // Save before adding text
        const device1 = link.device1 ? this.objects.find(obj => obj.id === link.device1) : null;
        const device2 = link.device2 ? this.objects.find(obj => obj.id === link.device2) : null;
        
        // Calculate link angle
        const angle = Math.atan2(link.end.y - link.start.y, link.end.x - link.start.x);
        
        // NORMALIZE perpendicular direction (match drawLink and updateAdjacentTextPosition)
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
        
        // Calculate perpendicular with normalized direction
        let perpAngle = angle + Math.PI / 2;
        if (!isNormalDirection) {
            perpAngle += Math.PI; // Flip to match drawLink
        }
        
        // Base offset for text from link (perpendicular distance)
        const baseTextOffset = 12;
        
        // Auto-determine side based on link offset direction
        // If link is offset upward (direction = 1), place text above
        // If link is offset downward (direction = -1), place text below
        // If link is centered (direction = 0), place text above by default
        const autoSide = linkDirection >= 0 ? -1 : 1;
        
        // Determine position based on selection
        let textX, textY;
        
        // Handle legacy positions with explicit top/bottom
        if (position === 'device1-top' || position === 'device1-bottom') {
            const side = position.includes('top') ? -1 : 1;
            const posAlongLink = 0.15;
            const alongX = link.start.x + (link.end.x - link.start.x) * posAlongLink;
            const alongY = link.start.y + (link.end.y - link.start.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * side);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else if (position === 'device2-top' || position === 'device2-bottom') {
            const side = position.includes('top') ? -1 : 1;
            const posAlongLink = 0.85;
            const alongX = link.start.x + (link.end.x - link.start.x) * posAlongLink;
            const alongY = link.start.y + (link.end.y - link.start.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * side);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else if (position === 'device1') {
            // Simplified position - auto-determine side
            const posAlongLink = 0.15;
            const alongX = link.start.x + (link.end.x - link.start.x) * posAlongLink;
            const alongY = link.start.y + (link.end.y - link.start.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else if (position === 'device2') {
            // Simplified position - auto-determine side
            const posAlongLink = 0.85;
            const alongX = link.start.x + (link.end.x - link.start.x) * posAlongLink;
            const alongY = link.start.y + (link.end.y - link.start.y) * posAlongLink;
            const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
            textX = alongX + Math.cos(perpAngle) * totalOffset;
            textY = alongY + Math.sin(perpAngle) * totalOffset;
        } else {
            // Middle (default for unbound links)
            const midX = (link.start.x + link.end.x) / 2;
            const midY = (link.start.y + link.end.y) / 2;
            const totalOffset = linkOffsetAmount + (baseTextOffset * autoSide);
            textX = midX + Math.cos(perpAngle) * totalOffset;
            textY = midY + Math.sin(perpAngle) * totalOffset;
        }
        
        // Calculate link length for text size
        const linkLength = Math.sqrt(Math.pow(link.end.x - link.start.x, 2) + Math.pow(link.end.y - link.start.y, 2));
        // Smaller text size - about 1/5 of link length or smaller
        const textSize = Math.max(8, Math.min(16, linkLength / 5));
        
        // Calculate rotation with flip for upside-down text
        let rotationDegrees = angle * 180 / Math.PI;
        while (rotationDegrees > 180) rotationDegrees -= 360;
        while (rotationDegrees < -180) rotationDegrees += 360;
        if (rotationDegrees > 90 || rotationDegrees < -90) {
            rotationDegrees += 180;
            while (rotationDegrees > 180) rotationDegrees -= 360;
            while (rotationDegrees < -180) rotationDegrees += 360;
        }
        
        const text = {
            id: `text_${this.textIdCounter++}`,
            type: 'text',
            x: textX,
            y: textY,
            text: textContent,
            fontSize: Math.round(textSize),
            color: '#333',
            rotation: rotationDegrees,
            linkId: link.id, // Track which link this text belongs to
            position: position // Track position for this link
        };
        
        this.objects.push(text);
        this.selectedObject = text;
        this.selectedObjects = [text];
        this.updateTextProperties();
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
        // Show color picker for selected object(s)
        this.hideContextMenu();
        
        if (this.selectedObject && (this.selectedObject.type === 'device' || this.selectedObject.type === 'text')) {
            // Use the properties panel color picker
            const colorPicker = document.getElementById('color-picker');
            if (colorPicker) {
                colorPicker.value = this.selectedObject.color || '#3498db';
                colorPicker.click();
                
                // Add one-time event listener to apply color
                const applyColor = (e) => {
                this.saveState();
                    const newColor = e.target.value;
                    if (this.selectedObjects.length > 0) {
                this.selectedObjects.forEach(obj => {
                    if (obj.type !== 'link' && obj.type !== 'unbound') {
                                obj.color = newColor;
                    }
                });
                    } else if (this.selectedObject) {
                        this.selectedObject.color = newColor;
                    }
                    this.updatePropertiesPanel();
                this.draw();
                    colorPicker.removeEventListener('input', applyColor);
                };
                colorPicker.addEventListener('input', applyColor);
            }
        }
    }
    
    handleContextSize() {
        if (this.selectedObject) {
            if (this.selectedObject.type === 'device') {
                document.getElementById('device-radius').focus();
            } else if (this.selectedObject.type === 'text') {
                document.getElementById('font-size').focus();
            }
        }
        this.hideContextMenu();
    }
    
    handleContextLabel() {
        // Ensure device is selected and properties panel is visible
        if (this.selectedObject && this.selectedObject.type === 'device') {
            // Make sure device is in select mode
            this.currentMode = 'select';
            this.updateModeIndicator();
            // Update properties panel to show label input
            this.updateDeviceProperties();
            // Focus the label input field
            const labelInput = document.getElementById('device-label');
            if (labelInput) {
                labelInput.focus();
                labelInput.select(); // Select all text for easy editing
            }
        }
        this.hideContextMenu();
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
            this.draw();
        } else if (this.selectedObject && (this.selectedObject.type === 'device' || this.selectedObject.type === 'text')) {
            this.saveState();
            this.selectedObject.locked = true;
            this.draw();
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
            this.draw();
        } else if (this.selectedObject && (this.selectedObject.type === 'device' || this.selectedObject.type === 'text')) {
            this.saveState();
            this.selectedObject.locked = false;
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
        const centerX = (this.canvas.width / 2) / this.zoom - this.panOffset.x;
        const centerY = (this.canvas.height / 2) / this.zoom - this.panOffset.y;
        
        const label = this.getNextDeviceLabel(type);
        
        // Validate device name uniqueness
        if (!this.isDeviceNameUnique(label)) {
            alert(`Device name "${label}" already exists. Please choose a different name.`);
            return;
        }
        
        this.saveState(); // Save before adding
        
        const device = {
            id: `device_${this.deviceIdCounter++}`,
            type: 'device',
            deviceType: type,
            x: centerX,
            y: centerY,
            radius: 30,
            rotation: 0,
            color: document.getElementById('color-picker').value,
            label: label,
            locked: false
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
        
        // Calculate device edge positions for initial TP placement
        const angle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
        const startX = device1.x + Math.cos(angle) * device1.radius;
        const startY = device1.y + Math.sin(angle) * device1.radius;
        const endX = device2.x - Math.cos(angle) * device2.radius;
        const endY = device2.y - Math.sin(angle) * device2.radius;
        
        const link = {
            id: `link_${this.linkIdCounter++}`,
            type: 'link',  // Reverted to 'link' type for proper offset logic
            originType: 'QL', // PRESERVE: Original link type (QL = Quick Link)
            createdAt: Date.now(), // Creation timestamp for BUL order tracking
            device1: device1.id,
            device2: device2.id,
            color: '#666',
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
        const centerX = (this.canvas.width / 2) / this.zoom - this.panOffset.x;
        const centerY = (this.canvas.height / 2) / this.zoom - this.panOffset.y;
        
        // Count existing unbound links to stack them vertically (avoid overlap)
        const unboundCount = this.objects.filter(obj => obj.type === 'unbound').length;
        const verticalOffset = unboundCount * 40; // 40px spacing between unbound links
        
        const link = {
            id: `link_${this.linkIdCounter++}`,
            type: 'unbound',
            originType: 'UL', // PRESERVE: Original link type (UL = Unbound Link)
            createdAt: Date.now(), // Creation timestamp for BUL order tracking
            device1: null,
            device2: null,
            color: '#666',
            start: { x: centerX - 50, y: centerY + verticalOffset },
            end: { x: centerX + 50, y: centerY + verticalOffset },
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
                
                // ENHANCED: Larger, zoom-aware hitbox for TPs (easier to grab)
                const tpHitRadius = 16 / this.zoom; // 16px screen space, scales with zoom
                
                if (startIsTP) {
                    const distStart = Math.hypot(x - obj.start.x, y - obj.start.y);
                    if (distStart < tpHitRadius) {
                        return { link: obj, endpoint: 'start', isConnectionPoint: false };
                    }
                }
                
                if (endIsTP) {
                    const distEnd = Math.hypot(x - obj.end.x, y - obj.end.y);
                    if (distEnd < tpHitRadius) {
                        return { link: obj, endpoint: 'end', isConnectionPoint: false };
                    }
                }
            }
        }
        
        // Second pass: Check connection points (MPs) - lower priority
        // Only check if no TP was found above
        // CRITICAL FIX: Find the CLOSEST MP, not just the first one
        let closestMP = null;
        let closestMPDistance = Infinity;
        const mpHitRadius = 14 / this.zoom; // 14px screen space
        
        // DEBUG: Log all potential MPs found
        const allMPsFound = [];
        
        for (let i = this.objects.length - 1; i >= 0; i--) {
            const obj = this.objects[i];
            if (obj.type === 'unbound') {
                // Get all links in the merge chain
                const allMergedLinks = this.getAllMergedLinks(obj);
                
                // Check all connection points in the chain
                for (const chainLink of allMergedLinks) {
                    // Check if this link is the parent in a merge (has mergedWith)
                    if (chainLink.mergedWith && chainLink.mergedWith.connectionPoint) {
                        const connPoint = chainLink.mergedWith.connectionPoint;
                        const distConn = Math.hypot(x - connPoint.x, y - connPoint.y);
                        
                        allMPsFound.push({
                            type: 'parent-mergedWith',
                            link: chainLink.id,
                            pos: `(${connPoint.x.toFixed(1)}, ${connPoint.y.toFixed(1)})`,
                            dist: distConn.toFixed(1),
                            endpoint: chainLink.mergedWith.connectionEndpoint
                        });
                        
                        if (distConn < mpHitRadius && distConn < closestMPDistance) {
                            // Found a closer MP - use stored connectionEndpoint (the parent's connected endpoint)
                            const connectedEndpoint = chainLink.mergedWith.connectionEndpoint ||
                                (chainLink.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start');
                            closestMP = { link: chainLink, endpoint: connectedEndpoint, isConnectionPoint: true };
                            closestMPDistance = distConn;
                        }
                    }
                    
                    // Check if this link is the child in a merge (has mergedInto)
                    if (chainLink.mergedInto && chainLink.mergedInto.connectionPoint) {
                        const connPoint = chainLink.mergedInto.connectionPoint;
                        const distConn = Math.hypot(x - connPoint.x, y - connPoint.y);
                        
                        allMPsFound.push({
                            type: 'child-mergedInto',
                            link: chainLink.id,
                            pos: `(${connPoint.x.toFixed(1)}, ${connPoint.y.toFixed(1)})`,
                            dist: distConn.toFixed(1),
                            endpoint: chainLink.mergedInto.childEndpoint
                        });
                        
                        if (distConn < mpHitRadius && distConn < closestMPDistance) {
                            // Found a closer MP - use stored childEndpoint directly (the child's connected endpoint)
                            const connectedEndpoint = chainLink.mergedInto.childEndpoint;
                            if (connectedEndpoint) {
                                closestMP = { link: chainLink, endpoint: connectedEndpoint, isConnectionPoint: true };
                                closestMPDistance = distConn;
                            }
                        }
                    }
                }
            }
        }
        
        // DEBUG: Log all MPs and the selected one
        if (this.debugger && allMPsFound.length > 0) {
            this.debugger.logInfo(`🔍 MP Detection at (${x.toFixed(1)}, ${y.toFixed(1)}):`);
            allMPsFound.forEach((mp, idx) => {
                this.debugger.logInfo(`   ${idx + 1}. ${mp.type}: ${mp.link} at ${mp.pos}, dist=${mp.dist}, endpoint=${mp.endpoint}`);
            });
            if (closestMP) {
                this.debugger.logSuccess(`   ✓ Selected: ${closestMP.link.id}.${closestMP.endpoint} (dist=${closestMPDistance.toFixed(1)})`);
            }
        }
        
        return closestMP;
    }
    
    createText(x, y) {
        const text = {
            id: `text_${this.textIdCounter++}`,
            type: 'text',
            x: x,
            y: y,
            text: 'Text',
            fontSize: document.getElementById('font-size').value,
            color: document.getElementById('color-picker').value,
            rotation: 0
        };
        
        return text;
    }
    
    drawLinkPreview(startDevice, endPos) {
        this.ctx.save();
        this.ctx.translate(this.panOffset.x, this.panOffset.y);
        this.ctx.scale(this.zoom, this.zoom);
        
        this.ctx.strokeStyle = startDevice.color || '#007bff'; // Use device color or fallback
        this.ctx.lineWidth = 3; // Thicker line
        this.ctx.setLineDash([8, 4]); // Longer dashes for better visibility
        
        const angle1 = Math.atan2(endPos.y - startDevice.y, endPos.x - startDevice.x);
        const startX = startDevice.x + Math.cos(angle1) * startDevice.radius;
        const startY = startDevice.y + Math.sin(angle1) * startDevice.radius;
        
        this.ctx.beginPath();
        this.ctx.moveTo(startX, startY);
        this.ctx.lineTo(endPos.x, endPos.y);
        this.ctx.stroke();
        
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
            document.getElementById('rotation-value').textContent = angle + '°';
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
            document.getElementById('font-size').value = this.selectedObject.fontSize;
            document.getElementById('rotation-slider').value = this.selectedObject.rotation;
            
            // ENHANCED: Display +/- format (-180 to +180)
            let degrees = Math.round(this.selectedObject.rotation) % 360;
            if (degrees > 180) degrees -= 360;
            if (degrees < -180) degrees += 360;
            const displayText = degrees >= 0 ? `+${degrees}°` : `${degrees}°`;
            document.getElementById('rotation-value').textContent = displayText;
            
            document.getElementById('color-picker').value = this.selectedObject.color;
        }
    }
    
    deleteSelected() {
        if (this.selectedObjects.length === 0 && !this.selectedObject) {
            if (this.debugger) {
                this.debugger.logInfo('No objects selected to delete');
            }
            return;
        }
        
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
        const offsetX = pastePos.x - (this.clipboardCentroid?.x || 0);
        const offsetY = pastePos.y - (this.clipboardCentroid?.y || 0);
        
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
        
        if (this.debugger) {
            const count = this.selectedObjects.length || 1;
            this.debugger.logAction(`Deleting ${count} object(s)`);
        }
        
        this.saveState(); // Save state before deleting
        
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
            console.log('saveState skipped: initializing (this is normal during setup)');
            return;
        }
        
        // Reduced logging: saveState() is called very frequently, don't log every time
        // Uncomment if debugging undo/redo issues:
        // if (this.debugger) {
        //     this.debugger.logAction('saveState() called');
        // }
        
        // Ensure history arrays exist
        if (!this.history) {
            this.history = [];
            this.historyIndex = -1;
        }
        
        try {
            console.log('saveState called with', this.objects.length, 'objects');
            console.log('Current historyIndex:', this.historyIndex, 'history.length:', this.history.length);
            
            // Create deep copy of current state
            const state = {
                objects: JSON.parse(JSON.stringify(this.objects)),
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
            
            console.log('After saveState - historyIndex:', this.historyIndex, 'history.length:', this.history.length);
            
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
        
        // Temporarily disable auto-save during restore to prevent triggering saveState
        const wasInitializing = this.initializing;
        this.initializing = true;
        
        this.objects = JSON.parse(JSON.stringify(state.objects));
        this.deviceIdCounter = state.deviceIdCounter;
        this.linkIdCounter = state.linkIdCounter;
        this.textIdCounter = state.textIdCounter;
        this.deviceCounters = { ...state.deviceCounters };
        
        this.selectedObject = null;
        this.selectedObjects = [];
        this.updatePropertiesPanel();
        this.draw();
        
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
    
    clearCanvas() {
        // Show custom confirmation dropdown
        this.showClearConfirmation();
    }
    
    showClearConfirmation() {
        // Create confirmation dropdown
        const dropdown = document.createElement('div');
        dropdown.id = 'clear-confirmation';
        dropdown.style.cssText = `
            position: fixed;
            top: 60px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.95);
            border: 2px solid #f00;
            border-radius: 8px;
            padding: 20px;
            z-index: 10001;
            box-shadow: 0 0 30px rgba(255, 0, 0, 0.5);
            min-width: 400px;
            color: #fff;
            font-family: Arial, sans-serif;
        `;
        
        const objectCount = this.objects.length;
        const deviceCount = this.objects.filter(o => o.type === 'device').length;
        const linkCount = this.objects.filter(o => o.type === 'link' || o.type === 'unbound').length;
        
        dropdown.innerHTML = `
            <div style="text-align: center; margin-bottom: 15px;">
                <div style="font-size: 48px; margin-bottom: 10px;">⚠️</div>
                <div style="font-size: 18px; font-weight: bold; color: #f00; margin-bottom: 10px;">
                    CLEAR ENTIRE CANVAS?
                </div>
                <div style="color: #ff0; font-size: 14px; margin-bottom: 15px;">
                    This will permanently delete:
                </div>
                <div style="background: rgba(255, 0, 0, 0.2); padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    <div style="color: #0ff;">📦 ${objectCount} Total Objects</div>
                    <div style="color: #0ff;">🔷 ${deviceCount} Devices</div>
                    <div style="color: #0ff;">🔗 ${linkCount} Links</div>
                </div>
                <div style="color: #f00; font-weight: bold; margin-bottom: 15px;">
                    ⚡ THIS CANNOT BE UNDONE! ⚡
                </div>
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <button id="confirm-clear-yes" style="
                        background: #f00;
                        color: #fff;
                        border: 2px solid #fff;
                        padding: 10px 30px;
                        cursor: pointer;
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 14px;
                    ">YES, DELETE ALL</button>
                    <button id="confirm-clear-no" style="
                        background: #27ae60;
                        color: #fff;
                        border: 2px solid #fff;
                        padding: 10px 30px;
                        cursor: pointer;
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 14px;
                    ">NO, CANCEL</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(dropdown);
        
        // Yes button - clear canvas
        document.getElementById('confirm-clear-yes').addEventListener('click', () => {
            this.performClearCanvas();
            document.body.removeChild(dropdown);
            
            if (this.debugger) {
                // Use logSuccess instead of logError - clearing canvas is intentional, not a bug
                this.debugger.logSuccess('🗑️ Canvas cleared - ALL objects deleted');
            }
        });
        
        // No button - cancel
        document.getElementById('confirm-clear-no').addEventListener('click', () => {
            document.body.removeChild(dropdown);
            
            if (this.debugger) {
                this.debugger.logInfo('✓ Clear cancelled by user');
            }
        });
        
        // Close on Escape
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                if (document.body.contains(dropdown)) {
                    document.body.removeChild(dropdown);
                }
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    }
    
    performClearCanvas() {
        // Actually clear the canvas
        this.objects = [];
        this.selectedObject = null;
        this.selectedObjects = [];
        this.deviceIdCounter = 0;
        this.linkIdCounter = 0;
        this.textIdCounter = 0;
        this.deviceCounters = { router: 0, switch: 0 };
        this.updatePropertiesPanel();
        this.draw();
        this.saveState(); // Save cleared state (triggers auto-save)
    }
    
    toggleTheme() {
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
        
        // Redraw canvas with new background
        this.draw();
        this.scheduleAutoSave();
    }
    
    drawGrid() {
        // Draw infinite grid that zooms with canvas - Notebook style
        const gridSize = 50; // Base grid size in world coordinates (50px squares)
        
        // Calculate extended visible area (draw beyond viewport for smooth panning)
        const margin = 500; // Extra margin to draw
        const startX = (-this.panOffset.x / this.zoom) - margin;
        const startY = (-this.panOffset.y / this.zoom) - margin;
        const endX = startX + (this.canvas.width / this.zoom) + margin * 2;
        const endY = startY + (this.canvas.height / this.zoom) + margin * 2;
        
        this.ctx.save();
        this.ctx.translate(this.panOffset.x, this.panOffset.y);
        this.ctx.scale(this.zoom, this.zoom);
        
        // Adjust grid color for dark mode
        this.ctx.strokeStyle = this.darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';
        this.ctx.lineWidth = 1 / this.zoom;
        
        // Draw vertical lines
        const gridStartX = Math.floor(startX / gridSize) * gridSize;
        for (let x = gridStartX; x <= endX; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, startY);
            this.ctx.lineTo(x, endY);
            this.ctx.stroke();
        }
        
        // Draw horizontal lines
        const gridStartY = Math.floor(startY / gridSize) * gridSize;
        for (let y = gridStartY; y <= endY; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(startX, y);
            this.ctx.lineTo(endX, y);
            this.ctx.stroke();
        }
        
        this.ctx.restore();
    }
    
    draw() {
        // ULTRA: Enable high-quality rendering for smooth, anti-aliased visuals
        this.ctx.imageSmoothingEnabled = true;
        this.ctx.imageSmoothingQuality = 'high';
        
        // Clear with appropriate background color
        if (this.darkMode) {
            this.ctx.fillStyle = '#1a1a1a';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        } else {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        
        // Draw grid before transformations (if enabled)
        if (this.gridZoomEnabled) {
            this.drawGrid();
        }
        
        this.ctx.save();
        // ULTRA: Translate to half-pixel boundaries for sharper rendering
        this.ctx.translate(Math.round(this.panOffset.x) + 0.5, Math.round(this.panOffset.y) + 0.5);
        this.ctx.scale(this.zoom, this.zoom);
        
        // Enable anti-aliasing for smooth circles and lines
        this.ctx.lineJoin = 'round';
        this.ctx.lineCap = 'round';
        
        // Update TP positions when devices move (for device-attached unbound links)
        // ENHANCED: Apply offset for multiple links between same devices
        // CRITICAL: Skip position updates for link being actively dragged
        this.objects.forEach(obj => {
            // Skip if this is the link currently being stretched (let handleMouseMove control it)
            if (this.stretchingLink && obj.id === this.stretchingLink.id) {
                return; // Don't recalculate position while user is dragging
            }
            
            if (obj.type === 'unbound' && (obj.device1 || obj.device2)) {
                // Get endpoint devices for offset calculation
                const endpoints = this.getBULEndpointDevices(obj);
                let baseAngle = null;
                let offsetAmount = 0;
                
                // Calculate offset if both endpoints are attached to devices
                if (endpoints.hasEndpoints && endpoints.device1 && endpoints.device2) {
                    const device1 = this.objects.find(o => o.id === endpoints.device1);
                    const device2 = this.objects.find(o => o.id === endpoints.device2);
                    
                    if (device1 && device2) {
                        // Base angle between the two endpoint devices
                        baseAngle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
                        
                        // Calculate offset based on linkIndex
                        // User requested logic: First (0) = Middle, Second (1) = Right (+), Third (2) = Left (-)
                        const linkIndex = this.calculateLinkIndex(obj);
                        if (linkIndex > 0) {
                            const magnitude = Math.ceil(linkIndex / 2) * 20;
                            const direction = (linkIndex % 2 === 1) ? 1 : -1; // Odd = Right (+), Even = Left (-)
                            offsetAmount = magnitude * direction;
                        }
                        
                        // Store linkIndex on the object for reference (don't log every frame)
                        if (obj.linkIndex !== linkIndex) {
                            obj.linkIndex = linkIndex;
                        }
                    }
                }
                
                // Update start TP if attached to device1
                if (obj.device1) {
                const device1 = this.objects.find(o => o.id === obj.device1);
                    if (device1) {
                        let angle = baseAngle;
                        
                        // If no baseAngle (not both ends attached), calculate dynamically
                        if (angle === null) {
                            // CRITICAL: Determine if this is a SINGLE UL (not part of BUL)
                            const isSingleUL = !obj.mergedWith && !obj.mergedInto;
                            
                            if (isSingleUL) {
                                // SINGLE UL: Always point toward the FREE endpoint (like QL behavior)
                                // This makes the attached end dynamically rotate around the device edge
                                angle = Math.atan2(obj.end.y - device1.y, obj.end.x - device1.x);
                            } else {
                                // BUL: Use stored attachment angle if available (preserves attachment location)
                                if (obj.device1Angle !== undefined) {
                                    angle = obj.device1Angle;
                                } else {
                                    // Fallback: calculate to other end or connected device
                            let targetPoint = obj.end;
                            if (obj.mergedWith || obj.mergedInto) {
                                const connectedDevices = this.getAllConnectedDevices(obj);
                                const otherDeviceId = connectedDevices.deviceIds.find(id => id !== obj.device1);
                                if (otherDeviceId) {
                                    const otherDevice = this.objects.find(o => o.id === otherDeviceId);
                                    if (otherDevice) {
                                        targetPoint = { x: otherDevice.x, y: otherDevice.y };
                                    }
                                }
                            }
                            angle = Math.atan2(targetPoint.y - device1.y, targetPoint.x - device1.x);
                                }
                            }
                        }
                        
                        // Calculate base position on device edge
                        const baseStartX = device1.x + Math.cos(angle) * device1.radius;
                        const baseStartY = device1.y + Math.sin(angle) * device1.radius;
                        
                        // ENHANCED: Apply perpendicular offset SAME AS QUICK LINKS
                        let targetX = baseStartX;
                        let targetY = baseStartY;
                        
                        if (baseAngle !== null) {
                            // Both ends attached - use EXACT same offset logic as QLs in drawLink()
                            const sortedIds = [endpoints.device1, endpoints.device2].sort();
                            // CRITICAL: Use the LINK's actual device1, not the sorted endpoint
                            const isNormalDirection = obj.device1 === sortedIds[0];
                            // CRITICAL: Use baseAngle for perpendicular, NOT the current angle
                            let perpAngle = baseAngle + Math.PI / 2;
                            if (!isNormalDirection) {
                                perpAngle += Math.PI;
                            }
                            
                            const offsetX = Math.cos(perpAngle) * offsetAmount;
                            const offsetY = Math.sin(perpAngle) * offsetAmount;
                            
                            // Create offset target point
                            const targetStartX = baseStartX + offsetX;
                            const targetStartY = baseStartY + offsetY;
                            
                            // Calculate direction from device center to offset target point
                            const startDirAngle = Math.atan2(targetStartY - device1.y, targetStartX - device1.x);
                            
                            // Final touch point on device edge along this direction
                            targetX = device1.x + Math.cos(startDirAngle) * device1.radius;
                            targetY = device1.y + Math.sin(startDirAngle) * device1.radius;
                        }
                        
                        // SMOOTH MOVEMENT: Use lerp for Arrow-style ULs for smoother animation
                        const linkStyle = obj.style !== undefined ? obj.style : 'solid';
                        if (linkStyle === 'arrow' && obj.start) {
                            obj._targetStart = { x: targetX, y: targetY }; // Store target for animation loop
                            obj.start = this.lerpPoint(obj.start, { x: targetX, y: targetY }, 0.2);
                        } else {
                            obj.start = { x: targetX, y: targetY };
                        }
                        
                        // If this is the connected end in a merge, update the MP position
                        if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'start') {
                            obj.mergedWith.connectionPoint.x = obj.start.x;
                            obj.mergedWith.connectionPoint.y = obj.start.y;
                            
                            // Also update child's connection point
                            const childLink = this.objects.find(o => o.id === obj.mergedWith.linkId);
                            if (childLink && childLink.mergedInto) {
                                childLink.mergedInto.connectionPoint.x = obj.start.x;
                                childLink.mergedInto.connectionPoint.y = obj.start.y;
                            }
                        }
                        if (obj.mergedInto) {
                            const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
                            if (parentLink && parentLink.mergedWith && parentLink.mergedWith.childFreeEnd !== 'start') {
                                obj.mergedInto.connectionPoint.x = obj.start.x;
                                obj.mergedInto.connectionPoint.y = obj.start.y;
                                parentLink.mergedWith.connectionPoint.x = obj.start.x;
                                parentLink.mergedWith.connectionPoint.y = obj.start.y;
                            }
                        }
                    }
                }
                
                // Update end TP if attached to device2
                if (obj.device2) {
                const device2 = this.objects.find(o => o.id === obj.device2);
                    if (device2) {
                        let angle = baseAngle !== null ? baseAngle + Math.PI : null; // Opposite direction
                        
                        // If no baseAngle (not both ends attached), calculate dynamically
                        if (angle === null) {
                            // CRITICAL: Determine if this is a SINGLE UL (not part of BUL)
                            const isSingleUL = !obj.mergedWith && !obj.mergedInto;
                            
                            if (isSingleUL) {
                                // SINGLE UL: Always point toward the FREE endpoint (like QL behavior)
                                // This makes the attached end dynamically rotate around the device edge
                                angle = Math.atan2(obj.start.y - device2.y, obj.start.x - device2.x);
                            } else {
                                // BUL: Use stored attachment angle if available (preserves attachment location)
                                if (obj.device2Angle !== undefined) {
                                    angle = obj.device2Angle;
                                } else {
                                    // Fallback: calculate to other end or connected device
                            let targetPoint = obj.start;
                            if (obj.mergedWith || obj.mergedInto) {
                                const connectedDevices = this.getAllConnectedDevices(obj);
                                const otherDeviceId = connectedDevices.deviceIds.find(id => id !== obj.device2);
                                if (otherDeviceId) {
                                    const otherDevice = this.objects.find(o => o.id === otherDeviceId);
                                    if (otherDevice) {
                                        targetPoint = { x: otherDevice.x, y: otherDevice.y };
                                    }
                                }
                            }
                                angle = Math.atan2(targetPoint.y - device2.y, targetPoint.x - device2.x);
                                }
                            }
                        }
                        
                        // Calculate base position on device edge
                        const baseEndX = device2.x + Math.cos(angle) * device2.radius;
                        const baseEndY = device2.y + Math.sin(angle) * device2.radius;
                        
                        // ENHANCED: Apply perpendicular offset SAME AS QUICK LINKS
                        let targetX = baseEndX;
                        let targetY = baseEndY;
                        
                        if (baseAngle !== null) {
                            // Both ends attached - use EXACT same offset logic as QLs in drawLink()
                            const sortedIds = [endpoints.device1, endpoints.device2].sort();
                            // CRITICAL: Use the LINK's actual device1 for consistent direction check
                            const isNormalDirection = obj.device1 === sortedIds[0];
                            // CRITICAL: Use baseAngle for perpendicular, NOT the current angle
                            let perpAngle = baseAngle + Math.PI / 2;
                            if (!isNormalDirection) {
                                perpAngle += Math.PI;
                            }
                            
                            const offsetX = Math.cos(perpAngle) * offsetAmount;
                            const offsetY = Math.sin(perpAngle) * offsetAmount;
                            
                            // Create offset target point
                            const targetEndX = baseEndX + offsetX;
                            const targetEndY = baseEndY + offsetY;
                            
                            // Calculate direction from device center to offset target point
                            const endDirAngle = Math.atan2(targetEndY - device2.y, targetEndX - device2.x);
                            
                            // Final touch point on device edge along this direction
                            targetX = device2.x + Math.cos(endDirAngle) * device2.radius;
                            targetY = device2.y + Math.sin(endDirAngle) * device2.radius;
                        }
                        
                        // SMOOTH MOVEMENT: Use lerp for Arrow-style ULs for smoother animation
                        const linkStyleEnd = obj.style !== undefined ? obj.style : 'solid';
                        if (linkStyleEnd === 'arrow' && obj.end) {
                            obj._targetEnd = { x: targetX, y: targetY }; // Store target for animation loop
                            obj.end = this.lerpPoint(obj.end, { x: targetX, y: targetY }, 0.2);
                        } else {
                            obj.end = { x: targetX, y: targetY };
                        }
                        
                        // If this is the connected end in a merge, update the MP position
                        if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'end') {
                            obj.mergedWith.connectionPoint.x = obj.end.x;
                            obj.mergedWith.connectionPoint.y = obj.end.y;
                            
                            // Also update child's connection point
                            const childLink = this.objects.find(o => o.id === obj.mergedWith.linkId);
                            if (childLink && childLink.mergedInto) {
                                childLink.mergedInto.connectionPoint.x = obj.end.x;
                                childLink.mergedInto.connectionPoint.y = obj.end.y;
                            }
                        }
                        if (obj.mergedInto) {
                            const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
                            if (parentLink && parentLink.mergedWith && parentLink.mergedWith.childFreeEnd !== 'end') {
                                obj.mergedInto.connectionPoint.x = obj.end.x;
                                obj.mergedInto.connectionPoint.y = obj.end.y;
                                parentLink.mergedWith.connectionPoint.x = obj.end.x;
                                parentLink.mergedWith.connectionPoint.y = obj.end.y;
                            }
                        }
                    }
                }
            }
        });
        
        // Update adjacent text positions to stay glued to links
        this.objects.forEach(obj => {
            if (obj.type === 'text' && obj.linkId && obj.position) {
                this.updateAdjacentTextPosition(obj);
            }
        });
        
        // No layer filtering - show all objects
        const visibleObjects = this.objects;
        
        // Draw links first (behind devices)
        visibleObjects.forEach(obj => {
            if (obj.type === 'link' || obj.type === 'unbound') {
                this.drawLink(obj);
            }
        });
        
        // Draw devices
        visibleObjects.forEach(obj => {
            if (obj.type === 'device') {
                this.drawDevice(obj);
            }
        });
        
        // Draw text
        visibleObjects.forEach(obj => {
            if (obj.type === 'text') {
                this.drawText(obj);
            }
        });
        
        // Draw marquee selection rectangle with visual feedback
        if (this.marqueeActive && this.selectionRectangle) {
            this.ctx.strokeStyle = '#3498db';
            this.ctx.fillStyle = 'rgba(52, 152, 219, 0.15)'; // Light blue fill
            this.ctx.lineWidth = 2 / this.zoom;
            this.ctx.setLineDash([5 / this.zoom, 5 / this.zoom]);
            
            this.ctx.fillRect(
                this.selectionRectangle.x,
                this.selectionRectangle.y,
                this.selectionRectangle.width,
                this.selectionRectangle.height
            );
            this.ctx.strokeRect(
                this.selectionRectangle.x,
                this.selectionRectangle.y,
                this.selectionRectangle.width,
                this.selectionRectangle.height
            );
            this.ctx.setLineDash([]);
        }
        
        this.ctx.restore();
        
        // SMOOTH MOVEMENT: Continue animation loop for Arrow-style ULs still interpolating
        // Check if any arrow-style ULs need more interpolation
        let needsMoreAnimation = false;
        this.objects.forEach(obj => {
            if (obj.type === 'unbound' && obj.style === 'arrow') {
                // Check if positions are still interpolating (not settled yet)
                if (obj._targetStart && obj.start) {
                    const startDist = Math.sqrt(
                        Math.pow(obj.start.x - obj._targetStart.x, 2) + 
                        Math.pow(obj.start.y - obj._targetStart.y, 2)
                    );
                    if (startDist > 1) needsMoreAnimation = true;
                }
                if (obj._targetEnd && obj.end) {
                    const endDist = Math.sqrt(
                        Math.pow(obj.end.x - obj._targetEnd.x, 2) + 
                        Math.pow(obj.end.y - obj._targetEnd.y, 2)
                    );
                    if (endDist > 1) needsMoreAnimation = true;
                }
            }
        });
        
        if (needsMoreAnimation && !this._smoothAnimationPending) {
            this._smoothAnimationPending = true;
            requestAnimationFrame(() => {
                this._smoothAnimationPending = false;
                this.draw();
            });
        }
    }
    
    drawDevice(device) {
        const isSelected = this.selectedObject === device || this.selectedObjects.includes(device);
        
        // Draw circle
        this.ctx.beginPath();
        this.ctx.arc(device.x, device.y, device.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = device.color;
        this.ctx.fill();
        
        // Draw border
        this.ctx.strokeStyle = isSelected ? '#3498db' : '#333';
        this.ctx.lineWidth = isSelected ? 3 : 2;
        this.ctx.stroke();
        
        // Draw device label - rotated and scaled with device
        this.ctx.save();
        this.ctx.translate(device.x, device.y);
        this.ctx.rotate((device.rotation || 0) * Math.PI / 180);
        
        const fontSize = Math.max(12, Math.min(device.radius * 0.7, 24));
        this.ctx.font = `bold ${fontSize}px Arial`;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        const label = device.label || (device.deviceType === 'router' ? 'NCP' : 'S');
        
        // Draw text with black stroke (outline) for better visibility
        this.ctx.strokeStyle = 'black';
        this.ctx.lineWidth = 3;
        this.ctx.strokeText(label, 0, 0);
        
        // Draw white fill on top
        this.ctx.fillStyle = 'white';
        this.ctx.fillText(label, 0, 0);
        
        this.ctx.restore();
        
        // Draw selection highlight ONLY in Select mode
        if (isSelected && this.currentMode === 'select') {
            // Selection highlight ring - scales with zoom for consistent appearance
            const selectionOffset = 5 / this.zoom; // 5px in screen space
            const dashLength = 5 / this.zoom; // Dash pattern scales with zoom
            
            this.ctx.beginPath();
            this.ctx.arc(device.x, device.y, device.radius + selectionOffset, 0, Math.PI * 2);
            this.ctx.strokeStyle = '#3498db';
            this.ctx.lineWidth = 2 / this.zoom; // Scale line width with zoom
            this.ctx.setLineDash([dashLength, dashLength]);
            this.ctx.stroke();
            this.ctx.setLineDash([]);
            
            // Draw rotation handle at bottom-right corner
            const deviceRotation = (device.rotation || 0) * Math.PI / 180;
            const baseAngle = -Math.PI / 4; // Bottom-right corner
            const rotatedAngle = baseAngle + deviceRotation;
            const handleDist = device.radius + 12; // 12px offset from device edge
            const handleX = device.x + Math.cos(rotatedAngle) * handleDist;
            const handleY = device.y + Math.sin(rotatedAngle) * handleDist;
            
            // Draw small rotation dot - scales with zoom for consistent screen appearance
            const handleRadius = 6 / this.zoom; // 6px in screen space
            this.ctx.beginPath();
            this.ctx.arc(handleX, handleY, handleRadius, 0, Math.PI * 2);
            this.ctx.fillStyle = '#27ae60'; // Green color for rotation handle
            this.ctx.fill();
            this.ctx.strokeStyle = '#ffffff';
            this.ctx.lineWidth = 1.5 / this.zoom; // Scale stroke with zoom
            this.ctx.stroke();
            
            // NEW: Draw Angle Meter if enabled - rotates with device for cleaner UI
            if (this.showAngleMeter) {
                const degrees = Math.round((device.rotation || 0) % 360);
                const normalizedDegrees = degrees < 0 ? degrees + 360 : degrees;
                
                this.ctx.save();
                
                // Position relative to handle with rotation
                const labelOffsetDist = 25 / this.zoom;
                const labelX = handleX + Math.cos(rotatedAngle) * labelOffsetDist;
                const labelY = handleY + Math.sin(rotatedAngle) * labelOffsetDist;
                
                // Translate to label position
                this.ctx.translate(labelX, labelY);
                
                // ENHANCED: Rotate label to align with device rotation for cleaner look
                // Keep text horizontal when rotation is near 0/180, otherwise align with device
                const shouldAlignWithDevice = Math.abs(degrees % 180) > 15 && Math.abs(degrees % 180) < 165;
                if (shouldAlignWithDevice) {
                    this.ctx.rotate(deviceRotation);
                }
                
                const text = `${normalizedDegrees}°`;
                this.ctx.font = `bold ${11 / this.zoom}px Arial`;
                const metrics = this.ctx.measureText(text);
                
                const bgPad = 5 / this.zoom;
                const bgW = metrics.width + bgPad * 2;
                const bgH = 16 / this.zoom;
                const radius = 4 / this.zoom;
                
                // Shadow for depth
                this.ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
                this.ctx.shadowBlur = 6 / this.zoom;
                this.ctx.shadowOffsetX = 1 / this.zoom;
                this.ctx.shadowOffsetY = 2 / this.zoom;
                
                // Gradient background for modern look
                const gradient = this.ctx.createLinearGradient(-bgW/2, -bgH/2, -bgW/2, bgH/2);
                gradient.addColorStop(0, 'rgba(46, 204, 113, 1)');
                gradient.addColorStop(1, 'rgba(39, 174, 96, 1)');
                
                // Rounded rectangle
                this.ctx.beginPath();
                this.ctx.moveTo(-bgW/2 + radius, -bgH/2);
                this.ctx.lineTo(bgW/2 - radius, -bgH/2);
                this.ctx.arcTo(bgW/2, -bgH/2, bgW/2, -bgH/2 + radius, radius);
                this.ctx.lineTo(bgW/2, bgH/2 - radius);
                this.ctx.arcTo(bgW/2, bgH/2, bgW/2 - radius, bgH/2, radius);
                this.ctx.lineTo(-bgW/2 + radius, bgH/2);
                this.ctx.arcTo(-bgW/2, bgH/2, -bgW/2, bgH/2 - radius, radius);
                this.ctx.lineTo(-bgW/2, -bgH/2 + radius);
                this.ctx.arcTo(-bgW/2, -bgH/2, -bgW/2 + radius, -bgH/2, radius);
                this.ctx.closePath();
                this.ctx.fillStyle = gradient;
                this.ctx.fill();
                
                // Subtle border
                this.ctx.shadowColor = 'transparent';
                this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
                this.ctx.lineWidth = 1.5 / this.zoom;
                this.ctx.stroke();
                
                // Text with shadow
                this.ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
                this.ctx.shadowBlur = 1 / this.zoom;
                this.ctx.shadowOffsetY = 1 / this.zoom;
                this.ctx.fillStyle = '#ffffff';
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(text, 0, 0);
                
                this.ctx.restore();
            }
        }
        
        // Draw lock icon if device is locked
        if (device.locked) {
            this.ctx.save();
            this.ctx.translate(device.x, device.y - device.radius - 15);
            
            // Draw lock icon
            this.ctx.fillStyle = '#e74c3c';
            this.ctx.strokeStyle = 'white';
            this.ctx.lineWidth = 1.5;
            
            // Lock body
            this.ctx.fillRect(-6, -2, 12, 10);
            this.ctx.strokeRect(-6, -2, 12, 10);
            
            // Lock shackle
            this.ctx.beginPath();
            this.ctx.arc(0, -2, 4, Math.PI, 0, false);
            this.ctx.stroke();
            
            this.ctx.restore();
        }
    }
    
    drawLink(link) {
        // Handle unbound links differently
        if (link.type === 'unbound') {
            this.drawUnboundLink(link);
            return;
        }
        
        const device1 = this.objects.find(obj => obj.id === link.device1);
        const device2 = this.objects.find(obj => obj.id === link.device2);
        
        if (!device1 || !device2) return;
        
        const isSelected = this.selectedObject === link || this.selectedObjects.includes(link);
        
        // Calculate connection points
        const angle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
        const startX = device1.x + Math.cos(angle) * device1.radius;
        const startY = device1.y + Math.sin(angle) * device1.radius;
        const endX = device2.x - Math.cos(angle) * device2.radius;
        const endY = device2.y - Math.sin(angle) * device2.radius;
        
        // DYNAMIC link index calculation for tracking across all link types
        // This ensures that Solid, Dashed, and Arrow links are all counted together
        // and positioned correctly relative to each other
        const connectedLinks = this.objects.filter(obj => 
            (obj.type === 'link' || (obj.type === 'unbound' && obj.device1 && obj.device2)) &&
            ((obj.device1 === device1.id && obj.device2 === device2.id) ||
             (obj.device1 === device2.id && obj.device2 === device1.id))
        ).sort((a, b) => {
            // Sort by ID to ensure stable order
            // Extract number from ID (link_123 -> 123)
            const idA = parseInt(a.id.split('_')[1]);
            const idB = parseInt(b.id.split('_')[1]);
            return idA - idB;
        });
        
        const linkIndex = connectedLinks.findIndex(l => l.id === link.id);
        if (linkIndex === -1) return; // Should not happen
        
        // NORMALIZE perpendicular direction for true bidirectional behavior
        // Always use the same perpendicular direction regardless of link direction
        // Sort device IDs to get consistent orientation
        const sortedIds = [link.device1, link.device2].sort();
        const isNormalDirection = link.device1 === sortedIds[0];
        
        // First link (index 0) is dead center - no offset
        let offsetAmount = 0;
        let direction = 0;
        if (linkIndex > 0) {
            // User requested logic:
            // First (0): Middle
            // Second (1): Right (+)
            // Third (2): Left (-)
            // Fourth (3): Right (+)
            // Fifth (4): Left (-)
            
            // Logic:
            // ceil(index / 2) gives magnitude: ceil(1/2)=1, ceil(2/2)=1, ceil(3/2)=2...
            // direction: index odd -> 1 (Right), index even -> -1 (Left)
            
            const magnitude = Math.ceil(linkIndex / 2) * 20;
            direction = (linkIndex % 2 === 1) ? 1 : -1;
            offsetAmount = magnitude * direction;
        }
        
        // Calculate perpendicular offset with normalized direction
        let perpAngle = angle + Math.PI / 2;
        // Flip perpendicular if link is in reverse direction (ensures consistent sides)
        if (!isNormalDirection) {
            perpAngle += Math.PI; // Flip 180 degrees
        }
        
        const offsetX = Math.cos(perpAngle) * offsetAmount;
        const offsetY = Math.sin(perpAngle) * offsetAmount;
        
        // Calculate offset start/end points
        const offsetStartX = startX + offsetX;
        const offsetStartY = startY + offsetY;
        const offsetEndX = endX + offsetX;
        const offsetEndY = endY + offsetY;
        
        // Calculate touch points on device edges that account for offset
        // Find intersection of offset line with device circles
        const actualStartAngle = Math.atan2(device2.y - device1.y, device2.x - device1.x);
        
        // Start with base touch points (centered line)
        const baseStartX = device1.x + Math.cos(actualStartAngle) * device1.radius;
        const baseStartY = device1.y + Math.sin(actualStartAngle) * device1.radius;
        const baseEndX = device2.x - Math.cos(actualStartAngle) * device2.radius;
        const baseEndY = device2.y - Math.sin(actualStartAngle) * device2.radius;
        
        // Apply offset to create target line
        const targetStartX = baseStartX + offsetX;
        const targetStartY = baseStartY + offsetY;
        const targetEndX = baseEndX + offsetX;
        const targetEndY = baseEndY + offsetY;
        
        // Calculate direction from device centers to offset target points
        const startDirAngle = Math.atan2(targetStartY - device1.y, targetStartX - device1.x);
        const endDirAngle = Math.atan2(targetEndY - device2.y, targetEndX - device2.x);
        
        // Final touch points on device edges along these directions (guaranteed to touch)
        const finalStartX = device1.x + Math.cos(startDirAngle) * device1.radius;
        const finalStartY = device1.y + Math.sin(startDirAngle) * device1.radius;
        const finalEndX = device2.x + Math.cos(endDirAngle) * device2.radius;
        const finalEndY = device2.y + Math.sin(endDirAngle) * device2.radius;
        
        // Update link positions
        link.start = { x: finalStartX, y: finalStartY };
        link.end = { x: finalEndX, y: finalEndY };
        
        // Determine if curve mode is enabled for this link
        // Magnetic field must be > 0 for curves to work
        const curveEnabled = (link.curveOverride !== undefined ? link.curveOverride : this.linkCurveMode) && this.magneticFieldStrength > 0;
        
        // Draw curved path for multiple links (more elegant)
        this.ctx.beginPath();
        
        let cp1x, cp1y, cp2x, cp2y;
        
        if (curveEnabled) {
            // Curve mode enabled - check for obstacles and curve around them
            const obstacles = this.findAllObstaclesOnPath(finalStartX, finalStartY, finalEndX, finalEndY, link);
            
            if (obstacles.length > 0) {
                // Gentle magnetic repulsion - mathematically accurate curve around obstacles
                // Use quadratic curve for smoother, more natural appearance
                
                // Calculate path midpoint and link direction
                const straightMidX = (finalStartX + finalEndX) / 2;
                const straightMidY = (finalStartY + finalEndY) / 2;
                const linkLength = Math.sqrt(Math.pow(finalEndX - finalStartX, 2) + Math.pow(finalEndY - finalStartY, 2));
                
                // Calculate combined magnetic repulsion from ALL obstacles
                let totalRepulsionX = 0;
                let totalRepulsionY = 0;
                let closestObstacleRadius = 0;
                
                obstacles.forEach((obstacleInfo) => {
                    const obstacle = obstacleInfo.device;
                    
                    // Vector from obstacle center to straight-line midpoint
                    const dx = straightMidX - obstacle.x;
                    const dy = straightMidY - obstacle.y;
                    const distToMid = Math.sqrt(dx * dx + dy * dy) || 1;
                    
                    // Safe clearance like guitar string avoiding a finger
                    const minClearance = obstacle.radius + 18;
                    
                    // Repulsion direction (away from obstacle)
                    const repelDirX = dx / distToMid;
                    const repelDirY = dy / distToMid;
                    
                    // Guitar string physics: strong elastic force with smooth falloff
                    // Magnetic field creates gravity effect on links
                    const k = minClearance * minClearance * this.magneticFieldStrength * 2; // Increased strength
                    const repulsionStrength = k / Math.pow(distToMid, 0.8); // Stronger magnetic repulsion
                    
                    totalRepulsionX += repelDirX * repulsionStrength;
                    totalRepulsionY += repelDirY * repulsionStrength;
                    
                    closestObstacleRadius = Math.max(closestObstacleRadius, obstacle.radius);
                });
                
                // Calculate gentle deflection (like a plucked guitar string)
                const deflectionMag = Math.sqrt(totalRepulsionX * totalRepulsionX + totalRepulsionY * totalRepulsionY);
                
                // More visible deflection for curvier appearance
                const maxDeflection = Math.min(linkLength * 0.45, closestObstacleRadius * 2.5);
                const actualDeflection = Math.min(deflectionMag, maxDeflection);
                
                const normalizedRepulX = totalRepulsionX / (deflectionMag || 1);
                const normalizedRepulY = totalRepulsionY / (deflectionMag || 1);
                
                const deflectedMidX = straightMidX + normalizedRepulX * actualDeflection;
                const deflectedMidY = straightMidY + normalizedRepulY * actualDeflection;
                
                // Curvier control point calculation for more visible elastic curves
                // Higher weight = more pronounced curve (like a stretched guitar string)
                const controlWeight = 0.7; // Increased from 0.6 for curvier appearance
                const midWeight = 1 - controlWeight;
                
                cp1x = finalStartX * midWeight + deflectedMidX * controlWeight;
                cp1y = finalStartY * midWeight + deflectedMidY * controlWeight;
                cp2x = finalEndX * midWeight + deflectedMidX * controlWeight;
                cp2y = finalEndY * midWeight + deflectedMidY * controlWeight;
                
                this.ctx.moveTo(finalStartX, finalStartY);
                this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, finalEndX, finalEndY);
        } else {
                // No obstacles - add slight curvature for visual separation
            const curveOffset = linkIndex > 0 ? Math.ceil(linkIndex / 2) * 10 * direction : 0;
            cp1x = finalStartX + Math.cos(perpAngle) * curveOffset;
            cp1y = finalStartY + Math.sin(perpAngle) * curveOffset;
            cp2x = finalEndX + Math.cos(perpAngle) * curveOffset;
            cp2y = finalEndY + Math.sin(perpAngle) * curveOffset;
        
        this.ctx.moveTo(finalStartX, finalStartY);
        this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, finalEndX, finalEndY);
            }
        } else {
            // Curve mode disabled - draw straight line (static, no gravity)
            this.ctx.moveTo(finalStartX, finalStartY);
            this.ctx.lineTo(finalEndX, finalEndY);
        }
        
        // FIXED: Brighter links in dark mode
        let linkColor = link.color;
        if (this.darkMode && !isSelected) {
            // Brighten link color for dark mode (increase RGB values)
            linkColor = this.brightenColor(link.color, 1.4);
        }
        
        // ENHANCED: Instant visual feedback with glow on selection
        if (isSelected) {
            // Draw subtle glow effect
            this.ctx.shadowColor = '#3498db';
            this.ctx.shadowBlur = 6; // Reduced from 15 for subtler effect
            this.ctx.strokeStyle = '#3498db';
            this.ctx.lineWidth = 3; // Slightly thicker but not overwhelming
        } else {
            this.ctx.shadowBlur = 0;
            this.ctx.strokeStyle = linkColor;
            this.ctx.lineWidth = 2;
        }
        
        // CRITICAL: Use link's own style if set
        // If link has no style property (old links), default to 'solid' (not global style)
        // This ensures existing links don't change when global style changes
        const linkStyle = link.style !== undefined ? link.style : 'solid';
        
        // ENHANCED: Apply link style (solid, dashed, arrow)
        if (linkStyle === 'dashed') {
            this.ctx.setLineDash([8, 4]); // Dashed pattern
        } else {
            this.ctx.setLineDash([]); // Solid line
        }
        
        this.ctx.stroke();
        this.ctx.shadowBlur = 0; // Reset shadow for other elements
        this.ctx.setLineDash([]); // Reset dash
        
        // Draw arrowhead at end point (only if arrow style is selected)
        if (linkStyle === 'arrow') {
        // ENHANCED: Bigger, more eye-catching arrow
        const arrowLength = 16; // Increased from 10
        const arrowAngle = Math.PI / 5; // Slightly wider angle (36°)
        let finalEndAngle;
        
        if (curveEnabled && (cp1x !== undefined && cp2x !== undefined)) {
            // For curved lines, calculate angle from second control point to end
            finalEndAngle = Math.atan2(finalEndY - cp2y, finalEndX - cp2x);
        } else {
            // For straight lines, calculate angle from start to end
            finalEndAngle = Math.atan2(finalEndY - finalStartY, finalEndX - finalStartX);
        }
        
        // Draw filled arrowhead for better visibility
        this.ctx.beginPath();
        this.ctx.moveTo(finalEndX, finalEndY);
        this.ctx.lineTo(
            finalEndX - arrowLength * Math.cos(finalEndAngle - arrowAngle),
            finalEndY - arrowLength * Math.sin(finalEndAngle - arrowAngle)
        );
        this.ctx.lineTo(
            finalEndX - arrowLength * Math.cos(finalEndAngle + arrowAngle),
            finalEndY - arrowLength * Math.sin(finalEndAngle + arrowAngle)
        );
        this.ctx.closePath();
        this.ctx.fillStyle = isSelected ? '#3498db' : linkColor;
        this.ctx.fill();
        this.ctx.strokeStyle = isSelected ? '#2980b9' : '#333';
        this.ctx.lineWidth = 1.5;
        this.ctx.stroke();
        }
        
        // Selection highlight with dashed outline
        if (isSelected) {
            this.ctx.shadowBlur = 0; // No shadow for dashed outline
            this.ctx.strokeStyle = '#3498db';
            this.ctx.lineWidth = 1;
            this.ctx.setLineDash([3, 3]);
            this.ctx.beginPath();
            this.ctx.moveTo(finalStartX, finalStartY);
            
            if (curveEnabled && (cp1x !== undefined && cp2x !== undefined)) {
                // Bezier curve
            this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, finalEndX, finalEndY);
            } else {
                // Straight line
                this.ctx.lineTo(finalEndX, finalEndY);
            }
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }
        
        // DEBUG VIEW: Draw link type label above link
        if (this.showLinkTypeLabels) {
            const midX = (finalStartX + finalEndX) / 2;
            const midY = (finalStartY + finalEndY) / 2;
            
            this.ctx.save();
            this.ctx.font = `bold ${11 / this.zoom}px Arial`;
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'bottom';
            
            // Use originType to preserve link creation method
            const label = link.originType || 'QL';
            const padding = 3 / this.zoom;
            const metrics = this.ctx.measureText(label);
            const textWidth = metrics.width;
            const textHeight = 11 / this.zoom;
            
            // Green background for QLs (they never merge with ULs)
            this.ctx.fillStyle = 'rgba(46, 204, 113, 0.9)';
            this.ctx.fillRect(
                midX - textWidth / 2 - padding,
                midY - 18 / this.zoom - textHeight - padding,
                textWidth + padding * 2,
                textHeight + padding * 2
            );
            
            // Draw label text
            this.ctx.fillStyle = 'white';
            this.ctx.strokeStyle = '#27ae60';
            this.ctx.lineWidth = 0.5 / this.zoom;
            this.ctx.strokeText(label, midX, midY - 18 / this.zoom);
            this.ctx.fillText(label, midX, midY - 18 / this.zoom);
            
            this.ctx.restore();
        }
    }
    
    drawUnboundLink(link) {
        // ENHANCED: Check if this link is part of a merged chain - highlight ALL links in the chain
        let isSelected = this.selectedObject === link || this.selectedObjects.includes(link);
        
        // If not directly selected, check if ANY link in the merge chain is selected
        if (!isSelected) {
            const mergedLinks = this.getAllMergedLinks(link);
            for (const mergedLink of mergedLinks) {
                if (mergedLink !== link && (this.selectedObject === mergedLink || this.selectedObjects.includes(mergedLink))) {
                    isSelected = true;
                    break;
                }
            }
        }
        
        // CRITICAL: If endpoint is attached to a device, calculate position from device
        let startX, startY, endX, endY;
        
        // Positions are already updated in draw() with proper offsets
        // Just use the stored positions
                startX = link.start.x;
                startY = link.start.y;
        
        // Positions are already updated in draw() with proper offsets
        // Just use the stored positions
        endX = link.end.x;
        endY = link.end.y;
        
        // Determine if curve mode is enabled for this unbound link
        const curveEnabled = link.curveOverride !== undefined ? link.curveOverride : this.linkCurveMode;
        
        // Draw line (curved or straight)
        this.ctx.beginPath();
        let cp1x, cp1y, cp2x, cp2y;
        
        if (curveEnabled) {
            // Apply guitar string physics to unbound links too
            const obstacles = this.findAllObstaclesOnPath(startX, startY, endX, endY, link);
            
            if (obstacles.length > 0) {
                // Guitar string curve around obstacles
                const straightMidX = (startX + endX) / 2;
                const straightMidY = (startY + endY) / 2;
                const linkLength = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
                
                let totalRepulsionX = 0;
                let totalRepulsionY = 0;
                let closestObstacleRadius = 0;
                
                obstacles.forEach((obstacleInfo) => {
                    const obstacle = obstacleInfo.device;
                    const dx = straightMidX - obstacle.x;
                    const dy = straightMidY - obstacle.y;
                    const distToMid = Math.sqrt(dx * dx + dy * dy) || 1;
                    const minClearance = obstacle.radius + 18;
                    const repelDirX = dx / distToMid;
                    const repelDirY = dy / distToMid;
                    const k = minClearance * minClearance * this.magneticFieldStrength; // User-adjustable
                    const repulsionStrength = k / Math.pow(distToMid, 0.9); // Match drawing
                    totalRepulsionX += repelDirX * repulsionStrength;
                    totalRepulsionY += repelDirY * repulsionStrength;
                    closestObstacleRadius = Math.max(closestObstacleRadius, obstacle.radius);
                });
                
                const deflectionMag = Math.sqrt(totalRepulsionX * totalRepulsionX + totalRepulsionY * totalRepulsionY);
                const maxDeflection = Math.min(linkLength * 0.45, closestObstacleRadius * 2.5); // Match drawing
                const actualDeflection = Math.min(deflectionMag, maxDeflection);
                const normalizedRepulX = totalRepulsionX / (deflectionMag || 1);
                const normalizedRepulY = totalRepulsionY / (deflectionMag || 1);
                const deflectedMidX = straightMidX + normalizedRepulX * actualDeflection;
                const deflectedMidY = straightMidY + normalizedRepulY * actualDeflection;
                
                // Curvier control points for unbound links
                const controlWeight = 0.7; // Match drawing
                const midWeight = 1 - controlWeight;
                cp1x = startX * midWeight + deflectedMidX * controlWeight;
                cp1y = startY * midWeight + deflectedMidY * controlWeight;
                cp2x = endX * midWeight + deflectedMidX * controlWeight;
                cp2y = endY * midWeight + deflectedMidY * controlWeight;
                
                this.ctx.moveTo(startX, startY);
                this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
            } else {
                // No obstacles - straight line
        this.ctx.moveTo(startX, startY);
        this.ctx.lineTo(endX, endY);
            }
        } else {
            // Curve disabled - straight line
            this.ctx.moveTo(startX, startY);
            this.ctx.lineTo(endX, endY);
        }
        
        // FIXED: Brighter links in dark mode
        let linkColor = link.color;
        if (this.darkMode && !isSelected) {
            linkColor = this.brightenColor(link.color, 1.4);
        }
        
        // ENHANCED: Subtle glow effect on selection
        if (isSelected) {
            this.ctx.shadowColor = '#3498db';
            this.ctx.shadowBlur = 6; // Reduced from 15 for subtler effect
            this.ctx.strokeStyle = '#3498db';
            this.ctx.lineWidth = 3; // Slightly thicker but not overwhelming
        } else {
            this.ctx.shadowBlur = 0;
            this.ctx.strokeStyle = linkColor;
            this.ctx.lineWidth = 2;
        }
        
        // CRITICAL: Use link's own style if set
        // If link has no style property (old links), default to 'solid' (not global style)
        // This ensures existing links don't change when global style changes
        const linkStyle = link.style !== undefined ? link.style : 'solid';
        
        // ENHANCED: Apply link style (solid, dashed, arrow)
        if (linkStyle === 'dashed') {
            this.ctx.setLineDash([8, 4]); // Dashed pattern
        } else {
            this.ctx.setLineDash([]); // Solid line
        }
        
        this.ctx.stroke();
        this.ctx.shadowBlur = 0; // Reset shadow after drawing link
        this.ctx.setLineDash([]); // Reset dash
        
        // CRITICAL: Calculate arrow position once and use for both drawing and hiding TP
        // This ensures arrow tip IS the TP (no separate dot)
        let arrowAtStart = false;
        let arrowAtEnd = false;
        let arrowX, arrowY, arrowAngle;
        
        if (linkStyle === 'arrow') {
            // Determine which endpoint is the free TP (where arrow should be)
            let isStartFree = true;
            let isEndFree = true;
            
            // Check if start is attached to device
            const startAttached = link.device1 !== null && link.device1 !== undefined;
            // Check if end is attached to device
            const endAttached = link.device2 !== null && link.device2 !== undefined;
            
            // Check merge status to determine free endpoints
            if (link.mergedWith) {
                // This is a parent link
                const parentFreeEnd = link.mergedWith.parentFreeEnd;
                isStartFree = (parentFreeEnd === 'start');
                isEndFree = (parentFreeEnd === 'end');
            }
            
            // CRITICAL: If also a child (middle link), MUST check parent connection too
            if (link.mergedInto) {
                // This is a child link
                const parentLink = this.objects.find(o => o.id === link.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                    // If parent says we are NOT free at start, then we are not free
                    if (childFreeEnd !== 'start') isStartFree = false;
                    if (childFreeEnd !== 'end') isEndFree = false;
                } else {
                    // Orphaned child metadata? Assume free unless parent found
                }
            }
            
            // Finally apply device attachments
            if (startAttached) isStartFree = false;
            if (endAttached) isEndFree = false;
            
            // Determine arrow position (prefer end if both free, or whichever is free)
            if (isEndFree && !isStartFree) {
                // End is free, start is connected
                arrowAtEnd = true;
                arrowX = endX;
                arrowY = endY;
                if (curveEnabled && (cp1x !== undefined && cp2x !== undefined)) {
                    arrowAngle = Math.atan2(endY - cp2y, endX - cp2x);
                } else {
                    arrowAngle = Math.atan2(endY - startY, endX - startX);
                }
            } else if (isStartFree && !isEndFree) {
                // Start is free, end is connected
                arrowAtStart = true;
                arrowX = startX;
                arrowY = startY;
                if (curveEnabled && (cp1x !== undefined && cp2x !== undefined)) {
                    arrowAngle = Math.atan2(startY - cp1y, startX - cp1x) + Math.PI; // Reverse direction
                } else {
                    arrowAngle = Math.atan2(startY - endY, startX - endX) + Math.PI; // Reverse direction
                }
            } else {
                // Both free (not merged) - draw at end (default behavior)
                arrowAtEnd = true;
                arrowX = endX;
                arrowY = endY;
                if (curveEnabled && (cp1x !== undefined && cp2x !== undefined)) {
                    arrowAngle = Math.atan2(endY - cp2y, endX - cp2x);
                } else {
                    arrowAngle = Math.atan2(endY - startY, endX - startX);
                }
            }
            
            // ENHANCED: Bigger, more eye-catching arrow
            const arrowLength = 16; // Increased from 10
            const arrowAngleSpread = Math.PI / 5; // Slightly wider angle (36°)
            
            // Draw filled arrowhead for better visibility
            // CRITICAL: Arrow tip IS at the endpoint (arrowX, arrowY), so it IS the TP
            this.ctx.beginPath();
            this.ctx.moveTo(arrowX, arrowY);
            this.ctx.lineTo(
                arrowX - arrowLength * Math.cos(arrowAngle - arrowAngleSpread),
                arrowY - arrowLength * Math.sin(arrowAngle - arrowAngleSpread)
            );
            this.ctx.lineTo(
                arrowX - arrowLength * Math.cos(arrowAngle + arrowAngleSpread),
                arrowY - arrowLength * Math.sin(arrowAngle + arrowAngleSpread)
            );
            this.ctx.closePath();
            this.ctx.fillStyle = isSelected ? '#3498db' : linkColor;
            this.ctx.fill();
            this.ctx.strokeStyle = isSelected ? '#2980b9' : '#333';
            this.ctx.lineWidth = 1.5;
            this.ctx.stroke();
        }
        
        // Draw endpoints (circles) with visual distinction for attached endpoints
        // ENHANCED: Draw connection points for merged ULs as movable points
        // CRITICAL: If arrow style is used, don't draw TP circle at the arrow tip (arrow tip IS the TP)
        const endpointRadius = isSelected ? 6 : 4;
        const isStretching = this.stretchingLink === link;
        
        // Check if start endpoint is an MP (actual connection point where 2 TPs merged)
        // CRITICAL: Only the ACTUAL merge points should be MPs, not free endpoints!
        let startIsMP = false;
        
        // CRITICAL FIX: Middle links (have BOTH mergedInto AND mergedWith) have BOTH ends as MPs!
        if (link.mergedInto && link.mergedWith) {
            // This is a middle link in a chain - BOTH ends are MPs (neither is a free TP)
            startIsMP = true;
        }
        // Check if this is a parent link and start is the CONNECTED end (not the free end)
        else if (link.mergedWith && link.mergedWith.parentFreeEnd !== 'start') {
            startIsMP = true; // Start is where this link connects to its child (MP)
        }
        // Check if this is a child link and start is the CONNECTED end (not the free end)
        else if (link.mergedInto) {
            const parentLink = this.objects.find(o => o.id === link.mergedInto.parentId);
            if (parentLink && parentLink.mergedWith) {
                const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                if (childFreeEnd !== 'start') {
                    startIsMP = true; // Start is where this link connects to its parent (MP)
                }
            }
        }
        
        const startConnectedToUL = startIsMP;
        
        // Start endpoint - draw normally if NOT connected to another UL and NOT attached to device
        // CRITICAL: Skip drawing TP circle if arrow is at this endpoint OR if attached to device
        const startAttached = link.device1 !== null && link.device1 !== undefined;
        
        if (!startConnectedToUL && !arrowAtStart && !startAttached) {
        // Only draw TP if it's FREE (not attached to device, not merged)
        const startIsStretching = isStretching && this.stretchingEndpoint === 'start';
        const startNearDevice = startIsStretching && this._stretchingNearDevice;
        
        this.ctx.beginPath();
        this.ctx.arc(startX, startY, endpointRadius, 0, Math.PI * 2);
        // Orange/yellow when near device, blue for selected, gray for normal
        if (startNearDevice) {
            this.ctx.fillStyle = '#f39c12'; // Orange - ready to attach
        } else if (isSelected) {
            this.ctx.fillStyle = '#3498db'; // Blue - selected
        } else {
            this.ctx.fillStyle = '#666'; // Gray - normal
        }
        this.ctx.fill();
        this.ctx.strokeStyle = 'white';
        this.ctx.lineWidth = 1;
        this.ctx.stroke();
        
        // ENHANCED: Add TP numbering - POSITIONAL (TP-1 and TP-2 are current free ends)
        // For individual UL: show which endpoint (TP1=start, TP2=end)
        // For BUL: TP-1 and TP-2 are the 2 current free endpoints
        const allLinks = this.getAllMergedLinks(link);
        const isBUL = allLinks.length > 1;
        
        if (isBUL) {
            // Find the 2 TPs in the BUL and number them positionally
            // TP-1 and TP-2 are the current free endpoints (can change as BUL grows)
            let tpNumber = 0;
            
            // Collect all TPs in the BUL with their link IDs
            // FIXED: Use clearer logic - endpoint is TP if NOT connected via mergedWith or mergedInto
            const tpsInBUL = [];
            for (const chainLink of allLinks) {
                // Check start - is it connected?
                let startIsConnected = false;
                // Via mergedWith: parentFreeEnd='end' means end is free, so start is connected
                if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') {
                    startIsConnected = true;
                }
                // Via mergedInto: childFreeEnd='end' means end is free, so start is connected
                if (chainLink.mergedInto) {
                    const parent = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                    if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'end') {
                        startIsConnected = true;
                    }
                }
                if (!startIsConnected) {
                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start', link: chainLink });
                }
                
                // Check end - is it connected?
                let endIsConnected = false;
                // Via mergedWith: parentFreeEnd='start' means start is free, so end is connected
                if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') {
                    endIsConnected = true;
                }
                // Via mergedInto: childFreeEnd='start' means start is free, so end is connected
                if (chainLink.mergedInto) {
                    const parent = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                    if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'start') {
                        endIsConnected = true;
                    }
                }
                if (!endIsConnected) {
                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end', link: chainLink });
                }
            }
            
            // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
            tpsInBUL.sort((a, b) => {
                const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                return ulNumA - ulNumB;
            });
            
            // Number TPs: TP-1 on lowest UL number, TP-2 on highest UL number
            // CRITICAL: Find index based on BOTH linkId AND endpoint
            const tpIndex = tpsInBUL.findIndex(tp => tp.linkId === link.id && tp.endpoint === 'start');
            tpNumber = (tpIndex >= 0) ? tpIndex + 1 : 0;
            
            // VALIDATION: If tpNumber is 0, this TP wasn't found in the list (BUG!)
            if (tpNumber === 0 && this.debugger) {
                this.debugger.logError(`❌ TP not found in BUL list! Link: ${link.id}, endpoint: start`);
                this.debugger.logInfo(`   TPs in BUL: ${JSON.stringify(tpsInBUL.map(tp => ({id: tp.linkId, ep: tp.endpoint})))}`);
            }
            
            // Draw TP number with UL identification
            const ulNumber = allLinks.findIndex(l => l.id === link.id) + 1;
            this.ctx.save();
            this.ctx.font = `bold ${8 / this.zoom}px Arial`;
            this.ctx.fillStyle = 'white';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(`${tpNumber}`, startX, startY);
            // Show which UL this TP belongs to
            this.ctx.font = `${6 / this.zoom}px Arial`;
            this.ctx.fillText(`U${ulNumber}`, startX, startY + 10 / this.zoom);
            this.ctx.restore();
        } else {
            // Individual UL - show which endpoint (1=start, 2=end)
            this.ctx.save();
            this.ctx.font = `bold ${7 / this.zoom}px Arial`;
            this.ctx.fillStyle = 'white';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText('1', startX, startY);
            this.ctx.restore();
        }
        }
        
        // Check if end endpoint is an MP (actual connection point where 2 TPs merged)
        // CRITICAL: Only the ACTUAL merge points should be MPs, not free endpoints!
        let endIsMP = false;
        
        // CRITICAL FIX: Middle links (have BOTH mergedInto AND mergedWith) have BOTH ends as MPs!
        if (link.mergedInto && link.mergedWith) {
            // This is a middle link in a chain - BOTH ends are MPs (neither is a free TP)
            endIsMP = true;
        }
        // Check if this is a parent link and end is the CONNECTED end (not the free end)
        else if (link.mergedWith && link.mergedWith.parentFreeEnd !== 'end') {
            endIsMP = true; // End is where this link connects to its child (MP)
        }
        // Check if this is a child link and end is the CONNECTED end (not the free end)
        else if (link.mergedInto) {
            const parentLink = this.objects.find(o => o.id === link.mergedInto.parentId);
            if (parentLink && parentLink.mergedWith) {
                const childFreeEnd = parentLink.mergedWith.childFreeEnd;
                if (childFreeEnd !== 'end') {
                    endIsMP = true; // End is where this link connects to its parent (MP)
                }
            }
        }
        
        const endConnectedToUL = endIsMP;
        
        // End endpoint - draw normally if NOT connected to another UL and NOT attached to device
        // CRITICAL: Skip drawing TP circle if arrow is at this endpoint OR if attached to device
        const endAttached = link.device2 !== null && link.device2 !== undefined;
        
        if (!endConnectedToUL && !arrowAtEnd && !endAttached) {
        // Only draw TP if it's FREE (not attached to device, not merged)
        const endIsStretching = isStretching && this.stretchingEndpoint === 'end';
        const endNearDevice = endIsStretching && this._stretchingNearDevice;
        
        this.ctx.beginPath();
        this.ctx.arc(endX, endY, endpointRadius, 0, Math.PI * 2);
        // Orange/yellow when near device, blue for selected, gray for normal
        if (endNearDevice) {
            this.ctx.fillStyle = '#f39c12'; // Orange - ready to attach
        } else if (isSelected) {
            this.ctx.fillStyle = '#3498db'; // Blue - selected
        } else {
            this.ctx.fillStyle = '#666'; // Gray - normal
        }
        this.ctx.fill();
        this.ctx.strokeStyle = 'white';
        this.ctx.lineWidth = 1;
        this.ctx.stroke();
        
        // ENHANCED: Add TP numbering - POSITIONAL (TP-1 and TP-2 are current free ends)
        const allLinks = this.getAllMergedLinks(link);
        const isBUL = allLinks.length > 1;
        
        if (isBUL) {
            // Find the 2 TPs in the BUL and number them positionally
            let tpNumber = 0;
            
            // Collect all TPs in the BUL
            // FIXED: Use clearer logic - endpoint is TP if NOT connected via mergedWith or mergedInto
            const tpsInBUL = [];
            for (const chainLink of allLinks) {
                // Check start - is it connected?
                let startIsConnected = false;
                if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') {
                    startIsConnected = true;
                }
                if (chainLink.mergedInto) {
                    const parent = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                    if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'end') {
                        startIsConnected = true;
                    }
                }
                if (!startIsConnected) {
                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start', link: chainLink });
                }
                
                // Check end - is it connected?
                let endIsConnected = false;
                if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') {
                    endIsConnected = true;
                }
                if (chainLink.mergedInto) {
                    const parent = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                    if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'start') {
                        endIsConnected = true;
                    }
                }
                if (!endIsConnected) {
                    tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end', link: chainLink });
                }
            }
            
            // FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
            tpsInBUL.sort((a, b) => {
                const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
                const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
                return ulNumA - ulNumB;
            });
            
            // Number TPs: TP-1 on lowest UL number, TP-2 on highest UL number
            // CRITICAL: Find index based on BOTH linkId AND endpoint
            const tpIndex = tpsInBUL.findIndex(tp => tp.linkId === link.id && tp.endpoint === 'end');
            tpNumber = (tpIndex >= 0) ? tpIndex + 1 : 0;
            
            // VALIDATION: If tpNumber is 0, this TP wasn't found in the list (BUG!)
            if (tpNumber === 0 && this.debugger) {
                this.debugger.logError(`❌ TP not found in BUL list! Link: ${link.id}, endpoint: end`);
                this.debugger.logInfo(`   TPs in BUL: ${JSON.stringify(tpsInBUL.map(tp => ({id: tp.linkId, ep: tp.endpoint})))}`);
            }
            
            // Draw TP number with UL identification
            const ulNumber = allLinks.findIndex(l => l.id === link.id) + 1;
            this.ctx.save();
            this.ctx.font = `bold ${8 / this.zoom}px Arial`;
            this.ctx.fillStyle = 'white';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(`${tpNumber}`, endX, endY);
            // Show which UL this TP belongs to
            this.ctx.font = `${6 / this.zoom}px Arial`;
            this.ctx.fillText(`U${ulNumber}`, endX, endY + 10 / this.zoom);
            this.ctx.restore();
        } else {
            // Individual UL - show which endpoint (1=start, 2=end)
            this.ctx.save();
            this.ctx.font = `bold ${7 / this.zoom}px Arial`;
            this.ctx.fillStyle = 'white';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText('2', endX, endY);
            this.ctx.restore();
        }
        }
        
        // ENHANCED: Draw MPs (merge points) - small purple dots showing where ULs connect
        // BUL chain structure: TP--MP--MP--MP--TP (2 TPs at ends, N-1 MPs for N links)
        
        // Draw MP at start if it's a merge point (NOT attached to device, NOT arrow tip)
        if (startIsMP && !startAttached && !arrowAtStart) {
            const mpRadius = isSelected ? 5 / this.zoom : 4 / this.zoom; // Slightly bigger when selected
            this.ctx.beginPath();
            this.ctx.arc(startX, startY, mpRadius, 0, Math.PI * 2);
            this.ctx.fillStyle = isSelected ? '#c04cb6' : '#9b59b6'; // Brighter purple when selected
            this.ctx.fill();
            this.ctx.strokeStyle = isSelected ? '#a83ca3' : '#8e44ad'; // Darker purple outline
            this.ctx.lineWidth = 2 / this.zoom;
            this.ctx.stroke();
            
            // ENHANCED: Add MP numbering based on CREATION ORDER
            // MPs are numbered by when they were created (MP-1, MP-2, MP-3...)
            const allLinks = this.getAllMergedLinks(link);
            if (allLinks.length > 1) {
                let mpNumber = 0;
                
                // Find which MP this is (at link's start)
                // Check if this link is the parent (mergedWith) and start is the connected end
                if (link.mergedWith) {
                    const parentConnectedEnd = link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                    if (parentConnectedEnd === 'start') {
                        // This MP is at this link's start
                        mpNumber = link.mergedWith.mpNumber || 0;
                    }
                }
                // Check if this link is a child (mergedInto) and start is where it connects
                if (link.mergedInto && mpNumber === 0) { // Only if not already found as parent
                    const parent = this.objects.find(o => o.id === link.mergedInto.parentId);
                    if (parent?.mergedWith) {
                        const childConnectedEnd = parent.mergedWith.childConnectionEndpoint ||
                            (parent.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                        if (childConnectedEnd === 'start') {
                            // This MP is at this link's start
                            mpNumber = parent.mergedWith.mpNumber || 0;
                        }
                    }
                }
                
                // Draw MP number with connected UL information
                const ulNumber = allLinks.findIndex(l => l.id === link.id) + 1;
                this.ctx.save();
                this.ctx.font = `bold ${7 / this.zoom}px Arial`;
                this.ctx.fillStyle = 'white';
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(`${mpNumber}`, startX, startY);
                // Show which UL this MP is on
                this.ctx.font = `${6 / this.zoom}px Arial`;
                this.ctx.fillText(`U${ulNumber}`, startX, startY + 10 / this.zoom);
                this.ctx.restore();
            }
        }
        
        // Draw MP at end if it's a merge point (NOT attached to device, NOT arrow tip)
        if (endIsMP && !endAttached && !arrowAtEnd) {
            const mpRadius = isSelected ? 5 / this.zoom : 4 / this.zoom; // Slightly bigger when selected
            this.ctx.beginPath();
            this.ctx.arc(endX, endY, mpRadius, 0, Math.PI * 2);
            this.ctx.fillStyle = isSelected ? '#c04cb6' : '#9b59b6'; // Brighter purple when selected
            this.ctx.fill();
            this.ctx.strokeStyle = isSelected ? '#a83ca3' : '#8e44ad'; // Darker purple outline
            this.ctx.lineWidth = 2 / this.zoom;
            this.ctx.stroke();
            
            // ENHANCED: Add MP numbering based on CREATION ORDER
            // MPs are numbered by when they were created (MP-1, MP-2, MP-3...)
            const allLinks = this.getAllMergedLinks(link);
            if (allLinks.length > 1) {
                let mpNumber = 0;
                
                // Find which MP this is (at link's end)
                // Check if this link is the parent (mergedWith) and end is the connected end
                if (link.mergedWith) {
                    const parentConnectedEnd = link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                    if (parentConnectedEnd === 'end') {
                        // This MP is at this link's end
                        mpNumber = link.mergedWith.mpNumber || 0;
                    }
                }
                // Check if this link is a child (mergedInto) and end is where it connects
                if (link.mergedInto && mpNumber === 0) { // Only if not already found as parent
                    const parent = this.objects.find(o => o.id === link.mergedInto.parentId);
                    if (parent?.mergedWith) {
                        const childConnectedEnd = parent.mergedWith.childConnectionEndpoint ||
                            (parent.mergedWith.childFreeEnd === 'start' ? 'end' : 'start');
                        if (childConnectedEnd === 'end') {
                            // This MP is at this link's end
                            mpNumber = parent.mergedWith.mpNumber || 0;
                        }
                    }
                }
                
                // Draw MP number with connected UL information
                const ulNumber = allLinks.findIndex(l => l.id === link.id) + 1;
                this.ctx.save();
                this.ctx.font = `bold ${7 / this.zoom}px Arial`;
                this.ctx.fillStyle = 'white';
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(`${mpNumber}`, endX, endY);
                // Show which UL this MP is on
                this.ctx.font = `${6 / this.zoom}px Arial`;
                this.ctx.fillText(`U${ulNumber}`, endX, endY + 10 / this.zoom);
                this.ctx.restore();
            }
        }
        
        // Draw visual feedback: highlight nearby device when stretching
        if (isStretching && this._stretchingNearDevice) {
            const device = this._stretchingNearDevice;
            // Draw pulsing highlight ring around device
            this.ctx.beginPath();
            this.ctx.arc(device.x, device.y, device.radius + 8, 0, Math.PI * 2);
            this.ctx.strokeStyle = '#f39c12';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([4, 4]);
            this.ctx.stroke();
            this.ctx.setLineDash([]);
            
            // Draw connection preview line
            const previewEndpoint = this.stretchingEndpoint === 'start' 
                ? { x: startX, y: startY }
                : { x: endX, y: endY };
            this.ctx.beginPath();
            this.ctx.moveTo(device.x, device.y);
            this.ctx.lineTo(previewEndpoint.x, previewEndpoint.y);
            this.ctx.strokeStyle = 'rgba(243, 156, 18, 0.4)';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([3, 3]);
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }
        
        // Selection highlight
        if (isSelected) {
            this.ctx.strokeStyle = '#3498db';
            this.ctx.lineWidth = 1;
            this.ctx.setLineDash([3, 3]);
            this.ctx.beginPath();
            this.ctx.moveTo(startX, startY);
            if (curveEnabled && cp1x !== undefined) {
                this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
            } else {
            this.ctx.lineTo(endX, endY);
            }
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }
        
        // DEBUG VIEW: Draw link type label above UL/BUL
        if (this.showLinkTypeLabels) {
            const midX = (startX + endX) / 2;
            const midY = (startY + endY) / 2;
            
            this.ctx.save();
            this.ctx.font = `bold ${11 / this.zoom}px Arial`;
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'bottom';
            
            // ENHANCED: Show origin type + creation order in BUL
            const originType = link.originType || 'UL'; // Preserve original type
            let label = originType; // Base label
            let bgColor = 'rgba(52, 152, 219, 0.9)'; // Blue background (single UL)
            let strokeColor = '#2980b9';
            
            // Add merge status and creation order
            if (link.mergedWith || link.mergedInto) {
                // Get all links in the BUL chain
                const allMergedLinks = this.getAllMergedLinks(link);
                
                // Sort by creation time to determine order
                const sortedByCreation = allMergedLinks.sort((a, b) => {
                    const aTime = a.createdAt || 0;
                    const bTime = b.createdAt || 0;
                    return aTime - bTime;
                });
                
                // Find this link's position in creation order
                const creationOrder = sortedByCreation.findIndex(l => l.id === link.id) + 1;
                
                // Show origin type + creation order number
                label = `${originType}${creationOrder}`;
                bgColor = 'rgba(155, 89, 182, 0.9)'; // Purple background (indicates part of BUL)
                strokeColor = '#8e44ad';
            }
            
            const padding = 3 / this.zoom;
            const metrics = this.ctx.measureText(label);
            const textWidth = metrics.width;
            const textHeight = 11 / this.zoom;
            
            // Draw background
            this.ctx.fillStyle = bgColor;
            this.ctx.fillRect(
                midX - textWidth / 2 - padding,
                midY - 18 / this.zoom - textHeight - padding,
                textWidth + padding * 2,
                textHeight + padding * 2
            );
            
            // Draw label text
            this.ctx.fillStyle = 'white';
            this.ctx.strokeStyle = strokeColor;
            this.ctx.lineWidth = 0.5 / this.zoom;
            this.ctx.strokeText(label, midX, midY - 18 / this.zoom);
            this.ctx.fillText(label, midX, midY - 18 / this.zoom);
            
            this.ctx.restore();
        }
    }
    
    drawText(text) {
        const isSelected = this.selectedObject === text || this.selectedObjects.includes(text);
        
        this.ctx.save();
        this.ctx.translate(text.x, text.y);
        this.ctx.rotate(text.rotation * Math.PI / 180);
        
        this.ctx.font = `${text.fontSize}px Arial`;
        this.ctx.fillStyle = text.color;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(text.text || 'Text', 0, 0);
        
        if (isSelected && this.currentMode === 'select') {
            const metrics = this.ctx.measureText(text.text || 'Text');
            const w = metrics.width;
            const h = parseInt(text.fontSize);
            this.ctx.strokeStyle = '#3498db';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([5, 5]);
            this.ctx.strokeRect(-w/2 - 5, -h/2 - 5, w + 10, h + 10);
            this.ctx.setLineDash([]);
            
            // ADAPTIVE: Calculate dot size based on text dimensions
            const textDiagonal = Math.sqrt(w * w + h * h);
            const dotSize = Math.max(8, Math.min(15, textDiagonal / 15)); // 8-15px range
            
            // Draw corner handles for size control
            const corners = [
                { x: -w/2 - 5, y: -h/2 - 5, type: 'resize' },  // Top-left
                { x: w/2 + 5, y: -h/2 - 5, type: 'rotation' },  // Top-right (rotation)
                { x: w/2 + 5, y: h/2 + 5, type: 'resize' },     // Bottom-right
                { x: -w/2 - 5, y: h/2 + 5, type: 'resize' }     // Bottom-left
            ];
            
            corners.forEach(corner => {
                if (corner.type === 'rotation') {
                    // ENHANCED: Draw arc meter around rotation handle
                    const rotationRadians = text.rotation * Math.PI / 180;
                    const arcRadius = dotSize + 6;
                    
                    // Draw background circle (light gray)
                    this.ctx.beginPath();
                    this.ctx.arc(corner.x, corner.y, arcRadius, 0, Math.PI * 2);
                    this.ctx.strokeStyle = 'rgba(200, 200, 200, 0.3)';
                    this.ctx.lineWidth = 3;
                    this.ctx.stroke();
                    
                    // Draw arc from 0° to current rotation
                    this.ctx.beginPath();
                    this.ctx.arc(corner.x, corner.y, arcRadius, 0, rotationRadians);
                    this.ctx.strokeStyle = '#27ae60';
                    this.ctx.lineWidth = 3;
                    this.ctx.stroke();
                    
                    // Draw rotation handle dot
                    this.ctx.beginPath();
                    this.ctx.arc(corner.x, corner.y, dotSize, 0, Math.PI * 2);
                    this.ctx.fillStyle = '#27ae60';
                    this.ctx.fill();
                    this.ctx.strokeStyle = 'white';
                    this.ctx.lineWidth = 2;
                    this.ctx.stroke();
                } else {
                    // Resize handles - Blue with adaptive size
                    this.ctx.beginPath();
                    this.ctx.arc(corner.x, corner.y, dotSize, 0, Math.PI * 2);
                    this.ctx.fillStyle = '#3498db';
                    this.ctx.fill();
                    this.ctx.strokeStyle = 'white';
                    this.ctx.lineWidth = 2;
                    this.ctx.stroke();
                }
            });
        }
        
        this.ctx.restore();
        
        // NEW: Draw Angle Meter if enabled - rotates with text for cleaner UI
        if (isSelected && this.currentMode === 'select' && this.showAngleMeter) {
            // ENHANCED: Use +/- format (-180 to +180)
            let degrees = Math.round(text.rotation || 0) % 360;
            // Normalize to -180 to +180 range
            if (degrees > 180) degrees -= 360;
            if (degrees < -180) degrees += 360;
            const normalizedDegrees = degrees;
            
            // Calculate position of rotation handle in world space
            this.ctx.save();
            this.ctx.font = `${text.fontSize}px Arial`;
            const metrics = this.ctx.measureText(text.text || 'Text');
            const w = metrics.width;
            const h = parseInt(text.fontSize);
            this.ctx.restore();
            
            const angle = text.rotation * Math.PI / 180;
            
            // Top-right corner in local space (rotation handle position)
            const localX = w/2 + 5;
            const localY = -h/2 - 5;
            
            // Rotate to world space to get handle position
            const handleX = text.x + (localX * Math.cos(angle) - localY * Math.sin(angle));
            const handleY = text.y + (localX * Math.sin(angle) + localY * Math.cos(angle));
            
            // Calculate angle from text center to handle
            const handleAngle = Math.atan2(handleY - text.y, handleX - text.x);
            const labelOffsetDist = 25 / this.zoom;
            const labelX = handleX + Math.cos(handleAngle) * labelOffsetDist;
            const labelY = handleY + Math.sin(handleAngle) * labelOffsetDist;
            
            this.ctx.save();
            this.ctx.translate(labelX, labelY);
            
            // ENHANCED: Align label with text rotation for cleaner look
            const shouldAlignWithText = Math.abs(degrees % 180) > 15 && Math.abs(degrees % 180) < 165;
            if (shouldAlignWithText) {
                this.ctx.rotate(angle);
            }
            
            const labelText = normalizedDegrees >= 0 ? `+${normalizedDegrees}°` : `${normalizedDegrees}°`;
            this.ctx.font = `bold ${11 / this.zoom}px Arial`;
            const textMetrics = this.ctx.measureText(labelText);
            
            const bgPad = 5 / this.zoom;
            const bgW = textMetrics.width + bgPad * 2;
            const bgH = 16 / this.zoom;
            const radius = 4 / this.zoom;
            
            // Shadow for depth
            this.ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
            this.ctx.shadowBlur = 6 / this.zoom;
            this.ctx.shadowOffsetX = 1 / this.zoom;
            this.ctx.shadowOffsetY = 2 / this.zoom;
            
            // Gradient background
            const gradient = this.ctx.createLinearGradient(-bgW/2, -bgH/2, -bgW/2, bgH/2);
            gradient.addColorStop(0, 'rgba(46, 204, 113, 1)');
            gradient.addColorStop(1, 'rgba(39, 174, 96, 1)');
            
            // Rounded rectangle
            this.ctx.beginPath();
            this.ctx.moveTo(-bgW/2 + radius, -bgH/2);
            this.ctx.lineTo(bgW/2 - radius, -bgH/2);
            this.ctx.arcTo(bgW/2, -bgH/2, bgW/2, -bgH/2 + radius, radius);
            this.ctx.lineTo(bgW/2, bgH/2 - radius);
            this.ctx.arcTo(bgW/2, bgH/2, bgW/2 - radius, bgH/2, radius);
            this.ctx.lineTo(-bgW/2 + radius, bgH/2);
            this.ctx.arcTo(-bgW/2, bgH/2, -bgW/2, bgH/2 - radius, radius);
            this.ctx.lineTo(-bgW/2, -bgH/2 + radius);
            this.ctx.arcTo(-bgW/2, -bgH/2, -bgW/2 + radius, -bgH/2, radius);
            this.ctx.closePath();
            this.ctx.fillStyle = gradient;
            this.ctx.fill();
            
            // Subtle border
            this.ctx.shadowColor = 'transparent';
            this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
            this.ctx.lineWidth = 1.5 / this.zoom;
            this.ctx.stroke();
            
            // Text with shadow
            this.ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
            this.ctx.shadowBlur = 1 / this.zoom;
            this.ctx.shadowOffsetY = 1 / this.zoom;
            this.ctx.fillStyle = '#ffffff';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(labelText, 0, 0);
        
        this.ctx.restore();
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
        }, 100); // Very short delay - feels instant to user
    }
    
    autoSave() {
        if (this.initializing) return;
        // Never overwrite an existing save with an empty topology
        if (!Array.isArray(this.objects) || this.objects.length === 0) {
            console.warn('Auto-save skipped: empty topology');
            return;
        }
        try {
            console.log('=== AUTO-SAVE START ===');
            console.log('Auto-saving topology with', this.objects.length, 'objects...');
            console.log('Objects being saved:', this.objects);
            const data = {
                version: '1.0',
                // Preserve link geometry so reload can render immediately without recomputation
                objects: this.objects.map(obj => ({ ...obj })),
                metadata: {
                    deviceIdCounter: this.deviceIdCounter,
                    linkIdCounter: this.linkIdCounter,
                    textIdCounter: this.textIdCounter,
                    deviceCounters: this.deviceCounters,
                    linkCurveMode: this.linkCurveMode,
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
            console.log('Auto-save data size:', jsonData.length, 'characters');
            localStorage.setItem('topology_autosave', jsonData);
            console.log('Auto-save completed successfully');
        } catch (error) {
            console.error('Auto-save failed:', error);
            console.error('Error details:', error.stack);
            // Don't alert - auto-save failures shouldn't interrupt workflow
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
                    this.objects = data.objects;
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
                });

                // IMPORTANT: Link positions will be calculated dynamically by draw()
                // based on device positions and linkIndex - no need to set them here
                // This ensures links stay properly connected and offset even after refresh

                this.deviceIdCounter = data.metadata?.deviceIdCounter || 0;
                this.linkIdCounter = data.metadata?.linkIdCounter || 0;
                this.textIdCounter = data.metadata?.textIdCounter || 0;
                this.deviceCounters = data.metadata?.deviceCounters || { router: 0, switch: 0 };

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
                            if (statusText) statusText.textContent = 'Collision: ON';
                            // Update icon to show separated circles
                            if (svg) {
                                svg.innerHTML = `
                                    <circle cx="8" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
                                    <circle cx="16" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
                                `;
                            }
                        } else {
                            btn.classList.remove('active');
                            btn.title = 'Collision OFF - Devices Can Overlap';
                            if (statusText) statusText.textContent = 'Collision: OFF';
                            // Update icon to show overlapping circles
                            if (svg) {
                                svg.innerHTML = `
                                    <circle cx="9" cy="12" r="5" stroke="currentColor" stroke-width="2" fill="none"/>
                                    <circle cx="15" cy="12" r="5" stroke="currentColor" stroke-width="2" fill="none"/>
                                `;
                            }
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
                            if (statusText) statusText.textContent = 'Movable: ON';
                        } else {
                            btn.classList.remove('active');
                            btn.title = 'Movable OFF - Devices Are Static';
                            if (statusText) statusText.textContent = 'Movable: OFF';
                        }
                    }
                }
                if (data.metadata?.magneticFieldStrength !== undefined) {
                    this.magneticFieldStrength = data.metadata.magneticFieldStrength;
                    document.getElementById('magnetic-field-value').textContent = this.magneticFieldStrength;
                    document.getElementById('magnetic-field-slider').value = this.magneticFieldStrength;
                }
                if (data.metadata?.gridZoomEnabled !== undefined) {
                    this.gridZoomEnabled = data.metadata.gridZoomEnabled;
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
                        } else if (this.linkStyle === 'dashed') {
                            dashedBtn.classList.add('active');
                        } else if (this.linkStyle === 'arrow') {
                            arrowBtn.classList.add('active');
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
    
    saveTopology() {
        const data = {
            version: '1.0',
            objects: this.objects.map(obj => {
                const copy = { ...obj };
                // All links are now 'unbound' with TPs - no need to remove start/end
                return copy;
            }),
            metadata: {
                deviceIdCounter: this.deviceIdCounter,
                linkIdCounter: this.linkIdCounter,
                textIdCounter: this.textIdCounter,
                linkCurveMode: this.linkCurveMode,
                linkContinuousMode: this.linkContinuousMode,
                linkStyle: this.linkStyle,
                showLinkTypeLabels: this.showLinkTypeLabels,
                deviceNumbering: this.deviceNumbering,
                deviceCollision: this.deviceCollision,
                movableDevices: this.movableDevices,
                magneticFieldStrength: this.magneticFieldStrength,
                gridZoomEnabled: this.gridZoomEnabled
            }
        };
        
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `topology_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    loadTopology(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                
                this.objects = data.objects || [];
                
                // Add missing properties for compatibility with old saves
                this.objects.forEach(obj => {
                    if (obj.type === 'device' && !obj.label) {
                        obj.label = obj.deviceType === 'router' ? 'NCP' : 'S';
                    }
                    // Ensure all links have a style property
                    if ((obj.type === 'link' || obj.type === 'unbound') && !obj.style) {
                        obj.style = 'solid';
                    }
                });
                
                this.deviceIdCounter = data.metadata?.deviceIdCounter || 0;
                this.linkIdCounter = data.metadata?.linkIdCounter || 0;
                this.textIdCounter = data.metadata?.textIdCounter || 0;
                
                // Restore link curve mode if saved
                if (data.metadata?.linkCurveMode !== undefined) {
                    this.linkCurveMode = data.metadata.linkCurveMode;
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
                
                // Restore continuous linking mode if saved
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
                
                // Recalculate device counters based on loaded devices
                this.updateDeviceCounters();
                
                this.selectedObject = null;
                this.selectedObjects = [];
                
                // Reset and save history after loading
                this.history = [];
                this.historyIndex = -1;
                this.saveState();
                this.updateUndoRedoButtons();
                
                this.updatePropertiesPanel();
                this.draw();
                
                alert('Topology loaded successfully!');
            } catch (error) {
                alert('Error loading topology: ' + error.message);
            }
        };
        reader.readAsText(file);
        
        // Reset file input
        event.target.value = '';
    }
}

// Initialize the editor when page loads
window.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('topology-canvas');
    const editor = new TopologyEditor(canvas);
    
    // Make editor globally accessible for debugging
    window.topologyEditor = editor;
    
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
        const saved = localStorage.getItem('topology_autosave');
        console.log('=== AUTO-SAVE CHECK ===');
        console.log('Data exists:', !!saved);
        console.log('Data length:', saved ? saved.length : 0);
        if (saved) {
            try {
                const data = JSON.parse(saved);
                console.log('Objects in save:', data.objects?.length || 0);
                console.log('Full data:', data);
            } catch (e) {
                console.error('Parse error:', e);
            }
        }
        console.log('Current editor objects:', editor.objects.length);
        return saved;
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
    
    // Helper to manually sync all toggle buttons if they get out of sync
    window.syncToggles = () => {
        console.log('🔄 Syncing all toggle buttons...');
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
    
    console.log('Topology Editor initialized.');
    console.log('Commands: window.checkAutoSave() | window.checkHistory() | window.syncToggles() | window.checkModes()');
    console.log('Toggle debugger: Press D key or click Hide/Show button');
    
    // ============================================================================
    // DRAGGABLE MODALS - Make all modals draggable and resizable
    // ============================================================================
    
    function makeDraggableModal(modalContent) {
        const header = modalContent.querySelector('.draggable-header');
        if (!header) {
            console.warn('⚠️ No draggable header found in modal');
            return;
        }
        
        console.log('✓ Setting up draggable modal with header:', header);
        
        let isDragging = false;
        let offsetX = 0;
        let offsetY = 0;
        let hasMoved = false; // Track if modal has been manually positioned
        
        // Ensure header has proper cursor
        header.style.cursor = 'move';
        
        // Reset to centered position when modal opens
        const parentModal = modalContent.closest('.modal');
        if (parentModal) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.attributeName === 'style' || mutation.attributeName === 'class') {
                        const isVisible = parentModal.style.display !== 'none' && 
                                        (parentModal.classList.contains('show') || parentModal.style.display === 'flex');
                        
                        if (isVisible && !hasMoved) {
                            // Reset to centered on open (if not manually positioned)
                            modalContent.style.position = 'relative';
                            modalContent.style.left = '';
                            modalContent.style.top = '';
                            modalContent.style.transform = '';
                        }
                    }
                });
            });
            observer.observe(parentModal, { attributes: true });
        }
        
        header.addEventListener('mousedown', (e) => {
            console.log('🖐️ Header mousedown, target:', e.target.tagName, 'class:', e.target.className);
            
            // Don't drag when clicking buttons or any interactive elements
            if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                console.log('❌ Blocked: Button click');
                return;
            }
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
                console.log('❌ Blocked: Input element');
                return;
            }
            
            // ENHANCED: Allow dragging from anywhere in header except close buttons
            // This makes it much easier to grab the window
            console.log('✅ Drag allowed, starting...');
            
            // CRITICAL FIX: If modal is centered (relative position), convert to fixed FIRST
            const currentPosition = window.getComputedStyle(modalContent).position;
            if (currentPosition === 'relative' || modalContent.style.position === 'relative' || !modalContent.style.left) {
                // Modal is centered - convert to fixed at current screen position
                const rect = modalContent.getBoundingClientRect();
                modalContent.style.position = 'fixed';
                modalContent.style.left = rect.left + 'px';
                modalContent.style.top = rect.top + 'px';
                modalContent.style.transform = 'none';
                modalContent.style.margin = '0'; // Remove any margin
                console.log('📐 Converted to fixed position');
            }
            
            // NOW capture offset after position is fixed
            const rect = modalContent.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            
            console.log('🔍 Modal Drag Start:', {
                modalAt: `(${rect.left.toFixed(1)}, ${rect.top.toFixed(1)})`,
                mouseAt: `(${e.clientX}, ${e.clientY})`,
                offset: `(${offsetX.toFixed(1)}, ${offsetY.toFixed(1)})`,
                position: modalContent.style.position
            });
            
            isDragging = true;
            window._linkModalDragging = true; // Track for backdrop click prevention
            hasMoved = true; // Mark as manually positioned
            header.style.cursor = 'grabbing';
            document.body.style.userSelect = 'none'; // Prevent text selection
            e.preventDefault();
            e.stopPropagation();
        });
        
        let dragMoveCount = 0;
        
        const mouseMoveHandler = (e) => {
            if (!isDragging) return;
            e.preventDefault();
            
            // Log every 10th move to avoid spam
            if (dragMoveCount % 10 === 0) {
                console.log('🚚 Dragging modal...', { mouseX: e.clientX, mouseY: e.clientY });
            }
            dragMoveCount++;
            
            // LOCKED ALGORITHM: newPosition = mousePosition - offset
            // This is the ONLY calculation - no deltas, no start positions
            let newLeft = e.clientX - offsetX;
            let newTop = e.clientY - offsetY;
            
            // Keep modal within viewport
            const modalWidth = modalContent.offsetWidth;
            const modalHeight = modalContent.offsetHeight;
            newLeft = Math.max(0, Math.min(newLeft, window.innerWidth - modalWidth));
            newTop = Math.max(0, Math.min(newTop, window.innerHeight - modalHeight));
            
            // Apply positioning
            modalContent.style.position = 'fixed';
            modalContent.style.left = newLeft + 'px';
            modalContent.style.top = newTop + 'px';
            modalContent.style.transform = 'none'; // Remove centering transform
        };
        
        const mouseUpHandler = (e) => {
            if (isDragging) {
                console.log('✋ Drag ended at', { x: e.clientX, y: e.clientY });
                isDragging = false;
                dragMoveCount = 0;
                header.style.cursor = 'move';
                document.body.style.userSelect = ''; // Restore text selection
                
                // Delay clearing flag to prevent immediate backdrop close
                setTimeout(() => {
                    window._linkModalDragging = false;
                    console.log('🔓 Drag flag cleared');
                }, 400);
            }
        };
        
        // Use document-level listeners for smooth dragging
        document.addEventListener('mousemove', mouseMoveHandler);
        document.addEventListener('mouseup', mouseUpHandler);
    }
    
    function makeResizableModal(modalContent) {
        let isResizing = false;
        let resizeType = null;
        let startX = 0;
        let startY = 0;
        let startWidth = 0;
        let startHeight = 0;
        let startLeft = 0;
        let startTop = 0;

        // Get all resize handles (8 directions)
        const handles = {
            left: modalContent.querySelector('.modal-resize-left'),
            right: modalContent.querySelector('.modal-resize-right'),
            top: modalContent.querySelector('.modal-resize-top'),
            bottom: modalContent.querySelector('.modal-resize-bottom'),
            topLeft: modalContent.querySelector('.modal-resize-top-left'),
            topRight: modalContent.querySelector('.modal-resize-top-right'),
            bottomLeft: modalContent.querySelector('.modal-resize-bottom-left'),
            bottomRight: modalContent.querySelector('.modal-resize-bottom-right')
        };

        // Add mousedown listeners to all handles
        Object.entries(handles).forEach(([type, handle]) => {
            if (!handle) return;
            
            handle.addEventListener('mousedown', (e) => {
                console.log('🔧 Resize handle grabbed:', type);
                
                isResizing = true;
                window._linkModalResizing = true; // Track for backdrop click prevention
                resizeType = type;
                startX = e.clientX;
                startY = e.clientY;
                
                const rect = modalContent.getBoundingClientRect();
                startWidth = rect.width;
                startHeight = rect.height;
                startLeft = rect.left;
                startTop = rect.top;
                
                console.log('📏 Initial size:', { width: startWidth, height: startHeight, left: startLeft, top: startTop });
                
                // Visual feedback
                modalContent.style.userSelect = 'none';
                document.body.style.cursor = handle.style.cursor;
                document.body.style.userSelect = 'none';
                
                e.preventDefault();
                e.stopPropagation();
            });
        });

        let resizeMoveCount = 0;

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            e.preventDefault();
            
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            
            // Log every 10th move to avoid spam
            if (resizeMoveCount % 10 === 0) {
                console.log('📐 Resizing...', { deltaX, deltaY, type: resizeType });
            }
            resizeMoveCount++;
            
            let newWidth = startWidth;
            let newHeight = startHeight;
            let newLeft = startLeft;
            let newTop = startTop;
            
            // Calculate new dimensions based on resize type (8 directions)
            switch (resizeType) {
                case 'left':
                    newWidth = startWidth - deltaX;
                    newLeft = startLeft + deltaX;
                    break;
                case 'right':
                    newWidth = startWidth + deltaX;
                    break;
                case 'top':
                    newHeight = startHeight - deltaY;
                    newTop = startTop + deltaY;
                    break;
                case 'bottom':
                    newHeight = startHeight + deltaY;
                    break;
                case 'topLeft':
                    newWidth = startWidth - deltaX;
                    newHeight = startHeight - deltaY;
                    newLeft = startLeft + deltaX;
                    newTop = startTop + deltaY;
                    break;
                case 'topRight':
                    newWidth = startWidth + deltaX;
                    newHeight = startHeight - deltaY;
                    newTop = startTop + deltaY;
                    break;
                case 'bottomLeft':
                    newWidth = startWidth - deltaX;
                    newHeight = startHeight + deltaY;
                    newLeft = startLeft + deltaX;
                    break;
                case 'bottomRight':
                    newWidth = startWidth + deltaX;
                    newHeight = startHeight + deltaY;
                    break;
            }
            
            // Apply minimum and maximum constraints
            const minWidth = 300;
            const minHeight = 200;
            const maxWidth = window.innerWidth - 20;
            const maxHeight = window.innerHeight - 20;
            
            // Clamp width with minimum constraint
            if (newWidth < minWidth) {
                if (resizeType.includes('Left') || resizeType === 'left') {
                    newLeft = startLeft + startWidth - minWidth;
                }
                newWidth = minWidth;
            } else if (newWidth > maxWidth) {
                newWidth = maxWidth;
            }
            
            // Clamp height with minimum constraint
            if (newHeight < minHeight) {
                if (resizeType.includes('top') || resizeType.includes('Top')) {
                    newTop = startTop + startHeight - minHeight;
                }
                newHeight = minHeight;
            } else if (newHeight > maxHeight) {
                newHeight = maxHeight;
            }
            
            // Ensure modal stays within viewport when resizing left
            if (resizeType.includes('Left') || resizeType === 'left') {
                if (newLeft < 0) {
                    newWidth = startWidth + startLeft;
                    newLeft = 0;
                }
                if (newLeft + newWidth > window.innerWidth) {
                    newLeft = window.innerWidth - newWidth;
                }
            }
            
            // Ensure modal stays within viewport when resizing right
            if (resizeType.includes('Right') || resizeType === 'right') {
                if (newLeft + newWidth > window.innerWidth) {
                    newWidth = window.innerWidth - newLeft;
                }
            }
            
            // Ensure modal stays within viewport when resizing top
            if (resizeType.includes('top') || resizeType.includes('Top')) {
                if (newTop < 0) {
                    newHeight = startHeight + startTop;
                    newTop = 0;
                }
                if (newTop + newHeight > window.innerHeight) {
                    newTop = window.innerHeight - newHeight;
                }
            }
            
            // Ensure modal stays within viewport when resizing bottom
            if (resizeType.includes('bottom') || resizeType.includes('Bottom')) {
                if (newTop + newHeight > window.innerHeight) {
                    newHeight = window.innerHeight - newTop;
                }
            }
            
            // Apply new dimensions and position
            modalContent.style.width = newWidth + 'px';
            modalContent.style.height = newHeight + 'px';
            
            // Apply horizontal position changes
            if (resizeType.includes('Left') || resizeType === 'left') {
                modalContent.style.left = newLeft + 'px';
            }
            
            // Apply vertical position changes
            if (resizeType.includes('top') || resizeType.includes('Top')) {
                modalContent.style.top = newTop + 'px';
            }
        });

        document.addEventListener('mouseup', (e) => {
            if (isResizing) {
                console.log('✋ Resize ended at', { x: e.clientX, y: e.clientY });
                isResizing = false;
                resizeType = null;
                resizeMoveCount = 0;
                modalContent.style.userSelect = '';
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                
                // Delay clearing flag to prevent immediate backdrop close
                setTimeout(() => {
                    window._linkModalResizing = false;
                    console.log('🔓 Resize flag cleared');
                }, 400);
            }
        });
    }
    
    // Apply to all draggable modals
    const draggableModals = document.querySelectorAll('.draggable-modal');
    draggableModals.forEach(modal => {
        makeDraggableModal(modal);
        makeResizableModal(modal);
    });
    
    console.log(`✓ Made ${draggableModals.length} modals draggable and resizable with debugger-style handles`);
    
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
            navigator.clipboard.writeText(tableText).then(() => {
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
});


