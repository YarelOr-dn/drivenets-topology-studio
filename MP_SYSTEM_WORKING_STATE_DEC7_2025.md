# MP (Moving Point) System - Working State Documentation
## Date: December 7, 2025

This document explains the working MP system logic for BUL (Bundled Unbound Link) chains. Use this as a reference if things break in the future.

---

## Core Concepts

### Data Structures

Each UL (Unbound Link) in a BUL chain has:
- `start` and `end` - the actual {x, y} positions of the link endpoints
- `device1` and `device2` - if set, means that endpoint is attached to a device (TP)
- `mergedWith` - metadata about the CHILD link (the link this one connects to downstream)
- `mergedInto` - metadata about the PARENT link (the link this one connects to upstream)

### Chain Structure Example

```
UL-1 (Head) → UL-2 (Middle) → UL-3 (Middle) → UL-4 (Tail)
      MP-1         MP-2            MP-3
```

- **Head (UL-1)**: Only has `mergedWith`, no `mergedInto`
- **Middle (UL-2, UL-3)**: Has BOTH `mergedWith` AND `mergedInto`
- **Tail (UL-4)**: Only has `mergedInto`, no `mergedWith`

### MP Storage

Each MP is stored in TWO places (both must stay synchronized):

1. **Parent's `mergedWith.connectionPoint`** - the parent link stores the MP position
2. **Child's `mergedInto.connectionPoint`** - the child link also stores the MP position

**CRITICAL**: These must be CLONES, not shared references!

```javascript
// CORRECT - Clone the connectionPoint
parentLink.mergedWith = {
    connectionPoint: { x: connectionPoint.x, y: connectionPoint.y }, // Clone!
    ...
};
childLink.mergedInto = {
    connectionPoint: { x: connectionPoint.x, y: connectionPoint.y }, // Clone!
    ...
};

// WRONG - Shared reference causes MPs to jump
parentLink.mergedWith = {
    connectionPoint: connectionPoint, // WRONG! Shared reference
    ...
};
```

---

## Key Metadata Fields

### `mergedWith` (on parent link)
```javascript
parentLink.mergedWith = {
    linkId: childLink.id,                    // ID of child link
    connectionPoint: { x, y },               // MP position (CLONED!)
    connectionEndpoint: 'start' or 'end',    // Which endpoint of PARENT connects
    childConnectionEndpoint: 'start' or 'end', // Which endpoint of CHILD connects
    parentFreeEnd: 'start' or 'end',         // Which endpoint of parent is FREE (TP)
    childFreeEnd: 'start' or 'end',          // Which endpoint of child is FREE (TP)
    ...
};
```

### `mergedInto` (on child link)
```javascript
childLink.mergedInto = {
    parentId: parentLink.id,                 // ID of parent link
    connectionPoint: { x, y },               // MP position (CLONED!)
    childEndpoint: 'start' or 'end',         // Which endpoint of THIS link connects
    parentEndpoint: 'start' or 'end',        // Which endpoint of parent connects
};
```

---

## MP Detection Logic (`findUnboundLinkEndpoint`)

When user clicks, we need to find the closest MP:

1. **First pass**: Check for TPs (free endpoints) - TPs have priority over MPs
2. **Second pass**: Check all connection points in all chains

For each link in a chain:
- Check `chainLink.mergedWith.connectionPoint` (if this link is a parent)
- Check `chainLink.mergedInto.connectionPoint` (if this link is a child)

**Return the CLOSEST MP**, not just the first found:
```javascript
if (distConn < mpHitRadius && distConn < closestMPDistance) {
    const connectedEndpoint = chainLink.mergedWith.connectionEndpoint; // USE STORED VALUE!
    closestMP = { link: chainLink, endpoint: connectedEndpoint, isConnectionPoint: true };
    closestMPDistance = distConn;
}
```

**CRITICAL**: Use the STORED `connectionEndpoint` value, not a calculated fallback!

---

## MP Dragging Logic (`handleMouseMove`)

When dragging an MP:

