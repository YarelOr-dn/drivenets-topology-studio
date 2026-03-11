# DNOS LDP (Label Distribution Protocol) Configuration Reference

*Comprehensive documentation for 26 LDP configuration commands*

---

## Overview

LDP (Label Distribution Protocol) is used to distribute MPLS labels between routers. It establishes Label Switched Paths (LSPs) by creating label mappings for FEC (Forwarding Equivalence Class) entries.

---

## Protocol Configuration

### protocols ldp

Enable LDP protocol globally.

**Syntax:**
```
protocols ldp
```

**Hierarchy:**
```
protocols {
    ldp {
        ...
    }
}
```

---

### ldp router-id

Configure LDP router ID.

**Syntax:**
```
protocols ldp router-id <ip-address>
```

**Parameters:**
| Parameter | Description | Type |
|-----------|-------------|------|
| `ip-address` | Router ID for LDP | IPv4 address |

**Example:**
```
protocols ldp router-id 1.1.1.1
```

**Notes:**
- Should match the loopback interface address
- Used to identify the router in LDP sessions

---

### ldp administrative-distance

Configure LDP administrative distance.

**Syntax:**
```
protocols ldp administrative-distance <value>
```

**Parameters:**
| Parameter | Description | Range |
|-----------|-------------|-------|
| `value` | Administrative distance | 1-255 |

**Example:**
```
protocols ldp administrative-distance 20
```

---

### ldp class-of-service

Configure Class of Service for LDP packets.

**Syntax:**
```
protocols ldp class-of-service <cos-value>
```

**Parameters:**
| Parameter | Description | Range |
|-----------|-------------|-------|
| `cos-value` | CoS value for LDP packets | 0-7 |

**Example:**
```
protocols ldp class-of-service 6
```

---

### ldp authentication

Configure LDP authentication.

**Syntax:**
```
protocols ldp authentication md5-key <key>
```

**Parameters:**
| Parameter | Description | Type |
|-----------|-------------|------|
| `md5-key` | MD5 authentication key | String |

**Example:**
```
protocols ldp authentication md5-key MySecretKey123
```

---

## Address Family Configuration

### ldp address-family

Configure LDP address family.

**Syntax:**
```
protocols ldp address-family <ipv4|ipv6>
```

**Parameters:**
| Parameter | Description |
|-----------|-------------|
| `ipv4` | IPv4 address family |
| `ipv6` | IPv6 address family |

**Hierarchy:**
```
protocols {
    ldp {
        address-family ipv4 {
            ...
        }
    }
}
```

---

### ldp address-family interface

Configure LDP on an interface.

**Syntax:**
```
protocols ldp address-family <ipv4|ipv6> interface <interface-name>
```

**Parameters:**
| Parameter | Description | Type |
|-----------|-------------|------|
| `interface-name` | Name of the interface | String (e.g., ge0/0/1) |

**Example:**
```
protocols ldp address-family ipv4 interface ge0/0/1
```

---

### ldp address-family discovery hello

Configure LDP discovery hello parameters.

**Syntax:**
```
protocols ldp address-family <ipv4|ipv6> discovery hello holdtime <seconds>
protocols ldp address-family <ipv4|ipv6> discovery hello interval <seconds>
```

**Parameters:**
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `holdtime` | Hello holdtime in seconds | 1-65535 | 15 |
| `interval` | Hello interval in seconds | 1-65535 | 5 |

**Example:**
```
protocols ldp address-family ipv4 discovery hello holdtime 45
protocols ldp address-family ipv4 discovery hello interval 15
```

---

### ldp address-family discovery transport-address

Configure LDP transport address.

**Syntax:**
```
protocols ldp address-family <ipv4|ipv6> discovery transport-address <ip-address|interface>
```

**Parameters:**
| Parameter | Description | Type |
|-----------|-------------|------|
| `ip-address` | Transport address | IPv4/IPv6 address |
| `interface` | Use interface address | Interface name |

**Example:**
```
protocols ldp address-family ipv4 discovery transport-address 1.1.1.1
```

---

### ldp address-family discovery targeted

Configure targeted LDP sessions.

