# TP/MP Numbering System for BUL Debugging

## Overview
Visual numbering has been added to all Terminal Points (TPs) and Moving Points (MPs) to make BUL structure instantly visible and help detect bugs immediately.

---

## Numbering Scheme

### Individual ULs (Not in BUL)
Each standalone UL shows:
- **S** = Start endpoint (TP at start)
- **E** = End endpoint (TP at end)

```
    S ━━━━━━━━━━━ E
  (start)        (end)
```

### BUL Chains (2+ ULs Merged)

#### TPs (Terminal Points - Gray Dots)
- **TP1** = First free endpoint in the BUL chain
- **TP2** = Second free endpoint in the BUL chain
- Below each TP: **U#** = Which UL this TP belongs to

```
Example: 3-Link BUL

TP1     MP1     MP2     TP2
 U1      U1      U2      U3
  ⚪ ━━ 🟣 ━━ 🟣 ━━ ⚪
 UL1    (conn)  (conn)  UL3
```

#### MPs (Moving Points - Purple Dots)
- **MP1, MP2, MP3...** = Numbered sequentially through the chain
- Below each MP: **U#** = Which UL this MP endpoint belongs to

```
Example: 4-Link BUL

TP1     MP1     MP2     MP3     TP2
 U1      U1      U2      U3      U4
  ⚪ ━━ 🟣 ━━ 🟣 ━━ 🟣 ━━ ⚪
```

---

## What the Numbers Tell You

### Correct 3-Link BUL Structure
```
Visual:
TP1     MP1     MP2     TP2
 U1      U1      U2      U3
  ⚪ ━━ 🟣 ━━ 🟣 ━━ ⚪

Console:
1. unbound_1: [MP]━━━[TP] (PARENT)   → Shows MP1 at start, TP1 at end
2. unbound_2: [MP]━━━[MP] (MIDDLE)   → Shows MP1 at start, MP2 at end
3. unbound_3: [TP]━━━[MP] (CHILD)    → Shows TP2 at start, MP2 at end

Total: 2 TPs, 2 MPs ✅
```

### Incorrect Structure (Bug Present)
```
Visual:
TP1     TP2     MP1     TP3
 U1      U2      U2      U3
  ⚪ ━━ ⚪ ━━ 🟣 ━━ ⚪

Console:
Total: 3 TPs, 1 MPs ❌

Problem: UL2 has TP2 when it should have MP1!
```

---

## Using the Numbering System

### Step 1: Enable Link Labels (Optional)
Click the "Labels: OFF/ON" button in the top bar to see UL1, UL2, UL3 labels on each link.

### Step 2: Create a BUL
1. Press Cmd+L three times (creates UL1, UL2, UL3)
2. Merge them together
3. Look at the endpoints

### Step 3: Verify Structure
Check the visual labels:

✅ **Correct 3-Link BUL**:
- You should see exactly **2 gray dots** labeled TP1 and TP2
- You should see exactly **2 purple dots** labeled MP1 and MP2
- Middle link (UL2) should have **NO gray dots** - only purple MPs

❌ **Incorrect (Bug)**:
- More than 2 gray TPs visible
- Wrong number of purple MPs
- Middle link has gray TPs (should be all MPs)

### Step 4: Check Console
The console will show validation:
```
Total: 2 TPs, 2 MPs ✅  // Correct
Total: 3 TPs, 2 MPs ❌  // Wrong! Shows bug
```

---

## Interpreting the Labels

### Label Format on Canvas

**For TPs**:
```
TP1  ← BUL TP number (1 or 2)
 U3  ← Which UL (1, 2, 3, etc.)
```

**For MPs**:
```
MP2  ← MP number in chain (1, 2, 3, etc.)
 U2  ← Which UL this endpoint belongs to
```

### What Each Label Means

| Label | Meaning | Expected Count |
|-------|---------|---------------|
| TP1 | First free endpoint in BUL | Always 1 |
| TP2 | Second free endpoint in BUL | Always 1 |
| MP1 | First connection point | N-1 for N links |
| MP2 | Second connection point | (if 3+ links) |
| MP3 | Third connection point | (if 4+ links) |
| U1, U2, U3 | Which UL number (1=first created) | 1 per link |

---

## Examples with Different Chain Lengths

### 2-Link BUL
```
TP1 ━━ MP1 ━━ TP2
 U1     U1     U2

Structure:
- UL1: [MP1 at start, TP1 at end]
- UL2: [TP2 at start, MP1 at end]
- Total: 2 TPs, 1 MP ✅
```

### 3-Link BUL
```
TP1 ━━ MP1 ━━ MP2 ━━ TP2
 U1     U1     U2     U3

Structure:
- UL1: [MP1 at start, TP1 at end]
- UL2: [MP1 at start, MP2 at end] ← BOTH SHOULD BE MPs!
- UL3: [TP2 at start, MP2 at end]
- Total: 2 TPs, 2 MPs ✅
```

