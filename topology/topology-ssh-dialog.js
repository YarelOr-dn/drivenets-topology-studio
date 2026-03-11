// ============================================================================
// TOPOLOGY SSH ADDRESS DIALOG MODULE
// ============================================================================
// Handles the SSH configuration dialog for devices.
// Extracted from topology.js to reduce main file size (~410 lines).
//
// Usage:
//   showSSHAddressDialog(editor, device);
// ============================================================================

/**
 * Show SSH address configuration dialog
 * @param {TopologyEditor} editor - The editor instance
 * @param {object} device - The device object
 */
function showSSHAddressDialog(editor, device) {
    // Remove any existing dialog
    const existing = document.getElementById('ssh-address-dialog');
    if (existing) existing.remove();
    
    // Get current SSH settings (support both old format and new format)
    const sshConfig = device.sshConfig || {};
    const currentHost = sshConfig.host || device.deviceAddress || '';
    const currentUser = sshConfig.user || 'dnroot';
    const currentPass = sshConfig.password || '';
    
    const rect = editor.canvas.getBoundingClientRect();
    const deviceScreenX = device.x * editor.zoom + editor.panOffset.x + rect.left;
    const deviceScreenY = device.y * editor.zoom + editor.panOffset.y + rect.top;
    const deviceRadius = (device.radius || 30) * editor.zoom;
    
    // Liquid Glass styling
    const isDarkMode = editor.darkMode;
    const glassBg = isDarkMode 
        ? 'linear-gradient(135deg, rgba(20, 25, 40, 0.85) 0%, rgba(15, 20, 35, 0.9) 100%)' 
        : 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(240, 245, 255, 0.85) 100%)';
    const glassBorder = isDarkMode ? 'rgba(100, 150, 255, 0.25)' : 'rgba(100, 150, 200, 0.2)';
    const glassShadow = isDarkMode 
        ? '0 12px 48px rgba(0, 0, 0, 0.5), 0 4px 16px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
        : '0 12px 48px rgba(0, 0, 0, 0.15), 0 4px 16px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.8)';
    const textColor = isDarkMode ? '#ecf0f1' : '#1a1a2e';
    const labelColor = isDarkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(30, 30, 50, 0.7)';
    const inputBg = isDarkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';
    const inputBorder = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.1)';
    
    // Create panel (no blocking overlay - Liquid Glass style)
    const panel = document.createElement('div');
    panel.id = 'ssh-address-dialog';
    panel.style.cssText = `
        position: fixed;
        left: ${deviceScreenX}px;
        top: ${deviceScreenY + deviceRadius + 20}px;
        transform: translateX(-50%);
        z-index: 100000;
        background: ${glassBg};
        border: 1px solid ${glassBorder};
        border-radius: 14px;
        padding: 16px 20px;
        min-width: 320px;
        box-shadow: ${glassShadow};
        backdrop-filter: blur(32px) saturate(180%);
        -webkit-backdrop-filter: blur(32px) saturate(180%);
        opacity: 0;
        animation: sshDialogFadeIn 0.2s ease forwards;
    `;
    
    // Add animation styles
    const styleId = 'ssh-dialog-styles';
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            @keyframes sshDialogFadeIn {
                from { opacity: 0; transform: translateX(-50%) translateY(8px); }
                to { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
        `;
        document.head.appendChild(style);
    }
    
    const inputStyle = `
        width: 100%;
        padding: 8px 10px;
        border-radius: 6px;
        border: 1px solid ${inputBorder};
        background: ${inputBg};
        color: ${textColor};
        font-size: 12px;
        outline: none;
        box-sizing: border-box;
        transition: border-color 0.2s;
    `;
    
    panel.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
            <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #27ae60, #2ecc71); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" width="18" height="18">
                    <rect x="2" y="3" width="20" height="14" rx="2"/>
                    <polyline points="7,8 9,10 7,12"/>
                    <line x1="11" y1="12" x2="15" y2="12"/>
                </svg>
            </div>
            <div style="flex: 1;">
                <div style="font-size: 13px; font-weight: 600; color: ${textColor};">SSH Connection</div>
                <div style="font-size: 11px; color: ${labelColor};">${device.label || 'Device'}</div>
            </div>
            <button id="ssh-help-btn" title="Copy SSH command for iTerm/Terminal" style="
                width: 24px;
                height: 24px;
                border-radius: 50%;
                border: 1px solid ${inputBorder};
                background: ${inputBg};
                color: ${labelColor};
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.15s;
            ">?</button>
        </div>
        
        <div style="margin-bottom: 10px;">
            <label style="display: block; margin-bottom: 4px; color: ${labelColor}; font-size: 11px; font-weight: 500;">
                Host / Serial Number
            </label>
            <input type="text" id="ssh-host-input" value="${currentHost}" 
                placeholder="IP, hostname, or serial number"
                style="${inputStyle} border-color: rgba(39, 174, 96, 0.5);"
            />
        </div>
        
        <div style="display: flex; gap: 10px; margin-bottom: 10px;">
            <div style="flex: 1;">
                <label style="display: block; margin-bottom: 4px; color: ${labelColor}; font-size: 11px; font-weight: 500;">
                    Username
                </label>
                <input type="text" id="ssh-user-input" value="${currentUser}" 
                    placeholder="dnroot"
                    style="${inputStyle}"
                />
            </div>
            <div style="flex: 1;">
                <label style="display: block; margin-bottom: 4px; color: ${labelColor}; font-size: 11px; font-weight: 500;">
                    Password
                </label>
                <div style="position: relative;">
                    <input type="password" id="ssh-pass-input" value="${currentPass}" 
                        placeholder="••••••"
                        style="${inputStyle} padding-right: 30px;"
                    />
                    <button id="ssh-toggle-pass" type="button" style="
                        position: absolute;
                        right: 6px;
                        top: 50%;
                        transform: translateY(-50%);
                        background: none;
                        border: none;
                        color: ${labelColor};
                        cursor: pointer;
                        padding: 2px;
                        display: flex;
                        align-items: center;
                    ">
                        <svg id="ssh-eye-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
        
        <div style="display: flex; align-items: center; gap: 8px; margin-top: 10px; margin-bottom: 6px;">
            <input type="checkbox" id="ssh-clear-hostkey" 
                style="width: 14px; height: 14px; accent-color: #e67e22; cursor: pointer;"
            />
            <label for="ssh-clear-hostkey" style="color: ${labelColor}; font-size: 11px; cursor: pointer; user-select: none;">
                Clear known host key <span style="color: ${isDarkMode ? '#FF7A33' : '#FF5E1F'};">(ssh-keygen -R)</span>
            </label>
        </div>
        
        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 12px;">
            <button id="ssh-dialog-cancel" style="
                padding: 6px 14px;
                border-radius: 6px;
                border: 1px solid ${inputBorder};
                background: ${inputBg};
                color: ${textColor};
                font-size: 11px;
                cursor: pointer;
                transition: all 0.15s;
            ">Cancel</button>
            <button id="ssh-dialog-save" style="
                padding: 6px 16px;
                border-radius: 6px;
                border: none;
                background: linear-gradient(135deg, #27ae60, #2ecc71);
                color: white;
                font-size: 11px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.15s;
                box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3);
            ">Save</button>
        </div>
    `;
    
    document.body.appendChild(panel);
    
    // Adjust position to keep within viewport
    requestAnimationFrame(() => {
        const panelRect = panel.getBoundingClientRect();
        const padding = 15;
        
        if (panelRect.right > window.innerWidth - padding) {
            panel.style.left = (window.innerWidth - panelRect.width / 2 - padding) + 'px';
        }
        if (panelRect.left < padding) {
            panel.style.left = (panelRect.width / 2 + padding) + 'px';
        }
        if (panelRect.bottom > window.innerHeight - padding) {
            panel.style.top = (deviceScreenY - deviceRadius - panelRect.height - 10) + 'px';
        }
        if (panelRect.top < padding) {
            panel.style.top = padding + 'px';
        }
    });
    
    // Get input references
    const hostInput = panel.querySelector('#ssh-host-input');
    const userInput = panel.querySelector('#ssh-user-input');
    const passInput = panel.querySelector('#ssh-pass-input');
    const togglePassBtn = panel.querySelector('#ssh-toggle-pass');
    const eyeIcon = panel.querySelector('#ssh-eye-icon');
    
    
    // Close dialog helper
    let handleClickOutside, handleEscape;
    const closeDialog = () => {
        panel.remove();
        if (handleEscape) document.removeEventListener('keydown', handleEscape);
        if (handleClickOutside) document.removeEventListener('click', handleClickOutside);
        setTimeout(() => {
            if (editor.showDeviceSelectionToolbar) editor.showDeviceSelectionToolbar(device);
        }, 50);
    };
    
    // Focus the host input
    setTimeout(() => {
        if (hostInput) {
            hostInput.focus();
            hostInput.select();
        }
    }, 50);
    
    // Toggle password visibility
    if (togglePassBtn && passInput && eyeIcon) {
        togglePassBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (passInput.type === 'password') {
                passInput.type = 'text';
                eyeIcon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
            } else {
                passInput.type = 'password';
                eyeIcon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
            }
        });
    }
    
    // Handle save
    const saveAddress = async () => {
        const host = hostInput.value.trim();
        const user = userInput.value.trim() || 'dnroot';
        const password = passInput.value;
        const clearHostKeyCheckbox = panel.querySelector('#ssh-clear-hostkey');
        const clearHostKey = clearHostKeyCheckbox ? clearHostKeyCheckbox.checked : false;
        
        // Run ssh-keygen -R if checkbox is checked
        if (clearHostKey && host) {
            try {
                const resp = await fetch('/api/ssh/clear-hostkey', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ host })
                });
                const result = await resp.json();
                if (result.ok) {
                    if (editor.showToast) editor.showToast(`Host key cleared for ${host}`, 'info');
                } else {
                    if (editor.showToast) editor.showToast(`ssh-keygen -R: ${result.error || result.output || 'failed'}`, 'warning');
                }
            } catch (err) {
                if (editor.showToast) editor.showToast(`Failed to clear host key: ${err.message}`, 'error');
            }
        }
        
        device.sshConfig = {
            host: host,
            user: user,
            password: password
        };
        
        device.deviceAddress = host ? `${user}@${host}` : '';
        
        if (editor.saveState) editor.saveState();
        if (editor.scheduleAutoSave) editor.scheduleAutoSave();
        
        if (editor.debugger) {
            if (host) {
                editor.debugger.logSuccess(`🖥️ SSH configured for ${device.label}: ${user}@${host}`);
            } else {
                editor.debugger.logInfo(`🖥️ SSH config cleared for ${device.label}`);
            }
        }
        
        if (editor.showToast) {
            editor.showToast(host ? `SSH set: ${user}@${host}` : 'SSH config cleared', 'success');
        }
        closeDialog();
        editor.draw();
    };
    
    // Event listeners
    const saveBtn = panel.querySelector('#ssh-dialog-save');
    const cancelBtn = panel.querySelector('#ssh-dialog-cancel');
    const helpBtn = panel.querySelector('#ssh-help-btn');
    
    if (saveBtn) saveBtn.addEventListener('click', saveAddress);
    if (cancelBtn) cancelBtn.addEventListener('click', closeDialog);
    
    // Help button: Copy SSH command to clipboard for iTerm/Terminal pasting
    if (helpBtn) {
        helpBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const host = hostInput.value.trim();
            const user = userInput.value.trim() || 'dnroot';
            const password = passInput.value;
            
            if (!host) {
                if (editor.showToast) editor.showToast('Enter a host/serial first', 'error');
                return;
            }
            
            const sshCommand = `ssh ${user}@${host}`;
            
            // Copy to clipboard
            window.safeClipboardWrite(sshCommand).then(() => {
                // Visual feedback
                helpBtn.textContent = '✓';
                helpBtn.style.background = 'rgba(39, 174, 96, 0.2)';
                helpBtn.style.color = '#27ae60';
                helpBtn.style.borderColor = 'rgba(39, 174, 96, 0.5)';
                
                setTimeout(() => {
                    helpBtn.textContent = '?';
                    helpBtn.style.background = inputBg;
                    helpBtn.style.color = labelColor;
                    helpBtn.style.borderColor = inputBorder;
                }, 2000);
                
                // Show toast with password info if available
                if (password && editor.showToast) {
                    editor.showToast(`📋 SSH command copied! Password: ${password}`, 'success', 5000);
                } else if (editor.showToast) {
                    editor.showToast(`📋 Copied: ${sshCommand}`, 'success');
                }
            }).catch(() => {
                if (editor.showToast) editor.showToast('Failed to copy to clipboard', 'error');
            });
        });
        
        // Hover effect for help button
        helpBtn.addEventListener('mouseenter', () => {
            helpBtn.style.background = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
            helpBtn.style.transform = 'scale(1.1)';
        });
        helpBtn.addEventListener('mouseleave', () => {
            if (helpBtn.textContent === '?') {
                helpBtn.style.background = inputBg;
            }
            helpBtn.style.transform = 'scale(1)';
        });
    }
    
    // Enter to save, Escape to cancel
    handleEscape = (e) => {
        if (e.key === 'Enter' && (document.activeElement === hostInput || 
                                   document.activeElement === userInput || 
                                   document.activeElement === passInput)) {
            e.preventDefault();
            saveAddress();
        } else if (e.key === 'Escape') {
            closeDialog();
        }
    };
    document.addEventListener('keydown', handleEscape);
    
    // Click outside to close (with delay)
    handleClickOutside = (e) => {
        if (!panel.contains(e.target)) {
            closeDialog();
        }
    };
    setTimeout(() => document.addEventListener('click', handleClickOutside), 100);
    
    // Hover effects
    if (saveBtn) {
        saveBtn.addEventListener('mouseenter', () => {
            saveBtn.style.transform = 'scale(1.02)';
            saveBtn.style.boxShadow = '0 4px 12px rgba(39, 174, 96, 0.4)';
        });
        saveBtn.addEventListener('mouseleave', () => {
            saveBtn.style.transform = 'scale(1)';
            saveBtn.style.boxShadow = '0 2px 8px rgba(39, 174, 96, 0.3)';
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('mouseenter', () => {
            cancelBtn.style.background = isDarkMode ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)';
        });
        cancelBtn.addEventListener('mouseleave', () => {
            cancelBtn.style.background = inputBg;
        });
    }
}

// Export function
window.showSSHAddressDialog = showSSHAddressDialog;

console.log('[topology-ssh-dialog.js] SSH Address Dialog module loaded');
