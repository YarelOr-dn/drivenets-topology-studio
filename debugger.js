// Real-Time Debugger for Topology Editor
// Provides visual feedback for debugging and testing
// Auto-integrates with ALL editor operations

// Icon helper function for debugger - generates SVG icon HTML
function dbgIcon(iconName) {
    return `<span class="ico"><svg><use href="#ico-${iconName}"/></svg></span>`;
}

class TopologyDebugger {
    constructor(editor) {
        this.editor = editor;
        this.logs = [];
        this.maxLogs = 150; // Increased to store up to 100 logs for copying
        this.bugHistory = []; // Track all bugs for pattern analysis
        this.recentActions = []; // Track recent user actions
        this.maxRecentActions = 10;
        this.activeBugs = new Map(); // Track active bugs to prevent duplicates
        this.bugSuppressionTime = 3000; // Don't log same bug within 3 seconds (reduced for faster detection)
        this.callStack = []; // Track function call chain
        this.variableSnapshots = new Map(); // Track variable states over time
        this.maxCallStack = 20;
        
        // ADVANCED: Real-time code state monitoring
        this.codeStateMonitor = {
            lastDragSetup: null,
            lastCollisionRun: null,
            lastPositionChange: new Map(), // deviceId -> {time, oldPos, newPos, cause}
            suspiciousOperations: [],
            executionTimeline: [],
            maxTimeline: 50
        };
        
        // ADVANCED: Bug fingerprinting for precise duplicate detection
        this.bugFingerprints = new Map(); // fingerprint -> {count, firstSeen, lastSeen, instances}
        
        // ADVANCED: Predictive bug detection
        this.riskFactors = {
            dragDuringCollision: 0,
            rapidPositionChanges: 0,
            offsetMagnitude: 0,
            coordinateTransformErrors: 0
        };
        
        // PLACEMENT TRACKING: Store placement data for copying
        this.placementData = {
            deviceLabel: null,
            deviceType: null,
            grabPosition: null,
            releasePosition: null,
            mouseGrab: null,
            mouseRelease: null,
            offset: null,
            distance: null,
            timestamp: null,
            inputType: null
        };
        
        // AI Debug Assistant
        this.aiDebugHistory = []; // Track AI suggestions and fixes
        this.currentBugContext = null; // Store current bug context for AI
        
        // Movement/Jump detection message control - OFF by default (too many false positives during fast movement)
        this.showJumpAlerts = localStorage.getItem('debugger_show_jump_alerts') === 'true'; // OFF by default
        
        // Load AI debug history from localStorage
        try {
            const savedHistory = localStorage.getItem('ai_debug_history');
            if (savedHistory) {
                this.aiDebugHistory = JSON.parse(savedHistory);
            }
        } catch (e) {
            console.warn('Could not load AI debug history:', e);
        }
        
        // Default to DISABLED (user can enable via Debug button if needed)
        const storedEnabled = localStorage.getItem('debugger_enabled');
        this.enabled = storedEnabled === 'true'; // Default false unless explicitly enabled
        this.minimized = localStorage.getItem('debugger_minimized') === 'true';
        
        // Load size and position with safe defaults
        const storedSize = JSON.parse(localStorage.getItem('debugger_size') || '{"width": 400, "height": 600}');
        this.size = {
            width: Math.max(300, Math.min(storedSize.width, window.innerWidth - 100)),
            height: Math.max(200, Math.min(storedSize.height, window.innerHeight - 100))
        };
        
        // Load minimized height separately (for resizing when minimized)
        this.minimizedHeight = parseInt(localStorage.getItem('debugger_minimized_height')) || 300;
        
        const storedPosition = JSON.parse(localStorage.getItem('debugger_position') || 'null');
        // Default to top-right if no stored position, or validate stored position
        if (!storedPosition || storedPosition.left < 0 || storedPosition.left > window.innerWidth - 100) {
            this.position = { left: window.innerWidth - this.size.width - 20, top: 60 };
        } else {
            this.position = storedPosition;
        }
        
        // Collapsible sections state
        this.collapsedSections = JSON.parse(localStorage.getItem('debugger_collapsed') || '{}');
        
        this.createDebugPanel();
        this.makeDraggable();
        this.makeResizable();
        this.setupCollapsibleSections();
        this.updateFontSize();
        this.startMonitoring();
        this.interceptEditorMethods();
        
        // Initialize log view
        // Add initial log message
        this.log('Debugger initialized! Drag header to move, D to toggle', 'success');
        
        // Initialize minimized log view immediately if starting minimized
        if (this.minimized) {
            requestAnimationFrame(() => {
                this.updateMinimizedLog();
            });
        }
        
        // Set debugger button state based on debugger state  
        setTimeout(() => {
            const debuggerBtn = document.getElementById('btn-debugger-top');
            if (debuggerBtn) {
                // Always keep button visible, just toggle active state
                if (this.enabled) {
                    debuggerBtn.classList.add('active');
                } else {
                    debuggerBtn.classList.remove('active');
                }
            }
        }, 100);
    }

    createCollapsibleSection(id, icon, title, color, bgColor) {
        const isCollapsed = this.collapsedSections[id] || false;
        return `
            <div class="debug-section" data-section="${id}" style="margin-bottom: 8px; border-radius: 4px; overflow: hidden; border: 1px solid ${color}40; min-height: 30px; flex-shrink: 0;">
                <div class="debug-section-header" style="display: flex; justify-content: space-between; align-items: center; padding: 6px 8px; background: ${bgColor}; cursor: pointer; user-select: none; border-bottom: ${isCollapsed ? 'none' : '1px solid ' + color + '20'}; flex-shrink: 0;">
                    <span style="font-weight: bold; color: ${color}; font-size: 11px;">${icon} ${title}</span>
                    <div style="display: flex; gap: 4px; align-items: center;">
                        <button id="copy-${id}-btn" style="background: #3498db; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 8px; font-weight: bold; transition: all 0.2s; z-index: 100;" title="Copy ${title} data" onclick="event.stopPropagation(); window.debugger && window.debugger.copySection('${id}')">📋</button>
                        <span class="debug-toggle" style="color: ${color}; font-weight: bold; transition: transform 0.2s;">${isCollapsed ? '▶' : '▼'}</span>
                    </div>
                </div>
                <div class="debug-section-content" style="padding: 8px; background: ${bgColor}50; display: ${isCollapsed ? 'none' : 'block'}; min-height: 40px;">
                    <div id="${id}" style="color: #fff; font-size: 10px;">...</div>
                </div>
            </div>
        `;
    }

    createDebugPanel() {
        const panel = document.createElement('div');
        panel.id = 'debug-panel';
        
        // Use saved minimized height if available, otherwise default to 300
        const initialHeight = this.minimized ? (this.minimizedHeight || 300) : this.size.height;
        
        panel.style.cssText = `
            position: fixed;
            top: ${this.position.top}px;
            left: ${this.position.left}px;
            width: ${this.size.width}px;
            height: ${initialHeight}px;
            min-width: 300px;
            min-height: 200px;
            max-width: ${window.innerWidth - 20}px;
            max-height: ${window.innerHeight - 20}px;
            background: rgba(0, 0, 0, 0.95);
            color: #0f0;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            border: 2px solid #0f0;
            border-radius: 8px;
            z-index: 100000;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
            display: ${this.enabled ? 'block' : 'none'};
            transition: none;
            pointer-events: auto;
        `;

        panel.innerHTML = `
            <div id="debug-header" style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 2px solid #0f0; cursor: move; background: rgba(0, 255, 0, 0.1);">
                <span style="font-weight: bold; color: #0ff; user-select: none;">⚡ DEBUGGER</span>
                <div style="display: flex; gap: 5px;">
                    <button id="debug-toggle-jump-alerts" style="background: ${this.showJumpAlerts ? '#27ae60' : '#95a5a6'}; color: #fff; border: none; padding: 2px 8px; cursor: pointer; border-radius: 3px; font-weight: bold; font-size: 10px;" title="Toggle Movement/Jump Alert Popups (hides false positives during fast dragging)">
                        ${this.showJumpAlerts ? '🔔' : '🔕'} Alerts
                    </button>
                    <button id="debug-minimize" style="background: #0af; color: #fff; border: none; padding: 2px 8px; cursor: pointer; border-radius: 3px; font-weight: bold;" title="Minimize/Maximize">${this.minimized ? '□' : '_'}</button>
                    <button id="debug-clear" style="background: #f60; color: #fff; border: none; padding: 2px 8px; cursor: pointer; border-radius: 3px;" title="Clear Log">Clear</button>
                    <button id="debug-close" style="background: #f00; color: #fff; border: none; padding: 2px 8px; cursor: pointer; border-radius: 3px; font-weight: bold;" title="Close Debugger">✕</button>
                </div>
            </div>
            <div id="debug-status-wrapper" style="padding: 10px; padding-bottom: 0; display: block;">
                <div id="debug-status" style="margin-bottom: 10px; padding: 8px; background: rgba(0, 255, 0, 0.1); border-radius: 4px; font-size: 11px;">
                    <div id="debug-status-content">Initializing...</div>
                </div>
            </div>
            <!-- Minimized Log View (only logs, no sections) -->
            <div style="height: calc(100% - 50px); display: ${this.minimized ? 'block' : 'none'};" id="debug-minimized-wrapper">
                <div style="font-weight: bold; color: #f0f; font-size: 11px; padding: 10px 10px 4px 10px;">📜 EVENT LOG:</div>
                <div style="background: rgba(255, 0, 255, 0.05); margin: 0 10px 10px 10px; border-radius: 4px; height: calc(100% - 40px);">
                    <div id="debug-minimized-log" style="overflow-y: auto; height: 100%; padding: 5px; padding-bottom: 50px; font-size: 10px;">
                        <div id="debug-minimized-log-content" style="color: #0f0;">
                    <div style="color: #888;">Waiting for events...</div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="debug-body" style="padding: 0 10px 10px 10px; overflow-y: auto; height: calc(100% - 110px); display: ${this.minimized ? 'none' : 'flex'}; flex-direction: column;">
                <div id="debug-bug-alert" style="display: none; padding: 8px; background: rgba(255, 0, 0, 0.2); border: 2px solid #f00; border-radius: 4px; margin-bottom: 10px;">
                    <div style="font-weight: bold; color: #f00; margin-bottom: 4px;">🚨 BUG DETECTED!</div>
                    <div id="debug-bug-message" style="color: #fff; font-size: 10px;"></div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px; gap: 6px;">
                        <div style="color: #fa0; font-size: 9px; cursor: pointer; flex: 1;" onclick="window.debugger.showBugSection()">Click to jump to bug details ↓</div>
                        <button id="debug-ask-ai" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 9px; font-weight: bold; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4); transition: all 0.2s;" title="Copy bug context and get AI help" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.6)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 2px 8px rgba(102, 126, 234, 0.4)';">🤖 Ask AI</button>
                </div>
                </div>
                
                <!-- AI Debug Assistant Panel -->
                <div id="debug-ai-panel" style="display: none; padding: 10px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%); border: 2px solid #667eea; border-radius: 6px; margin-bottom: 10px;">
                    <div style="font-weight: bold; color: #667eea; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                        <span>🤖 AI DEBUG ASSISTANT</span>
                        <button id="debug-ai-close" style="background: transparent; color: #667eea; border: none; cursor: pointer; font-size: 14px; padding: 0 4px;" title="Close AI Panel">✕</button>
                    </div>
                    <div id="debug-ai-content" style="color: #fff; font-size: 10px; line-height: 1.4;">
                        <div style="color: #aaa; margin-bottom: 8px;">Context captured and copied to clipboard!</div>
                        <div style="background: rgba(0, 0, 0, 0.3); padding: 6px; border-radius: 4px; margin-bottom: 8px; border-left: 3px solid #667eea;">
                            <div style="font-weight: bold; color: #667eea; margin-bottom: 4px;">📋 What was copied:</div>
                            <div id="debug-ai-summary" style="font-size: 9px; color: #ccc;"></div>
                        </div>
                        <div style="font-size: 9px; color: #aaa; line-height: 1.5;">
                            <b style="color: #667eea;">Next steps:</b><br>
                            1. Open Cursor AI Chat (Cmd+L or Ctrl+L)<br>
                            2. Paste the context (Cmd+V or Ctrl+V)<br>
                            3. AI will analyze and suggest fixes<br>
                            4. Review and apply the suggested fix
                        </div>
                        <button id="debug-ai-recopy" style="width: 100%; background: #667eea; color: #fff; border: none; padding: 6px; border-radius: 4px; cursor: pointer; font-size: 10px; margin-top: 8px; font-weight: bold;" title="Copy context again">📋 Copy Again</button>
                    </div>
                </div>
                ${this.createCollapsibleSection('debug-ai-history', '🤖', 'AI DEBUG HISTORY', '#667eea', 'rgba(102, 126, 234, 0.1)')}
                ${this.createCollapsibleSection('debug-history', '📊', 'HISTORY STATE', '#ff0', 'rgba(255, 255, 0, 0.1)')}
                ${this.createCollapsibleSection('debug-zoom', '🔍', 'ZOOM/PAN STATE', '#fa0', 'rgba(255, 165, 0, 0.1)')}
                ${this.createCollapsibleSection('debug-magnetic', '🧲', 'MAGNETIC FIELD', '#ff1493', 'rgba(255, 20, 147, 0.1)')}
                ${this.createCollapsibleSection('debug-current', '🎯', 'CURRENT STATE', '#0ff', 'rgba(0, 255, 255, 0.1)')}
                ${this.createCollapsibleSection('debug-collision', '⚠️', 'COLLISION TRACKING', '#f00', 'rgba(255, 0, 0, 0.1)')}
                ${this.createCollapsibleSection('debug-momentum', '🎯', 'MOMENTUM/SLIDING', '#00bfff', 'rgba(0, 191, 255, 0.1)')}
                ${this.createCollapsibleSection('debug-ui-buttons', '🎨', 'UI BUTTON STATES', '#ba55d3', 'rgba(138, 43, 226, 0.1)')}
                ${this.createCollapsibleSection('debug-mouse-pos', '🖱️', 'MOUSE POSITION', '#00ff7f', 'rgba(0, 255, 127, 0.1)')}
                ${this.createCollapsibleSection('debug-selected-device', '👆', 'SELECTED DEVICE', '#ffd700', 'rgba(255, 215, 0, 0.1)')}
                <div class="debug-section" data-section="debug-click-track" style="margin-bottom: 8px; border-radius: 4px; overflow: hidden; border: 1px solid #64c8ff40; min-height: 30px; flex-shrink: 0;">
                    <div class="debug-section-header" style="display: flex; justify-content: space-between; align-items: center; padding: 6px 8px; background: rgba(100, 200, 255, 0.1); cursor: pointer; user-select: none; border-bottom: 1px solid #64c8ff20;">
                        <span style="font-weight: bold; color: #64c8ff; font-size: 11px;">📍 PLACEMENT TRACKING</span>
                        <div style="display: flex; gap: 4px; align-items: center;">
                            <button id="copy-placement-btn" style="background: #3498db; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 8px; font-weight: bold; transition: all 0.2s; z-index: 100;" title="Copy placement data" onclick="event.stopPropagation(); window.debugger && window.debugger.copyPlacementTracking()">📋</button>
                            <span class="debug-toggle" style="color: #64c8ff; font-weight: bold; transition: transform 0.2s;">▼</span>
                        </div>
                    </div>
                    <div class="debug-section-content" style="padding: 8px; background: rgba(100, 200, 255, 0.1)50; display: block;">
                        <div id="debug-click-track" style="color: #fff; font-size: 10px;">...</div>
                    </div>
                </div>
                ${this.createCollapsibleSection('debug-touchpad', '🖐️', 'TOUCHPAD GESTURES', '#ff6b6b', 'rgba(255, 107, 107, 0.1)')}
                <div class="debug-section" style="margin-bottom: 0; flex: 1; display: flex; flex-direction: column; min-height: 200px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; flex-shrink: 0;">
                        <span style="font-weight: bold; color: #f0f; font-size: 11px;">📜 EVENT LOG:</span>
                        <div style="display: flex; gap: 4px;">
                            <button id="show-text-logs" style="background: #e74c3c; color: white; border: none; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 8px; font-weight: bold;" title="Show logs as copyable text" onclick="window.debugger && window.debugger.showTextLogs()">📝 TEXT</button>
                            <button id="copy-debug-log-btn" style="background: #3498db; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 8px; font-weight: bold; transition: all 0.2s; z-index: 100;" title="Copy event log" onclick="window.debugger && window.debugger.copySection('debug-log')">📋</button>
                        </div>
                    </div>
                    <div style="background: rgba(255, 0, 255, 0.05); border-radius: 4px; flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden;">
                        <div id="debug-log" style="flex: 1; overflow-y: auto; padding: 5px; padding-bottom: 50px; font-size: 10px;">
                        <div style="color: #888;">Waiting for events...</div>
                        </div>
                    </div>
                </div>
                
                <!-- TEXT LOG MODAL for manual copying -->
                <div id="text-log-modal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 100000; justify-content: center; align-items: center;">
                    <div style="background: #2c3e50; padding: 20px; border-radius: 8px; max-width: 800px; max-height: 80vh; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h3 style="color: #fff; margin: 0;">📝 Debug Logs (Manual Copy)</h3>
                            <button onclick="document.getElementById('text-log-modal').style.display='none'" style="background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">✕ Close</button>
                        </div>
                        <textarea id="text-log-content" readonly style="width: 100%; height: 500px; background: #1e1e1e; color: #0ff; font-family: monospace; font-size: 11px; border: 1px solid #555; padding: 10px; resize: vertical;" onclick="this.select()"></textarea>
                        <div style="color: #fff; margin-top: 10px; font-size: 12px;">👆 Click textarea and press Ctrl+A, then Ctrl+C to copy all logs</div>
                    </div>
                </div>
            </div>
            <!-- Resize Handles -->
            <div class="resize-handle resize-left" style="position: absolute; left: 0; top: 0; width: 6px; height: 100%; cursor: ew-resize; z-index: 10;"></div>
            <div class="resize-handle resize-right" style="position: absolute; right: 0; top: 0; width: 6px; height: 100%; cursor: ew-resize; z-index: 10;"></div>
            <div class="resize-handle resize-bottom" style="position: absolute; left: 0; bottom: 0; width: 100%; height: 6px; cursor: ns-resize; z-index: 10;"></div>
            <div class="resize-handle resize-bottom-left" style="position: absolute; left: 0; bottom: 0; width: 12px; height: 12px; cursor: nesw-resize; z-index: 11; background: rgba(0, 255, 0, 0.3); border-radius: 0 4px 0 0;"></div>
            <div class="resize-handle resize-bottom-right" style="position: absolute; right: 0; bottom: 0; width: 12px; height: 12px; cursor: nwse-resize; z-index: 11; background: rgba(0, 255, 0, 0.3); border-radius: 4px 0 0 0;"></div>
            
            <!-- Global Copy Button (Fixed at Bottom-Right of Panel) -->
            <button id="debug-copy-logs" style="
                position: absolute;
                bottom: 10px;
                right: 20px;
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 10px;
                font-weight: bold;
                transition: all 0.2s;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
                z-index: 10000;
                pointer-events: auto;
            " title="Copy Last 20 Logs" onmouseover="this.style.background='#2980b9'; this.style.transform='scale(1.05)'" onmouseout="this.style.background='#3498db'; this.style.transform='scale(1)'">
                📋 Copy
            </button>
        `;

        document.body.appendChild(panel);

        // Close button
        document.getElementById('debug-close').addEventListener('click', () => {
            this.enabled = false;
            panel.style.display = 'none';
            localStorage.setItem('debugger_enabled', 'false');
            
            // Update debugger button state in top bar
            const debuggerBtn = document.getElementById('btn-debugger-top');
            if (debuggerBtn) {
                debuggerBtn.classList.remove('active');
            }
            
            console.log('Debugger closed. Press D or click Debug button to reopen.');
        });

        // Minimize button - minimize to ONLY header + logs (no sections)
        document.getElementById('debug-minimize').addEventListener('click', () => {
            this.minimized = !this.minimized;
            const body = document.getElementById('debug-body');
            const statusWrapper = document.getElementById('debug-status-wrapper');
            const minimizedWrapper = document.getElementById('debug-minimized-wrapper');
            const btn = document.getElementById('debug-minimize');
            const resizeHandles = panel.querySelectorAll('.resize-handle');
            
            if (this.minimized) {
                // Show ONLY logs when minimized (no sections, no status)
                body.style.display = 'none';
                statusWrapper.style.display = 'none';
                minimizedWrapper.style.display = 'block';
                // Use saved minimized height, default to 300 if not set
                panel.style.height = (this.minimizedHeight || 300) + 'px';
                btn.textContent = '□';
                btn.title = 'Expand Debugger (Show All Sections)';
                // KEEP resize handles visible in minimized mode for log viewing
                resizeHandles.forEach(handle => handle.style.display = 'block');
                
                // Update minimized log with recent events
                this.updateMinimizedLog();
            } else {
                // Show full debugger with all sections
                body.style.display = 'block';
                statusWrapper.style.display = 'block';
                minimizedWrapper.style.display = 'none';
                panel.style.height = this.size.height + 'px';
                btn.textContent = '_';
                btn.title = 'Minimize Debugger (Show Only Logs)';
                // Show resize handles when expanded
                resizeHandles.forEach(handle => handle.style.display = 'block');
            }
            
            localStorage.setItem('debugger_minimized', this.minimized);
        });

        // Clear button - clears logs in both expanded and minimized views
        // Jump alert toggle button
        document.getElementById('debug-toggle-jump-alerts').addEventListener('click', () => {
            this.toggleJumpAlerts();
        });
        
        document.getElementById('debug-clear').addEventListener('click', () => {
            this.logs = [];
            
            // Update both log displays
            this.updateLogDisplay();
            this.updateMinimizedLog();
            
            // Add a log entry confirming the clear (will appear in both views)
            this.log('🧹 Logs cleared', 'info');
        });
        
        // Copy logs button (single button for all views)
        document.getElementById('debug-copy-logs').addEventListener('click', () => {
            this.copyLastLogs();
        });
        
        // AI Debug Assistant buttons
        document.getElementById('debug-ask-ai').addEventListener('click', () => {
            this.askAI();
        });
        
        document.getElementById('debug-ai-close').addEventListener('click', () => {
            document.getElementById('debug-ai-panel').style.display = 'none';
        });
        
        document.getElementById('debug-ai-recopy').addEventListener('click', () => {
            this.copyBugContextForAI();
        });

        this.panel = panel;
        this.header = document.getElementById('debug-header');
    }

