# DNOS flowspec-local-policies Full Hierarchy Map

**Source:** Live `?` from PE-4 (YOR_CL_PE-4, DNOS, `kvm108-cl408d-ncc0`), 2026-02-22. YANG: `dn-flowspec-local-policies.yang`.

---

## 1. routing-policy flowspec-local-policies

### 1.1 Top level

**CLI path:** `configure` → `routing-policy` → `flowspec-local-policies`

| Option | Description (from PE-4 `?`) |
|--------|----------------------------|
| **ipv4** | Configure the ipv4 MCs and rules |
| **ipv6** | Configure the ipv6 MCs and rules |

---

### 1.2 flowspec-local-policies ipv4 / ipv6

Both AFIs have the same sub-options:

| Option | Description (PE-4 `?`) |
|--------|------------------------|
| **match-class** \<name\> | Configure a Match Class |
| **policy** \<name\> | Configure a policy |

---

## 2. match-class (under ipv4 or ipv6)

**CLI:** `routing-policy flowspec-local-policies ipv4 match-class <name>`

All knobs from PE-4 `?`:

| Knob | PE-4 Description | Value / Range | Details |
|------|-------------------|---------------|---------|
| **dest-ip** | Configure the dest-ip match criteria | `<A.B.C.D/x>` IPv4 address | Required if no src-ip |
| **src-ip** | Configure the src-ip match criteria | `<A.B.C.D/x>` IPv4 address | Required if no dest-ip |
| **dest-ports** | Configure the dest-port match criteria | `<0-65535>` Port or range | e.g. `53`, `80-443` |
| **src-ports** | Configure the src-ports range match criteria | `<0-65535>` Port or range | e.g. `123`, `1024-65535` |
| **protocol** | Configure a protocol match criteria | Protocol name or hex | See protocol map below |
| **dscp** | Configure a dscp match criteria | `<0-63>` DSCP value | IPv4 only |
| **packet-length** | Configure the packet-length match criteria | `<0-65535>` Length or range | e.g. `64-1500` |
| **tcp-flag** | Set the tcp-flag(s) to match | `syn,ack,urg,psh,rst,fin` | Comma-separated string |
| **fragmented** | Configure match on fragmented packets | `<CR>` (presence flag) | No value needed |
| **icmp** | Configure the icmp match criteria | ICMP message type | See ICMP map below |
| **vrf** | Configure the vrf match criteria | `<text>` VRF Name | Restrict to specific VRF |
| **description** | Set the description of the match class | Free text | 1–255 chars |
| apply-groups | To apply the configuration groups | Group name | Inherited config |
| apply-groups-exclude | To exclude the configuration groups | Group name | Inherited config |

**Rule:** At least one of `dest-ip` or `src-ip` is required. All criteria are ANDed.

---

## 3. policy (under ipv4 or ipv6)

**CLI:** `routing-policy flowspec-local-policies ipv4 policy <name>`

### 3.1 Policy-level options (PE-4 `?`)

| Option | Description |
|--------|-------------|
| **match-class** \<mc-name\> | Assign a Match Class to the Policy |
| **description** | Set the description of the policy |
| apply-groups | To apply the configuration groups |
| apply-groups-exclude | To exclude the configuration groups |

### 3.2 Policy > match-class (actions)

**CLI:** `policy <name> match-class <mc-name>`

| Option | Description (PE-4 `?`) |
|--------|------------------------|
| **action** | Configure the Action to be applied upon match to this match-class |

### 3.3 action sub-options (PE-4 `?`)

| Action | CLI Syntax | Value (PE-4 `?`) | Notes |
|--------|------------|-------------------|-------|
| **rate-limit** | `action rate-limit <kbps>` | `<0, 64-4294967295>` — Set rate-limit (kbps), value 0 means drop | `0` = drop all matched traffic |
| **redirect-to-vrf** | `action redirect-to-vrf <vrf-name>` | `<text>` — Configure the VRF name | Redirect matched traffic to scrubbing VRF |

**Note:** `redirect-to-ip` is NOT supported for flowspec-local-policies.

