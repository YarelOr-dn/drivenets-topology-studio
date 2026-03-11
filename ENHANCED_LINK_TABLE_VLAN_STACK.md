# Enhanced Link Table with VLAN-Stack, DNaaS, and Manipulation

## Overview
Completely redesigned the link connection details table to support:
1. **VLAN-Stack** with Outer/Inner subsections (QinQ support)
2. **DNaaS VLAN** section for managed VLAN services
3. **VLAN Manipulation** column with all Drivenets supported operations

---

## New Table Structure

### Visual Layout

```
┌─────────┬───────────┬────────────────┬────────────┬──────────────┬─────────┬──────────────┬────────────┬────────────────┬───────────┬─────────┐
│ Device  │ Interface │  VLAN Stack    │Transceiver │    VLAN      │ DNaaS   │     Link     │   DNaaS    │    VLAN      │Transceiver│  VLAN  Stack   │Interface│ Device  │
│         │           │ Outer | Inner  │            │ Manipulation │  VLAN   │      ↔       │   VLAN     │ Manipulation │           │ Outer | Inner  │         │         │
├─────────┼───────────┼───────┼────────┼────────────┼──────────────┼─────────┼──────────────┼────────────┼──────────────┼───────────┼───────┼────────┼─────────┼─────────┤
│ TP-1:   │   eth0    │  100  │  200   │ 400G DR4   │ Push VLAN    │   500   │      ↔       │   600      │ 1:1 Trans    │ 400G DR4  │  300  │  400   │  eth1   │ TP-2:   │
│ NCP-1   │           │       │        │            │              │         │              │            │              │           │       │        │         │ NCP-2   │
└─────────┴───────────┴───────┴────────┴────────────┴──────────────┴─────────┴──────────────┴────────────┴──────────────┴───────────┴───────┴────────┴─────────┴─────────┘
```

### Column Breakdown

**Left Side (Device 1 / TP-1)**:
1. Device - Shows device name (with TP-1 label for BULs)
2. Interface - Interface name (from interface label)
3. VLAN Stack Outer - Outer VLAN tag (S-VLAN for QinQ)
4. VLAN Stack Inner - Inner VLAN tag (C-VLAN for QinQ)
5. Transceiver - Optics type
6. VLAN Manipulation - Drivenets manipulation options
7. DNaaS VLAN - Managed VLAN service ID

**Center**:
8. Link ↔ - Visual separator

**Right Side (Device 2 / TP-2)**:
9. DNaaS VLAN - Managed VLAN service ID
10. VLAN Manipulation - Drivenets manipulation options
11. Transceiver - Optics type
12. VLAN Stack Outer - Outer VLAN tag
13. VLAN Stack Inner - Inner VLAN tag
14. Interface - Interface name
15. Device - Shows device name (with TP-2 label for BULs)

---

## Feature 1: VLAN-Stack (Outer/Inner)

### What It Supports

**QinQ (802.1ad) Double Tagging**:
- **Outer VLAN** (S-VLAN): Service provider tag
- **Inner VLAN** (C-VLAN): Customer tag

**Example Use Cases**:
```
Single VLAN:
- Outer: 100
- Inner: (empty)
→ Standard single VLAN tagging

QinQ Double Tag:
- Outer: 100 (Service VLAN)
- Inner: 200 (Customer VLAN)
→ Service provider isolation with customer VLAN inside

Triple VLAN (with DNaaS):
- Outer: 100
- Inner: 200
- DNaaS: 500
→ Complex multi-layer VLAN scenario
```

### Data Storage

**New Fields**:
```javascript
link.device1VlanOuter  // Outer VLAN tag (device 1 side)
link.device1VlanInner  // Inner VLAN tag (device 1 side)
link.device2VlanOuter  // Outer VLAN tag (device 2 side)
link.device2VlanInner  // Inner VLAN tag (device 2 side)
```

**Backward Compatibility**:
```javascript
// Old single VLAN field migrated to Outer
if (link.device1Vlan && !link.device1VlanOuter) {
    link.device1VlanOuter = link.device1Vlan;
}

// Legacy field maintained for compatibility
link.device1Vlan = d1VlanOuter || d1VlanInner || '';
```

---

