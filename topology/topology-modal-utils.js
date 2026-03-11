/**
 * topology-modal-utils.js - Modal Dragging and Resizing Utilities
 * 
 * Extracted from topology.js for modular architecture
 * Contains: makeDraggableModal, makeResizableModal
 * 
 * These functions make modals draggable by their header and resizable
 * from all 8 directions using resize handles.
 */

'use strict';

window.ModalUtils = {
    /**
     * Make a modal draggable by its header
     * @param {HTMLElement} modalContent - The modal content element
     */
    makeDraggableModal(modalContent) {
        const header = modalContent.querySelector('.draggable-header');
        if (!header) {
            console.warn('[ModalUtils] No draggable header found in modal');
            return;
        }
        
        console.log('[ModalUtils] Setting up draggable modal with header:', header);
        
        let isDragging = false;
        let offsetX = 0;
        let offsetY = 0;
        let hasMoved = false; // Track if modal has been manually positioned
        
        // Ensure header has proper cursor
        header.style.cursor = 'move';
        
        // Reset to centered position when modal opens
        const parentModal = modalContent.closest('.modal');
        if (parentModal) {
            let wasVisible = false;
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.attributeName === 'style' || mutation.attributeName === 'class') {
                        const isVisible = parentModal.style.display !== 'none' && 
                                        (parentModal.classList.contains('show') || parentModal.style.display === 'flex');
                        
                        // Reset hasMoved when modal was hidden and is now visible (reopening)
                        if (isVisible && !wasVisible) {
                            // Modal just opened - reset position to centered
                            hasMoved = false;
                            modalContent.style.position = 'relative';
                            modalContent.style.left = '';
                            modalContent.style.top = '';
                            modalContent.style.transform = '';
                            modalContent.style.margin = '';
                        }
                        
                        wasVisible = isVisible;
                    }
                });
            });
            observer.observe(parentModal, { attributes: true });
        }
        
        header.addEventListener('mousedown', (e) => {
            // Don't drag when clicking buttons or any interactive elements
            if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                return;
            }
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // CRITICAL FIX: If modal is centered (relative position), convert to fixed FIRST
            const currentPosition = window.getComputedStyle(modalContent).position;
            if (currentPosition === 'relative' || modalContent.style.position === 'relative' || !modalContent.style.left) {
                // Modal is centered - convert to fixed at current screen position
                const rect = modalContent.getBoundingClientRect();
                modalContent.style.position = 'fixed';
                modalContent.style.left = rect.left + 'px';
                modalContent.style.top = rect.top + 'px';
                modalContent.style.transform = 'none';
                modalContent.style.margin = '0'; // Remove any margin
            }
            
            // NOW capture offset after position is fixed
            const rect = modalContent.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            
            isDragging = true;
            window._linkModalDragging = true; // Track for backdrop click prevention
            hasMoved = true; // Mark as manually positioned
            header.style.cursor = 'grabbing';
            document.body.style.userSelect = 'none'; // Prevent text selection
            e.preventDefault();
            e.stopPropagation();
        });
        
        const mouseMoveHandler = (e) => {
            if (!isDragging) return;
            e.preventDefault();
            
            // LOCKED ALGORITHM: newPosition = mousePosition - offset
            // This is the ONLY calculation - no deltas, no start positions
            let newLeft = e.clientX - offsetX;
            let newTop = e.clientY - offsetY;
            
            // Keep modal within viewport
            const modalWidth = modalContent.offsetWidth;
            const modalHeight = modalContent.offsetHeight;
            newLeft = Math.max(0, Math.min(newLeft, window.innerWidth - modalWidth));
            newTop = Math.max(0, Math.min(newTop, window.innerHeight - modalHeight));
            
            // Apply positioning
            modalContent.style.position = 'fixed';
            modalContent.style.left = newLeft + 'px';
            modalContent.style.top = newTop + 'px';
            modalContent.style.transform = 'none'; // Remove centering transform
        };
        
        const mouseUpHandler = (e) => {
            if (isDragging) {
                isDragging = false;
                header.style.cursor = 'move';
                document.body.style.userSelect = ''; // Restore text selection
                
                // Delay clearing flag to prevent immediate backdrop close
                setTimeout(() => {
                    window._linkModalDragging = false;
                }, 400);
            }
        };
        
        // Use document-level listeners for smooth dragging
        document.addEventListener('mousemove', mouseMoveHandler);
        document.addEventListener('mouseup', mouseUpHandler);
    },

    /**
     * Make a modal resizable from all 8 directions
     * @param {HTMLElement} modalContent - The modal content element
     */
    makeResizableModal(modalContent) {
        let isResizing = false;
        let resizeType = null;
        let startX = 0;
        let startY = 0;
        let startWidth = 0;
        let startHeight = 0;
        let startLeft = 0;
        let startTop = 0;

        // Get all resize handles (8 directions)
        const handles = {
            left: modalContent.querySelector('.modal-resize-left'),
            right: modalContent.querySelector('.modal-resize-right'),
            top: modalContent.querySelector('.modal-resize-top'),
            bottom: modalContent.querySelector('.modal-resize-bottom'),
            topLeft: modalContent.querySelector('.modal-resize-top-left'),
            topRight: modalContent.querySelector('.modal-resize-top-right'),
            bottomLeft: modalContent.querySelector('.modal-resize-bottom-left'),
            bottomRight: modalContent.querySelector('.modal-resize-bottom-right')
        };

        // Add mousedown listeners to all handles
        Object.entries(handles).forEach(([type, handle]) => {
            if (!handle) return;
            
            handle.addEventListener('mousedown', (e) => {
                isResizing = true;
                window._linkModalResizing = true; // Track for backdrop click prevention
                resizeType = type;
                startX = e.clientX;
                startY = e.clientY;
                
                const rect = modalContent.getBoundingClientRect();
                startWidth = rect.width;
                startHeight = rect.height;
                startLeft = rect.left;
                startTop = rect.top;
                
                // Visual feedback
                modalContent.style.userSelect = 'none';
                document.body.style.cursor = handle.style.cursor;
                document.body.style.userSelect = 'none';
                
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
            
            // Calculate new dimensions based on resize type (8 directions)
            switch (resizeType) {
                case 'left':
                    newWidth = startWidth - deltaX;
                    newLeft = startLeft + deltaX;
                    break;
                case 'right':
                    newWidth = startWidth + deltaX;
                    break;
                case 'top':
                    newHeight = startHeight - deltaY;
                    newTop = startTop + deltaY;
                    break;
                case 'bottom':
                    newHeight = startHeight + deltaY;
                    break;
                case 'topLeft':
                    newWidth = startWidth - deltaX;
                    newHeight = startHeight - deltaY;
                    newLeft = startLeft + deltaX;
                    newTop = startTop + deltaY;
                    break;
                case 'topRight':
                    newWidth = startWidth + deltaX;
                    newHeight = startHeight - deltaY;
                    newTop = startTop + deltaY;
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
            
            // Clamp width with minimum constraint
            if (newWidth < minWidth) {
                if (resizeType.includes('Left') || resizeType === 'left') {
                    newLeft = startLeft + startWidth - minWidth;
                }
                newWidth = minWidth;
            } else if (newWidth > maxWidth) {
                newWidth = maxWidth;
            }
            
            // Clamp height with minimum constraint
            if (newHeight < minHeight) {
                if (resizeType.includes('top') || resizeType.includes('Top')) {
                    newTop = startTop + startHeight - minHeight;
                }
                newHeight = minHeight;
            } else if (newHeight > maxHeight) {
                newHeight = maxHeight;
            }
            
            // Ensure modal stays within viewport when resizing left
            if (resizeType.includes('Left') || resizeType === 'left') {
                if (newLeft < 0) {
                    newWidth = startWidth + startLeft;
                    newLeft = 0;
                }
                if (newLeft + newWidth > window.innerWidth) {
                    newLeft = window.innerWidth - newWidth;
                }
            }
            
            // Ensure modal stays within viewport when resizing right
            if (resizeType.includes('Right') || resizeType === 'right') {
                if (newLeft + newWidth > window.innerWidth) {
                    newWidth = window.innerWidth - newLeft;
                }
            }
            
            // Ensure modal stays within viewport when resizing top
            if (resizeType.includes('top') || resizeType.includes('Top')) {
                if (newTop < 0) {
                    newHeight = startHeight + startTop;
                    newTop = 0;
                }
                if (newTop + newHeight > window.innerHeight) {
                    newTop = window.innerHeight - newHeight;
                }
            }
            
            // Ensure modal stays within viewport when resizing bottom
            if (resizeType.includes('bottom') || resizeType.includes('Bottom')) {
                if (newTop + newHeight > window.innerHeight) {
                    newHeight = window.innerHeight - newTop;
                }
            }
            
            // Apply new dimensions and position
            modalContent.style.width = newWidth + 'px';
            modalContent.style.height = newHeight + 'px';
            
            // Apply horizontal position changes
            if (resizeType.includes('Left') || resizeType === 'left') {
                modalContent.style.left = newLeft + 'px';
            }
            
            // Apply vertical position changes
            if (resizeType.includes('top') || resizeType.includes('Top')) {
                modalContent.style.top = newTop + 'px';
            }
        });

        document.addEventListener('mouseup', (e) => {
            if (isResizing) {
                isResizing = false;
                resizeType = null;
                modalContent.style.userSelect = '';
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                
                // Delay clearing flag to prevent immediate backdrop close
                setTimeout(() => {
                    window._linkModalResizing = false;
                }, 400);
            }
        });
    },

    /**
     * Initialize all draggable modals on the page
     */
    initAllModals() {
        const draggableModals = document.querySelectorAll('.draggable-modal');
        draggableModals.forEach(modal => {
            this.makeDraggableModal(modal);
            this.makeResizableModal(modal);
        });
        console.log(`[ModalUtils] Made ${draggableModals.length} modals draggable and resizable`);
    }
};

console.log('[topology-modal-utils.js] ModalUtils loaded');