---

## 4. forwarding-options flowspec-local (attachment)

**CLI:** `configure` → `forwarding-options` → `flowspec-local`

### 4.1 forwarding-options top-level (PE-4 `?`)

| Option | Description |
|--------|-------------|
| **flowspec-local** | Install a Flowspec Local Policy |
| global-access-list | Global Access list attachment |
| igp-frr-scale | Configure hardware optimized fast-reroute logic |
| install-qppb-policy | Install a QPPB Policy |
| ipv4-verify | Configure ipv4 packet verification settings |
| preferred-vlan-ranges | Configure preferred VLAN ranges |
| prefix-set | Configure prefix-set |

### 4.2 flowspec-local (PE-4 `?`)

| Option | Description |
|--------|-------------|
| **ipv4** | Install the ipv4 flowspec-local policy |
| **ipv6** | Install the ipv6 flowspec-local policy |

### 4.3 flowspec-local ipv4 / ipv6 (PE-4 `?`)

| Option | CLI Syntax | Value |
|--------|------------|-------|
| **apply-policy-to-flowspec** | `apply-policy-to-flowspec <policy-name>` | `<text>` — The name of an existing IPv4/IPv6 Policy |

**One policy per AFI.**

### 4.4 Full hierarchy

```
configure
  forwarding-options
    flowspec-local
      ipv4
        apply-policy-to-flowspec <policy-name>
      !
      ipv6
        apply-policy-to-flowspec <policy-name>
      !
    !
  !
!
```

---

## 5. ICMP message types (PE-4 `?`)

All values from `icmp ?` on PE-4:

| ICMP Message | ICMP Message |
|-------------|-------------|
| bad-length | missing-required-option |
| communication-administratively-prohibited | network-administratively-prohibited |
| destination-host-unknown | network-unreachable-for-tos |
| destination-host-unreachable | pointer-indicates-error |
| destination-network-unknown | precedence-cutoff-in-effect |
| destination-network-unreachable | redirect-host |
| destination-port-unreachable | redirect-network |
| destination-protocol-unreachable | redirect-tos-host |
| echo-reply | redirect-tos-network |
| echo-request | router-advertisement |
| fragment-reassembly | router-solicitation |
| fragmentation-required | source-host-isolated |
| host-administratively-prohibited | source-route-failed |
| host-precedence-violation | timestamp |
| host-unreachable-for-tos | timestamp-reply |
| | ttl-expired-in-transit |

---

## 6. TCP flags (PE-4 `?`)

| Flag | Flag |
|------|------|
| syn | psh |
| ack | rst |
| urg | fin |

Format: comma-separated, e.g. `tcp-flag syn,ack`

---

## 7. Protocol map (PE-4 `?` — named protocols)

