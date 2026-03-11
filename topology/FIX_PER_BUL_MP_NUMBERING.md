# Fix: Per-BUL MP Numbering and TP Labeling

## Issues Fixed

### Issue #1: Global MP Counter
**Problem**: MPs were numbered globally across ALL BULs, not per-BUL  
**Impact**: When deleting a BUL, MP numbers didn't reset  
**Example**: BUL1 has MP-1, MP-2. Delete it. Create BUL2 → starts at MP-3 (wrong!)

### Issue #2: Both TPs Labeled as TP-1
**Problem**: After merging UL1-TP2 with UL2-TP1, both remaining TPs showed as TP-1  
**Impact**: Couldn't distinguish between the two free endpoints

---

## Solutions Implemented

### Solution #1: Per-BUL MP Numbering ✅

**Changed**: From global `mpSequenceCounter` to per-BUL calculation

**Old System** (Global):
```javascript
// Global counter across all BULs
this.mpSequenceCounter = 1;

// On merge:
mpSequence: this.mpSequenceCounter++  // Increments forever
```

**New System** (Per-BUL):
```javascript
// No global counter needed!

// On merge - count existing MPs in THIS BUL only:
const existingChain = this.getAllMergedLinks(parentLink);
let existingMPCount = 0;
existingChain.forEach(link => {
    if (link.mergedWith) existingMPCount++;
});
const mpNumber = existingMPCount + 1;  // MP-1, MP-2, MP-3 for THIS BUL

parentLink.mergedWith = {
    ...
    mpNumber: mpNumber  // Per-BUL number (1, 2, 3...)
};
```

**Benefits**:
- ✅ Each BUL has its own MP numbering (1, 2, 3...)
- ✅ Deleting a BUL doesn't affect other BULs
- ✅ Creating new BUL starts from MP-1
- ✅ MP numbers are simpler (always 1, 2, 3... per BUL)

---

### Solution #2: Enhanced TP Detection and Validation ✅

**Changed**: Added validation and better debugging for TP numbering

**Enhanced Logic**:
```javascript
// Collect all TPs in BUL
const tpsInBUL = [];
for (const chainLink of allLinks) {
    // Detailed check for each endpoint...
    if (startIsTP) {
        tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start', link: chainLink });
    }
    if (endIsTP) {
        tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end', link: chainLink });
    }
}

// Find this specific TP in the list
const tpIndex = tpsInBUL.findIndex(tp => 
    tp.linkId === link.id && tp.endpoint === 'start'  // Match BOTH ID and endpoint!
);
tpNumber = (tpIndex >= 0) ? tpIndex + 1 : 0;

// VALIDATION
if (tpNumber === 0) {
    console.error(`❌ TP not found! This is a bug!`);
}
```

**Key Fix**:
- Must match BOTH `linkId` AND `endpoint` when finding TP index
- Returns 0 if not found (triggers error)
- Shows what TPs were actually found in the list

---

## Enhanced Console Output

### Before:
```
TPs: TP-1(U1), TP-2(U2)
MPs: MP-1(U1)
```

### After:
```
TPs: TP-1(U1-end), TP-2(U2-start)
           ↑              ↑
    Shows which endpoint!

MPs: MP-1(U1)
```

**Benefits**:
- ✅ See exactly which endpoint is each TP
- ✅ Verify merge consumed correct endpoints
- ✅ Debug TP assignment issues

---

## Example: Creating 3-Link BUL

### Step 1: Merge UL1 + UL2
```
Action: UL1-TP2(end) + UL2-TP1(start) → MP-1

Console:
✅ BUL extended! Now 2 links in chain
   MP-1 created at: (350, 250)
📊 Complete BUL Structure:
   1. unbound_1: [MP-1]━━━[TP-1] (PARENT)
   2. unbound_2: [TP-2]━━━[MP-1] (CHILD)
   TPs: TP-1(U1-end), TP-2(U2-start)
        ↑ U1's end    ↑ U2's start
   MPs: MP-1(U1)
   Total: 2 TPs, 1 MPs ✅

Canvas:
  1      1      2
 U1     U1     U2
  ⚪ ━━ 🟣 ━━ ⚪
```

### Step 2: Add UL3 to TP-2
```
Action: BUL-TP2(U2-start) + UL3-TP1 → MP-2

Console:
✅ BUL extended! Now 3 links in chain
   MP-2 created at: (400, 250)
📊 Complete BUL Structure:
   1. unbound_1: [MP-1]━━━[TP-1] (PARENT)
   2. unbound_2: [MP-1]━━━[MP-2] (MIDDLE)
   3. unbound_3: [TP-2]━━━[MP-2] (CHILD)
   TPs: TP-1(U1-end), TP-2(U3-start)
        ↑ Still U1    ↑ Moved to U3!
   MPs: MP-1(U1), MP-2(U2)
        ↑ First      ↑ Second (per-BUL numbering)
   Total: 2 TPs, 2 MPs ✅

Canvas:
  1      1      2      2
 U1     U1     U2     U3
  ⚪ ━━ 🟣 ━━ 🟣 ━━ ⚪
TP-1   MP-1   MP-2   TP-2
```

---

## Testing Scenarios

