// History/Undo-Redo System
// Handles state saving, restoration, and undo/redo operations

class HistoryManager {
    constructor(editor) {
        this.editor = editor;
        this.history = [];
        this.historyIndex = -1;
        this.maxHistorySize = 50;
    }

    saveState() {
        if (this.editor.initializing) return;
        try {
            console.log('saveState called with', this.editor.objects.length, 'objects');
            
            // Create deep copy of current state
            const state = {
                objects: JSON.parse(JSON.stringify(this.editor.objects)),
                deviceIdCounter: this.editor.deviceIdCounter,
                linkIdCounter: this.editor.linkIdCounter,
                textIdCounter: this.editor.textIdCounter,
                deviceCounters: { ...this.editor.deviceCounters }
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
            this.editor.files.scheduleAutoSave();
        } catch (error) {
            console.error('ERROR in saveState():', error);
            alert('Error saving state: ' + error.message);
        }
    }

    restoreState(state) {
        if (!state) return;
        
        // Temporarily disable auto-save during restore to prevent triggering saveState
        const wasInitializing = this.editor.initializing;
        this.editor.initializing = true;
        
        this.editor.objects = JSON.parse(JSON.stringify(state.objects));
        this.editor.deviceIdCounter = state.deviceIdCounter;
        this.editor.linkIdCounter = state.linkIdCounter;
        this.editor.textIdCounter = state.textIdCounter;
        this.editor.deviceCounters = { ...state.deviceCounters };
        
        this.editor.selectedObject = null;
        this.editor.selectedObjects = [];
        this.editor.ui.updatePropertiesPanel();
        this.editor.drawing.draw();
        
        // Restore initializing flag
        this.editor.initializing = wasInitializing;
    }

    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const state = this.history[this.historyIndex];
            this.restoreState(state);
            this.updateUndoRedoButtons();
            this.updateStepCounter();
            // Recalculate device counters for proper numbering
            this.editor.devices.updateDeviceCounters();
        }
    }

    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            const state = this.history[this.historyIndex];
            this.restoreState(state);
            this.updateUndoRedoButtons();
            this.updateStepCounter();
            // Recalculate device counters for proper numbering
            this.editor.devices.updateDeviceCounters();
        }
    }

    updateUndoRedoButtons() {
        const undoBtn = document.getElementById('btn-undo');
        const redoBtn = document.getElementById('btn-redo');
        
        if (undoBtn && redoBtn) {
            undoBtn.disabled = this.historyIndex <= 0;
            redoBtn.disabled = this.historyIndex >= this.history.length - 1;
            
            undoBtn.style.opacity = undoBtn.disabled ? '0.5' : '1';
            redoBtn.style.opacity = redoBtn.disabled ? '0.5' : '1';
        }
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

    initializeHistory(initialState) {
        // Create initial history entry without triggering auto-save
        this.history.push(initialState);
        this.historyIndex = 0;
        this.updateUndoRedoButtons();
        this.updateStepCounter();
    }
}

