/**
 * topology-link-editor.js - Link Details Editor Modal
 * 
 * Handles the link details modal for viewing and editing link properties.
 * This module provides a clean interface for the link editor functionality.
 * 
 * The actual implementation is still in topology.js (showLinkDetails).
 * This module serves as a wrapper that will eventually contain the full
 * implementation as code is migrated incrementally.
 * 
 * @version 1.0.0
 * @date 2026-02-03
 */

class LinkEditorModal {
    constructor(editor) {
        this.editor = editor;
        this.isVisible = false;
        this.currentLink = null;
        this.editingBulLinks = [];
        this.modalElement = null;
    }

    // ========================================================================
    // MAIN METHODS
    // ========================================================================

    /**
     * Show the link details modal
     * @param {object} link - Link to edit
     */
    show(link) {
        if (!link) return;
        
        this.currentLink = link;
        this.isVisible = true;
        
        // Delegate to editor's showLinkDetails for now
        if (typeof this.editor.showLinkDetails === 'function') {
            this.editor.showLinkDetails(link);
        }
        
        this.editor.events?.emit('linkEditor:opened', { link });
    }

    /**
     * Hide the link details modal (with validation)
     * Returns false if validation fails and modal should stay open
     * @returns {boolean} Whether the modal was closed
     */
    hide() {
        console.log('[LinkEditorModal] hide() called');
        
        // Auto-save before closing (if valid)
        if (this.currentLink || this.editor.editingLink) {
            const validity = this.checkValidity();
            if (!validity.valid) {
                // Show error toast when trying to close with invalid fields
                if (typeof this.editor.showValidationErrorToast === 'function') {
                    this.editor.showValidationErrorToast(validity.errors);
                }
                console.log('[LinkEditorModal] Not closed - invalid inputs', validity.errors);
                // Don't close modal - let user fix the errors
                return false;
            }
            // Valid - save before closing
            this.saveQuiet();
            console.log('[LinkEditorModal] Auto-saved before closing');
        }
        
        const modal = document.getElementById('link-details-modal');
        if (!modal) {
            console.error('[LinkEditorModal] Modal element not found!');
            return false;
        }
        
        modal.classList.remove('show');
        this.isVisible = false;
        this.currentLink = null;
        this.editingBulLinks = [];
        this.editor.editingLink = null;
        this.editor.editingBulLinks = null;
        
        this.editor.events?.emit('linkEditor:closed');
        console.log('[LinkEditorModal] Modal closed successfully');
        return true;
    }

    /**
     * Force hide the link details modal (ignores validation - for close button)
     */
    forceHide() {
        console.log('[LinkEditorModal] forceHide() called - ignoring validation');
        
        const modal = document.getElementById('link-details-modal');
        if (!modal) {
            console.error('[LinkEditorModal] Modal element not found!');
            return;
        }
        
        // Stop observing resize when modal closes
        const modalContent = modal.querySelector('.link-table-modal');
        if (modalContent && this.editor._modalResizeObserver) {
            this.editor._modalResizeObserver.unobserve(modalContent);
        }
        
        // Check if there are invalid fields and warn user
        if (this.currentLink || this.editor.editingLink) {
            const validity = this.checkValidity();
            if (!validity.valid) {
                // Show brief warning that changes weren't saved
                if (typeof this.editor.showValidationErrorToast === 'function') {
                    this.editor.showValidationErrorToast(validity.errors);
                }
            } else {
                // Valid - save before closing
                this.saveQuiet();
            }
        }
        
        modal.classList.remove('show');
        this.isVisible = false;
        this.currentLink = null;
        this.editingBulLinks = [];
        this.editor.editingLink = null;
        this.editor.editingBulLinks = null;
        
        this.editor.events?.emit('linkEditor:closed');
        console.log('[LinkEditorModal] Modal force closed');
    }

    /**
     * Check validity of current form
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    checkValidity() {
        if (typeof this.editor.checkLinkTableValidity === 'function') {
            return this.editor.checkLinkTableValidity();
        }
        return { valid: true, errors: [] };
    }

    /**
     * Save link details quietly (no notifications)
     */
    saveQuiet() {
        if (typeof this.editor.saveLinkDetailsQuiet === 'function') {
            this.editor.saveLinkDetailsQuiet();
        }
    }