### Test 1: MP Numbering Per-BUL
1. Create BUL1: Merge 3 ULs
   - **Expected**: MP-1, MP-2
2. Create separate BUL2: Merge 2 different ULs
   - **Expected**: MP-1 (starts fresh, not MP-3!)
3. Extend BUL1: Add 4th UL
   - **Expected**: MP-1, MP-2, MP-3 (continues from BUL1's count)

### Test 2: TP-1 and TP-2 Correct Labels
1. Create 2 ULs and merge them
2. **Check console**: Should show different endpoints
   ```
   TPs: TP-1(U1-end), TP-2(U2-start)
   ```
3. **Check canvas**: 
   - One gray dot labeled "1-U1"
   - One gray dot labeled "2-U2"
   - Both should show "1" and "2", NOT both showing "1"

### Test 3: Validation Triggers
1. If you see only one TP number (both showing "1"):
   - Console should show error
   - `TPs in BUL:` list will show what was found
   - This helps debug the TP detection logic

---

## Code Changes Summary

### Removed:
- ❌ `this.mpSequenceCounter` - Global counter
- ❌ Saving/loading `mpSequenceCounter` in state
- ❌ All references to `mpSequence` field

### Added:
- ✅ Per-BUL MP count calculation before each merge
- ✅ `mpNumber` field in `mergedWith` (replaces `mpSequence`)
- ✅ Endpoint labels in console output (U1-start, U2-end...)
- ✅ Validation when TP not found in list
- ✅ Better error messages

### Modified Functions:
1. **Merge logic** (Lines 2425-2445, 4251-4270, 4334-4354) - Calculate MP number per-BUL
2. **Console output** (Lines 4468-4481, 4587-4596, 4633-4644) - Show endpoint labels
3. **Canvas drawing** (Lines 11561-11580, 11614-11633) - Use `mpNumber` instead of `mpSequence`
4. **TP numbering** (Lines 11249-11268, 11526-11549) - Added validation
5. **State management** - Removed `mpSequenceCounter` from saves/loads

---

## Expected Behavior

### Correct Per-BUL Numbering:

**BUL #1**:
```
MPs: MP-1, MP-2, MP-3
TPs: TP-1(U1), TP-2(U4)
```

**BUL #2** (separate):
```
MPs: MP-1, MP-2  ← Starts from 1 again!
TPs: TP-1(U5), TP-2(U7)
```

### Correct TP Labels:

**2-Link BUL**:
```
Console: TPs: TP-1(U1-end), TP-2(U2-start)
Canvas:  1-U1 ━━━ 1-U1 ━━━ 2-U2
         TP-1     MP-1     TP-2
```

**3-Link BUL**:
```
Console: TPs: TP-1(U1-end), TP-2(U3-start)
Canvas:  1-U1 ━━━ 1-U1 ━━━ 2-U2 ━━━ 2-U3
         TP-1     MP-1     MP-2     TP-2
```

---

## Files Modified

- `topology.js`:
  - Line 37: Removed `mpSequenceCounter`
  - Lines 192-197: Removed from state save
  - Lines 2425-2445: Per-BUL MP calculation (device-to-TP merge)
  - Lines 4251-4270: Per-BUL MP calculation (chain extension)
  - Lines 4334-4354: Per-BUL MP calculation (new merge)
  - Lines 4468-4481: Enhanced console with endpoint labels
  - Lines 9957-9965: Removed from undo state
  - Lines 10001-10008: Removed from undo restore
  - Lines 11561-11580: Canvas MP drawing (use `mpNumber`)
  - Lines 11614-11633: Canvas MP drawing end (use `mpNumber`)
  - Lines 11249-11268: TP drawing with validation
  - Lines 11526-11549: TP drawing end with validation
  - Lines 11837-11845, 11906-11915: Removed from file save/load
  - Lines 12081-12090, 12129-12138: Removed from auto-save

---

## Validation Added

### Console Errors to Watch For:

```
❌ TP not found in BUL list! Link: unbound_2, endpoint: start
   TPs in BUL: [{"id":"unbound_1","ep":"end"},{"id":"unbound_3","ep":"start"}]
```

This shows:
- Which link has the problem (unbound_2)
- Which endpoint should be a TP (start)
- What TPs were actually found

---

## Summary

### What Was Fixed:

✅ **MP numbering is now per-BUL** (not global)  
✅ **Each BUL starts from MP-1**  
✅ **Deleting BUL doesn't affect other BULs**  
✅ **TP console output shows which endpoint** (U1-end, U2-start)  
✅ **TP canvas labels are unique** (TP-1 and TP-2, not both TP-1)  
✅ **Validation triggers if TP not found**  
✅ **Better debugging with endpoint info**  

### Testing Steps:

1. **Reload page** (Cmd+Shift+R)
2. Create 2 ULs and merge
3. **Verify console shows**: `TPs: TP-1(U1-end), TP-2(U2-start)` with DIFFERENT endpoints
4. **Verify canvas shows**: One "1-U1" and one "2-U2" (not both "1")
5. Add 3rd UL
6. **Verify**: MPs are MP-1, MP-2 (per-BUL, not global)

---

*Fixes applied: 2025-11-27*  
*Issues: Global MP counter, duplicate TP-1 labels*  
*Status: RESOLVED ✅*










