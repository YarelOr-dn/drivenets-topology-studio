/**
 * topology-link-details.js - Link Details Modal and Validation
 * 
 * Extracted from topology.js for modular architecture.
 * All methods receive 'editor' as first parameter instead of using 'this'.
 */

'use strict';

window.LinkDetailsHandlers = {
    showLinkEditor(editor, link) {
        if (!link || (link.type !== 'link' && link.type !== 'unbound')) return;
        
        editor.editingLink = link;
        
        // ENHANCED: If this is part of a BUL, store all links in the chain for unified editing
        if (link.type === 'unbound' && (link.mergedWith || link.mergedInto)) {
            editor.editingBulLinks = editor.getAllMergedLinks(link);
            if (editor.debugger) {
                editor.debugger.logInfo(`🔗 Editing BUL with ${editor.editingBulLinks.length} links`);
            }
        } else {
            editor.editingBulLinks = null;
        }
        
        // Update modal title to indicate BUL editing
        const modalHeader = document.querySelector('#link-editor-modal .modal-header h2');
        if (modalHeader) {
            if (editor.editingBulLinks && editor.editingBulLinks.length > 1) {
                modalHeader.innerHTML = `${appIcon('link')} BUL Properties (${editor.editingBulLinks.length} links)`;
            } else if (link.type === 'unbound') {
                modalHeader.innerHTML = `${appIcon('ruler')} UL Properties`;
            } else {
                modalHeader.innerHTML = `${appIcon('ruler')} Link Properties`;
            }
        }
        
        // Set current values - with null checks
        const editorLinkColor = document.getElementById('editor-link-color');
        const editorLinkWidth = document.getElementById('editor-link-width');
        const editorLinkWidthValue = document.getElementById('editor-link-width-value');
        const editorLinkStyle = document.getElementById('editor-link-style');
        const editorLinkCurve = document.getElementById('editor-link-curve');
        
        if (editorLinkColor) editorLinkColor.value = link.color || '#3498db';
        const editorWidthValue = link.width !== undefined ? link.width : editor.currentLinkWidth;
        if (editorLinkWidth) editorLinkWidth.value = editorWidthValue;
        if (editorLinkWidthValue) editorLinkWidthValue.textContent = editorWidthValue;
        if (editorLinkStyle) editorLinkStyle.value = link.style || 'solid';
        if (editorLinkCurve) editorLinkCurve.checked = link.curveOverride !== undefined ? link.curveOverride : editor.linkCurveMode;
        
        // Set curve mode dropdown (per-link override)
        const editorLinkCurveMode = document.getElementById('editor-link-curve-mode');
        if (editorLinkCurveMode) {
            editorLinkCurveMode.value = link.curveMode || '';
        }
        
        // Set curve magnitude (use link-specific or global)
        const curveMagnitude = link.curveMagnitude !== undefined ? link.curveMagnitude : editor.magneticFieldStrength;
        const editorLinkCurveMagnitude = document.getElementById('editor-link-curve-magnitude');
        const editorLinkCurveMagnitudeValue = document.getElementById('editor-link-curve-magnitude-value');
        if (editorLinkCurveMagnitude) editorLinkCurveMagnitude.value = curveMagnitude;
        if (editorLinkCurveMagnitudeValue) editorLinkCurveMagnitudeValue.textContent = curveMagnitude;
        
        // Show/hide curve magnitude section based on curve enabled state
        const curveEnabled = link.curveOverride !== undefined ? link.curveOverride : editor.linkCurveMode;
        const magnitudeSection = document.getElementById('editor-curve-magnitude-section');
        if (magnitudeSection) {
            magnitudeSection.style.display = curveEnabled ? 'block' : 'none';
        }
        
        // Show/hide "Keep Current Curve" section (UL/BUL only)
        const keepCurveSection = document.getElementById('editor-keep-curve-section');
        const keepCurveCheckbox = document.getElementById('editor-link-keep-curve');
        if (keepCurveSection && keepCurveCheckbox) {
            // Only show for unbound links when curve is enabled
            if (link.type === 'unbound' && curveEnabled) {
                keepCurveSection.style.display = 'block';
                keepCurveCheckbox.checked = link.keepCurve || false;
            } else {
                keepCurveSection.style.display = 'none';
            }
        }
        
        // Update recent colors display
        editor.updateRecentColorsUI();
        
        const modal = document.getElementById('link-editor-modal');
        if (modal) {
            // CRITICAL: Reset modal position to centered before showing
            const modalContent = modal.querySelector('.modal-content');
            if (modalContent) {
                modalContent.style.position = 'relative';
                modalContent.style.left = '';
                modalContent.style.top = '';
                modalContent.style.transform = '';
                modalContent.style.margin = '';
            }
            modal.classList.add('show');
        }
    },

    updateLinkEditorProperty(editor, property, value) {
        if (!editor.editingLink) return;
        editor.saveState();
        
        // Helper to apply property to a single link
        const applyToLink = (link) => {
            link[property] = value;
            
            // CRITICAL FIX: When setting curveMode, also update curveOverride for drawing code
            if (property === 'curveMode') {
                if (value === 'off' || value === null || value === '') {
                    // Off or Global: delete curveOverride so it uses global setting
                    delete link.curveOverride;
                    if (value === 'off') {
                        link.curveOverride = false;
                    }
                } else if (value === 'auto' || value === 'manual') {
                    // Auto or Manual: enable curving
                    link.curveOverride = true;
                }
            }
            
            // When setting curveOverride directly, ensure it matches
            if (property === 'curveOverride') {
                if (value === false) {
                    link.curveMode = 'off';
                } else if (value === true && !link.curveMode) {
                    link.curveMode = 'auto';
                }
            }
        };
        
        // ENHANCED: If editing a BUL, apply changes to ALL links in the chain
        if (editor.editingBulLinks && editor.editingBulLinks.length > 0) {
            editor.editingBulLinks.forEach(link => applyToLink(link));
            if (editor.debugger) {
                editor.debugger.logInfo(`🔗 Applied ${property}=${value} to ${editor.editingBulLinks.length} BUL links`);
                }
            } else {
            // Single link editing
            applyToLink(editor.editingLink);
        }
        
        // Track color changes for recent colors
        if (property === 'color') {
            editor.addRecentColor(value);
        }
        
        editor.draw();
    },

    handleKeepCurveChange(editor, enabled) {
        if (!editor.editingLink || editor.editingLink.type !== 'unbound') return;
        
        editor.saveState();
        
        // Get all links to update (single link or entire BUL chain)
        const linksToUpdate = editor.editingBulLinks && editor.editingBulLinks.length > 0 
            ? editor.editingBulLinks 
            : [editor.editingLink];
        
        linksToUpdate.forEach(link => {
            if (enabled) {
                // Save current control points
                link.keepCurve = true;
                if (link._cp1 && link._cp2) {
                    link.savedCp1 = { x: link._cp1.x, y: link._cp1.y };
                    link.savedCp2 = { x: link._cp2.x, y: link._cp2.y };
                    // Also save the relative curve shape
                    const midX = (link.start.x + link.end.x) / 2;
                    const midY = (link.start.y + link.end.y) / 2;
                    const linkLength = Math.sqrt(
                        Math.pow(link.end.x - link.start.x, 2) + 
                        Math.pow(link.end.y - link.start.y, 2)
                    );
                    // Store curve offset relative to link length
                    link.savedCurveOffset = {
                        cp1OffsetX: (link._cp1.x - midX) / (linkLength || 1),
                        cp1OffsetY: (link._cp1.y - midY) / (linkLength || 1),
                        cp2OffsetX: (link._cp2.x - midX) / (linkLength || 1),
                        cp2OffsetY: (link._cp2.y - midY) / (linkLength || 1)
                    };
                }
            } else {
                // Clear saved control points
                link.keepCurve = false;
                delete link.savedCp1;
                delete link.savedCp2;
                delete link.savedCurveOffset;
            }
        });
        
        if (editor.debugger) {
            editor.debugger.logInfo(`🔒 Keep Curve ${enabled ? 'ENABLED' : 'DISABLED'} for ${linksToUpdate.length} link(s)`);
        }
        
        editor.draw();
    },

    showLinkDetails(editor, link) {
        if (!link || (link.type !== 'link' && link.type !== 'unbound')) return;
        
        editor.editingLink = link;
        
        // ENHANCED: If this is part of a BUL, store all links in the chain for unified editing
        if (link.type === 'unbound' && (link.mergedWith || link.mergedInto)) {
            editor.editingBulLinks = editor.getAllMergedLinks(link);
            if (editor.debugger) {
                editor.debugger.logInfo(`🔗 Showing BUL details with ${editor.editingBulLinks.length} links`);
            }
        } else {
            editor.editingBulLinks = null;
        }
        
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
        const connectedDevicesInfo = editor.getAllConnectedDevices(link);
        
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
            device1 = link.device1 ? editor.objects.find(obj => obj.id === link.device1) : null;
            device2 = link.device2 ? editor.objects.find(obj => obj.id === link.device2) : null;
        }
        
        // Find interface labels for this link or BUL chain
        // Check all links in the BUL chain for interface labels
        const allLinksInChain = editor.getAllMergedLinks(link);
        const allLinkIds = allLinksInChain.map(l => l.id);
        
        const interfaceTexts = editor.objects.filter(obj => 
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
                const textLink = editor.objects.find(l => l.id === t.linkId);
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
                const textLink = editor.objects.find(l => l.id === t.linkId);
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
        const device1InterfaceName = device1Interface ? device1Interface.text : '';
        const device2InterfaceName = device2Interface ? device2Interface.text : '';
        
        // Update device header
        const d1NameEl = document.getElementById('link-device1-name');
        const d2NameEl = document.getElementById('link-device2-name');
        if (d1NameEl) d1NameEl.textContent = device1Name;
        if (d2NameEl) d2NameEl.textContent = device2Name;
        
        // Initialize all link properties with defaults
        const initProps = [
            'device1PlatformCategory', 'device2PlatformCategory',
            'device1Platform', 'device2Platform',
            'device1Interface', 'device2Interface',
            'device1Transceiver', 'device2Transceiver',
            'device1IpType', 'device2IpType',
            'device1IpAddress', 'device2IpAddress',
            'device1VlanTpid', 'device2VlanTpid',
            'device1OuterTag', 'device2OuterTag',
            'device1InnerTag', 'device2InnerTag',
            'device1IngressAction', 'device2IngressAction',
            'device1EgressAction', 'device2EgressAction',
            'device1DnaasVlan', 'device2DnaasVlan'
        ];
        initProps.forEach(prop => {
            if (link[prop] === undefined) link[prop] = '';
        });
        
        // Populate the new tabbed interface fields
        editor.populateLinkTableFields(link, device1InterfaceName, device2InterfaceName);
        
        // Show the modal
        const modal = document.getElementById('link-details-modal');
        modal.classList.add('show');
        
        // Restore saved modal size and position if available
        const modalContent = modal.querySelector('.link-table-modal');
        if (modalContent) {
            const savedSize = localStorage.getItem('link_table_modal_size');
            if (savedSize) {
                try {
                    const { width, height } = JSON.parse(savedSize);
                    if (width && height) {
                        modalContent.style.width = width + 'px';
                        modalContent.style.height = height + 'px';
                    }
                } catch (e) {
                    console.warn('Failed to restore modal size:', e);
                }
            }
            
            // Restore saved position (with bounds check)
            const savedPos = localStorage.getItem('link_table_modal_position');
            if (savedPos) {
                try {
                    let { x, y } = JSON.parse(savedPos);
                    
                    // Get modal dimensions
                    const rect = modalContent.getBoundingClientRect();
                    const modalWidth = rect.width || 680;
                    const modalHeight = rect.height || 500;
                    
                    // Ensure modal is fully visible in viewport
                    x = Math.max(0, Math.min(x, window.innerWidth - modalWidth));
                    y = Math.max(0, Math.min(y, window.innerHeight - modalHeight));
                    
                    modalContent.style.position = 'fixed';
                    modalContent.style.left = x + 'px';
                    modalContent.style.top = y + 'px';
                    modalContent.style.transform = 'none';
                } catch (e) {
                    console.warn('Failed to restore modal position:', e);
                }
            } else {
                // Center the modal if no saved position
                modalContent.style.position = 'fixed';
                const rect = modalContent.getBoundingClientRect();
                const x = Math.max(0, (window.innerWidth - rect.width) / 2);
                const y = Math.max(0, (window.innerHeight - rect.height) / 2);
                modalContent.style.left = x + 'px';
                modalContent.style.top = y + 'px';
                modalContent.style.transform = 'none';
            }
            
            // Set up resize observer to save size on change
            if (!editor._modalResizeObserver) {
                editor._modalResizeObserver = new ResizeObserver((entries) => {
                    for (const entry of entries) {
                        const { width, height } = entry.contentRect;
                        if (width > 0 && height > 0) {
                            localStorage.setItem('link_table_modal_size', JSON.stringify({ width, height }));
                        }
                    }
                });
            }
            editor._modalResizeObserver.observe(modalContent);
            
            // Set up header dragging (delegate to linkEditor module if available)
            if (editor.linkEditor && typeof editor.linkEditor.setupModalDragging === 'function') {
                editor.linkEditor.setupModalDragging(modalContent);
            } else {
                editor.setupModalDragging(modalContent);
            }
            
            // Set up edge/corner resizing (delegate to linkEditor module if available)
            if (editor.linkEditor && typeof editor.linkEditor.setupModalResize === 'function') {
                editor.linkEditor.setupModalResize(modalContent);
            } else {
                editor.setupModalResize(modalContent);
            }
        }
        
        // Set up real-time validation
        editor.setupLinkTableValidation();
        
        // Try to load interfaces from device configs (async, non-blocking)
        editor.loadInterfacesFromDeviceConfigs().catch(err => {
            console.warn('Failed to load interfaces from configs:', err);
        });
    },

    validateVlanInput(editor, value) {
        // Delegate to linkEditor module if available
        if (editor.linkEditor && typeof editor.linkEditor.validateVlanInput === 'function') {
            return editor.linkEditor.validateVlanInput(value);
        }
        
        // Fallback: original implementation
        if (!value || value.trim() === '') return { valid: true, value: '' };
        
        const trimmed = value.trim();
        const parts = trimmed.split(',').map(p => p.trim()).filter(p => p);
        
        for (const part of parts) {
            if (part.includes('-')) {
                const rangeParts = part.split('-').map(p => p.trim());
                if (rangeParts.length !== 2) return { valid: false, error: 'Invalid range format' };
                const start = parseInt(rangeParts[0], 10);
                const end = parseInt(rangeParts[1], 10);
                if (isNaN(start) || isNaN(end)) return { valid: false, error: 'Range must be numbers' };
                if (start < 1 || start > 4096 || end < 1 || end > 4096) return { valid: false, error: 'VLAN must be 1-4096' };
                if (start > end) return { valid: false, error: 'Invalid range (start > end)' };
            } else {
                const num = parseInt(part, 10);
                if (isNaN(num) || part !== String(num)) return { valid: false, error: 'Must be a number' };
                if (num < 1 || num > 4096) return { valid: false, error: 'VLAN must be 1-4096' };
            }
        }
        return { valid: true, value: trimmed };
    },

    validateIPv4(editor, value) {
        // Delegate to linkEditor module if available
        if (editor.linkEditor && typeof editor.linkEditor.validateIPv4 === 'function') {
            return editor.linkEditor.validateIPv4(value);
        }
        
        // Fallback: original implementation
        if (!value || value.trim() === '') return { valid: true, value: '' };
        const trimmed = value.trim();
        let ip = trimmed;
        if (trimmed.includes('/')) {
            const parts = trimmed.split('/');
            ip = parts[0];
            const prefix = parseInt(parts[1], 10);
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
    },

    validateIPv6(editor, value) {
        // Delegate to linkEditor module if available
        if (editor.linkEditor && typeof editor.linkEditor.validateIPv6 === 'function') {
            return editor.linkEditor.validateIPv6(value);
        }
        
        // Fallback: original implementation
        if (!value || value.trim() === '') return { valid: true, value: '' };
        const trimmed = value.trim();
        let ip = trimmed;
        if (trimmed.includes('/')) {
            const lastSlash = trimmed.lastIndexOf('/');
            ip = trimmed.substring(0, lastSlash);
            const prefix = parseInt(trimmed.substring(lastSlash + 1), 10);
            if (isNaN(prefix) || prefix < 0 || prefix > 128) {
                return { valid: false, error: 'Prefix must be 0-128' };
            }
        }
        const ipv6Pattern = /^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]+|::(ffff(:0{1,4})?:)?((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\.){3}(25[0-5]|(2[0-4]|1?[0-9])?[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\.){3}(25[0-5]|(2[0-4]|1?[0-9])?[0-9]))$/;
        if (!ipv6Pattern.test(ip)) {
            return { valid: false, error: 'Invalid IPv6 format' };
        }
        return { valid: true, value: trimmed };
    },

    validateVlanConfiguration(editor) {
        const validationDiv = document.getElementById('link-vlan-validation');
        if (!validationDiv) return;
        
        let issues = [];
        let isValid = true;
        
        // Get calculated stacks
        const stackToB = editor.calculateEgressStack('toB');
        const stackToA = editor.calculateEgressStack('toA');
        
        // Get interface VLAN-ID/Tags
        const d1VlanOuter = document.getElementById('link-d1-vlan-outer')?.value.trim() || '';
        const d1VlanInner = document.getElementById('link-d1-vlan-inner')?.value.trim() || '';
        const d2VlanOuter = document.getElementById('link-d2-vlan-outer')?.value.trim() || '';
        const d2VlanInner = document.getElementById('link-d2-vlan-inner')?.value.trim() || '';
        
        // Get DNaaS VLAN-ID/Tags
        const dnaasAVlanOuter = document.getElementById('link-dnaas-a-vlan-outer')?.value.trim() || '';
        const dnaasAVlanInner = document.getElementById('link-dnaas-a-vlan-inner')?.value.trim() || '';
        const dnaasBVlanOuter = document.getElementById('link-dnaas-b-vlan-outer')?.value.trim() || '';
        const dnaasBVlanInner = document.getElementById('link-dnaas-b-vlan-inner')?.value.trim() || '';
        
        // Format VLAN stacks for comparison
        const formatStack = (outer, inner) => {
            if (outer && inner) return `${outer}.${inner}`;
            if (outer) return outer;
            if (inner) return inner;
            return '(empty)';
        };
        
        const d1Stack = formatStack(d1VlanOuter, d1VlanInner);
        const d2Stack = formatStack(d2VlanOuter, d2VlanInner);
        const dnaasAStack = formatStack(dnaasAVlanOuter, dnaasAVlanInner);
        const dnaasBStack = formatStack(dnaasBVlanOuter, dnaasBVlanInner);
        
        // Validation 1: Check if traffic to Side B matches Side B interface expectation
        // Stack arriving at Side B should match what Side B expects (or be empty if no expectation)
        if (d2VlanOuter || d2VlanInner) {
            if (stackToB !== d2Stack && stackToB !== '(empty)') {
                isValid = false;
                issues.push(`A→B: Arriving stack "${stackToB}" ≠ Side B expected "${d2Stack}"`);
            }
        }
        
        // Validation 2: Check if traffic to Side A matches Side A interface expectation
        if (d1VlanOuter || d1VlanInner) {
            if (stackToA !== d1Stack && stackToA !== '(empty)') {
                isValid = false;
                issues.push(`B→A: Arriving stack "${stackToA}" ≠ Side A expected "${d1Stack}"`);
            }
        }
        
        // Validation 3: Check DNaaS VLAN consistency (optional - only if DNaaS VLANs are specified)
        if (dnaasAVlanOuter || dnaasAVlanInner || dnaasBVlanOuter || dnaasBVlanInner) {
            // If DNaaS VLANs are specified, they should be consistent across the cloud
            // (This is a soft warning, not a hard error)
            if (dnaasAStack !== dnaasBStack && dnaasAStack !== '(empty)' && dnaasBStack !== '(empty)') {
                issues.push(`⚠️ DNaaS VLAN mismatch: Side A "${dnaasAStack}" ≠ Side B "${dnaasBStack}"`);
            }
        }
        
        // Update validation display
        if (isValid && issues.length === 0) {
            validationDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: linear-gradient(135deg, rgba(39,174,96,0.15), rgba(46,204,113,0.15)); border-radius: 6px; border: 1px solid rgba(39,174,96,0.3);">
                    <span style="font-size: 18px;">✅</span>
                    <span style="color: #27ae60; font-weight: 600; font-size: 12px;">VLAN Configuration Valid</span>
                    <span style="color: #2ecc71; font-size: 10px; opacity: 0.8;">No mismatches detected</span>
                </div>
            `;
        } else {
            const issueItems = issues.map(issue => 
                `<div style="display: flex; align-items: flex-start; gap: 4px; padding: 2px 0;">
                    <span style="color: ${issue.startsWith('⚠️') ? '#FF7A33' : '#e74c3c'};">•</span>
                    <span style="font-size: 10px; color: ${issue.startsWith('⚠️') ? '#FF7A33' : '#e74c3c'};">${issue}</span>
                </div>`
            ).join('');
            
            validationDiv.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 4px; padding: 8px 12px; background: linear-gradient(135deg, rgba(231,76,60,0.15), rgba(192,57,43,0.15)); border-radius: 6px; border: 1px solid rgba(231,76,60,0.3);">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 18px;">❌</span>
                        <span style="color: #e74c3c; font-weight: 600; font-size: 12px;">VLAN Configuration ${isValid ? 'Warning' : 'Invalid'}</span>
                    </div>
                    <div style="margin-left: 26px;">
                        ${issueItems}
                    </div>
                </div>
            `;
        }
    },

    setupVlanCalculationListeners(editor) {
        // Get all input fields - VLAN outer/inner
        const d1VlanOuterInput = document.getElementById('link-d1-vlan-outer');
        const d1VlanInnerInput = document.getElementById('link-d1-vlan-inner');
        const d2VlanOuterInput = document.getElementById('link-d2-vlan-outer');
        const d2VlanInnerInput = document.getElementById('link-d2-vlan-inner');
        
        // Side A device manipulation fields
        const d1EgressAction = document.getElementById('link-d1-egress-action');
        const d1EgressOuter = document.getElementById('link-d1-egress-outer');
        const d1EgressInner = document.getElementById('link-d1-egress-inner');
        const d1IngressAction = document.getElementById('link-d1-ingress-action');
        const d1IngressOuter = document.getElementById('link-d1-ingress-outer');
        const d1IngressInner = document.getElementById('link-d1-ingress-inner');
        
        // Side B device manipulation fields
        const d2EgressAction = document.getElementById('link-d2-egress-action');
        const d2EgressOuter = document.getElementById('link-d2-egress-outer');
        const d2EgressInner = document.getElementById('link-d2-egress-inner');
        const d2IngressAction = document.getElementById('link-d2-ingress-action');
        const d2IngressOuter = document.getElementById('link-d2-ingress-outer');
        const d2IngressInner = document.getElementById('link-d2-ingress-inner');
        
        // DNaaS Side A manipulation fields
        const dnaasAIngressAction = document.getElementById('link-dnaas-a-ingress-action');
        const dnaasAIngressOuter = document.getElementById('link-dnaas-a-ingress-outer');
        const dnaasAIngressInner = document.getElementById('link-dnaas-a-ingress-inner');
        const dnaasAEgressAction = document.getElementById('link-dnaas-a-egress-action');
        const dnaasAEgressOuter = document.getElementById('link-dnaas-a-egress-outer');
        const dnaasAEgressInner = document.getElementById('link-dnaas-a-egress-inner');
        
        // DNaaS Side B manipulation fields
        const dnaasBIngressAction = document.getElementById('link-dnaas-b-ingress-action');
        const dnaasBIngressOuter = document.getElementById('link-dnaas-b-ingress-outer');
        const dnaasBIngressInner = document.getElementById('link-dnaas-b-ingress-inner');
        const dnaasBEgressAction = document.getElementById('link-dnaas-b-egress-action');
        const dnaasBEgressOuter = document.getElementById('link-dnaas-b-egress-outer');
        const dnaasBEgressInner = document.getElementById('link-dnaas-b-egress-inner');
        
        // Combined update function
        const updateFn = () => {
            editor.updateDnaasVlanFields();
            editor.updateCalculatedStacks();
        };
        
        // Attach input listeners to all text input fields
        [d1VlanOuterInput, d1VlanInnerInput, d2VlanOuterInput, d2VlanInnerInput,
         d1EgressOuter, d1EgressInner, d1IngressOuter, d1IngressInner,
         d2EgressOuter, d2EgressInner, d2IngressOuter, d2IngressInner,
         dnaasAIngressOuter, dnaasAIngressInner, dnaasAEgressOuter, dnaasAEgressInner,
         dnaasBIngressOuter, dnaasBIngressInner, dnaasBEgressOuter, dnaasBEgressInner
        ].forEach(el => {
            if (el) el.addEventListener('input', updateFn);
        });
        
        // Attach change listeners to all select fields
        [d1EgressAction, d1IngressAction, d2EgressAction, d2IngressAction,
         dnaasAIngressAction, dnaasAEgressAction, dnaasBIngressAction, dnaasBEgressAction
        ].forEach(el => {
            if (el) el.addEventListener('change', updateFn);
        });
        
        // Initial calculation
        updateFn();
    },

    async autoFillFromLldp(editor, link) {
        if (!link) return false;
        const device1 = editor.objects.find(d => d.id === link.device1);
        const device2 = editor.objects.find(d => d.id === link.device2);
        if (!device1?.label || !device2?.label) return false;

        const name1 = device1.label.trim();
        const name2 = device2.label.trim();
        let filled = false;

        try {
            const sshHost1 = device1.sshConfig?.host || device1.sshConfig?.hostBackup || '';
            const url = new URL(`/api/dnaas/device/${encodeURIComponent(name1)}/lldp`, window.location.origin);
            if (sshHost1 && /^\d+\.\d+\.\d+\.\d+$/.test(sshHost1)) {
                url.searchParams.set('ssh_host', sshHost1);
            }
            const resp = await fetch(url.toString());
            if (!resp.ok) return false;
            const data = await resp.json();
            const neighbors = data.neighbors || data.lldp_neighbors || [];

            for (const n of neighbors) {
                const nbrName = (n.neighbor || n.remote_device || '').trim();
                if (nbrName.toLowerCase() === name2.toLowerCase()) {
                    if (n.interface && !link.device1Interface) {
                        link.device1Interface = n.interface;
                        filled = true;
                    }
                    if ((n.remote_port || n.remote_interface) && !link.device2Interface) {
                        link.device2Interface = n.remote_port || n.remote_interface;
                        filled = true;
                    }
                    break;
                }
            }

            if (filled) {
                const d1Input = document.getElementById('lt-d1-interface');
                const d2Input = document.getElementById('lt-d2-interface');
                if (d1Input && link.device1Interface) {
                    d1Input.value = link.device1Interface;
                    d1Input.style.background = 'rgba(0, 102, 250, 0.15)';
                    d1Input.title = 'Auto-filled from LLDP';
                }
                if (d2Input && link.device2Interface) {
                    d2Input.value = link.device2Interface;
                    d2Input.style.background = 'rgba(0, 102, 250, 0.15)';
                    d2Input.title = 'Auto-filled from LLDP';
                }
                if (editor.debugger) {
                    editor.debugger.logSuccess(`LLDP auto-fill: ${name1} [${link.device1Interface}] <-> ${name2} [${link.device2Interface}]`);
                }
            }
        } catch (err) {
            console.warn('LLDP auto-fill failed:', err);
        }
        return filled;
    }
};

console.log('[topology-link-details.js] LinkDetailsHandlers loaded');