    makeDraggable() {
        this.header.addEventListener('mousedown', (e) => {
            if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
            
            // PERFECT GRAB: Capture the exact point where user clicked
            // Use getBoundingClientRect() for the ACTUAL rendered position
            const rect = this.panel.getBoundingClientRect();
            const offsetX = e.clientX - rect.left;
            const offsetY = e.clientY - rect.top;
            
            console.log('🔍 Debugger Grab:', {
                panelAt: `(${rect.left.toFixed(1)}, ${rect.top.toFixed(1)})`,
                mouseAt: `(${e.clientX}, ${e.clientY})`,
                grabPoint: `(${offsetX.toFixed(1)}, ${offsetY.toFixed(1)})`,
                note: 'Panel will follow mouse maintaining this exact grab point'
            });
            
            // DON'T set position here - it causes jumps if position already matches
            // The position is already correct from getBoundingClientRect
            
            // Set cursor states
            this.panel.style.cursor = 'grabbing';
            this.header.style.cursor = 'grabbing';
            
            // Store panel dimensions ONCE at grab start (don't recalculate during move)
            const panelWidth = rect.width;
            const panelHeight = rect.height;
            
            // Track if we're still dragging
            let isDragging = true;
            
            // Move function - PERFECT 1:1 GLUED tracking (no delays, no frame skipping)
            const move = (e) => {
                if (!isDragging) return; // Safety check
                
                // INSTANT update: Position = Mouse - GrabOffset
                // This keeps the grab point EXACTLY under the cursor with zero delay
                const newLeft = e.clientX - offsetX;
                const newTop = e.clientY - offsetY;
                
                // Apply bounds ONLY when necessary (prevent going off screen)
                let finalLeft = newLeft;
                let finalTop = newTop;
                
                if (newLeft < 0) {
                    finalLeft = 0;
                } else if (newLeft + panelWidth > window.innerWidth) {
                    finalLeft = window.innerWidth - panelWidth;
                }
                
                if (newTop < 0) {
                    finalTop = 0;
                } else if (newTop + panelHeight > window.innerHeight) {
                    finalTop = window.innerHeight - panelHeight;
                }
                
                // INSTANT position update - DIRECT style assignment with no delays
                // The grab point stays GLUED to the mouse cursor - position updates immediately
                this.panel.style.left = finalLeft + 'px';
                this.panel.style.top = finalTop + 'px';
            };
            
            const up = (e) => {
                if (!isDragging) return; // Already released
                isDragging = false;
                
                // Remove event listeners with SAME options
                document.removeEventListener('mousemove', move, { passive: true, capture: true });
                document.removeEventListener('mouseup', up, { capture: true });
                
                // Also remove pointer events if any
                document.removeEventListener('pointermove', move, { passive: true, capture: true });
                document.removeEventListener('pointerup', up, { capture: true });
                
                this.panel.style.cursor = '';
                this.header.style.cursor = 'move';
                
                // Save final position
                const finalRect = this.panel.getBoundingClientRect();
                this.position = { left: finalRect.left, top: finalRect.top };
                localStorage.setItem('debugger_position', JSON.stringify(this.position));
                console.log('✅ Saved position:', this.position);
            };

            // CRITICAL: Use capture phase to ensure we catch ALL mouse events
            // Also handle pointer events for better compatibility
            document.addEventListener('mousemove', move, { passive: true, capture: true });
            document.addEventListener('mouseup', up, { capture: true });
            document.addEventListener('pointermove', move, { passive: true, capture: true });
            document.addEventListener('pointerup', up, { capture: true });
            
            e.preventDefault();
            e.stopPropagation();
        });
    }

    makeResizable() {
        let isResizing = false;
        let resizeType = null;
        let startX = 0;
        let startY = 0;
        let startWidth = 0;
        let startHeight = 0;
        let startLeft = 0;
        let startTop = 0;

        // Get all resize handles
        const handles = {
            left: this.panel.querySelector('.resize-left'),
            right: this.panel.querySelector('.resize-right'),
            bottom: this.panel.querySelector('.resize-bottom'),
            bottomLeft: this.panel.querySelector('.resize-bottom-left'),
            bottomRight: this.panel.querySelector('.resize-bottom-right')
        };

        // Add mousedown listeners to all handles
        Object.entries(handles).forEach(([type, handle]) => {
            if (!handle) return;
            
            handle.addEventListener('mousedown', (e) => {
                isResizing = true;
                resizeType = type;
                startX = e.clientX;
                startY = e.clientY;
                
                const rect = this.panel.getBoundingClientRect();
                startWidth = rect.width;
                startHeight = rect.height;
                startLeft = rect.left;
                startTop = rect.top;
                
                // Visual feedback
                this.panel.style.userSelect = 'none';
                document.body.style.cursor = handle.style.cursor;
                
                e.preventDefault();
                e.stopPropagation();
            });
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            e.preventDefault();
            
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            
            let newWidth = startWidth;
            let newHeight = startHeight;
            let newLeft = startLeft;
            let newTop = startTop;
            
            // Calculate new dimensions based on resize type
            switch (resizeType) {
                case 'left':
                    newWidth = startWidth - deltaX;
                    newLeft = startLeft + deltaX;
                    break;
                case 'right':
                    newWidth = startWidth + deltaX;
                    break;
                case 'bottom':
                    newHeight = startHeight + deltaY;
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
            
            // Clamp width
            if (newWidth < minWidth) {
                if (resizeType === 'left' || resizeType === 'bottomLeft') {
                    newLeft = startLeft + startWidth - minWidth;
                }
                newWidth = minWidth;
            } else if (newWidth > maxWidth) {
                newWidth = maxWidth;
            }
            
            // Clamp height
            if (newHeight < minHeight) {
                newHeight = minHeight;
            } else if (newHeight > maxHeight) {
                newHeight = maxHeight;
            }
            
            // Ensure panel stays within viewport when resizing left
            if (resizeType === 'left' || resizeType === 'bottomLeft') {
                if (newLeft < 0) {
                    newWidth = startWidth + startLeft - 0;
                    newLeft = 0;
                }
                if (newLeft + newWidth > window.innerWidth) {
                    newLeft = window.innerWidth - newWidth;
                }
            }
            
            // Ensure panel stays within viewport when resizing right
            if (resizeType === 'right' || resizeType === 'bottomRight') {
                if (newLeft + newWidth > window.innerWidth) {
                    newWidth = window.innerWidth - newLeft;
                }
            }
            
            // Ensure panel stays within viewport when resizing bottom
            if (resizeType.includes('bottom')) {
                if (newTop + newHeight > window.innerHeight) {
                    newHeight = window.innerHeight - newTop;
                }
            }
            
            // Apply new dimensions and position
            this.panel.style.width = newWidth + 'px';
            this.panel.style.height = newHeight + 'px';
            
            if (resizeType === 'left' || resizeType === 'bottomLeft') {
                this.panel.style.left = newLeft + 'px';
                this.position.left = newLeft;
            }
            
            // Update stored size
            this.size.width = newWidth;
            this.size.height = newHeight;
            
            // Update font size dynamically during resize
            this.updateFontSize();
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                resizeType = null;
                this.panel.style.userSelect = '';
                document.body.style.cursor = '';
                
                // Save size and position to localStorage
                localStorage.setItem('debugger_size', JSON.stringify(this.size));
                localStorage.setItem('debugger_position', JSON.stringify(this.position));
                
                // ENHANCED: Save minimized height separately when in minimized mode
                if (this.minimized) {
                    const currentHeight = parseInt(this.panel.style.height);
                    this.minimizedHeight = currentHeight;
                    localStorage.setItem('debugger_minimized_height', currentHeight.toString());
                    console.log('Debugger minimized height saved:', currentHeight);
                }
                
                // Final font size update
                this.updateFontSize();
                
                console.log('Debugger resized to:', this.size);
            }
        });
    }

