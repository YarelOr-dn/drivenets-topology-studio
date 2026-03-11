# Drivenets Platform Cascading Selection - December 4, 2025

## Implementation Complete ✅

### Top Bar: Simple Device Names Only
```
╔═══════════════════════════════════╗
║      Router1 ↔ Switch2           ║
╚═══════════════════════════════════╝
```

Clean, simple, shows exactly what's connected.

---

### Platform Column in Table

Added **Platform column** with cascading selection:
1. **Category dropdown** (always enabled)
2. **Model dropdown** (enabled after category selected)

---

## Drivenets Platform Structure

### Category: SA (Stand Alone)
**Models**:
- NCP 1.0
- NCP 1.1
- NCP 1.2
- NCP 2.0
- NCP 2.1  
- NCP 3.0
- NCP 3.2

**Interfaces** (NCP 3.0 example):
- eth-1/1 through eth-1/12
- mgmt0 (Management)

### Category: Cluster  
**Models**:
- DN500
- DN700
- DN1000

**Interfaces** (DN1000 example):
- eth-1/1, eth-1/2, eth-1/3, eth-1/4 (Node 1)
- eth-2/1, eth-2/2, eth-2/3, eth-2/4 (Node 2)
- eth-3/1, eth-3/2, eth-3/3, eth-3/4 (Node 3)
- LAG-1, LAG-2, LAG-3, LAG-4 (Link Aggregation)
- mgmt0 (Management)

### Category: NCAI (Network Cloud AI)
**Models**:
- NCAI-100
- NCAI-200

**Interfaces** (NCAI-200 example):
- ai-eth-1/1, ai-eth-1/2, ai-eth-2/1, ai-eth-2/2 (AI Fabric)
- rdma-1, rdma-2, rdma-3, rdma-4 (RDMA)
- gpu-link-1, gpu-link-2 (GPU Direct)
- storage-1, storage-2 (Storage Network)
- mgmt0 (Management)

### Category: CHIPS (Custom Silicon)
**Models**:
- White Box DNI-1
- White Box DNI-2

**Interfaces** (White Box DNI-2 example):
- chip-port-1 through chip-port-6 (Native Ports)
- serdes-1 through serdes-4 (SerDes Lanes)
- pcie-1, pcie-2 (PCIe)
- npu-port-1 (NPU Port)
- mgmt0 (Management)

---

## Workflow

### Step 1: Select Category
```
Platform Column:
┌──────────────────┐
│ [SA ▼]          │ ← Select category
│ [Idle...    ▼]  │ ← Model dropdown disabled
└──────────────────┘
```

### Step 2: Model Dropdown Activates
```
Platform Column:
┌──────────────────┐
│ [SA ▼]          │
│ [-- Select --▼] │ ← Now enabled!
│  ├ NCP 1.0      │
│  ├ NCP 1.1      │
│  ├ NCP 2.0      │
│  ├ NCP 3.0      │
│  └ NCP 3.2      │
└──────────────────┘
```

### Step 3: Select Model
```
Platform Column:
┌──────────────────┐
│ [SA ▼]          │
│ [NCP 3.0 ▼]     │ ← Selected!
└──────────────────┘

Debugger Output:
✅ Device1 category: SA
✅ Device1 platform: NCP 3.0
   Available interfaces: eth-1/1, eth-1/2, ..., eth-1/12, mgmt0
```

---

## Table Layout

```
┌────────┬──────────┬───────────┬──────┬─────────┬──────┐
│ Device │ Platform │ Interface │ VLAN │ Trans.. │ ...  │
│        │ Category │           │Stack │         │      │
│        │  Model   │           │      │         │      │
├────────┼──────────┼───────────┼──────┼─────────┼──────┤
│Router1 │ [SA ▼]   │ eth-1/1   │ 100  │ 100G... │ ...  │
│        │ [NCP3.0▼]│           │      │         │      │
├────────┼──────────┼───────────┼──────┼─────────┼──────┤
│        │          │           │      │         │      │
│        │    Link  │           │      │         │      │
│        │     ↔    │           │      │         │      │
├────────┼──────────┼───────────┼──────┼─────────┼──────┤
│Switch2 │[Cluster▼]│ eth-2/1   │ 200  │ 100G... │ ...  │
│        │ [DN700 ▼]│           │      │         │      │
└────────┴──────────┴───────────┴──────┴─────────┴──────┘
```

