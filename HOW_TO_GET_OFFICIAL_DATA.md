# How to Get Official Drivenets Platform Data

## Current Status

❌ **I don't have access to Drivenets' internal company portal**
✅ **I've created a complete framework ready for official data**
⏳ **Waiting for you to provide official information**

## What I Need From You

### Option 1: Give Me Access (Preferred)

If you can provide:
- Drivenets portal URL
- Documentation links (publicly accessible)
- Or PDF files with specifications

I can extract the data directly.

### Option 2: Fill This Template

Access your Drivenets portal and fill in this information:

---

## DATA EXTRACTION TEMPLATE

### SA PLATFORMS

For each NCP model, I need:

```
Model: NCP _____
Official Code: SA-_____
Chip: Q2D / Q3D / Other: _____
Total Capacity: _____G
Number of Ports: _____
Interface CLI Names (exact format):
  - eth-____/____/____
  - eth-____/____/____
  - (list all)
  - mgmt0 (or other management interface name)
```

**Fill in for**:
- [ ] NCP 1.0
- [ ] NCP 1.1
- [ ] NCP 1.2 (if exists)
- [ ] NCP 2.0
- [ ] NCP 2.1
- [ ] NCP 2.2 (if exists)
- [ ] NCP 3.0
- [ ] NCP 3.1 (if exists)
- [ ] NCP 3.2
- [ ] Any other SA models

---

### CLUSTER PLATFORMS

For each Cluster model:

```
Model: CL-_____
Official Name: _____
Chip: _____
Total Capacity: _____T
Number of Nodes: _____
Interfaces per Node: _____
LAG Support: Yes/No
Interface CLI Names:
  Node 1:
    - eth-1/____/____
    - eth-1/____/____
  Node 2:
    - eth-2/____/____
    - eth-2/____/____
  (etc for all nodes)
  LAGs:
    - lag-1
    - lag-2
    - (list all)
  Management:
    - mgmt0
```

**Fill in for**:
- [ ] CL-51
- [ ] CL-71
- [ ] CL-102
- [ ] Any other Cluster models

---

### NCAI / AI PLATFORMS

```
Model: _____
Official Name: _____
Chip: _____
Optimized For: AI/ML/GPU
Interface Types: Ethernet / RDMA / GPU Direct / Storage
Interface CLI Names:
  - ai-eth-____/____/____
  - rdma-____
  - gpu-link-____
  - storage-____
  - mgmt0
```

---

### CHIPS / SILICON

```
Chip Model: Q2D / Q3D / Other: _____
Generation: _____
Max Capacity per Port: _____
Native Interface Names:
  - npu-port-____/____
  - serdes-____
  - pcie-____
  - mgmt0
```

---

## Where to Find This Information

### In Drivenets Portal

Look for these documents:

1. **Product Datasheets**
   - Path: Products > Specifications > Datasheets
   - Contains: Model names, chips, capacity

2. **DNOS CLI Reference Guide**
   - Path: Documentation > CLI Reference
   - Contains: Interface naming, command syntax
   - Look for: "show interfaces" command examples

3. **Hardware Installation Guide**
   - Path: Documentation > Hardware
   - Contains: Port layouts, interface counts

4. **Configuration Examples**
   - Path: Documentation > Configuration > Examples
   - Contains: Real CLI configurations with interface names

5. **Release Notes**
   - Path: Downloads > Release Notes
   - Contains: Platform-specific features, interfaces

### Specific Commands to Run (If You Have Access to a Device)

```bash
# Get all interfaces on the platform
show interfaces brief

# Get interface naming
show running-config interfaces

# Get hardware info
show hardware

# Get platform model
show version
```

Copy the output and I can extract the interface names from there!

## What the System Will Do

Once you provide the data, the interface menu will:

1. **Auto-populate based on platform**:
   ```
   User selects: NCP 3.0 (SA-800C)
   ↓
   Interface dropdown shows ONLY:
   - eth-1/1/1
   - eth-1/1/2
   - ...
   - eth-1/1/12
   - mgmt0
   
   (Exact interfaces for that platform!)
   ```

2. **Prevent invalid selections**:
   - Can't select `eth-2/1/1` on SA platform (that's cluster only)
   - Can't select `lag-1` on platforms without LAG support
   - Only valid interfaces shown

3. **Show in debugger**:
   ```
   ✅ Device1 platform: NCP 3.0 (SA-800C)
      Chip: Q3D | Capacity: 800G
      Available interfaces: eth-1/1/1, eth-1/1/2, ..., mgmt0
   ```

## Current Workaround

Until we get official data:
- ✅ System works with placeholder data
- ✅ Structure is correct
- ✅ Easy to update when you get official info
- ⚠️ Interface names might not match exact CLI format

## How to Update (When You Have Data)

1. **If you get CSV**: Fill the template file I created
2. **If you get JSON**: Share it, I'll format it
3. **If you get PDF**: Share key pages, I'll extract
4. **If you have portal access**: Share screenshots of spec pages

Then I'll update line ~9974 in topology.js with official data!

## Summary

**What I've Built**:
✅ Complete cascading platform selection
✅ Category → Model → Interfaces flow
✅ Framework ready for official data
✅ Easy update mechanism

**What I Need**:
❌ Access to Drivenets official documentation
❌ Exact platform models and interface names
❌ CLI naming conventions

**Next Step**: 
👉 **You** access Drivenets portal and provide the data
👉 **I** integrate it perfectly into the system

Ready to update as soon as you have the official information! 📊





