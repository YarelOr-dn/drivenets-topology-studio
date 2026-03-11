/**
 * topology-link-popups.js - Link Popup UI Components
 * 
 * Extracted from topology.js for modular architecture.
 * Contains popup dialogs for link width, style, and curve configuration.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.LinkPopups = {

    /**
     * Show width slider popup for a link
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} link - The link object
     */
    showWidthSliderPopup(editor, link) {
        // Get context menu position
        const contextMenu = document.getElementById('context-menu');
        const menuRect = contextMenu.getBoundingClientRect();
        
        // Remove only this popup type (allow multiple different popups)
        this.hideWidthSliderPopup(editor);
        
        // Temporarily disable link highlight to see actual width
        editor._colorEditingLink = link;
        editor.draw();
        
        // Create width slider popup first, then position after adding to DOM
        const popup = document.createElement('div');
        popup.id = 'width-slider-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${menuRect.right + 5}px;
            top: 0px;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #FF5E1F;
            border-radius: 8px;
            padding: 12px;
            z-index: 10001;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            min-width: 200px;
            visibility: hidden;
        `;
        
        // Title
        const title = document.createElement('div');
        title.innerHTML = `${appIcon('ruler')} Link Width`;
        title.style.cssText = 'color: #FF5E1F; font-size: 12px; font-weight: bold; margin-bottom: 10px; text-align: center;';
        popup.appendChild(title);
        
        // Current width display (use per-link width if set, otherwise use global)
        const currentWidth = link.width !== undefined ? link.width : editor.currentLinkWidth;
        const widthDisplay = document.createElement('div');
        widthDisplay.id = 'popup-width-display';
        widthDisplay.textContent = `${currentWidth}px`;
        widthDisplay.style.cssText = 'text-align: center; color: #FF5E1F; font-size: 18px; font-weight: bold; margin-bottom: 8px;';
        popup.appendChild(widthDisplay);
        
        // Calculate max width to prevent overlap
        const maxWidth = editor.getMaxLinkWidth(link);
        
        // Width slider
        const slider = document.createElement('input');
        slider.type = 'range';
        slider.min = '1';
        slider.max = maxWidth.toString();
        slider.value = Math.min(currentWidth, maxWidth);
        slider.style.cssText = 'width: 100%; height: 8px; background: linear-gradient(to right, #95a5a6, #FF5E1F); border-radius: 4px; outline: none; appearance: none; -webkit-appearance: none; cursor: pointer;';
        slider.oninput = (e) => {
            const width = Math.min(parseInt(e.target.value), maxWidth);
            // ENHANCED: For BUL chains, apply width to ALL links
            if ((link.type === 'link' || link.type === 'unbound') && (link.mergedWith || link.mergedInto)) {
                const allLinksInChain = editor.getAllMergedLinks(link);
                for (const chainLink of allLinksInChain) {
                    chainLink.width = width;
                }
            } else {
                link.width = width;
            }
            widthDisplay.textContent = `${width}px`;
            editor.draw();
            editor.scheduleAutoSave(); // Save width change
        };
        popup.appendChild(slider);
        
        // Show max width info if limited
        if (maxWidth < 12) {
            const maxInfo = document.createElement('div');
            maxInfo.textContent = `Max: ${maxWidth}px (prevents overlap)`;
            maxInfo.style.cssText = 'color: #FF7A33; font-size: 10px; text-align: center; margin-top: 4px;';
            popup.appendChild(maxInfo);
        }
        
        // Min/max labels
        const labels = document.createElement('div');
        labels.style.cssText = 'display: flex; justify-content: space-between; font-size: 9px; color: #95a5a6; margin-top: 4px;';
        labels.innerHTML = '<span>1px (thin)</span><span>12px (thick)</span>';
        popup.appendChild(labels);
        
        // Quick preset buttons
        const presetsLabel = document.createElement('div');
        presetsLabel.textContent = 'Quick Presets';
        presetsLabel.style.cssText = 'color: #FF7A33; font-size: 11px; margin-top: 10px; margin-bottom: 6px; font-weight: 600;';
        popup.appendChild(presetsLabel);
        
        const presetsContainer = document.createElement('div');
        presetsContainer.style.cssText = 'display: flex; gap: 6px; justify-content: center;';
        
        [1, 2, 3, 4, 6, 8, 10, 12].forEach(w => {
            const btn = document.createElement('button');
            btn.textContent = w;
            btn.style.cssText = `
                width: 24px; height: 24px; border-radius: 4px;
                background: ${w === currentWidth ? '#FF5E1F' : '#34495e'};
                border: 1px solid ${w === currentWidth ? '#FF7A33' : '#4a5568'};
                color: white; cursor: pointer; font-size: 10px; font-weight: bold;
                transition: all 0.1s;
            `;
            btn.onmouseenter = () => { if (w !== link.width) btn.style.background = '#4a5568'; };
            btn.onmouseleave = () => { if (w !== link.width) btn.style.background = '#34495e'; };
            btn.onclick = () => {
                // ENHANCED: For BUL chains, apply width to ALL links
                if ((link.type === 'link' || link.type === 'unbound') && (link.mergedWith || link.mergedInto)) {
                    const allLinksInChain = editor.getAllMergedLinks(link);
                    for (const chainLink of allLinksInChain) {
                        chainLink.width = w;
                    }
                } else {
                    link.width = w;
                }
                slider.value = w;
                widthDisplay.textContent = `${w}px`;
                // Update button styles
                presetsContainer.querySelectorAll('button').forEach(b => {
                    b.style.background = '#34495e';
                    b.style.borderColor = '#4a5568';
                });
                btn.style.background = '#FF5E1F';
                btn.style.borderColor = '#FF7A33';
                editor.draw();
                editor.scheduleAutoSave(); // Save width change
            };
            presetsContainer.appendChild(btn);
        });
        popup.appendChild(presetsContainer);
        
        // Done button
        const doneBtn = document.createElement('button');
        doneBtn.innerHTML = `${appIcon('check')} Done`;
        doneBtn.style.cssText = `
            width: 100%; margin-top: 12px; padding: 8px;
            background: #27ae60; border: none; border-radius: 4px;
            color: white; cursor: pointer; font-weight: bold;
            transition: background 0.2s;
        `;
        doneBtn.onmouseenter = () => doneBtn.style.background = '#2ecc71';
        doneBtn.onmouseleave = () => doneBtn.style.background = '#27ae60';
        doneBtn.onclick = () => {
            editor.saveState();
            // Close width popup but keep context menu open
            const popup = document.getElementById('width-slider-popup');
            if (popup) popup.remove();
            editor._colorEditingLink = null;
            editor.draw();
        };
        popup.appendChild(doneBtn);
        
        document.body.appendChild(popup);
        
        // Calculate position - stack below color popup if it exists
        let topOffset = menuRect.top;
        const colorPopup = document.getElementById('color-palette-popup');
        if (colorPopup) {
            const colorRect = colorPopup.getBoundingClientRect();
            topOffset = colorRect.bottom + 10;
        }
        popup.style.top = topOffset + 'px';
        popup.style.visibility = 'visible';
        
        // Adjust position if popup goes off screen
        const popupRect = popup.getBoundingClientRect();
        if (popupRect.right > window.innerWidth) {
            popup.style.left = (menuRect.left - popupRect.width - 5) + 'px';
        }
        if (popupRect.bottom > window.innerHeight) {
            popup.style.top = (window.innerHeight - popupRect.height - 10) + 'px';
        }
    },

    /**
     * Hide width slider popup
     * @param {Object} editor - TopologyEditor instance
     */
    hideWidthSliderPopup(editor) {
        const popup = document.getElementById('width-slider-popup');
        if (popup) popup.remove();
        if (editor) editor._colorEditingLink = null;
    },

    /**
     * Show style options popup for a link
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} link - The link object
     */
    showStyleOptionsPopup(editor, link) {
        // Get context menu position
        const contextMenu = document.getElementById('context-menu');
        const menuRect = contextMenu.getBoundingClientRect();
        
        // Remove only this popup type (allow multiple different popups)
        this.hideStyleOptionsPopup(editor);
        
        // Temporarily disable link highlight to see actual style
        editor._colorEditingLink = link;
        editor.draw();
        
        // Create style options popup (position will be set after adding to DOM)
        const popup = document.createElement('div');
        popup.id = 'style-options-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${menuRect.right + 5}px;
            top: 0px;
            background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
            border: 1px solid #0066FA;
            border-radius: 8px;
            padding: 12px;
            z-index: 10000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5), 0 0 15px rgba(0, 180, 216, 0.2);
            min-width: 180px;
            visibility: hidden;
        `;
        
        // Title
        const title = document.createElement('div');
        title.innerHTML = `${appIcon('sparkle')} Link Style`;
        title.style.cssText = 'color: #FF5E1F; font-size: 12px; font-weight: bold; margin-bottom: 12px; text-align: center;';
        popup.appendChild(title);
        
        const currentStyle = link.style || 'solid';
        
        // Style options with visual previews - all 8 styles
        const styles = [
            { id: 'solid', name: 'Solid', desc: 'Standard line' },
            { id: 'dashed', name: 'Dashed', desc: 'Short dashes' },
            { id: 'dashed-wide', name: 'Dashed Wide', desc: 'Long dashes' },
            { id: 'dotted', name: 'Dotted', desc: 'Dot pattern' },
            { id: 'arrow', name: 'Arrow', desc: 'End arrow' },
            { id: 'double-arrow', name: 'Double Arrow', desc: 'Both ends' },
            { id: 'dashed-arrow', name: 'Dashed Arrow', desc: 'Dashed + arrow' },
            { id: 'dashed-double-arrow', name: 'Dashed Double', desc: 'Dashed + both' }
        ];
        
        styles.forEach(style => {
            const btn = document.createElement('div');
            btn.className = 'style-option-btn';
            btn.style.cssText = `
                display: flex; align-items: center; gap: 10px;
                padding: 10px; margin-bottom: 6px;
                background: ${style.id === currentStyle ? 'rgba(255, 94, 31, 0.25)' : 'rgba(0,0,0,0.2)'};
                border: 1px solid ${style.id === currentStyle ? '#FF5E1F' : 'rgba(255,255,255,0.1)'};
                border-radius: 6px; cursor: pointer;
                transition: all 0.2s;
            `;
            
            // Icon preview using SVG
            const iconContainer = document.createElement('div');
            iconContainer.style.cssText = 'width: 50px; display: flex; justify-content: center;';
            
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('width', '50');
            svg.setAttribute('height', '16');
            svg.setAttribute('viewBox', '0 0 50 16');
            
            const color = link.color || '#3498db';
            const isDashed = style.id.includes('dashed');
            const isDashedWide = style.id === 'dashed-wide';
            const isDotted = style.id === 'dotted';
            const hasEndArrow = style.id.includes('arrow') && style.id !== 'double-arrow' || style.id === 'double-arrow' || style.id === 'dashed-double-arrow';
            const hasStartArrow = style.id === 'double-arrow' || style.id === 'dashed-double-arrow';
            
            // Calculate line endpoints based on arrows
            const x1 = hasStartArrow ? 10 : 2;
            const x2 = (style.id.includes('arrow')) ? 40 : 48;
            
            // Draw the line
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1); line.setAttribute('y1', '8');
            line.setAttribute('x2', x2); line.setAttribute('y2', '8');
            line.setAttribute('stroke', color);
            line.setAttribute('stroke-width', '3');
            line.setAttribute('stroke-linecap', 'round');
            
            if (isDotted) {
                line.setAttribute('stroke-dasharray', '2,4');
            } else if (isDashedWide) {
                line.setAttribute('stroke-dasharray', '10,5');
            } else if (isDashed) {
                line.setAttribute('stroke-dasharray', '6,4');
            }
            svg.appendChild(line);
            
            // Draw start arrow if needed
            if (hasStartArrow) {
                const arrow1 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                arrow1.setAttribute('points', '10,3 2,8 10,13');
                arrow1.setAttribute('fill', color);
                svg.appendChild(arrow1);
            }
            
            // Draw end arrow if needed
            if (style.id.includes('arrow')) {
                const arrow2 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                arrow2.setAttribute('points', '40,3 48,8 40,13');
                arrow2.setAttribute('fill', color);
                svg.appendChild(arrow2);
            }
            
            iconContainer.appendChild(svg);
            btn.appendChild(iconContainer);
            
            // Label
            const label = document.createElement('div');
            label.innerHTML = `<div style="color: #fff; font-weight: bold; font-size: 12px;">${style.name}</div>
                              <div style="color: #888; font-size: 9px;">${style.desc}</div>`;
            btn.appendChild(label);
            
            // Checkmark for selected - use class for reliable selection
            if (style.id === currentStyle) {
                const check = document.createElement('div');
                check.className = 'style-check-icon';
                check.innerHTML = appIcon('check');
                check.style.cssText = 'color: #2ecc71; font-size: 16px; margin-left: auto;';
                btn.appendChild(check);
            }
            
            btn.onmouseenter = () => {
                if (style.id !== currentStyle) {
                    btn.style.background = 'rgba(155, 89, 182, 0.2)';
                    btn.style.borderColor = 'rgba(155, 89, 182, 0.5)';
                }
            };
            btn.onmouseleave = () => {
                // Check if this is still NOT the selected style (may have changed via click)
                const actualStyle = link.style || 'solid';
                if (style.id !== actualStyle) {
                    btn.style.background = 'rgba(0,0,0,0.2)';
                    btn.style.borderColor = 'rgba(255,255,255,0.1)';
                }
            };
            btn.onclick = () => {
                editor.saveState();
                // ENHANCED: For BUL chains, apply style to ALL links
                if ((link.type === 'link' || link.type === 'unbound') && (link.mergedWith || link.mergedInto)) {
                    const allLinksInChain = editor.getAllMergedLinks(link);
                    for (const chainLink of allLinksInChain) {
                        chainLink.style = style.id;
                    }
                } else {
                    link.style = style.id;
                }
                // Update button visuals to show new selection - use class for reliable removal
                popup.querySelectorAll('.style-option-btn').forEach(b => {
                    b.style.background = 'rgba(0,0,0,0.2)';
                    b.style.borderColor = 'rgba(255,255,255,0.1)';
                    // Remove ALL existing checkmarks
                    b.querySelectorAll('.style-check-icon').forEach(c => c.remove());
                });
                btn.style.background = 'rgba(255, 94, 31, 0.25)';
                btn.style.borderColor = '#FF5E1F';
                // Only add check if not already present
                if (!btn.querySelector('.style-check-icon')) {
                    const check = document.createElement('div');
                    check.className = 'style-check-icon';
                    check.innerHTML = appIcon('check');
                    check.style.cssText = 'color: #2ecc71; font-size: 16px; margin-left: auto;';
                    btn.appendChild(check);
                }
                editor.draw();
                // Don't close menu - let user make more changes
            };
            
            popup.appendChild(btn);
        });
        
        document.body.appendChild(popup);
        
        // Calculate position - stack below other popups if they exist
        let topOffset = menuRect.top;
        const colorPopup = document.getElementById('color-palette-popup');
        const widthPopup = document.getElementById('width-slider-popup');
        if (widthPopup) {
            const widthRect = widthPopup.getBoundingClientRect();
            topOffset = widthRect.bottom + 10;
        } else if (colorPopup) {
            const colorRect = colorPopup.getBoundingClientRect();
            topOffset = colorRect.bottom + 10;
        }
        popup.style.top = topOffset + 'px';
        popup.style.visibility = 'visible';
        
        // Adjust position if popup goes off screen
        const popupRect = popup.getBoundingClientRect();
        if (popupRect.right > window.innerWidth) {
            popup.style.left = (menuRect.left - popupRect.width - 5) + 'px';
        }
        if (popupRect.bottom > window.innerHeight) {
            popup.style.top = (window.innerHeight - popupRect.height - 10) + 'px';
        }
    },

    /**
     * Hide style options popup
     * @param {Object} editor - TopologyEditor instance
     */
    hideStyleOptionsPopup(editor) {
        const popup = document.getElementById('style-options-popup');
        if (popup) popup.remove();
        if (editor) editor._colorEditingLink = null;
    },

    /**
     * Show curve magnitude popup for a link
     * @param {Object} editor - TopologyEditor instance
     * @param {Object} link - The link object
     */
    showCurveMagnitudePopup(editor, link) {
        // Get curve submenu position
        const submenu = document.getElementById('ctx-curve-submenu');
        if (!submenu) {
            return;
        }
        const menuRect = submenu.getBoundingClientRect();
        
        // Remove existing popup
        const existingPopup = document.getElementById('curve-magnitude-popup');
        if (existingPopup) existingPopup.remove();
        
        // Temporarily disable link highlight to see actual curve
        editor._colorEditingLink = link;
        editor.draw();
        
        // Get current values
        const currentMagnitude = link.curveMagnitude || 0;
        const currentDirection = link.curveDirection !== undefined ? link.curveDirection : 1;
        
        // Create curve magnitude popup
        const popup = document.createElement('div');
        popup.id = 'curve-magnitude-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${menuRect.right + 5}px;
            top: ${menuRect.top}px;
            background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
            border: 1px solid #0066FA;
            border-radius: 8px;
            padding: 12px;
            z-index: 10001;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5), 0 0 15px rgba(0, 180, 216, 0.2);
            min-width: 180px;
        `;
        
        // Title
        const title = document.createElement('div');
        title.innerHTML = `${appIcon('curve')} Curve Magnitude`;
        title.style.cssText = 'color: #FF5E1F; font-size: 12px; font-weight: bold; margin-bottom: 10px; text-align: center;';
        popup.appendChild(title);
        
        // Current value display
        const valueDisplay = document.createElement('div');
        valueDisplay.id = 'curve-magnitude-value';
        valueDisplay.textContent = currentMagnitude > 0 ? currentMagnitude : 'Off';
        valueDisplay.style.cssText = 'color: #ecf0f1; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 8px;';
        popup.appendChild(valueDisplay);
        
        // Slider
        const sliderContainer = document.createElement('div');
        sliderContainer.style.cssText = 'display: flex; align-items: center; gap: 8px; margin-bottom: 8px;';
        
        const slider = document.createElement('input');
        slider.type = 'range';
        slider.min = '0';
        slider.max = '80';
        slider.value = currentMagnitude;
        slider.style.cssText = 'flex: 1; accent-color: #FF5E1F;';
        
        slider.oninput = () => {
            const value = parseInt(slider.value);
            valueDisplay.textContent = value > 0 ? value : 'Off';
            link.curveMagnitude = value;
            editor.draw();
        };
        
        sliderContainer.appendChild(slider);
        popup.appendChild(sliderContainer);
        
        // Labels
        const labels = document.createElement('div');
        labels.style.cssText = 'display: flex; justify-content: space-between; color: #95a5a6; font-size: 10px; margin-bottom: 10px;';
        labels.innerHTML = '<span>Off</span><span>Max</span>';
        popup.appendChild(labels);
        
        // Direction toggle button
        const directionBtn = document.createElement('button');
        directionBtn.textContent = currentDirection === 1 ? '↻ Curve Right' : '↺ Curve Left';
        directionBtn.style.cssText = `
            width: 100%;
            padding: 8px;
            background: #1a1a1a;
            border: 1px solid #0066FA;
            border-radius: 4px;
            color: #ecf0f1;
            cursor: pointer;
            font-size: 12px;
            margin-bottom: 8px;
        `;
        directionBtn.onclick = () => {
            link.curveDirection = link.curveDirection === 1 ? -1 : 1;
            directionBtn.textContent = link.curveDirection === 1 ? '↻ Curve Right' : '↺ Curve Left';
            editor.draw();
        };
        popup.appendChild(directionBtn);
        
        // Quick presets
        const presetsLabel = document.createElement('div');
        presetsLabel.textContent = 'Quick Presets';
        presetsLabel.style.cssText = 'color: #FF7A33; font-size: 11px; margin-bottom: 6px; font-weight: 600;';
        popup.appendChild(presetsLabel);
        
        const presetsContainer = document.createElement('div');
        presetsContainer.style.cssText = 'display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 10px;';
        
        const presets = [0, 10, 20, 30, 40, 60, 80];
        presets.forEach(preset => {
            const btn = document.createElement('button');
            btn.textContent = preset === 0 ? 'Off' : preset;
            btn.style.cssText = `
                padding: 4px 8px;
                background: ${currentMagnitude === preset ? '#FF5E1F' : '#1a1a1a'};
                border: 1px solid #0066FA;
                border-radius: 4px;
                color: white;
                cursor: pointer;
                font-size: 11px;
            `;
            btn.onclick = () => {
                link.curveMagnitude = preset;
                slider.value = preset;
                valueDisplay.textContent = preset > 0 ? preset : 'Off';
                // Update all preset button styles
                presetsContainer.querySelectorAll('button').forEach(b => {
                    b.style.background = '#1a1a1a';
                });
                btn.style.background = '#FF5E1F';
                editor.draw();
            };
            presetsContainer.appendChild(btn);
        });
        popup.appendChild(presetsContainer);
        
        // Done button
        const doneBtn = document.createElement('button');
        doneBtn.innerHTML = `${appIcon('check')} Done`;
        doneBtn.style.cssText = `
            width: 100%;
            padding: 8px;
            background: #27ae60;
            border: none;
            border-radius: 4px;
            color: white;
            cursor: pointer;
            font-size: 12px;
            font-weight: bold;
        `;
        doneBtn.onclick = () => {
            editor.saveState();
            this.hideCurveMagnitudePopup(editor);
            editor.hideCurveSubmenu();
            editor.hideContextMenu();
        };
        popup.appendChild(doneBtn);
        
        document.body.appendChild(popup);
        
        // Adjust position if popup goes off screen
        const popupRect = popup.getBoundingClientRect();
        if (popupRect.right > window.innerWidth) {
            popup.style.left = (menuRect.left - popupRect.width - 5) + 'px';
        }
        if (popupRect.bottom > window.innerHeight) {
            popup.style.top = (window.innerHeight - popupRect.height - 10) + 'px';
        }
    },

    /**
     * Hide curve magnitude popup
     * @param {Object} editor - TopologyEditor instance
     */
    hideCurveMagnitudePopup(editor) {
        const popup = document.getElementById('curve-magnitude-popup');
        if (popup) popup.remove();
        if (editor) {
            editor._colorEditingLink = null;
            editor.draw();
        }
    }
};

console.log('[topology-link-popups.js] LinkPopups loaded');
