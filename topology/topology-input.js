/**
 * topology-input.js - Input State Machine for Topology App
 * 
 * Manages all user input through a finite state machine pattern.
 * Each interaction state (idle, dragging, drawing, etc.) is handled
 * by a dedicated state handler for cleaner, more maintainable code.
 * 
 * @version 1.0.0
 * @date 2026-02-03
 */

// ============================================================================
// INPUT STATES
// ============================================================================

/**
 * Base class for all input state handlers
 */
class InputStateHandler {
    constructor(editor, inputManager) {
        this.editor = editor;
        this.inputManager = inputManager;
        this.name = 'base';
    }
    
    /**
     * Called when entering this state
     * @param {Object} context - Context data from previous state
     */
    enter(context = {}) {
        this.context = context;
    }
    
    /**
     * Called when exiting this state
     */
    exit() {
        this.context = null;
    }
    
    /**
     * Handle mouse down event
     * @param {MouseEvent} e - The mouse event
     * @returns {string|null} Next state name, or null to stay in current state
     */
    onMouseDown(e) { return null; }
    
    /**
     * Handle mouse move event
     * @param {MouseEvent} e - The mouse event
     * @returns {string|null} Next state name, or null to stay in current state
     */
    onMouseMove(e) { return null; }
    
    /**
     * Handle mouse up event
     * @param {MouseEvent} e - The mouse event
     * @returns {string|null} Next state name, or null to stay in current state
     */
    onMouseUp(e) { return null; }
    
    /**
     * Handle key down event
     * @param {KeyboardEvent} e - The keyboard event
     * @returns {string|null} Next state name, or null to stay in current state
     */
    onKeyDown(e) { return null; }
    
    /**
     * Handle key up event
     * @param {KeyboardEvent} e - The keyboard event
     * @returns {string|null} Next state name, or null to stay in current state
     */
    onKeyUp(e) { return null; }
    
    /**
     * Handle wheel/scroll event
     * @param {WheelEvent} e - The wheel event
     * @returns {string|null} Next state name, or null to stay in current state
     */
    onWheel(e) { return null; }
    
    /**
     * Handle double click event
     * @param {MouseEvent} e - The mouse event
     * @returns {string|null} Next state name, or null to stay in current state
     */
    onDoubleClick(e) { return null; }
    
    /**
     * Handle context menu event
     * @param {MouseEvent} e - The mouse event
     * @returns {string|null} Next state name, or null to stay in current state
     */
    onContextMenu(e) { return null; }
}

// ============================================================================
// IDLE STATE - Default state, waiting for user input
// ============================================================================

class IdleStateHandler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = 'idle';
    }
    
    onMouseDown(e) {
        // Delegate to editor's existing handleMouseDown for now
        // This will be refactored incrementally
        if (this.editor._originalHandleMouseDown) {
            this.editor._originalHandleMouseDown(e);
        }
        return null;
    }
    
    onMouseMove(e) {
        // Delegate to editor's existing handleMouseMove
        if (this.editor._originalHandleMouseMove) {
            this.editor._originalHandleMouseMove(e);
        }
        return null;
    }
    
    onMouseUp(e) {
        // Delegate to editor's existing handleMouseUp
        if (this.editor._originalHandleMouseUp) {
            this.editor._originalHandleMouseUp(e);
        }
        return null;
    }
    
    onKeyDown(e) {
        // Handle escape to cancel any pending operation
        if (e.key === 'Escape') {
            this.editor.events?.emit('input:escape');
        }
        
        // Delegate to editor's existing handleKeyDown
        if (this.editor._originalHandleKeyDown) {
            this.editor._originalHandleKeyDown(e);
        }
        return null;
    }
    
    onKeyUp(e) {
        if (this.editor._originalHandleKeyUp) {
            this.editor._originalHandleKeyUp(e);
        }
        return null;
    }
    
    onWheel(e) {
        if (this.editor._originalHandleWheel) {
            this.editor._originalHandleWheel(e);
        }
        return null;
    }
    
    onDoubleClick(e) {
        if (this.editor._originalHandleDoubleClick) {
            this.editor._originalHandleDoubleClick(e);
        }
        return null;
    }
    
    onContextMenu(e) {
        if (this.editor._originalHandleContextMenu) {
            this.editor._originalHandleContextMenu(e);
        }
        return null;
    }
}

// ============================================================================
// DRAGGING DEVICE STATE - When dragging a device
// ============================================================================