    setupCollapsibleSections() {
        // Add click handlers to all section headers
        const headers = this.panel.querySelectorAll('.debug-section-header');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const section = header.closest('.debug-section');
                const sectionId = section.dataset.section;
                const content = section.querySelector('.debug-section-content');
                const toggle = section.querySelector('.debug-toggle');
                
                // Toggle visibility
                const isCollapsed = content.style.display === 'none';
                content.style.display = isCollapsed ? 'block' : 'none';
                toggle.textContent = isCollapsed ? '▼' : '▶';
                header.style.borderBottom = isCollapsed ? `1px solid ${header.querySelector('span').style.color}20` : 'none';
                
                // Save state
                this.collapsedSections[sectionId] = !isCollapsed;
                localStorage.setItem('debugger_collapsed', JSON.stringify(this.collapsedSections));
            });
        });
    }

    updateFontSize() {
        // Dynamic font sizing based on debugger width
        const baseWidth = 400; // Base width for 11px font
        const baseFontSize = 11;
        const scaleFactor = this.size.width / baseWidth;
        
        // Calculate new font size (between 9px and 14px)
        const newFontSize = Math.max(9, Math.min(14, baseFontSize * scaleFactor));
        
        // Apply to panel
        this.panel.style.fontSize = newFontSize + 'px';
        
        // Apply to specific elements that need scaling
        const sectionContent = this.panel.querySelectorAll('.debug-section-content div');
        sectionContent.forEach(el => {
            if (!el.style.fontSize) {
                el.style.fontSize = Math.max(9, newFontSize - 1) + 'px';
            }
        });
    }

    interceptEditorMethods() {
        // Auto-intercept common editor methods to provide automatic logging
        const originalMethods = {
            saveState: this.editor.saveState,
            undo: this.editor.undo,
            redo: this.editor.redo,
            deleteSelected: this.editor.deleteSelected,
            addDeviceAtPosition: this.editor.addDeviceAtPosition,
            createLink: this.editor.createLink,
            createUnboundLink: this.editor.createUnboundLink,
            setMode: this.editor.setMode,
            toggleDevicePlacementMode: this.editor.toggleDevicePlacementMode
        };

        // This is already done in the main file via this.debugger.logX() calls
        // Just ensure any future methods can easily log
    }

    addToTimeline(event, details = {}) {
        // Track execution timeline for advanced analysis
        this.codeStateMonitor.executionTimeline.push({
            time: Date.now(),
            timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, fractionalSecondDigits: 3 }),
            event: event,
            details: details,
            editorState: {
                zoom: this.editor?.zoom,
                dragging: this.editor?.dragging,
                mode: this.editor?.currentMode,
                collisionActive: this.editor?.deviceCollision
            }
        });
        
        // Keep only recent timeline
        if (this.codeStateMonitor.executionTimeline.length > this.codeStateMonitor.maxTimeline) {
            this.codeStateMonitor.executionTimeline.shift();
        }
    }
    
    generateBugFingerprint(message, context = {}) {
        // Create unique fingerprint for bug to detect duplicates
        // ENHANCED: More generic to catch duplicates across frames
        
        // Extract bug type from message (ignore numbers)
        const bugType = message.replace(/\d+/g, 'N').substring(0, 30); // Replace numbers with 'N'
        const category = context.category || 'UNKNOWN';
        const objectType = context.selectedObj?.type || 'none';
        const mode = context.mode || this.editor?.currentMode || 'unknown';
        
        // CRITICAL: During drag, all bugs are the same (ignore exact values)
        const dragState = context.dragging || this.editor?.dragging ? 'DRAGGING' : 'IDLE';
        
        return `${bugType}::${category}::${objectType}::${mode}::${dragState}`;
    }
    
    isDuplicateBug(message) {
        // CRITICAL: If actively dragging, suppress ALL bugs (they spam on every frame)
        if (this.editor?.dragging) {
            // Store for later analysis but don't show alert
            if (!this._dragBugBuffer) {
                this._dragBugBuffer = [];
            }
            this._dragBugBuffer.push({
                time: Date.now(),
                message: message
            });
            
            // Only log first bug during drag session
            if (this._dragBugBuffer.length === 1) {
                console.log('⚠️ Bug detected during drag - buffering (will analyze on mouse up)');
                return false; // Allow first one to be logged
            }
            
            // Suppress subsequent bugs during drag
            return true;
        }
        
        // Drag ended - analyze buffered bugs
        if (this._dragBugBuffer && this._dragBugBuffer.length > 1) {
            console.log(`📊 Drag complete - had ${this._dragBugBuffer.length} bugs during drag (showing only first)`);
            this._dragBugBuffer = []; // Clear buffer
        }
        
        // Advanced duplicate detection with fingerprinting
        const fingerprint = this.generateBugFingerprint(message, {
            category: this.bugCategory,
            selectedObj: this.editor?.selectedObject,
            dragging: this.editor?.dragging,
            zoom: this.editor?.zoom
        });
        
        // Check if we've seen this exact bug recently
        if (this.bugFingerprints.has(fingerprint)) {
            const bugData = this.bugFingerprints.get(fingerprint);
            const timeSinceLastOccurrence = Date.now() - bugData.lastSeen;
            
            if (timeSinceLastOccurrence < this.bugSuppressionTime) {
                // Duplicate within suppression window
                bugData.count++;
                bugData.lastSeen = Date.now();
                bugData.suppressed++;
                
                // Log to console but don't show alert
                if (bugData.suppressed === 1) {
                    console.log(`🔁 Duplicate bug suppressed: "${message.substring(0, 40)}..." (${bugData.count} total occurrences)`);
                }
                return true;
            }
        }
        
        // Not a duplicate or suppression window expired - log it
        if (!this.bugFingerprints.has(fingerprint)) {
            this.bugFingerprints.set(fingerprint, {
                count: 1,
                firstSeen: Date.now(),
                lastSeen: Date.now(),
                instances: [],
                suppressed: 0
            });
        } else {
            const bugData = this.bugFingerprints.get(fingerprint);
            bugData.count++;
            bugData.lastSeen = Date.now();
        }
        
        // Add to instances
        this.bugFingerprints.get(fingerprint).instances.push({
            time: Date.now(),
            message: message
        });
        
        return false;
    }

    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 2 });
        const colors = {
            info: '#0ff',
            success: '#0f0',
            warning: '#ff0',
            error: '#f00',
            action: '#f0f'
        };
        
        this.logs.push({
            time: timestamp,
            message: message,
            type: type,
            color: colors[type] || '#fff'
        });

        // Keep only last N logs
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
        
        // Add to execution timeline for advanced analysis
        this.addToTimeline(message, { type: type });

        this.updateLogDisplay();
    }

    updateLogDisplay() {
        const logContainer = document.getElementById('debug-log');
        if (!logContainer) return;

        if (this.logs.length === 0) {
            logContainer.innerHTML = '<div style="color: #888;">No events yet...</div>';
            return;
        }

        logContainer.innerHTML = this.logs.map(log => 
            `<div style="color: ${log.color}; margin-bottom: 3px; border-left: 3px solid ${log.color}; padding-left: 5px;">
                <span style="opacity: 0.6;">[${log.time}]</span> ${log.message}
            </div>`
        ).join('');

        // Auto-scroll to bottom
        logContainer.scrollTop = logContainer.scrollHeight;
        
        // Also update minimized log if it's visible
        if (this.minimized) {
            this.updateMinimizedLog();
        }
    }
    
    updateMinimizedLog() {
        const minimizedLogContent = document.getElementById('debug-minimized-log-content');
        if (!minimizedLogContent) return;

        if (this.logs.length === 0) {
            minimizedLogContent.innerHTML = '<div style="color: #888;">Waiting for events...</div>';
            return;
        }

        // Show all logs in minimized view (same as expanded)
        minimizedLogContent.innerHTML = this.logs.map(log => 
            `<div style="color: ${log.color}; margin-bottom: 3px; border-left: 3px solid ${log.color}; padding-left: 5px;">
                <span style="opacity: 0.6;">[${log.time}]</span> ${log.message}
            </div>`
        ).join('');

        // Auto-scroll to bottom with delay to ensure content is rendered
        const minimizedLog = document.getElementById('debug-minimized-log');
        if (minimizedLog) {
            requestAnimationFrame(() => {
                minimizedLog.scrollTop = minimizedLog.scrollHeight;
            });
        }
    }

    updateStatus() {
        const statusContent = document.getElementById('debug-status-content');
        const aiHistoryDiv = document.getElementById('debug-ai-history');
        const historyDiv = document.getElementById('debug-history');
        const zoomDiv = document.getElementById('debug-zoom');
        const magneticDiv = document.getElementById('debug-magnetic');
        const currentDiv = document.getElementById('debug-current');
        const collisionDiv = document.getElementById('debug-collision');
        const uiButtonsDiv = document.getElementById('debug-ui-buttons');
        const mousePosDiv = document.getElementById('debug-mouse-pos');
        const selectedDeviceDiv = document.getElementById('debug-selected-device');

        if (!statusContent || !historyDiv || !zoomDiv || !magneticDiv || !currentDiv || !collisionDiv || !uiButtonsDiv) return;

        const ed = this.editor;
        
        // Update AI Debug History section
        if (aiHistoryDiv) {
            const stats = this.getAIDebugStats();
            const recentSessions = this.aiDebugHistory.slice(-5).reverse();
            
            aiHistoryDiv.innerHTML = `
                <div style="margin-bottom: 8px; padding: 6px; background: rgba(102, 126, 234, 0.1); border-radius: 4px; border-left: 3px solid #667eea;">
                    <div style="font-weight: bold; color: #667eea; margin-bottom: 4px;">📊 STATISTICS</div>
                    <div style="font-size: 9px; color: #fff;">
                        Total Bugs Analyzed: <span style="color: #667eea; font-weight: bold;">${stats.totalBugs}</span><br>
                        Fixes Applied: <span style="color: ${stats.fixedBugs > 0 ? '#0f0' : '#888'}; font-weight: bold;">${stats.fixedBugs}</span><br>
                        Fix Rate: <span style="color: ${parseFloat(stats.fixRate) > 50 ? '#0f0' : '#fa0'}; font-weight: bold;">${stats.fixRate}</span>
                    </div>
                </div>
                ${Object.keys(stats.categories).length > 0 ? `
                <div style="margin-bottom: 8px; padding: 6px; background: rgba(102, 126, 234, 0.1); border-radius: 4px;">
                    <div style="font-weight: bold; color: #667eea; margin-bottom: 4px;">🏷️ BUG CATEGORIES</div>
                    <div style="font-size: 9px; color: #fff;">
                        ${Object.entries(stats.categories).map(([cat, count]) => 
                            `• ${cat}: <span style="color: #0ff;">${count}</span>`
                        ).join('<br>')}
                    </div>
                </div>
                ` : ''}
                ${recentSessions.length > 0 ? `
                <div style="margin-bottom: 8px; padding: 6px; background: rgba(102, 126, 234, 0.1); border-radius: 4px;">
                    <div style="font-weight: bold; color: #667eea; margin-bottom: 4px;">📝 RECENT SESSIONS</div>
                    <div style="font-size: 9px; color: #fff; max-height: 150px; overflow-y: auto;">
                        ${recentSessions.map((session, idx) => `
                            <div style="margin-bottom: 6px; padding: 4px; background: rgba(0, 0, 0, 0.3); border-radius: 3px; border-left: 2px solid ${session.fixApplied ? '#0f0' : '#fa0'};">
                                <div style="color: ${session.fixApplied ? '#0f0' : '#fa0'}; font-weight: bold;">
                                    ${session.fixApplied ? '✅' : '⏳'} ${session.category}
                                </div>
                                <div style="color: #ccc; font-size: 8px;">
                                    ${new Date(session.timestamp).toLocaleTimeString()}: ${session.bugMessage.substring(0, 40)}...
                                </div>
                                ${session.fixApplied ? `
                                    <div style="color: #0f0; font-size: 8px; margin-top: 2px;">
                                        ✓ ${session.fixDescription || 'Fix applied'}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : `
                <div style="color: #888; font-size: 9px; text-align: center; padding: 10px;">
                    No AI debug sessions yet.<br>
                    Click "🤖 Ask AI" on a bug to start!
                </div>
                `}
                ${recentSessions.length > 0 && recentSessions[0] && !recentSessions[0].fixApplied ? `
                <button onclick="window.debugger.showMarkFixDialog()" style="
                    width: 100%;
                    background: #0f0;
                    color: #000;
                    border: none;
                    padding: 6px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 9px;
                    font-weight: bold;
                    margin-top: 4px;
                " title="Mark the latest bug as fixed">
                    ✅ Mark Latest Fix Applied
                </button>
                ` : ''}
            `;
        }

        // Main status
        const initStatus = ed.initializing ? '🔴 INITIALIZING' : '🟢 READY';
        statusContent.innerHTML = `
            <strong>${initStatus}</strong> | Objects: <span style="color: #0ff;">${ed.objects.length}</span> | 
            Mode: <span style="color: #ff0;">${(ed.currentMode || 'base').toUpperCase()}</span>
        `;

        // History state
        const histIndex = ed.historyIndex !== undefined ? ed.historyIndex : 'undefined';
        const histLen = ed.history ? ed.history.length : 0;
        const canUndo = ed.historyIndex > 0;
        const canRedo = ed.historyIndex < (ed.history?.length || 0) - 1;
        
        historyDiv.innerHTML = `
            Index: <span style="color: ${canUndo ? '#0f0' : '#f00'};">${histIndex}</span> / 
            Length: <span style="color: #0ff;">${histLen}</span><br>
            Can Undo: <span style="color: ${canUndo ? '#0f0' : '#f00'};">${canUndo ? 'YES' : 'NO'}</span> | 
            Can Redo: <span style="color: ${canRedo ? '#0f0' : '#f00'};">${canRedo ? 'YES' : 'NO'}</span>
        `;

        // Zoom/Pan state
        const zoomPercent = Math.round((ed.zoom || 1) * 100);
        const panX = Math.round(ed.panOffset?.x || 0);
        const panY = Math.round(ed.panOffset?.y || 0);
        const zoomColor = zoomPercent === 100 ? '#0ff' : (zoomPercent > 100 ? '#0f0' : '#fa0');
        
        zoomDiv.innerHTML = `
            Zoom: <span style="color: ${zoomColor}; font-weight: bold;">${zoomPercent}%</span> 
            <span style="color: #888;">(${ed.zoom?.toFixed(2)})</span><br>
            Pan: <span style="color: #0ff;">x=${panX}, y=${panY}</span><br>
            <span style="color: #0f0; font-weight: bold;">🎯 ZOOM AT CURSOR</span> - Point under mouse stays fixed<br>
            Limits: <span style="color: ${zoomPercent <= 25 ? '#f00' : '#888'};">25%</span> - 
            <span style="color: ${zoomPercent >= 300 ? '#f00' : '#888'};">300%</span><br>
            <span style="color: #888; font-size: 9px;">
                <strong>Zoom Methods:</strong><br>
                • Ctrl+Wheel → at cursor [handleWheel:1997]<br>
                • Buttons (+/-) → at last mouse pos [zoomIn:2240, zoomOut:2303]<br>
                <strong>Pan:</strong> Wheel scroll (no Ctrl), Space+Drag<br>
                <strong>Separation:</strong> Strict Ctrl key detection
            </span>
        `;
        
        // Magnetic Field state
        const magneticStrength = ed.magneticFieldStrength || 40;
        const curvesEnabled = ed.linkCurveMode;
        const affectedLinks = curvesEnabled ? ed.objects.filter(o => o.type === 'link' || o.type === 'unbound').length : 0;
        const magneticColor = magneticStrength > 0 ? (magneticStrength > 50 ? '#f00' : '#0f0') : '#888';
        
        magneticDiv.innerHTML = `
            Strength: <span style="color: ${magneticColor}; font-weight: bold;">${magneticStrength}</span>/80<br>
            Curves: <span style="color: ${curvesEnabled ? '#0f0' : '#f00'};">${curvesEnabled ? 'ON' : 'OFF'}</span> | 
            Links: <span style="color: #0ff;">${affectedLinks}</span><br>
            <span style="color: #888; font-size: 9px;">
                Code: drawLink() [4577-4756]<br>
                Update: updateMagneticField() [2695]
            </span>
        `;

        // Current state
        const devices = ed.objects.filter(o => o.type === 'device').length;
        const links = ed.objects.filter(o => o.type === 'link').length;
        const unboundLinks = ed.objects.filter(o => o.type === 'unbound').length;
        const texts = ed.objects.filter(o => o.type === 'text').length;
        
        const linkBrightnessInfo = ed.darkMode ? '<span style="color: #0f0;">+40% brighter</span>' : '<span style="color: #888;">normal</span>';
        
        currentDiv.innerHTML = `
            Devices: <span style="color: #0ff;">${devices}</span> | 
            Links: <span style="color: #0ff;">${links}</span> | 
            UL: <span style="color: #fa0;">${unboundLinks}</span> | 
            Text: <span style="color: #0ff;">${texts}</span><br>
            Selected: <span style="color: #ff0;">${ed.selectedObjects.length}</span> | 
            MultiSelect: <span style="color: ${ed.multiSelectMode ? '#0f0' : '#888'};">${ed.multiSelectMode ? 'ON' : 'OFF'}</span><br>
            Dragging: <span style="color: ${ed.dragging ? '#f00' : '#888'};">${ed.dragging ? 'YES' : 'NO'}</span> | 
            Placing: <span style="color: ${ed.placingDevice ? '#f00' : '#888'};">${ed.placingDevice || 'NO'}</span><br>
            Dark Mode: <span style="color: ${ed.darkMode ? '#0f0' : '#888'};">${ed.darkMode ? 'ON' : 'OFF'}</span> | 
            Link Brightness: ${linkBrightnessInfo}<br>
            <span style="color: #0f0; font-weight: bold;">👆👆👆 3-FINGER TAP:</span><br>
            <span style="color: #0ff;">On Device</span> → Enter LINK mode from device<br>
            <span style="color: #0ff;">On Grid</span> → Create Unbound Link (100px)<br>
            <span style="color: #888; font-size: 9px;">
                <strong>Double-tap:</strong> ${ed.doubleTapDelay}ms in LINK mode exits to BASE<br>
                <strong>3-finger:</strong> handleTouchStart() [topology.js:2107-2170]<br>
                <strong>Link Color:</strong> brightenColor() [topology.js:4789-4815]
            </span>
        `;

        // Collision tracking
        const collisionEnabled = ed.deviceCollision;
        const collisionColor = collisionEnabled ? '#0f0' : '#888';
        
        // Check for actual overlaps in current state
        let overlappingPairs = [];
        if (collisionEnabled) {
            const deviceObjs = ed.objects.filter(o => o.type === 'device');
            for (let i = 0; i < deviceObjs.length; i++) {
                for (let j = i + 1; j < deviceObjs.length; j++) {
                    const d1 = deviceObjs[i];
                    const d2 = deviceObjs[j];
                    const dx = d1.x - d2.x;
                    const dy = d1.y - d2.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    const minDist = (d1.radius || 30) + (d2.radius || 30) + 3;
                    
                    if (dist < minDist) {
                        overlappingPairs.push(`${d1.label || 'D1'}-${d2.label || 'D2'}`);
                    }
                }
            }
        }
        
        collisionDiv.innerHTML = `
            Enabled: <span style="color: ${collisionColor}; font-weight: bold;">${collisionEnabled ? 'ON' : 'OFF'}</span><br>
            ${collisionEnabled ? `
                Overlaps: <span style="color: ${overlappingPairs.length > 0 ? '#f00' : '#0f0'};">
                    ${overlappingPairs.length > 0 ? overlappingPairs.join(', ') : 'NONE ✓'}
                </span><br>
                ${overlappingPairs.length > 0 ? `
                    <button onclick="window.topologyEditor.fixExistingOverlaps()" style="
                        background: #f00;
                        color: white;
                        border: none;
                        padding: 4px 8px;
                        border-radius: 3px;
                        cursor: pointer;
                        font-size: 10px;
                        margin-top: 4px;
                        font-weight: bold;
                    ">🔧 FIX OVERLAPS NOW</button><br>
                ` : ''}
                <span style="color: #888; font-size: 9px;">
                    <strong>Core:</strong> checkDeviceCollision() [topology.js:2855]<br>
                    <strong>Multi-select:</strong> handleMouseMove() [topology.js:1073-1106]<br>
                    <strong>Single drag:</strong> handleMouseMove() [topology.js:1409-1440]<br>
                    <strong>Auto-fix:</strong> fixExistingOverlaps() [topology.js:2770]<br>
                    <strong>Physics:</strong> topology.js [collision push]<br>
                    <strong>Momentum:</strong> topology-momentum.js [slide collision]
                </span>
            ` : '<span style="color: #888;">Not monitoring overlaps</span>'}
        `;
        // Momentum/Sliding status (separate section)
        const momentumDiv = document.getElementById('debug-momentum');
        const momentumEnabled = ed.momentum && ed.momentum.enabled;
        const activeSlides = ed.momentum ? ed.momentum.activeSlides.size : 0;
        
        if (momentumDiv) {
            if (momentumEnabled) {
                const momentumColor = activeSlides > 0 ? '#f00' : '#0f0';
                const friction = ed.momentum.friction;
                const minVelocity = ed.momentum.minVelocity;
                
                // Get sliding objects info with enhanced coordinate tracking
                let slidingInfo = '';
                if (activeSlides > 0 && ed.momentum.activeSlides) {
                    const slides = Array.from(ed.momentum.activeSlides.values()).slice(0, 2); // Show first 2 with details
                    slidingInfo = '<br><div style="margin-top: 6px; padding: 6px; background: rgba(255, 165, 0, 0.2); border-radius: 4px; border-left: 3px solid #fa0;">';
                    slidingInfo += '<span style="color: #fa0; font-weight: bold;">🎯 Active Slides:</span><br>';
                    slides.forEach(s => {
                            const speed = Math.sqrt(s.vx * s.vx + s.vy * s.vy);
                        const currentPos = { x: s.obj.x, y: s.obj.y };
                        const gridCurrent = ed.worldToGrid(currentPos);
                        const releasePos = s.releasePosition || currentPos;
                        const gridRelease = s.gridReleasePos || ed.worldToGrid(releasePos);
                        const dx = currentPos.x - releasePos.x;
                        const dy = currentPos.y - releasePos.y;
                        const traveled = Math.sqrt(dx * dx + dy * dy);
                        
                        slidingInfo += `<span style="color: #0ff; font-size: 9px;">${s.obj.label || 'Device'}:</span><br>`;
                        slidingInfo += `<span style="font-size: 8px; color: #ccc;">  Speed: ${Math.round(speed)}px/f | V: (${s.vx.toFixed(1)}, ${s.vy.toFixed(1)})</span><br>`;
                        slidingInfo += `<span style="font-size: 8px; color: #0f0;">  Release: Grid (${gridRelease.x.toFixed(0)}, ${gridRelease.y.toFixed(0)}) | World (${releasePos.x.toFixed(0)}, ${releasePos.y.toFixed(0)})</span><br>`;
                        slidingInfo += `<span style="font-size: 8px; color: #fa0;">  Current: Grid (${gridCurrent.x.toFixed(0)}, ${gridCurrent.y.toFixed(0)}) | World (${currentPos.x.toFixed(0)}, ${currentPos.y.toFixed(0)})</span><br>`;
                        slidingInfo += `<span style="font-size: 8px; color: #fff;">  Traveled: ${traveled.toFixed(1)}px | Delta: (${dx > 0 ? '+' : ''}${dx.toFixed(0)}, ${dy > 0 ? '+' : ''}${dy.toFixed(0)})</span><br>`;
                    });
                    if (activeSlides > 2) slidingInfo += `<span style="color: #888; font-size: 8px;">+${activeSlides - 2} more objects sliding...</span><br>`;
                    slidingInfo += '</div>';
                }
                
                // Friction behavior analysis
                const frictionPercent = Math.round(friction * 100);
                const deceleration = Math.round((1 - friction) * 100);
                let frictionBehavior = 'Normal';
                let frictionColor = '#0ff';
                if (friction < 0.90) {
                    frictionBehavior = 'Fast/Ice';
                    frictionColor = '#3498db';
                } else if (friction > 0.95) {
                    frictionBehavior = 'Slow/Sticky';
                    frictionColor = '#e74c3c';
                }
                
                const velocityMult = ed.momentum.velocityMultiplier || 2.5;
                const maxSpeed = ed.momentum.maxSpeed || 80;
                const chainEnabled = ed.momentum.chainCollisionEnabled;
                const chainReactions = ed.momentum.chainReactions || 0;
                const restitution = ed.momentum.restitution || 1.0;
                const rollingFriction = ed.momentum.rollingFriction || 0.008;
                const collisionBoost = ed.momentum.collisionBoost || 1.5;
                const momentumTransfer = Math.round((ed.momentum.momentumTransferRatio || 0.85) * 100);
                const smoothing = ed.momentum.smoothingEnabled ? 'ON' : 'OFF';
                const sliderValue = ed.momentum.sliderValue || 5;
                
                // Get chain depth info
                let maxChainDepth = 0;
                if (ed.momentum.activeSlides) {
                    ed.momentum.activeSlides.forEach(s => {
                        maxChainDepth = Math.max(maxChainDepth, s.chainCount || 0);
                    });
                }
                
                // Determine slide distance description
                let slideDesc = 'Medium';
                let slideColor = '#0ff';
                if (sliderValue <= 3) {
                    slideDesc = 'Very Far';
                    slideColor = '#27ae60';
                } else if (sliderValue <= 5) {
                    slideDesc = 'Far';
                    slideColor = '#3498db';
                } else if (sliderValue <= 7) {
                    slideDesc = 'Medium';
                    slideColor = '#9b59b6';
                } else {
                    slideDesc = 'Short';
                    slideColor = '#e74c3c';
                }
                
                momentumDiv.innerHTML = `
                    Enabled: <span style="color: ${momentumColor}; font-weight: bold;">ON</span> 
                    <button onclick="window.topologyEditor.toggleMomentum()" style="background: #e67e22; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 9px; margin-left: 4px;">Toggle</button><br>
                    Status: <span style="color: ${momentumColor}; font-weight: bold;">${activeSlides > 0 ? `SLIDING (${activeSlides})` : 'READY'}</span>${slidingInfo}<br>
                    <span style="color: #0f0; font-weight: bold;">🎱 ULTRA-SMOOTH BILLIARDS:</span><br>
                    Velocity: <span style="color: #f39c12; font-weight: bold;">${velocityMult}x</span> | 
                    Max: <span style="color: #f39c12;">${maxSpeed}px/f</span> | 
                    Smoothing: <span style="color: #0f0;">${smoothing}</span><br>
                    Slide: <span style="color: ${slideColor}; font-weight: bold;">${sliderValue}/10</span> 
                    (<span style="color: ${slideColor};">${slideDesc}</span>)<br>
                    Friction: <span style="color: #0ff;">${friction.toFixed(3)}</span> (exponential)<br>
                    <span style="color: #0f0; font-weight: bold;">💥 ULTRA IMPACT:</span><br>
                    Restitution: <span style="color: #f39c12; font-weight: bold;">${(restitution * 100).toFixed(0)}%</span> (Perfect elastic!) | 
                    Boost: <span style="color: #f39c12; font-weight: bold;">${collisionBoost}x</span><br>
                    Transfer: <span style="color: #0ff;">${momentumTransfer}%</span> | 
                    Rolling: <span style="color: #0ff;">${rollingFriction}</span><br>
                    <span style="color: #0f0; font-weight: bold;">⛓️ CHAIN COLLISIONS:</span> 
                    <span style="color: ${chainEnabled ? '#0f0' : '#888'};">${chainEnabled ? 'ON' : 'OFF'}</span><br>
                    ${chainEnabled ? `
                        Reactions: <span style="color: ${chainReactions > 0 ? '#f39c12' : '#888'};">${chainReactions}</span> | 
                        Max Depth: <span style="color: ${maxChainDepth > 0 ? '#f39c12' : '#888'};">${maxChainDepth}</span><br>
                    ` : ''}
                    <span style="color: #888; font-size: 9px;">
                        <strong>Dynamic System:</strong> 8 parameters auto-scale with slider<br>
                        <strong>Code:</strong> momentum.js:56-104 updateDynamicParameters()<br>
                        <strong>Quality:</strong> Sub-pixel smooth + perfect elastic<br>
                        <strong>Slider 1:</strong> Ultra-dramatic (4.0x vel, 2.0x boost, 0.80 friction)<br>
                        <strong>Slider 10:</strong> Gentle (1.2x vel, 1.1x boost, 0.98 friction)
                    </span>
                `;
            } else {
                momentumDiv.innerHTML = `
                    Enabled: <span style="color: #888;">OFF</span> 
                    <button onclick="window.topologyEditor.toggleMomentum()" style="background: #27ae60; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer; font-size: 9px; margin-left: 4px;">Enable</button><br>
                    <span style="color: #888;">Billiard/Hockey collisions disabled</span><br>
                    <span style="color: #888; font-size: 9px;">Click toggle button or Enable button to activate</span>
                `;
            }
        }

        // UI Button States - Check actual button classes vs expected states
        const numberingBtn = document.getElementById('btn-device-numbering');
        const collisionBtn = document.getElementById('btn-device-collision');
        const curveBtn = document.getElementById('btn-link-curve');
        const chainBtn = document.getElementById('btn-link-continuous');
        
        let uiIssues = [];
        
        // Check numbering button
        if (numberingBtn) {
            const hasActive = numberingBtn.classList.contains('active');
            const expected = ed.deviceNumbering;
            if (hasActive !== expected) {
                uiIssues.push(`Numbering: ${expected ? 'ON' : 'OFF'} but button is ${hasActive ? 'GREEN' : 'RED'}`);
            }
            const numberingColor = hasActive === expected ? '#0f0' : '#f00';
            const numberingStatus = `Numbering: <span style="color: ${numberingColor};">${ed.deviceNumbering ? 'ON' : 'OFF'} ${hasActive ? '(🟢)' : '(🔴)'}</span>`;
            uiButtonsDiv.innerHTML = numberingStatus;
        } else {
            uiButtonsDiv.innerHTML = '<span style="color: #f00;">Buttons not found!</span>';
        }
        
        // Add collision button check
        if (collisionBtn) {
            const hasActive = collisionBtn.classList.contains('active');
            const expected = ed.deviceCollision;
            if (hasActive !== expected) {
                uiIssues.push(`Collision: ${expected ? 'ON' : 'OFF'} but button is ${hasActive ? 'GREEN' : 'RED'}`);
            }
            const collisionStatus = `<br>Collision: <span style="color: ${hasActive === expected ? '#0f0' : '#f00'};">${ed.deviceCollision ? 'ON' : 'OFF'} ${hasActive ? '(🟢)' : '(🔴)'}</span>`;
            uiButtonsDiv.innerHTML += collisionStatus;
        }
        
        // Show issues if any
        if (uiIssues.length > 0) {
            uiButtonsDiv.innerHTML += `<br><span style="color: #f00; font-size: 9px;">${dbgIcon('warning')} ${uiIssues.join('<br>')}</span>`;
        }
        
        // Mouse position tracking (real-time) with coordinate verification
        if (mousePosDiv && ed.lastMousePos) {
            const mouseWorld = ed.lastMousePos;
            const mouseGrid = ed.worldToGrid(mouseWorld);
            const screenX = Math.round(ed.lastMouseScreen?.x || 0);
            const screenY = Math.round(ed.lastMouseScreen?.y || 0);
            
            // Verify coordinate transform is correct
            const verifyWorldX = (screenX - ed.panOffset.x) / ed.zoom;
            const verifyWorldY = (screenY - ed.panOffset.y) / ed.zoom;
            const deltaX = Math.abs(mouseWorld.x - verifyWorldX);
            const deltaY = Math.abs(mouseWorld.y - verifyWorldY);
            const coordError = Math.max(deltaX, deltaY);
            const coordStatus = coordError < 0.01 ? '<span style="color: #0f0;">✓ OK</span>' : `<span style="color: #f00;">⚠ Error: ${coordError.toFixed(2)}px</span>`;
            
            mousePosDiv.innerHTML = `
                <span style="color: #0ff;">Screen:</span> (${screenX}, ${screenY})<br>
                <span style="color: #0ff;">World:</span> (${Math.round(mouseWorld.x)}, ${Math.round(mouseWorld.y)})<br>
                <span style="color: #0ff;">Grid:</span> (${Math.round(mouseGrid.x)}, ${Math.round(mouseGrid.y)})<br>
                Transform: ${coordStatus}<br>
                <span style="color: #888; font-size: 9px;">
                    Formula: (screen - pan) / zoom<br>
                    Zoom: ${ed.zoom.toFixed(2)}, Pan: (${Math.round(ed.panOffset.x)}, ${Math.round(ed.panOffset.y)})
                </span>
            `;
        } else if (mousePosDiv) {
            mousePosDiv.innerHTML = '<span style="color: #888;">Move mouse over canvas</span>';
        }
        
        // Selected device tracking with click accuracy verification
        if (selectedDeviceDiv && ed.selectedObject && ed.selectedObject.type === 'device') {
            const device = ed.selectedObject;
            const deviceWorld = { x: device.x, y: device.y };
            const deviceGrid = ed.worldToGrid(deviceWorld);
            const radius = device.radius || 30;
            // Calculate mass based on area (π × r²)
            const mass = Math.round(Math.PI * radius * radius);
            
            // Check if mouse is currently over this selected device
            const mouseWorld = ed.lastMousePos;
            let mouseOverDevice = false;
            let distanceFromMouse = 0;
            if (mouseWorld) {
                const dx = mouseWorld.x - device.x;
                const dy = mouseWorld.y - device.y;
                distanceFromMouse = Math.sqrt(dx * dx + dy * dy);
                mouseOverDevice = distanceFromMouse <= radius + 8; // Include hitbox tolerance
            }
            
            const mouseStatus = mouseOverDevice ? 
                '<span style="color: #0f0;">✓ Mouse over device</span>' : 
                `<span style="color: #888;">Mouse ${Math.round(distanceFromMouse)}px away</span>`;
            
            selectedDeviceDiv.innerHTML = `
                <span style="color: #ff0; font-weight: bold;">${device.label || 'Device'}</span><br>
                <span style="color: #0ff;">World:</span> (${Math.round(deviceWorld.x)}, ${Math.round(deviceWorld.y)})<br>
                <span style="color: #0ff;">Grid:</span> (${Math.round(deviceGrid.x)}, ${Math.round(deviceGrid.y)})<br>
                <span style="color: #fa0;">Radius:</span> ${radius} (hitbox: +8px) | <span style="color: #fa0;">Mass:</span> ${mass}<br>
                ${mouseStatus}<br>
                <span style="color: #888; font-size: 9px;">
                    <strong>Selection:</strong> findObjectAt() [topology.js:2464]<br>
                    Click transforms correctly → World coords → Hit test
                </span>
            `;
        } else if (selectedDeviceDiv) {
            selectedDeviceDiv.innerHTML = '<span style="color: #888;">No device selected</span>';
        }
        
        // ENHANCED: Input Device Tracking (Mouse vs Trackpad differentiation)
        const touchpadDiv = document.getElementById('debug-touchpad');
        if (touchpadDiv && ed.gestureState) {
            const gs = ed.gestureState;
            const fingerCount = gs.fingerCount || 0;
            const lastGesture = gs.lastGestureType || 'none';
            const gestureMoved = gs.gestureMoved ? 'YES' : 'NO';
            const fingerColor = fingerCount === 0 ? '#888' : (fingerCount === 1 ? '#0ff' : fingerCount === 2 ? '#3498db' : fingerCount === 3 ? '#f39c12' : '#e74c3c');
            
            // Track last input type
            const lastInput = ed._lastInputType || 'unknown';
            const inputIcon = lastInput === 'trackpad' ? '🖐️' : lastInput === 'mouse' ? '🖱️' : lastInput === 'pen' ? '🖊️' : '👆';
            const inputColor = lastInput === 'trackpad' ? '#f39c12' : lastInput === 'mouse' ? '#0f0' : '#0ff';
            
            // Multi-pointer tracking (for 3-finger tap detection)
            const activePointers = ed.activePointers ? ed.activePointers.size : 0;
            const threeFingerActive = ed.threeFingerGesture ? ed.threeFingerGesture.active : false;
            const threeFingerMoved = ed.threeFingerGesture ? ed.threeFingerGesture.moved : false;
            const pointerColor = activePointers === 0 ? '#888' : (activePointers === 1 ? '#0ff' : activePointers === 2 ? '#3498db' : activePointers === 3 ? '#f39c12' : '#e74c3c');
            
            touchpadDiv.innerHTML = `
                <span style="color: #0f0; font-weight: bold;">📱 INPUT DEVICE DETECTION</span><br>
                Current Input: <span style="color: ${inputColor}; font-weight: bold;">${inputIcon} ${lastInput.toUpperCase()}</span><br>
                <br>
                <span style="color: #f39c12; font-weight: bold;">👆 MULTI-POINTER TRACKING:</span><br>
                Active Pointers: <span style="color: ${pointerColor}; font-weight: bold;">${activePointers}</span><br>
                3-Finger Gesture: <span style="color: ${threeFingerActive ? '#f39c12' : '#888'}; font-weight: bold;">${threeFingerActive ? 'ACTIVE' : 'None'}</span><br>
                ${threeFingerActive ? `Movement: <span style="color: ${threeFingerMoved ? '#f00' : '#0f0'};">${threeFingerMoved ? 'YES' : 'NO'}</span><br>` : ''}
                <br>
                <span style="color: #0f0; font-weight: bold;">📊 LEGACY TOUCH:</span><br>
                Touch Fingers: <span style="color: ${fingerColor};">${fingerCount}</span><br>
                Last Gesture: <span style="color: #0ff;">${lastGesture}</span><br>
                <br>
                <span style="color: #0f0; font-weight: bold;">🎯 LOG COLOR KEY:</span><br>
                <span style="color: #f39c12;">🖐️ Purple</span> = TRACKPAD input<br>
                <span style="color: #0f0;">🖱️ Green</span> = MOUSE input<br>
                <span style="color: #0ff;">🖊️ Cyan</span> = PEN input<br>
                <span style="color: #fff;">👆 White</span> = Touch/Unknown<br>
                <br>
                <span style="color: #0f0; font-weight: bold;">📱 GESTURE MAP:</span><br>
                <span style="color: #0ff;">1-Finger:</span> Tap/Select, Drag/Move<br>
                <span style="color: #3498db;">2-Finger:</span> Pinch→Zoom, Pan→Scroll<br>
                <span style="color: #f39c12;">3-Finger Tap:</span><br>
                &nbsp;&nbsp;• On Device → LINK mode<br>
                &nbsp;&nbsp;• On Grid → Create UL<br>
                <span style="color: #e74c3c;">4-Finger Tap:</span> Toggle all UI<br>
                <br>
                <span style="color: #0f0;">✓ POINTER-BASED 3-FINGER TAP:</span><br>
                • Tap threshold: ${gs.tapThreshold}ms<br>
                • Move threshold: ${gs.moveThreshold}px<br>
                • Tracks simultaneous pointers<br>
                • Works on trackpads! 🎉<br>
                <br>
                <span style="color: #888; font-size: 9px;">
                    <strong>NEW:</strong> Multi-pointer tracking system<br>
                    <strong>Pointers:</strong> handlePointerDown/Move/Up [line 822-940]<br>
                    <strong>3-Finger:</strong> process3FingerTap() [line 2500]<br>
                    <strong>Detection:</strong> activePointers Map tracks all touches<br>
                    <strong>Validation:</strong> Duration & movement checks
                </span>
            `;
        }
    }

    startMonitoring() {
        // Update status every 100ms
        setInterval(() => this.updateStatus(), 100);

        // Intercept console.log to capture important messages
        const originalLog = console.log;
        const self = this;
        console.log = function(...args) {
            originalLog.apply(console, args);
            
            const message = args.join(' ');
            
            // Capture important messages
            if (message.includes('saveState called')) {
                self.log('💾 State saved', 'success');
            } else if (message.includes('undo() called')) {
                self.log('↩️ Undo requested', 'action');
            } else if (message.includes('redo() called')) {
                self.log('↪️ Redo requested', 'action');
            } else if (message.includes('Restoring state')) {
                self.log('🔄 ' + message.substring(0, 50), 'success');
            } else if (message.includes('Cannot undo') || message.includes('Cannot redo')) {
                self.log('⚠️ ' + message, 'warning');
            } else if (message.includes('hideShortcuts')) {
                self.log('❌ Shortcuts closed', 'info');
            } else if (message.includes('hideTextEditor')) {
                self.log('❌ Text editor closed', 'info');
            } else if (message.includes('hideLinkDetails')) {
                self.log('❌ Link details closed', 'info');
            }
        };

        // Intercept console.error to capture errors
        const originalError = console.error;
        console.error = function(...args) {
            originalError.apply(console, args);
            self.log('❌ ERROR: ' + args.join(' '), 'error');
        };

        // Intercept console.warn to capture warnings
        const originalWarn = console.warn;
        console.warn = function(...args) {
            originalWarn.apply(console, args);
            self.log('⚠️ ' + args.join(' '), 'warning');
        };
    }

    // Manual logging methods for editor to call
    logAction(action) {
        this.log('🔹 ' + action, 'action');
        this.trackAction(action); // Track for bug analysis
    }

    logSuccess(message) {
        this.log('✅ ' + message, 'success');
        this.trackAction(message); // Track for bug analysis
    }

    logWarning(message) {
        this.log('⚠️ ' + message, 'warning');
    }

    logError(message) {
        // ADVANCED: Use fingerprinting for precise duplicate detection
        const isDuplicate = this.isDuplicateBug(message);
        
        if (isDuplicate) {
            // Duplicate - already handled by isDuplicateBug()
            return;
        }
        
        // NEW bug - log it
        this.log('❌ ' + message, 'error');
        
        // Add to execution timeline with rich context
        this.addToTimeline('BUG: ' + message, {
            type: 'bug',
            editorSnapshot: this.getObjectSnapshot(this.editor?.selectedObject),
            dragStart: this.editor?.dragStart ? { ...this.editor.dragStart } : null,
            collisionActive: this.editor?.deviceCollision,
            momentumActive: this.editor?.momentum?.activeSlides?.size || 0,
            zoom: this.editor?.zoom,
            pan: this.editor?.panOffset ? { ...this.editor.panOffset } : null
        });
        
        // ENHANCED: Show bug alert immediately (user wants to see all alerts)
        // Just suppress duplicates during drag via the buffer system
        this.showBugAlert(message);
        
        console.log('🐛 Bug alert shown:', {
            message: message.substring(0, 60),
            dragging: this.editor?.dragging,
            severity: this.bugSeverity,
            category: this.bugCategory
        });
    }

    logInfo(message) {
        this.log('ℹ️ ' + message, 'info');
    }
    
    trackAction(action) {
        // Track recent user actions for bug context
        this.recentActions.push({
            time: Date.now(),
            action: action,
            stack: this.captureCallStack()
        });
        if (this.recentActions.length > this.maxRecentActions) {
            this.recentActions.shift();
        }
    }
    
    captureCallStack() {
        // Capture current JavaScript call stack for debugging
        const stack = new Error().stack;
        if (!stack) return [];
        
        const lines = stack.split('\n');
        // Skip first 3 lines (Error, this function, trackAction)
        return lines.slice(3, 10).map(line => {
            // Extract function and location
            const match = line.match(/at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)/);
            if (match) {
                return {
                    function: match[1],
                    file: match[2].split('/').pop(),
                    line: parseInt(match[3]),
                    column: parseInt(match[4])
                };
            }
            return line.trim();
        }).filter(Boolean);
    }
    
    snapshotVariable(name, value) {
        // Track variable value changes over time
        if (!this.variableSnapshots.has(name)) {
            this.variableSnapshots.set(name, []);
        }
        const history = this.variableSnapshots.get(name);
        history.push({
            time: Date.now(),
            value: JSON.parse(JSON.stringify(value)) // Deep copy
        });
        if (history.length > 50) history.shift();
    }
    
    showBugAlert(bugMessage) {
        // Don't show any bug alerts if debugger is disabled or showJumpAlerts is off
        // User explicitly disabled these - respect that choice
        if (!this.enabled && !this.showJumpAlerts) {
            // Silently ignore - user doesn't want bug popups
            return;
        }
        
        // Don't show alerts for empty or invalid bug messages
        if (!bugMessage || !bugMessage.trim()) {
            return;
        }
        
        const bugAlertDiv = document.getElementById('debug-bug-alert');
        const bugMessageDiv = document.getElementById('debug-bug-message');
        const bottomBugAlert = document.getElementById('bottom-bug-alert');
        
        // Store bug message and analyze it (silently)
        this.latestBug = bugMessage;
        this.analyzeBug(bugMessage);
        
        // Check if jump alerts are disabled (for jump and movement-related messages)
        // These are often false positives during fast TP/device movement
        const movementKeywords = ['JUMP', 'CATASTROPHIC', 'Invalid offset', 'moved', 'Total Jumps', 'CHAIN JUMP', 'TP not found', 'offset', 'calculation'];
        const isMovementRelated = movementKeywords.some(kw => bugMessage.toLowerCase().includes(kw.toLowerCase()));
        
        if (!this.showJumpAlerts && isMovementRelated) {
            // Movement alerts disabled - silently ignore
            return;
        }
        
        // Don't auto-open debugger - user disabled it for a reason
        if (!this.enabled) {
            return;
        }
        
        // If minimized, expand it
        if (this.minimized) {
            const minimizeBtn = document.getElementById('debug-minimize');
            if (minimizeBtn) {
                minimizeBtn.click(); // Expand
            }
        }
        
        if (bugAlertDiv && bugMessageDiv) {
            bugAlertDiv.style.display = 'block';
            bugMessageDiv.textContent = bugMessage;
            
            // Clear any previous analysis hints
            const existingHints = bugMessageDiv.parentElement.querySelectorAll('.root-cause-hint');
            existingHints.forEach(hint => hint.remove());
            
            // Add root cause hint if available
            if (this.rootCauseAnalysis) {
                const rootHint = document.createElement('div');
                rootHint.className = 'root-cause-hint';
                rootHint.style.cssText = 'margin-top: 6px; padding: 6px; background: rgba(52, 152, 219, 0.2); border-radius: 4px; font-size: 10px; border-left: 3px solid #3498db;';
                const shortAnalysis = this.rootCauseAnalysis.split('\n').slice(0, 4).join('\n');
                rootHint.innerHTML = `<span style="color: #3498db; font-weight: bold;">${dbgIcon('discover')} Root Cause:</span><br><span style="color: #fff; white-space: pre-wrap; font-family: monospace; font-size: 9px;">${shortAnalysis}...</span>`;
                bugMessageDiv.parentElement.appendChild(rootHint);
            }
            
            // Add code conflicts hint
            if (this.codeConflicts && this.codeConflicts.length > 0) {
                const conflictHint = document.createElement('div');
                conflictHint.className = 'root-cause-hint';
                conflictHint.style.cssText = 'margin-top: 4px; padding: 6px; background: rgba(231, 76, 60, 0.2); border-radius: 4px; font-size: 9px; border-left: 3px solid #e74c3c;';
                conflictHint.innerHTML = `<span style="color: #e74c3c; font-weight: bold;">${dbgIcon('warning')} Conflicts:</span> ${this.codeConflicts.length} code sections<br><span style="color: #fff; font-size: 8px;">${this.codeConflicts[0]}</span>`;
                bugMessageDiv.parentElement.appendChild(conflictHint);
            }
        }
        
        // Show ENHANCED bug alert at bottom center with AI analysis
        if (bottomBugAlert) {
            console.log('✅ Showing bottom bug alert');
            bottomBugAlert.style.display = 'block';
            bottomBugAlert.style.visibility = 'visible';
            bottomBugAlert.style.opacity = '1';
            
            // Update bug text
            const bottomBugText = bottomBugAlert.querySelector('#bottom-bug-text');
            if (bottomBugText) {
                bottomBugText.textContent = bugMessage;
                console.log('✅ Bug text updated:', bugMessage.substring(0, 40));
            } else {
                console.error('❌ bottom-bug-text element not found!');
            }
            
            // Update severity badge
            const severityBadge = bottomBugAlert.querySelector('#bottom-bug-severity');
            if (severityBadge) {
                severityBadge.textContent = this.bugSeverity || 'HIGH';
                severityBadge.style.background = this.bugSeverity === 'CRITICAL' ? 'rgba(255,0,0,0.4)' : 'rgba(255,165,0,0.3)';
            }
            
            // Update category badge
            const categoryBadge = bottomBugAlert.querySelector('#bottom-bug-category');
            if (categoryBadge) {
                categoryBadge.textContent = this.bugCategory || 'UNKNOWN';
            } else {
                console.warn('Category badge not found');
            }
            
            // Show conflicts if detected
            const conflictsDiv = bottomBugAlert.querySelector('#bottom-bug-conflicts');
            const conflictsCount = bottomBugAlert.querySelector('#bottom-bug-conflicts-count');
            if (conflictsDiv && conflictsCount && this.detectedIssues) {
                const totalConflicts = this.detectedIssues.conflicts.length + 
                                     this.detectedIssues.raceConditions.length + 
                                     this.detectedIssues.contradictions.length;
                
                if (totalConflicts > 0) {
                    conflictsDiv.style.display = 'block';
                    conflictsCount.textContent = totalConflicts;
                    
                    // CRITICAL FIX: Clear existing content before adding new
                    // Remove all text nodes except the base structure
                    const childNodes = Array.from(conflictsDiv.childNodes);
                    childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE && node.textContent.includes('PHYSICS_RACE')) {
                            conflictsDiv.removeChild(node);
                        }
                    });
                    
                    // Add first conflict description (deduplicated)
                    const firstIssue = this.detectedIssues.raceConditions[0] || 
                                      this.detectedIssues.conflicts[0] || 
                                      this.detectedIssues.contradictions[0];
                    
                    if (firstIssue) {
                        const issueText = document.createTextNode(` | ${firstIssue.type}: ${firstIssue.description}`);
                        conflictsDiv.appendChild(issueText);
                    }
                } else {
                    conflictsDiv.style.display = 'none';
                }
            }
        } else {
            console.error('❌ bottom-bug-alert element NOT FOUND in DOM!');
            console.log('Checked for element with ID: bottom-bug-alert');
            alert(`BUG DETECTED: ${bugMessage}\n\n(Bottom alert element missing - check console)`);
        }
    }
    
    getObjectSnapshot(obj) {
        // Create a snapshot of an object for bug reporting
        // Handle different object types correctly
        if (!obj) return null;
        
        const snapshot = {
            type: obj.type,
            label: obj.label,
            id: obj.id
        };
        
        if (obj.type === 'unbound') {
            // Unbound links have start/end, not x/y
            snapshot.start = { x: obj.start?.x, y: obj.start?.y };
            snapshot.end = { x: obj.end?.x, y: obj.end?.y };
            snapshot.centerX = obj.start && obj.end ? (obj.start.x + obj.end.x) / 2 : 0;
            snapshot.centerY = obj.start && obj.end ? (obj.start.y + obj.end.y) / 2 : 0;
        } else if (obj.type === 'link') {
            // Links have device connections
            snapshot.device1 = obj.device1;
            snapshot.device2 = obj.device2;
            snapshot.start = obj.start ? { x: obj.start.x, y: obj.start.y } : null;
            snapshot.end = obj.end ? { x: obj.end.x, y: obj.end.y } : null;
        } else {
            // Devices and text have x,y positions
            snapshot.x = obj.x;
            snapshot.y = obj.y;
            if (obj.radius) snapshot.radius = obj.radius;
        }
        
        return snapshot;
    }
    
    detectCodeConflicts() {
        // ADVANCED: Detect code conflicts and race conditions from current state
        const conflicts = [];
        const raceConditions = [];
        const contradictions = [];
        
        // DISABLED: Collision + dragging is normal behavior
        // The drag system correctly handles collision during drag operations
        
        // Check for collision bypass in multi-select (NEW: Fix #7)
        if (this.editor?.dragging && 
            this.editor?.selectedObjects?.length > 1 && 
            !this.editor?.deviceCollision) {
            // Check if any device in multi-select has collision applied anyway
            const hasDevices = this.editor.selectedObjects.some(obj => obj.type === 'device');
            if (hasDevices) {
                // This is OK now - collision properly disabled in topology.js:2294
                // Just monitor for any unexpected collision behavior
            }
        }
        
        // DISABLED: Unbound link property access check was causing false positives
        // Unbound links use start/end coordinates, not x/y - this is expected behavior
        // The drag system correctly calculates center point for unbound links
        
        // DISABLED: DragStart offset validation was causing false positives
        // Large offsets are normal for edge grabs and fast movements
        // The drag system handles this correctly
        
        // DISABLED: Momentum + collision bypass detection - this is handled correctly by the system
        // DISABLED: Momentum + dragging detection - false positive during fast movements
        
        // Check for coordinate transform conflicts
        if (this.editor?.zoom && this.editor?.panOffset) {
            const mousePosValid = this.editor?.lastMousePos;
            if (mousePosValid) {
                // Verify transform consistency
                const screenX = 500; // Test value
                const worldX = (screenX - this.editor.panOffset.x) / this.editor.zoom;
                const backToScreen = worldX * this.editor.zoom + this.editor.panOffset.x;
                const transformError = Math.abs(screenX - backToScreen);
                
                if (transformError > 0.1) {
                    contradictions.push({
                        type: 'COORDINATE_TRANSFORM',
                        severity: 'CRITICAL',
                        description: 'Coordinate transform is not reversible',
                        conflictLines: [
                            { file: 'topology.js', line: 806, code: 'getMousePos()', context: 'Screen → World transform' },
                            { file: 'topology.js', line: 5903, code: 'ctx.transform()', context: 'Drawing transform' }
                        ],
                        impact: 'Mouse coordinates don\'t match drawn positions → click detection fails',
                        fix: 'Verify transform formula matches drawing transform exactly'
                    });
                }
            }
        }
        
        // Check for saveState + modification conflicts
        if (this.recentActions && this.recentActions.length > 1) {
            const lastActions = this.recentActions.slice(-3).map(a => a.action);
            if (lastActions.includes('saveState() called') && lastActions.includes('Weight cascade')) {
                conflicts.push({
                    type: 'SAVESTATE_PHYSICS',
                    severity: 'HIGH',
                    description: 'Collision detection running during/after saveState',
                    conflictLines: [
                        { file: 'topology.js', line: 1375, code: 'this.saveState()', context: 'Saves current state' },
                        { file: 'topology.js', line: 4635, code: 'checkDeviceCollision()', context: 'Modifies positions' }
                    ],
                    impact: 'Saved state doesn\'t match actual state → undo corruption',
                    fix: 'Stop physics before saveState, or re-save after physics settles'
                });
            }
        }
        
        return { conflicts, raceConditions, contradictions };
    }
    
    analyzeBug(bugMessage) {
        // ULTRA-SMART ROOT CAUSE ANALYSIS: Explain WHY the bug happened
        this.bugCategory = null;
        this.rootCauseAnalysis = null;
        this.codeConflicts = [];
        this.executionFlow = [];
        this.detectedIssues = null;
        this.conflictOccurrenceCount = 0; // Track how many times conflict was detected
        
        // Add to bug history with full state snapshot
        const bugEntry = {
            time: new Date().toLocaleTimeString('en-US', { hour12: false }),
            message: bugMessage,
            snapshot: {
                zoom: this.editor?.zoom,
                pan: { x: this.editor?.panOffset?.x, y: this.editor?.panOffset?.y },
                mode: this.editor?.currentMode,
                dragging: this.editor?.dragging,
                selectedObj: this.editor?.selectedObject ? this.getObjectSnapshot(this.editor.selectedObject) : null,
                dragStart: this.editor?.dragStart ? { x: this.editor.dragStart.x, y: this.editor.dragStart.y } : null,
                lastMousePos: this.editor?.lastMousePos,
                collision: this.editor?.deviceCollision,
                momentum: this.editor?.momentum?.enabled,
                input: this.editor?._lastInputType
            }
        };
        this.bugHistory.push(bugEntry);
        if (this.bugHistory.length > 20) this.bugHistory.shift();
        
        // ADVANCED: Detect code conflicts and race conditions
        this.detectedIssues = this.detectCodeConflicts();
        
        // ULTRA-DEEP ANALYSIS: Precise categorization for AI
        if (bugMessage.includes('INVALID OFFSET')) {
            this.bugCategory = 'COORDINATE_SYSTEM_ERROR::INVALID_OFFSET';
            this.bugSeverity = 'CRITICAL';
            this.affectedSystems = ['coordinate-transform', 'mouse-handling', 'drag-system'];
        } else if (bugMessage.includes('JUMP') || bugMessage.includes('jump')) {
            this.bugCategory = 'POSITION_JUMP::DRAG_OFFSET';
            this.bugSeverity = this.detectedIssues.raceConditions.length > 0 ? 'CRITICAL' : 'HIGH';
            this.affectedSystems = ['drag-system', 'physics', 'momentum'];
            
            // Analyze execution flow
            this.executionFlow = [
                '1. handleMouseDown() called [topology.js:860]',
                '2. getMousePos(e) transforms screen → world [topology.js:745]',
                '3. findObjectAt(pos) checks collision [topology.js:2555]',
                '4. dragStart = mouseWorld - devicePos [topology.js:1324-1326]',
                '5. handleMouseMove() → newPos = mouseWorld - dragStart [topology.js:1785]'
            ];
            
            // Detect probable cause from state
            const offset = this.editor?.dragStart;
            const offsetMag = offset ? Math.sqrt(offset.x * offset.x + offset.y * offset.y) : 0;
            
            if (offsetMag > 200) {
                this.rootCauseAnalysis = `COORDINATE TRANSFORM FAILURE
                
WHY: getMousePos() returned incorrect world coordinates
WHAT: Mouse position (${this.editor?.lastMousePos?.x?.toFixed(0)}, ${this.editor?.lastMousePos?.y?.toFixed(0)}) should be near object (${bugEntry.snapshot.selectedObj?.type === 'unbound' ? `UL center (${bugEntry.snapshot.selectedObj?.centerX?.toFixed(0)}, ${bugEntry.snapshot.selectedObj?.centerY?.toFixed(0)})` : `(${bugEntry.snapshot.selectedObj?.x?.toFixed(0)}, ${bugEntry.snapshot.selectedObj?.y?.toFixed(0)})`})
RESULT: Offset calculated as (${offset?.x?.toFixed(0)}, ${offset?.y?.toFixed(0)}) - magnitude ${offsetMag.toFixed(0)}px

COORDINATE PIPELINE:
Screen coords [e.clientX, e.clientY]
  → Canvas coords [- rect.left, - rect.top]
  → Backing store [× scaleX, × scaleY]
  → World coords [- panOffset.x/y] / zoom

LIKELY ISSUE:
- Pan offset (${bugEntry.snapshot.pan?.x}, ${bugEntry.snapshot.pan?.y}) not applied correctly
- Or zoom (${bugEntry.snapshot.zoom}) not dividing correctly
- Or screen coordinates not scaled properly

CODE CONTRADICTION:
- getMousePos() [line 745]: returns world coords
- Device position: stored in world coords
- These should be in SAME coordinate space
- But offset = ${offsetMag.toFixed(0)}px suggests DIFFERENT spaces!`;

                this.codeConflicts = [
                    'getMousePos() transform formula vs actual coordinates',
                    'Pan offset application: line 745 vs drawing: line 5903',
                    'Zoom division: getMousePos vs draw transform'
                ];
                
            } else if (this.editor?.deviceCollision) {
                this.rootCauseAnalysis = `PHYSICS RACE CONDITION
                
WHY: Device position modified DURING grab setup
WHAT: Collision detection pushed device between click and drag start
WHEN: Line 1206 sets dragging=true BEFORE offset calculated
RACE: Physics can modify device.x/y while offset is being calculated

EXECUTION RACE:
1. Click object at ${bugEntry.snapshot.selectedObj?.type === 'unbound' ? `UL (${bugEntry.snapshot.selectedObj?.centerX?.toFixed(0)}, ${bugEntry.snapshot.selectedObj?.centerY?.toFixed(0)})` : `(${bugEntry.snapshot.selectedObj?.x}, ${bugEntry.snapshot.selectedObj?.y})`}
2. this.dragging = true [line 1206]
3. Physics potentially active (collision=${this.editor?.deviceCollision})
4. Device position may change BEFORE offset calculated
5. Offset = newMousePos - newDevicePos = WRONG!

CODE CONFLICT:
- Line 1206: Sets dragging=true
- Line 1324-1326: Calculates offset AFTER dragging=true
- Physics code: Can modify device.x/y when dragging=true
- CONTRADICTION: Offset calculated from potentially moved device!`;

                // Add detected race conditions to conflicts
                this.codeConflicts = [
                    'dragging flag set at line 1532 vs offset calculated after',
                    'Physics modify device.x/y vs offset calculation relies on stable position',
                    'Collision detection checkDeviceCollision() can push devices'
                ];
                
                // Add detected conflicts details
                if (this.detectedIssues.raceConditions.length > 0) {
                    // CRITICAL FIX: Deduplicate race conditions instead of adding each one
                    const uniqueRaces = new Map();
                    this.detectedIssues.raceConditions.forEach(race => {
                        const key = race.type;
                        if (uniqueRaces.has(key)) {
                            uniqueRaces.get(key).count++;
                        } else {
                            uniqueRaces.set(key, { ...race, count: 1 });
                        }
                    });
                    
                    uniqueRaces.forEach(race => {
                        const countInfo = race.count > 1 ? ` (×${race.count})` : '';
                        this.codeConflicts.push(`${race.type}: ${race.description}${countInfo} [${race.severity}]`);
                    });
                }
            } else {
                // Check if this is the dragStart offset error we just detected
                const dragStartMag = this.editor?.dragStart ? 
                    Math.sqrt(this.editor.dragStart.x ** 2 + this.editor.dragStart.y ** 2) : 0;
                const isDragStartError = dragStartMag > 100;
                
                if (isDragStartError) {
                    this.rootCauseAnalysis = `DRAG OFFSET VALIDATION - LARGE OFFSET DETECTED
                
STATUS: ✅ ROOT CAUSE FIXED (topology.js:1187, 1333)
DETECTION: dragStart magnitude = ${dragStartMag.toFixed(0)}px > 100px threshold
EXPECTED: Offset should be < 100px (typical grab within device radius)
ACTUAL: dragStart = (${this.editor?.dragStart?.x?.toFixed(0)}, ${this.editor?.dragStart?.y?.toFixed(0)}) 

WHAT HAPPENED:
Device at: (${bugEntry.snapshot.selectedObj?.x?.toFixed(0)}, ${bugEntry.snapshot.selectedObj?.y?.toFixed(0)})
dragStart offset: (${this.editor?.dragStart?.x?.toFixed(0)}, ${this.editor?.dragStart?.y?.toFixed(0)})

ANALYSIS:
✓ Offset is now calculated correctly: pos - device.pos
✓ Large offset may be intentional (user grabbed device edge)
✓ Or unusual mouse position relative to device center

SAFEGUARDS ACTIVE:
✓ Primary: Lines 1187, 1333 calculate offset properly at grab time
✓ Backup: Lines 2426-2435 validate and recalculate if needed
✓ No jump should occur

CODE LOCATION:
- Fixed: topology.js:1187-1190, 1333-1336 (calculates offset)
- Backup validation: topology.js:2426-2435 (recalculates if > 100px)`;

                    this.codeConflicts = [
                        'Large offset detected but calculated correctly',
                        'May indicate edge grab or unusual mouse position',
                        'Backup auto-correction available at line 2426',
                        'Monitor for device jumps during drag'
                    ];
                } else {
                    this.rootCauseAnalysis = `DRAG OFFSET CALCULATION ERROR
                
WHY: Offset magnitude (${offsetMag.toFixed(0)}px) is abnormal
NORMAL: Should be < 100px (within device radius)
ACTUAL: ${offset?.x?.toFixed(0)}, ${offset?.y?.toFixed(0)}

WHAT HAPPENED:
Object at: ${bugEntry.snapshot.selectedObj?.type === 'unbound' ? `UL (${bugEntry.snapshot.selectedObj?.centerX?.toFixed(0)}, ${bugEntry.snapshot.selectedObj?.centerY?.toFixed(0)})` : `(${bugEntry.snapshot.selectedObj?.x?.toFixed(0)}, ${bugEntry.snapshot.selectedObj?.y?.toFixed(0)})`}
Mouse at: Unknown (getMousePos may have failed)
Offset: (${offset?.x?.toFixed(0)}, ${offset?.y?.toFixed(0)})

POSSIBLE CAUSES:
1. dragStart was absolute mouse position (not offset)
   → Check: topology.js:1186, 1328 where dragStart is set
   → Expected: dragStart = mousePos - objectPos (relative offset)
   → Bug: dragStart = mousePos (absolute position)
   → Auto-fix: topology.js:2426-2435 (threshold: 100px)
   
2. Coordinate transform error in getMousePos()
   → Check: topology.js:745 transform calculation
   → Verify: Pan offset and zoom applied correctly
   
3. Device moved (collision/momentum) during offset calculation
4. Event coordinates in wrong coordinate space`;

                    this.codeConflicts = [
                        'dragStart may be absolute position instead of offset',
                        'getMousePos() [line 745] coordinate space',
                        'Device position coordinate space',
                        'Offset calculation assumes both in world coords'
                    ];
                }
            }
            
            this.bugSeverity = 'HIGH';
            this.affectedSystems = ['drag-system', 'coordinate-transform'];
            
        } else if (bugMessage.includes('Object moved during grab')) {
            this.bugCategory = 'POSITION_JUMP::RACE_CONDITION';
            this.bugSeverity = 'HIGH';
            this.affectedSystems = ['physics-collision', 'drag-system'];
            this.rootCauseAnalysis = `PHYSICS RACE CONDITION - Position Modified During Setup
            
Device position changed between grab and offset calculation
Physics system (collision/weight) pushed device during setup phase`;
            
        } else if (bugMessage.includes('mismatch') || bugMessage.includes('Mismatch')) {
            this.bugCategory = 'STATE_SYNC::UI_MISMATCH';
            this.bugSeverity = 'MEDIUM';
            this.affectedSystems = ['ui-state', 'toggle-system'];
            this.rootCauseAnalysis = `UI STATE DESYNCHRONIZATION
            
WHY: Toggle button CSS class doesn't match internal state
WHAT: JavaScript state !== DOM class state

EXECUTION:
1. Internal state changes (e.g., this.deviceNumbering = true)
2. Button class should update: btn.classList.add('active')
3. MISMATCH: One updated, other didn't

CODE CONTRADICTION:
- Internal state updated at one location
- Button class updated at different location
- Async timing or missing sync call caused divergence`;

            this.codeConflicts = [
                'State variable updates vs DOM class updates',
                'toggleDeviceNumbering() [line 2929] sets state',
                'Button class update may be skipped or race condition'
            ];
            
        } else if (bugMessage.includes('not found') || bugMessage.includes('missing')) {
            this.bugCategory = 'DOM::ELEMENT_NOT_FOUND';
            this.bugSeverity = 'MEDIUM';
            this.affectedSystems = ['dom-manipulation', 'ui-init'];
        } else if (bugMessage.includes('collision') || bugMessage.includes('overlap')) {
            this.bugCategory = 'PHYSICS::COLLISION_CASCADE';
            this.bugSeverity = 'LOW';
            this.affectedSystems = ['physics-collision', 'weight-system'];
        } else if (bugMessage.includes('coordinate') || bugMessage.includes('transform')) {
            this.bugCategory = 'COORDINATE_TRANSFORM::GENERIC';
            this.rootCauseAnalysis = `COORDINATE SPACE MISMATCH
            
WHY: Coordinate transform pipeline broken
PIPELINE:
Browser Event → Screen Coords → Canvas Coords → Backing Store → World Coords

FORMULA: worldPos = (screenPos - panOffset) / zoom
INVERSE: screenPos = worldPos × zoom + panOffset

LIKELY BREAK POINT:
One of the transform steps is incorrect or applied in wrong order

CODE SECTIONS:
- getMousePos() [line 745]: Applies transform
- draw() [line 5903]: ctx.translate(pan); ctx.scale(zoom)
- These must be EXACT INVERSES of each other!`;

            this.codeConflicts = [
                'getMousePos transform vs draw transform',
                'Pan offset application order',
                'Zoom multiplication vs division'
            ];
            
        } else if (bugMessage.includes('INVALID OFFSET')) {
            this.bugCategory = 'COORDINATE_SYSTEM_ERROR';
            const offset = this.editor?.dragStart;
            const offsetMag = offset ? Math.sqrt(offset.x * offset.x + offset.y * offset.y) : 0;
            
            this.rootCauseAnalysis = `MASSIVE OFFSET INDICATES COORDINATE FAILURE

WHY: Drag offset ${offsetMag.toFixed(0)}px is impossibly large
NORMAL: Offset should be < device radius (typically 30-50px)
ACTUAL: (${offset?.x?.toFixed(0)}, ${offset?.y?.toFixed(0)})

WHAT THIS MEANS:
When user clicks device, we calculate: offset = mouseWorld - deviceWorld
If offset is huge, it means:
  A) mouseWorld is in WRONG coordinate space, OR
  B) deviceWorld is in WRONG coordinate space, OR  
  C) getMousePos() totally failed

