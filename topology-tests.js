// ============================================================================
// TOPOLOGY MODULE TEST SUITE
// ============================================================================
// Automated tests for verifying module loading and integration.
// Run these tests after each module extraction to ensure nothing breaks.
//
// Usage:
//   TopologyTests.runAll();           // Run all tests
//   TopologyTests.runModule('events'); // Run specific module tests
//   TopologyTests.runIntegration();   // Run integration tests
// ============================================================================

const TopologyTests = {
    results: [],
    totalPassed: 0,
    totalFailed: 0,

    // ========== TEST UTILITIES ==========
    
    log(message, type = 'info') {
        const prefix = {
            'pass': '✅',
            'fail': '❌',
            'info': 'ℹ️',
            'warn': '⚠️',
            'section': '\n📦'
        }[type] || '';
        console.log(`${prefix} ${message}`);
    },

    assert(condition, testName, details = '') {
        if (condition) {
            this.totalPassed++;
            this.results.push({ name: testName, passed: true });
            this.log(`${testName}: PASS`, 'pass');
            return true;
        } else {
            this.totalFailed++;
            this.results.push({ name: testName, passed: false, details });
            this.log(`${testName}: FAIL ${details ? '- ' + details : ''}`, 'fail');
            return false;
        }
    },

    assertEqual(actual, expected, testName) {
        return this.assert(
            actual === expected, 
            testName, 
            `expected ${expected}, got ${actual}`
        );
    },

    assertExists(obj, testName) {
        return this.assert(obj !== undefined && obj !== null, testName, 'is undefined or null');
    },

    assertFunction(fn, testName) {
        return this.assert(typeof fn === 'function', testName, `is ${typeof fn}, not function`);
    },

    // ========== MODULE TESTS ==========

    testEventsModule() {
        this.log('Events Module (TopologyEventBus)', 'section');
        
        // Test 1: Module loaded
        this.assertExists(window.TopologyEventBus, 'TopologyEventBus class exists');
        
        // Test 2: Can instantiate
        let bus;
        try {
            bus = new TopologyEventBus();
            this.assert(true, 'TopologyEventBus instantiates');
        } catch (e) {
            this.assert(false, 'TopologyEventBus instantiates', e.message);
            return;
        }
        
        // Test 3: on() method
        this.assertFunction(bus.on, 'bus.on is a function');
        
        // Test 4: emit() method
        this.assertFunction(bus.emit, 'bus.emit is a function');
        
        // Test 5: off() method
        this.assertFunction(bus.off, 'bus.off is a function');
        
        // Test 6: Event subscription and emission
        let received = false;
        let receivedData = null;
        bus.on('test:event', (data) => {
            received = true;
            receivedData = data;
        });
        bus.emit('test:event', { value: 42 });
        this.assert(received, 'Event subscription works');
        this.assertEqual(receivedData?.value, 42, 'Event data passed correctly');
        
        // Test 7: Unsubscribe via returned function
        let count = 0;
        const unsub = bus.on('test:unsub', () => count++);
        bus.emit('test:unsub');
        unsub(); // Unsubscribe
        bus.emit('test:unsub');
        this.assertEqual(count, 1, 'Unsubscribe via returned function works');
        
        // Test 8: Factory function
        this.assertFunction(window.createEventBus, 'createEventBus factory exists');
        
        // Test 9: Editor integration
        if (window.topologyEditor) {
            this.assertExists(window.topologyEditor.events, 'Editor has events property');
            this.assertFunction(window.topologyEditor.events.emit, 'Editor events.emit works');
        }
    },

    testGeometryModule() {
        this.log('Geometry Module (TopologyGeometry)', 'section');
        
        // Test 1: Module loaded
        this.assertExists(window.TopologyGeometry, 'TopologyGeometry object exists');
        
        const G = window.TopologyGeometry;
        
        // Test 2: distanceBetweenPoints
        this.assertFunction(G.distanceBetweenPoints, 'distanceBetweenPoints exists');
        const dist = G.distanceBetweenPoints({x: 0, y: 0}, {x: 3, y: 4});
        this.assertEqual(dist, 5, 'distanceBetweenPoints calculates correctly (3-4-5 triangle)');
        
        // Test 3: distanceToLine
        this.assertFunction(G.distanceToLine, 'distanceToLine exists');
        const lineDist = G.distanceToLine(0, 5, {x: 0, y: 0}, {x: 10, y: 0});
        this.assertEqual(lineDist, 5, 'distanceToLine calculates correctly');
        
        // Test 4: isPointInCircle
        this.assertFunction(G.isPointInCircle, 'isPointInCircle exists');
        this.assert(G.isPointInCircle(5, 5, 5, 5, 10), 'isPointInCircle: point at center is inside');
        this.assert(!G.isPointInCircle(100, 100, 5, 5, 10), 'isPointInCircle: distant point is outside');
        
        // Test 5: isPointInRect
        this.assertFunction(G.isPointInRect, 'isPointInRect exists');
        this.assert(G.isPointInRect(15, 15, 10, 10, 20, 20), 'isPointInRect: point inside');
        this.assert(!G.isPointInRect(5, 5, 10, 10, 20, 20), 'isPointInRect: point outside');
        
        // Test 6: pointOnBezier
        this.assertFunction(G.pointOnBezier, 'pointOnBezier exists');
        const bezierStart = G.pointOnBezier(0, {x:0,y:0}, {x:10,y:0}, {x:10,y:10}, {x:0,y:10});
        this.assertEqual(bezierStart.x, 0, 'pointOnBezier t=0 returns start point');
        
        // Test 7: midpoint
        this.assertFunction(G.midpoint, 'midpoint exists');
        const mid = G.midpoint({x: 0, y: 0}, {x: 10, y: 10});
        this.assert(mid.x === 5 && mid.y === 5, 'midpoint calculates correctly');
        
        // Test 8: angleBetween
        this.assertFunction(G.angleBetween, 'angleBetween exists');
        const angle = G.angleBetween({x: 0, y: 0}, {x: 1, y: 0});
        this.assertEqual(angle, 0, 'angleBetween: 0 degrees to the right');
        
        // Test 9: lerp
        this.assertFunction(G.lerp, 'lerp exists');
        this.assertEqual(G.lerp(0, 10, 0.5), 5, 'lerp interpolates correctly');
        
        // Test 10: clamp
        this.assertFunction(G.clamp, 'clamp exists');
        this.assertEqual(G.clamp(15, 0, 10), 10, 'clamp upper bound works');
        this.assertEqual(G.clamp(-5, 0, 10), 0, 'clamp lower bound works');
    },

    testPlatformDataModule() {
        this.log('Platform Data Module (PlatformData)', 'section');
        
        // Test 1: Module loaded
        this.assertExists(window.PlatformData, 'PlatformData class exists');
        
        // Test 2: Can instantiate
        let pd;
        try {
            pd = new PlatformData();
            this.assert(true, 'PlatformData instantiates');
        } catch (e) {
            this.assert(false, 'PlatformData instantiates', e.message);
            return;
        }
        
        // Test 3: platforms property
        this.assertExists(pd.platforms, 'platforms property exists');
        
        // Test 4: transceivers property
        this.assertExists(pd.transceivers, 'transceivers property exists');
        
        // Test 5: getPlatform method
        this.assertFunction(pd.getPlatform, 'getPlatform method exists');
        const sa40c = pd.getPlatform('SA-40C');
        this.assertExists(sa40c, 'getPlatform finds SA-40C');
        this.assertEqual(sa40c?.displayName, 'NCP1 (SA-40C)', 'SA-40C has correct displayName');
        
        // Test 6: getPlatformsByCategory
        this.assertFunction(pd.getPlatformsByCategory, 'getPlatformsByCategory exists');
        const saPlatforms = pd.getPlatformsByCategory('SA');
        this.assert(saPlatforms.length > 0, 'SA category has platforms');
        
        // Test 7: getCategories
        this.assertFunction(pd.getCategories, 'getCategories exists');
        const categories = pd.getCategories();
        this.assert(categories.includes('SA'), 'Categories include SA');
        this.assert(categories.includes('CL'), 'Categories include CL');
        
        // Test 8: getTransceiversForSpeed
        this.assertFunction(pd.getTransceiversForSpeed, 'getTransceiversForSpeed exists');
        const transceivers400G = pd.getTransceiversForSpeed('400G');
        this.assert(transceivers400G.length > 0, '400G transceivers exist');
        
        // Test 9: generateInterfaces
        this.assertFunction(pd.generateInterfaces, 'generateInterfaces exists');
        const interfaces = pd.generateInterfaces('SA-40C');
        this.assert(interfaces.length === 40, 'SA-40C generates 40 interfaces');
        this.assert(interfaces[0].startsWith('ge100'), 'SA-40C interfaces start with ge100');
        
        // Test 10: Factory function
        this.assertFunction(window.createPlatformData, 'createPlatformData factory exists');
        
        // Test 11: Editor integration
        if (window.topologyEditor) {
            this.assertExists(window.topologyEditor.platformData, 'Editor has platformData property');
        }
    },

    // ========== INTEGRATION TESTS ==========

    testEditorIntegration() {
        this.log('Editor Integration', 'section');
        
        // Test 1: Editor exists (skip if running standalone)
        if (!window.topologyEditor) {
            this.log('Skipping editor integration tests - editor not loaded (run on index.html)', 'info');
            return;
        }
        
        this.assert(true, 'topologyEditor global exists');
        
        const editor = window.topologyEditor;
        
        // Test 2: Canvas
        this.assertExists(editor.canvas, 'Editor has canvas');
        this.assertExists(editor.ctx, 'Editor has context');
        
        // Test 3: Objects array
        this.assert(Array.isArray(editor.objects), 'Editor has objects array');
        
        // Test 4: Events module integrated
        this.assertExists(editor.events, 'Editor has events module');
        
        // Test 5: PlatformData integrated
        this.assertExists(editor.platformData, 'Editor has platformData module');
        
        // Test 6: Legacy platform data still works
        this.assertExists(editor.driveNetsPlatforms, 'Legacy driveNetsPlatforms still exists');
        
        // Test 7: Core methods exist
        this.assertFunction(editor.draw, 'editor.draw exists');
        this.assertFunction(editor.saveState, 'editor.saveState exists');
        
        // Test 8: History/undo system
        this.assert(Array.isArray(editor.history), 'Editor has history array');
        this.assertFunction(editor.undo, 'editor.undo exists');
        this.assertFunction(editor.redo, 'editor.redo exists');
    },

    testAppFunctionality() {
        this.log('App Functionality', 'section');
        
        if (!window.topologyEditor) {
            this.log('Skipping app functionality tests - editor not loaded (run on index.html)', 'info');
            return;
        }
        
        const editor = window.topologyEditor;
        const initialCount = editor.objects.length;
        
        // Test 1: Can add device (signature: addDeviceAtPosition(type, x, y))
        try {
            editor.addDeviceAtPosition('SA-40C', 100, 100);
            this.assertEqual(editor.objects.length, initialCount + 1, 'Device added to objects');
            
            // Verify the device was created correctly
            const newDevice = editor.objects[editor.objects.length - 1];
            this.assert(newDevice && newDevice.type === 'device', 'New device has correct type');
            
            // Clean up
            editor.undo();
        } catch (e) {
            this.assert(false, 'Can add device', e.message);
        }
        
        // Test 2: Draw doesn't throw
        try {
            editor.draw();
            this.assert(true, 'draw() executes without error');
        } catch (e) {
            this.assert(false, 'draw() executes without error', e.message);
        }
        
        // Test 3: History works
        const historyBefore = editor.historyIndex;
        editor.saveState();
        this.assert(editor.historyIndex >= historyBefore, 'saveState updates history');
    },

    // ========== SPECIFIC MODULE TESTS (for future modules) ==========

    testDrawingModule() {
        this.log('Drawing Module (DrawingManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.DrawingManager, 'DrawingManager class exists');
        
        if (!window.DrawingManager) {
            this.log('DrawingManager not loaded - skipping', 'warn');
            return;
        }
        
        // Test 2: Can instantiate (with mock editor)
        let dm;
        try {
            const mockEditor = { 
                ctx: {}, 
                canvas: { width: 800, height: 600 }, 
                draw: () => {},
                zoom: 1,
                panOffset: { x: 0, y: 0 },
                darkMode: false,
                objects: []
            };
            dm = new DrawingManager(mockEditor);
            this.assert(true, 'DrawingManager instantiates');
        } catch (e) {
            this.assert(false, 'DrawingManager instantiates', e.message);
            return;
        }
        
        // Test 3: Methods exist
        this.assertFunction(dm.draw, 'draw method exists');
        this.assertFunction(dm.drawObject, 'drawObject method exists');
        this.assertFunction(dm.drawDevice, 'drawDevice method exists');
        this.assertFunction(dm.drawLink, 'drawLink method exists');
        this.assertFunction(dm.getContext, 'getContext method exists');
        
        // Test 4: Factory function
        this.assertFunction(window.createDrawingManager, 'createDrawingManager factory exists');
        
        // Test 5: Editor integration
        if (window.topologyEditor) {
            this.assertExists(window.topologyEditor.drawing, 'Editor has drawing property');
        }
        
        // Test 6: Utility methods (MIGRATED)
        this.assertFunction(dm.drawGrid, 'drawGrid method exists');
        this.assertFunction(dm.clearCanvas, 'clearCanvas method exists');
        this.assertFunction(dm.screenToWorld, 'screenToWorld method exists');
        this.assertFunction(dm.worldToScreen, 'worldToScreen method exists');
        this.assertFunction(dm.getVisibleBounds, 'getVisibleBounds method exists');
        
        // Test 7: Performance methods
        this.assertFunction(dm.requestRedraw, 'requestRedraw method exists');
        this.assertFunction(dm.markDirty, 'markDirty method exists');
        this.assertFunction(dm.isObjectVisible, 'isObjectVisible method exists');
        this.assertFunction(dm.getVisibleObjects, 'getVisibleObjects method exists');
        this.assertFunction(dm.getStats, 'getStats method exists');
        
        // Test 8: Coordinate conversion
        const worldPoint = dm.screenToWorld(100, 200);
        this.assert(typeof worldPoint.x === 'number', 'screenToWorld returns x coordinate');
        this.assert(typeof worldPoint.y === 'number', 'screenToWorld returns y coordinate');
        
        const screenPoint = dm.worldToScreen(100, 200);
        this.assert(typeof screenPoint.x === 'number', 'worldToScreen returns x coordinate');
        this.assert(typeof screenPoint.y === 'number', 'worldToScreen returns y coordinate');
        
        // Test 9: Visible bounds
        const bounds = dm.getVisibleBounds();
        this.assert(typeof bounds.minX === 'number', 'getVisibleBounds has minX');
        this.assert(typeof bounds.maxX === 'number', 'getVisibleBounds has maxX');
        this.assert(typeof bounds.width === 'number', 'getVisibleBounds has width');
        
        // Test 10: Object visibility (viewport culling)
        const mockDevice = { type: 'device', x: 100, y: 100, radius: 30 };
        const isVisible = dm.isObjectVisible(mockDevice);
        this.assert(typeof isVisible === 'boolean', 'isObjectVisible returns boolean');
        
        // Test 11: Get stats
        const stats = dm.getStats();
        this.assert(typeof stats.totalObjects === 'number', 'getStats has totalObjects');
        this.assert(typeof stats.visibleObjects === 'number', 'getStats has visibleObjects');
    },

    testPlatformMigration() {
        this.log('Platform Data Migration', 'section');
        
        if (!window.topologyEditor) {
            this.log('Skipping platform migration tests - editor not loaded', 'info');
            return;
        }
        
        const editor = window.topologyEditor;
        
        // Test 1: Both data sources exist
        this.assertExists(editor.platformData, 'Editor has platformData module');
        this.assertExists(editor.driveNetsPlatforms, 'Editor has legacy driveNetsPlatforms');
        
        // Test 2: getPlatformByOfficial works via module
        const platform1 = editor.getPlatformByOfficial('SA-40C');
        this.assertExists(platform1, 'getPlatformByOfficial finds SA-40C');
        this.assertEqual(platform1?.displayName, 'NCP1 (SA-40C)', 'SA-40C displayName correct');
        
        // Test 3: getPlatformsByCategory works via module
        const saPlatforms = editor.getPlatformsByCategory('SA');
        this.assert(saPlatforms.length > 0, 'getPlatformsByCategory returns SA platforms');
        this.assert(saPlatforms.some(p => p.official === 'SA-40C'), 'SA category includes SA-40C');
        
        // Test 4: Module and legacy data have same platforms
        const moduleCategories = editor.platformData.getCategories();
        const legacyCategories = Object.keys(editor.driveNetsPlatforms);
        this.assertEqual(moduleCategories.length, legacyCategories.length, 'Same number of categories');
        
        // Test 5: Interface generation still works
        const interfaces = editor.getInterfacesForPlatform('SA-40C', 'SA');
        this.assert(interfaces.length > 0, 'getInterfacesForPlatform returns interfaces');
    },

    testUIModule() {
        this.log('UI Module (UIManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.UIManager, 'UIManager class exists');
        
        if (!window.UIManager) {
            this.log('Skipping UIManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createUIManager, 'createUIManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { objects: [], selectedObjects: [] };
        let uiMgr;
        try {
            uiMgr = new UIManager(mockEditor);
            this.assert(true, 'UIManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'UIManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(uiMgr.showDeviceToolbar, 'uiMgr.showDeviceToolbar is a function');
        this.assertFunction(uiMgr.hideDeviceToolbar, 'uiMgr.hideDeviceToolbar is a function');
        this.assertFunction(uiMgr.showLinkToolbar, 'uiMgr.showLinkToolbar is a function');
        this.assertFunction(uiMgr.hideLinkToolbar, 'uiMgr.hideLinkToolbar is a function');
        this.assertFunction(uiMgr.showTextToolbar, 'uiMgr.showTextToolbar is a function');
        this.assertFunction(uiMgr.showShapeToolbar, 'uiMgr.showShapeToolbar is a function');
        this.assertFunction(uiMgr.showToolbar, 'uiMgr.showToolbar is a function');
        this.assertFunction(uiMgr.hideToolbar, 'uiMgr.hideToolbar is a function');
        this.assertFunction(uiMgr.hideAllToolbars, 'uiMgr.hideAllToolbars is a function');
        this.assertFunction(uiMgr.showDeviceEditor, 'uiMgr.showDeviceEditor is a function');
        this.assertFunction(uiMgr.showLinkEditor, 'uiMgr.showLinkEditor is a function');
        this.assertFunction(uiMgr.showLinkDetails, 'uiMgr.showLinkDetails is a function');
        this.assertFunction(uiMgr.getActiveToolbarType, 'uiMgr.getActiveToolbarType is a function');
        this.assertFunction(uiMgr.hasActiveToolbar, 'uiMgr.hasActiveToolbar is a function');
    },

    testMinimapModule() {
        this.log('Minimap Module (MinimapManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.MinimapManager, 'MinimapManager class exists');
        
        if (!window.MinimapManager) {
            this.log('Skipping MinimapManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createMinimapManager, 'createMinimapManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { objects: [] };
        let minimapMgr;
        try {
            minimapMgr = new MinimapManager(mockEditor);
            this.assert(true, 'MinimapManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'MinimapManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(minimapMgr.setup, 'minimapMgr.setup is a function');
        this.assertFunction(minimapMgr.toggle, 'minimapMgr.toggle is a function');
        this.assertFunction(minimapMgr.show, 'minimapMgr.show is a function');
        this.assertFunction(minimapMgr.hide, 'minimapMgr.hide is a function');
        this.assertFunction(minimapMgr.isVisible, 'minimapMgr.isVisible is a function');
        this.assertFunction(minimapMgr.render, 'minimapMgr.render is a function');
        this.assertFunction(minimapMgr.navigateFromClick, 'minimapMgr.navigateFromClick is a function');
        this.assertFunction(minimapMgr.getBounds, 'minimapMgr.getBounds is a function');
        this.assertFunction(minimapMgr.getElement, 'minimapMgr.getElement is a function');
        this.assertFunction(minimapMgr.getCanvas, 'minimapMgr.getCanvas is a function');
        this.assertFunction(minimapMgr.isDragging, 'minimapMgr.isDragging is a function');
        
        // Test 5: getBounds returns object with expected properties
        const bounds = minimapMgr.getBounds();
        this.assertExists(bounds, 'getBounds returns object');
        this.assert(typeof bounds.minX === 'number', 'bounds.minX is number');
        this.assert(typeof bounds.width === 'number', 'bounds.width is number');
    },

    testLinkEditorModule() {
        this.log('Link Editor Module (LinkEditorModal)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.LinkEditorModal, 'LinkEditorModal class exists');
        
        if (!window.LinkEditorModal) {
            this.log('Skipping LinkEditorModal tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createLinkEditorModal, 'createLinkEditorModal factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { 
            objects: [],
            events: { emit: () => {} },
            showLinkDetails: () => {},
            hideLinkDetails: () => {},
            saveLinkDetails: () => {},
            populateLinkTableFields: () => {},
            checkLinkTableValidity: () => ({ valid: true, errors: [] }),
            setupLinkTableValidation: () => {}
        };
        let linkEditor;
        try {
            linkEditor = new LinkEditorModal(mockEditor);
            this.assert(true, 'LinkEditorModal instantiates with editor');
        } catch (e) {
            this.assert(false, 'LinkEditorModal instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(linkEditor.show, 'linkEditor.show is a function');
        this.assertFunction(linkEditor.hide, 'linkEditor.hide is a function');
        this.assertFunction(linkEditor.save, 'linkEditor.save is a function');
        this.assertFunction(linkEditor.getIsVisible, 'linkEditor.getIsVisible is a function');
        this.assertFunction(linkEditor.getCurrentLink, 'linkEditor.getCurrentLink is a function');
        this.assertFunction(linkEditor.populateFields, 'linkEditor.populateFields is a function');
        this.assertFunction(linkEditor.validateForm, 'linkEditor.validateForm is a function');
        this.assertFunction(linkEditor.getFormData, 'linkEditor.getFormData is a function');
        this.assertFunction(linkEditor.getEditingChain, 'linkEditor.getEditingChain is a function');
        this.assertFunction(linkEditor.setEditingChain, 'linkEditor.setEditingChain is a function');
        this.assertFunction(linkEditor.getTableElement, 'linkEditor.getTableElement is a function');
        this.assertFunction(linkEditor.getModalElement, 'linkEditor.getModalElement is a function');
        this.assertFunction(linkEditor.focusFirstInput, 'linkEditor.focusFirstInput is a function');
        
        // Test 5: Initial state is correct
        this.assert(linkEditor.getIsVisible() === false, 'Initial visibility is false');
        this.assert(linkEditor.getCurrentLink() === null, 'Initial currentLink is null');
        this.assert(Array.isArray(linkEditor.getEditingChain()), 'getEditingChain returns array');
        this.assertEqual(linkEditor.getEditingChain().length, 0, 'Initial editingChain is empty');
        
        // Test 6: setEditingChain works
        const mockChain = [{ id: 'l1' }, { id: 'l2' }];
        linkEditor.setEditingChain(mockChain);
        this.assertEqual(linkEditor.getEditingChain().length, 2, 'setEditingChain updates chain');
        
        // Test 7: validateForm returns result
        const validity = linkEditor.validateForm();
        this.assertExists(validity, 'validateForm returns result');
        this.assert(validity.valid === true, 'validateForm returns valid: true for mock');
        
        // Test 8: getFormData returns object with link
        const formData = linkEditor.getFormData();
        this.assertExists(formData, 'getFormData returns object');
        this.assert('link' in formData, 'formData has link property');
        
        // Test 9: Editor integration check
        if (window.topologyEditor && window.topologyEditor.linkEditor) {
            this.assertExists(window.topologyEditor.linkEditor, 'Editor has linkEditor property');
            this.assert(window.topologyEditor.linkEditor instanceof LinkEditorModal, 
                'editor.linkEditor is LinkEditorModal instance');
        }
        
        // Test 10: Modal UI setup methods (MIGRATED)
        this.assertFunction(linkEditor.setupModalDragging, 'setupModalDragging method exists');
        this.assertFunction(linkEditor.setupModalResize, 'setupModalResize method exists');
        this.assertFunction(linkEditor.setupResponsiveColumns, 'setupResponsiveColumns method exists');
        
        // Test 11: Hide methods (MIGRATED)
        this.assertFunction(linkEditor.forceHide, 'forceHide method exists');
        this.assertFunction(linkEditor.checkValidity, 'checkValidity method exists');
        this.assertFunction(linkEditor.saveQuiet, 'saveQuiet method exists');
        
        // Test 12: checkValidity returns correct structure
        const validityResult = linkEditor.checkValidity();
        this.assertExists(validityResult, 'checkValidity returns result');
        this.assert('valid' in validityResult, 'checkValidity result has valid property');
        this.assert('errors' in validityResult, 'checkValidity result has errors property');
        
        // Test 13: Floating labels method (MIGRATED)
        this.assertFunction(linkEditor.initFloatingLabels, 'initFloatingLabels method exists');
        
        // Test 14: Table value management methods (MIGRATED)
        this.assertFunction(linkEditor.updateValue, 'updateValue method exists');
        this.assertFunction(linkEditor.updateCalculatedFields, 'updateCalculatedFields method exists');
        this.assertFunction(linkEditor.resetFields, 'resetFields method exists');
        this.assertFunction(linkEditor.copyAsMarkdown, 'copyAsMarkdown method exists');
        
        // Test 15: Static field mappings exist
        this.assertExists(LinkEditorModal.FIELD_MAPPINGS, 'FIELD_MAPPINGS static property exists');
        this.assertExists(LinkEditorModal.LINK_PROPERTIES, 'LINK_PROPERTIES static property exists');
        this.assert(Object.keys(LinkEditorModal.FIELD_MAPPINGS).length > 20, 'FIELD_MAPPINGS has >20 entries');
        this.assert(LinkEditorModal.LINK_PROPERTIES.length > 20, 'LINK_PROPERTIES has >20 entries');
        
        // Test 16: Validation error display methods (MIGRATED)
        this.assertFunction(linkEditor.formatValidationErrors, 'formatValidationErrors method exists');
        this.assertFunction(linkEditor.showValidationErrorToast, 'showValidationErrorToast method exists');
        
        // Test 17: formatValidationErrors works
        const testErrors = [
            { fieldName: 'Test Field', value: '123', error: 'Invalid' }
        ];
        const formatted = linkEditor.formatValidationErrors(testErrors);
        this.assert(typeof formatted === 'string', 'formatValidationErrors returns string');
        this.assert(formatted.includes('Test Field'), 'formatValidationErrors includes field name');
        
        // Test 18: Input validation methods (MIGRATED)
        this.assertFunction(linkEditor.validateVlanInput, 'validateVlanInput method exists');
        this.assertFunction(linkEditor.validateIPv4, 'validateIPv4 method exists');
        this.assertFunction(linkEditor.validateIPv6, 'validateIPv6 method exists');
        this.assertFunction(linkEditor.validateIpAddress, 'validateIpAddress method exists');
        
        // Test 19: VLAN validation
        const vlanValid = linkEditor.validateVlanInput('100');
        this.assert(vlanValid.valid === true, 'VLAN 100 is valid');
        const vlanRange = linkEditor.validateVlanInput('100-200');
        this.assert(vlanRange.valid === true, 'VLAN range 100-200 is valid');
        const vlanInvalid = linkEditor.validateVlanInput('5000');
        this.assert(vlanInvalid.valid === false, 'VLAN 5000 is invalid');
        
        // Test 20: IPv4 validation
        const ipv4Valid = linkEditor.validateIPv4('192.168.1.1');
        this.assert(ipv4Valid.valid === true, 'IPv4 192.168.1.1 is valid');
        const ipv4Cidr = linkEditor.validateIPv4('10.0.0.0/24');
        this.assert(ipv4Cidr.valid === true, 'IPv4 with CIDR is valid');
        const ipv4Invalid = linkEditor.validateIPv4('999.999.999.999');
        this.assert(ipv4Invalid.valid === false, 'IPv4 999.999.999.999 is invalid');
        
        // Test 21: IPv6 validation
        const ipv6Valid = linkEditor.validateIPv6('::1');
        this.assert(ipv6Valid.valid === true, 'IPv6 ::1 is valid');
        const ipv6Invalid = linkEditor.validateIPv6('invalid');
        this.assert(ipv6Invalid.valid === false, 'IPv6 "invalid" is invalid');
        
        // Test 22: VLAN field management methods (MIGRATED)
        this.assertFunction(linkEditor.updateVlanFieldsVisibility, 'updateVlanFieldsVisibility method exists');
        this.assertFunction(linkEditor.deriveCategoryFromModel, 'deriveCategoryFromModel method exists');
        this.assertFunction(linkEditor.showToast, 'showToast method exists');
        
        // Test 23: deriveCategoryFromModel works
        this.assertEqual(linkEditor.deriveCategoryFromModel('SA-40C'), 'SA', 'SA-40C derives to SA');
        this.assertEqual(linkEditor.deriveCategoryFromModel('CL-32C'), 'CL', 'CL-32C derives to CL');
        this.assertEqual(linkEditor.deriveCategoryFromModel('NCM-1'), 'DNAAS', 'NCM-1 derives to DNAAS');
        this.assertEqual(linkEditor.deriveCategoryFromModel('AI-100'), 'NC-AI', 'AI-100 derives to NC-AI');
        this.assertEqual(linkEditor.deriveCategoryFromModel(''), '', 'Empty string returns empty');
        
        // Test 24: Auto-save methods (MIGRATED)
        this.assertFunction(linkEditor.autoSave, 'autoSave method exists');
        this.assertFunction(linkEditor.saveQuietFull, 'saveQuietFull method exists');
        
        // Test 25: Interface population methods (MIGRATED)
        this.assertFunction(linkEditor.populateInterfacesForPlatform, 'populateInterfacesForPlatform method exists');
        this.assertFunction(linkEditor.handleCustomInterfaceInput, 'handleCustomInterfaceInput method exists');
        
        // Test 26: Full validity check (MIGRATED)
        this.assertFunction(linkEditor.checkLinkTableValidity, 'checkLinkTableValidity method exists');
        const fullValidity = linkEditor.checkLinkTableValidity();
        this.assert(typeof fullValidity === 'object', 'checkLinkTableValidity returns object');
        this.assert(typeof fullValidity.valid === 'boolean', 'checkLinkTableValidity has valid property');
        this.assert(Array.isArray(fullValidity.errors), 'checkLinkTableValidity has errors array');
        
        // Test 27: Field helper methods (MIGRATED)
        this.assertFunction(linkEditor.setFieldValue, 'setFieldValue method exists');
        this.assertFunction(linkEditor.updateIpAddressFieldVisibility, 'updateIpAddressFieldVisibility method exists');
        this.assertFunction(linkEditor.populateModelsForCategory, 'populateModelsForCategory method exists');
        this.assertFunction(linkEditor.validateIpField, 'validateIpField method exists');
        this.assertFunction(linkEditor.validateVlanField, 'validateVlanField method exists');
        
        // Test 28: DNAAS and detection methods (MIGRATED)
        this.assertFunction(linkEditor.showDnaasAutoFillIndicator, 'showDnaasAutoFillIndicator method exists');
        this.assertFunction(linkEditor.detectModelFromDeviceName, 'detectModelFromDeviceName method exists');
        this.assertFunction(linkEditor.updateStackColumnHeaders, 'updateStackColumnHeaders method exists');
        
        // Test 29: detectModelFromDeviceName works
        this.assertEqual(linkEditor.detectModelFromDeviceName('DNAAS-LEAF-1'), 'NCM-1600', 'LEAF device detected');
        this.assertEqual(linkEditor.detectModelFromDeviceName('YOR_PE-1'), 'SA-36CD-S', 'PE device detected');
        this.assertEqual(linkEditor.detectModelFromDeviceName('MY-CE-1'), 'SA-40C', 'CE device detected');
        
        // Test 30: Platform cascading method (MIGRATED)
        this.assertFunction(linkEditor.setupPlatformCascading, 'setupPlatformCascading method exists');
        
        // Test 31: Dropdown population methods (MIGRATED)
        this.assertFunction(linkEditor.populatePlatformDropdown, 'populatePlatformDropdown method exists');
        this.assertFunction(linkEditor.populateInterfaceDropdown, 'populateInterfaceDropdown method exists');
        this.assertFunction(linkEditor.populateTransceiverDropdown, 'populateTransceiverDropdown method exists');
        
        // Test 32: Static data exists
        this.assertExists(LinkEditorModal.FIELD_MAPPINGS, 'FIELD_MAPPINGS static data exists');
        this.assertExists(LinkEditorModal.LINK_PROPERTIES, 'LINK_PROPERTIES static data exists');
    },
    
    // =========================================================================
    // Groups Module Tests
    // =========================================================================
    testGroupsModule() {
        this.log('Groups Module (GroupManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.GroupManager, 'GroupManager class exists');
        
        if (!window.GroupManager) {
            this.log('Skipping GroupManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createGroupManager, 'createGroupManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { 
            objects: [], 
            selectedObjects: [],
            selectedObject: null,
            showToast: () => {},
            saveState: () => {},
            draw: () => {}
        };
        let groups;
        try {
            groups = new GroupManager(mockEditor);
            this.assert(true, 'GroupManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'GroupManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(groups.generateId, 'groups.generateId is a function');
        this.assertFunction(groups.findLeader, 'groups.findLeader is a function');
        this.assertFunction(groups.groupSelected, 'groups.groupSelected is a function');
        this.assertFunction(groups.ungroupSelected, 'groups.ungroupSelected is a function');
        this.assertFunction(groups.getMembers, 'groups.getMembers is a function');
        this.assertFunction(groups.isGrouped, 'groups.isGrouped is a function');
        this.assertFunction(groups.expandSelection, 'groups.expandSelection is a function');
        this.assertFunction(groups.validate, 'groups.validate is a function');
        this.assertFunction(groups.setupDrag, 'groups.setupDrag is a function');
        
        // Test 5: generateId returns unique IDs
        const id1 = groups.generateId();
        const id2 = groups.generateId();
        this.assert(id1.startsWith('group_'), 'generateId starts with group_');
        this.assert(id1 !== id2, 'generateId returns unique IDs');
        
        // Test 6: findLeader works
        const testObjects = [
            { id: 'a', x: 0, y: 0 },
            { id: 'b', x: 100, y: 0 },  // rightmost
            { id: 'c', x: 50, y: 50 }
        ];
        const leader = groups.findLeader(testObjects);
        this.assertEqual(leader.id, 'b', 'findLeader finds rightmost object');
        
        // Test 7: isGrouped works
        this.assert(groups.isGrouped({ groupId: 'test' }) === true, 'isGrouped returns true for grouped');
        this.assert(groups.isGrouped({ groupId: null }) === false, 'isGrouped returns false for ungrouped');
        this.assert(groups.isGrouped(null) === false, 'isGrouped handles null');
        
        // Test 8: Editor has groups property
        this.assertExists(topologyEditor.groups, 'Editor has groups property');
    },
    
    // =========================================================================
    // Toolbar Module Tests
    // =========================================================================
    testToolbarModule() {
        this.log('Toolbar Module (ToolbarManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.ToolbarManager, 'ToolbarManager class exists');
        
        if (!window.ToolbarManager) {
            this.log('Skipping ToolbarManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createToolbarManager, 'createToolbarManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { 
            currentTool: 'select',
            setMode: () => {},
            toggleTool: () => {},
            draw: () => {}
        };
        let toolbar;
        try {
            toolbar = new ToolbarManager(mockEditor);
            this.assert(true, 'ToolbarManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'ToolbarManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(toolbar.setup, 'toolbar.setup is a function');
        this.assertFunction(toolbar.safeAddListener, 'toolbar.safeAddListener is a function');
        this.assertFunction(toolbar.setupToolButtons, 'toolbar.setupToolButtons is a function');
        this.assertFunction(toolbar.setupDeviceStyleButtons, 'toolbar.setupDeviceStyleButtons is a function');
        this.assertFunction(toolbar.setupLinkStyleButtons, 'toolbar.setupLinkStyleButtons is a function');
        this.assertFunction(toolbar.setupFontButtons, 'toolbar.setupFontButtons is a function');
        this.assertFunction(toolbar.updateButtonStates, 'toolbar.updateButtonStates is a function');
        
        // Test 5: Editor has toolbarMgr property
        this.assertExists(topologyEditor.toolbarMgr, 'Editor has toolbarMgr property');
    },
    
    // =========================================================================
    // DNAAS Module Tests
    // =========================================================================
    testDnaasModule() {
        this.log('DNAAS Module (DnaasManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.DnaasManager, 'DnaasManager class exists');
        
        if (!window.DnaasManager) {
            this.log('Skipping DnaasManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createDnaasManager, 'createDnaasManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { 
            showToast: () => {},
            loadDnaasData: () => {}
        };
        let dnaas;
        try {
            dnaas = new DnaasManager(mockEditor);
            this.assert(true, 'DnaasManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'DnaasManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(dnaas.setupPanel, 'dnaas.setupPanel is a function');
        this.assertFunction(dnaas.startMultiBdDiscovery, 'dnaas.startMultiBdDiscovery is a function');
        this.assertFunction(dnaas.cancelDiscovery, 'dnaas.cancelDiscovery is a function');
        this.assertFunction(dnaas.dismissResult, 'dnaas.dismissResult is a function');
        this.assertFunction(dnaas.loadTopology, 'dnaas.loadTopology is a function');
        this.assertFunction(dnaas.loadData, 'dnaas.loadData is a function');
        this.assertFunction(dnaas.isRouter, 'dnaas.isRouter is a function');
        this.assertFunction(dnaas.populateSuggestions, 'dnaas.populateSuggestions is a function');
        
        // Test 5: isRouter detection works
        this.assert(dnaas.isRouter('NCM-SPINE-1') === true, 'NCM device detected as router');
        this.assert(dnaas.isRouter('NCF-LEAF-2') === true, 'NCF device detected as router');
        this.assert(dnaas.isRouter('PE-1') === false, 'PE device not detected as router');
        this.assert(dnaas.isRouter('CE-SITE-A') === false, 'CE device not detected as router');
        
        // Test 6: Editor has dnaas property
        this.assertExists(topologyEditor.dnaas, 'Editor has dnaas property');
    },
    
    // =========================================================================
    // Module Stats Tests
    // =========================================================================
    testModuleStats() {
        console.log('📦 Module Stats System');
        
        // Test 1: ModuleStats class exists
        this.assertExists(window.ModuleStats, 'ModuleStats class exists');
        
        // Test 2: Core methods exist
        this.assertFunction(ModuleStats.register, 'register method exists');
        this.assertFunction(ModuleStats.getSummary, 'getSummary method exists');
        this.assertFunction(ModuleStats.print, 'print method exists');
        this.assertFunction(ModuleStats.getHealth, 'getHealth method exists');
        
        // Test 3: getSummary returns proper structure
        const summary = ModuleStats.getSummary();
        this.assertExists(summary, 'getSummary returns object');
        this.assert(typeof summary.totalModules === 'number', 'summary has totalModules');
        this.assert(typeof summary.loadedModules === 'number', 'summary has loadedModules');
        this.assert(typeof summary.modules === 'object', 'summary has modules object');
        
        // Test 4: Health check works
        const health = ModuleStats.getHealth();
        this.assert(['healthy', 'degraded', 'critical'].includes(health), 'getHealth returns valid status');
    },

    testMenusModule() {
        this.log('Menus Module (MenuManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.MenuManager, 'MenuManager class exists');
        
        if (!window.MenuManager) {
            this.log('Skipping MenuManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createMenuManager, 'createMenuManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { objects: [], selectedObjects: [] };
        let menuMgr;
        try {
            menuMgr = new MenuManager(mockEditor);
            this.assert(true, 'MenuManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'MenuManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(menuMgr.showContextMenu, 'menuMgr.showContextMenu is a function');
        this.assertFunction(menuMgr.hideContextMenu, 'menuMgr.hideContextMenu is a function');
        this.assertFunction(menuMgr.showBackgroundMenu, 'menuMgr.showBackgroundMenu is a function');
        this.assertFunction(menuMgr.showBulkMenu, 'menuMgr.showBulkMenu is a function');
        this.assertFunction(menuMgr.showMarqueeMenu, 'menuMgr.showMarqueeMenu is a function');
        this.assertFunction(menuMgr.showMultiSelectMenu, 'menuMgr.showMultiSelectMenu is a function');
        this.assertFunction(menuMgr.handleCopyStyle, 'menuMgr.handleCopyStyle is a function');
        this.assertFunction(menuMgr.handleDuplicate, 'menuMgr.handleDuplicate is a function');
        this.assertFunction(menuMgr.handleDelete, 'menuMgr.handleDelete is a function');
        this.assertFunction(menuMgr.handleLayerToFront, 'menuMgr.handleLayerToFront is a function');
        this.assertFunction(menuMgr.isContextMenuVisible, 'menuMgr.isContextMenuVisible is a function');
        this.assertFunction(menuMgr.hideAllMenus, 'menuMgr.hideAllMenus is a function');
    },

    testLinksModule() {
        this.log('Links Module (LinkManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.LinkManager, 'LinkManager class exists');
        
        if (!window.LinkManager) {
            this.log('Skipping LinkManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createLinkManager, 'createLinkManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockLink1 = { type: 'link', id: 'l1', device1: 'd1', device2: null, mergedWith: 'l2' };
        const mockLink2 = { type: 'link', id: 'l2', device1: null, device2: 'd2', parentLink: 'l1' };
        const mockEditor = { 
            objects: [
                { type: 'device', id: 'd1' },
                { type: 'device', id: 'd2' },
                mockLink1,
                mockLink2
            ], 
            selectedObjects: []
        };
        let linkMgr;
        try {
            linkMgr = new LinkManager(mockEditor);
            this.assert(true, 'LinkManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'LinkManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(linkMgr.findAt, 'linkMgr.findAt is a function');
        this.assertFunction(linkMgr.getAll, 'linkMgr.getAll is a function');
        this.assertFunction(linkMgr.getById, 'linkMgr.getById is a function');
        this.assertFunction(linkMgr.analyzeBULChain, 'linkMgr.analyzeBULChain is a function');
        this.assertFunction(linkMgr.getAllMerged, 'linkMgr.getAllMerged is a function');
        this.assertFunction(linkMgr.getBULEndpoints, 'linkMgr.getBULEndpoints is a function');
        this.assertFunction(linkMgr.isHead, 'linkMgr.isHead is a function');
        this.assertFunction(linkMgr.isTail, 'linkMgr.isTail is a function');
        this.assertFunction(linkMgr.getEndpoints, 'linkMgr.getEndpoints is a function');
        this.assertFunction(linkMgr.showToolbar, 'linkMgr.showToolbar is a function');
        
        // Test 5: getAll filters correctly
        const allLinks = linkMgr.getAll();
        this.assert(Array.isArray(allLinks), 'getAll returns array');
        this.assertEqual(allLinks.length, 2, 'getAll returns only links (2)');
        
        // Test 6: getById works
        const link1 = linkMgr.getById('l1');
        this.assertExists(link1, 'getById finds link l1');
        
        // Test 7: BUL chain position detection
        this.assert(linkMgr.isHead(mockLink1), 'Link1 is HEAD (no parentLink)');
        this.assert(!linkMgr.isTail(mockLink1), 'Link1 is NOT TAIL (has mergedWith)');
        this.assert(!linkMgr.isHead(mockLink2), 'Link2 is NOT HEAD (has parentLink)');
        this.assert(linkMgr.isTail(mockLink2), 'Link2 is TAIL (no mergedWith)');
        
        // Test 8: getCount works
        this.assertEqual(linkMgr.getCount(), 2, 'getCount returns 2');
        
        // Test 9: hasTerminalPoints
        const tps = linkMgr.hasTerminalPoints(mockLink1);
        this.assert(typeof tps.start === 'boolean', 'hasTerminalPoints returns start boolean');
        this.assert(typeof tps.end === 'boolean', 'hasTerminalPoints returns end boolean');
        
        // Test 10: getChainPosition
        const pos = linkMgr.getChainPosition(mockLink1);
        this.assert(pos.isHead === true, 'getChainPosition identifies HEAD');
        this.assert(typeof pos.chainLength === 'number', 'getChainPosition has chainLength');
    },

    testDevicesModule() {
        this.log('Devices Module (DeviceManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.DeviceManager, 'DeviceManager class exists');
        
        if (!window.DeviceManager) {
            this.log('Skipping DeviceManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createDeviceManager, 'createDeviceManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { 
            objects: [
                { type: 'device', id: 'd1', label: 'PE-1' },
                { type: 'device', id: 'd2', label: 'PE-2' },
                { type: 'link', id: 'l1' }
            ], 
            selectedObjects: [],
            platformData: { getCategories: () => ['SA', 'CL'] }
        };
        let deviceMgr;
        try {
            deviceMgr = new DeviceManager(mockEditor);
            this.assert(true, 'DeviceManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'DeviceManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(deviceMgr.add, 'deviceMgr.add is a function');
        this.assertFunction(deviceMgr.addAtPosition, 'deviceMgr.addAtPosition is a function');
        this.assertFunction(deviceMgr.findAt, 'deviceMgr.findAt is a function');
        this.assertFunction(deviceMgr.getAll, 'deviceMgr.getAll is a function');
        this.assertFunction(deviceMgr.getSelected, 'deviceMgr.getSelected is a function');
        this.assertFunction(deviceMgr.getById, 'deviceMgr.getById is a function');
        this.assertFunction(deviceMgr.getByLabel, 'deviceMgr.getByLabel is a function');
        this.assertFunction(deviceMgr.checkCollision, 'deviceMgr.checkCollision is a function');
        this.assertFunction(deviceMgr.showToolbar, 'deviceMgr.showToolbar is a function');
        this.assertFunction(deviceMgr.getCategories, 'deviceMgr.getCategories is a function');
        this.assertFunction(deviceMgr.getPlatforms, 'deviceMgr.getPlatforms is a function');
        
        // Test 5: getAll filters correctly
        const allDevices = deviceMgr.getAll();
        this.assert(Array.isArray(allDevices), 'getAll returns array');
        this.assertEqual(allDevices.length, 2, 'getAll returns only devices (2)');
        
        // Test 6: getById works
        const device1 = deviceMgr.getById('d1');
        this.assertExists(device1, 'getById finds device d1');
        this.assertEqual(device1?.label, 'PE-1', 'getById returns correct device');
        
        // Test 7: getByLabel works
        const device2 = deviceMgr.getByLabel('PE-2');
        this.assertExists(device2, 'getByLabel finds PE-2');
        
        // Test 8: getCount works
        this.assertEqual(deviceMgr.getCount(), 2, 'getCount returns 2');
        
        // Test 9: getCategories works with platformData
        const categories = deviceMgr.getCategories();
        this.assert(Array.isArray(categories), 'getCategories returns array');
        this.assert(categories.includes('SA'), 'Categories include SA');
        
        // Test 10: Naming functions (MIGRATED)
        this.assertFunction(deviceMgr.getNextLabel, 'getNextLabel method exists');
        this.assertFunction(deviceMgr.isNameUnique, 'isNameUnique method exists');
        this.assertFunction(deviceMgr.updateCounters, 'updateCounters method exists');
        
        // Test 11: isNameUnique works
        this.assert(deviceMgr.isNameUnique('PE-3'), 'PE-3 is unique');
        this.assert(!deviceMgr.isNameUnique('PE-1'), 'PE-1 is not unique');
    },

    testShapesModule() {
        this.log('Shapes Module (ShapeManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.ShapeManager, 'ShapeManager class exists');
        
        if (!window.ShapeManager) {
            this.log('Skipping ShapeManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createShapeManager, 'createShapeManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { objects: [], selectedObjects: [] };
        let shapeMgr;
        try {
            shapeMgr = new ShapeManager(mockEditor);
            this.assert(true, 'ShapeManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'ShapeManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(shapeMgr.create, 'shapeMgr.create is a function');
        this.assertFunction(shapeMgr.findAt, 'shapeMgr.findAt is a function');
        this.assertFunction(shapeMgr.getAll, 'shapeMgr.getAll is a function');
        this.assertFunction(shapeMgr.selectType, 'shapeMgr.selectType is a function');
        this.assertFunction(shapeMgr.enterPlacementMode, 'shapeMgr.enterPlacementMode is a function');
        this.assertFunction(shapeMgr.draw, 'shapeMgr.draw is a function');
        this.assertFunction(shapeMgr.getShapeTypes, 'shapeMgr.getShapeTypes is a function');
        
        // Test 5: getAll returns array from mock
        const allShapes = shapeMgr.getAll();
        this.assert(Array.isArray(allShapes), 'getAll returns array');
        
        // Test 6: getShapeTypes returns expected types
        const types = shapeMgr.getShapeTypes();
        this.assert(types.includes('rectangle'), 'Has rectangle type');
        this.assert(types.includes('ellipse'), 'Has ellipse type');
        this.assert(types.includes('line'), 'Has line type');
    },

    testTextModule() {
        this.log('Text Module (TextManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.TextManager, 'TextManager class exists');
        
        if (!window.TextManager) {
            this.log('Skipping TextManager tests - class not loaded', 'warn');
            return;
        }
        
        // Test 2: Factory function exists
        this.assertFunction(window.createTextManager, 'createTextManager factory exists');
        
        // Test 3: Can instantiate with mock editor
        const mockEditor = { objects: [], selectedObjects: [] };
        let textMgr;
        try {
            textMgr = new TextManager(mockEditor);
            this.assert(true, 'TextManager instantiates with editor');
        } catch (e) {
            this.assert(false, 'TextManager instantiates', e.message);
            return;
        }
        
        // Test 4: Key methods exist
        this.assertFunction(textMgr.create, 'textMgr.create is a function');
        this.assertFunction(textMgr.findAt, 'textMgr.findAt is a function');
        this.assertFunction(textMgr.getAll, 'textMgr.getAll is a function');
        this.assertFunction(textMgr.getSelected, 'textMgr.getSelected is a function');
        this.assertFunction(textMgr.showEditor, 'textMgr.showEditor is a function');
        this.assertFunction(textMgr.hideEditor, 'textMgr.hideEditor is a function');
        this.assertFunction(textMgr.updateSize, 'textMgr.updateSize is a function');
        this.assertFunction(textMgr.showToolbar, 'textMgr.showToolbar is a function');
        this.assertFunction(textMgr.attachToLink, 'textMgr.attachToLink is a function');
        this.assertFunction(textMgr.enterPlacementMode, 'textMgr.enterPlacementMode is a function');
        
        // Test 5: getAll returns array from mock
        const allTexts = textMgr.getAll();
        this.assert(Array.isArray(allTexts), 'getAll returns array');
        this.assertEqual(allTexts.length, 0, 'getAll returns empty array for mock');
        
        // Test 6: getCount works
        this.assertEqual(textMgr.getCount(), 0, 'getCount returns 0 for empty');
    },

    testFilesModule() {
        this.log('Files Module (FileManager)', 'section');
        
        // Test 1: Class exists
        this.assertExists(window.FileManager, 'FileManager class exists');
        
        if (!window.FileManager) {
            this.log('FileManager not loaded - skipping', 'warn');
            return;
        }
        
        // Test 2: Can instantiate (with mock editor)
        let fm;
        try {
            const mockEditor = { objects: [], initializing: false };
            fm = new FileManager(mockEditor);
            this.assert(true, 'FileManager instantiates');
        } catch (e) {
            this.assert(false, 'FileManager instantiates', e.message);
            return;
        }
        
        // Test 3: Methods exist
        this.assertFunction(fm.scheduleAutoSave, 'scheduleAutoSave method exists');
        this.assertFunction(fm.autoSave, 'autoSave method exists');
        this.assertFunction(fm.loadAutoSave, 'loadAutoSave method exists');
        this.assertFunction(fm.exportJSON, 'exportJSON method exists');
        this.assertFunction(fm.importJSON, 'importJSON method exists');
        
        // Test 4: Properties
        this.assertExists(fm.autoSaveKey, 'autoSaveKey property exists');
        this.assert(fm.autoSaveDelay > 0, 'autoSaveDelay is positive');
        
        // Test 5: Factory function
        this.assertFunction(window.createFileManager, 'createFileManager factory exists');
        
        // Test 6: Editor integration
        if (window.topologyEditor) {
            this.assertExists(window.topologyEditor.files, 'Editor has files property');
        }
    },

    // ========== TEST RUNNERS ==========

    runModule(moduleName) {
        this.results = [];
        this.totalPassed = 0;
        this.totalFailed = 0;
        
        const tests = {
            'events': () => this.testEventsModule(),
            'geometry': () => this.testGeometryModule(),
            'platform': () => this.testPlatformDataModule(),
            'drawing': () => this.testDrawingModule(),
            'files': () => this.testFilesModule(),
            'text': () => this.testTextModule(),
            'shapes': () => this.testShapesModule(),
            'devices': () => this.testDevicesModule(),
            'links': () => this.testLinksModule(),
            'ui': () => this.testUIModule(),
            'menus': () => this.testMenusModule(),
            'minimap': () => this.testMinimapModule(),
            'linkeditor': () => this.testLinkEditorModule(),
            'groups': () => this.testGroupsModule(),
            'toolbar': () => this.testToolbarModule(),
            'dnaas': () => this.testDnaasModule(),
            'stats': () => this.testModuleStats(),
            'migration': () => this.testPlatformMigration(),
            'integration': () => this.testEditorIntegration(),
            'app': () => this.testAppFunctionality()
        };
        
        if (tests[moduleName]) {
            tests[moduleName]();
        } else {
            this.log(`Unknown module: ${moduleName}`, 'warn');
        }
        
        return this.getSummary();
    },

    runAll() {
        console.clear();
        this.log('🧪 TOPOLOGY MODULE TEST SUITE', 'info');
        this.log('================================\n', 'info');
        
        this.results = [];
        this.totalPassed = 0;
        this.totalFailed = 0;
        
        // Run all module tests
        this.testEventsModule();
        this.testGeometryModule();
        this.testPlatformDataModule();
        this.testDrawingModule();
        this.testFilesModule();
        this.testTextModule();
        this.testShapesModule();
        this.testDevicesModule();
        this.testLinksModule();
        this.testUIModule();
        this.testMenusModule();
        this.testMinimapModule();
        this.testLinkEditorModule();
        this.testGroupsModule();       // Object grouping
        this.testToolbarModule();      // Toolbar management
        this.testDnaasModule();        // DNAAS discovery
        this.testModuleStats();        // Module diagnostics
        this.testPlatformMigration();  // Migration verification
        this.testEditorIntegration();
        this.testAppFunctionality();
        
        return this.getSummary();
    },

    runIntegration() {
        this.results = [];
        this.totalPassed = 0;
        this.totalFailed = 0;
        
        this.testEditorIntegration();
        this.testAppFunctionality();
        
        return this.getSummary();
    },

    getSummary() {
        const total = this.totalPassed + this.totalFailed;
        const passRate = total > 0 ? Math.round((this.totalPassed / total) * 100) : 0;
        
        console.log('\n================================');
        console.log(`📊 RESULTS: ${this.totalPassed}/${total} passed (${passRate}%)`);
        
        if (this.totalFailed > 0) {
            console.log('\n❌ FAILED TESTS:');
            this.results.filter(r => !r.passed).forEach(r => {
                console.log(`   - ${r.name}${r.details ? ': ' + r.details : ''}`);
            });
        }
        
        console.log('================================\n');
        
        return {
            passed: this.totalPassed,
            failed: this.totalFailed,
            total: total,
            passRate: passRate,
            allPassed: this.totalFailed === 0,
            results: this.results
        };
    }
};

// Export for use
window.TopologyTests = TopologyTests;

console.log('TopologyTests module loaded - run TopologyTests.runAll() to test');