class DraggingDeviceHandler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = 'draggingDevice';
        this.device = null;
        this.startPos = null;
        this.offset = null;
    }
    
    enter(context = {}) {
        super.enter(context);
        this.device = context.device;
        this.startPos = context.startPos;
        this.offset = context.offset;
        this.editor.canvas.style.cursor = 'grabbing';
    }
    
    exit() {
        this.editor.canvas.style.cursor = 'default';
        this.device = null;
        this.startPos = null;
        this.offset = null;
        super.exit();
    }
    
    onMouseMove(e) {
        // Device dragging logic will be migrated here
        // For now, delegate to editor
        if (this.editor._originalHandleMouseMove) {
            this.editor._originalHandleMouseMove(e);
        }
        return null;
    }
    
    onMouseUp(e) {
        // Complete the drag operation
        if (this.editor._originalHandleMouseUp) {
            this.editor._originalHandleMouseUp(e);
        }
        return 'idle';
    }
    
    onKeyDown(e) {
        if (e.key === 'Escape') {
            // Cancel drag - restore original position
            this.editor.events?.emit('drag:cancelled', { device: this.device });
            return 'idle';
        }
        return null;
    }
}

// ============================================================================
// DRAGGING LINK STATE - When dragging a link segment
// ============================================================================

class DraggingLinkHandler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = 'draggingLink';
        this.link = null;
        this.dragType = null; // 'segment', 'endpoint', 'control'
    }
    
    enter(context = {}) {
        super.enter(context);
        this.link = context.link;
        this.dragType = context.dragType;
        this.editor.canvas.style.cursor = 'move';
    }
    
    exit() {
        this.editor.canvas.style.cursor = 'default';
        this.link = null;
        this.dragType = null;
        super.exit();
    }
    
    onMouseMove(e) {
        if (this.editor._originalHandleMouseMove) {
            this.editor._originalHandleMouseMove(e);
        }
        return null;
    }
    
    onMouseUp(e) {
        if (this.editor._originalHandleMouseUp) {
            this.editor._originalHandleMouseUp(e);
        }
        return 'idle';
    }
    
    onKeyDown(e) {
        if (e.key === 'Escape') {
            return 'idle';
        }
        return null;
    }
}

// ============================================================================
// DRAWING LINK STATE - When creating a new link
// ============================================================================

class DrawingLinkHandler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = 'drawingLink';
        this.startDevice = null;
        this.currentPos = null;
    }
    
    enter(context = {}) {
        super.enter(context);
        this.startDevice = context.startDevice;
        this.editor.canvas.style.cursor = 'crosshair';
    }
    
    exit() {
        this.editor.canvas.style.cursor = 'default';
        this.startDevice = null;
        this.currentPos = null;
        super.exit();
    }
    
    onMouseMove(e) {
        if (this.editor._originalHandleMouseMove) {
            this.editor._originalHandleMouseMove(e);
        }
        return null;
    }
    
    onMouseUp(e) {
        if (this.editor._originalHandleMouseUp) {
            this.editor._originalHandleMouseUp(e);
        }
        // Stay in drawing mode if continuous mode is enabled
        if (this.editor.linkContinuousMode) {
            return null;
        }
        return 'idle';
    }
    
    onKeyDown(e) {
        if (e.key === 'Escape') {
            this.editor.events?.emit('link:cancelled');
            return 'idle';
        }
        return null;
    }
}

// ============================================================================
// SELECTING STATE - Marquee selection
// ============================================================================

class SelectingHandler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = 'selecting';
        this.startPos = null;
        this.currentPos = null;
    }
    
    enter(context = {}) {
        super.enter(context);
        this.startPos = context.startPos;
        this.editor.canvas.style.cursor = 'crosshair';
    }
    
    exit() {
        this.editor.canvas.style.cursor = 'default';
        this.startPos = null;
        this.currentPos = null;
        super.exit();
    }
    
    onMouseMove(e) {
        if (this.editor._originalHandleMouseMove) {
            this.editor._originalHandleMouseMove(e);
        }
        return null;
    }
    
    onMouseUp(e) {
        if (this.editor._originalHandleMouseUp) {
            this.editor._originalHandleMouseUp(e);
        }
        return 'idle';
    }
    
    onKeyDown(e) {
        if (e.key === 'Escape') {
            return 'idle';
        }
        return null;
    }
}

// ============================================================================
// PANNING STATE - When panning the canvas
// ============================================================================

