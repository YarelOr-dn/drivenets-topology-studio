# BUL TP/MP Numbering System - Complete Specification

## Overview
This document explains the intelligent numbering system for Terminal Points (TPs) and Moving Points (MPs) in BUL chains. The numbering helps instantly visualize the BUL structure and detect configuration errors.

---

## Numbering Principles

### **MP Numbering** = Creation Order 🕐
- **MP-1**: The first merge point created (when 2 ULs first connected)
- **MP-2**: The second merge point created (when 3rd UL connected)
- **MP-3**: The third merge point created (when 4th UL connected)
- **MP numbers NEVER change** after creation (permanent)
- Stored in `mergedWith.mpSequence` field

### **TP Numbering** = Positional 📍
- **TP-1**: The first current free endpoint of the BUL
- **TP-2**: The second current free endpoint of the BUL
- **TP numbers CAN change** as the BUL grows (dynamic)
- Always exactly 2 TPs in any BUL (one at each end)

---

## Visual Examples

### Example 1: Creating a 2-Link BUL

**Step 1: Two separate ULs**
```
UL1:  1 ━━━━━ 2       UL2:  1 ━━━━━ 2
    (start) (end)          (start) (end)
```

**Step 2: Merge UL1's endpoint-2 with UL2's endpoint-1**
```
Action: UL1-TP2 + UL2-TP1 → Creates MP-1 (first merge ever!)

Result:
  1      MP-1      2
 U1       U1      U2
  ⚪ ━━━ 🟣 ━━━ ⚪
 (TP-1)  (1st   (TP-2)
         merge)

BUL State:
- TP-1: UL1's start (free)
- MP-1: First connection created (UL1 end + UL2 start)
- TP-2: UL2's end (free)
- Total: 2 TPs, 1 MP ✅
```

---

### Example 2: Adding 3rd UL

**Step 3: Create UL3**
```
UL3:  1 ━━━━━ 2
```

**Step 4: Merge UL3's endpoint-1 with BUL's TP-2**
```
Action: UL3-TP1 + BUL-TP2 → Creates MP-2 (second merge!)

Before:
  1      MP-1      2      +   UL3
 U1       U1      U2          
  ⚪ ━━━ 🟣 ━━━ ⚪   
(TP-1)  (1st    (TP-2)      1 ━━ 2
        merge)  (becomes MP!)

After:
  1      MP-1     MP-2      2
 U1       U1      U2       U3
  ⚪ ━━━ 🟣 ━━━ 🟣 ━━━ ⚪
(TP-1)  (1st    (2nd     (TP-2)
        merge)  merge)  (NEW!)

BUL State:
- TP-1: UL1's start (still U1, still TP-1)
- MP-1: First connection (still numbered 1)
- MP-2: Second connection created (UL2 end + UL3 start)
- TP-2: UL3's end (NEW free endpoint, was U2, now U3)
- Total: 2 TPs, 2 MPs ✅
```