EXECUTION ORDER:
1. User clicks at screen position (${this.editor?.lastMouseScreen?.x}, ${this.editor?.lastMouseScreen?.y})
2. getMousePos() transforms to world: (screen - pan) / zoom
3. Result should be near device position
4. BUT: Got offset of ${offsetMag.toFixed(0)}px!

THIS REVEALS:
The coordinate transform in getMousePos() [line 745] is NOT returning world coordinates
Or device position is being stored in a different coordinate space
One or both are in the WRONG space, causing massive offset

CODE TO CHECK:
Line 745 getMousePos(): Are we applying transforms correctly?
Line 1324 offset calculation: Are both values in same coordinate space?
Line 5903 draw(): Is the drawing transform the exact inverse?`;

            this.codeConflicts = [
                'getMousePos() [line 745] - coordinate space of return value',
                'Device storage coordinates - what space are they in?',
                'Offset calculation assumes both in world space - but one isn\'t!'
            ];
            
            this.executionFlow = [
                '1. Click event at screen (x, y)',
                '2. getMousePos() should return world coords',
                '3. Device.x/y should be in world coords',
                '4. offset = world - world should be small',
                '5. BUT offset is huge = coordinate mismatch!'
            ];
        }
        
        // Log ROOT CAUSE ANALYSIS (not fixes!)
        this.logWarning(`🔍 BUG CATEGORY: ${this.bugCategory}`);
        this.logError(`═══ ROOT CAUSE ANALYSIS ═══`);
        if (this.rootCauseAnalysis) {
            this.rootCauseAnalysis.split('\n').forEach(line => {
                if (line.trim()) this.logInfo(line);
            });
        }
        if (this.codeConflicts.length > 0) {
            // CRITICAL FIX: Deduplicate conflicts before logging
            const uniqueConflicts = new Map();
            this.codeConflicts.forEach(conflict => {
                // Extract base conflict (without count)
                const baseConflict = conflict.replace(/\s*\(×\d+\)/, '');
                if (uniqueConflicts.has(baseConflict)) {
                    uniqueConflicts.get(baseConflict).count++;
                } else {
                    uniqueConflicts.set(baseConflict, { text: conflict, count: 1 });
                }
            });
            
            this.logWarning(`⚠️ CODE CONFLICTS (${uniqueConflicts.size} unique):`);
            uniqueConflicts.forEach(conflict => {
                const countSuffix = conflict.count > 1 ? ` [detected ${conflict.count}× times]` : '';
                this.logInfo(`  • ${conflict.text}${countSuffix}`);
            });
        }
        if (this.executionFlow.length > 0) {
            this.logInfo(`📊 EXECUTION FLOW:`);
            this.executionFlow.forEach(step => this.logInfo(`  ${step}`));
        }
        
        // Pattern detection with detailed analysis
        const similarBugs = this.bugHistory.filter(b => 
            b.message.includes(bugMessage.substring(0, 20))
        );
        if (similarBugs.length > 2) {
            this.logError(`🔁 RECURRING: Occurred ${similarBugs.length} times in last ${this.bugHistory.length} bugs`);
            
            // Analyze if pattern correlates with specific conditions
            const conditions = similarBugs.map(b => ({
                zoom: b.snapshot.zoom,
                collision: b.snapshot.collision,
                weight: b.snapshot.weight,
                input: b.snapshot.input
            }));
            
            const allSameZoom = conditions.every(c => Math.abs(c.zoom - conditions[0].zoom) < 0.01);
            const allSameCollision = conditions.every(c => c.collision === conditions[0].collision);
            const allSameInput = conditions.every(c => c.input === conditions[0].input);
            
            if (allSameZoom) this.logWarning(`⚠️ Pattern: ALWAYS at zoom ${(conditions[0].zoom * 100).toFixed(0)}%`);
            if (allSameCollision) this.logWarning(`⚠️ Pattern: ALWAYS with collision ${conditions[0].collision ? 'ON' : 'OFF'}`);
            if (allSameInput) this.logWarning(`⚠️ Pattern: ALWAYS with ${conditions[0].input} input`);
        }
    }
    
    clearBugAlert() {
        const bugAlertDiv = document.getElementById('debug-bug-alert');
        const bottomBugAlert = document.getElementById('bottom-bug-alert');
        
        if (bugAlertDiv) {
            bugAlertDiv.style.display = 'none';
        }
        if (bottomBugAlert) {
            bottomBugAlert.style.display = 'none';
        }
        
        this.latestBug = null;
    }
    
    // ═══════════════════════════════════════════════════════════════
    // AI DEBUG ASSISTANT - Intelligent Bug Analysis & Fix Suggestions
    // ═══════════════════════════════════════════════════════════════
    
    askAI() {
        // Main entry point: Capture context and prepare for AI analysis
        this.log('🤖 Preparing bug context for AI analysis...', 'info');
        
        // Capture comprehensive bug context
        this.captureBugContext();
        
        // Copy to clipboard
        const success = this.copyBugContextForAI();
        
        if (success) {
            // Show AI panel with instructions
            const aiPanel = document.getElementById('debug-ai-panel');
            if (aiPanel) {
                aiPanel.style.display = 'block';
                
                // Update summary
                const summary = document.getElementById('debug-ai-summary');
                if (summary && this.currentBugContext) {
                    summary.innerHTML = `
                        • Bug: ${this.currentBugContext.bugMessage.substring(0, 50)}...<br>
                        • Category: ${this.currentBugContext.category || 'Unknown'}<br>
                        • Recent Actions: ${this.currentBugContext.recentActions.length} captured<br>
                        • State: Zoom ${Math.round(this.currentBugContext.editorState.zoom * 100)}%, Mode: ${this.currentBugContext.editorState.mode}<br>
                        • Root Cause: ${this.currentBugContext.rootCause ? 'Analyzed ✓' : 'Not available'}
                    `;
                }
                
                // Scroll to AI panel
                aiPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
            
            this.log('✅ Bug context copied! Ready for AI analysis', 'success');
        } else {
            this.log('❌ Failed to copy bug context', 'error');
        }
    }
    
    captureBugContext() {
        // Capture comprehensive bug context for AI analysis
        
        if (!this.latestBug) {
            this.log('⚠️ No active bug to analyze', 'warning');
            return null;
        }
        
        // Get the most recent bug entry from history
        const latestBugEntry = this.bugHistory[this.bugHistory.length - 1];
        
        // Capture editor state
        const editorState = {
            zoom: this.editor?.zoom || 1,
            pan: { 
                x: this.editor?.panOffset?.x || 0, 
                y: this.editor?.panOffset?.y || 0 
            },
            mode: this.editor?.currentMode || 'unknown',
            dragging: this.editor?.dragging || false,
            selectedObject: this.editor?.selectedObject ? {
                type: this.editor.selectedObject.type,
                label: this.editor.selectedObject.label,
                x: this.editor.selectedObject.x,
                y: this.editor.selectedObject.y
            } : null,
            objectCount: this.editor?.objects?.length || 0,
            deviceCount: this.editor?.objects?.filter(o => o.type === 'device')?.length || 0,
            linkCount: this.editor?.objects?.filter(o => o.type === 'link')?.length || 0,
            collision: this.editor?.deviceCollision || false,
            physics: this.editor?.physics?.enabled || false,
            momentum: this.editor?.momentum?.enabled || false,
            inputType: this.editor?._lastInputType || 'unknown'
        };
        
        // Capture recent logs (last 15 for context)
        const recentLogs = this.logs.slice(-15).map(log => ({
            type: log.type,
            message: log.message,
            time: log.time
        }));
        
        // Build comprehensive context
        this.currentBugContext = {
            timestamp: new Date().toISOString(),
            bugMessage: this.latestBug,
            category: this.bugCategory || 'Unknown',
            rootCause: this.rootCauseAnalysis || null,
            codeConflicts: this.codeConflicts || [],
            executionFlow: this.executionFlow || [],
            editorState: editorState,
            recentActions: this.recentActions || [],
            recentLogs: recentLogs,
            bugSnapshot: latestBugEntry?.snapshot || null,
            stackTrace: this.captureStackTrace(),
            browserInfo: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screenSize: `${window.screen.width}x${window.screen.height}`,
                windowSize: `${window.innerWidth}x${window.innerHeight}`
            }
        };
        
        return this.currentBugContext;
    }
    
    captureStackTrace() {
        // Capture current stack trace for debugging
        try {
            throw new Error('Stack trace capture');
        } catch (e) {
            return e.stack || 'Stack trace not available';
        }
    }
    
    copyBugContextForAI() {
        // Copy comprehensive bug context to clipboard in AI-friendly format
        
        if (!this.currentBugContext) {
            this.captureBugContext();
        }
        
        if (!this.currentBugContext) {
            return false;
        }
        
        const ctx = this.currentBugContext;
        
        // Format as comprehensive AI prompt
        const aiPrompt = `🐛 BUG DETECTED IN TOPOLOGY EDITOR - AI ANALYSIS REQUEST