class PanningHandler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = 'panning';
        this.startOffset = null;
        this.startMouse = null;
    }
    
    enter(context = {}) {
        super.enter(context);
        this.startOffset = context.startOffset;
        this.startMouse = context.startMouse;
        this.editor.canvas.style.cursor = 'grabbing';
    }
    
    exit() {
        this.editor.canvas.style.cursor = 'default';
        this.startOffset = null;
        this.startMouse = null;
        super.exit();
    }
    
    onMouseMove(e) {
        if (this.editor._originalHandleMouseMove) {
            this.editor._originalHandleMouseMove(e);
        }
        return null;
    }
    
    onMouseUp(e) {
        return 'idle';
    }
    
    onKeyUp(e) {
        // Exit panning when space is released
        if (e.code === 'Space') {
            return 'idle';
        }
        return null;
    }
}

// ============================================================================
// TEXT EDITING STATE - When editing text inline
// ============================================================================

class TextEditingHandler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = 'textEditing';
        this.textObject = null;
    }
    
    enter(context = {}) {
        super.enter(context);
        this.textObject = context.textObject;
    }
    
    exit() {
        this.textObject = null;
        super.exit();
    }
    
    onMouseDown(e) {
        // Click outside text = finish editing
        const clickedText = this.editor.findTextAt?.(this.editor.getMousePos(e));
        if (clickedText !== this.textObject) {
            this.editor.events?.emit('text:editEnd', { text: this.textObject });
            return 'idle';
        }
        return null;
    }
    
    onKeyDown(e) {
        if (e.key === 'Escape') {
            this.editor.events?.emit('text:editCancel', { text: this.textObject });
            return 'idle';
        }
        if (e.key === 'Enter' && !e.shiftKey) {
            this.editor.events?.emit('text:editEnd', { text: this.textObject });
            return 'idle';
        }
        return null;
    }
}

// ============================================================================
// RESIZING SHAPE STATE - When resizing a shape
// ============================================================================

class ResizingShapeHandler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = 'resizingShape';
        this.shape = null;
        this.handle = null;
    }
    
    enter(context = {}) {
        super.enter(context);
        this.shape = context.shape;
        this.handle = context.handle;
    }
    
    exit() {
        this.shape = null;
        this.handle = null;
        super.exit();
    }
    
    onMouseMove(e) {
        if (this.editor._originalHandleMouseMove) {
            this.editor._originalHandleMouseMove(e);
        }
        return null;
    }
    
    onMouseUp(e) {
        if (this.editor._originalHandleMouseUp) {
            this.editor._originalHandleMouseUp(e);
        }
        return 'idle';
    }
    
    onKeyDown(e) {
        if (e.key === 'Escape') {
            return 'idle';
        }
        return null;
    }
}

// ============================================================================
// INPUT MANAGER - Main state machine controller
// ============================================================================

class InputManager {
    constructor(editor) {
        this.editor = editor;
        this.currentState = 'idle';
        this.previousState = null;
        this.stateHistory = [];
        this.maxHistory = 10;
        
        // Initialize state handlers
        this.handlers = {
            idle: new IdleStateHandler(editor, this),
            draggingDevice: new DraggingDeviceHandler(editor, this),
            draggingLink: new DraggingLinkHandler(editor, this),
            drawingLink: new DrawingLinkHandler(editor, this),
            selecting: new SelectingHandler(editor, this),
            panning: new PanningHandler(editor, this),
            textEditing: new TextEditingHandler(editor, this),
            resizingShape: new ResizingShapeHandler(editor, this),
        };
        
        // Debug mode
        this.debug = false;
        
        console.log('[InputManager] Initialized with states:', Object.keys(this.handlers));
    }
    
    /**
     * Get the current state handler
     * @returns {InputStateHandler}
     */
    getCurrentHandler() {
        return this.handlers[this.currentState] || this.handlers.idle;
    }
    
    /**
     * Transition to a new state
     * @param {string} newState - Name of the state to transition to
     * @param {Object} context - Context data for the new state
     */
    transition(newState, context = {}) {
        if (!this.handlers[newState]) {
            console.warn(`[InputManager] Unknown state: ${newState}`);
            return;
        }
        
        const oldState = this.currentState;
        
        // Exit current state
        this.getCurrentHandler().exit();
        
        // Record history
        this.stateHistory.push({
            from: oldState,
            to: newState,
            timestamp: Date.now()
        });
        if (this.stateHistory.length > this.maxHistory) {
            this.stateHistory.shift();
        }
        
        // Update state
        this.previousState = this.currentState;
        this.currentState = newState;
        
        // Enter new state
        this.handlers[newState].enter(context);
        
        // Emit event
        this.editor.events?.emit('input:stateChange', {
            from: oldState,
            to: newState,
            context
        });
        
        if (this.debug) {
            console.log(`[InputManager] ${oldState} -> ${newState}`, context);
        }
    }
    