### 1. Determine if it's a Middle Link
```javascript
const isMiddleLink = this.stretchingLink.mergedWith && this.stretchingLink.mergedInto;
```

### 2. For Middle Links - Use Stored Endpoints
```javascript
if (isMiddleLink) {
    // Get ACTUAL endpoint values from metadata
    const parentConnectionEndpoint = this.stretchingLink.mergedInto.childEndpoint;
    const childConnectionEndpoint = this.stretchingLink.mergedWith.connectionEndpoint;
    
    // Determine which connection the grabbed endpoint belongs to
    const grabbedIsParentConnection = (this.stretchingEndpoint === parentConnectionEndpoint);
    const grabbedIsChildConnection = (this.stretchingEndpoint === childConnectionEndpoint);
    
    if (grabbedIsParentConnection) {
        // Moving the MP that connects to parent
        partnerLink = findParentLink();
    } else if (grabbedIsChildConnection) {
        // Moving the MP that connects to child
        partnerLink = findChildLink();
    }
}
```

**WRONG approach** (old bug):
```javascript
// DON'T assume start=parent and end=child!
if (this.stretchingEndpoint === 'start') {
    partnerLink = parent; // WRONG - endpoint could be either!
}
```

### 3. Update BOTH Connection Points
When moving an MP, update both clones:
```javascript
// Update stretching link's connection point
if (this.stretchingLink.mergedWith.connectionPoint) {
    this.stretchingLink.mergedWith.connectionPoint.x = newX;
    this.stretchingLink.mergedWith.connectionPoint.y = newY;
}

// Update partner link's connection point (the other clone)
if (partnerLink.mergedInto.connectionPoint) {
    partnerLink.mergedInto.connectionPoint.x = newX;
    partnerLink.mergedInto.connectionPoint.y = newY;
}
```

---

## Common Bugs and Solutions

### Bug 1: MPs Jump to Wrong Position
**Cause**: Connection points shared same object reference
**Fix**: Clone when creating: `{ x: connectionPoint.x, y: connectionPoint.y }`

### Bug 2: Only Newest MP Works
**Cause**: Detection returned first MP found, not closest
**Fix**: Track `closestMPDistance` and only update if new MP is closer

### Bug 3: Wrong MP Moves (e.g., MP-2 moves when grabbing MP-3)
**Cause**: Code assumed `start` = parent connection, `end` = child connection
**Fix**: Read actual values from `mergedInto.childEndpoint` and `mergedWith.connectionEndpoint`

### Bug 4: Middle Link Drags Wrong Partner
**Cause**: Didn't check WHICH endpoint was grabbed on middle links
**Fix**: Compare grabbed endpoint against both stored endpoints to determine partner

---

## Testing Checklist

1. ✅ Create 2-link BUL - MP-1 should work
2. ✅ Create 3-link BUL - Both MP-1 and MP-2 should work independently
3. ✅ Create 4-link BUL - All MPs should work independently
4. ✅ Drag MP-1 - Only MP-1 should move, not MP-2
5. ✅ Drag MP-2 on 3-link - Only MP-2 should move
6. ✅ All TP connection combinations should work (TP-1↔TP-1, TP-1↔TP-2, TP-2↔TP-1, TP-2↔TP-2)

---

## Key Files and Line Numbers (as of Dec 7, 2025)

- **MP Detection**: `topology.js` ~lines 11011-11090 (`findUnboundLinkEndpoint`)
- **MP Dragging**: `topology.js` ~lines 2745-2920 (`handleMouseMove`, `stretchingConnectionPoint` block)
- **Merge Creation**: `topology.js` ~lines 5044-5098 (where `mergedWith` and `mergedInto` are set)
- **BUL Extension**: `topology.js` ~lines 4811-4922 (standalone UL joining BUL)

---

## Revert Instructions

If the MP system breaks in the future, check:

1. Are connection points being CLONED (not shared)?
2. Is MP detection using stored `connectionEndpoint` values?
3. Is middle link dragging checking actual endpoint metadata?
4. Are BOTH connection point clones being updated during drag?

If all else fails, compare against this documentation and the working state saved on Dec 7, 2025.



















