# DNOS MPLS Configuration Reference

*Configuration commands for MPLS protocol*

---

## Overview

MPLS (Multiprotocol Label Switching) is a packet-forwarding technology that uses labels to make data forwarding decisions. It enables efficient network traffic flow by creating label-switched paths (LSPs).

---

## Protocol Configuration

### protocols mpls

Enable MPLS protocol globally.

**Syntax:**
```
protocols mpls
```

**Hierarchy:**
```
protocols {
    mpls {
        ...
    }
}
```

---

### mpls ttl-propagate

Configure MPLS TTL propagation behavior.

**Syntax:**
```
protocols mpls ttl-propagate <all|disabled>
```

**Parameters:**
| Parameter | Description |
|-----------|-------------|
| `all` | Propagate TTL from IP to MPLS and vice versa |
| `disabled` | Disable TTL propagation |

**Example:**
```
protocols mpls ttl-propagate all
```

**Notes:**
- When disabled, MPLS core is hidden from traceroute
- Security consideration: hiding core topology
- Operational consideration: debugging becomes harder

---

## MPLS Interface Configuration

### mpls interface

Enable MPLS on an interface.

**Syntax:**
```
interfaces <interface-name> mpls
```

**Example:**
```
interfaces ge0/0/1 {
    mpls
}
```

---

## Label Range Configuration

### mpls label-range

Configure MPLS label range.

**Syntax:**
```
protocols mpls label-range <start-label> <end-label>
```

**Parameters:**
| Parameter | Description | Range |
|-----------|-------------|-------|
| `start-label` | Starting label value | 16-1048575 |
| `end-label` | Ending label value | 16-1048575 |

**Example:**
```
protocols mpls label-range 16 100000
```

**Notes:**
- Labels 0-15 are reserved
- Default range is platform-specific
- Ensure adequate label space for network scale

---

## Complete MPLS Configuration Example

```
# Enable MPLS globally
protocols {
    mpls {
        ttl-propagate all
    }
}

# Enable MPLS on interfaces
interfaces {
    ge0/0/1 {
        description "MPLS Core Link to R2"
        mtu 9216
        mpls
    }
    
    ge0/0/2 {
        description "MPLS Core Link to R3"
        mtu 9216
        mpls
    }
    
    lo0 {
        description "Loopback"
        mpls
    }
}

# LDP for label distribution
protocols {
    ldp {
        router-id 1.1.1.1
        address-family ipv4 {
            discovery transport-address 1.1.1.1
            interface ge0/0/1
            interface ge0/0/2
        }
    }
}
```

---

## MPLS with Segment Routing

For Segment Routing MPLS, refer to the Segment-Routing documentation:

```
protocols {
    segment-routing {
        global-block {
            lower-bound 16000
            upper-bound 23999
        }
        
        mpls {
            admin-state enabled
            
            prefix-sid-map {
                prefix 1.1.1.1/32 index 1
            }
        }
    }
}
```

---

## MPLS Traffic Engineering

For MPLS-TE configuration, refer to the Traffic-Engineering documentation:

```
protocols {
    mpls {
        traffic-engineering {
            router-id 1.1.1.1
            
            interface ge0/0/1 {
                admin-group blue
                te-metric 10
            }
            
            tunnel RSVP-TE-TO-R5 {
                destination 5.5.5.5
                path PRIMARY {
                    explicit-path AVOID-R3
                }
            }
        }
    }
}
```

---

## Show Commands

| Command | Description |
|---------|-------------|
| `show mpls` | Display MPLS summary |
| `show mpls forwarding-table` | Display MPLS forwarding table |
| `show mpls label-range` | Display MPLS label range |
| `show mpls route` | Display MPLS routes |
| `show mpls statistics` | Display MPLS statistics |
| `show mpls statistics forwarding-table` | Display forwarding table stats |
| `show mpls traffic-engineering` | Display MPLS-TE info |
| `show mpls traffic-engineering tunnels` | Display MPLS-TE tunnels |
| `show mpls p2mp` | Display P2MP information |

---

## Clear Commands

| Command | Description |
|---------|-------------|
| `clear mpls statistics forwarding-table` | Clear forwarding table statistics |
| `clear mpls statistics route p2mp` | Clear P2MP route statistics |
| `clear mpls traffic-engineering pcep counters` | Clear PCEP counters |

---

## MPLS MTU Considerations

Ensure adequate MTU for MPLS labels:

| Scenario | Additional Bytes | Recommended MTU |
|----------|-----------------|-----------------|
| Single label | 4 bytes | 1504+ |
| LDP + VPN | 8 bytes | 1508+ |
| LDP + VPN + ELI/EL | 16 bytes | 1516+ |
| SR with deep stacks | 32+ bytes | 9000+ (jumbo) |

**Configuration:**
```
interfaces ge0/0/1 {
    mtu 9216
    mpls
}
```

---

## Best Practices

1. **Use jumbo MTU**: Enable 9000+ byte MTU on MPLS interfaces
2. **Configure TTL propagation carefully**: Based on security requirements
3. **Reserve adequate label space**: Plan for future growth
4. **Enable MPLS on all core interfaces**: Consistent forwarding plane
5. **Use Segment Routing or LDP**: Choose one label distribution mechanism
6. **Monitor forwarding table**: Stay within platform limits

