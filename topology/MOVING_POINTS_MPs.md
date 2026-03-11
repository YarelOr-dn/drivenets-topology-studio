# Moving Points (MPs) - Connection Point Dragging

## Overview

Connection points between merged ULs are now **draggable Moving Points (MPs)**. You can drag them to adjust the link routing without moving the free endpoints (TPs).

## Terminology

- **TP (Termination Point)** = Free endpoint that can merge with other ULs
- **MP (Moving Point)** = Connection point where two ULs merge (purple circle 🟣)
- **BUL (Bound ULs)** = Two or more ULs that are merged together

## Behavior

### MPs are Draggable ✅

When you click and drag a purple connection point (MP):
- **MP moves** to the new position ✅
- **Both connected endpoints** move with the MP ✅
- **Free endpoints (TPs)** stay fixed 🔒
- **Link shape adjusts** smoothly ✅

### Visual Representation

```
Before dragging MP:
UL1 🔘----------🟣----------🔘 UL2
   TP          MP          TP
   (free)   (connection)   (free)

After dragging MP up:
UL1 🔘        
      \       🟣 MP (dragged up)
       \    /
        \ /
UL2      🔘
        TP
```

### What Moves vs What Stays Fixed

| Element | When Dragging MP | Status |
|---------|------------------|--------|
| **MP (connection point)** | Follows mouse | ✅ Moves |
| **Connected endpoints** | Move with MP | ✅ Moves |
| **Free endpoints (TPs)** | Stay in place | 🔒 Fixed |
| **Link shape** | Adjusts smoothly | ✅ Updates |

## Use Cases

### 1. Routing Around Obstacles

```
Before:
Device1
  |
  🟣---- straight line ----🔘 UL2
  |
UL1

After dragging MP:
Device1
  |    🟣 (moved left)
  |   / \
  | /     \
UL1       🔘 UL2
```

### 2. Creating Complex Topologies

```
Star topology with adjustable connection points:

    🔘 UL1
     |
     🟣 (MP - adjustable)
    /|\
   / | \
 🔘 🔘 🔘
UL2 UL3 UL4
```

### 3. Fine-Tuning Link Angles

Drag MPs to adjust the angle and curvature of merged links for better visual clarity.

## How to Use

### Creating an MP

1. **Create two ULs**: Double-tap or Cmd+L twice
2. **Merge them**: Drag one TP to another TP
3. **MP appears**: Purple connection point 🟣 forms at merge location

### Dragging an MP

1. **Hover over MP**: Purple connection point 🟣
2. **Click and drag**: MP follows your mouse
3. **Release**: MP stays at new position
4. **Result**: Link shape adjusts, TPs stay fixed

### Important Notes

- ✅ **MPs are draggable** - Click and drag purple connection points
- 🔒 **TPs stay fixed** - Free endpoints don't move when dragging MP
- ✅ **Smooth adjustment** - Links bend naturally around the MP
- 🚫 **MPs can't merge** - Connection points are for routing only

## Technical Implementation

### Detection (findUnboundLinkEndpoint)

```javascript
// Check connection points FIRST (higher priority)
if (obj.mergedWith && obj.mergedWith.connectionPoint) {
    const distConn = sqrt(distance to connection point);
    if (distConn < connectionPointRadius) {
        return { 
            link: obj, 
            endpoint: connectedEndpoint, 
            isConnectionPoint: true  // Mark as MP
        };
    }
}
```

### Dragging (handleMouseMove)

```javascript
// Special handling for MPs
if (this.stretchingConnectionPoint) {
    // Update the stretching link's endpoint
    this.stretchingLink[endpoint] = { x: pos.x, y: pos.y };
    
    // Update partner link's connected endpoint
    partnerLink[partnerEndpoint] = { x: pos.x, y: pos.y };
    
    // Update connection point metadata
    connectionPoint.x = pos.x;
    connectionPoint.y = pos.y;
    
    // TPs (free endpoints) remain unchanged!
}
```

## Examples

### Example 1: Simple Chain Adjustment

```
Initial:
UL1 ----🟣---- UL2 ----🟣---- UL3
       MP1           MP2

Drag MP1 up, MP2 down:
UL1 \    🟣 MP1
     \  /
      \/
      /\
     /  \
UL2 /    🟣 MP2
              \
               🔘 UL3
```

### Example 2: Star Topology

```
      🔘 UL1
       |
Device--🟣--🔘 UL2
       |
      🔘 UL3
```

Drag MPs to adjust spoke angles without moving UL endpoints!

## Key Differences from Before

| Feature | Before | After |
|---------|--------|-------|
| MP dragging | ❌ Not supported | ✅ Fully supported |
| What moves | Entire BUL chain | Only MP + connected points |
| TPs (free endpoints) | Moved with chain | Stay fixed 🔒 |
| Use case | Limited routing | Flexible routing ✅ |
| Visual feedback | Purple (non-interactive) | Purple (draggable) ✨ |

## Benefits

1. ✅ **Flexible Routing**: Adjust link paths without breaking merges
2. ✅ **Fixed TPs**: Free endpoints stay where you put them
3. ✅ **Visual Control**: Drag MPs for precise link positioning
4. ✅ **No Unintended Movement**: Only MPs move, not the whole chain
5. ✅ **Intuitive**: Purple MPs are clearly draggable

## Rules Summary

### Can Do ✅
- Drag MPs (purple 🟣) to adjust routing
- Free endpoints (TPs) can still merge with other ULs
- MPs work with any number of merged ULs
- Create complex routing with multiple MPs

### Cannot Do 🚫
- Merge new ULs at MPs (use TPs instead)
- Move TPs by dragging MPs (they stay fixed)
- Drag MPs onto devices (MPs are for routing only)

## Testing

1. **Create 2 ULs** and merge them
2. **Purple MP appears** at connection point
3. **Click and drag MP** - should move smoothly
4. **Free endpoints stay fixed** - verify TPs don't move
5. **Link shape adjusts** - curves follow MP
6. **Works with chains** - create UL1→UL2→UL3, drag middle MP

## Summary

- **MPs (Moving Points)** = Draggable connection points 🟣
- **TPs (Termination Points)** = Fixed free endpoints 🔘
- **Drag MPs** to adjust link routing
- **TPs stay fixed** when dragging MPs
- **Perfect for** complex topology routing!