    /**
     * Initialize floating labels for Link Table inputs
     * Adds focus/blur/change animations and auto-saves on change
     */
    initFloatingLabels() {
        const fields = document.querySelectorAll('.link-table-field');
        const self = this;
        
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
                    
                    // Auto-save changes (delegate to editor)
                    if (typeof self.editor.updateLinkTableValue === 'function') {
                        self.editor.updateLinkTableValue(input.id, input.value);
                    }
                });
                
                // Input event (for text inputs)
                input.addEventListener('input', () => {
                    if (input.value) {
                        field.classList.add('has-value');
                    } else {
                        field.classList.remove('has-value');
                    }
                    
                    // Auto-save changes (delegate to editor)
                    if (typeof self.editor.updateLinkTableValue === 'function') {
                        self.editor.updateLinkTableValue(input.id, input.value);
                    }
                });
            }
        });
    }

    /**
     * Save link details
     * @returns {boolean} Success
     */
    save() {
        if (typeof this.editor.saveLinkDetails === 'function') {
            this.editor.saveLinkDetails();
            this.editor.events?.emit('linkEditor:saved', { link: this.currentLink });
            return true;
        }
        return false;
    }

    /**
     * Check if editor is visible
     * @returns {boolean}
     */
    getIsVisible() {
        return this.isVisible;
    }

    /**
     * Get current link being edited
     * @returns {object|null}
     */
    getCurrentLink() {
        return this.currentLink;
    }

    // ========================================================================
    // FIELD MANAGEMENT
    // ========================================================================

    /**
     * Populate form fields with link data
     */
    populateFields() {
        if (typeof this.editor.populateLinkTableFields === 'function') {
            this.editor.populateLinkTableFields();
        }
    }

    /**
     * Validate current form data
     * @returns {boolean} True if valid
     */
    validateForm() {
        if (typeof this.editor.checkLinkTableValidity === 'function') {
            return this.editor.checkLinkTableValidity();
        }
        return true;
    }

    /**
     * Get form data
     * @returns {object} Form data
     */
    getFormData() {
        // Collect data from modal form fields
        const data = {
            link: this.currentLink,
            // Additional form data would be collected here
        };
        return data;
    }

    // ========================================================================
    // INTERFACE MANAGEMENT
    // ========================================================================

    /**
     * Populate interface dropdown
     * @param {HTMLElement} selectElement - Select element
     * @param {object} device - Device object
     * @param {string} currentValue - Current selected value
     */
    populateInterfaces(selectElement, device, currentValue = '') {
        if (typeof this.editor.populateInterfaces === 'function') {
            this.editor.populateInterfaces(selectElement, device, currentValue);
        }
    }

    /**
     * Populate platform models dropdown
     * @param {HTMLElement} selectElement - Select element
     * @param {string} currentValue - Current selected value
     */
    populatePlatformModels(selectElement, currentValue = '') {
        if (typeof this.editor.populatePlatformModels === 'function') {
            this.editor.populatePlatformModels(selectElement, currentValue);
        }
    }

    // ========================================================================
    // VLAN MANAGEMENT
    // ========================================================================

    /**
     * Validate VLAN configuration
     * @returns {object} Validation result
     */
    validateVlanConfiguration() {
        if (typeof this.editor.validateVlanConfiguration === 'function') {
            return this.editor.validateVlanConfiguration();
        }
        return { valid: true };
    }

    /**
     * Setup VLAN validation listeners
     */
    setupVlanValidation() {
        if (typeof this.editor.setupLinkTableValidation === 'function') {
            this.editor.setupLinkTableValidation();
        }
    }

    // ========================================================================
    // BUL CHAIN SUPPORT
    // ========================================================================

    /**
     * Get all links in the BUL chain being edited
     * @returns {array}
     */
    getEditingChain() {
        return this.editingBulLinks || [];
    }

    /**
     * Set the BUL chain being edited
     * @param {array} links - Links in the chain
     */
    setEditingChain(links) {
        this.editingBulLinks = links || [];
    }

    // ========================================================================
    // UTILITIES
    // ========================================================================

    /**
     * Check if a specific row has valid data
     * @param {number} rowIndex - Row index
     * @returns {boolean}
     */
    isRowValid(rowIndex) {
        // Would check specific row validity
        return true;
    }

    /**
     * Get link table element
     * @returns {HTMLElement|null}
     */
    getTableElement() {
        return document.getElementById('link-table-body');
    }

    /**
     * Get modal container element
     * @returns {HTMLElement|null}
     */
    getModalElement() {
        return document.getElementById('link-details-panel') || 
               document.querySelector('.link-details-modal');
    }

    /**
     * Focus the first input in the modal
     */
    focusFirstInput() {
        const modal = this.getModalElement();
        if (modal) {
            const firstInput = modal.querySelector('input, select');
            if (firstInput) firstInput.focus();
        }
    }

    // ========================================================================
    // TABLE VALUE MANAGEMENT (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Field mappings from input IDs to link properties
     */
    static FIELD_MAPPINGS = {
        'lt-platform-cat-a': 'device1PlatformCategory',
        'lt-platform-cat-b': 'device2PlatformCategory',
        'lt-platform-model-a': 'device1Platform',
        'lt-platform-model-b': 'device2Platform',
        'lt-interface-a': 'device1Interface',
        'lt-interface-b': 'device2Interface',
        'lt-transceiver-a': 'device1Transceiver',
        'lt-transceiver-b': 'device2Transceiver',
        'lt-ip-type-a': 'device1IpType',
        'lt-ip-type-b': 'device2IpType',
        'lt-ip-addr-a': 'device1IpAddress',
        'lt-ip-addr-b': 'device2IpAddress',
        'lt-vlan-tpid-a': 'device1VlanTpid',
        'lt-vlan-tpid-b': 'device2VlanTpid',
        'lt-outer-tag-a': 'device1OuterTag',
        'lt-outer-tag-b': 'device2OuterTag',
        'lt-inner-tag-a': 'device1InnerTag',
        'lt-inner-tag-b': 'device2InnerTag',
        'lt-ingress-a': 'device1IngressAction',
        'lt-ingress-b': 'device2IngressAction',
        'lt-egress-a': 'device1EgressAction',
        'lt-egress-b': 'device2EgressAction',
        'lt-dnaas-vlan-a': 'device1DnaasVlan',
        'lt-dnaas-vlan-b': 'device2DnaasVlan'
    };

    /**
     * Link properties list for reset operations
     */
    static LINK_PROPERTIES = [
        'device1PlatformCategory', 'device2PlatformCategory',
        'device1Platform', 'device2Platform',
        'device1Interface', 'device2Interface',
        'device1Transceiver', 'device2Transceiver',
        'device1IpType', 'device2IpType',
        'device1IpAddress', 'device2IpAddress',
        'device1VlanMode', 'device2VlanMode',
        'device1VlanId', 'device2VlanId',
        'device1VlanTpid', 'device2VlanTpid',
        'device1OuterTag', 'device2OuterTag',
        'device1InnerTag', 'device2InnerTag',
        'device1IngressAction', 'device2IngressAction',
        'device1EgressAction', 'device2EgressAction',
        'device1DnaasVlan', 'device2DnaasVlan'
    ];

    /**
     * Update link property from table input
     * @param {string} inputId - Input element ID
     * @param {string} value - New value
     */
    updateValue(inputId, value) {
        const link = this.currentLink || this.editor.editingLink;
        if (!link) return;
        
        const property = LinkEditorModal.FIELD_MAPPINGS[inputId];
        if (property) {
            link[property] = value;
            this.updateCalculatedFields();
        }
    }

    /**
     * Update calculated/readonly fields (VLAN stacks, manipulation summaries)
     */
    updateCalculatedFields() {
        const link = this.currentLink || this.editor.editingLink;
        if (!link) return;
        
        // Calculate VLAN Stack for Side A
        const outerA = document.getElementById('lt-outer-tag-a')?.value || '';
        const innerA = document.getElementById('lt-inner-tag-a')?.value || '';
        const stackA = document.getElementById('lt-vlan-stack-a');
        if (stackA) {
            if (outerA && innerA) {
                stackA.value = `${outerA}.${innerA}`;
            } else if (outerA) {
                stackA.value = outerA;
            } else {
                stackA.value = '';
            }
        }
        
        // Calculate VLAN Stack for Side B
        const outerB = document.getElementById('lt-outer-tag-b')?.value || '';
        const innerB = document.getElementById('lt-inner-tag-b')?.value || '';
        const stackB = document.getElementById('lt-vlan-stack-b');
        if (stackB) {
            if (outerB && innerB) {
                stackB.value = `${outerB}.${innerB}`;
            } else if (outerB) {
                stackB.value = outerB;
            } else {
                stackB.value = '';
            }
        }
        
        // Calculate Manipulation Summary for Side A
        const ingressA = document.getElementById('lt-ingress-a')?.value || '';
        const egressA = document.getElementById('lt-egress-a')?.value || '';
        const manipA = document.getElementById('lt-manip-summary-a');
        if (manipA) {
            const parts = [];
            if (ingressA) parts.push(`In: ${ingressA}`);
            if (egressA) parts.push(`Out: ${egressA}`);
            manipA.value = parts.join(' | ') || 'None';
        }
        
        // Calculate Manipulation Summary for Side B
        const ingressB = document.getElementById('lt-ingress-b')?.value || '';
        const egressB = document.getElementById('lt-egress-b')?.value || '';
        const manipB = document.getElementById('lt-manip-summary-b');
        if (manipB) {
            const parts = [];
            if (ingressB) parts.push(`In: ${ingressB}`);
            if (egressB) parts.push(`Out: ${egressB}`);
            manipB.value = parts.join(' | ') || 'None';
        }
    }

    /**
     * Reset all Link Table fields to empty
     */
    resetFields() {
        const link = this.currentLink || this.editor.editingLink;
        if (!link) return;
        
        // Clear all input fields using the correct modal class
        const inputs = document.querySelectorAll('.link-table-modal input:not([readonly]), .link-table-modal select');
        inputs.forEach(input => {
            if (input.type === 'number') {
                input.value = '';
            } else if (input.tagName === 'SELECT') {
                input.selectedIndex = 0;
            } else {
                input.value = '';
            }
            
            // Remove validation states
            input.classList.remove('valid', 'invalid');
        });
        
        // Clear link properties
        LinkEditorModal.LINK_PROPERTIES.forEach(prop => {
            link[prop] = '';
        });
        
        // Update VLAN visibility (delegate to editor)
        if (typeof this.editor.updateVlanFieldsVisibility === 'function') {
            this.editor.updateVlanFieldsVisibility();
        }
        
        // Update calculated fields
        this.updateCalculatedFields();
    }

    // ========================================================================
    // INPUT VALIDATION (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Validate VLAN input (1-4096, ranges with "-", multiples with ",")
     * @param {string} value - VLAN value to validate
     * @returns {Object} { valid: boolean, value?: string, error?: string }
     */
    validateVlanInput(value) {
        if (!value || value.trim() === '') return { valid: true, value: '' };
        
        const trimmed = value.trim();
        
        // Split by comma for multiple VLANs
        const parts = trimmed.split(',').map(p => p.trim()).filter(p => p);
        
        for (const part of parts) {
            // Check if it's a range (e.g., "100-200")
            if (part.includes('-')) {
                const rangeParts = part.split('-').map(p => p.trim());
                if (rangeParts.length !== 2) return { valid: false, error: 'Invalid range format' };
                
                const start = parseInt(rangeParts[0], 10);
                const end = parseInt(rangeParts[1], 10);
                
                if (isNaN(start) || isNaN(end)) return { valid: false, error: 'Range must be numbers' };
                if (start < 1 || start > 4096 || end < 1 || end > 4096) return { valid: false, error: 'VLAN must be 1-4096' };
                if (start > end) return { valid: false, error: 'Invalid range (start > end)' };
            } else {
                // Single VLAN value
                const num = parseInt(part, 10);
                if (isNaN(num) || part !== String(num)) return { valid: false, error: 'Must be a number' };
                if (num < 1 || num > 4096) return { valid: false, error: 'VLAN must be 1-4096' };
            }
        }
        
        return { valid: true, value: trimmed };
    }

    /**
     * Validate IPv4 address (x.x.x.x where x is 0-255)
     * @param {string} value - IPv4 value to validate
     * @returns {Object} { valid: boolean, value?: string, error?: string }
     */
    validateIPv4(value) {
        if (!value || value.trim() === '') return { valid: true, value: '' };
        
        const trimmed = value.trim();
        
        // Check for CIDR notation (x.x.x.x/prefix)
        let ip = trimmed;
        let prefix = null;
        if (trimmed.includes('/')) {
            const parts = trimmed.split('/');
            ip = parts[0];
            prefix = parseInt(parts[1], 10);
            if (isNaN(prefix) || prefix < 0 || prefix > 32) {
                return { valid: false, error: 'Prefix must be 0-32' };
            }
        }
        
        const octets = ip.split('.');
        if (octets.length !== 4) return { valid: false, error: 'Must have 4 octets' };
        
        for (const octet of octets) {
            const num = parseInt(octet, 10);
            if (isNaN(num) || octet !== String(num)) return { valid: false, error: 'Octets must be numbers' };
            if (num < 0 || num > 255) return { valid: false, error: 'Octets must be 0-255' };
        }
        
        return { valid: true, value: trimmed };
    }

    /**
     * Validate IPv6 address
     * @param {string} value - IPv6 value to validate
     * @returns {Object} { valid: boolean, value?: string, error?: string }
     */
    validateIPv6(value) {
        if (!value || value.trim() === '') return { valid: true, value: '' };
        
        const trimmed = value.trim();
        
        // Check for CIDR notation
        let ip = trimmed;
        let prefix = null;
        if (trimmed.includes('/')) {
            const lastSlash = trimmed.lastIndexOf('/');
            ip = trimmed.substring(0, lastSlash);
            prefix = parseInt(trimmed.substring(lastSlash + 1), 10);
            if (isNaN(prefix) || prefix < 0 || prefix > 128) {
                return { valid: false, error: 'Prefix must be 0-128' };
            }
        }
        
        // IPv6 regex pattern (simplified)
        const ipv6Pattern = /^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]+|::(ffff(:0{1,4})?:)?((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\.){3}(25[0-5]|(2[0-4]|1?[0-9])?[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\.){3}(25[0-5]|(2[0-4]|1?[0-9])?[0-9]))$/;
        
        if (!ipv6Pattern.test(ip)) {
            return { valid: false, error: 'Invalid IPv6 format' };
        }
        
        return { valid: true, value: trimmed };
    }

    /**
     * Validate IP address based on type
     * @param {string} value - IP address value
     * @param {string} type - 'IPv4', 'IPv6', or 'L2-Service'
     * @returns {Object} { valid: boolean, value?: string, error?: string }
     */
    validateIpAddress(value, type) {
        if (type === 'IPv4') return this.validateIPv4(value);
        if (type === 'IPv6') return this.validateIPv6(value);
        return { valid: true, value: value }; // L2-Service doesn't need IP validation
    }

    // ========================================================================
    // VLAN FIELD MANAGEMENT (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Update VLAN fields visibility based on mode selection
     */
    updateVlanFieldsVisibility() {
        const modeA = document.getElementById('lt-vlan-mode-a')?.value || '';
        const modeB = document.getElementById('lt-vlan-mode-b')?.value || '';
        
        // Get row elements
        const vlanIdRow = document.getElementById('lt-vlan-id-row');
        const tpidRow = document.getElementById('lt-vlan-tpid-row');
        const outerTagRow = document.getElementById('lt-outer-tag-row');
        const innerTagRow = document.getElementById('lt-inner-tag-row');
        
        // Determine what to show based on both sides
        const showVlanId = modeA === 'vlan-id' || modeB === 'vlan-id';
        const showVlanTags = modeA === 'vlan-tags' || modeB === 'vlan-tags';
        
        // Update visibility
        if (vlanIdRow) vlanIdRow.style.display = showVlanId ? '' : 'none';
        if (tpidRow) tpidRow.style.display = showVlanTags ? '' : 'none';
        if (outerTagRow) outerTagRow.style.display = showVlanTags ? '' : 'none';
        if (innerTagRow) innerTagRow.style.display = showVlanTags ? '' : 'none';
        
        // Disable fields on the side that's not using that mode
        // Side A fields
        const vlanIdA = document.getElementById('lt-vlan-id-a');
        const tpidA = document.getElementById('lt-vlan-tpid-a');
        const outerA = document.getElementById('lt-outer-tag-a');
        const innerA = document.getElementById('lt-inner-tag-a');
        
        if (vlanIdA) vlanIdA.disabled = modeA !== 'vlan-id';
        if (tpidA) tpidA.disabled = modeA !== 'vlan-tags';
        if (outerA) outerA.disabled = modeA !== 'vlan-tags';
        if (innerA) innerA.disabled = modeA !== 'vlan-tags';
        
        // Side B fields
        const vlanIdB = document.getElementById('lt-vlan-id-b');
        const tpidB = document.getElementById('lt-vlan-tpid-b');
        const outerB = document.getElementById('lt-outer-tag-b');
        const innerB = document.getElementById('lt-inner-tag-b');
        
        if (vlanIdB) vlanIdB.disabled = modeB !== 'vlan-id';
        if (tpidB) tpidB.disabled = modeB !== 'vlan-tags';
        if (outerB) outerB.disabled = modeB !== 'vlan-tags';
        if (innerB) innerB.disabled = modeB !== 'vlan-tags';
    }

    /**
     * Derive Category from Model prefix
     * Categories: DNAAS, NC-AI, SA, CL
     * @param {string} model - Platform model name
     * @returns {string} Category name or empty string
     */
    deriveCategoryFromModel(model) {
        if (!model) return '';
        
        const modelUpper = model.toUpperCase();
        
        // NCM, NCC = DNAAS (Network Cloud Module, Network Cloud Controller)
        if (modelUpper.startsWith('NCM') || modelUpper.startsWith('NCC')) {
            return 'DNAAS';
        }
        
        // AI- prefix = NC-AI (Network Cloud AI)
        if (modelUpper.startsWith('AI-')) {
            return 'NC-AI';
        }
        
        // CL- prefix = CL (Cluster)
        if (modelUpper.startsWith('CL-')) {
            return 'CL';
        }
        
        // SA- prefix = SA (Standalone)
        if (modelUpper.startsWith('SA-')) {
            return 'SA';
        }
        
        // Legacy NCP detection - map to NC-AI
        if (modelUpper.startsWith('NCP')) {
            return 'NC-AI';
        }
        
        return '';
    }

    /**
     * Simple toast notification
     * @param {string} message - Message to display
     * @param {string} type - 'success', 'error', or 'info'
     */
    showToast(message, type = 'info') {
        if (window.NotificationManager) {
            return window.NotificationManager.showNotification(this.editor, message, type);
        }
    }

    // ========================================================================
    // AUTO-SAVE MANAGEMENT (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Auto-save link table when values change (debounced)
     */
    autoSave() {
        if (!this.editor.editingLink) return;
        
        // Debounce auto-save to avoid too many saves
        if (this._autoSaveTimeout) {
            clearTimeout(this._autoSaveTimeout);
        }
        
        this._autoSaveTimeout = setTimeout(() => {
            this.saveQuiet();
        }, 300);
    }

    /**
     * Save link details without showing toast (for auto-save)
     * Collects all form values and updates the link object
     */
    saveQuietFull() {
        if (!this.editor.editingLink) return;
        
        const link = this.editor.editingLink;
        
        // Platform
        link.device1PlatformCategory = document.getElementById('lt-platform-cat-a')?.value || '';
        link.device2PlatformCategory = document.getElementById('lt-platform-cat-b')?.value || '';
        link.device1Platform = document.getElementById('lt-platform-model-a')?.value || '';
        link.device2Platform = document.getElementById('lt-platform-model-b')?.value || '';
        
        // Interface - capture for TB creation
        const newDevice1Interface = document.getElementById('lt-interface-a')?.value || '';
        const newDevice2Interface = document.getElementById('lt-interface-b')?.value || '';
        
        // Check if interface values changed for auto-TB creation
        const interface1Changed = newDevice1Interface && newDevice1Interface !== link.device1Interface;
        const interface2Changed = newDevice2Interface && newDevice2Interface !== link.device2Interface;
        
        link.device1Interface = newDevice1Interface;
        link.device2Interface = newDevice2Interface;
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
        
        // AUTO-CREATE TEXT BOXES from interface fields
        if (interface1Changed && this.editor.createOrUpdateInterfaceTextBox) {
            this.editor.createOrUpdateInterfaceTextBox(link, 'device1', newDevice1Interface);
        }
        if (interface2Changed && this.editor.createOrUpdateInterfaceTextBox) {
            this.editor.createOrUpdateInterfaceTextBox(link, 'device2', newDevice2Interface);
        }
        
        // Redraw to show changes
        if (this.editor.draw) {
            this.editor.draw();
        }
    }

    // ========================================================================
    // DNAAS AUTO-FILL INDICATOR (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Show visual indicator that DNAAS data was auto-filled
     */
    showDnaasAutoFillIndicator() {
        const modal = document.getElementById('link-details-modal');
        if (!modal) return;
        
        // Add DNAAS badge to header if not already present
        const header = modal.querySelector('.link-details-header');
        if (header && !header.querySelector('.dnaas-autofill-badge')) {
            const badge = document.createElement('span');
            badge.className = 'dnaas-autofill-badge';
            badge.innerHTML = '🔗 DNAAS Auto-filled';
            badge.style.cssText = `
                background: linear-gradient(135deg, #9b59b6, #8e44ad);
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
                margin-left: 10px;
                animation: pulse 2s ease-in-out;
            `;
            header.appendChild(badge);
            
            // Remove after 5 seconds
            setTimeout(() => badge.remove(), 5000);
        }
        
        // Highlight auto-filled fields briefly
        const fieldsToHighlight = [
            'lt-vlan-id-a', 'lt-vlan-id-b',
            'lt-inner-tag-a', 'lt-inner-tag-b',
            'lt-ingress-a', 'lt-ingress-b',
            'lt-ip-type-a', 'lt-ip-type-b'
        ];
        
        fieldsToHighlight.forEach(id => {
            const field = document.getElementById(id);
            if (field && field.value) {
                field.style.background = 'rgba(155, 89, 182, 0.2)';
                field.style.transition = 'background 0.3s ease';
                setTimeout(() => {
                    field.style.background = '';
                }, 2000);
            }
        });
    }

    /**
     * Detect Model from device name (e.g., DNAAS-LEAF-B10 -> NCM-1600)
     * @param {string} deviceName - Device name to analyze
     * @returns {string} Platform model or empty string
     */
    detectModelFromDeviceName(deviceName) {
        if (!deviceName) return '';
        
        const nameLower = deviceName.toLowerCase();
        
        // DNAAS fabric devices (LEAF, SPINE, SuperSpine)
        if (nameLower.includes('leaf') || nameLower.includes('spine') || nameLower.includes('superspine')) {
            return 'NCM-1600';
        }
        
        // PE routers / Termination devices
        if (nameLower.includes('pe') || nameLower.includes('yor_') || nameLower.includes('_pe')) {
            return 'SA-36CD-S';
        }
        
        // CE / Customer Edge
        if (nameLower.includes('ce')) {
            return 'SA-40C';
        }
        
        // P routers / Provider core
        if (nameLower.includes('_p-') || nameLower.includes('-p-') || nameLower.match(/\bp\d+\b/)) {
            return 'SA-36CD-S';
        }
        
        return '';
    }

    /**
     * Update the "To A/B" column headers with actual device names and interfaces
     * @param {string} device1Name - Device 1 name
     * @param {string} device1Interface - Device 1 interface
     * @param {string} device2Name - Device 2 name
     * @param {string} device2Interface - Device 2 interface
     */
    updateStackColumnHeaders(device1Name, device1Interface, device2Name, device2Interface) {
        const thStackToB = document.getElementById('th-stack-to-b');
        const thStackToA = document.getElementById('th-stack-to-a');
        
        if (thStackToB) {
            thStackToB.innerHTML = `→ ${device2Name}<br><span id="th-stack-to-b-sub" style="font-size: 9px; font-weight: normal; opacity: 0.9;">(${device2Interface || 'interface'})</span>`;
        }
        if (thStackToA) {
            thStackToA.innerHTML = `${device1Name} ←<br><span id="th-stack-to-a-sub" style="font-size: 9px; font-weight: normal; opacity: 0.9;">(${device1Interface || 'interface'})</span>`;
        }
        
        // Update cell labels
        const stackToBLabel = document.getElementById('stack-to-b-label');
        const stackToBIface = document.getElementById('stack-to-b-iface');
        const stackToALabel = document.getElementById('stack-to-a-label');
        const stackToAIface = document.getElementById('stack-to-a-iface');
        
        if (stackToBLabel) stackToBLabel.textContent = `→ ${device2Name}`;
        if (stackToBIface) stackToBIface.textContent = `(${device2Interface || 'interface'})`;
        if (stackToALabel) stackToALabel.textContent = `${device1Name} ←`;
        if (stackToAIface) stackToAIface.textContent = `(${device1Interface || 'interface'})`;
    }

    /**
     * Setup platform cascading dropdowns (category -> platform -> interface -> transceiver)
     * @param {string} side - 'd1' or 'd2'
     * @param {Object} link - Link object
     */
    setupPlatformCascading(side, link) {
        const categorySelect = document.getElementById(`link-${side}-platform-category`);
        const platformSelect = document.getElementById(`link-${side}-platform`);
        const interfaceSelect = document.getElementById(`link-${side}-interface`);
        const transceiverSelect = document.getElementById(`link-${side}-transceiver`);
        
        if (!categorySelect || !platformSelect || !interfaceSelect) return;
        
        // Helper to reset transceiver
        const resetTransceiver = () => {
            if (transceiverSelect) {
                transceiverSelect.innerHTML = '<option value="">-- Select Interface First --</option>';
                transceiverSelect.disabled = true;
            }
        };
        
        // Helper to reset interface
        const resetInterface = () => {
            interfaceSelect.innerHTML = '<option value="">-- Select Platform First --</option>';
            interfaceSelect.disabled = true;
            resetTransceiver();
        };
        
        // Set initial values if they exist
        const categoryProp = side === 'd1' ? 'device1PlatformCategory' : 'device2PlatformCategory';
        const platformProp = side === 'd1' ? 'device1Platform' : 'device2Platform';
        const interfaceProp = side === 'd1' ? 'device1Interface' : 'device2Interface';
        
        if (link[categoryProp]) {
            categorySelect.value = link[categoryProp];
            if (this.editor.populatePlatformDropdown) {
                this.editor.populatePlatformDropdown(side, link[categoryProp]);
            }
            
            if (link[platformProp]) {
                platformSelect.value = link[platformProp];
                if (this.editor.populateInterfaceDropdown) {
                    this.editor.populateInterfaceDropdown(side, link[platformProp]);
                }
                
                // Set interface value after dropdown is populated
                setTimeout(() => {
                    const currentInterfaceSelect = document.getElementById(`link-${side}-interface`);
                    if (currentInterfaceSelect && link[interfaceProp]) {
                        currentInterfaceSelect.value = link[interfaceProp];
                        if (this.editor.populateTransceiverDropdown) {
                            this.editor.populateTransceiverDropdown(side, link[interfaceProp]);
                        }
                    }
                }, 20);
            }
        }
        
        // Category change handler
        categorySelect.addEventListener('change', () => {
            const category = categorySelect.value;
            if (category && this.editor.populatePlatformDropdown) {
                this.editor.populatePlatformDropdown(side, category);
            } else {
                platformSelect.innerHTML = '<option value="">-- Select Category First --</option>';
                platformSelect.disabled = true;
            }
            resetInterface();
        });
        
        // Platform change handler
        platformSelect.addEventListener('change', () => {
            const platform = platformSelect.value;
            if (platform && this.editor.populateInterfaceDropdown) {
                this.editor.populateInterfaceDropdown(side, platform);
            } else {
                resetInterface();
            }
            resetTransceiver();
        });
        
        // Interface change handler
        interfaceSelect.addEventListener('change', () => {
            const iface = interfaceSelect.value;
            if (this.editor.populateTransceiverDropdown) {
                this.editor.populateTransceiverDropdown(side, iface);
            }
        });
    }

    /**
     * Populate platform dropdown based on category
     * @param {string} side - 'd1' or 'd2'
     * @param {string} category - Platform category
     */
    populatePlatformDropdown(side, category) {
        const platformSelect = document.getElementById(`link-${side}-platform`);
        if (!platformSelect || !category) {
            if (platformSelect) {
                platformSelect.innerHTML = '<option value="">-- Select Category First --</option>';
                platformSelect.disabled = true;
            }
            return;
        }
        
        const platforms = this.editor.getPlatformsByCategory ? 
            this.editor.getPlatformsByCategory(category) : [];
            
        if (platforms.length === 0) {
            platformSelect.innerHTML = '<option value="">-- No Platforms --</option>';
            platformSelect.disabled = true;
            return;
        }
        
        let optionsHtml = '<option value="">-- Select Platform --</option>';
        platforms.forEach(p => {
            optionsHtml += `<option value="${p.official}">${p.displayName}</option>`;
        });
        
        platformSelect.innerHTML = optionsHtml;
        platformSelect.disabled = false;
        
        // Smooth transition
        platformSelect.style.opacity = '0';
        setTimeout(() => {
            platformSelect.style.transition = 'opacity 0.3s ease';
            platformSelect.style.opacity = '1';
        }, 10);
    }

    /**
     * Populate interface dropdown based on platform
     * @param {string} side - 'd1' or 'd2'
     * @param {string} platformOfficial - Platform official name
     */
    populateInterfaceDropdown(side, platformOfficial) {
        const interfaceSelect = document.getElementById(`link-${side}-interface`);
        if (!interfaceSelect) return;
        
        if (!platformOfficial) {
            interfaceSelect.innerHTML = '<option value="">-- Select Platform First --</option>';
            interfaceSelect.disabled = true;
            return;
        }
        
        const platform = this.editor.getPlatformByOfficial ? 
            this.editor.getPlatformByOfficial(platformOfficial) : null;
            
        if (!platform || !platform.interfaces || platform.interfaces.length === 0) {
            interfaceSelect.innerHTML = '<option value="">-- No Interfaces --</option>';
            interfaceSelect.disabled = true;
            return;
        }
        
        // Group interfaces by type
        const interfaces = platform.interfaces;
        const grouped = {};
        
        interfaces.forEach(iface => {
            const match = iface.match(/^([a-z]+\d*)/i);
            const prefix = match ? match[1] : 'other';
            if (!grouped[prefix]) grouped[prefix] = [];
            grouped[prefix].push(iface);
        });
        
        let optionsHtml = '<option value="">-- Select Interface --</option>';
        
        const prefixOrder = ['ge100', 'ge400', 'ge800', 'ge25', 'ge10', 'lag', 'mgmt', 'loopback'];
        const sortedPrefixes = Object.keys(grouped).sort((a, b) => {
            const idxA = prefixOrder.indexOf(a);
            const idxB = prefixOrder.indexOf(b);
            if (idxA === -1 && idxB === -1) return a.localeCompare(b);
            if (idxA === -1) return 1;
            if (idxB === -1) return -1;
            return idxA - idxB;
        });
        
        sortedPrefixes.forEach(prefix => {
            const groupInterfaces = grouped[prefix];
            const toShow = groupInterfaces.slice(0, 10);
            
            optionsHtml += `<optgroup label="${prefix.toUpperCase()} (${groupInterfaces.length})">`;
            toShow.forEach(iface => {
                optionsHtml += `<option value="${iface}">${iface}</option>`;
            });
            if (groupInterfaces.length > 10) {
                optionsHtml += `<option value="" disabled>... ${groupInterfaces.length - 10} more</option>`;
            }
            optionsHtml += '</optgroup>';
        });
        
        interfaceSelect.innerHTML = optionsHtml;
        interfaceSelect.disabled = false;
        
        // Smooth transition
        interfaceSelect.style.opacity = '0';
        setTimeout(() => {
            interfaceSelect.style.transition = 'opacity 0.2s ease';
            interfaceSelect.style.opacity = '1';
        }, 10);
    }

    /**
     * Populate transceiver dropdown based on interface type
     * @param {string} side - 'd1' or 'd2'
     * @param {string} interfaceName - Interface name
     */
    populateTransceiverDropdown(side, interfaceName) {
        const transceiverSelect = document.getElementById(`link-${side}-transceiver`);
        if (!transceiverSelect) return;
        
        if (!interfaceName) {
            transceiverSelect.innerHTML = '<option value="">-- Select Interface First --</option>';
            transceiverSelect.disabled = true;
            return;
        }
        
        const transceivers = this.editor.getTransceiversForInterface ? 
            this.editor.getTransceiversForInterface(interfaceName) : [];
        
        if (transceivers.length === 0) {
            transceiverSelect.innerHTML = '<option value="">-- N/A (No Optics) --</option>';
            transceiverSelect.disabled = true;
            return;
        }
        
        let optionsHtml = '<option value="">-- Select Transceiver --</option>';
        
        // Group by form factor
        const grouped = {};
        transceivers.forEach(t => {
            const formFactor = t.type.split(' ')[0];
            if (!grouped[formFactor]) grouped[formFactor] = [];
            grouped[formFactor].push(t);
        });
        
        Object.keys(grouped).forEach(formFactor => {
            optionsHtml += `<optgroup label="${formFactor}">`;
            grouped[formFactor].forEach(t => {
                const tooltip = `${t.type} | Reach: ${t.reach} | Media: ${t.media}`;
                optionsHtml += `<option value="${t.name}" title="${tooltip}">${t.name} (${t.reach})</option>`;
            });
            optionsHtml += '</optgroup>';
        });
        
        transceiverSelect.innerHTML = optionsHtml;
        transceiverSelect.disabled = false;
        
        // Smooth transition
        transceiverSelect.style.opacity = '0';
        setTimeout(() => {
            transceiverSelect.style.transition = 'opacity 0.2s ease';
            transceiverSelect.style.opacity = '1';
        }, 10);
    }

    // ========================================================================
    // FIELD HELPERS (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Helper to set a field value (handles both input and select elements)
     * @param {string} elementId - ID of the element
     * @param {string} value - Value to set
     */
    setFieldValue(elementId, value) {
        const el = document.getElementById(elementId);
        if (!el) return;
        
        // For select elements, add the option if it doesn't exist
        if (el.tagName === 'SELECT' && value) {
            let optionExists = Array.from(el.options).some(opt => opt.value === value);
            if (!optionExists) {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                el.appendChild(option);
            }
        }
        
        el.value = value || '';
        
        // Update field state for floating labels
        const field = el.closest('.link-table-field');
        if (field) {
            if (value) {
                field.classList.add('has-value');
            } else {
                field.classList.remove('has-value');
            }
        }
    }

    /**
     * Update IP address field visibility based on IP type selection
     */
    updateIpAddressFieldVisibility() {
        const ipTypeA = document.getElementById('lt-ip-type-a');
        const ipTypeB = document.getElementById('lt-ip-type-b');
        const ipAddrA = document.getElementById('lt-ip-addr-a');
        const ipAddrB = document.getElementById('lt-ip-addr-b');
        
        if (ipTypeA && ipAddrA) {
            const typeA = ipTypeA.value;
            if (typeA === 'IPv4') {
                ipAddrA.placeholder = 'e.g. 192.168.1.1/24';
                ipAddrA.disabled = false;
                ipAddrA.classList.remove('disabled');
            } else if (typeA === 'IPv6') {
                ipAddrA.placeholder = 'e.g. 2001:db8::1/64';
                ipAddrA.disabled = false;
                ipAddrA.classList.remove('disabled');
            } else {
                ipAddrA.placeholder = 'N/A for L2 Service';
                ipAddrA.value = '';
                ipAddrA.disabled = true;
                ipAddrA.classList.add('disabled');
                ipAddrA.classList.remove('invalid', 'valid');
            }
        }
        
        if (ipTypeB && ipAddrB) {
            const typeB = ipTypeB.value;
            if (typeB === 'IPv4') {
                ipAddrB.placeholder = 'e.g. 192.168.1.2/24';
                ipAddrB.disabled = false;
                ipAddrB.classList.remove('disabled');
            } else if (typeB === 'IPv6') {
                ipAddrB.placeholder = 'e.g. 2001:db8::2/64';
                ipAddrB.disabled = false;
                ipAddrB.classList.remove('disabled');
            } else {
                ipAddrB.placeholder = 'N/A for L2 Service';
                ipAddrB.value = '';
                ipAddrB.disabled = true;
                ipAddrB.classList.add('disabled');
                ipAddrB.classList.remove('invalid', 'valid');
            }
        }
    }

    /**
     * Populate Models dropdown based on selected Category
     * @param {string} selectId - ID of the select element
     * @param {string} category - Category name (DNAAS, NC-AI, SA, CL)
     */
    populateModelsForCategory(selectId, category) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        select.innerHTML = '<option value="">--</option>';
        
        if (!category) return;
        
        const platforms = this.editor.driveNetsPlatforms || {};
        const categoryData = platforms[category];
        if (!categoryData || !categoryData.platforms) {
            console.warn(`No platforms found for category: ${category}`);
            return;
        }
        
        categoryData.platforms.forEach(platform => {
            const option = document.createElement('option');
            option.value = platform.official;
            option.textContent = platform.displayName || platform.official;
            select.appendChild(option);
        });
        
        // Clear the interface dropdown since model changed
        const side = selectId.includes('-a') ? 'a' : 'b';
        const interfaceSelect = document.getElementById(`lt-interface-${side}`);
        if (interfaceSelect) {
            interfaceSelect.innerHTML = '<option value="">--</option>';
        }
    }

    /**
     * Validate IP address field with visual feedback
     * @param {string} fieldId - ID of the field to validate
     * @param {string} ipType - 'IPv4', 'IPv6', or 'L2-Service'
     * @returns {boolean} True if valid
     */
    validateIpField(fieldId, ipType) {
        const field = document.getElementById(fieldId);
        const msgEl = document.getElementById(fieldId + '-msg');
        if (!field) return true;
        
        const value = field.value.trim();
        if (!value) {
            field.classList.remove('invalid', 'valid');
            if (msgEl) msgEl.classList.remove('show');
            return true;
        }
        
        let result;
        if (ipType === 'IPv4') {
            result = this.validateIPv4(value);
        } else if (ipType === 'IPv6') {
            result = this.validateIPv6(value);
        } else {
            // L2 service - no IP needed
            field.classList.remove('invalid', 'valid');
            if (msgEl) msgEl.classList.remove('show');
            return true;
        }
        
        if (result.valid) {
            field.classList.remove('invalid');
            field.classList.add('valid');
            if (msgEl) msgEl.classList.remove('show');
            return true;
        } else {
            field.classList.remove('valid');
            field.classList.add('invalid');
            if (msgEl) {
                msgEl.textContent = result.error;
                msgEl.classList.add('show');
            }
            return false;
        }
    }

    /**
     * Validate VLAN field with visual feedback
     * @param {string} fieldId - ID of the field to validate
     * @returns {boolean} True if valid
     */
    validateVlanField(fieldId) {
        const field = document.getElementById(fieldId);
        const msgEl = document.getElementById(fieldId + '-msg');
        if (!field) return true;
        
        const value = field.value.trim();
        if (!value) {
            field.classList.remove('invalid', 'valid');
            if (msgEl) msgEl.classList.remove('show');
            return true;
        }
        
        const numValue = parseInt(value, 10);
        if (isNaN(numValue) || numValue < 1 || numValue > 4094) {
            field.classList.remove('valid');
            field.classList.add('invalid');
            if (msgEl) {
                msgEl.textContent = 'VLAN must be 1-4094';
                msgEl.classList.add('show');
            }
            return false;
        } else {
            field.classList.remove('invalid');
            field.classList.add('valid');
            if (msgEl) msgEl.classList.remove('show');
            return true;
        }
    }

    // ========================================================================
    // INTERFACE POPULATION (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Populate interfaces based on platform model selection
     * Supports: physical interfaces, sub-interfaces, bundles, bundle sub-interfaces
     * @param {string} selectId - ID of the select element
     * @param {string} platformModel - Platform model name (e.g., 'SA-40C')
     */
    populateInterfacesForPlatform(selectId, platformModel) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        // Clear existing options
        select.innerHTML = '<option value="">--</option>';
        
        // Add "Custom" option at the top
        const customOption = document.createElement('option');
        customOption.value = '__custom__';
        customOption.textContent = '📝 Enter Custom Interface...';
        select.appendChild(customOption);
        
        if (!platformModel) return;
        
        // Find the platform category
        let category = null;
        const platforms = this.editor.driveNetsPlatforms || {};
        for (const [cat, data] of Object.entries(platforms)) {
            if (data.platforms && data.platforms.some(p => p.official === platformModel)) {
                category = cat;
                break;
            }
        }
        
        // Add Bundle Interfaces optgroup (common across all platforms)
        const bundleGroup = document.createElement('optgroup');
        bundleGroup.label = '── Bundle Interfaces ──';
        
        for (let i = 1; i <= 10; i++) {
            const opt = document.createElement('option');
            opt.value = `bundle-${i}`;
            opt.textContent = `bundle-${i}`;
            bundleGroup.appendChild(opt);
        }
        select.appendChild(bundleGroup);
        
        // Add Bundle Sub-interfaces optgroup
        const bundleSubGroup = document.createElement('optgroup');
        bundleSubGroup.label = '── Bundle Sub-interfaces ──';
        
        const bundleSubExamples = [
            'bundle-1.100', 'bundle-1.200', 'bundle-1.1000',
            'bundle-2.100', 'bundle-2.200'
        ];
        bundleSubExamples.forEach(iface => {
            const opt = document.createElement('option');
            opt.value = iface;
            opt.textContent = iface;
            bundleSubGroup.appendChild(opt);
        });
        select.appendChild(bundleSubGroup);
        
        if (!category) return;
        
        // Generate physical interfaces using the helper function
        const interfaces = this.editor.getInterfacesForPlatform ? 
            this.editor.getInterfacesForPlatform(platformModel, category) : [];
            
        if (interfaces && Array.isArray(interfaces) && interfaces.length > 0) {
            // Add Physical Interfaces optgroup
            const physicalGroup = document.createElement('optgroup');
            physicalGroup.label = '── Physical Interfaces ──';
            
            interfaces.forEach(iface => {
                const option = document.createElement('option');
                option.value = iface;
                option.textContent = iface;
                physicalGroup.appendChild(option);
            });
            select.appendChild(physicalGroup);
            
            // Add Sub-interface examples for first few physical interfaces
            const subIfaceGroup = document.createElement('optgroup');
            subIfaceGroup.label = '── Physical Sub-interfaces ──';
            
            const sampleInterfaces = interfaces.slice(0, 3);
            const commonVlans = [100, 200, 1000];
            
            sampleInterfaces.forEach(iface => {
                commonVlans.forEach(vlan => {
                    const opt = document.createElement('option');
                    opt.value = `${iface}.${vlan}`;
                    opt.textContent = `${iface}.${vlan}`;
                    subIfaceGroup.appendChild(opt);
                });
            });
            select.appendChild(subIfaceGroup);
        }
        
        // Trigger auto-save
        this.autoSave();
    }

    /**
     * Handle custom interface input when "__custom__" is selected
     * @param {string} selectId - ID of the select element
     */
    handleCustomInterfaceInput(selectId) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        const customInterface = prompt(
            'Enter interface name:\n\n' +
            'Examples:\n' +
            '• Physical: ge400-0/0/4, ge100-0/0/0\n' +
            '• Sub-interface: ge400-0/0/4.100\n' +
            '• Bundle: bundle-100\n' +
            '• Bundle Sub-interface: bundle-100.200',
            ''
        );
        
        if (customInterface && customInterface.trim()) {
            const cleanInterface = customInterface.trim();
            
            // Add the custom option to the dropdown
            const option = document.createElement('option');
            option.value = cleanInterface;
            option.textContent = cleanInterface;
            
            // Insert after first option (before Custom option)
            if (select.options.length > 1) {
                select.insertBefore(option, select.options[1]);
            } else {
                select.appendChild(option);
            }
            
            // Select the new option
            select.value = cleanInterface;
            this.autoSave();
        } else {
            // Reset to empty if cancelled
            select.value = '';
        }
    }

    // ========================================================================
    // FORM VALIDITY CHECK (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Check if all link table inputs are valid
     * @returns {Object} { valid: boolean, errors: Array }
     */
    checkLinkTableValidity() {
        let allValid = true;
        const errors = [];
        
        // Field name mapping for user-friendly error messages
        const fieldNames = {
            'link-d1-vlan-outer': 'Side A - Outer VLAN',
            'link-d1-vlan-inner': 'Side A - Inner VLAN',
            'link-d2-vlan-outer': 'Side B - Outer VLAN',
            'link-d2-vlan-inner': 'Side B - Inner VLAN',
            'link-d1-egress-outer': 'Side A - Egress Outer Tag',
            'link-d1-egress-inner': 'Side A - Egress Inner Tag',
            'link-d1-ingress-outer': 'Side A - Ingress Outer Tag',
            'link-d1-ingress-inner': 'Side A - Ingress Inner Tag',
            'link-d2-egress-outer': 'Side B - Egress Outer Tag',
            'link-d2-egress-inner': 'Side B - Egress Inner Tag',
            'link-d2-ingress-outer': 'Side B - Ingress Outer Tag',
            'link-d2-ingress-inner': 'Side B - Ingress Inner Tag',
            'link-dnaas-a-vlan-outer': 'DNaaS Side A - Outer VLAN',
            'link-dnaas-a-vlan-inner': 'DNaaS Side A - Inner VLAN',
            'link-dnaas-a-ingress-outer': 'DNaaS Side A - Ingress Outer Tag',
            'link-dnaas-a-ingress-inner': 'DNaaS Side A - Ingress Inner Tag',
            'link-dnaas-a-egress-outer': 'DNaaS Side A - Egress Outer Tag',
            'link-dnaas-a-egress-inner': 'DNaaS Side A - Egress Inner Tag',
            'link-dnaas-b-vlan-outer': 'DNaaS Side B - Outer VLAN',
            'link-dnaas-b-vlan-inner': 'DNaaS Side B - Inner VLAN',
            'link-dnaas-b-ingress-outer': 'DNaaS Side B - Ingress Outer Tag',
            'link-dnaas-b-ingress-inner': 'DNaaS Side B - Ingress Inner Tag',
            'link-dnaas-b-egress-outer': 'DNaaS Side B - Egress Outer Tag',
            'link-dnaas-b-egress-inner': 'DNaaS Side B - Egress Inner Tag',
            'link-d1-ip-address': 'Side A - IP Address',
            'link-d2-ip-address': 'Side B - IP Address'
        };
        
        // Get all VLAN inputs and validate
        const vlanInputs = [
            'link-d1-vlan-outer', 'link-d1-vlan-inner',
            'link-d2-vlan-outer', 'link-d2-vlan-inner',
            'link-d1-egress-outer', 'link-d1-egress-inner',
            'link-d1-ingress-outer', 'link-d1-ingress-inner',
            'link-d2-egress-outer', 'link-d2-egress-inner',
            'link-d2-ingress-outer', 'link-d2-ingress-inner',
            'link-dnaas-a-vlan-outer', 'link-dnaas-a-vlan-inner',
            'link-dnaas-a-ingress-outer', 'link-dnaas-a-ingress-inner',
            'link-dnaas-a-egress-outer', 'link-dnaas-a-egress-inner',
            'link-dnaas-b-vlan-outer', 'link-dnaas-b-vlan-inner',
            'link-dnaas-b-ingress-outer', 'link-dnaas-b-ingress-inner',
            'link-dnaas-b-egress-outer', 'link-dnaas-b-egress-inner'
        ];
        
        vlanInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input && input.value.trim()) {
                const result = this.validateVlanInput(input.value);
                if (!result.valid) {
                    allValid = false;
                    input.style.borderColor = '#e74c3c';
                    input.style.background = 'rgba(231,76,60,0.1)';
                    input.title = result.error;
                    errors.push({ 
                        id, 
                        fieldName: fieldNames[id] || id,
                        error: result.error,
                        value: input.value
                    });
                } else {
                    input.style.borderColor = '';
                    input.style.background = '';
                    input.title = '';
                }
            } else if (input) {
                input.style.borderColor = '';
                input.style.background = '';
                input.title = '';
            }
        });
        
        // Validate IP addresses
        const d1IpType = document.getElementById('link-d1-ip-type')?.value || '';
        const d1IpInput = document.getElementById('link-d1-ip-address');
        if (d1IpInput && d1IpType && d1IpInput.value.trim()) {
            const result = this.validateIpAddress(d1IpInput.value, d1IpType);
            if (!result.valid) {
                allValid = false;
                d1IpInput.style.borderColor = '#e74c3c';
                d1IpInput.style.background = 'rgba(231,76,60,0.1)';
                d1IpInput.title = result.error;
                errors.push({
                    id: 'link-d1-ip-address',
                    fieldName: fieldNames['link-d1-ip-address'],
                    error: result.error,
                    value: d1IpInput.value
                });
            } else {
                d1IpInput.style.borderColor = '';
                d1IpInput.style.background = '';
                d1IpInput.title = '';
            }
        } else if (d1IpInput) {
            d1IpInput.style.borderColor = '';
            d1IpInput.style.background = '';
            d1IpInput.title = '';
        }
        
        const d2IpType = document.getElementById('link-d2-ip-type')?.value || '';
        const d2IpInput = document.getElementById('link-d2-ip-address');
        if (d2IpInput && d2IpType && d2IpInput.value.trim()) {
            const result = this.validateIpAddress(d2IpInput.value, d2IpType);
            if (!result.valid) {
                allValid = false;
                d2IpInput.style.borderColor = '#e74c3c';
                d2IpInput.style.background = 'rgba(231,76,60,0.1)';
                d2IpInput.title = result.error;
                errors.push({
                    id: 'link-d2-ip-address',
                    fieldName: fieldNames['link-d2-ip-address'],
                    error: result.error,
                    value: d2IpInput.value
                });
            } else {
                d2IpInput.style.borderColor = '';
                d2IpInput.style.background = '';
                d2IpInput.title = '';
            }
        } else if (d2IpInput) {
            d2IpInput.style.borderColor = '';
            d2IpInput.style.background = '';
            d2IpInput.title = '';
        }
        
        return { valid: allValid, errors };
    }

    // ========================================================================
    // VALIDATION DISPLAY (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Format validation errors for display
     * @param {Array} errors - Array of error objects
     * @returns {string} Formatted error string
     */
    formatValidationErrors(errors) {
        if (!errors || errors.length === 0) return '';
        return errors.map(e => `• ${e.fieldName}: "${e.value}" - ${e.error}`).join('\n');
    }

    /**
     * Show validation error toast notification
     * @param {Array} errors - Array of error objects
     */
    showValidationErrorToast(errors) {
        // Remove any existing toast
        const existingToast = document.getElementById('validation-error-toast');
        if (existingToast) existingToast.remove();
        
        // Create toast element
        const toast = document.createElement('div');
        toast.id = 'validation-error-toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 100000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 500px;
            animation: slideDown 0.3s ease;
        `;
        
        // Add animation keyframes if not exists
        if (!document.getElementById('toast-animation-style')) {
            const style = document.createElement('style');
            style.id = 'toast-animation-style';
            style.textContent = `
                @keyframes slideDown {
                    from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
                    to { transform: translateX(-50%) translateY(0); opacity: 1; }
                }
                @keyframes slideUp {
                    from { transform: translateX(-50%) translateY(0); opacity: 1; }
                    to { transform: translateX(-50%) translateY(-100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        const errorList = errors.map(e => 
            `<div style="margin: 4px 0; padding-left: 15px; text-indent: -15px;">
                <span style="color: #ffd700;">⚠</span> <strong>${e.fieldName}</strong>: "${e.value}" - ${e.error}
            </div>`
        ).join('');
        
        toast.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">❌</span>
                <div>
                    <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px;">
                        Invalid Fields - Changes Not Saved
                    </div>
                    <div style="font-size: 12px; opacity: 0.95;">
                        ${errorList}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideUp 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
        
        // Click to dismiss
        toast.addEventListener('click', () => {
            toast.style.animation = 'slideUp 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        });
    }

    /**
     * Copy Link Table as Markdown
     */
    copyAsMarkdown() {
        const link = this.currentLink || this.editor.editingLink;
        if (!link) return;
        
        const device1Name = document.getElementById('link-device1-name')?.textContent || 'Side A';
        const device2Name = document.getElementById('link-device2-name')?.textContent || 'Side B';
        
        // Build markdown table
        let markdown = `# Link Connection: ${device1Name} ↔ ${device2Name}\n\n`;
        markdown += `| Property | ${device1Name} | ${device2Name} |\n`;
        markdown += `|----------|----------|----------|\n`;
        
        // Platform tab
        markdown += `| Platform Category | ${link.device1PlatformCategory || '-'} | ${link.device2PlatformCategory || '-'} |\n`;
        markdown += `| Platform Model | ${link.device1Platform || '-'} | ${link.device2Platform || '-'} |\n`;
        
        // Interface tab
        markdown += `| Interface | ${link.device1Interface || '-'} | ${link.device2Interface || '-'} |\n`;
        markdown += `| Transceiver | ${link.device1Transceiver || '-'} | ${link.device2Transceiver || '-'} |\n`;
        
        // VLAN/IP tab
        markdown += `| IP Type | ${link.device1IpType || '-'} | ${link.device2IpType || '-'} |\n`;
        markdown += `| IP Address | ${link.device1IpAddress || '-'} | ${link.device2IpAddress || '-'} |\n`;
        markdown += `| VLAN TPID | ${link.device1VlanTpid || '-'} | ${link.device2VlanTpid || '-'} |\n`;
        markdown += `| Outer Tag | ${link.device1OuterTag || '-'} | ${link.device2OuterTag || '-'} |\n`;
        markdown += `| Inner Tag | ${link.device1InnerTag || '-'} | ${link.device2InnerTag || '-'} |\n`;
        
        // Advanced tab
        markdown += `| Ingress Action | ${link.device1IngressAction || '-'} | ${link.device2IngressAction || '-'} |\n`;
        markdown += `| Egress Action | ${link.device1EgressAction || '-'} | ${link.device2EgressAction || '-'} |\n`;
        markdown += `| DNaaS VLAN | ${link.device1DnaasVlan || '-'} | ${link.device2DnaasVlan || '-'} |\n`;
        
        // Copy to clipboard
        navigator.clipboard.writeText(markdown).then(() => {
            // Show success toast (delegate to editor)
            if (typeof this.editor.showToast === 'function') {
                this.editor.showToast('Copied as Markdown!', 'success');
            }
        }).catch(err => {
            console.error('[LinkEditorModal] Failed to copy:', err);
            if (typeof this.editor.showToast === 'function') {
                this.editor.showToast('Failed to copy', 'error');
            }
        });
    }

    // ========================================================================
    // MODAL UI SETUP (MIGRATED FROM topology.js)
    // ========================================================================

    /**
     * Set up modal dragging via header
     * @param {HTMLElement} modalContent - Modal content element
     */
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

    /**
     * Set up modal edge/corner resizing
     * @param {HTMLElement} modalContent - Modal content element
     */
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
        this.setupResponsiveColumns(modalContent);
    }

    /**
     * Set up ResizeObserver to show/hide extra columns based on modal width
     * @param {HTMLElement} modalContent - Modal content element
     */
    setupResponsiveColumns(modalContent) {
        if (modalContent._responsiveColumnsSetup) return;
        modalContent._responsiveColumnsSetup = true;
        
        const WIDE_THRESHOLD = 750; // Show extra columns when width > 750px
        
        // Update width data attribute
        const updateWidthMode = () => {
            const width = modalContent.offsetWidth;
            const mode = width > WIDE_THRESHOLD ? 'wide' : 'narrow';
            modalContent.dataset.width = mode;
        };
        
        // Initial check
        updateWidthMode();
        
        // Set up ResizeObserver
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver((entries) => {
                for (const entry of entries) {
                    updateWidthMode();
                }
            });
            resizeObserver.observe(modalContent);
            
            // Store observer for cleanup
            modalContent._resizeObserver = resizeObserver;
        } else {
            // Fallback: Check on window resize
            window.addEventListener('resize', updateWidthMode);
        }
    }
}

// ============================================================================
// EXPORT
// ============================================================================

window.LinkEditorModal = LinkEditorModal;

window.createLinkEditorModal = function(editor) {
    return new LinkEditorModal(editor);
};

console.log('[topology-link-editor.js] LinkEditorModal wrapper loaded');