| Protocol | Hex | Protocol | Hex |
|----------|-----|----------|-----|
| any | - | ipv6(0x29) | 0x29 |
| hopopt(0x00) | 0x00 | ipv6-frag(0x2C) | 0x2C |
| icmp(0x01) | 0x01 | ipv6-icmp(0x3A) | 0x3A |
| igmp(0x02) | 0x02 | ipv6-nonxt(0x3B) | 0x3B |
| ggp(0x03) | 0x03 | ipv6-opts(0x3C) | 0x3C |
| ip-in-ip(0x04) | 0x04 | ipv6-route(0x2B) | 0x2B |
| tcp(0x06) | 0x06 | ipx-in-ip(0x6F) | 0x6F |
| cbt(0x07) | 0x07 | irtp(0x1C) | 0x1C |
| egp(0x08) | 0x08 | is-is-over-ipv4(0x7C) | 0x7C |
| igp(0x09) | 0x09 | iso-ip(0x50) | 0x50 |
| bbn-rcc-mon(0x0A) | 0x0A | iso-tp4(0x1D) | 0x1D |
| nvp-ii(0x0B) | 0x0B | kryptolan(0x41) | 0x41 |
| pup(0x0C) | 0x0C | l2tp(0x73) | 0x73 |
| argus(0x0D) | 0x0D | larp(0x5B) | 0x5B |
| emcon(0x0E) | 0x0E | leaf-1(0x19) | 0x19 |
| xnet(0x0F) | 0x0F | leaf-2(0x1A) | 0x1A |
| chaos(0x10) | 0x10 | manet(0x8A) | 0x8A |
| udp(0x11) | 0x11 | merit-inp(0x20) | 0x20 |
| mux(0x12) | 0x12 | mfe-nsp(0x1F) | 0x1F |
| dcn-meas(0x13) | 0x13 | micp(0x5F) | 0x5F |
| hmp(0x14) | 0x14 | mobile(0x37) | 0x37 |
| prm(0x15) | 0x15 | mobility-header(0x87) | 0x87 |
| xns-idp(0x16) | 0x16 | mpls-in-ip(0x89) | 0x89 |
| trunk-1(0x17) | 0x17 | mtp(0x5C) | 0x5C |
| trunk-2(0x18) | 0x18 | narp(0x36) | 0x36 |
| rdp(0x1B) | 0x1B | netblt(0x1E) | 0x1E |
| dccp(0x21) | 0x21 | nsfnet-igp(0x55) | 0x55 |
| ddp(0x25) | 0x25 | os(0x5E) | 0x5E |
| idpr(0x23) | 0x23 | ospf(0x59) | 0x59 |
| idpr-cmtp(0x26) | 0x26 | pgm(0x71) | 0x71 |
| tp++(0x27) | 0x27 | pim(0x67) | 0x67 |
| il(0x28) | 0x28 | pipe(0x83) | 0x83 |
| sdrp(0x2A) | 0x2A | pnni(0x66) | 0x66 |
| rsvp(0x2E) | 0x2E | ptp(0x7B) | 0x7B |
| gre(0x2F) | 0x2F | pvp(0x4B) | 0x4B |
| idrp(0x2D) | 0x2D | qnx(0x6A) | 0x6A |
| bna(0x31) | 0x31 | rohc(0x8E) | 0x8E |
| esp(0x32) | 0x32 | rsvp-e2e-ignore(0x86) | 0x86 |
| ah(0x33) | 0x33 | rvd(0x42) | 0x42 |
| i-nlsp(0x34) | 0x34 | sat-expak(0x40) | 0x40 |
| swipe(0x35) | 0x35 | sat-mon(0x45) | 0x45 |
| mobile(0x37) | 0x37 | scc-sp(0x60) | 0x60 |
| tlsp(0x38) | 0x38 | scps(0x69) | 0x69 |
| skip(0x39) | 0x39 | sctp(0x84) | 0x84 |
| etherip(0x61) | 0x61 | secure-vmtp(0x52) | 0x52 |
| encap(0x62) | 0x62 | shim6(0x8C) | 0x8C |
| gmtp(0x64) | 0x64 | sm(0x7A) | 0x7A |
| ifmp(0x65) | 0x65 | smp(0x79) | 0x79 |
| aris(0x68) | 0x68 | snp(0x6D) | 0x6D |
| a/n(0x44) | 0x44 | sprite-rpc(0x5A) | 0x5A |
| cftp(0x3E) | 0x3E | sps(0x82) | 0x82 |
| compaq-peer(0x6E) | 0x6E | srp(0x77) | 0x77 |
| cphb(0x3F) | 0x3F | sscopmce(0x80) | 0x80 |
| cpnx(0x48) | 0x48 | stp(0x76) | 0x76 |
| crtp(0x7E) | 0x7E | sun-nd(0x4D) | 0x4D |
| crudp(0x7F) | 0x7F | swipe(0x35) | 0x35 |
| ddx(0x74) | 0x74 | tcf(0x57) | 0x57 |
| dgp(0x56) | 0x56 | ttp/iptm(0x54) | 0x54 |
| eigrp(0x58) | 0x58 | udplite(0x88) | 0x88 |
| fc(0x85) | 0x85 | uti(0x78) | 0x78 |
| fire(0x7D) | 0x7D | vines(0x53) | 0x53 |
| iatp(0x75) | 0x75 | visa(0x46) | 0x46 |
| ipcomp(0x6C) | 0x6C | vmtp(0x51) | 0x51 |
| ipcu(0x47) | 0x47 | vrrp(0x70) | 0x70 |
| iplt(0x81) | 0x81 | wb-expak(0x4F) | 0x4F |
| ippc(0x43) | 0x43 | wb-mon(0x4E) | 0x4E |
| ax.25(0x5D) | 0x5D | wesp(0x8D) | 0x8D |
| br-sat-mon(0x4C) | 0x4C | wsn(0x4A) | 0x4A |
| ipx-in-ip(0x6F) | 0x6F | xtp(0x24) | 0x24 |