## Feature 2: DNaaS VLAN

### What It Is

**DNaaS (Data Network as a Service)** VLAN for managed network services:
- Separate column for service-level VLAN tagging
- Orange color coding for easy identification
- Typically used for:
  - Service provider VPNs
  - Managed L2/L3 VPN services
  - Cloud interconnect VLANs
  - Provider backbone VLANs

### Visual Design

**Color Coding**: Orange background (`rgba(230, 126, 34, 0.05)`)
**Border**: Orange border (`#e67e22`)
**Label**: "DNaaS VLAN" in header

**Example Values**:
- `500` - DNaaS service VLAN ID
- `1000-1010` - VLAN range for service
- `MPLS:100` - MPLS label notation
- Empty - No DNaaS service

### Data Storage

```javascript
link.device1DnaasVlan  // DNaaS VLAN for device 1 side
link.device2DnaasVlan  // DNaaS VLAN for device 2 side
```

---

## Feature 3: VLAN Manipulation

### Drivenets Supported Operations

**Complete list of VLAN manipulation options**:

#### VLAN Translation
```
1:1 Translation  - One-to-one VLAN mapping
N:1 Translation  - Many-to-one VLAN aggregation
1:N Translation  - One-to-many VLAN distribution
```

#### VLAN Stacking
```
Push VLAN (Add Outer)    - Add outer VLAN tag (QinQ)
Pop VLAN (Remove Outer)  - Remove outer VLAN tag
Swap Outer VLAN          - Replace outer tag with new value
Swap Inner VLAN          - Replace inner tag with new value
```

#### QinQ Operations
```
QinQ Push (Double Tag)    - Add double VLAN tags
QinQ Pop (Remove Double)  - Remove both VLAN tags
QinQ Swap                 - Replace both tags
```

#### Priority Operations
```
Set CoS/Priority      - Set Class of Service bits
Map Priority          - Map VLAN priority to QoS class
Preserve Priority     - Maintain original priority
```

#### Advanced
```
Transparent (No Change)  - Pass through without modification
Strip All Tags          - Remove all VLAN tags
Add Default VLAN        - Add default VLAN if untagged
```

### Visual Design

**Color Coding**: Teal/green background (`rgba(22, 160, 133, 0.05)`)
**Border**: Teal border (`#16a085`)
**Label**: "VLAN Manipulation" in header (spans 2 rows)

### Data Storage

```javascript
link.device1VlanManipulation  // Manipulation operation for device 1 side
link.device2VlanManipulation  // Manipulation operation for device 2 side
```

**Example Values**:
- `push-vlan` - Push VLAN operation
- `1:1-translation` - One-to-one translation
- `qinq-push` - QinQ double tagging
- `transparent` - No manipulation

---

## Complete Example Use Case

### Scenario: Provider Edge with QinQ

**Network Setup**:
- Customer VLAN 200 enters at NCP-1
- Provider adds Service VLAN 100
- DNaaS service assigns VLAN 500
- Customer VLAN 300 exits at NCP-2

**Table Configuration**:
```
┌──────────┬─────────┬───────┬───────┬────────────┬──────────────┬─────────┬──────┬──────────────┬────────────┬───────┬───────┬─────────┬──────────┐
│  Device  │Interface│ Outer │ Inner │Transceiver │Manipulation  │ DNaaS   │ Link │    DNaaS     │Manipulation│Trans  │ Outer │ Inner │Interface│  Device  │
├──────────┼─────────┼───────┼───────┼────────────┼──────────────┼─────────┼──────┼──────────────┼────────────┼───────┼───────┼───────┼─────────┼──────────┤
│ TP-1:    │  eth0   │  100  │  200  │ 400G DR4   │ QinQ Push    │   500   │  ↔   │     500      │ QinQ Pop   │400G   │  100  │  300  │  eth1   │ TP-2:    │
│ NCP-1    │         │       │       │            │              │         │      │              │            │ DR4   │       │       │         │ NCP-2    │
└──────────┴─────────┴───────┴───────┴────────────┴──────────────┴─────────┴──────┴──────────────┴────────────┴───────┴───────┴───────┴─────────┴──────────┘
```

