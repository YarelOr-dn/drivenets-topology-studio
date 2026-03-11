/**
 * topology-errors.js - Error Boundary System for Topology App
 * 
 * Provides crash protection, error reporting, and graceful degradation.
 * Load this FIRST before other topology modules.
 * 
 * @version 1.0.0
 * @date 2026-02-03
 */

class ErrorBoundary {
    static errors = [];
    static maxErrors = 100;
    static listeners = [];
    static recoveryAttempts = 0;
    static maxRecoveryAttempts = 3;
    
    /**
     * Wrap a synchronous function with error handling
     * @param {Function} fn - Function to wrap
     * @param {Object} context - 'this' context for the function
     * @param {*} fallback - Value to return on error
     * @param {string} name - Optional name for error reporting
     * @returns {Function} Wrapped function
     */
    static wrap(fn, context = null, fallback = undefined, name = null) {
        const fnName = name || fn.name || 'anonymous';
        return function(...args) {
            try {
                return fn.apply(context || this, args);
            } catch (error) {
                ErrorBoundary.handleError(error, fnName, args);
                return fallback;
            }
        };
    }
    
    /**
     * Wrap an async function with error handling
     * @param {Function} fn - Async function to wrap
     * @param {Object} context - 'this' context for the function
     * @param {*} fallback - Value to return on error
     * @param {string} name - Optional name for error reporting
     * @returns {Function} Wrapped async function
     */
    static wrapAsync(fn, context = null, fallback = undefined, name = null) {
        const fnName = name || fn.name || 'anonymous';
        return async function(...args) {
            try {
                return await fn.apply(context || this, args);
            } catch (error) {
                ErrorBoundary.handleError(error, fnName, args);
                return fallback;
            }
        };
    }
    
    /**
     * Wrap an event handler with error handling (prevents event propagation issues)
     * @param {Function} handler - Event handler function
     * @param {Object} context - 'this' context
     * @param {string} eventName - Name of the event for reporting
     * @returns {Function} Wrapped event handler
     */
    static wrapEventHandler(handler, context = null, eventName = 'event') {
        return function(event) {
            try {
                return handler.call(context || this, event);
            } catch (error) {
                ErrorBoundary.handleError(error, `${eventName}Handler`, [event]);
                // Prevent event from causing further issues
                if (event && typeof event.stopPropagation === 'function') {
                    event.stopPropagation();
                }
            }
        };
    }
    
    /**
     * Wrap a drawing/render function (critical for canvas operations)
     * @param {Function} drawFn - Drawing function
     * @param {Object} context - 'this' context
     * @param {string} name - Name for error reporting
     * @returns {Function} Wrapped drawing function
     */
    static wrapDraw(drawFn, context = null, name = 'draw') {
        let consecutiveErrors = 0;
        const maxConsecutive = 3;
        
        return function(...args) {
            try {
                const result = drawFn.apply(context || this, args);
                consecutiveErrors = 0; // Reset on success
                return result;
            } catch (error) {
                consecutiveErrors++;
                ErrorBoundary.handleError(error, name, args);
                
                if (consecutiveErrors >= maxConsecutive) {
                    console.error(`[ErrorBoundary] ${name} failed ${maxConsecutive} times consecutively. Skipping renders.`);
                    // Don't throw, just skip rendering
                }
            }
        };
    }
    
