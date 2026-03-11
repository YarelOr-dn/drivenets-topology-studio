# Text Placement & Link Table Improvements - December 4, 2025

## Issues to Fix

### 1. Text Placement Issues
- Text doesn't work as specified  
- Text disappears when selecting and dragging

### 2. Link Table Improvements
- Add color transitions between columns
- Make actions editable
- Add DNOS VLAN manipulation options (pop-pop, swap-swap)
- Make VLAN values editable  
- Smart VLAN detection (ingress from device, egress to device after manipulations, bidirectional)

## Investigation Summary

### Text Placement Analysis

Current behavior:
- Text is placed when clicking in text mode
- Text can be selected by clicking on it
- Text can be dragged
- `draw()` is called after dragging ends

The issue might be:
1. Text selection is not being maintained after drag
2. Text tool mode might be interfering with selection
3. Draw might not be rendering text properly

### Link Table Analysis

Current implementation needs:
1. Visual styling with color transitions
2. Editable action dropdowns
3. DNOS-specific VLAN options
4. Bidirectional VLAN tracking

## Implementation Plan

### Phase 1: Fix Text Issues (IN PROGRESS)
- Ensure text stays selected after dragging
- Prevent mode changes that clear selection
- Verify draw() renders selected text

### Phase 2: Link Table Enhancements
- Add CSS transitions for column colors
- Implement editable action cells
- Add DNOS VLAN manipulation dropdown
- Implement smart VLAN detection

## Next Steps

1. Test current text behavior in browser
2. Identify exact reproduction steps for text disappearing
3. Implement fixes
4. Add link table improvements





