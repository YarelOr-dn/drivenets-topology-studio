# Movable Connection Points for Merged ULs

## Feature Overview

When two Unbound Links (ULs) are merged together, the connection point where they meet is now visible and can be moved independently. This allows for better control over the shape and routing of merged links.

## Visual Indicators

### Connection Point Appearance
- **Color**: Purple/Magenta (#9b59b6 / #8e44ad)
- **Shape**: Circle with outer ring and cross indicator inside
- **Size**: 6px radius (normal), 8px radius (selected)
- **Cross Indicator**: White cross inside the circle to show it's movable

### Regular Endpoints
- **Unattached**: Gray (#666)
- **Attached to Device**: Green (#27ae60) with green ring
- **Near Device (ready to attach)**: Orange (#f39c12)
- **Selected**: Blue (#3498db)

## How It Works

### 1. **Merging ULs**
When you stretch one UL endpoint near another UL endpoint:
- The two ULs merge into one logical link
- The connection point is stored in metadata
- Both links remain as separate objects but are linked together

### 2. **Connection Point Detection**
- Connection points have a larger hit area (12px / zoom) than regular endpoints
- Click detection prioritizes connection points over regular endpoints
- Both the parent and child links can be clicked to access the connection point

### 3. **Dragging Connection Points**
When you drag a connection point:
- **Both** merged links move their connected endpoints together
- The connection stays intact
- The free endpoints of both links remain in place
- The connection point metadata is updated in real-time

### 4. **Link Synchronization**
The system automatically keeps the merged links synchronized:
- When dragging the parent link's free endpoint, the child's connected endpoint follows
- When dragging the child link's free endpoint, the parent's connected endpoint follows
- When dragging the connection point, both connected endpoints move together

## Usage Instructions

### Creating Merged ULs
1. Create an Unbound Link (Cmd+L or double-tap background)
2. Create another Unbound Link
3. Drag one UL's endpoint near the other UL's endpoint
4. They will snap together and merge (purple connection point appears)

### Moving Connection Points
1. Click on the purple connection point (it will highlight)
2. Drag it to adjust the link routing
3. Both merged links will bend at the new connection point location
4. Release to set the new position

### Separating Merged ULs
To separate merged ULs, you would need to:
1. Delete one of the links, or
2. Drag an endpoint far enough away to break the connection (if implemented)

## Technical Implementation

### Modified Files
- `topology.js`: Main implementation

### Key Changes

1. **`drawUnboundLink()`** - Modified to draw connection points instead of hiding them
   - Lines 8693-8833: Added purple connection point rendering with cross indicator
   
2. **`findUnboundLinkEndpoint()`** - Enhanced to detect connection points
   - Lines 7525-7571: Added connection point hit detection with higher priority
   
3. **`handleMouseDown()`** - Modified to track connection point dragging
   - Line 1135: Store `isConnectionPoint` flag when initiating stretch
   
4. **`handleMouseMove()`** - Special handling for connection point dragging
   - Lines 2240-2306: Move both merged links' endpoints together when dragging connection point
   
5. **Constructor** - Added new flag
   - Line 48: `this.stretchingConnectionPoint` flag

### Data Structures

#### Parent Link (mergedWith)
```javascript
{
    linkId: 'child_link_id',
    connectionPoint: { x: 100, y: 200 },
    parentFreeEnd: 'start',  // Which end is free
    childFreeEnd: 'end',     // Which end of child is free
    childStart: { x: ..., y: ... },
    childEnd: { x: ..., y: ... },
    parentDevice: 'device_id',  // If attached
    childDevice: 'device_id'    // If attached
}
```

#### Child Link (mergedInto)
```javascript
{
    parentId: 'parent_link_id',
    connectionPoint: { x: 100, y: 200 }
}
```

## Benefits

1. **Better Link Routing**: Adjust the connection point to route links around obstacles
2. **Visual Clarity**: Purple connection points clearly show where links are merged
3. **Flexibility**: Move the connection point without breaking the merge
4. **Intuitive**: Drag-and-drop interface is familiar to users
5. **Consistency**: Connection points behave like other movable elements

## Future Enhancements

Possible future improvements:
- [ ] Snap connection points to grid
- [ ] Magnetic attraction between connection points and devices
- [ ] Break merge by dragging connection point far from both links
- [ ] Multiple connection points per link (more complex routing)
- [ ] Connection point labels/annotations
- [ ] Connection point properties (color, size, style)