### 7.1 Unnamed protocols (hex only, PE-4 `?`)

These appear as raw hex values with no name in the CLI:

`0x05`, `0x8F`–`0x99`, `0xA0`–`0xAF`, `0xB0`–`0xB9`, `0xBA`–`0xBC`, `0xBE`–`0xBF`, `0xC0`–`0xCF`, `0xD0`–`0xDF`, `0xE0`–`0xEF`, `0xF0`–`0xFC`

IANA names for common unnamed ones:
- `0x05` — ST (Stream)
- `0xBD` — (unassigned)
- `0xFD`–`0xFE` — Experimental
- `0xFF` — Reserved

---

## 8. Common protocol suggestions

| Use case | Protocol | CLI value |
|----------|----------|-----------|
| TCP (HTTP, HTTPS, SYN) | TCP | `tcp(0x06)` |
| UDP (DNS, NTP, Memcached) | UDP | `udp(0x11)` |
| ICMP (ping flood) | ICMP | `icmp(0x01)` |
| ICMPv6 | IPv6-ICMP | `ipv6-icmp(0x3A)` |
| GRE tunnels | GRE | `gre(0x2F)` |
| ESP (IPsec) | ESP | `esp(0x32)` |
| OSPF | OSPF | `ospf(0x59)` |
| Any protocol | Any | `any` |

---

## 9. Port suggestions by attack type

| Attack | dest-ports | src-ports | protocol |
|--------|------------|-----------|----------|
| DNS amplification | `53` | `53` | `udp(0x11)` |
| NTP monlist | `123` | `123` | `udp(0x11)` |
| Memcached | `11211` | `11211` | `udp(0x11)` |
| HTTP/HTTPS flood | `80`, `443` or `80-443` | — | `tcp(0x06)` |
| SYN flood | — | — | `tcp(0x06)` + `tcp-flag syn` |
| ICMP flood | — | — | `icmp(0x01)` |
| Fragment attack | — | — | any + `fragmented` |

---

## 10. Complete config example

```
routing-policy
  flowspec-local-policies
    ipv4
      match-class MC-DNS-AMPL
        dest-ip 0.0.0.0/0
        src-ports 53
        protocol udp(0x11)
        description "Drop DNS amplification"
      !
      match-class MC-SYN-FLOOD
        dest-ip 192.168.1.0/24
        protocol tcp(0x06)
        tcp-flag syn
        description "Rate-limit SYN flood"
      !
      match-class MC-VRF-FILTER
        dest-ip 10.0.0.0/8
        vrf CUSTOMER-A
        protocol any
        description "Drop all to CUSTOMER-A VRF"
      !
      policy FLOWSPEC-PROTECTION
        match-class MC-DNS-AMPL
          action rate-limit 0
        !
        match-class MC-SYN-FLOOD
          action rate-limit 10000
        !
        match-class MC-VRF-FILTER
          action redirect-to-vrf SCRUBBING
        !
      !
    !
  !
!

forwarding-options
  flowspec-local
    ipv4
      apply-policy-to-flowspec FLOWSPEC-PROTECTION
    !
  !
!
```

---

## 11. Limits (YANG)

| Resource | IPv4 | IPv6 |
|----------|------|------|
| Match-classes | 8,000 | 4,000 |
| Policies | 20 | 20 |
| Match-classes per policy | 8,000 | 4,000 |
| Policies in forwarding-options | 1 | 1 |
