// ============================================================================
// TOPOLOGY GROUPS MODULE
// ============================================================================
// Handles permanent object grouping - binding objects together so they move
// as a unit. Supports devices, unbound links, text, and shapes.
//
// Features:
//   - Group selected objects together
//   - Ungroup selected objects
//   - Auto-expand selection to group members
//   - Leader detection (top-right most object)
//   - Group validation after load/delete
//
// Usage:
//   const groups = new GroupManager(editor);
//   groups.groupSelected();
//   groups.ungroupSelected();
// ============================================================================

class GroupManager {
    constructor(editor) {
        this.editor = editor;
    }

    // ========== GROUP OPERATIONS ==========

    /**
     * Generate unique group ID
     * @returns {string} Unique group identifier
     */
    generateId() {
        return 'group_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Find the group leader (top-right most object) based on position
     * @param {object[]} objects - Objects to find leader from
     * @returns {object|null} Leader object
     */
    findLeader(objects) {
        if (!objects || objects.length === 0) return null;
        
        // Calculate position for each object (center point)
        const getObjPos = (obj) => {
            if (obj.type === 'unbound') {
                // For links, use the rightmost endpoint
                return { 
                    x: Math.max(obj.start.x, obj.end.x), 
                    y: Math.min(obj.start.y, obj.end.y) // top is smaller y
                };
            }
            return { x: obj.x || 0, y: obj.y || 0 };
        };
        
        // Sort by: first by x (descending - rightmost), then by y (ascending - topmost)
        let leader = objects[0];
        let leaderPos = getObjPos(leader);
        
        for (let i = 1; i < objects.length; i++) {
            const obj = objects[i];
            const pos = getObjPos(obj);
            
            // Prioritize rightmost, then topmost
            if (pos.x > leaderPos.x || (pos.x === leaderPos.x && pos.y < leaderPos.y)) {
                leader = obj;
                leaderPos = pos;
            }
        }
        
        return leader;
    }

    /**
     * Group selected objects together
     */
    groupSelected() {
        const selected = this.editor.selectedObjects;
        
        if (selected.length < 2) {
            this.editor.showToast('Select 2+ objects to group', 'warning');
            return;
        }
        
        const groupId = this.generateId();
        this.editor.saveState();
        
        // Find the leader (top-right most object)
        const leader = this.findLeader(selected);
        const leaderId = leader ? leader.id : selected[0].id;
        
        // Store leader's position as reference for all group members
        const leaderPos = leader.type === 'unbound' 
            ? { x: (leader.start.x + leader.end.x) / 2, y: (leader.start.y + leader.end.y) / 2 }
            : { x: leader.x, y: leader.y };
        
        selected.forEach(obj => {
            obj.groupId = groupId;
            obj.groupLeaderId = leaderId;
            
            // Store relative position from leader for each member
            const objPos = obj.type === 'unbound'
                ? { x: (obj.start.x + obj.end.x) / 2, y: (obj.start.y + obj.end.y) / 2 }
                : { x: obj.x, y: obj.y };
            
            obj.groupOffsetX = objPos.x - leaderPos.x;
            obj.groupOffsetY = objPos.y - leaderPos.y;
        });
        
        this.editor.showToast(`Grouped ${selected.length} objects (leader: ${leader.label || leader.id})`, 'success');
        this.editor.draw();
    }

    /**
     * Ungroup selected objects
     */
    ungroupSelected() {
        this.editor.saveState();
        const ungrouped = this.editor.selectedObjects.filter(obj => obj.groupId);
        
        ungrouped.forEach(obj => {
            obj.groupId = null;
            obj.groupLeaderId = null;
            obj.groupOffsetX = null;
            obj.groupOffsetY = null;
        });
        
        if (ungrouped.length > 0) {
            this.editor.showToast(`Ungrouped ${ungrouped.length} objects`, 'info');
        } else {
            this.editor.showToast('No grouped objects selected', 'warning');
        }
        this.editor.draw();
    }

    // ========== GROUP QUERIES ==========

    /**
     * Get all objects in the same group as the given object
     * @param {object} obj - Object to find group members for
     * @returns {object[]} Array of group members
     */
    getMembers(obj) {
        if (!obj || !obj.groupId) return [obj];
        return this.editor.objects.filter(o => o.groupId === obj.groupId);
    }

    /**
     * Check if an object belongs to a group
     * @param {object} obj - Object to check
     * @returns {boolean} True if grouped
     */
    isGrouped(obj) {
        if (!obj) return false;
        return obj.groupId !== null && obj.groupId !== undefined;
    }

    /**
     * Get unique group IDs from objects
     * @returns {Set<string>} Set of group IDs
     */
    getAllGroupIds() {
        const ids = new Set();
        this.editor.objects.forEach(obj => {
            if (obj.groupId) ids.add(obj.groupId);
        });
        return ids;
    }

    // ========== GROUP VALIDATION ==========

    /**
     * Expand selection to include all group members
     * Call this after setting selectedObject to ensure group integrity
     * @param {object} [obj] - Optional object to check for group membership (defaults to selectedObject)
     * @returns {boolean} True if selection was expanded
     */
    expandSelection(obj = null) {
        const selected = obj || this.editor.selectedObject;
        if (!selected || !selected.groupId) return false;
        
        const groupMembers = this.getMembers(selected);
        if (groupMembers.length <= 1) return false;
        
        let expanded = false;
        groupMembers.forEach(member => {
            if (!this.editor.selectedObjects.includes(member)) {
                this.editor.selectedObjects.push(member);
                expanded = true;
            }
        });
        
        return expanded;
    }

    /**
     * Validate all groups - called after load and delete operations
     * - Removes groupId from objects in groups with < 2 members
     * - Reassigns leader if leader was deleted
     */
    validate() {
        // Collect all unique group IDs
        const groupIds = this.getAllGroupIds();
        
        // Validate each group
        groupIds.forEach(groupId => {
            const members = this.editor.objects.filter(o => o.groupId === groupId);
            
            if (members.length < 2) {
                // Group has less than 2 members - ungroup remaining
                members.forEach(m => {
                    m.groupId = null;
                    m.groupLeaderId = null;
                    m.groupOffsetX = null;
                    m.groupOffsetY = null;
                });
                console.log(`[GROUP] Auto-ungrouped single member from group ${groupId}`);
                return;
            }
            
            // Check if leader still exists
            const leaderId = members[0]?.groupLeaderId;
            const leaderExists = leaderId && members.some(m => m.id === leaderId);
            
            if (!leaderExists) {
                // Leader was deleted - assign new leader
                const newLeader = this.findLeader(members);
                if (newLeader) {
                    const newLeaderPos = newLeader.type === 'unbound'
                        ? { x: (newLeader.start.x + newLeader.end.x) / 2, y: (newLeader.start.y + newLeader.end.y) / 2 }
                        : { x: newLeader.x, y: newLeader.y };
                    
                    members.forEach(m => {
                        m.groupLeaderId = newLeader.id;
                        const memberPos = m.type === 'unbound'
                            ? { x: (m.start.x + m.end.x) / 2, y: (m.start.y + m.end.y) / 2 }
                            : { x: m.x, y: m.y };
                        m.groupOffsetX = memberPos.x - newLeaderPos.x;
                        m.groupOffsetY = memberPos.y - newLeaderPos.y;
                    });
                    console.log(`[GROUP] Assigned new leader ${newLeader.id} for group ${groupId}`);
                }
            }
        });
    }

    // ========== DRAG SETUP ==========

    /**
     * Set up multi-select drag for group members
     * @param {object} pos - Current position {x, y}
     * @returns {boolean} True if group drag was set up
     */
    setupDrag(pos) {
        const selected = this.editor.selectedObjects;
        if (selected.length <= 1) return false;
        
        // Stop momentum before capturing - prevents TB+shape jump
        if (this.editor.momentum) {
            this.editor.momentum.stopAll();
            this.editor.momentum.reset();
        }
        
        // Block: BUL (merged) links grouped with devices/shapes/text - moving fails
        const hasMergedLinks = selected.some(o =>
            o.type === 'unbound' && (o.mergedWith || o.mergedInto)
        );
        const hasOtherObjects = selected.some(o =>
            o.type === 'device' || o.type === 'shape' || o.type === 'text'
        );
        if (hasMergedLinks && hasOtherObjects) {
            if (this.editor.showToast) {
                this.editor.showToast(
                    'BUL chains grouped with devices/shapes cannot be moved together. Ungroup first, or move each separately.',
                    'warning'
                );
            }
            return false;
        }
        
        this.editor.dragStart = { x: pos.x, y: pos.y };
        this.editor.dragStartTime = Date.now();
        this.editor.multiSelectInitialPositions = selected.map(obj => {
            const initPos = { id: obj.id, x: obj.x, y: obj.y };
            if (obj.type === 'unbound') {
                initPos.startX = obj.start.x;
                initPos.startY = obj.start.y;
                initPos.endX = obj.end.x;
                initPos.endY = obj.end.y;
                initPos.curvePointX = obj.manualCurvePoint?.x;
                initPos.curvePointY = obj.manualCurvePoint?.y;
                initPos.controlPointX = obj.manualControlPoint?.x;
                initPos.controlPointY = obj.manualControlPoint?.y;
            }
            return initPos;
        });
        
        // Populate Quick Link and Attached UL CPs (prevents jump when group has devices)
        const deviceIds = selected.filter(o => o.type === 'device').map(o => o.id);
        this.editor._initialQuickLinkCPs = this.editor.objects
            .filter(obj => obj.type === 'link' &&
                (deviceIds.includes(obj.device1) || deviceIds.includes(obj.device2)) &&
                (obj.manualCurvePoint || obj.manualControlPoint))
            .map(ql => ({
                id: ql.id,
                curvePointX: ql.manualCurvePoint?.x,
                curvePointY: ql.manualCurvePoint?.y,
                controlPointX: ql.manualControlPoint?.x,
                controlPointY: ql.manualControlPoint?.y,
                bothEndpointsMoved: deviceIds.includes(ql.device1) && deviceIds.includes(ql.device2)
            }));
        const selectedLinkIds = selected.filter(o => o.type === 'unbound').map(o => o.id);
        this.editor._initialAttachedULCPs = this.editor.objects
            .filter(obj => obj.type === 'unbound' &&
                obj.manualCurvePoint &&
                !selectedLinkIds.includes(obj.id) &&
                (deviceIds.includes(obj.device1) || deviceIds.includes(obj.device2)))
            .map(ul => ({
                id: ul.id,
                curvePointX: ul.manualCurvePoint?.x,
                curvePointY: ul.manualCurvePoint?.y,
                bothEndpointsMoved: deviceIds.includes(ul.device1) && deviceIds.includes(ul.device2)
            }));
        
        this.editor._pendingDrag = {
            object: this.editor.selectedObject,
            isMultiSelect: true,
            isGroup: true,
            startX: pos.x,
            startY: pos.y,
            dragStart: { ...this.editor.dragStart },
            multiSelectInitialPositions: [...this.editor.multiSelectInitialPositions],
            _initialQuickLinkCPs: this.editor._initialQuickLinkCPs ? [...this.editor._initialQuickLinkCPs] : [],
            _initialAttachedULCPs: this.editor._initialAttachedULCPs ? [...this.editor._initialAttachedULCPs] : [],
            threshold: 5
        };
        
        return true;
    }
}

// Factory function
window.createGroupManager = function(editor) {
    return new GroupManager(editor);
};

// Export for module use
window.GroupManager = GroupManager;
