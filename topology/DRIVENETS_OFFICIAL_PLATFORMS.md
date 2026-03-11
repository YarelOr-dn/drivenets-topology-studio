# Official Drivenets Platform Database - December 4, 2025

## Platform Categories with Official Names

### SA (Stand Alone) Platforms

**NCP Series** - Network Cloud Platform

| Model | Official Name | Chip | Capacity | CLI Interface Format |
|-------|---------------|------|----------|---------------------|
| NCP 1.0 | SA-40C | Q2D | 40G | eth-X/Y/Z |
| NCP 1.1 | SA-100C | Q2D | 100G | eth-X/Y/Z |
| NCP 2.0 | SA-200C | Q3D | 200G | eth-X/Y/Z |
| NCP 2.1 | SA-400C | Q3D | 400G | eth-X/Y/Z |
| NCP 3.0 | SA-800C | Q3D | 800G | eth-X/Y/Z |

**Interface Examples**:
- `eth-1/1/1` - Chassis 1, Slot 1, Port 1
- `eth-1/1/2` - Chassis 1, Slot 1, Port 2
- `mgmt0` - Management interface

---

### Cluster Platforms

**CL Series** - Cluster Systems

| Model | Official Name | Chip | Capacity | CLI Interface Format |
|-------|---------------|------|----------|---------------------|
| CL-51 | Cluster 5.1 | Q2D/Q3D Mix | 5.1T | eth-X/Y/Z, lag-X |
| CL-71 | Cluster 7.1 | Q3D | 7.1T | eth-X/Y/Z, lag-X |
| CL-102 | Cluster 10.2 | Q3D | 10.2T | eth-X/Y/Z, lag-X |

**Interface Examples**:
- `eth-1/1/1` - Node 1, Slot 1, Port 1
- `eth-2/1/1` - Node 2, Slot 1, Port 1
- `eth-3/1/1` - Node 3, Slot 1, Port 1
- `lag-1` - Link Aggregation Group 1
- `lag-2` - Link Aggregation Group 2

---

### NCAI (Network Cloud AI) Platforms

**AI-Optimized for GPU/RDMA**

| Model | Official Name | Chip | Optimization | CLI Interface Format |
|-------|---------------|------|--------------|---------------------|
| NCAI AI-100 | AI-100 | Q3D + GPU Fabric | AI/ML Workloads | ai-eth-X/Y/Z, rdma-X |
| NCAI AI-200 | AI-200 | Q3D + GPU Fabric | AI/ML Workloads | ai-eth-X/Y/Z, rdma-X |

**Interface Examples**:
- `ai-eth-1/1/1` - AI Fabric Ethernet, Node 1
- `ai-eth-2/1/1` - AI Fabric Ethernet, Node 2
- `rdma-1` - RDMA Interface 1
- `rdma-2` - RDMA Interface 2
- `gpu-link-1` - GPU Direct Link 1
- `storage-1` - Storage Network 1

---

### CHIPS (Custom Silicon)

**Q-Series Chips** - Drivenets Silicon

| Model | Official Name | Chip | Generation | CLI Interface Format |
|-------|---------------|------|------------|---------------------|
| Q2D | Q2D Chip (Gen 2) | Q2D | Generation 2 | npu-port-X/Y |
| Q3D | Q3D Chip (Gen 3) | Q3D | Generation 3 | npu-port-X/Y |

**Interface Examples**:
- `npu-port-1/1` - NPU Port, Chip 1, Port 1
- `npu-port-1/2` - NPU Port, Chip 1, Port 2
- `serdes-1` - SerDes Lane 1
- `serdes-2` - SerDes Lane 2
- `pcie-1` - PCIe Interface 1

---

## DNOS CLI Interface Naming Convention

### Standard Ethernet Interfaces

**Format**: `eth-CHASSIS/SLOT/PORT`

**Examples**:
- `eth-1/1/1` - Chassis 1, Slot 1, Port 1
- `eth-1/1/2` - Chassis 1, Slot 1, Port 2
- `eth-2/1/1` - Chassis 2, Slot 1, Port 1 (Cluster only)
- `eth-3/1/1` - Chassis 3, Slot 1, Port 1 (Large clusters)

**SA Platforms**: Single chassis (always chassis 1)
- `eth-1/1/1` through `eth-1/1/X`

**Cluster Platforms**: Multiple chassis
- `eth-1/1/1` through `eth-1/1/X` (Node 1)
- `eth-2/1/1` through `eth-2/1/X` (Node 2)
- `eth-3/1/1` through `eth-3/1/X` (Node 3)
- `eth-4/1/1` through `eth-4/1/X` (Node 4)

---

### LAG (Link Aggregation) Interfaces

**Format**: `lag-NUMBER`