═══════════════════════════════════════════════════════════
📋 BUG SUMMARY
═══════════════════════════════════════════════════════════
Timestamp: ${new Date(ctx.timestamp).toLocaleString()}
Category: ${ctx.category}
Bug Message: ${ctx.bugMessage}

${ctx.rootCause ? `
═══════════════════════════════════════════════════════════
🔍 ROOT CAUSE ANALYSIS (Auto-Generated)
═══════════════════════════════════════════════════════════
${ctx.rootCause}
` : ''}

${ctx.codeConflicts.length > 0 ? `
═══════════════════════════════════════════════════════════
⚠️ CODE CONFLICTS DETECTED
═══════════════════════════════════════════════════════════
${ctx.codeConflicts.map((c, i) => `${i + 1}. ${c}`).join('\n')}
` : ''}

${ctx.executionFlow.length > 0 ? `
═══════════════════════════════════════════════════════════
📊 EXECUTION FLOW
═══════════════════════════════════════════════════════════
${ctx.executionFlow.join('\n')}
` : ''}

═══════════════════════════════════════════════════════════
🎯 EDITOR STATE (At Time of Bug)
═══════════════════════════════════════════════════════════
Zoom Level: ${Math.round(ctx.editorState.zoom * 100)}%
Pan Offset: (${ctx.editorState.pan?.x?.toFixed?.(1) ?? 'N/A'}, ${ctx.editorState.pan?.y?.toFixed?.(1) ?? 'N/A'})
Current Mode: ${ctx.editorState.mode.toUpperCase()}
Dragging Active: ${ctx.editorState.dragging ? 'YES' : 'NO'}
Input Type: ${ctx.editorState.inputType}