**What This Represents**:
- **Ingress (NCP-1)**:
  - VLAN Stack: 100 (Outer), 200 (Inner)
  - Manipulation: QinQ Push (adds double tag)
  - DNaaS VLAN: 500 (provider service)

- **Egress (NCP-2)**:
  - VLAN Stack: 100 (Outer), 300 (Inner)
  - Manipulation: QinQ Pop (removes provider tags)
  - DNaaS VLAN: 500 (same service)

---

## Technical Implementation

### Files Modified

#### 1. index.html (Lines 664-686)

**Changed table header** from single-row to two-row with merged cells:

```html
<thead>
    <tr style="background: #34495e; color: white;">
        <th>Device</th>
        <th>Interface</th>
        <th colspan="2">VLAN Stack</th>  <!-- Spans 2 columns -->
        <th>Transceiver</th>
        <th rowspan="2">VLAN Manipulation</th>  <!-- Spans 2 rows -->
        <th rowspan="2">DNaaS VLAN</th>  <!-- Spans 2 rows -->
        <th rowspan="2">Link</th>  <!-- Spans 2 rows -->
        <!-- ... mirror for right side -->
    </tr>
    <tr style="background: #34495e; color: white;">
        <!-- Empty cells for first columns -->
        <th>Outer</th>  <!-- VLAN Stack subsection -->
        <th>Inner</th>  <!-- VLAN Stack subsection -->
        <!-- ... mirror for right side -->
    </tr>
</thead>
```

**Key Features**:
- `colspan="2"` for "VLAN Stack" header
- `rowspan="2"` for manipulation and DNaaS columns
- Two-row header for organized structure

#### 2. topology.js

**A. Initialize New Fields** (Lines 9312-9329):
```javascript
// New VLAN stack fields
if (!link.device1VlanOuter) link.device1VlanOuter = '';
if (!link.device1VlanInner) link.device1VlanInner = '';
// ... same for device2

// New DNaaS fields
if (!link.device1DnaasVlan) link.device1DnaasVlan = '';
if (!link.device2DnaasVlan) link.device2DnaasVlan = '';

// New manipulation fields
if (!link.device1VlanManipulation) link.device1VlanManipulation = '';
if (!link.device2VlanManipulation) link.device2VlanManipulation = '';

// Migration from old single VLAN
if (link.device1Vlan && !link.device1VlanOuter) {
    link.device1VlanOuter = link.device1Vlan;
}
```

**B. Generate Table Rows** (Lines 9443-9600):
```javascript
tableBody.innerHTML = `
    <tr>
        <td>${device1Name}</td>
        <td>${device1InterfaceName}</td>
        <td><input id="link-d1-vlan-outer" ...></td>
        <td><input id="link-d1-vlan-inner" ...></td>
        <td><select id="link-d1-transceiver" ...></td>
        <td><select id="link-d1-vlan-manipulation" ...></td>
        <td><input id="link-d1-dnaas-vlan" ...></td>
        <td>↔</td>
        <!-- Mirror for device 2 -->
    </tr>
`;
```

**C. Save All Fields** (Lines 9828-9861):
```javascript
saveLinkDetails() {
    // Get all new field values
    const d1VlanOuter = document.getElementById('link-d1-vlan-outer').value;
    const d1VlanInner = document.getElementById('link-d1-vlan-inner').value;
    const d1DnaasVlan = document.getElementById('link-d1-dnaas-vlan').value;
    const d1VlanManipulation = document.getElementById('link-d1-vlan-manipulation').value;
    // ... same for device 2
    
    // Save to link object
    this.editingLink.device1VlanOuter = d1VlanOuter;
    this.editingLink.device1VlanInner = d1VlanInner;
    // ... all fields
}
```

**D. Restore Dropdown Values** (Lines 9818-9840):
```javascript
setTimeout(() => {
    // Set transceiver dropdowns
    if (d1Transceiver && link.device1Transceiver) {
        d1Transceiver.value = link.device1Transceiver;
    }
    // Set manipulation dropdowns
    if (d1Manipulation && link.device1VlanManipulation) {
        d1Manipulation.value = link.device1VlanManipulation;
    }
}, 10);
```

---

## VLAN Manipulation Options Reference

### Translation Operations

