# DNOS Multicast Configuration Reference

*Configuration commands for Multicast routing*

---

## Overview

Multicast enables efficient one-to-many data distribution, allowing a single source to send data to multiple receivers simultaneously without duplicating traffic.

---

## Protocol Configuration

### multicast

Enable multicast globally.

**Syntax:**
```
multicast
```

**Hierarchy:**
```
multicast {
    ...
}
```

---

### multicast max-sg-replications

Configure maximum (S,G) replications for multicast.

**Syntax:**
```
multicast max-sg-replications <value>
```

**Parameters:**
| Parameter | Description | Range |
|-----------|-------------|-------|
| `value` | Maximum number of (S,G) replications | Platform dependent |

**Example:**
```
multicast max-sg-replications 32000
```

**Notes:**
- Controls the maximum number of multicast forwarding entries
- Adjust based on expected multicast scale
- Platform limits apply

---

### rpf-intact admin-state

Configure RPF (Reverse Path Forwarding) intact mode.

**Syntax:**
```
multicast rpf-intact admin-state <enabled|disabled>
```

**Parameters:**
| Parameter | Description |
|-----------|-------------|
| `enabled` | Enable RPF intact mode |
| `disabled` | Disable RPF intact mode |

**Example:**
```
multicast rpf-intact admin-state enabled
```

**Notes:**
- RPF intact preserves the RPF check behavior
- Used in specific multicast VPN scenarios

---

## PIM Configuration

### protocols pim

Enable PIM (Protocol Independent Multicast).

**Syntax:**
```
protocols pim
```

**Hierarchy:**
```
protocols {
    pim {
        ...
    }
}
```

---

### PIM Interface Configuration

```
protocols pim interface <interface-name>
```

**Sub-commands:**
| Command | Description |
|---------|-------------|
| `admin-state enabled` | Enable PIM on interface |
| `mode sparse` | Configure sparse mode |
| `mode dense` | Configure dense mode |
| `hello-interval <seconds>` | Configure hello interval |
| `dr-priority <priority>` | Configure DR priority |
| `bfd admin-state enabled` | Enable BFD for PIM |

**Example:**
```
protocols {
    pim {
        interface ge0/0/1 {
            admin-state enabled
            mode sparse
            hello-interval 30
            dr-priority 100
        }
    }
}
```

---

### PIM Rendezvous Point Configuration

```
protocols pim rp-address <rp-ip>
```

**Parameters:**
| Parameter | Description |
|-----------|-------------|
| `rp-ip` | IP address of the Rendezvous Point |

**Example:**
```
protocols pim rp-address 10.0.0.1
```

---

### PIM Sparse Mode Configuration

```
protocols pim sparse {
    spt-threshold <value|infinity>
    join-prune-interval <seconds>
}
```

**Example:**
```
protocols {
    pim {
        sparse {
            spt-threshold infinity
            join-prune-interval 60
        }
    }
}
```

---

## MSDP Configuration

### protocols msdp

Enable MSDP (Multicast Source Discovery Protocol).

**Syntax:**
```
protocols msdp
```

**Hierarchy:**
```
protocols {
    msdp {
        ...
    }
}
```

---

### MSDP Peer Configuration

```
protocols msdp peer <peer-ip>
```

**Sub-commands:**
| Command | Description |
|---------|-------------|
| `remote-as <asn>` | Configure remote AS number |
| `connect-source <interface>` | Configure source interface |
| `default-peer` | Configure as default peer |
| `mesh-group <name>` | Configure mesh group membership |

**Example:**
```
protocols {
    msdp {
        peer 10.0.0.2 {
            remote-as 65001
            connect-source lo0
        }
        peer 10.0.0.3 {
            remote-as 65002
            connect-source lo0
        }
    }
}
```

---

## IGMP Configuration

### protocols igmp

Enable IGMP (Internet Group Management Protocol).

**Syntax:**
```
protocols igmp
```

**Hierarchy:**
```
protocols {
    igmp {
        ...
    }
}
```

---

### IGMP Interface Configuration

```
protocols igmp interface <interface-name>
```

**Sub-commands:**
| Command | Description |
|---------|-------------|
| `admin-state enabled` | Enable IGMP on interface |
| `version <1|2|3>` | Configure IGMP version |
| `query-interval <seconds>` | Configure query interval |
| `query-max-response-time <seconds>` | Configure max response time |

**Example:**
```
protocols {
    igmp {
        interface ge0/0/1 {
            admin-state enabled
            version 3
            query-interval 125
        }
    }
}
```

---

## Complete Configuration Example

```
# Global multicast configuration
multicast {
    max-sg-replications 32000
    rpf-intact admin-state disabled
}

# PIM configuration
protocols {
    pim {
        rp-address 10.0.0.1
        
        sparse {
            spt-threshold infinity
            join-prune-interval 60
        }
        
        interface ge0/0/1 {
            admin-state enabled
            mode sparse
            hello-interval 30
            dr-priority 100
        }
        
        interface ge0/0/2 {
            admin-state enabled
            mode sparse
            hello-interval 30
            dr-priority 50
        }
        
        interface lo0 {
            admin-state enabled
            mode sparse
        }
    }
}

# IGMP configuration
protocols {
    igmp {
        interface ge0/0/1 {
            admin-state enabled
            version 3
        }
    }
}

# MSDP configuration (for inter-domain multicast)
protocols {
    msdp {
        peer 10.0.0.2 {
            remote-as 65001
            connect-source lo0
        }
    }
}
```

---

## Show Commands

| Command | Description |
|---------|-------------|
| `show multicast` | Display multicast summary |
| `show multicast forwarding-table` | Display multicast forwarding table |
| `show multicast route` | Display multicast routes |
| `show multicast route statistics` | Display multicast route statistics |
| `show pim` | Display PIM summary |
| `show pim interface` | Display PIM interfaces |
| `show pim neighbor` | Display PIM neighbors |
| `show pim rp` | Display PIM RP information |
| `show pim tree` | Display PIM tree information |
| `show pim statistics` | Display PIM statistics |
| `show msdp` | Display MSDP summary |
| `show msdp peers` | Display MSDP peers |
| `show msdp cache` | Display MSDP SA cache |

---

## Clear Commands

| Command | Description |
|---------|-------------|
| `clear multicast route statistics` | Clear multicast route statistics |
| `clear pim statistics` | Clear PIM statistics |
| `clear pim tree` | Clear PIM tree state |
| `clear msdp cache` | Clear MSDP SA cache |
| `clear msdp peers` | Reset MSDP peer sessions |
| `clear msdp statistics` | Clear MSDP statistics |

---

## Best Practices

1. **Use PIM Sparse Mode**: More scalable than dense mode
2. **Configure Anycast RP**: For RP redundancy
3. **Tune IGMP timers**: Balance between responsiveness and overhead
4. **Monitor (S,G) scale**: Stay within platform limits
5. **Use BFD for PIM**: Fast neighbor failure detection

