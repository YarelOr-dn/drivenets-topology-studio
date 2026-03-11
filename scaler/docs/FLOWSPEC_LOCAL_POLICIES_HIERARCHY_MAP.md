# DNOS flowspec-local-policies Hierarchy Map

**Source:** DNOS CLI docs (`dnos_cheetah_docs/Routing-policy/flowspec-local-policies/`), YANG (`dn-flowspec-local-policies.yang`). Device state (GI vs DNOS) is cached in `db/configs/{hostname}/operational.json`; run [R] Refresh in scaler-wizard to re-detect after upgrades.

---

## 1. Hierarchy Structure

```
configure
  routing-policy
    flowspec-local-policies          ← Top level
      ipv4                           ← Address family
      ipv6                           ← Address family
```

---

## 2. flowspec-local-policies (top level)

| Option | Type | Description |
|--------|------|--------------|
| **ipv4** | sub-mode | IPv4 address family (match-classes + policies) |
| **ipv6** | sub-mode | IPv6 address family (match-classes + policies) |

---

## 3. flowspec-local-policies ipv4 / ipv6

| Option | Type | Description |
|--------|------|-------------|
| **match-class** \<name\> | sub-mode | Define a match-class (traffic criteria) |
| **policy** \<name\> | sub-mode | Define a policy (references match-classes + actions) |
| **description** | leaf | Optional description |

---

## 4. flowspec-local-policies ipv4 match-class (match criteria)

| Option | CLI Syntax | Range/Values | Description |
|--------|------------|--------------|-------------|
| **vrf** | `vrf <vrf-name>` | VRF ref | Restrict to traffic from this VRF (SW-182546) |
| **dest-ip** | `dest-ip <prefix>` | A.B.C.D/M | Destination IPv4 prefix (MANDATORY if no source-ip) |
| **source-ip** | `source-ip <prefix>` | A.B.C.D/M | Source IPv4 prefix (MANDATORY if no dest-ip) |
| **dest-ports** | `dest-ports <port>` or `dest-ports <start>-<end>` | 0-65535 | Destination port or range |
| **src-ports** | `src-ports <port>` or `src-ports <start>-<end>` | 0-65535 | Source port or range |
| **protocol** | `protocol <name>(0xNN)` or `protocol any` | See Protocol Map | IP protocol number |
| **dscp** | `dscp <0-63>` | 0-63 | DSCP value (IPv4) |
| **traffic-class** | `traffic-class <0-63>` | 0-63 | Traffic class (IPv6 only) |
| **packet-length** | `packet-length <len>` or `packet-length <min>-<max>` | 0-65535 | Packet length or range |
| **tcp-flag** | `tcp-flag syn,ack,...` | syn, ack, urg, psh, rst, fin | TCP flags (when protocol=TCP) |
| **fragmented** | `fragmented` | presence | Match fragmented packets |
| **icmp** | `icmp <message-type>` | See ICMP Map | ICMP message type (when protocol=ICMP) |
| **description** | `description <text>` | 1-255 chars | Match-class description |

---

## 5. flowspec-local-policies ipv4 policy match-class (actions)

| Option | CLI Syntax | Description |
|--------|------------|-------------|
| **action-type rate-limit** | `action-type rate-limit max-rate <kbps>` | Rate-limit traffic (0 = drop) |
| **action-type redirect-to-vrf** | `action-type redirect-to-vrf <vrf-name>` | Redirect to VRF |
| **action-type redirect-to-vrf-and-rate-limit** | `action-type redirect-to-vrf-and-rate-limit vrf <vrf> max-rate <kbps>` | Redirect + rate-limit |
| **action-type no-action** | `action-type no-action` | Allow (pass through) |

**Note:** `redirect-to-ip` is **NOT supported** in flowspec-local-policies (BGP FlowSpec-VPN rejects it per SW-182545). Use `redirect-to-vrf` instead.

---

## 6. Protocol Map (unnamed protocols named)