    /**
     * Handle mouse down event
     * @param {MouseEvent} e
     */
    handleMouseDown(e) {
        const nextState = this.getCurrentHandler().onMouseDown(e);
        if (nextState) {
            this.transition(nextState);
        }
    }
    
    /**
     * Handle mouse move event
     * @param {MouseEvent} e
     */
    handleMouseMove(e) {
        const nextState = this.getCurrentHandler().onMouseMove(e);
        if (nextState) {
            this.transition(nextState);
        }
    }
    
    /**
     * Handle mouse up event
     * @param {MouseEvent} e
     */
    handleMouseUp(e) {
        const nextState = this.getCurrentHandler().onMouseUp(e);
        if (nextState) {
            this.transition(nextState);
        }
    }
    
    /**
     * Handle key down event
     * @param {KeyboardEvent} e
     */
    handleKeyDown(e) {
        const nextState = this.getCurrentHandler().onKeyDown(e);
        if (nextState) {
            this.transition(nextState);
        }
    }
    
    /**
     * Handle key up event
     * @param {KeyboardEvent} e
     */
    handleKeyUp(e) {
        const nextState = this.getCurrentHandler().onKeyUp(e);
        if (nextState) {
            this.transition(nextState);
        }
    }
    
    /**
     * Handle wheel event
     * @param {WheelEvent} e
     */
    handleWheel(e) {
        const nextState = this.getCurrentHandler().onWheel(e);
        if (nextState) {
            this.transition(nextState);
        }
    }
    
    /**
     * Handle double click event
     * @param {MouseEvent} e
     */
    handleDoubleClick(e) {
        const nextState = this.getCurrentHandler().onDoubleClick(e);
        if (nextState) {
            this.transition(nextState);
        }
    }
    
    /**
     * Handle context menu event
     * @param {MouseEvent} e
     */
    handleContextMenu(e) {
        const nextState = this.getCurrentHandler().onContextMenu(e);
        if (nextState) {
            this.transition(nextState);
        }
    }
    
    /**
     * Force transition to idle state
     */
    reset() {
        this.transition('idle');
    }
    
    /**
     * Check if in a specific state
     * @param {string} stateName
     * @returns {boolean}
     */
    isInState(stateName) {
        return this.currentState === stateName;
    }
    
    /**
     * Check if currently in an active operation (not idle)
     * @returns {boolean}
     */
    isActive() {
        return this.currentState !== 'idle';
    }
    
    /**
     * Register a custom state handler
     * @param {string} name - State name
     * @param {InputStateHandler} handler - The handler instance
     */
    registerState(name, handler) {
        if (this.handlers[name]) {
            console.warn(`[InputManager] Overwriting existing state: ${name}`);
        }
        this.handlers[name] = handler;
        console.log(`[InputManager] Registered state: ${name}`);
    }
    
    /**
     * Enable debug logging
     * @param {boolean} enabled
     */
    setDebug(enabled) {
        this.debug = enabled;
        console.log(`[InputManager] Debug mode: ${enabled ? 'ON' : 'OFF'}`);
    }
    
    /**
     * Get state info for debugging
     * @returns {Object}
     */
    getDebugInfo() {
        return {
            currentState: this.currentState,
            previousState: this.previousState,
            history: this.stateHistory,
            registeredStates: Object.keys(this.handlers)
        };
    }
}

// Export
window.InputManager = InputManager;
window.InputStateHandler = InputStateHandler;

// Export individual handlers for extension
window.IdleStateHandler = IdleStateHandler;
window.DraggingDeviceHandler = DraggingDeviceHandler;
window.DraggingLinkHandler = DraggingLinkHandler;
window.DrawingLinkHandler = DrawingLinkHandler;
window.SelectingHandler = SelectingHandler;
window.PanningHandler = PanningHandler;
window.TextEditingHandler = TextEditingHandler;
window.ResizingShapeHandler = ResizingShapeHandler;

window.createInputManager = function(editor) {
    return new InputManager(editor);
};

console.log('[topology-input.js] InputManager state machine loaded');
