/**
 * topology-registry.js - Feature Registry for Topology App
 * 
 * A manifest that tells Cursor (and developers) exactly where each type
 * of functionality belongs. This enables smart routing of new features
 * to the correct modules.
 * 
 * @version 1.0.0
 * @date 2026-02-03
 */

const TopologyRegistry = {
    // ========================================================================
    // MODULE REGISTRY
    // ========================================================================
    // Maps feature types to their owning modules
    
    modules: {
        // ===== Object Types =====
        'device': {
            file: 'topology-devices.js',
            class: 'DeviceManager',
            prop: 'devices',
            description: 'Network devices (routers, switches, NCPs)',
            methods: ['add', 'addAtPosition', 'findAt', 'getAll', 'getById', 'getByLabel', 'remove']
        },
        'link': {
            file: 'topology-links.js',
            class: 'LinkManager',
            prop: 'links',
            description: 'Connections between devices, BUL chains',
            methods: ['findAt', 'getAll', 'getById', 'analyzeBULChain', 'getAllMerged']
        },
        'text': {
            file: 'topology-text.js',
            class: 'TextManager',
            prop: 'text',
            description: 'Text labels and annotations',
            methods: ['create', 'findAt', 'getAll', 'showEditor', 'attachToLink']
        },
        'shape': {
            file: 'topology-shapes.js',
            class: 'ShapeManager',
            prop: 'shapes',
            description: 'Geometric shapes (rectangles, circles, etc.)',
            methods: ['create', 'findAt', 'getAll', 'selectType', 'draw']
        },
        
        // ===== UI Components =====
        'toolbar': {
            file: 'topology-ui.js',
            class: 'UIManager',
            prop: 'ui',
            description: 'Selection toolbars for devices, links, etc.',
            methods: ['showDeviceToolbar', 'showLinkToolbar', 'showTextToolbar', 'hideAllToolbars']
        },
        'contextMenu': {
            file: 'topology-menus.js',
            class: 'MenuManager',
            prop: 'menus',
            description: 'Right-click context menus',
            methods: ['showContextMenu', 'hideContextMenu', 'showBackgroundMenu', 'showBulkMenu']
        },
        'minimap': {
            file: 'topology-minimap.js',
            object: 'MinimapModule',
            description: 'Navigation minimap setup and interaction',
            methods: ['setup', 'startDragLoop', 'stopDragLoop', 'updateDragTarget', 'navigateFromDrag', 'toggle', 'getBounds', 'getTopologyBounds']
        },
        'scrollbars': {
            file: 'topology-scrollbars.js',
            object: 'ScrollbarsModule',
            description: 'Scrollbar setup and updates',
            methods: ['setup', 'update']
        },
        'linkEditor': {
            file: 'topology-link-editor.js',
            class: 'LinkEditorModal',
            prop: 'linkEditor',
            description: 'Link details editor modal (~2,172 lines)',
            methods: [
                'show', 'hide', 'forceHide', 'save', 'saveQuiet', 'saveQuietFull',
                'populateFields', 'validateForm', 'checkValidity', 'checkLinkTableValidity',
                'getFormData', 'getEditingChain', 'setEditingChain',
                'setupModalDragging', 'setupModalResize', 'setupResponsiveColumns',
                'initFloatingLabels', 'updateValue', 'updateCalculatedFields', 'resetFields',
                'copyAsMarkdown', 'formatValidationErrors', 'showValidationErrorToast',
                'validateVlanInput', 'validateIPv4', 'validateIPv6', 'validateIpAddress',
                'validateIpField', 'validateVlanField', 'setFieldValue',
                'updateVlanFieldsVisibility', 'updateIpAddressFieldVisibility',
                'deriveCategoryFromModel', 'detectModelFromDeviceName', 'showToast',
                'showDnaasAutoFillIndicator', 'updateStackColumnHeaders',
                'populateModelsForCategory', 'populateInterfacesForPlatform',
                'handleCustomInterfaceInput', 'setupPlatformCascading',
                'populatePlatformDropdown', 'populateInterfaceDropdown', 'populateTransceiverDropdown'
            ]
        },
        'groups': {
            file: 'topology-groups.js',
            class: 'GroupManager',
            prop: 'groups',
            description: 'Object grouping - bind objects to move as a unit',
            methods: ['generateId', 'findLeader', 'groupSelected', 'ungroupSelected', 'getMembers', 'isGrouped', 'expandSelection', 'validate', 'setupDrag']
        },
        'toolbar': {
            file: 'topology-toolbar.js',
            class: 'ToolbarManager',
            prop: 'toolbarMgr',
            description: 'Toolbar setup and button handlers',
            methods: ['setup', 'setupToolButtons', 'setupDeviceStyleButtons', 'setupLinkStyleButtons', 'setupFontButtons', 'updateButtonStates']
        },
        'dnaas': {
            file: 'topology-dnaas.js',
            class: 'DnaasManager',
            prop: 'dnaas',
            description: 'DNAAS network discovery and operations',
            methods: ['setupPanel', 'startMultiBdDiscovery', 'cancelDiscovery', 'loadTopology', 'loadData', 'isRouter', 'populateSuggestions']
        },
        
        // ===== Core Systems =====
        'input': {
            file: 'topology-input.js',
            class: 'InputManager',
            prop: 'input',
            description: 'Input state machine (mouse, keyboard, touch)',
            methods: ['handleMouseDown', 'handleMouseMove', 'handleMouseUp', 'transition', 'reset']
        },
        'drawing': {
            file: 'topology-drawing.js',
            class: 'DrawingManager',
            prop: 'drawing',
            description: 'Canvas rendering',
            methods: ['draw', 'drawObject', 'drawDevice', 'drawLink', 'requestRedraw']
        },
        'files': {
            file: 'topology-files.js',
            class: 'FileManager',
            prop: 'files',
            description: 'File operations, auto-save, crash recovery',
            methods: ['enableAutoSave', 'saveRecoveryPoint', 'checkForRecovery', 'exportJSON', 'importJSON']
        },
        'history': {
            file: 'topology-history.js',
            class: 'HistoryManager',
            prop: 'history',
            description: 'Undo/redo stack',
            methods: ['saveState', 'undo', 'redo', 'updateUndoRedoButtons']
        },
        'errors': {
            file: 'topology-errors.js',
            class: 'ErrorBoundary',
            prop: null, // Static class
            description: 'Error handling and crash protection',
            methods: ['wrap', 'wrapAsync', 'wrapEventHandler', 'handleError', 'showUserNotification']
        },
        
        // ===== Utilities =====
        'geometry': {
            file: 'topology-geometry.js',
            object: 'TopologyGeometry',
            description: 'Math and geometry utilities',
            methods: ['distanceToLine', 'pointOnBezier', 'isPointInRect', 'lineSegmentIntersection']
        },
        'events': {
            file: 'topology-events.js',
            class: 'TopologyEventBus',
            prop: 'events',
            description: 'Pub/sub event system',
            methods: ['on', 'off', 'emit', 'once']
        },
        'platformData': {
            file: 'topology-platform-data.js',
            class: 'PlatformData',
            prop: 'platformData',
            description: 'DriveNets platform and transceiver data',
            methods: ['getPlatform', 'getPlatformsByCategory', 'getTransceiversForSpeed']
        },
        'curveMode': {
            file: 'topology-curve-mode.js',
            object: 'CurveModeManager',
            description: 'Link curve mode switching and calculations',
            methods: ['setGlobalMode', 'updateUI', 'getEffectiveMode', 'getEndpoints', 'getMidpoint', 'getAutoCurveMidpoint']
        },
        'devicePlacement': {
            file: 'topology-device-placement.js',
            object: 'DevicePlacement',
            description: 'Device collision detection and placement',
            methods: ['getCollisionRadiusInDirection', 'getCollisionRadius', 'checkCollision']
        },
        'linkTable': {
            file: 'topology-link-table.js',
            object: 'LinkTableManager',
            description: 'Link Table modal field management',
            methods: ['setupResponsiveColumns', 'populateFields', 'autoFillFromDnaasDiscovery', 'updateValue', 'updateCalculatedFields', 'resetFields', 'copyAsMarkdown', 'showToast']
        },
        'modalUtils': {
            file: 'topology-modal-utils.js',
            object: 'ModalUtils',
            description: 'Modal dragging and resizing utilities',
            methods: ['makeDraggableModal', 'makeResizableModal', 'initAllModals']
        },
        'notifications': {
            file: 'topology-notifications.js',
            object: 'NotificationManager',
            description: 'Toast notifications, hints, and setup dialogs',
            methods: ['showSplitHelperHint', 'showSplitPaneNotification', 'showItermSetupHint', 'showNotification', 'showValidationErrorToast']
        },
        'dialogs': {
            file: 'topology-dialogs.js',
            object: 'DialogManager',
            description: 'Input, info, and confirm dialogs (replacements for browser prompts)',
            methods: ['showInputDialog', 'showInfoDialog', 'showConfirmDialog']
        },
        'sampleData': {
            file: 'topology-sample-data.js',
            object: 'SampleTopologyData',
            description: 'Sample DNAAS topology data for demos and testing',
            methods: ['getDnaasLogicalBD210Topology', 'getDnaasBD210Topology']
        },
        'bulUtils': {
            file: 'topology-bul-utils.js',
            object: 'BulUtils',
            description: 'BUL (Bi-directional Unbound Link) utility functions',
            methods: ['distanceToLine', 'linksAlreadyShareMP', 'getAllMergedLinks', 'getParentConnectionEndpoint', 'getChildConnectionEndpoint', 'isEndpointConnected', 'getOppositeEndpoint']
        },
        'interfaces': {
            file: 'topology-interfaces.js',
            object: 'InterfaceGenerator',
            description: 'Interface generation for different platform types',
            methods: ['generateInterfaces', 'generateClusterInterfaces', 'generateAIInterfaces', 'generateDNAASInterfaces', 'getInterfacesForPlatform', 'extractInterfacesFromConfig', 'getSubInterfacesWithVlan', 'extractVlanFromSubInterface', 'validateVlanMatch']
        },
        'momentum': {
            file: 'topology-momentum.js',
            class: 'MomentumEngine',
            prop: 'momentum',
            description: 'Inertia/sliding physics for pan/zoom',
            methods: ['trackVelocity', 'startSlide', 'toggle']
        },
        
        // ===== Integrations =====
        'scaler': {
            file: 'scaler-api.js',
            class: 'ScalerAPI',
            prop: null,
            description: 'SCALER tool integration',
            methods: ['connect', 'pushConfig', 'getDevices']
        },
        
        // ===== Extracted Modules (Feb 2026) =====
        'mouseHandler': {
            file: 'topology-mouse.js',
            object: 'MouseHandler',
            description: 'Mouse event handlers (down, move, up, double-click)',
            methods: ['handleMouseDown', 'handleMouseMove', 'handleMouseUp', 'handleDoubleClick']
        },
        'linkDrawing': {
            file: 'topology-link-drawing.js',
            object: 'LinkDrawing',
            description: 'Link rendering (drawLink, drawUnboundLink)',
            methods: ['drawLink', 'drawUnboundLink']
        },
        'toolbarSetup': {
            file: 'topology-toolbar-setup.js',
            object: 'ToolbarSetup',
            description: 'Toolbar button setup and event listeners',
            methods: ['setupToolbar']
        },
        'drawModule': {
            file: 'topology-draw.js',
            object: 'DrawModule',
            description: 'Main draw loop',
            methods: ['draw']
        },
        'canvasDrawing': {
            file: 'topology-canvas-drawing.js',
            object: 'CanvasDrawing',
            description: 'Canvas drawing (device, label, text)',
            methods: ['drawDevice', 'drawDeviceLabel', 'drawText']
        },
        'minimapRender': {
            file: 'topology-minimap-render.js',
            object: 'MinimapRender',
            description: 'Minimap rendering',
            methods: ['renderMinimap']
        },
        'shapeDrawing': {
            file: 'topology-shape-drawing.js',
            object: 'ShapeDrawing',
            description: 'Shape drawing',
            methods: ['drawShape', 'drawShapeSelectionHandles']
        },
        'objectDetection': {
            file: 'topology-object-detection.js',
            object: 'ObjectDetection',
            description: 'Hit detection and object finding',
            methods: ['findObjectAt', 'findTextAt', 'findRotationHandle', 'findTextHandle', 'findTerminalButton']
        },
        'modalUtils': {
            file: 'topology-modal-utils.js',
            object: 'ModalUtils',
            description: 'Modal drag/resize utilities',
            methods: ['makeDraggableModal', 'makeResizableModal', 'initAllModals']
        },
        'mathUtils': {
            file: 'topology-math-utils.js',
            object: 'MathUtils',
            description: 'Math and animation utility functions',
            methods: ['lerp', 'lerpPoint', 'getDistance', 'getTwoFingerCenter', 'distanceToLine', 'clamp', 'degToRad', 'radToDeg', 'angleBetween', 'distanceBetween', 'hexToRgba']
        },
        'linkPopups': {
            file: 'topology-link-popups.js',
            object: 'LinkPopups',
            description: 'Link popup UI components (width, style, curve)',
            methods: ['showWidthSliderPopup', 'hideWidthSliderPopup', 'showStyleOptionsPopup', 'hideStyleOptionsPopup', 'showCurveMagnitudePopup', 'hideCurveMagnitudePopup']
        },
        'colorPopups': {
            file: 'topology-color-popups.js',
            object: 'ColorPopups',
            description: 'Color palette popup UI components',
            methods: ['showColorPalettePopup', 'showColorPalettePopupFromToolbar', 'hideColorPalettePopup']
        },
        'lldpDialog': {
            file: 'topology-lldp-dialog.js',
            object: 'LldpDialog',
            description: 'LLDP neighbor discovery dialog',
            methods: ['show', 'hide', 'loadFromDevice', 'parseOutput']
        },
        'dnaasHelpers': {
            file: 'topology-dnaas-helpers.js',
            object: 'DnaasHelpers',
            description: 'DNAAS helper functions',
            methods: ['fetchInterfaceDetails', 'parseDeviceConfig', 'autoFillFromDiscovery']
        },
        'keyboardHandler': {
            file: 'topology-keyboard.js',
            object: 'KeyboardHandler',
            description: 'Keyboard shortcut handlers',
            methods: ['handleKeyDown', 'handleKeyUp']
        },
        'deviceToolbar': {
            file: 'topology-device-toolbar.js',
            object: 'DeviceToolbar',
            description: 'Device selection toolbar',
            methods: ['show', 'hide', 'update']
        },
        'linkToolbar': {
            file: 'topology-link-toolbar.js',
            object: 'LinkToolbar',
            description: 'Link selection toolbar',
            methods: ['show', 'hide', 'update']
        },
        'multiselectMenu': {
            file: 'topology-multiselect-menu.js',
            object: 'MultiselectMenu',
            description: 'Multi-select context menu',
            methods: ['show', 'hide', 'buildMenu']
        },
        'deviceStyles': {
            file: 'topology-device-styles.js',
            object: 'DeviceStyles',
            description: 'Device visual styles and shapes',
            methods: ['getStyle', 'applyStyle', 'getAvailableStyles']
        },
        'dnaasOperations': {
            file: 'topology-dnaas-operations.js',
            object: 'DnaasOperations',
            description: 'DNAAS layout helpers',
            methods: ['calculateLabelWidth', 'calculateRowSpacing', 'sortDevicesByLabel']
        },
        'bdLegend': {
            file: 'topology-bd-legend.js',
            object: 'BDLegend',
            description: 'Bridge Domain legend panel, visibility, and lifecycle',
            methods: ['showBDLegend', 'hideBDLegend', 'toggleBDVisibility', 'setBDVisibilityAll', 'updateDeviceVisibilityByBD', 'toggleBDLegendPanel', 'updateBDHierarchyButton', '_saveBDPanelState', '_loadBDPanelState', 'restoreBDPanelIfNeeded', '_updateBDPanelTheme', '_reconstructBDMetadataFromCanvas', 'toggleBDLinkView', 'applyBDViewMode', 'highlightBDPath', 'createBDTextBox', 'inject']
        },
        'touchHandler': {
            file: 'topology-touch.js',
            object: 'TouchHandler',
            description: 'Multi-touch gesture handling (pinch, pan, taps)',
            methods: ['handleTouchStart', 'handleTouchMove', 'handleTouchEnd', 'process3FingerTap', 'toggle4FingerMode']
        },
        'contextMenus': {
            file: 'topology-context-menus.js',
            object: 'ContextMenus',
            description: 'Context menu positioning and display',
            methods: ['adjustMenuPosition', 'showBackgroundContextMenu', 'showBulkContextMenu', 'showMarqueeContextMenu']
        },
        'textEditor': {
            file: 'topology-text-editor.js',
            object: 'TextEditorModule',
            description: 'Text editing modal and inline editor',
            methods: ['show', 'hide', 'apply', 'showInline', 'updateInlinePosition', 'hideInline']
        },
        'textToolbar': {
            file: 'topology-text-toolbar.js',
            object: 'TextToolbar',
            description: 'Text selection toolbar with liquid glass styling',
            methods: ['showTextSelectionToolbar', 'hideTextSelectionToolbar']
        },
        'shapeToolbar': {
            file: 'topology-shape-toolbar.js',
            object: 'ShapeToolbar',
            description: 'Shape selection toolbar with fill/stroke controls',
            methods: ['showShapeSelectionToolbar', 'hideShapeSelectionToolbar']
        }
    },
    
    // ========================================================================
    // FEATURE CATEGORIES
    // ========================================================================
    
    categories: {
        'objectType': ['device', 'link', 'text', 'shape'],
        'ui': ['toolbar', 'contextMenu', 'minimap', 'linkEditor', 'deviceToolbar', 'linkToolbar', 'multiselectMenu'],
        'core': ['input', 'drawing', 'files', 'history', 'errors', 'mouseHandler', 'keyboardHandler'],
        'utility': ['geometry', 'events', 'platformData', 'momentum', 'modalUtils'],
        'rendering': ['drawModule', 'canvasDrawing', 'linkDrawing', 'shapeDrawing', 'minimapRender', 'objectDetection'],
        'integration': ['scaler', 'dnaasHelpers', 'lldpDialog'],
        'setup': ['toolbarSetup', 'deviceStyles']
    },
    
    // ========================================================================
    // DECISION HELPERS
    // ========================================================================
    
    /**
     * Determine where new code should go based on feature description
     * @param {string} featureDescription - Natural language description of the feature
     * @returns {Object} { action: 'edit'|'create', file: string, reason: string, module: string }
     */
    whereDoesThisBelong(featureDescription) {
        const desc = featureDescription.toLowerCase();
        
        // Check for keywords that map to existing modules
        const keywordMap = {
            'device': ['device', 'router', 'switch', 'ncp', 'node', 'platform'],
            'link': ['link', 'connection', 'edge', 'wire', 'bul', 'unbound'],
            'text': ['text', 'label', 'annotation', 'caption'],
            'shape': ['shape', 'rectangle', 'circle', 'ellipse', 'polygon'],
            'toolbar': ['toolbar', 'selection bar', 'tool panel'],
            'contextMenu': ['context menu', 'right-click', 'popup menu'],
            'linkEditor': ['link details', 'link editor', 'link modal', 'link properties', 'vlan', 'interface config'],
            'groups': ['group', 'ungroup', 'grouping', 'bind objects', 'move together'],
            'toolbar': ['toolbar', 'tool button', 'tool panel', 'device style', 'link style', 'font button'],
            'dnaas': ['dnaas', 'discovery', 'lldp', 'network discovery', 'bridge domain', 'ncm', 'ncf', 'inventory'],
            'input': ['mouse', 'keyboard', 'touch', 'drag', 'click', 'gesture'],
            'drawing': ['draw', 'render', 'canvas', 'paint', 'display'],
            'files': ['save', 'load', 'export', 'import', 'file', 'backup'],
            'geometry': ['math', 'geometry', 'calculate', 'distance', 'intersection'],
            'events': ['event', 'emit', 'subscribe', 'notify'],
            'scaler': ['scaler', 'config push', 'device config']
        };
        
        for (const [moduleName, keywords] of Object.entries(keywordMap)) {
            if (keywords.some(kw => desc.includes(kw))) {
                const module = this.modules[moduleName];
                if (module) {
                    return {
                        action: 'edit',
                        file: module.file,
                        module: moduleName,
                        reason: `Feature relates to ${module.description}`,
                        class: module.class
                    };
                }
            }
        }
        
        // Check for new module indicators
        if (desc.includes('modal') || desc.includes('dialog') || desc.includes('popup')) {
            const name = this.extractFeatureName(desc);
            return {
                action: 'create',
                file: `topology-${name}-modal.js`,
                module: name,
                reason: 'Complex modal/dialog should be separate module',
                template: 'modal'
            };
        }
        
        if (desc.includes('api') || desc.includes('integration') || desc.includes('external')) {
            const name = this.extractFeatureName(desc);
            return {
                action: 'create',
                file: `topology-${name}-api.js`,
                module: name,
                reason: 'External integration should be separate module',
                template: 'integration'
            };
        }
        
        // Default: suggest creating new module for complex features
        return {
            action: 'unknown',
            file: null,
            reason: 'Could not determine best location. Consider: Is this >200 lines? Does it need state? Is it related to existing modules?',
            suggestions: Object.keys(this.modules)
        };
    },
    
    /**
     * Extract a feature name from a description
     * @param {string} desc - Feature description
     * @returns {string} Feature name in kebab-case
     */
    extractFeatureName(desc) {
        // Remove common words and extract the main noun
        const words = desc.toLowerCase()
            .replace(/[^a-z\s]/g, '')
            .split(/\s+/)
            .filter(w => !['a', 'an', 'the', 'new', 'add', 'create', 'for', 'to', 'with'].includes(w));
        
        return words.slice(0, 2).join('-') || 'feature';
    },
    
    /**
     * Get the module info for a given feature type
     * @param {string} featureType - The feature type name
     * @returns {Object|null} Module info or null
     */
    getModule(featureType) {
        return this.modules[featureType] || null;
    },
    
    /**
     * Get all modules in a category
     * @param {string} category - Category name
     * @returns {Array} Array of module names
     */
    getModulesInCategory(category) {
        return this.categories[category] || [];
    },
    
    /**
     * Check if a module exists
     * @param {string} moduleName - Module name
     * @returns {boolean}
     */
    hasModule(moduleName) {
        return !!this.modules[moduleName];
    },
    
    // ========================================================================
    // TEMPLATE GENERATORS
    // ========================================================================
    
    templates: {
        /**
         * Generate template for a new Object Manager
         */
        objectManager: (name) => `
/**
 * topology-${name.toLowerCase()}.js - ${name} Manager
 * 
 * Manages ${name.toLowerCase()} objects in the topology editor.
 */

class ${name}Manager {
    constructor(editor) {
        this.editor = editor;
        this.items = [];
        
        // Register with editor
        this.editor.${name.toLowerCase()}s = this;
        
        console.log('${name}Manager initialized');
    }
    
    // CRUD operations
    create(options) {
        const item = { 
            id: Date.now(), 
            type: '${name.toLowerCase()}',
            ...options 
        };
        this.items.push(item);
        this.editor.events?.emit('${name.toLowerCase()}:created', item);
        this.editor.saveState?.();
        return item;
    }
    
    getAll() { 
        return this.items; 
    }
    
    getById(id) { 
        return this.items.find(i => i.id === id); 
    }
    
    remove(id) {
        const index = this.items.findIndex(i => i.id === id);
        if (index > -1) {
            const item = this.items.splice(index, 1)[0];
            this.editor.events?.emit('${name.toLowerCase()}:removed', { id });
            this.editor.saveState?.();
            return item;
        }
        return null;
    }
    
    // Spatial query
    findAt(x, y) {
        return this.items.find(item => {
            // TODO: Implement hit test for ${name.toLowerCase()}
            return false;
        });
    }
    
    // Drawing
    draw(ctx, item) {
        // TODO: Implement drawing for ${name.toLowerCase()}
    }
    
    getCount() {
        return this.items.length;
    }
}

window.${name}Manager = ${name}Manager;
window.create${name}Manager = (editor) => new ${name}Manager(editor);

console.log('[topology-${name.toLowerCase()}.js] ${name}Manager loaded');
`,

        /**
         * Generate template for a new Modal
         */
        modal: (name) => `
/**
 * topology-${name.toLowerCase()}-modal.js - ${name} Modal
 * 
 * Modal dialog for ${name.toLowerCase()} operations.
 */

class ${name}Modal {
    constructor(editor) {
        this.editor = editor;
        this.element = null;
        this.isVisible = false;
        this.data = null;
    }
    
    show(data = {}) {
        this.data = data;
        this.createModal();
        this.populateFields();
        this.setupEventListeners();
        this.isVisible = true;
        this.editor.events?.emit('${name.toLowerCase()}Modal:opened', data);
    }
    
    hide() {
        if (this.element) {
            this.element.remove();
            this.element = null;
        }
        this.isVisible = false;
        this.data = null;
        this.editor.events?.emit('${name.toLowerCase()}Modal:closed');
    }
    
    createModal() {
        // Remove existing modal if any
        this.hide();
        
        this.element = document.createElement('div');
        this.element.className = '${name.toLowerCase()}-modal-overlay';
        this.element.innerHTML = \`
            <div class="${name.toLowerCase()}-modal">
                <div class="${name.toLowerCase()}-modal-header">
                    <h2>${name}</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="${name.toLowerCase()}-modal-body">
                    <!-- TODO: Add form fields -->
                </div>
                <div class="${name.toLowerCase()}-modal-footer">
                    <button class="btn-cancel">Cancel</button>
                    <button class="btn-save">Save</button>
                </div>
            </div>
        \`;
        
        document.body.appendChild(this.element);
    }
    
    populateFields() {
        // TODO: Populate form fields from this.data
    }
    
    setupEventListeners() {
        this.element.querySelector('.modal-close')?.addEventListener('click', () => this.hide());
        this.element.querySelector('.btn-cancel')?.addEventListener('click', () => this.hide());
        this.element.querySelector('.btn-save')?.addEventListener('click', () => this.save());
        
        // Close on overlay click
        this.element.addEventListener('click', (e) => {
            if (e.target === this.element) this.hide();
        });
        
        // Close on Escape
        this.escHandler = (e) => {
            if (e.key === 'Escape') this.hide();
        };
        document.addEventListener('keydown', this.escHandler);
    }
    
    save() {
        // TODO: Validate and save data
        const formData = this.collectFormData();
        
        this.editor.events?.emit('${name.toLowerCase()}Modal:saved', formData);
        this.hide();
    }
    
    collectFormData() {
        // TODO: Collect data from form fields
        return {};
    }
}

window.${name}Modal = ${name}Modal;

console.log('[topology-${name.toLowerCase()}-modal.js] ${name}Modal loaded');
`,

        /**
         * Generate template for a new Integration/API
         */
        integration: (name) => `
/**
 * topology-${name.toLowerCase()}-api.js - ${name} Integration
 * 
 * Integration with external ${name} service.
 */

class ${name}Integration {
    constructor(editor) {
        this.editor = editor;
        this.baseUrl = '';
        this.connected = false;
        this.config = {};
    }
    
    async connect(config = {}) {
        this.config = config;
        
        try {
            // TODO: Implement connection logic
            this.connected = true;
            this.editor.events?.emit('${name.toLowerCase()}:connected');
            console.log('[${name}Integration] Connected');
            return true;
        } catch (error) {
            this.editor.events?.emit('${name.toLowerCase()}:error', error);
            console.error('[${name}Integration] Connection failed:', error);
            throw error;
        }
    }
    
    async disconnect() {
        this.connected = false;
        this.editor.events?.emit('${name.toLowerCase()}:disconnected');
        console.log('[${name}Integration] Disconnected');
    }
    
    isConnected() {
        return this.connected;
    }
    
    async fetch(endpoint, options = {}) {
        if (!this.connected) {
            throw new Error('${name}Integration: Not connected');
        }
        
        try {
            const response = await fetch(\`\${this.baseUrl}\${endpoint}\`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(\`HTTP \${response.status}: \${response.statusText}\`);
            }
            
            return await response.json();
        } catch (error) {
            this.editor.events?.emit('${name.toLowerCase()}:error', error);
            throw error;
        }
    }
    
    async push(data) {
        // TODO: Implement push logic
        return this.fetch('/push', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

window.${name}Integration = ${name}Integration;

console.log('[topology-${name.toLowerCase()}-api.js] ${name}Integration loaded');
`,

        /**
         * Generate template for a new Input State Handler
         */
        inputState: (name) => `
/**
 * ${name}Handler - Input state handler for ${name.toLowerCase()} operations
 * 
 * Add this to topology-input.js handlers
 */

class ${name}Handler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = '${name.charAt(0).toLowerCase() + name.slice(1)}';
        this.active = false;
    }
    
    enter(context = {}) {
        super.enter(context);
        this.active = true;
        // TODO: Setup cursor, UI hints
        this.editor.canvas.style.cursor = 'crosshair';
    }
    
    exit() {
        this.active = false;
        this.editor.canvas.style.cursor = 'default';
        super.exit();
    }
    
    onMouseDown(e) {
        // TODO: Handle mouse down
        // Return next state name or null to stay in current state
        return null;
    }
    
    onMouseMove(e) {
        if (!this.active) return null;
        // TODO: Handle mouse move
        return null;
    }
    
    onMouseUp(e) {
        // TODO: Handle mouse up
        // Return 'idle' when operation is complete
        return 'idle';
    }
    
    onKeyDown(e) {
        if (e.key === 'Escape') {
            return 'idle';
        }
        return null;
    }
}

// Register with InputManager:
// inputManager.registerState('${name.charAt(0).toLowerCase() + name.slice(1)}', new ${name}Handler(editor, inputManager));
`
    },
    
    /**
     * Generate boilerplate code for a new feature
     * @param {string} templateName - Template type: 'objectManager', 'modal', 'integration', 'inputState'
     * @param {string} featureName - Name of the feature (PascalCase)
     * @returns {string} Generated code
     */
    generateTemplate(templateName, featureName) {
        const template = this.templates[templateName];
        if (!template) {
            return `// Unknown template: ${templateName}`;
        }
        return template(featureName);
    },
    
    // ========================================================================
    // UTILITY METHODS
    // ========================================================================
    
    /**
     * List all registered modules
     * @returns {Array} Array of module info objects
     */
    listModules() {
        return Object.entries(this.modules).map(([name, info]) => ({
            name,
            ...info
        }));
    },
    
    /**
     * Get a summary of the registry for documentation
     * @returns {string} Markdown summary
     */
    getSummary() {
        let summary = '# Topology Module Registry\n\n';
        
        for (const [category, modules] of Object.entries(this.categories)) {
            summary += `## ${category.charAt(0).toUpperCase() + category.slice(1)}\n\n`;
            summary += '| Module | File | Class | Description |\n';
            summary += '|--------|------|-------|-------------|\n';
            
            for (const moduleName of modules) {
                const m = this.modules[moduleName];
                if (m) {
                    summary += `| ${moduleName} | ${m.file} | ${m.class || m.object} | ${m.description} |\n`;
                }
            }
            summary += '\n';
        }
        
        return summary;
    }
};

// Export
window.TopologyRegistry = TopologyRegistry;

console.log('[topology-registry.js] Feature Registry loaded with', Object.keys(TopologyRegistry.modules).length, 'modules');