| Hex | DNOS Name | Full Name (IANA) |
|-----|-----------|------------------|
| 0x00 | hopopt | IPv6 Hop-by-Hop Option |
| 0x01 | icmp | ICMP |
| 0x02 | igmp | IGMP |
| 0x03 | ggp | Gateway-to-Gateway |
| 0x04 | ip-in-ip | IPv4-in-IPv4 Encapsulation |
| 0x05 | **St** | **Stream** (RFC 1190) |
| 0x06 | tcp | TCP |
| 0x07 | cbt | CBT |
| 0x08 | egp | EGP |
| 0x09 | igp | IGP (any private) |
| 0x0A | bbn-rcc-mon | BBN RCC Monitoring |
| 0x0B | nvp-ii | Network Voice Protocol |
| 0x0C | pup | PUP |
| 0x0D | argus | ARGUS |
| 0x0E | emcon | EMCON |
| 0x0F | xnet | Cross Net Debugger |
| 0x10 | chaos | Chaos |
| 0x11 | udp | UDP |
| 0x12 | mux | Multiplexing |
| 0x13 | dcn-meas | DCN Measurement |
| 0x14 | hmp | Host Monitoring |
| 0x15 | prm | Packet Radio Measurement |
| 0x16 | xns-idp | XNS IDP |
| 0x17 | trunk-1 | Trunk-1 |
| 0x18 | trunk-2 | Trunk-2 |
| 0x19 | leaf-1 | Leaf-1 |
| 0x1A | leaf-2 | Leaf-2 |
| 0x1B | rdp | Reliable Data Protocol |
| 0x1C | irtp | Internet Reliable Transaction |
| 0x1D | iso-tp4 | ISO Transport Class 4 |
| 0x1E | netblt | Bulk Data Transfer |
| 0x1F | mfe-nsp | MFE Network Services |
| 0x20 | merit-inp | MERIT Internodal |
| 0x21 | dccp | DCCP |
| 0x22 | 3pc | Third Party Connect |
| 0x23 | idpr | Inter-Domain Policy Routing |
| 0x24 | xtp | XTP |
| 0x25 | ddp | Datagram Delivery |
| 0x26 | idpr-cmtp | IDPR Control Message |
| 0x27 | tp++ | TP++ Transport Protocol |
| 0x28 | il | IL Transport Protocol |
| 0x29 | ipv6 | IPv6 Encapsulation |
| 0x2A | sdrp | Source Demand Routing |
| 0x2B | ipv6-route | IPv6 Routing Header |
| 0x2C | ipv6-frag | IPv6 Fragment Header |
| 0x2D | idrp | IDRP |
| 0x2E | rsvp | RSVP |
| 0x2F | gre | GRE |
| 0x30 | dsr | Dynamic Source Routing |
| 0x31 | bna | BNA |
| 0x32 | esp | ESP |
| 0x33 | ah | AH |
| 0x34 | i-nlsp | I-NLSP |
| 0x35 | swipe | SWIPE |
| 0x36 | narp | NARP |
| 0x37 | mobile | Mobile |
| 0x38 | tlsp | TLSP |
| 0x39 | skip | SKIP |
| 0x3A | ipv6-icmp | ICMPv6 |
| 0x3B | ipv6-nonxt | IPv6 No Next Header |
| 0x3C | ipv6-opts | IPv6 Destination Options |
| 0x3D | any-host | Any Host Internal |
| 0x3E | cftp | CFTP |
| 0x3F | any-local-network | Any Local Network |
| 0x40 | sat-expak | SATNET and Backroom EXPAK |
| 0x41 | kryptolan | Kryptolan |
| 0x42 | rvd | MIT RVD |
| 0x43 | ippc | Internet Pluribus Packet Core |
| 0x44 | any-dist-file-sys | Any Distributed File System |
| 0x45 | sat-mon | SATNET Monitoring |
| 0x46 | visa | VISA Protocol |
| 0x47 | ipcu | IPCU |
| 0x48 | cpnx | CPNX |
| 0x49 | cphb | CPHB |
| 0x4A | wsn | Wang Span Network |
| 0x4B | pvp | Packet Video Protocol |
| 0x4C | br-sat-mon | Backroom SATNET Monitoring |
| 0x4D | sun-nd | SUN ND PROTOCOL-Temporary |
| 0x4E | wb-mon | WB Monitoring |
| 0x4F | wb-expak | WB EXPAK |
| 0x50 | iso-ip | ISO IP |
| 0x51 | vmtp | VMTP |
| 0x52 | secure-vmtp | Secure VMTP |
| 0x53 | vines | VINES |
| 0x54 | ttp/iptm | TTP |
| 0x55 | nsfnet-igp | NSFNET-IGP |
| 0x56 | dgp | DGP |
| 0x57 | tcf | TCF |
| 0x58 | eigrp | EIGRP |
| 0x59 | ospf | OSPF |
| 0x5A | sprite-rpc | Sprite RPC |
| 0x5B | larp | LARP |
| 0x5C | mtp | MTP |
| 0x5D | ax.25 | AX.25 |
| 0x5E | os | IPIP (OS) |
| 0x5F | micp | MICP |
| 0x60 | scc-sp | SCC-SP |
| 0x61 | etherip | Ethernet-in-IPv4 |
| 0x62 | encap | Encapsulation |
| 0x63 | any-private-encrypt-scheme | Any Private Encryption |
| 0x64 | gmtp | GMTP |
| 0x65 | ifmp | IFMP |
| 0x66 | pnni | PNNI over IP |
| 0x67 | pim | PIM |
| 0x68 | aris | ARIS |
| 0x69 | scps | SCPS |
| 0x6A | qnx | QNX |
| 0x6B | a/n | Active Networks |
| 0x6C | ipcomp | IP Payload Compression |
| 0x6D | snp | SNP |
| 0x6E | compaq-peer | Compaq Peer |
| 0x6F | ipx-in-ip | IPX in IP |
| 0x70 | vrrp | VRRP |
| 0x71 | pgm | PGM |
| 0x72 | any-0-hop-protocol | Any 0-Hop Protocol |
| 0x73 | l2tp | L2TP |
| 0x74 | ddx | DDX |
| 0x75 | iatp | IATP |
| 0x76 | stp | STP |
| 0x77 | srp | SRP |
| 0x78 | uti | UTI |
| 0x79 | smp | SMP |
| 0x7A | sm | SM |
| 0x7B | ptp | PTP |
| 0x7C | is-is-over-ipv4 | ISIS over IPv4 |
| 0x7D | fire | FIRE |
| 0x7E | crtp | CRTP |
| 0x7F | crudp | CRUDP |
| 0x80 | sscopmce | SSCOPMCE |
| 0x81 | iplt | IPLT |
| 0x82 | sps | SPS |
| 0x83 | pipe | PIPE |
| 0x84 | sctp | SCTP |
| 0x85 | fc | FC |
| 0x86 | rsvp-e2e-ignore | RSVP-E2E-IGNORE |
| 0x87 | mobility-header | Mobility Header |
| 0x88 | udplite | UDPLite |
| 0x89 | mpls-in-ip | MPLS-in-IP |
| 0x8A | manet | MANET |
| 0x8B | hip | HIP |
| 0x8C | shim6 | Shim6 |
| 0x8D | wesp | WESP |
| 0x8E | rohc | ROHC |
| 0x8F–0xFF | 0x8F … 0xFF | Unnamed (use hex) |
| - | **any** | Match any protocol |

