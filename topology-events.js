// ============================================================================
// TOPOLOGY EVENT BUS
// ============================================================================
// Lightweight pub/sub system for module-to-module communication.
// Enables loose coupling between modules without direct references.
//
// Usage:
//   editor.events.on('object:created', (data) => { ... });
//   editor.events.emit('object:created', { type: 'device', obj: device });
//   const unsub = editor.events.on('event', cb); unsub(); // to unsubscribe
//
// Standard Events:
//   - object:created, object:deleted, object:modified
//   - selection:changed, selection:cleared
//   - mode:changed, tool:changed
//   - view:zoomed, view:panned
//   - history:saved, history:restored
// ============================================================================

class TopologyEventBus {
    constructor() {
        this._listeners = {};
        this._onceListeners = {};
    }

    /**
     * Subscribe to an event
     * @param {string} event - Event name
     * @param {function} callback - Handler function
     * @returns {function} Unsubscribe function
     */
    on(event, callback) {
        if (typeof callback !== 'function') {
            console.warn('TopologyEventBus.on: callback must be a function');
            return () => {};
        }
        
        if (!this._listeners[event]) {
            this._listeners[event] = [];
        }
        this._listeners[event].push(callback);
        
        // Return unsubscribe function
        return () => this.off(event, callback);
    }

    /**
     * Subscribe to an event once (auto-removes after first call)
     * @param {string} event - Event name
     * @param {function} callback - Handler function
     */
    once(event, callback) {
        const wrapper = (data) => {
            this.off(event, wrapper);
            callback(data);
        };
        this.on(event, wrapper);
    }

    /**
     * Unsubscribe from an event
     * @param {string} event - Event name
     * @param {function} callback - Handler to remove
     */
    off(event, callback) {
        if (!this._listeners[event]) return;
        
        this._listeners[event] = this._listeners[event].filter(cb => cb !== callback);
        
        // Clean up empty arrays
        if (this._listeners[event].length === 0) {
            delete this._listeners[event];
        }
    }

    /**
     * Emit an event to all subscribers
     * @param {string} event - Event name
     * @param {*} data - Data to pass to handlers
     */
    emit(event, data) {
        const listeners = this._listeners[event];
        if (!listeners || listeners.length === 0) return;
        
        // Copy array in case handlers modify it
        const handlers = [...listeners];
        
        for (const handler of handlers) {
            try {
                handler(data);
            } catch (error) {
                console.error(`TopologyEventBus: Error in handler for "${event}":`, error);
            }
        }
    }

    /**
     * Remove all listeners for an event (or all events)
     * @param {string} [event] - Event name (optional, clears all if not provided)
     */
    clear(event) {
        if (event) {
            delete this._listeners[event];
        } else {
            this._listeners = {};
        }
    }

    /**
     * Get count of listeners for an event
     * @param {string} event - Event name
     * @returns {number} Number of listeners
     */
    listenerCount(event) {
        return this._listeners[event]?.length || 0;
    }

    /**
     * Debug: List all registered events
     * @returns {string[]} Array of event names with listener counts
     */
    debug() {
        const events = Object.keys(this._listeners);
        console.log('TopologyEventBus registered events:');
        events.forEach(event => {
            console.log(`  ${event}: ${this._listeners[event].length} listeners`);
        });
        return events;
    }
}

// ============================================================================
// STANDARD EVENT DEFINITIONS (for documentation)
// ============================================================================
// These are the standard events used across modules. Custom events can be added.
//
// Object Lifecycle:
//   object:created    { type: 'device'|'link'|'text'|'shape', obj: object }
//   object:deleted    { type: string, obj: object }
//   object:modified   { type: string, obj: object, changes: object }
//
// Selection:
//   selection:changed { selected: object|null, previous: object|null }
//   selection:multi   { selected: object[], added: object[], removed: object[] }
//   selection:cleared { previous: object|object[] }
//
// Mode/Tool:
//   mode:changed      { mode: string, previous: string }
//   tool:changed      { tool: string, previous: string }
//
// View:
//   view:zoomed       { zoom: number, previous: number }
//   view:panned       { offset: {x,y}, previous: {x,y} }
//
// History:
//   history:saved     { index: number, count: number }
//   history:restored  { index: number, direction: 'undo'|'redo' }
//
// File:
//   file:loaded       { name: string }
//   file:saved        { name: string }
//   file:autosaved    { timestamp: number }
// ============================================================================

// Export for use
window.TopologyEventBus = TopologyEventBus;

// Factory function for conditional initialization
window.createEventBus = function() {
    return new TopologyEventBus();
};

console.log('TopologyEventBus module loaded');