    /**
     * Handle an error - log, store, notify
     * @param {Error} error - The error object
     * @param {string} location - Where the error occurred
     * @param {Array} args - Arguments that were passed to the function
     */
    static handleError(error, location, args = []) {
        const errorRecord = {
            timestamp: new Date().toISOString(),
            location: location,
            message: error.message,
            stack: error.stack,
            args: ErrorBoundary.safeStringify(args),
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        // Store error
        ErrorBoundary.errors.push(errorRecord);
        if (ErrorBoundary.errors.length > ErrorBoundary.maxErrors) {
            ErrorBoundary.errors.shift(); // Remove oldest
        }
        
        // Log to console with styling
        console.error(
            `%c[TopologyError] ${location}`,
            'color: #ff6b6b; font-weight: bold;',
            '\n', error
        );
        
        // Notify listeners
        ErrorBoundary.listeners.forEach(listener => {
            try {
                listener(errorRecord);
            } catch (e) {
                console.warn('Error in error listener:', e);
            }
        });
        
        // Save to localStorage for recovery info
        ErrorBoundary.saveErrorState();
    }
    
    /**
     * Report error to external service (placeholder for future implementation)
     * @param {Object} errorRecord - The error record
     */
    static report(errorRecord) {
        // Future: Send to error tracking service
        // For now, just log
        if (window.DEBUG_MODE) {
            console.log('[ErrorBoundary] Would report:', errorRecord);
        }
    }
    
    /**
     * Add a listener for errors
     * @param {Function} listener - Callback function(errorRecord)
     */
    static addListener(listener) {
        if (typeof listener === 'function') {
            ErrorBoundary.listeners.push(listener);
        }
    }
    
    /**
     * Remove a listener
     * @param {Function} listener - The listener to remove
     */
    static removeListener(listener) {
        const index = ErrorBoundary.listeners.indexOf(listener);
        if (index > -1) {
            ErrorBoundary.listeners.splice(index, 1);
        }
    }
    
    /**
     * Get recent errors
     * @param {number} count - Number of errors to return
     * @returns {Array} Recent errors
     */
    static getRecentErrors(count = 10) {
        return ErrorBoundary.errors.slice(-count);
    }
    
    /**
     * Clear all stored errors
     */
    static clearErrors() {
        ErrorBoundary.errors = [];
        localStorage.removeItem('topology_errors');
    }
    
    /**
     * Save error state to localStorage
     */
    static saveErrorState() {
        try {
            const state = {
                errors: ErrorBoundary.errors.slice(-20), // Last 20 errors
                lastError: new Date().toISOString(),
                recoveryAttempts: ErrorBoundary.recoveryAttempts
            };
            localStorage.setItem('topology_errors', JSON.stringify(state));
        } catch (e) {
            // localStorage might be full or unavailable
            console.warn('Could not save error state:', e);
        }
    }
    
    /**
     * Load error state from localStorage
     * @returns {Object|null} Previous error state
     */
    static loadErrorState() {
        try {
            const state = localStorage.getItem('topology_errors');
            return state ? JSON.parse(state) : null;
        } catch (e) {
            return null;
        }
    }
    
    /**
     * Check if app crashed recently (for recovery prompt)
     * @returns {boolean} True if crash detected
     */
    static checkForRecentCrash() {
        const state = ErrorBoundary.loadErrorState();
        if (!state || !state.lastError) return false;
        
        const lastError = new Date(state.lastError);
        const now = new Date();
        const hourAgo = new Date(now - 60 * 60 * 1000);
        
        // If there were errors in the last hour, might have crashed
        return lastError > hourAgo && state.errors && state.errors.length > 0;
    }
    
    /**
     * Safely stringify arguments for error logging
     * @param {Array} args - Arguments to stringify
     * @returns {string} Safe string representation
     */
    static safeStringify(args) {
        try {
            return JSON.stringify(args, (key, value) => {
                // Handle circular references and DOM elements
                if (value instanceof HTMLElement) {
                    return `[HTMLElement: ${value.tagName}]`;
                }
                if (value instanceof Event) {
                    return `[Event: ${value.type}]`;
                }
                if (typeof value === 'function') {
                    return `[Function: ${value.name || 'anonymous'}]`;
                }
                return value;
            }, 2).slice(0, 1000); // Limit length
        } catch (e) {
            return '[Could not stringify args]';
        }
    }
    
    /**
     * Create a safe module initializer
     * @param {string} moduleName - Name of the module
     * @param {Function} initFn - Initialization function
     * @param {Function} fallbackFn - Fallback if init fails
     * @returns {*} Module instance or fallback
     */
    static safeModuleInit(moduleName, initFn, fallbackFn = null) {
        try {
            console.log(`[ErrorBoundary] Initializing ${moduleName}...`);
            const result = initFn();
            console.log(`[ErrorBoundary] ${moduleName} initialized successfully`);
            return result;
        } catch (error) {
            console.error(`[ErrorBoundary] ${moduleName} failed to initialize:`, error);
            ErrorBoundary.handleError(error, `${moduleName}.init`);
            
            if (fallbackFn) {
                console.log(`[ErrorBoundary] Using fallback for ${moduleName}`);
                try {
                    return fallbackFn();
                } catch (fallbackError) {
                    console.error(`[ErrorBoundary] Fallback for ${moduleName} also failed:`, fallbackError);
                }
            }
            
            return null;
        }
    }
    
    /**
     * Try to recover from a critical error
     * @param {Function} recoveryFn - Recovery function to attempt
     * @returns {boolean} True if recovery succeeded
     */
    static attemptRecovery(recoveryFn) {
        if (ErrorBoundary.recoveryAttempts >= ErrorBoundary.maxRecoveryAttempts) {
            console.error('[ErrorBoundary] Max recovery attempts reached. Please refresh the page.');
            return false;
        }
        
        ErrorBoundary.recoveryAttempts++;
        
        try {
            recoveryFn();
            console.log('[ErrorBoundary] Recovery attempt succeeded');
            return true;
        } catch (error) {
            console.error('[ErrorBoundary] Recovery attempt failed:', error);
            return false;
        }
    }
    
    /**
     * Show error notification to user
     * @param {string} message - User-friendly message
     * @param {string} type - 'error', 'warning', 'info'
     */
    static showUserNotification(message, type = 'error') {
        // Create notification element if it doesn't exist
        let notification = document.getElementById('topology-error-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'topology-error-notification';
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                color: white;
                font-family: 'Poppins', -apple-system, sans-serif;
                font-size: 14px;
                z-index: 10000;
                max-width: 400px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                transition: opacity 0.3s, transform 0.3s;
                cursor: pointer;
            `;
            document.body.appendChild(notification);
            
            notification.addEventListener('click', () => {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => notification.style.display = 'none', 300);
            });
        }
        
        const colors = {
            error: '#e74c3c',
            warning: '#FF7A33',
            info: '#3498db'
        };
        
        notification.style.backgroundColor = colors[type] || colors.error;
        notification.textContent = message;
        notification.style.display = 'block';
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
        }, 5000);
    }
}

/**
 * Global error handler for uncaught errors
 */
window.addEventListener('error', (event) => {
    ErrorBoundary.handleError(
        event.error || new Error(event.message),
        `global:${event.filename}:${event.lineno}`
    );
});

/**
 * Global handler for unhandled promise rejections
 */
window.addEventListener('unhandledrejection', (event) => {
    ErrorBoundary.handleError(
        event.reason || new Error('Unhandled promise rejection'),
        'unhandledPromise'
    );
});

// Export for use
window.ErrorBoundary = ErrorBoundary;

/**
 * ModuleStats - Track module loading and performance
 */
class ModuleStats {
    static modules = {};
    static loadStart = performance.now();
    
    /**
     * Register a module's load time
     * @param {string} name - Module name
     * @param {number} loadTime - Time in ms to load
     * @param {number} lineCount - Approximate line count
     */
    static register(name, loadTime, lineCount = 0) {
        ModuleStats.modules[name] = {
            loadTime: loadTime,
            lineCount: lineCount,
            loadedAt: performance.now() - ModuleStats.loadStart,
            methods: 0,
            callCount: 0,
            errorCount: 0,
            status: 'loaded'
        };
    }
    
    /**
     * Mark a module as failed
     * @param {string} name - Module name
     * @param {string} reason - Failure reason
     */
    static markFailed(name, reason) {
        ModuleStats.modules[name] = {
            status: 'failed',
            reason: reason,
            loadedAt: performance.now() - ModuleStats.loadStart
        };
    }
    
    /**
     * Track method call
     * @param {string} moduleName - Module name
     */
    static trackCall(moduleName) {
        if (ModuleStats.modules[moduleName]) {
            ModuleStats.modules[moduleName].callCount++;
        }
    }
    
    /**
     * Track error in module
     * @param {string} moduleName - Module name
     */
    static trackError(moduleName) {
        if (ModuleStats.modules[moduleName]) {
            ModuleStats.modules[moduleName].errorCount++;
        }
    }
    
    /**
     * Get summary of all modules
     * @returns {Object} Module summary
     */
    static getSummary() {
        const summary = {
            totalModules: Object.keys(ModuleStats.modules).length,
            loadedModules: 0,
            failedModules: 0,
            totalLoadTime: 0,
            totalLines: 0,
            totalCalls: 0,
            totalErrors: 0,
            modules: {}
        };
        
        for (const [name, stats] of Object.entries(ModuleStats.modules)) {
            if (stats.status === 'loaded') {
                summary.loadedModules++;
                summary.totalLoadTime += stats.loadTime || 0;
                summary.totalLines += stats.lineCount || 0;
                summary.totalCalls += stats.callCount || 0;
                summary.totalErrors += stats.errorCount || 0;
            } else {
                summary.failedModules++;
            }
            summary.modules[name] = stats;
        }
        
        return summary;
    }
    
    /**
     * Print formatted stats to console
     */
    static print() {
        const summary = ModuleStats.getSummary();
        
        console.log('%c📊 Topology Module Stats', 'color: #3498db; font-weight: bold; font-size: 14px;');
        console.log(`   Loaded: ${summary.loadedModules}/${summary.totalModules} modules`);
        console.log(`   Total load time: ${summary.totalLoadTime.toFixed(1)}ms`);
        console.log(`   Total lines: ${summary.totalLines.toLocaleString()}`);
        console.log(`   API calls: ${summary.totalCalls.toLocaleString()}`);
        console.log(`   Errors: ${summary.totalErrors}`);
        
        console.log('\n%cModule Details:', 'font-weight: bold;');
        console.table(Object.entries(summary.modules).map(([name, stats]) => ({
            Module: name,
            Status: stats.status,
            'Load (ms)': stats.loadTime?.toFixed(1) || '-',
            Lines: stats.lineCount || '-',
            Calls: stats.callCount || 0,
            Errors: stats.errorCount || 0
        })));
    }
    
    /**
     * Get health status
     * @returns {string} 'healthy', 'degraded', or 'critical'
     */
    static getHealth() {
        const summary = ModuleStats.getSummary();
        
        if (summary.failedModules === 0 && summary.totalErrors === 0) {
            return 'healthy';
        } else if (summary.failedModules > 0 || summary.totalErrors > 10) {
            return 'critical';
        } else {
            return 'degraded';
        }
    }
}

window.ModuleStats = ModuleStats;

console.log('[topology-errors.js] ErrorBoundary and ModuleStats loaded');