---

## 7. ICMP Message Types (IPv4)

| DNOS Name | Type | Description |
|-----------|------|-------------|
| echo-reply | 0 | Echo Reply |
| destination-network-unreachable | 3 | Dest Network Unreachable |
| destination-host-unreachable | 1 | Dest Host Unreachable |
| destination-protocol-unreachable | 2 | Dest Protocol Unreachable |
| destination-port-unreachable | 3 | Dest Port Unreachable |
| fragmentation-required | 4 | Fragmentation Required |
| source-route-failed | 5 | Source Route Failed |
| destination-network-unknown | 6 | Dest Network Unknown |
| destination-host-unknown | 7 | Dest Host Unknown |
| source-host-isolated | 8 | Source Host Isolated |
| network-administratively-prohibited | 9 | Network Admin Prohibited |
| host-administratively-prohibited | 10 | Host Admin Prohibited |
| network-unreachable-for-tos | 11 | Network Unreachable for TOS |
| host-unreachable-for-tos | 12 | Host Unreachable for TOS |
| communication-administratively-prohibited | 13 | Communication Admin Prohibited |
| host-precedence-violation | 14 | Host Precedence Violation |
| precedence-cutoff-in-effect | 15 | Precedence Cutoff |
| redirect-network | 5 | Redirect Network |
| redirect-host | 5 | Redirect Host |
| redirect-tos-network | 5 | Redirect TOS Network |
| redirect-tos-host | 5 | Redirect TOS Host |
| echo-request | 8 | Echo Request |
| router-advertisement | 9 | Router Advertisement |
| router-solicitation | 10 | Router Solicitation |
| ttl-expired-in-transit | 11 | TTL Exceeded |
| fragment-reassembly | 12 | Fragment Reassembly Time Exceeded |
| pointer-indicates-error | 12 | Parameter Problem |
| missing-required-option | 12 | Parameter Problem |
| bad-length | 12 | Parameter Problem |
| timestamp | 13 | Timestamp Request |
| timestamp-reply | 14 | Timestamp Reply |

---

## 8. Apply Policy (forwarding-options)

Policy is applied under a **separate hierarchy**:

```
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
```

---

## 9. Limits (from YANG)

| Resource | IPv4 | IPv6 |
|----------|------|------|
| Match-classes | 8,000 | 4,000 |
| Policies | 20 | 20 |
| Match-classes per policy | 8,000 | 4,000 |
| Policies in forwarding-options | 1 | 1 |