**Syntax:**
```
protocols ldp address-family <ipv4|ipv6> discovery targeted
```

**Sub-commands:**
| Command | Description |
|---------|-------------|
| `accept` | Accept targeted hello from any source |
| `hello holdtime <seconds>` | Configure targeted hello holdtime |
| `hello interval <seconds>` | Configure targeted hello interval |

**Example:**
```
protocols ldp address-family ipv4 discovery targeted accept
protocols ldp address-family ipv4 discovery targeted hello holdtime 60
protocols ldp address-family ipv4 discovery targeted hello interval 20
```

---

### ldp address-family session holdtime

Configure LDP session holdtime.

**Syntax:**
```
protocols ldp address-family <ipv4|ipv6> session holdtime <seconds>
```

**Parameters:**
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `seconds` | Session holdtime in seconds | 15-65535 | 180 |

**Example:**
```
protocols ldp address-family ipv4 session holdtime 180
```

---

### ldp address-family label allocation-filter

Configure LDP label allocation filter.

**Syntax:**
```
protocols ldp address-family <ipv4|ipv6> label allocation-filter <prefix-list-name>
```

**Parameters:**
| Parameter | Description | Type |
|-----------|-------------|------|
| `prefix-list-name` | Name of the prefix list | String |

**Example:**
```
protocols ldp address-family ipv4 label allocation-filter LOOPBACKS-ONLY
```

---

### ldp address-family label explicit-null

Configure LDP explicit null labels.

**Syntax:**
```
protocols ldp address-family <ipv4|ipv6> label explicit-null <for|filter>
```

**Options:**
| Option | Description |
|--------|-------------|
| `for prefix-list` | Apply explicit-null for specific prefixes |
| `filter prefix-list` | Filter explicit-null for specific prefixes |

**Example:**
```
protocols ldp address-family ipv4 label explicit-null for EXPLICIT-NULL-PREFIXES
```

---

### ldp address-family interface discovery hello

Configure per-interface LDP discovery parameters.

**Syntax:**
```
protocols ldp address-family <ipv4|ipv6> interface <interface-name> discovery hello holdtime <seconds>
protocols ldp address-family <ipv4|ipv6> interface <interface-name> discovery hello interval <seconds>
```

**Example:**
```
protocols ldp address-family ipv4 interface ge0/0/1 discovery hello holdtime 30
protocols ldp address-family ipv4 interface ge0/0/1 discovery hello interval 10
```

---

## Graceful Restart Configuration

### ldp graceful-restart

Configure LDP graceful restart.

**Syntax:**
```
protocols ldp graceful-restart
```

**Sub-commands:**
| Command | Description |
|---------|-------------|
| `admin-state enabled` | Enable graceful restart |
| `reconnect-time <seconds>` | Configure reconnect time |
| `recovery-time <seconds>` | Configure recovery time |

---

### ldp graceful-restart admin-state

Enable or disable LDP graceful restart.

**Syntax:**
```
protocols ldp graceful-restart admin-state <enabled|disabled>
```

**Example:**
```
protocols ldp graceful-restart admin-state enabled
```

---

### ldp graceful-restart reconnect-time

Configure LDP graceful restart reconnect time.

**Syntax:**
```
protocols ldp graceful-restart reconnect-time <seconds>
```

**Parameters:**
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `seconds` | Reconnect time in seconds | 10-300 | 120 |

**Example:**
```
protocols ldp graceful-restart reconnect-time 120
```

---

### ldp graceful-restart recovery-time

Configure LDP graceful restart recovery time.

**Syntax:**
```
protocols ldp graceful-restart recovery-time <seconds>
```

**Parameters:**
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `seconds` | Recovery time in seconds | 60-1800 | 300 |

**Example:**
```
protocols ldp graceful-restart recovery-time 300
```

---

## Neighbor Configuration

### ldp neighbor

Configure LDP neighbor-specific settings.

**Syntax:**
```
protocols ldp neighbor <neighbor-ip>
```

**Sub-commands:**
| Command | Description |
|---------|-------------|
| `authentication md5-key <key>` | Configure per-neighbor authentication |
| `session holdtime <seconds>` | Configure per-neighbor session holdtime |