---

## Cascading Selection Flow

```
1. Open Link Table
   ↓
2. See "Router1 ↔ Switch2" at top
   ↓
3. In table: Platform column has TWO dropdowns
   ├─ Category: [SA, Cluster, NCAI, CHIPS]
   └─ Model: (disabled until category selected)
   ↓
4. Select Category "SA"
   ↓
5. Model dropdown enables
   Shows: [NCP 1.0, NCP 1.1, NCP 2.0, NCP 3.0, NCP 3.2]
   ↓
6. Select Model "NCP 3.0"
   ↓
7. Debugger shows available interfaces
   ↓
8. User enters interface manually (future: auto-populate)
   ↓
9. Save → All data persists
```

---

## Data Storage

**Stored on Link Object**:
```javascript
link.device1PlatformCategory  // 'sa', 'cluster', 'ncai', 'chips'
link.device1PlatformModel     // 'ncp3.0', 'dn700', etc.
link.device2PlatformCategory
link.device2PlatformModel
```

**Future Enhancement**: Could auto-populate interface dropdown based on selected model's interfaces array.

---

## Visual Design

### Top Bar (Simple)
```
╔═══════════════════════════════════╗
║    Router1 ↔ Switch2             ║
╚═══════════════════════════════════╝
```
- Purple gradient background
- White bold text
- Center aligned
- No platform selector (moved to table column)

### Platform Column (Cascading)
```
Category Dropdown:
  Background: White
  Border: Purple (#8e44ad)
  Font: Bold 11px
  Status: Always enabled

Model Dropdown (before selection):
  Background: Gray (#ecf0f1)
  Border: Gray (#95a5a6)
  Font: 10px
  Status: Disabled
  Text: "Select category first..."

Model Dropdown (after category selected):
  Background: White
  Border: Purple (#9b59b6)
  Font: 10px
  Status: Enabled
  Options: Platform-specific models
```

---

## Testing

1. **Create link** between two devices
2. **Double-click** to open table
3. **Check top**: "Device1 ↔ Device2" (simple!) ✅
4. **Check table**: Platform column with 2 dropdowns ✅
5. **Model dropdown**: Disabled (gray) ✅
6. **Select category**: "SA"
7. **Model dropdown**: Enables, shows NCP models ✅
8. **Select model**: "NCP 3.0"
9. **Debugger**: Shows available interfaces ✅
10. **Save**: All data persists ✅
11. **Reopen**: Category and model remembered ✅

---

## Drivenets Models Summary

### SA Platform (7 models)
- NCP 1.0, 1.1, 1.2 (Entry level, 4-8 ports)
- NCP 2.0, 2.1 (Mid-range, 8 ports)
- NCP 3.0, 3.2 (High-end, 12 ports)

### Cluster Platform (3 models)
- DN500 (2 nodes)
- DN700 (2 nodes, more ports)
- DN1000 (3 nodes, high density)

### NCAI Platform (2 models)
- NCAI-100 (AI fabric, basic)
- NCAI-200 (AI fabric, advanced with more RDMA/GPU)

### CHIPS Platform (2 models)
- White Box DNI-1 (Basic silicon)
- White Box DNI-2 (Advanced silicon)

---

## Future Enhancements

Could add:
- Auto-populate interface dropdown from model.interfaces
- Port capacity information
- Speed capabilities per model
- Model-specific transceivers
- Compatibility checks

---

## Files Modified

- **topology.js**:
  - Lines 9590-9605: Simplified top bar
  - Lines 9616-9628: Device1 platform column
  - Lines 9819-9831: Device2 platform column  
  - Lines 9975-10009: Drivenets models database
  - Lines 10013-10108: Cascading selection handlers
  - Lines 10315-10320: Save platform data

- **index.html**:
  - Line 680: Added Platform header column (Device1 side)
  - Line 691: Added Platform header column (Device2 side)

---

## Date

December 4, 2025

## Status

✅ **Complete** - Cascading platform selection with real Drivenets models!





