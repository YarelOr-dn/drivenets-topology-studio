# Quick Test Guide - BUL All TP Combinations

## What Was Fixed

✅ BUL MPs now work correctly with **ALL TP connection combinations**, not just one specific pattern.

## Quick Test (5 minutes)

### Setup
1. Open terminal
2. Run: `python3 -m http.server 8001`
3. Open browser: `http://localhost:8001/index.html`
4. Enable debugger (checkbox at top)

### Test 1: Different Connection Patterns (2 minutes)

**Pattern A: TP-2 to TP-1 (The one that worked before)**
1. Create UL1 (double-tap canvas or Cmd+L)
2. Create UL2 (double-tap canvas or Cmd+L)
3. Drag UL2 left endpoint to UL1 left endpoint → Creates BUL
4. Drag the purple MP dot → Both ULs move ✅

**Pattern B: TP-1 to TP-1 (Should work now)**
1. Clear canvas (or create new ULs away from first test)
2. Create UL1
3. Create UL2
4. Drag UL1 right endpoint to UL2 left endpoint → Creates BUL
5. Drag the purple MP dot → Both ULs move ✅

**Pattern C: TP-1 to TP-2 (Should work now)**
1. Create UL1
2. Create UL2
3. Drag UL1 right endpoint to UL2 right endpoint → Creates BUL
4. Drag the purple MP dot → Both ULs move ✅

### Test 2: 3-UL Extension (2 minutes)

1. Create a 2-UL BUL (any pattern from above)
2. Create UL3
3. Drag UL3 endpoint to either TP of the BUL → Extends to 3-UL
4. Drag MP-1 → Only first 2 ULs move ✅
5. Drag MP-2 → Only last 2 ULs move ✅

### Test 3: Verify No Crashes (1 minute)

Try crazy combinations:
1. Create 4-5 ULs with different TP patterns
2. Drag MPs randomly
3. Check debugger output - should show no errors ✅

## What to Look For

### ✅ Good Signs
- MPs drag smoothly
- Both connected ULs move together
- Other ULs in chain stay fixed
- Debugger shows clear TP/MP numbering
- No jumps or glitches

### ❌ Bad Signs (Report if seen)
- MP drags but only one UL moves
- MPs jump to wrong positions
- Console shows errors
- ULs disconnect unexpectedly
- Wrong ULs move when dragging MP

## Debug Output Example

When dragging MP, you should see:
```
🟣 MP-1(U2) moving: 45px from start
   U1 and U2 moving together
```

When extending BUL, you should see:
```
🔗 Extending 3-link BUL chain
   Connection: U3-TP(end) + U1-TP(start) → MP-2
✅ BUL extended! Now 3 links in chain
```

## Quick Comparison

| Test | Before Fix | After Fix |
|------|-----------|-----------|
| UL2 TP-2 → UL1 TP-1 | ✅ Works | ✅ Works |
| UL1 TP-1 → UL2 TP-1 | ❌ Broken | ✅ Works |
| UL1 TP-1 → UL2 TP-2 | ❌ Broken | ✅ Works |
| UL1 TP-2 → UL2 TP-1 | ❌ Broken | ✅ Works |
| 3-UL extensions | ❌ Most broken | ✅ All work |

## Need More Detail?

See: `BUL_FIX_ALL_TP_COMBINATIONS.md` for comprehensive documentation