---

### ldp neighbor authentication

Configure per-neighbor LDP authentication.

**Syntax:**
```
protocols ldp neighbor <neighbor-ip> authentication md5-key <key>
```

**Example:**
```
protocols ldp neighbor 2.2.2.2 authentication md5-key Neighbor2Key
```

---

### ldp neighbor session holdtime

Configure per-neighbor LDP session holdtime.

**Syntax:**
```
protocols ldp neighbor <neighbor-ip> session holdtime <seconds>
```

**Example:**
```
protocols ldp neighbor 2.2.2.2 session holdtime 300
```

---

## IGP Synchronization

### ldp ldp-sync on-session-delay

Configure LDP-IGP synchronization delay.

**Syntax:**
```
protocols ldp ldp-sync on-session-delay <seconds>
```

**Parameters:**
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `seconds` | Delay before declaring sync | 0-60 | 0 |

**Example:**
```
protocols ldp ldp-sync on-session-delay 10
```

**Notes:**
- Used with IS-IS or OSPF LDP-IGP synchronization
- Prevents traffic black-holing during LDP convergence

---

## Other Configuration

### ldp rcv-addr-withdraw-delay

Configure receive address withdraw delay.

**Syntax:**
```
protocols ldp rcv-addr-withdraw-delay <seconds>
```

**Parameters:**
| Parameter | Description | Range |
|-----------|-------------|-------|
| `seconds` | Delay in seconds | 0-60 |

**Example:**
```
protocols ldp rcv-addr-withdraw-delay 5
```

---

## Complete Configuration Example

```
protocols {
    ldp {
        router-id 1.1.1.1
        class-of-service 6
        authentication md5-key GlobalLDPKey123
        administrative-distance 20
        rcv-addr-withdraw-delay 5
        
        ldp-sync on-session-delay 10
        
        graceful-restart {
            admin-state enabled
            reconnect-time 120
            recovery-time 300
        }
        
        address-family ipv4 {
            discovery {
                transport-address 1.1.1.1
                hello holdtime 45
                hello interval 15
                targeted {
                    accept
                    hello holdtime 60
                    hello interval 20
                }
            }
            
            session holdtime 180
            
            label {
                allocation-filter LOOPBACKS-ONLY
            }
            
            interface ge0/0/1 {
                discovery hello holdtime 30
                discovery hello interval 10
            }
            
            interface ge0/0/2
            interface ge0/0/3
        }
        
        neighbor 2.2.2.2 {
            authentication md5-key Neighbor2Key
            session holdtime 300
        }
    }
}

# Associated prefix list
routing-policy {
    prefix-list LOOPBACKS-ONLY {
        prefix 1.1.1.0/24 le 32
        prefix 2.2.2.0/24 le 32
        prefix 3.3.3.0/24 le 32
    }
}
```

---

## Show Commands

| Command | Description |
|---------|-------------|
| `show ldp` | Display LDP summary |
| `show ldp summary` | Display LDP summary with statistics |
| `show ldp bindings` | Display LDP label bindings |
| `show ldp discovery` | Display LDP discovery information |
| `show ldp interface` | Display LDP interfaces |
| `show ldp neighbor` | Display LDP neighbors |
| `show ldp igp-sync` | Display LDP-IGP sync status |
| `show ldp statistics` | Display LDP statistics |
| `show ldp capabilities` | Display LDP capabilities |
| `show ldp address-family` | Display LDP address family info |

---

## Clear Commands

| Command | Description |
|---------|-------------|
| `clear ldp neighbor` | Reset LDP neighbor sessions |
| `clear ldp neighbor statistics` | Clear LDP neighbor statistics |
| `clear ldp label-allocation` | Clear LDP label allocations |

---

## Best Practices

1. **Use router-id**: Set explicit router-id matching loopback
2. **Enable authentication**: Secure LDP sessions with MD5
3. **Configure graceful restart**: For non-stop forwarding during restarts
4. **Use label allocation filter**: Limit label distribution to necessary prefixes
5. **Enable LDP-IGP sync**: Prevent traffic loss during convergence
6. **Tune hello/holdtimes**: Balance between detection speed and stability

