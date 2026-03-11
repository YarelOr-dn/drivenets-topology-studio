# DriveNets Version Stack Architecture

This document describes the DriveNets software stack architecture, version compatibility rules, and upgrade procedures.

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                          STACK                                  │
├─────────┬─────────┬─────────┬─────────┬─────────────────────────┤
│  ONIE   │Firmware │ BaseOS  │   GI    │         DNOS            │
│         │         │         │         │                         │
│Bootloader│ HW FW  │Linux OS │Golden   │ DriveNets Network OS    │
│         │ (NCM)  │(Ubuntu) │ Image   │                         │
└─────────┴─────────┴─────────┴─────────┴─────────────────────────┘
```

### Component Descriptions

| Component | Description | Package Pattern |
|-----------|-------------|-----------------|
| **DNOS** | DriveNets Network Operating System - main routing software | `drivenets_dnos_*.tar` |
| **GI** | Golden Image - container orchestration layer | `drivenets_gi_*.tar` |
| **BaseOS** | Linux Ubuntu-based OS running on physical hardware | `drivenets_baseos_*.tar` |
| **Firmware** | Hardware-specific firmware (NCM, BMC, StrataX) | `onie-firmware-*.tar` |
| **ONIE** | Open Network Install Environment - bootloader | `onie-*.tar` |

## Version Compatibility Rules

### Major Version Matching
**Critical Rule:** DNOS, GI, and BaseOS must share the same major version.

```
✅ v25.1 DNOS + v25.1 GI + v25.1 BaseOS
✅ v19.3 DNOS + v19.3 GI + v19.3 BaseOS
❌ v25.1 DNOS + v19.3 GI + v25.1 BaseOS  (VERSION MISMATCH!)
```

### Private Build Rules
When working with private/development builds:
- **DNOS**: Take from the private branch
- **GI + BaseOS**: Always take from the **main branch** of the same version

Example:
```
For testing private feature on v25.1:
- DNOS: From private branch (e.g., SW-12345-my-feature)
- GI: From dev_v25_1 main branch
- BaseOS: From dev_v25_1 main branch
```

### Build Version Format
```
DNOS:   25.1.0.464_dev.dev_v25_1_1050
        │   │ │   │   │          │
        │   │ │   │   │          └── Jenkins build number
        │   │ │   │   └── Branch name
        │   │ │   └── Build type (dev/priv/rel)
        │   │ └── Patch version
        │   └── Minor version
        └── Major version

BaseOS: 2.25104397329
        │ │
        │ └── Computed version from DNOS version + seeds
        └── BaseOS major version

GI:     25.1.0.59_dev.dev_v25_1_143
        Same format as DNOS
```

## Storage Locations (Minio Buckets)

| Bucket | Retention | Purpose | URL Pattern |
|--------|-----------|---------|-------------|
| `dnpkg-48hrs` | 48 hours | Dev builds | `http://minio-ssd.dev.drivenets.net:9000/dnpkg-48hrs/` |
| `dnpkg-30days` | 30 days | Extended dev | `http://minio-ssd.dev.drivenets.net:9000/dnpkg-30days/` |
| `dnpkg-60days` | 60 days | QA versions | `http://minio-ssd.dev.drivenets.net:9000/dnpkg-60days/` |
| `dnos-rel` | Permanent | Official releases | `http://minio-il.dev.drivenets.net:9000/dnos-rel/` |

### Minio URLs
- **Israel Office**: `http://minio-ssd.dev.drivenets.net:9000/`
- **Romania Office**: `http://minio-ssd-ro.dev.drivenets.net:9000/`
- **Legacy/IO**: `http://minioio.dev.drivenets.net:9000/`

## Jenkins Build System

### Main Build Jobs

| Job | Purpose | URL |
|-----|---------|-----|
| `cheetah` | Main DNOS build pipeline | `/job/drivenets/job/cheetah/job/{branch}/` |
| `ArtifactCreator` | Creates signed tarballs | `/job/ArtifactCreator/` |
| `cdnos_image_creation` | Container DNOS images | `/job/cdnos_image_creation/` |
| `MainBranches` | Branch management | `/job/MainBranches/` |

### Build Parameters

| Parameter | Values | Effect |
|-----------|--------|--------|
| `SHOULD_BUILD_BASEOS_CONTAINERS` | Yes/No | Build BaseOS package |
| `TESTS_BASEOS` | true/false | Run BaseOS tests |
| `NIGHTLY` | true/false | Nightly build (no delta, save stable) |
| `QA_VERSION` | true/false | 60-day retention, QA registry |
| `PROMOTE_RELEASE` | true/false | Official release, permanent storage |

### Build Artifacts
After a successful build, these artifact files contain Minio URLs:

