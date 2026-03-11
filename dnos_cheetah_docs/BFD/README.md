# DNOS BFD (Bidirectional Forwarding Detection) Configuration Reference

*Configuration commands for BFD protocol*

---

## Overview

BFD (Bidirectional Forwarding Detection) is a protocol for detecting faults in the bidirectional path between two forwarding engines. It provides fast failure detection for routing protocols.

---

## Protocol Configuration

### protocols bfd

Enable BFD protocol globally.

**Syntax:**
```
protocols bfd
```

**Hierarchy:**
```
protocols {
    bfd {
        ...
    }
}
```

---

### protocols bfd class-of-service

Configure Class of Service for BFD packets.

**Syntax:**
```
protocols bfd class-of-service <cos-value>
```

**Parameters:**
| Parameter | Description | Range |
|-----------|-------------|-------|
| `cos-value` | CoS value for BFD packets | 0-7 |

**Example:**
```
protocols bfd class-of-service 6
```

---

### protocols bfd interface

Configure BFD on an interface.

**Syntax:**
```
protocols bfd interface <interface-name>
```

**Parameters:**
| Parameter | Description | Type |
|-----------|-------------|------|
| `interface-name` | Name of the interface | String (e.g., ge0/0/1, bundle1) |

**Example:**
```
protocols bfd interface ge0/0/1
```

**Hierarchy:**
```
protocols {
    bfd {
        interface ge0/0/1 {
            ...
        }
    }
}
```

---

### protocols bfd maximum-sessions

Configure maximum BFD sessions.

**Syntax:**
```
protocols bfd maximum-sessions <value>
```

**Parameters:**
| Parameter | Description | Range |
|-----------|-------------|-------|
| `value` | Maximum number of BFD sessions | Platform dependent |

**Example:**
```
protocols bfd maximum-sessions 1000
```

---

## Interface BFD Configuration

### bfd interface local-address

Configure local address for BFD on an interface.

**Syntax:**
```
protocols bfd interface <interface-name> local-address <ip-address>
```

**Parameters:**
| Parameter | Description | Type |
|-----------|-------------|------|
| `interface-name` | Name of the interface | String |
| `ip-address` | Local IP address for BFD | IPv4/IPv6 address |

**Example:**
```
protocols bfd interface ge0/0/1 local-address 10.0.0.1
```

---

### bfd interface min-rx

Configure minimum receive interval for BFD.

**Syntax:**
```
protocols bfd interface <interface-name> min-rx <interval>
```

**Parameters:**
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `interval` | Minimum receive interval in milliseconds | 50-60000 | 300 |

**Example:**
```
protocols bfd interface ge0/0/1 min-rx 100
```

---

### bfd interface min-tx

Configure minimum transmit interval for BFD.

**Syntax:**
```
protocols bfd interface <interface-name> min-tx <interval>
```

**Parameters:**
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `interval` | Minimum transmit interval in milliseconds | 50-60000 | 300 |

**Example:**
```
protocols bfd interface ge0/0/1 min-tx 100
```

---

### bfd interface multiplier

Configure detection multiplier for BFD.

**Syntax:**
```
protocols bfd interface <interface-name> multiplier <value>
```

**Parameters:**
| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `value` | Detection multiplier | 2-255 | 3 |

**Notes:**
- Detection time = multiplier × interval
- With multiplier 3 and interval 100ms, detection time is 300ms

**Example:**
```
protocols bfd interface ge0/0/1 multiplier 3
```

---

### bfd interface neighbor

Configure BFD neighbor on an interface.

**Syntax:**
```
protocols bfd interface <interface-name> neighbor <neighbor-ip>
```

**Parameters:**
| Parameter | Description | Type |
|-----------|-------------|------|
| `interface-name` | Name of the interface | String |
| `neighbor-ip` | Neighbor IP address | IPv4/IPv6 address |

**Example:**
```
protocols bfd interface ge0/0/1 neighbor 10.0.0.2
```

---

## Complete Configuration Example

```
protocols {
    bfd {
        class-of-service 6
        maximum-sessions 500
        interface ge0/0/1 {
            local-address 10.0.0.1
            min-rx 100
            min-tx 100
            multiplier 3
            neighbor 10.0.0.2
        }
        interface ge0/0/2 {
            local-address 10.0.1.1
            min-rx 100
            min-tx 100
            multiplier 3
            neighbor 10.0.1.2
        }
    }
}
```

---

## BFD with Routing Protocols

### BFD with IS-IS

```
protocols {
    isis area-1 {
        interface ge0/0/1 {
            bfd {
                admin-state enabled
                min-rx 100
                min-tx 100
                multiplier 3
            }
        }
    }
}
```

### BFD with OSPF

```
protocols {
    ospf 1 {
        area 0 {
            interface ge0/0/1 {
                bfd {
                    admin-state enabled
                }
            }
        }
    }
}
```

### BFD with BGP

```
protocols {
    bgp {
        neighbor 10.0.0.2 {
            bfd {
                admin-state enabled
                min-rx 100
                min-tx 100
                multiplier 3
            }
        }
    }
}
```

---

## Show Commands

| Command | Description |
|---------|-------------|
| `show bfd` | Display BFD summary |
| `show bfd sessions` | Display all BFD sessions |
| `show bfd sessions brief` | Display brief BFD session info |
| `show bfd sessions detail` | Display detailed BFD session info |
| `show bfd interface` | Display BFD interface configuration |
| `show bfd statistics` | Display BFD statistics |
| `show seamless-bfd` | Display Seamless BFD info |

---

## Clear Commands

| Command | Description |
|---------|-------------|
| `clear bfd session` | Clear BFD sessions |
| `clear bfd statistics` | Clear BFD statistics |

---

## Best Practices

1. **Tune timers appropriately**: Balance between fast detection and CPU load
2. **Use multiplier >= 3**: Prevents false positives from transient issues
3. **Consider async mode**: For unidirectional failure detection
4. **Monitor BFD flaps**: Frequent flaps may indicate network instability
5. **Use dedicated BFD sessions**: Separate from protocol sessions for better visibility