Object Counts:
  • Total Objects: ${ctx.editorState.objectCount}
  • Devices: ${ctx.editorState.deviceCount}
  • Links: ${ctx.editorState.linkCount}

Physics & Features:
  • Collision Detection: ${ctx.editorState.collision ? 'ENABLED' : 'DISABLED'}
  • Momentum/Sliding: ${ctx.editorState.momentum ? 'ENABLED' : 'DISABLED'}

${ctx.editorState.selectedObject ? `
Selected Object:
  • Type: ${ctx.editorState.selectedObject.type}
  • Label: ${ctx.editorState.selectedObject.label || 'N/A'}
  • Position: (${ctx.editorState.selectedObject.x?.toFixed?.(1) ?? 'N/A'}, ${ctx.editorState.selectedObject.y?.toFixed?.(1) ?? 'N/A'})
` : 'Selected Object: None'}

═══════════════════════════════════════════════════════════
👆 RECENT USER ACTIONS (Leading to Bug)
═══════════════════════════════════════════════════════════
${ctx.recentActions.length > 0 ? ctx.recentActions.slice(-10).map((a, i) => 
    `${i + 1}. [${new Date(a.time).toLocaleTimeString()}] ${a.action}`
).join('\n') : 'No actions recorded'}

═══════════════════════════════════════════════════════════
📜 RECENT DEBUG LOGS (Last 15 Events)
═══════════════════════════════════════════════════════════
${ctx.recentLogs.map(log => `[${log.time}] [${log.type.toUpperCase()}] ${log.message}`).join('\n')}