| Artifact File | Content |
|---------------|---------|
| `gi_DNOS_artifact.txt` | DNOS package Minio URL |
| `gi_GI_artifact.txt` | GI package Minio URL |
| `gi_BaseOS_artifact.txt` | BaseOS package Minio URL |
| `minio_link.txt` | Combined image URL |

## Device Stack Management

### Viewing Current Stack
```bash
# Show all stacks (revert, current, target)
show system stack

# Example output:
| Component | HW Model | Revert | Current | Target |
|-----------|----------|--------|---------|--------|
| BASEOS | default | 2.25104397329 | 2.25104397329 | 2.25104397329 |
| DNOS | default | 25.1.0.464_dev | 25.1.0.464_dev | 25.1.0.464_dev |
| GI | default | 25.1.0.59_dev | 25.1.0.59_dev | 25.1.0.59_dev |
| FIRMWARE | 5916-54XL | 3.3.5.2 | 3.3.5.2 | 3.3.5.2 |

# Detailed stack info
show system stack detail
show system stack detail os-packages
```

### Loading Packages to Target Stack
```bash
# Load each component (order: BaseOS -> GI -> DNOS recommended)
request system target-stack load http://minio-ssd.dev.drivenets.net:9000/dnpkg-48hrs/drivenets_baseos_2.25104397329.tar
request system target-stack load http://minio-ssd.dev.drivenets.net:9000/dnpkg-48hrs/drivenets_gi_25.1.0.59_dev.dev_v25_1_143.tar
request system target-stack load http://minio-ssd.dev.drivenets.net:9000/dnpkg-48hrs/drivenets_dnos_25.1.0.464_dev.dev_v25_1_1050.tar

# Check load progress
show system target-stack load history
```

### Installing Target Stack
```bash
# From DNOS mode - upgrade
request system target-stack install

# From GI mode - deploy new system
request system deploy system-type SA-40C name ROUTER-01 ncc-id 0

# System types:
# SA-40C   - NCP1 Standalone
# SA-36CD-S - NCP3 Standalone  
# CL-16    - DNI Cluster
# CL-51    - NCP3 Cluster
```

### Monitoring Installation
```bash
# Watch installation progress
show system install

# Example output:
Task ID: 1719993530376
Installation type: upgrade
Task status: IN-PROGRESS
Task start time: 2024-07-03 11:29:30
Task elapsed time: 0:05:09

# When complete:
Task status: COMPLETED
```

### Reverting to Previous Version
```bash
# Revert to previous stack
request system revert-stack install
```

### Deleting DNOS (to re-deploy)
```bash
# From DNOS mode - delete current installation
request system delete

# Or restore to GI mode
request system restore
```

## Upgrade Flow Diagrams

### Standard Upgrade (DNOS to DNOS)
```
[DNOS Running] 
    │
    ├─ request system target-stack load <baseos_url>
    ├─ request system target-stack load <gi_url>
    ├─ request system target-stack load <dnos_url>
    │
    ├─ show system stack  (verify target)
    │
    └─ request system target-stack install
           │
           └─ [Upgrade in Progress]
                  │
                  └─ [New DNOS Running]
```

### Fresh Deploy (GI to DNOS)
```
[GI Mode - gicli#] 
    │
    ├─ request system target-stack load <dnos_url>
    │
    ├─ show system stack  (verify target)
    │
    └─ request system deploy system-type <type> name <name> ncc-id 0
           │
           └─ [Deployment in Progress]
                  │
                  └─ [DNOS Running]
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Target stack is empty" | No packages loaded | Load packages first |
| "Version mismatch" | Incompatible versions | Use matching major versions |
| Load failed | URL expired (>48hrs) | Get fresh build URL |
| Install stuck | Network/storage issue | Check connectivity, retry |

### Checking Build Age
Dev builds in `dnpkg-48hrs` expire after 48 hours. Always check build timestamp:
- Jenkins build page shows "Build Time"
- If >48hrs old, trigger a new build or use QA/release versions

### Logs and Debugging
```bash
# From shell access
run start shell
cd /var/log/
tail -f gi-manager.log

# Check container status
docker ps
```

## References

- [GI Logic | Versioning](https://drivenets.atlassian.net/wiki/spaces/QA/pages/5271486545)
- [G.I. - DNOS Versions and GI](https://drivenets.atlassian.net/wiki/spaces/QA/pages/3461152771)
- [DNOS versioning and artifacts](https://drivenets.atlassian.net/wiki/spaces/DNDOPS/pages/2041675834)
- [How to Deploy DNOS over GI BaseOS](https://drivenets.atlassian.net/wiki/spaces/UP/pages/4976313672)