### 4-Link BUL
```
TP1 ━━ MP1 ━━ MP2 ━━ MP3 ━━ TP2
 U1     U1     U2     U3     U4

Structure:
- UL1: [MP1 at one end, TP1 at other]
- UL2: [MP1 at one end, MP2 at other] ← MIDDLE
- UL3: [MP2 at one end, MP3 at other] ← MIDDLE
- UL4: [TP2 at one end, MP3 at other]
- Total: 2 TPs, 3 MPs ✅
```

### 5-Link BUL
```
TP1 ━━ MP1 ━━ MP2 ━━ MP3 ━━ MP4 ━━ TP2
 U1     U1     U2     U3     U4     U5

Total: 2 TPs, 4 MPs ✅
```

---

## Debugging with Numbering

### Problem Detection

If you see:
- **More than 2 TPs** → Bug: Middle link has TP when it shouldn't
- **Wrong MP count** → Bug: Merge structure incorrect
- **TP on middle UL** → Bug: That endpoint should be an MP
- **Duplicate numbers** → Bug: Counting logic error

### Example Bug Scenario

**What You See**:
```
TP1 ━━ TP2 ━━ MP1 ━━ TP3
 U1     U2     U2     U3
```

**Diagnosis**:
- ❌ 3 TPs (should be 2)
- ❌ UL2 has TP2 (should be MP)
- ❌ Structure shows UL2 not properly connected to UL1

**Root Cause**:
- UL2's start should be an MP (connected to UL1)
- But it's showing as TP (free endpoint)
- This means the merge between UL1 and UL2 is broken

---

## How MPs Are Numbered

MPs are numbered based on the order they appear in the parent→child chain:

1. **MP1**: Connection between first parent and its child
2. **MP2**: Connection between second parent and its child  
3. **MP3**: Connection between third parent and its child
4. etc.

### Example with 3 Links:
```
Chain: UL1 → UL2 → UL3

- UL1.mergedWith points to UL2 → Creates MP1
- UL2.mergedWith points to UL3 → Creates MP2

Result:
UL1: [MP1]━━━[TP1]
UL2: [MP1]━━━[MP2]  ← Both ends are MPs
UL3: [TP2]━━━[MP2]
```

---

## Validation Rules

For any N-link BUL to be correct:

✅ **Exactly 2 TPs** (TP1 and TP2)  
✅ **Exactly N-1 MPs** (MP1, MP2, ..., MP(N-1))  
✅ **Edge ULs** (U1 and UN) have 1 TP each  
✅ **Middle ULs** (U2 through UN-1) have 2 MPs each  
✅ **No duplicate TP numbers**  
✅ **Sequential MP numbers** (1, 2, 3, ...)  

---

## Console Output Correlation

When you merge links, the console shows:

```
📊 Complete BUL Structure:
   1. unbound_1: [MP]━━━[TP] (PARENT)
   2. unbound_2: [MP]━━━[MP] (MIDDLE)
   3. unbound_3: [TP]━━━[MP] (CHILD)
   Total: 2 TPs, 2 MPs
```

This matches the visual labels:
- **[MP]━━━[TP]** for UL1 → Shows MP1 at start (U1), TP1 at end (U1)
- **[MP]━━━[MP]** for UL2 → Shows MP1 at start (U2), MP2 at end (U2)
- **[TP]━━━[MP]** for UL3 → Shows TP2 at start (U3), MP2 at end (U3)

---

## Quick Reference Card

| Symbol | Color | Label Format | Meaning |
|--------|-------|--------------|---------|
| ⚪ | Gray | TP1/TP2 + U# | Free terminal point |
| 🟣 | Purple | MP# + U# | Connection point (movable) |
| S/E | Gray | S or E | Start/End (individual UL) |

### Legend
- **TP#**: Which BUL TP (1 or 2)
- **MP#**: Which MP in chain (1, 2, 3...)
- **U#**: Which UL (1, 2, 3...)
- **S**: Start of standalone UL
- **E**: End of standalone UL

---

## Testing with Numbering

### Test Case: Create 3-Link BUL

**Step 1**: Create 3 ULs
```
UL1:  S ━━━ E
UL2:  S ━━━ E  
UL3:  S ━━━ E
```

**Step 2**: Merge UL1 + UL2
```
Expected:
TP1 ━━ MP1 ━━ TP2
 U1     U1     U2

If correct: 2 labels total (TP1-U1, TP2-U2)
If wrong: More than 2 TPs
```

**Step 3**: Merge UL3 to UL2's free TP
```
Expected:
TP1 ━━ MP1 ━━ MP2 ━━ TP2
 U1     U1     U2     U3

Visual Check:
✅ Exactly 2 gray dots (TP1-U1, TP2-U3)
✅ Exactly 2 purple dots (MP1-U1, MP2-U2)
✅ UL2 (middle) has NO gray dots
✅ Console shows: "Total: 2 TPs, 2 MPs"
```

