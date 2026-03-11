# Drivenets Platform Data Framework - December 4, 2025

## Current Limitation

I don't have access to Drivenets' internal company portal or private documentation. The platform data I've implemented is based on general networking knowledge and needs to be updated with official information.

## How to Get Official Data

### Step 1: Access Drivenets Portal

You'll need to access:
- **Drivenets Partner Portal** or **Customer Portal**
- **Product Documentation** section
- **DNOS CLI Reference Guide**
- **Hardware Specifications** documents

### Step 2: Extract Platform Information

For each platform, gather:

#### Platform Details
```json
{
  "officialName": "NCP 3.0",
  "modelCode": "SA-800C",
  "category": "sa",
  "chip": "Q3D",
  "capacity": "800G",
  "description": "Stand-Alone 800G Network Cloud Platform"
}
```

#### Interface Information
```json
{
  "cliFormat": "eth-CHASSIS/SLOT/PORT",
  "interfaces": [
    "eth-1/1/1",
    "eth-1/1/2",
    ...
    "mgmt0"
  ],
  "lagSupport": true,
  "lagInterfaces": ["lag-1", "lag-2"]
}
```

### Step 3: Update the Code

The data structure to update is in `topology.js` around line 9974:

```javascript
const drivenetsModels = {
    'sa': {
        label: 'SA (Stand Alone)',
        models: [
            {
                value: 'UNIQUE_ID',        // ← Update
                label: 'OFFICIAL_NAME',    // ← Update with official name
                chip: 'CHIP_MODEL',        // ← Update (Q2D, Q3D, etc.)
                capacity: 'CAPACITY',      // ← Update (40G, 800G, etc.)
                interfaces: ['LIST', 'OF', 'INTERFACES']  // ← Update with CLI names
            },
            // Add more models...
        ]
    },
    // Repeat for cluster, ncai, chips...
};
```

## Current Implementation

I've created a working framework with:

### SA Platforms (Placeholder Data - NEEDS UPDATE)
- NCP 1.0 (SA-40C) - Q2D chip
- NCP 1.1 (SA-100C) - Q2D chip
- NCP 2.0 (SA-200C) - Q3D chip
- NCP 2.1 (SA-400C) - Q3D chip
- NCP 3.0 (SA-800C) - Q3D chip

### Cluster Platforms (Placeholder Data - NEEDS UPDATE)
- CL-51 (Cluster 5.1)
- CL-71 (Cluster 7.1)
- CL-102 (Cluster 10.2)

### NCAI Platforms (Placeholder Data - NEEDS UPDATE)
- NCAI AI-100
- NCAI AI-200

### CHIPS (Placeholder Data - NEEDS UPDATE)
- Q2D Chip
- Q3D Chip

## What You Need to Find in Drivenets Portal

### Document 1: Product Catalog
**Look for**:
- Complete list of all SA models (NCP series)
- Complete list of all Cluster models (CL series)
- Any NCAI or AI-optimized platforms
- Official model codes (e.g., SA-40C, SA-800C, CL-51, etc.)

### Document 2: Hardware Specifications
**Look for**:
- Which chip each platform uses (Q2D, Q3D, or future chips)
- Port count per platform
- Capacity per platform (40G, 100G, 200G, 400G, 800G, etc.)
- Interface types supported (Ethernet, LAG, RDMA, etc.)

### Document 3: DNOS CLI Reference
**Look for**:
- Interface naming convention: `eth-X/Y/Z` format
- How chassis/slot/port numbers work
- LAG interface naming: `lag-X`
- Management interface naming: `mgmt0` or other
- Special interface types (if any)

### Document 4: Platform-Specific Guides
**For each platform, find**:
- Exact interface names in CLI
- Number of interfaces available
- Interface capabilities
- Any platform-specific naming conventions

## How I Would Extract the Data (If I Had Access)

### Method 1: From PDF Documentation

```python
# Pseudo-code for extraction
1. Download DNOS CLI Reference PDF
2. Search for sections:
   - "Interface Configuration"
   - "Platform Specifications"
   - "show interfaces" command output examples
3. Extract interface naming patterns
4. Build data structure
```

### Method 2: From Web Portal

```python
# Pseudo-code for web scraping
1. Login to Drivenets Portal
2. Navigate to: Products > Specifications
3. For each platform:
   - Extract model name
   - Extract chip type
   - Extract interface list
4. Navigate to: Documentation > CLI Reference
5. Extract interface naming conventions
6. Combine data into JSON structure
```

### Method 3: From API (If Available)

```python
# If Drivenets has an API
1. API endpoint: /api/platforms
2. GET all platforms
3. For each platform ID:
   GET /api/platforms/{id}/interfaces
4. Parse response into our data structure
```

## Current Implementation Status

✅ **Framework Created**: Complete data structure ready
✅ **Cascading Selection**: Category → Model working
✅ **Interface Menu**: Platform-dependent (currently uses placeholder data)
❌ **Official Data**: NEEDS to be obtained from Drivenets portal

## How to Update with Official Data

Once you have the official information, simply replace the `drivenetsModels` object in `topology.js` (line ~9974).

### Example Update Template

```javascript
const drivenetsModels = {
    'sa': {
        label: 'SA (Stand Alone)',
        models: [
            // ===== UPDATE EACH MODEL BLOCK LIKE THIS =====
            {
                value: 'ncp-3.0-sa800c',           // Unique ID (any format)
                label: 'NCP 3.0 (SA-800C)',        // ← FROM OFFICIAL DOCS
                chip: 'Q3D',                       // ← FROM DATASHEET
                capacity: '800G',                  // ← FROM SPECS
                interfaces: [                       // ← FROM CLI REFERENCE
                    'eth-1/1/1',
                    'eth-1/1/2',
                    // ... complete list from documentation
                    'mgmt0'
                ]
            },
            // Add all other SA models from portal
        ]
    },
    'cluster': {
        // Same structure for cluster platforms
    },
    // ... other categories
};
```

## Next Steps for You

1. **Access Drivenets Portal**: Login to partner/customer portal
2. **Find Documentation**: Look for product specs and CLI guides
3. **Extract Data**: Use table from this document as template
4. **Share with Me**: Provide the official data
5. **I'll Update**: I'll integrate it into the code perfectly

Would you like me to:
A) Create a more detailed extraction template you can fill in?
B) Implement a CSV/JSON import feature so you can load official data?
C) Create a tool to help you format the data once you have it?

Let me know what would be most helpful!