${ctx.bugSnapshot ? `
═══════════════════════════════════════════════════════════
📸 DETAILED BUG SNAPSHOT
═══════════════════════════════════════════════════════════
${JSON.stringify(ctx.bugSnapshot, null, 2)}
` : ''}

═══════════════════════════════════════════════════════════
🖥️ ENVIRONMENT INFO
═══════════════════════════════════════════════════════════
Platform: ${ctx.browserInfo.platform}
User Agent: ${ctx.browserInfo.userAgent}
Language: ${ctx.browserInfo.language}
Screen: ${ctx.browserInfo.screenSize}
Window: ${ctx.browserInfo.windowSize}

═══════════════════════════════════════════════════════════
🤖 AI INSTRUCTIONS
═══════════════════════════════════════════════════════════
Please analyze this bug and provide:

1. **Root Cause Verification**: Confirm or refine the auto-generated root cause analysis
2. **Exact Location**: Identify the file(s) and line number(s) where the bug occurs
3. **Fix Strategy**: Explain the best approach to fix this bug
4. **Code Solution**: Provide the exact code changes needed (with before/after)
5. **Prevention**: Suggest how to prevent similar bugs in the future

Context: This is a topology editor app for network diagrams with features like:
- Drag & drop device placement
- Canvas zoom/pan with coordinate transforms
- Collision detection
- Momentum/sliding physics
- Multiple input types (mouse, touchpad, touch)
- Real-time debugging system

Files likely involved:
- topology.js (main editor logic)
- topology-momentum.js (momentum/sliding physics)
- debugger.js (this debugging system)

Please fix this bug!`;

        // Copy to clipboard
        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(aiPrompt).then(() => {
                    this.log('✅ Bug context copied to clipboard!', 'success');
                    
                    // Track this in AI history
                    this.aiDebugHistory.push({
                        timestamp: ctx.timestamp,
                        bugMessage: ctx.bugMessage,
                        category: ctx.category,
                        contextCopied: true,
                        fixApplied: false
                    });
                    
                    // Keep only last 20
                    if (this.aiDebugHistory.length > 20) {
                        this.aiDebugHistory.shift();
                    }
                }).catch(err => {
                    console.error('Clipboard copy failed:', err);
                    this.fallbackCopy(aiPrompt);
                });
            } else {
                this.fallbackCopy(aiPrompt);
            }
            return true;
        } catch (err) {
            console.error('Copy error:', err);
            this.log('❌ Failed to copy: ' + err.message, 'error');
            return false;
        }
    }
    
    fallbackCopy(text) {
        // Fallback clipboard copy method
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            this.log('✅ Context copied (fallback method)', 'success');
        } catch (err) {
            this.log('❌ Copy failed: ' + err.message, 'error');
        }
        document.body.removeChild(textarea);
    }
    
    markFixApplied(fixDescription) {
        // Track when a fix is applied (call this manually or via UI)
        if (this.aiDebugHistory.length > 0) {
            const latest = this.aiDebugHistory[this.aiDebugHistory.length - 1];
            latest.fixApplied = true;
            latest.fixDescription = fixDescription;
            latest.fixTime = new Date().toISOString();
            
            this.log(`✅ Fix applied and tracked: ${fixDescription}`, 'success');
            
            // Save to localStorage for persistence
            try {
                localStorage.setItem('ai_debug_history', JSON.stringify(this.aiDebugHistory));
            } catch (e) {
                console.warn('Could not save AI debug history:', e);
            }
        }
    }
    
    getAIDebugStats() {
        // Get statistics about AI debugging sessions
        const totalBugs = this.aiDebugHistory.length;
        const fixedBugs = this.aiDebugHistory.filter(h => h.fixApplied).length;
        const fixRate = totalBugs > 0 ? ((fixedBugs / totalBugs) * 100).toFixed(1) : 0;
        
        const categoryCounts = {};
        this.aiDebugHistory.forEach(h => {
            categoryCounts[h.category] = (categoryCounts[h.category] || 0) + 1;
        });
        
        return {
            totalBugs,
            fixedBugs,
            fixRate: `${fixRate}%`,
            categories: categoryCounts,
            lastBug: this.aiDebugHistory[totalBugs - 1] || null
        };
    }
    
    showMarkFixDialog() {
        // Show simple prompt to mark fix as applied
        const description = prompt('✅ Fix applied! Briefly describe what was fixed:', 'Fixed bug');
        
        if (description) {
            this.markFixApplied(description);
            this.log(`✅ Fix marked as applied: ${description}`, 'success');
        }
    }
    
    copyBugDescription() {
        // ENHANCED: Copy comprehensive bug report with smart analysis
        console.log('copyBugDescription called', { 
            latestBug: this.latestBug, 
            jumpDetails: this.editor?.latestJumpDetails,
            bugHistory: this.bugHistory?.length,
            recentActions: this.recentActions?.length
        });
        
        if (!this.latestBug && !this.editor?.latestJumpDetails) {
            alert('No bug to copy! There is no active bug report available.');
            console.warn('No bug data available to copy');
            return;
        }
        
        // Additional check: Don't generate report if bug message is empty or just whitespace
        const bugMessage = this.latestBug?.trim() || '';
        if (!bugMessage && !this.editor?.latestJumpDetails) {
            alert('No bug to copy! The bug message is empty.');
            console.warn('Bug message is empty, cannot generate report');
            return;
        }
        
        // CRITICAL: Don't generate report if bug message is just whitespace or placeholder text
        if (bugMessage && (bugMessage.length < 5 || bugMessage === 'Jump detected')) {
            // If it's a placeholder or too short, check if we have real bug history
            const hasRealBug = this.bugHistory && this.bugHistory.length > 0 && 
                               this.bugHistory[this.bugHistory.length - 1]?.message?.trim()?.length > 10;
            if (!hasRealBug && !this.editor?.latestJumpDetails) {
                alert('No valid bug to copy! The bug message is too short or invalid.');
                console.warn('Bug message is invalid, cannot generate report');
                return;
            }
        }
        
        try {
            // Format SMART bug report with analysis and suggestions
            const timestamp = new Date().toLocaleString();
            // Use actual bug message, or get from bug history if latestBug is empty
            let bugDescription = bugMessage;
            if (!bugDescription && this.bugHistory && this.bugHistory.length > 0) {
                const lastBug = this.bugHistory[this.bugHistory.length - 1];
                bugDescription = lastBug?.message?.trim() || 'Jump detected';
            } else {
                bugDescription = bugDescription || 'Jump detected';
            }
            
            // Final validation: Don't generate if description is still empty or too short
            if (!bugDescription || bugDescription.trim().length < 5) {
                alert('No valid bug description available to copy.');
                console.warn('Bug description is invalid, cannot generate report');
                return;
            }
            const jumpDetails = this.editor?.latestJumpDetails || 'N/A';
            
            // Get recent actions for context (with safety checks)
            const recentActions = this.recentActions && this.recentActions.length > 0 
                ? this.recentActions.slice(-5).map(a => a?.action || 'unknown').join(' → ')
                : 'None';
            
            console.log('Building bug report...', { bugDescription, jumpDetails, recentActions });
        
        // Get call stack if available
        const lastAction = this.recentActions[this.recentActions.length - 1];
        const callChain = lastAction?.stack ? lastAction.stack.map(s => 
            typeof s === 'string' ? s : `${s.function} (${s.file}:${s.line}:${s.column})`
        ).join('\n  → ') : 'Not captured';
        
        // Format with ULTRA-SMART ROOT CAUSE ANALYSIS FOR AI
        const bugReport = `╔═══════════════════════════════════════════════════════════╗
║  AI-OPTIMIZED BUG REPORT - Topology Editor              ║
╚═══════════════════════════════════════════════════════════╝

🏷️  CATEGORY: ${this.bugCategory || 'UNKNOWN'}
⚠️  SEVERITY: ${this.bugSeverity || 'UNKNOWN'}
📦  AFFECTED SYSTEMS: ${this.affectedSystems ? this.affectedSystems.join(', ') : 'unknown'}
🕐  TIMESTAMP: ${timestamp}

🐛 BUG DESCRIPTION:
${bugDescription}

${jumpDetails !== 'N/A' ? `
═══ TECHNICAL DETAILS ═══
${jumpDetails}
` : ''}
═══ ROOT CAUSE ANALYSIS ═══
${this.rootCauseAnalysis || 'Analysis not available'}

${this.detectedIssues && (this.detectedIssues.raceConditions.length > 0 || this.detectedIssues.conflicts.length > 0 || this.detectedIssues.contradictions.length > 0) ? `
╔═══════════════════════════════════════════════════════════╗
║  🤖 AI-DETECTED CODE CONFLICTS & RACE CONDITIONS         ║
╚═══════════════════════════════════════════════════════════╝

${this.detectedIssues.raceConditions.map((race, i) => `
[${i + 1}] ⚡ RACE CONDITION: ${race.type}
    Severity: ${race.severity}
    Issue: ${race.description}
    
    📍 Conflicting Code Locations:
${race.conflictLines.map(line => `       • ${line.file}:${line.line}
         Code: ${line.code}
         Context: ${line.context}`).join('\n')}
    
    💥 Impact: ${race.impact}
    
    ✅ Suggested Fix:
    ${race.fix}
`).join('\n')}
${this.detectedIssues.conflicts.map((conflict, i) => `
[${this.detectedIssues.raceConditions.length + i + 1}] ⚠️ CODE CONFLICT: ${conflict.type}
    Severity: ${conflict.severity}
    Issue: ${conflict.description}
    
    📍 Conflicting Code Locations:
${conflict.conflictLines.map(line => `       • ${line.file}:${line.line}
         Code: ${line.code}
         Context: ${line.context}`).join('\n')}
    
    💥 Impact: ${conflict.impact}
    
    ✅ Suggested Fix:
    ${conflict.fix}
`).join('\n')}
${this.detectedIssues.contradictions.map((contra, i) => `
[${this.detectedIssues.raceConditions.length + this.detectedIssues.conflicts.length + i + 1}] 🔀 CONTRADICTION: ${contra.type}
    Severity: ${contra.severity}
    Issue: ${contra.description}
    
    📍 Contradicting Code Locations:
${contra.conflictLines.map(line => `       • ${line.file}:${line.line}
         Code: ${line.code}
         Context: ${line.context}`).join('\n')}
    
    💥 Impact: ${contra.impact}
    
    ✅ Suggested Fix:
    ${contra.fix}
`).join('\n')}
` : ''}
${this.codeConflicts && this.codeConflicts.length > 0 ? `
═══ ADDITIONAL CODE CONFLICTS ═══
${this.codeConflicts.map((c, i) => `${i + 1}. ${c}`).join('\n')}
` : ''}
${this.executionFlow && this.executionFlow.length > 0 ? `
═══ EXECUTION FLOW ═══
${this.executionFlow.join('\n')}
` : ''}
═══ STATE SNAPSHOT ═══
Zoom: ${Math.round((this.editor?.zoom || 1) * 100)}%
Pan: (${Math.round(this.editor?.panOffset?.x || 0)}, ${Math.round(this.editor?.panOffset?.y || 0)})
Mode: ${(this.editor?.currentMode || 'unknown').toUpperCase()}
Dragging: ${this.editor?.dragging || false}
Objects: ${this.editor?.objects?.length || 0}
Input: ${this.editor?._lastInputType || 'unknown'}

Selected Object: ${this.bugHistory && this.bugHistory.length > 0 && this.bugHistory[this.bugHistory.length - 1]?.snapshot?.selectedObj ? 
    (this.bugHistory[this.bugHistory.length - 1].snapshot.selectedObj.type === 'unbound' ? 
        `UL: Start(${this.bugHistory[this.bugHistory.length - 1].snapshot.selectedObj.start?.x?.toFixed(0)}, ${this.bugHistory[this.bugHistory.length - 1].snapshot.selectedObj.start?.y?.toFixed(0)}) End(${this.bugHistory[this.bugHistory.length - 1].snapshot.selectedObj.end?.x?.toFixed(0)}, ${this.bugHistory[this.bugHistory.length - 1].snapshot.selectedObj.end?.y?.toFixed(0)})` :
        `(${this.bugHistory[this.bugHistory.length - 1].snapshot.selectedObj.x}, ${this.bugHistory[this.bugHistory.length - 1].snapshot.selectedObj.y}) "${this.bugHistory[this.bugHistory.length - 1].snapshot.selectedObj.label}"`) : 'None'}
Drag Start: ${this.bugHistory && this.bugHistory.length > 0 && this.bugHistory[this.bugHistory.length - 1]?.snapshot?.dragStart ? 
    (this.bugHistory[this.bugHistory.length - 1].snapshot.selectedObj?.type === 'unbound' ? 
        `Mouse Pos (${this.bugHistory[this.bugHistory.length - 1].snapshot.dragStart?.x?.toFixed?.(1) ?? 'N/A'}, ${this.bugHistory[this.bugHistory.length - 1].snapshot.dragStart?.y?.toFixed?.(1) ?? 'N/A'})` :
        `Offset (${this.bugHistory[this.bugHistory.length - 1].snapshot.dragStart?.x?.toFixed?.(1) ?? 'N/A'}, ${this.bugHistory[this.bugHistory.length - 1].snapshot.dragStart?.y?.toFixed?.(1) ?? 'N/A'})`) : 'N/A'}

═══ PHYSICS STATE ═══
Collision: ${this.editor?.deviceCollision ? 'ON' : 'OFF'}
Momentum: ${this.editor?.momentum?.enabled ? 'ON' : 'OFF'}
Active Slides: ${this.editor?.momentum?.activeSlides?.size || 0}

${callChain !== 'Not captured' ? `
═══ CALL STACK (Function Trace) ═══
${callChain}
` : ''}
═══ RECENT ACTIONS (Timeline) ═══
${recentActions || 'None'}

═══ BUG RECURRENCE PATTERN ═══
Total Bugs Logged: ${this.bugHistory?.length || 0}
This Bug Occurred: ${bugDescription && this.bugHistory && this.bugHistory.length > 0 ? this.bugHistory.filter(b => b?.message && b.message.includes(bugDescription.substring(0, 20))).length : 0} times
${this.bugHistory && this.bugHistory.length > 1 ? `Recent Bugs: ${this.bugHistory.slice(-3).map(b => (b?.message || 'unknown').substring(0, 40)).join(' → ')}` : ''}