---

## Debug Output Enhancement

The console now shows:
```
✅ BUL extended! Now 3 links in chain
   Parent: unbound_1 (free: end)
   Child: unbound_3 (free: end)
   MP at: (250, 300)
📊 Complete BUL Structure:
   1. unbound_1: [MP]━━━[TP] (PARENT)
   2. unbound_2: [MP]━━━[MP] (MIDDLE)  ← Should have MPs on BOTH ends
   3. unbound_3: [TP]━━━[MP] (CHILD)
   Total: 2 TPs, 2 MPs
```

Match this with the visual labels to verify correctness!

---

## Implementation Details

### Code Locations

**TP Labeling**: `topology.js` lines 11220-11245, 11359-11384

**MP Labeling**: `topology.js` lines 11276-11290, 11407-11421

### How It Works

1. **Get all links in BUL**: `getAllMergedLinks(link)`
2. **Count TPs in chain**: Iterate through all links, check which endpoints are TPs
3. **Number TPs**: TP1 is first found, TP2 is second
4. **Count MPs**: Each `mergedWith` relationship is an MP
5. **Number MPs**: Sequential numbering (1, 2, 3...)
6. **Find UL number**: Index of link in chain + 1

### Visual Styling

- **TP labels**: 8px bold font, white text on gray circle
- **MP labels**: 7px bold font, white text on purple circle
- **UL numbers**: 6px font below the TP/MP label
- **All labels**: Scaled with zoom for readability

---

## Benefits

### Instant Visual Verification
- ✅ See exact TP/MP count at a glance
- ✅ Identify which UL each point belongs to
- ✅ Spot structural errors immediately
- ✅ No need to check console for basic validation

### Enhanced Debugging
- ✅ Match visual labels with console output
- ✅ Trace which UL is causing issues
- ✅ Verify MP numbering sequence
- ✅ Confirm middle links have no TPs

### Better Testing
- ✅ Create test cases and verify visually
- ✅ Screenshot bugs with labels visible
- ✅ Share issues with clear visual evidence
- ✅ Track complex BUL chains easily

---

## Troubleshooting Guide

### If You See More Than 2 TPs

**Problem**: TP count > 2
**Cause**: A middle link has a TP when both ends should be MPs
**Fix**: Check the merge logic - the middle link's free end calculation is wrong

**Look for**:
- Which UL has the extra TP (check U# label)
- Is that UL in the middle of the chain?
- Console should show WRONG TP COUNT error

### If You See Wrong MP Count

**Problem**: MP count ≠ (link count - 1)
**Cause**: Missing merge relationship or duplicate merges
**Fix**: Check `mergedWith` and `mergedInto` relationships

### If MP Labels Show Wrong UL Numbers

**Problem**: MP1 shows U3, but it's between U1 and U2
**Cause**: Chain order is wrong or counting is incorrect
**Fix**: Check link sorting (by createdAt timestamp)

---

## Expected Label Patterns

### 2-Link BUL
```
Canvas:     TP1-U1 ━━ MP1-U1 ━━ TP2-U2
Console:    2 TPs, 1 MPs ✅
```

### 3-Link BUL
```
Canvas:     TP1-U1 ━━ MP1-U1 ━━ MP2-U2 ━━ TP2-U3
Console:    2 TPs, 2 MPs ✅
```

### 4-Link BUL
```
Canvas:     TP1-U1 ━━ MP1-U1 ━━ MP2-U2 ━━ MP3-U3 ━━ TP2-U4
Console:    2 TPs, 3 MPs ✅
```

### 5-Link BUL
```
Canvas:     TP1-U1 ━━ MP1-U1 ━━ MP2-U2 ━━ MP3-U3 ━━ MP4-U4 ━━ TP2-U5
Console:    2 TPs, 4 MPs ✅
```

---

## Summary

### What You Can Now See

✅ **TP numbering**: TP1, TP2 (always exactly 2 in a BUL)  
✅ **MP numbering**: MP1, MP2, MP3... (N-1 for N links)  
✅ **UL identification**: U1, U2, U3... (which UL the point belongs to)  
✅ **Visual validation**: Instantly see if structure is correct  
✅ **Console correlation**: Match visual with console output  

### How to Use

1. **Create BUL** → Look at labels
2. **Verify structure** → Check TP and MP counts
3. **Test operations** → Drag MPs, watch labels
4. **Debug issues** → Screenshot with labels visible
5. **Report bugs** → Share labeled screenshots + console output

The numbering system makes BUL structure debugging **crystal clear**! 🎯

---

*Feature added: 2025-11-27*  
*Purpose: Enhanced BUL debugging*  
*Status: ACTIVE ✅*