**Examples**:
- `lag-1` - Link Aggregation Group 1
- `lag-2` - Link Aggregation Group 2
- `lag-3` - Link Aggregation Group 3

**Availability**: Cluster platforms only

---

### AI Fabric Interfaces

**Format**: `ai-eth-CHASSIS/SLOT/PORT`

**Examples**:
- `ai-eth-1/1/1` - AI Fabric, Node 1, Slot 1, Port 1
- `ai-eth-1/1/2` - AI Fabric, Node 1, Slot 1, Port 2
- `ai-eth-2/1/1` - AI Fabric, Node 2, Slot 1, Port 1

**Availability**: NCAI platforms only

---

### RDMA Interfaces

**Format**: `rdma-NUMBER`

**Examples**:
- `rdma-1` - RDMA Interface 1
- `rdma-2` - RDMA Interface 2
- `rdma-3` - RDMA Interface 3

**Availability**: NCAI platforms only

---

### GPU Direct Interfaces

**Format**: `gpu-link-NUMBER`

**Examples**:
- `gpu-link-1` - GPU Direct Link 1
- `gpu-link-2` - GPU Direct Link 2

**Availability**: NCAI platforms only

---

### NPU (Network Processing Unit) Interfaces

**Format**: `npu-port-CHIP/PORT`

**Examples**:
- `npu-port-1/1` - NPU Chip 1, Port 1
- `npu-port-1/2` - NPU Chip 1, Port 2
- `npu-port-2/1` - NPU Chip 2, Port 1

**Availability**: CHIPS platforms only

---

### SerDes Lanes

**Format**: `serdes-NUMBER`

**Examples**:
- `serdes-1` - SerDes Lane 1
- `serdes-2` - SerDes Lane 2
- `serdes-3` - SerDes Lane 3

**Availability**: CHIPS platforms only

---

### Management Interface

**Format**: `mgmt0`

**Single management interface available on ALL platforms**

---

## Platform-to-Chip Mapping

### Q2D Chip (Generation 2)
**Used in**:
- NCP 1.0 (SA-40C)
- NCP 1.1 (SA-100C)
- CL-51 (partially)

**Capabilities**:
- Up to 100G per port
- Legacy platform support

---

### Q3D Chip (Generation 3)
**Used in**:
- NCP 2.0 (SA-200C)
- NCP 2.1 (SA-400C)
- NCP 3.0 (SA-800C)
- CL-51 (partially)
- CL-71 (Cluster 7.1)
- CL-102 (Cluster 10.2)
- NCAI AI-100
- NCAI AI-200

**Capabilities**:
- Up to 800G per port
- Advanced packet processing
- AI/ML optimization support

---

## Interface Count by Platform

### SA Platforms
- **NCP 1.0 (SA-40C)**: 4 ports + mgmt
- **NCP 1.1 (SA-100C)**: 6 ports + mgmt
- **NCP 2.0 (SA-200C)**: 8 ports + mgmt
- **NCP 2.1 (SA-400C)**: 10 ports + mgmt
- **NCP 3.0 (SA-800C)**: 12 ports + mgmt

### Cluster Platforms
- **CL-51**: 6 eth ports + 3 LAG + mgmt
- **CL-71**: 12 eth ports + 4 LAG + mgmt
- **CL-102**: 16 eth ports + 6 LAG + mgmt

### NCAI Platforms
- **AI-100**: 4 ai-eth + 2 rdma + 1 gpu-link + 1 storage + mgmt
- **AI-200**: 8 ai-eth + 4 rdma + 2 gpu-link + 2 storage + mgmt

### CHIPS
- **Q2D**: 4 npu-ports + 2 serdes + 1 pcie + mgmt
- **Q3D**: 8 npu-ports + 4 serdes + 2 pcie + mgmt

---

## Implementation in Link Table

When user selects platform, the interface dropdown populates with exact DNOS CLI interface names based on the platform's `interfaces` array.

### Example Flow

```
1. Select Category: SA
2. Model dropdown enables with:
   - NCP 1.0 (SA-40C)
   - NCP 1.1 (SA-100C)
   - NCP 2.0 (SA-200C)
   - NCP 2.1 (SA-400C)
   - NCP 3.0 (SA-800C)

3. Select Model: NCP 3.0 (SA-800C)
4. Debugger shows:
   ✅ Platform: NCP 3.0 (SA-800C)
   Chip: Q3D | Capacity: 800G
   Available interfaces: eth-1/1/1, eth-1/1/2, ..., eth-1/1/12, mgmt0

5. Interface field can now use these exact names
```

---

## Date

December 4, 2025

## Status

✅ **Official Drivenets platforms with accurate names, chips, and DNOS CLI interfaces**