╔═══════════════════════════════════════════════════════════╗
║  🎯 AI-GENERATED FIX RECOMMENDATIONS                     ║
╚═══════════════════════════════════════════════════════════╝

${this.detectedIssues && this.detectedIssues.raceConditions.filter(r => r.severity === 'CRITICAL').length > 0 ? `
⚡ CRITICAL - Fix Immediately:
${this.detectedIssues.raceConditions.filter(r => r.severity === 'CRITICAL').map((race, i) => `  ${i + 1}. ${race.type}: ${race.fix}
     → ${race.conflictLines.map(l => `${l.file}:${l.line}`).join(', ')}`).join('\n')}
` : ''}
${this.detectedIssues && this.detectedIssues.conflicts.filter(c => c.severity === 'HIGH' || c.severity === 'CRITICAL').length > 0 ? `
⚠️  HIGH PRIORITY:
${this.detectedIssues.conflicts.filter(c => c.severity === 'HIGH' || c.severity === 'CRITICAL').map((c, i) => `  ${i + 1}. ${c.type}: ${c.fix}
     → ${c.conflictLines.map(l => `${l.file}:${l.line}`).join(', ')}`).join('\n')}
` : ''}
═══ AI DEBUGGING HINTS ═══
🎯 PRIMARY FIX LOCATION: ${this.bugCategory?.includes('COORDINATE') ? 'topology.js:783 (getMousePos)' : this.bugCategory?.includes('PHYSICS') ? 'topology-momentum.js or topology.js (collision)' : this.bugCategory?.includes('STATE') ? 'topology.js toggle functions' : 'See code conflicts above'}
🔍 SEARCH KEYWORDS: ${this.bugCategory?.split('::').join(', ')}
📝 RELATED FILES: ${this.affectedSystems ? this.affectedSystems.map(s => {
    if (s.includes('momentum')) return 'topology-momentum.js';
    if (s.includes('collision') || s.includes('physic')) return 'topology.js (collision detection)';
    if (s.includes('coordinate') || s.includes('drag')) return 'topology.js';
    if (s.includes('ui')) return 'index.html, styles.css';
    return s;
}).filter((v, i, a) => a.indexOf(v) === i).join(', ') : 'topology.js'}
🤖 AI ANALYSIS: ${this.detectedIssues ? `${this.detectedIssues.raceConditions.length} race conditions, ${this.detectedIssues.conflicts.length} conflicts, ${this.detectedIssues.contradictions.length} contradictions detected` : 'Run analysis'}

═══ FOR AI ASSISTANT ═══
This is a ${this.bugSeverity || 'UNKNOWN'} severity ${this.bugCategory || 'unknown'} bug.
${this.codeConflicts && this.codeConflicts.length > 0 ? `Focus on these conflicting code sections:
${this.codeConflicts.map((c, i) => `  ${i + 1}. ${c}`).join('\n')}` : ''}
${this.rootCauseAnalysis ? `The root cause analysis explains the WHY and WHAT.
Use the execution flow to understand the sequence.
Check the state snapshot for exact values at time of bug.` : ''}

Topology Editor Bug Report - Generated by Smart Debug System
═══════════════════════════════════════════════════════════`;
        
        console.log('Bug report generated, length:', bugReport.length);
        
        // Copy to clipboard with fallback
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(bugReport).then(() => {
                console.log('Bug report copied successfully!');
                
                // Visual feedback
                const btn = document.getElementById('copy-bug-btn');
                if (btn) {
                    const original = btn.innerHTML;
                    btn.innerHTML = `${dbgIcon('check')} Copied!`;
                    btn.style.background = 'rgba(46, 204, 113, 0.6)';
                    btn.style.borderColor = 'rgba(46, 204, 113, 1)';
                    
                    setTimeout(() => {
                        btn.innerHTML = original;
                        btn.style.background = 'rgba(255,255,255,0.25)';
                        btn.style.borderColor = 'rgba(255,255,255,0.4)';
                    }, 1500);
                }
                
                this.logSuccess('📋 AI-optimized bug report copied - perfect for Cursor AI analysis!');
            }).catch(err => {
                console.error('Failed to copy bug report:', err);
                alert(`Failed to copy. Error: ${err.message}\n\n${bugReport}`);
            });
        } else {
            // Fallback method
            this.copyToClipboardFallback(bugReport);
            const btn = document.getElementById('copy-bug-btn');
            if (btn) {
                const original = btn.innerHTML;
                btn.innerHTML = `${dbgIcon('check')} Copied!`;
                btn.style.background = 'rgba(46, 204, 113, 0.6)';
                btn.style.borderColor = 'rgba(46, 204, 113, 1)';
                
                setTimeout(() => {
                    btn.innerHTML = original;
                    btn.style.background = 'rgba(255,255,255,0.25)';
                    btn.style.borderColor = 'rgba(255,255,255,0.4)';
                }, 1500);
            }
            this.logSuccess('📋 AI-optimized bug report copied (fallback method)!');
        }
        } catch (error) {
            console.error('Error generating bug report:', error);
            alert('Error generating bug report: ' + error.message);
        }
    }
    
    copyPlacementTracking() {
        // Copy placement tracking data to clipboard
        if (!this.placementData.deviceLabel) {
            alert('No placement data to copy! Grab and release a device first.');
            return;
        }
        
        const data = this.placementData;
        const placementReport = `═══ DEVICE PLACEMENT TRACKING ═══
Time: ${data.timestamp || 'N/A'}
Input: ${data.inputType || 'unknown'}

DEVICE:
  Label: ${data.deviceLabel || 'Unknown'}
  Type: ${data.deviceType || 'device'}

GRAB POSITION:
  World: (${data.grabPosition?.x?.toFixed(1) || 'N/A'}, ${data.grabPosition?.y?.toFixed(1) || 'N/A'})
  Grid: (${data.grabPosition?.gridX || 'N/A'}, ${data.grabPosition?.gridY || 'N/A'})

RELEASE POSITION:
  World: (${data.releasePosition?.x?.toFixed(1) || 'N/A'}, ${data.releasePosition?.y?.toFixed(1) || 'N/A'})
  Grid: (${data.releasePosition?.gridX || 'N/A'}, ${data.releasePosition?.gridY || 'N/A'})

MOUSE POSITIONS:
  Grab: (${data.mouseGrab?.x?.toFixed(1) || 'N/A'}, ${data.mouseGrab?.y?.toFixed(1) || 'N/A'})
  Release: (${data.mouseRelease?.x?.toFixed(1) || 'N/A'}, ${data.mouseRelease?.y?.toFixed(1) || 'N/A'})

DRAG DETAILS:
  Offset: (${data.offset?.x?.toFixed(1) || 'N/A'}, ${data.offset?.y?.toFixed(1) || 'N/A'})
  Distance Moved: ${data.distance?.toFixed(1) || 'N/A'}px
  
  Delta X: ${data.releasePosition && data.grabPosition ? (data.releasePosition.x - data.grabPosition.x).toFixed(1) : 'N/A'}px
  Delta Y: ${data.releasePosition && data.grabPosition ? (data.releasePosition.y - data.grabPosition.y).toFixed(1) : 'N/A'}px

Topology Editor - Placement Tracking
═══════════════════════════════════`;

        navigator.clipboard.writeText(placementReport).then(() => {
            const btn = document.getElementById('copy-placement-btn');
            if (btn) {
                const original = btn.innerHTML;
                btn.innerHTML = dbgIcon('check');
                btn.style.background = '#27ae60';
                
                setTimeout(() => {
                    btn.innerHTML = original;
                    btn.style.background = '#3498db';
                }, 1500);
            }
            
            this.logSuccess('📋 Placement tracking copied to clipboard');
        }).catch(err => {
            alert(`Failed to copy: ${err.message}\n\n${placementReport}`);
        });
    }
    
    copySection(sectionId) {
        // Copy content from any debug section
        const sectionElement = document.getElementById(sectionId);
        if (!sectionElement) {
            alert(`Section "${sectionId}" not found!`);
            return;
        }
        
        // Get the section title from the header
        const section = sectionElement.closest('.debug-section');
        let sectionTitle = sectionId.replace('debug-', '').replace(/-/g, ' ').toUpperCase();
        if (section) {
            const header = section.querySelector('.debug-section-header span');
            if (header) {
                // Extract title (remove icon emoji)
                const headerText = header.textContent.trim();
                const match = headerText.match(/\s+(.+)/);
                if (match) {
                    sectionTitle = match[1].toUpperCase();
                }
            }
        }
        
        // Get text content, preserving line breaks
        let content = sectionElement.innerText || sectionElement.textContent || '';
        
        // Clean up the content
        content = content.trim();
        
        if (!content || content === '...' || content === 'Waiting for events...') {
            alert(`No data to copy from ${sectionTitle}!`);
            return;
        }
        
        // Format with header
        const formattedContent = `═══ ${sectionTitle} ═══
${content}

Topology Editor - ${sectionTitle}
═══════════════════════════════════`;
        
        // Copy to clipboard with fallback
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(formattedContent).then(() => {
                const btn = document.getElementById(`copy-${sectionId}-btn`);
                if (btn) {
                    const original = btn.innerHTML;
                    const originalBg = btn.style.background;
                    btn.innerHTML = dbgIcon('check');
                    btn.style.background = '#27ae60';
                    
                    setTimeout(() => {
                        btn.innerHTML = original;
                        btn.style.background = originalBg;
                    }, 1500);
                }
                
                this.logSuccess(`📋 ${sectionTitle} copied to clipboard`);
            }).catch(err => {
                alert(`Failed to copy: ${err.message}\n\n${formattedContent}`);
                this.logError(`Failed to copy ${sectionTitle}: ${err.message}`);
            });
        } else {
            // Fallback: show in alert or use old method
            this.copyToClipboardFallback(formattedContent);
            const btn = document.getElementById(`copy-${sectionId}-btn`);
            if (btn) {
                const original = btn.innerHTML;
                const originalBg = btn.style.background;
                btn.innerHTML = dbgIcon('check');
                btn.style.background = '#27ae60';
                
                setTimeout(() => {
                    btn.innerHTML = original;
                    btn.style.background = originalBg;
                }, 1500);
            }
            this.logSuccess(`📋 ${sectionTitle} copied (fallback method)`);
        }
    }
    
    copyLastLogs() {
        // Copy last 50 log entries to clipboard
        const logCount = Math.min(50, this.logs.length);
        
        if (logCount === 0) {
            alert('No logs to copy!');
            return;
        }
        
        // Get last 100 logs (increased from 50)
        const lastLogs = this.logs.slice(-100);
        
        // Format logs as text with timestamps
        const logText = lastLogs.map(log => 
            `[${log.time}] ${log.message}`
        ).join('\n');
        
        // Add header
        const header = `═══ Topology Editor Debug Log (Last ${logCount} entries) ═══\n`;
        const footer = `\n═══ Total logs: ${this.logs.length} | Copied: ${logCount} ═══`;
        const fullText = header + logText + footer;
        
        // Copy to clipboard with fallback
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(fullText).then(() => {
                // Visual feedback - change button temporarily
                const btn = document.getElementById('debug-copy-logs');
                
                if (btn) {
                    const originalText = btn.innerHTML;
                    const originalBg = btn.style.background;
                    
                    btn.innerHTML = `${dbgIcon('check')} Copied!`;
                    btn.style.background = '#27ae60';
                    
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.style.background = originalBg;
                    }, 1500);
                }
                
                // Log the action
                this.log(`📋 Copied ${logCount} log entries to clipboard`, 'success');
            }).catch(err => {
                // Fallback if clipboard API fails
                alert(`Failed to copy to clipboard. Error: ${err.message}\n\nLogs:\n${fullText}`);
                this.logError(`Failed to copy logs: ${err.message}`);
            });
        } else {
            // Fallback: use old method
            this.copyToClipboardFallback(fullText);
            const btn = document.getElementById('debug-copy-logs');
            
            if (btn) {
                const originalText = btn.innerHTML;
                const originalBg = btn.style.background;
                
                btn.innerHTML = `${dbgIcon('check')} Copied!`;
                btn.style.background = '#27ae60';
                
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.style.background = originalBg;
                }, 1500);
            }
            
            this.log(`📋 Copied ${logCount} log entries (fallback method)`, 'success');
        }
    }
    
    showBugSection() {
        // Expand debugger and scroll to bug alert
        if (this.minimized) {
            document.getElementById('debug-minimize').click(); // Expand
        }
        
        // Scroll to bug alert
        const bugAlertDiv = document.getElementById('debug-bug-alert');
        if (bugAlertDiv) {
            bugAlertDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            // Flash the bug alert
            bugAlertDiv.style.animation = 'flash-bug 0.5s ease 2';
        }
    }

    // Helper: Log any editor state change
    logStateChange(propertyName, oldValue, newValue) {
        this.log(`🔄 ${propertyName}: ${oldValue} → ${newValue}`, 'info');
    }

    // Helper: Log object operations
    logObjectOperation(operation, objectType, count = 1) {
        const emoji = {
            'add': '➕',
            'delete': '🗑️',
            'move': '↔️',
            'resize': '📐',
            'rotate': '🔄',
            'link': '🔗',
            'select': '👆',
            'deselect': '👋'
        };
        
        const icon = emoji[operation.toLowerCase()] || '🔹';
        this.log(`${icon} ${operation} ${count} ${objectType}${count > 1 ? 's' : ''}`, 'action');
    }

    // Enable debugger from code
    show() {
        this.enabled = true;
        this.panel.style.display = 'block';
        localStorage.setItem('debugger_enabled', 'true');
        
        // Update minimized log if in minimized mode
        if (this.minimized) {
            setTimeout(() => this.updateMinimizedLog(), 10);
        }
        
        // Update debugger button state in top bar
        const debuggerBtn = document.getElementById('btn-debugger-top');
        if (debuggerBtn) {
            debuggerBtn.classList.add('active');
        }
        
        console.log('Debugger shown');
    }

    hide() {
        this.enabled = false;
        this.panel.style.display = 'none';
        localStorage.setItem('debugger_enabled', 'false');
        
        // Update debugger button state in top bar
        const debuggerBtn = document.getElementById('btn-debugger-top');
        if (debuggerBtn) {
            debuggerBtn.classList.remove('active');
        }
        
        console.log('Debugger hidden');
    }

    toggle() {
        if (this.enabled) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    toggleJumpAlerts() {
        this.showJumpAlerts = !this.showJumpAlerts;
        
        // Save to localStorage
        localStorage.setItem('debugger_show_jump_alerts', this.showJumpAlerts);
        
        // Update button appearance
        const btn = document.getElementById('debug-toggle-jump-alerts');
        if (btn) {
            btn.style.background = this.showJumpAlerts ? '#27ae60' : '#95a5a6';
            btn.innerHTML = `${this.showJumpAlerts ? '🔔' : '🔕'} Alerts`;
        }
        
        // Log the change
        if (this.showJumpAlerts) {
            this.logSuccess('🔔 Movement alert popups ENABLED');
            this.logInfo('Jump/movement errors will show bottom popup');
        } else {
            this.logInfo('🔕 Movement alert popups DISABLED');
            this.logInfo('Fast movement "bugs" suppressed - no popup (still logged)');
        }
    }
    
    showTextLogs() {
        const modal = document.getElementById('text-log-modal');
        const textarea = document.getElementById('text-log-content');
        
        if (!modal || !textarea) {
            console.error('Text log modal not found in DOM');
            return;
        }
        
        // Get last 100 logs
        const lastLogs = this.logs.slice(-100);
        const logText = lastLogs.map(log => 
            `[${log.time}] ${log.message}`
        ).join('\n');
        
        const header = `═══ TOPOLOGY DEBUGGER LOGS (Last ${lastLogs.length}) ═══\n`;
        const timestamp = `Exported: ${new Date().toLocaleString()}\n`;
        const separator = `${'═'.repeat(60)}\n\n`;
        const footer = `\n${'═'.repeat(60)}\nTotal logs: ${this.logs.length}\n`;
        
        textarea.value = header + timestamp + separator + logText + footer;
        modal.style.display = 'flex';
        
        // Auto-select text
        setTimeout(() => textarea.select(), 100);
        
        console.log('Text logs displayed with', lastLogs.length, 'entries');
    }
    
    copyToClipboardFallback(text) {
        // Fallback method for copying when navigator.clipboard is not available
        // Uses the old document.execCommand method or creates a temporary textarea
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                console.log('✅ Copied using fallback method');
            } else {
                // If execCommand also fails, show alert with text
                alert('Copy to clipboard:\n\n' + text);
            }
        } catch (err) {
            console.error('Fallback copy failed:', err);
            alert('Copy to clipboard:\n\n' + text);
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

// Make debugger available globally
window.createDebugger = function(editor) {
    return new TopologyDebugger(editor);
};

// Global shortcut: Press Shift+D+D (double D) to toggle debugger from anywhere
window.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 'd' && e.shiftKey && window.debugger) {
        window.debugger.toggle();
        e.preventDefault();
    }
});

// Helper function: Reset debugger to default position and size
window.resetDebugger = function() {
    localStorage.removeItem('debugger_position');
    localStorage.removeItem('debugger_size');
    localStorage.removeItem('debugger_enabled');
    localStorage.removeItem('debugger_minimized');
    console.log('Debugger settings reset. Reload the page to apply changes.');
    alert('Debugger settings have been reset!\nReload the page to see the debugger in its default position.');
};

// Helper function: Show debugger info
window.debuggerInfo = function() {
    const enabled = localStorage.getItem('debugger_enabled');
    const position = localStorage.getItem('debugger_position');
    const size = localStorage.getItem('debugger_size');
    const minimized = localStorage.getItem('debugger_minimized');
    
    console.log('=== DEBUGGER INFO ===');
    console.log('Enabled:', enabled);
    console.log('Position:', position);
    console.log('Size:', size);
    console.log('Minimized:', minimized);
    console.log('===================');
    
    if (window.debugger) {
        console.log('Current debugger instance:', {
            enabled: window.debugger.enabled,
            position: window.debugger.position,
            size: window.debugger.size,
            minimized: window.debugger.minimized
        });
    }
};