| Option | Code Value | Use Case |
|--------|------------|----------|
| 1:1 Translation | `1:1-translation` | Map VLAN X to VLAN Y |
| N:1 Translation | `n:1-translation` | Aggregate multiple VLANs to one |
| 1:N Translation | `1:n-translation` | Distribute one VLAN to multiple |

### Stacking Operations

| Option | Code Value | Use Case |
|--------|------------|----------|
| Push VLAN (Add Outer) | `push-vlan` | Add outer tag for QinQ |
| Pop VLAN (Remove Outer) | `pop-vlan` | Remove outer tag |
| Swap Outer VLAN | `swap-outer` | Replace outer tag |
| Swap Inner VLAN | `swap-inner` | Replace inner tag |

### QinQ Operations

| Option | Code Value | Use Case |
|--------|------------|----------|
| QinQ Push (Double Tag) | `qinq-push` | Add both outer and inner tags |
| QinQ Pop (Remove Double) | `qinq-pop` | Remove both tags |
| QinQ Swap | `qinq-swap` | Replace both tags |

### Priority Operations

| Option | Code Value | Use Case |
|--------|------------|----------|
| Set CoS/Priority | `set-priority` | Set specific priority value |
| Map Priority | `map-priority` | Map VLAN priority to QoS |
| Preserve Priority | `preserve-priority` | Keep original priority |

### Advanced Operations

| Option | Code Value | Use Case |
|--------|------------|----------|
| Transparent (No Change) | `transparent` | Pass through unchanged |
| Strip All Tags | `strip-all` | Remove all VLAN tags |
| Add Default VLAN | `add-default` | Tag untagged frames |

---

## Usage Examples

### Example 1: Simple VLAN Translation

**Requirement**: Translate VLAN 10 to VLAN 20

**Configuration**:
```
Device 1 Side:
- VLAN Outer: 10
- VLAN Inner: (empty)
- Manipulation: 1:1 Translation

Device 2 Side:
- VLAN Outer: 20
- VLAN Inner: (empty)
- Manipulation: Transparent
```

### Example 2: QinQ Service Provider

**Requirement**: Provider adds S-VLAN 100 to customer VLAN 200

**Configuration**:
```
Device 1 Side (Customer):
- VLAN Outer: (empty or 200)
- VLAN Inner: (empty)
- Manipulation: Transparent

Device 2 Side (Provider):
- VLAN Outer: 100 (S-VLAN)
- VLAN Inner: 200 (C-VLAN)
- Manipulation: QinQ Push
```

### Example 3: DNaaS with VLAN Manipulation

**Requirement**: Managed service with VLAN translation

**Configuration**:
```
Device 1 Side:
- VLAN Outer: 10
- VLAN Inner: (empty)
- DNaaS VLAN: 500
- Manipulation: Push VLAN

Device 2 Side:
- VLAN Outer: 100
- VLAN Inner: 10
- DNaaS VLAN: 500
- Manipulation: Pop VLAN
```

### Example 4: Complex Multi-Layer

**Requirement**: Full QinQ with service VLAN and manipulation

**Configuration**:
```
Device 1 Side:
- VLAN Outer: 100
- VLAN Inner: 200
- DNaaS VLAN: 500
- Manipulation: QinQ Push

Device 2 Side:
- VLAN Outer: 300
- VLAN Inner: 400
- DNaaS VLAN: 500
- Manipulation: QinQ Swap
```

---

## Visual Design

### Color Coding

**VLAN Stack Columns**:
- Header: Dark gray (`#2c3e50`) - same as other headers
- Cells: White background with light border
- Subsections labeled "Outer" and "Inner"

**VLAN Manipulation Columns**:
- Header: Teal/green (`#16a085`)
- Background: Light teal (`rgba(22, 160, 133, 0.05)`)
- Border: Teal (`#16a085`)
- Easily distinguishable from other columns

**DNaaS VLAN Columns**:
- Header: Orange (`#e67e22`)
- Background: Light orange (`rgba(230, 126, 34, 0.05)`)
- Border: Orange (`#e67e22`)
- Stands out for managed services

**Link Center Column**:
- Blue background (`#3498db`)
- White text
- Large ↔ arrow
- Visual separator between sides