**Key Point**: 
- ✅ MP-1 keeps its number (creation order preserved)
- ✅ TP-2 moved to UL3 (positional - it's the new end)
- ✅ Old TP-2 became MP-2 (consumed by the merge)

---

### Example 3: Adding 4th UL to the OTHER End

**Step 5: Create UL4**
```
UL4:  1 ━━━━━ 2
```

**Step 6: Merge UL4's endpoint-2 with BUL's TP-1**
```
Action: UL4-TP2 + BUL-TP1 → Creates MP-3 (third merge!)

Before:
  1      MP-1     MP-2      2
 U1       U1      U2       U3
  ⚪ ━━━ 🟣 ━━━ 🟣 ━━━ ⚪
(TP-1)
(becomes MP!)

After:
  1      MP-3      MP-1     MP-2      2
 U4       U4       U1       U2       U3
  ⚪ ━━━ 🟣 ━━━ 🟣 ━━━ 🟣 ━━━ ⚪
(TP-1)  (3rd    (1st    (2nd     (TP-2)
(NEW!)  merge)  merge)  merge)

BUL State:
- TP-1: UL4's start (NEW free endpoint, was U1, now U4)
- MP-3: Third connection created (UL4 end + UL1 start)
- MP-1: First connection (STILL numbered 1, not changed!)
- MP-2: Second connection (STILL numbered 2)
- TP-2: UL3's end (still U3, still TP-2)
- Total: 2 TPs, 3 MPs ✅
```

**Key Points**:
- ✅ MP numbers reflect creation order: MP-1 (first), MP-2 (second), MP-3 (third)
- ✅ MP positions in chain don't matter - they keep their creation numbers
- ✅ TP-1 moved to UL4 (new end of chain)
- ✅ TP-2 stayed on UL3 (still the other end)

---

## Visual Legend

### On Canvas Labels

**For TPs (Gray Dots ⚪)**:
```
  1     ← TP number (1 or 2 - positional)
 U3     ← Which UL (1, 2, 3, 4...)
```

**For MPs (Purple Dots 🟣)**:
```
  2     ← MP number (1, 2, 3... - creation order)
 U2     ← Which UL this MP endpoint is on
```

**For Individual ULs** (not in BUL):
```
  1     ← Start endpoint
  2     ← End endpoint
```

---

## Complete Evolution Example

### Timeline: Creating a 5-Link BUL

#### **Time 0: Five Separate ULs**
```
UL1: 1 ━━ 2
UL2: 1 ━━ 2
UL3: 1 ━━ 2
UL4: 1 ━━ 2
UL5: 1 ━━ 2
```

#### **Time 1: First Merge (UL1 + UL2)**
```
Action: Create MP-1
Result:
  1      1      2
 U1     U1     U2
  ⚪ ━━ 🟣 ━━ ⚪
(TP-1) (MP-1) (TP-2)

State: 2 TPs, 1 MP
```

#### **Time 2: Second Merge (BUL + UL3)**
```
Action: BUL's TP-2 + UL3 → Create MP-2
Result:
  1      1      2      2
 U1     U1     U2     U3
  ⚪ ━━ 🟣 ━━ 🟣 ━━ ⚪
(TP-1) (MP-1) (MP-2) (TP-2)
                     (new!)

State: 2 TPs, 2 MPs
```

#### **Time 3: Third Merge (BUL + UL4)**
```
Action: BUL's TP-1 + UL4 → Create MP-3
Result:
  1      3      1      2      2
 U4     U4     U1     U2     U3
  ⚪ ━━ 🟣 ━━ 🟣 ━━ 🟣 ━━ ⚪
(TP-1) (MP-3) (MP-1) (MP-2) (TP-2)
(new!)

State: 2 TPs, 3 MPs
```

#### **Time 4: Fourth Merge (BUL + UL5)**
```
Action: BUL's TP-2 + UL5 → Create MP-4
Result:
  1      3      1      2      4      2
 U4     U4     U1     U2     U3     U5
  ⚪ ━━ 🟣 ━━ 🟣 ━━ 🟣 ━━ 🟣 ━━ ⚪
(TP-1) (MP-3) (MP-1) (MP-2) (MP-4) (TP-2)

State: 2 TPs, 4 MPs ✅

Final Structure:
- MPs numbered by creation: 1, 2, 3, 4
- TPs numbered by position: 1 (left), 2 (right)
- ULs numbered by creation: 1, 2, 3, 4, 5
```

---

## Key Rules

### Rule 1: MP Numbers Are Permanent
Once an MP is created with a number (e.g., MP-1), that number **never changes**, even if:
- More MPs are added before or after it
- The BUL is rearranged
- ULs are added to either end

**Example**:
- First merge ever → MP-1 (forever!)
- Second merge → MP-2 (forever!)
- Third merge → MP-3 (forever!)

### Rule 2: TP Numbers Are Positional
TP numbers represent the current position:
- **TP-1**: Whichever free endpoint comes first
- **TP-2**: Whichever free endpoint comes second

When a new UL is added:
- Old TP becomes an MP
- New UL's free endpoint becomes the new TP
- The TP number shifts to the new endpoint

**Example**:
```
Before: TP-1(U1) ━━ MP-1 ━━ TP-2(U2)
Add U3: TP-1(U1) ━━ MP-1 ━━ MP-2 ━━ TP-2(U3)
                                      ↑
                            TP-2 moved from U2 to U3!
```

### Rule 3: Always 2 TPs
Regardless of BUL length:
- ✅ 2 ULs → 2 TPs, 1 MP
- ✅ 3 ULs → 2 TPs, 2 MPs
- ✅ 4 ULs → 2 TPs, 3 MPs
- ✅ 5 ULs → 2 TPs, 4 MPs
- ✅ N ULs → 2 TPs, (N-1) MPs

---

## Implementation Details

### MP Sequence Tracking

**Data Structure**:
```javascript
parentLink.mergedWith = {
    linkId: childLink.id,
    connectionPoint: { x, y },
    parentFreeEnd: 'start' or 'end',
    childFreeEnd: 'start' or 'end',
    mpCreatedAt: Date.now(),        // Timestamp
    mpSequence: this.mpSequenceCounter++  // Sequential number (1, 2, 3...)
};
```

**Counter Management**:
- **Initialized**: `this.mpSequenceCounter = 1` in constructor
- **Incremented**: Each time a new MP is created
- **Persisted**: Saved in state history and file exports
- **Restored**: Loaded from saves and undo/redo operations

### TP Position Detection

**Algorithm**:
```javascript
// Find all TPs in the BUL
const tpsInBUL = [];
for (const chainLink of allLinks) {
    // Check if start is a TP (not an MP)
    if (isFreeTp(chainLink, 'start')) {
        tpsInBUL.push({ link: chainLink, endpoint: 'start' });
    }
    // Check if end is a TP
    if (isFreeTp(chainLink, 'end')) {
        tpsInBUL.push({ link: chainLink, endpoint: 'end' });
    }
}

// Number them: first is TP-1, second is TP-2
tpNumber = tpsInBUL.findIndex(tp => tp.link.id === currentLink.id) + 1;
```

### Drawing Code

**Location**: `topology.js` lines 11220-11273 (start TP), 11331-11381 (end TP), 11400-11437 (start MP), 11453-11490 (end MP)

**Labels Drawn**:
1. Main number (TP# or MP#) in larger font
2. UL identifier (U#) in smaller font below

---

## Console Output Correlation

### What You See in Console
```
📊 Complete BUL Structure:
   1. unbound_1: [MP]━━━[TP] (PARENT)
   2. unbound_2: [MP]━━━[MP] (MIDDLE)
   3. unbound_3: [TP]━━━[MP] (CHILD)
   Total: 2 TPs, 2 MPs
```

### What You See on Canvas
```
Visual Labels:
  1      1      2      2
 U1     U1     U2     U3
  ⚪ ━━ 🟣 ━━ 🟣 ━━ ⚪
(TP-1) (MP-1) (MP-2) (TP-2)

Correlation:
- UL1: [MP]━━━[TP] → Shows MP-1 at start, TP-1 at end
- UL2: [MP]━━━[MP] → Shows MP-1 at start, MP-2 at end
- UL3: [TP]━━━[MP] → Shows TP-2 at start, MP-2 at end
```

---

## Error Detection

### Correct Patterns

**2-Link BUL**:
```
Canvas:  1-U1 ━━ 1-U1 ━━ 2-U2
         TP-1    MP-1    TP-2
Console: 2 TPs, 1 MP ✅
```

**3-Link BUL**:
```
Canvas:  1-U1 ━━ 1-U1 ━━ 2-U2 ━━ 2-U3
         TP-1    MP-1    MP-2    TP-2
Console: 2 TPs, 2 MPs ✅
```

**4-Link BUL**:
```
Canvas:  1-U1 ━━ 1-U1 ━━ 2-U2 ━━ 3-U3 ━━ 2-U4
         TP-1    MP-1    MP-2    MP-3    TP-2
Console: 2 TPs, 3 MPs ✅
```

### Incorrect Patterns (Bugs)

**Wrong TP Count**:
```
Canvas:  1-U1 ━━ 1-U1 ━━ 2-U2 ━━ 1-U2 ━━ 2-U3
         TP-1    MP-1    MP-2    TP?     TP-2
                              ↑
                         SHOULD BE MP, NOT TP!

Console: ❌ WRONG TP COUNT! Expected 2, got 3
```

**Duplicate TP Numbers**:
```
Canvas:  1-U1 ━━ 1-U1 ━━ 1-U3
         TP-1    MP-1    TP-1  ← TWO TP-1s!

Problem: Counting logic error
```

**Wrong MP Sequence**:
```
Canvas:  1-U1 ━━ 2-U1 ━━ 1-U2 ━━ 2-U3
         TP-1    MP-2    MP-1    TP-2
                  ↑
         Should be MP-1 if it was first merge!

Problem: MP sequence not stored correctly
```

---

## Testing Scenarios

### Test 1: Verify MP Creation Order
1. Create UL1 and UL2, merge them → **Check**: MP-1 appears
2. Create UL3, merge to BUL → **Check**: MP-2 appears (not MP-1)
3. Create UL4, merge to OTHER end → **Check**: MP-3 appears
4. **Verify**: MPs numbered 1, 2, 3 in creation order (not position order)

### Test 2: Verify TP Relabeling
1. Create 2-link BUL → **Check**: TP-1 on U1, TP-2 on U2
2. Add UL3 to TP-2 side → **Check**: TP-2 moves to U3, TP-1 stays on U1
3. Add UL4 to TP-1 side → **Check**: TP-1 moves to U4, TP-2 stays on U3

### Test 3: Complex Chain
1. Create 5 ULs and merge in order: U1→U2→U3→U4→U5
2. **Expected MP labels**: 1, 2, 3, 4 (in creation order)
3. **Expected TP labels**: TP-1 on U1, TP-2 on U5
4. **Verify**: Console shows "2 TPs, 4 MPs"

### Test 4: Non-Sequential Merging
1. Create UL1, UL2, UL3, UL4
2. Merge U1+U2 → MP-1
3. Merge U3+U4 → MP-2 (separate chain)
4. Merge the two chains → MP-3
5. **Check**: MPs numbered by when they were created globally

---

## Benefits of This System

### 1. **Instant Structure Visibility** 👁️
- See at a glance: "This BUL has MP-1, MP-2, MP-3" = 3 merges happened
- Know immediately: "Only TP-1 and TP-2" = exactly 2 free ends (correct!)

### 2. **Bug Detection** 🐛
- If you see TP-3 → ERROR: Too many free endpoints
- If you see TP-1, TP-1 → ERROR: Duplicate numbering
- If MPs skip numbers (MP-1, MP-3) → ERROR: Missing merge data

### 3. **Historical Tracking** 📜
- MP-1 shows which connection was made first
- MP-4 shows which was made fourth
- Understand the evolution of the BUL

### 4. **Movement Clarity** 🎯
- "Drag MP-2" → You know exactly which connection you're adjusting
- "TP-1 and TP-2 stay fixed" → Clear which endpoints don't move

### 5. **Debugging Precision** 🔍
- Screenshot shows labeled structure
- Console output correlates with visual labels
- Easy to identify mismatched expectations

---

## Technical Implementation

### Files Modified
- `topology.js` - Lines 37, 193, 196, 2434, 2436, 4302, 4304, 4255, 4257, 9806, 9848, 11684, 11755, 11929, 11975
- Drawing code: Lines 11220-11490

### New Fields
- `this.mpSequenceCounter` - Global counter, starts at 1
- `mergedWith.mpSequence` - Stored MP number (permanent)
- `mergedWith.mpCreatedAt` - Timestamp (for reference)

### Persistence
- ✅ Saved in state history (undo/redo)
- ✅ Saved in file exports
- ✅ Loaded from file imports
- ✅ Restored on undo/redo

---

## Validation

### Automatic Checks

After each merge, the system validates:
```javascript
const analysis = this.analyzeBULChain(link);
if (analysis.tpCount !== 2) {
    console.error(`❌ WRONG TP COUNT! Expected 2, got ${analysis.tpCount}`);
}
if (analysis.mpCount !== allLinks.length - 1) {
    console.error(`❌ WRONG MP COUNT! Expected ${allLinks.length - 1}, got ${analysis.mpCount}`);
}
```

### Visual Validation

User can verify by:
1. **Counting gray dots**: Should be exactly 2 (TP-1 and TP-2)
2. **Counting purple dots**: Should be N-1 for N links
3. **Checking UL numbers**: Should show which UL each point is on
4. **Verifying middle ULs**: Should have NO gray dots (all purple)

---

## Quick Reference

| Element | Color | Numbering | Meaning |
|---------|-------|-----------|---------|
| TP | Gray ⚪ | 1 or 2 (positional) | Free endpoint, can connect |
| MP | Purple 🟣 | 1, 2, 3... (creation order) | Connection point, draggable |
| U# | Below dot | 1, 2, 3... | Which UL this point belongs to |

### Formulas
- **TP count**: Always 2
- **MP count**: N - 1 (where N = number of ULs in BUL)
- **MP sequence**: Increments globally (1, 2, 3, 4, ...)
- **UL number**: Creation order (1 = first created)

---

*Numbering system implemented: 2025-11-27*  
*Purpose: Enhanced BUL debugging and visualization*  
*Status: COMPLETE ✅*