---

## Modal Sizing

**Updated modal width** to accommodate new columns:
- **Before**: 900px
- **After**: 1400px
- **Max width**: 98vw (responsive)

**Benefits**:
- ✅ All columns visible without horizontal scroll
- ✅ Responsive on smaller screens
- ✅ Clean, organized layout

---

## Data Persistence

### Saved Fields (Per Link)

**Total 10 new fields per link**:
1. `device1VlanOuter` - Left outer VLAN
2. `device1VlanInner` - Left inner VLAN
3. `device1DnaasVlan` - Left DNaaS VLAN
4. `device1VlanManipulation` - Left manipulation operation
5. `device1Transceiver` - Left transceiver (existing)
6. `device2VlanOuter` - Right outer VLAN
7. `device2VlanInner` - Right inner VLAN
8. `device2DnaasVlan` - Right DNaaS VLAN
9. `device2VlanManipulation` - Right manipulation operation
10. `device2Transceiver` - Right transceiver (existing)

### Persistence

All fields saved to:
- ✅ Link object in memory
- ✅ Undo/redo history (via saveState())
- ✅ File export/import
- ✅ Browser local storage

---

## Console Logging

### When Saving Details

```
💾 Link details saved
   Device 1 VLAN: Outer=100 Inner=200
   Device 1 DNaaS: 500
   Device 1 Manipulation: qinq-push
```

**Benefits**:
- Quick verification of saved values
- Debugging complex VLAN configurations
- Audit trail for changes

---

## Backward Compatibility

### Legacy VLAN Field

**Maintained for old configs**:
```javascript
// Old field still works
link.device1Vlan = "100"  

// Auto-migrates to new structure
→ link.device1VlanOuter = "100"
→ link.device1VlanInner = ""

// When saving, legacy field updated
link.device1Vlan = d1VlanOuter || d1VlanInner || '';
```

**Benefits**:
- ✅ Old topology files still load correctly
- ✅ Existing VLANs appear in Outer column
- ✅ Smooth migration path

---

## Summary of Changes

### Files Modified
- `index.html`
  - Lines 651: Increased modal width to 1400px
  - Lines 664-686: Redesigned table header with 2 rows, merged cells

- `topology.js`
  - Lines 9312-9329: Initialize all new VLAN fields
  - Lines 9443-9600: Generate table with new columns
  - Lines 9828-9861: Save all new fields
  - Lines 9818-9840: Restore dropdown selections

### New Features

1. ✅ **VLAN-Stack** - Outer/Inner subsections for QinQ
2. ✅ **DNaaS VLAN** - Managed service VLAN column
3. ✅ **VLAN Manipulation** - 15+ Drivenets operations
4. ✅ **Color coding** - Teal for manipulation, orange for DNaaS
5. ✅ **Backward compatible** - Old configs auto-migrate
6. ✅ **BUL support** - Works with TP-1/TP-2 labels

---

## Benefits

### For Network Engineers

**Better VLAN Management**:
- 🏷️ Full QinQ/802.1ad support with Outer/Inner
- 🔄 Complete manipulation options (push, pop, swap, translate)
- ☁️ DNaaS service VLAN tracking
- 📊 All info in one organized table

### For Service Providers

**Enterprise Features**:
- Provider VLAN stacking (S-VLAN + C-VLAN)
- Managed service VLAN (DNaaS) tracking
- Complex VLAN manipulation workflows
- Industry-standard operations

### For Users

**Easier to Use**:
- Clear column organization
- Color-coded sections
- Dropdown selections (no typing manipulation names)
- Comprehensive options in logical groups

---

## Complete Feature Set

The enhanced link table now supports:
- ✅ Device connections with TP-1/TP-2 labels (BULs)
- ✅ Interface labels
- ✅ VLAN Stack (Outer/Inner) for QinQ
- ✅ DNaaS VLAN for managed services
- ✅ VLAN Manipulation with 15+ Drivenets options
- ✅ Transceiver selection (800G, 400G, 200G, 100G, 40G, 10G)
- ✅ Link info section with BUL chain details
- ✅ Copy table to clipboard
- ✅ Draggable/resizable modal

**Professional-grade link configuration table!** 🎉







