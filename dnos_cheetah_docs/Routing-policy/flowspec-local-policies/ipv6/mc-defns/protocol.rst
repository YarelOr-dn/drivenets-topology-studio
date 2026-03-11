routing-policy flowspec-local-policies ipv6 match-class protocol
----------------------------------------------------------------

**Minimum user role:** operator

Configures the protocol as a match criteria of this match class. For the match to be made. all criteria must match.

**Command syntax: protocol [protocol]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6 match-class

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------------------------------------+---------+
| Parameter | Description                                                                      | Range                                | Default |
+===========+==================================================================================+======================================+=========+
| protocol  | Protocol that is passed on top of Network layer (i.e. on top of IPv4/IPv6        | | hopopt(0x00)                       | \-      |
|           | header)                                                                          | | icmp(0x01)                         |         |
|           |                                                                                  | | igmp(0x02)                         |         |
|           |                                                                                  | | ggp(0x03)                          |         |
|           |                                                                                  | | ip-in-ip(0x04)                     |         |
|           |                                                                                  | | St(0x05)                           |         |
|           |                                                                                  | | tcp(0x06)                          |         |
|           |                                                                                  | | cbt(0x07)                          |         |
|           |                                                                                  | | egp(0x08)                          |         |
|           |                                                                                  | | igp(0x09)                          |         |
|           |                                                                                  | | bbn-rcc-mon(0x0A)                  |         |
|           |                                                                                  | | nvp-ii(0x0B)                       |         |
|           |                                                                                  | | pup(0x0C)                          |         |
|           |                                                                                  | | argus(0x0D)                        |         |
|           |                                                                                  | | emcon(0x0E)                        |         |
|           |                                                                                  | | xnet(0x0F)                         |         |
|           |                                                                                  | | chaos(0x10)                        |         |
|           |                                                                                  | | udp(0x11)                          |         |
|           |                                                                                  | | mux(0x12)                          |         |
|           |                                                                                  | | dcn-meas(0x13)                     |         |
|           |                                                                                  | | hmp(0x14)                          |         |
|           |                                                                                  | | prm(0x15)                          |         |
|           |                                                                                  | | xns-idp(0x16)                      |         |
|           |                                                                                  | | trunk-1(0x17)                      |         |
|           |                                                                                  | | trunk-2(0x18)                      |         |
|           |                                                                                  | | leaf-1(0x19)                       |         |
|           |                                                                                  | | leaf-2(0x1A)                       |         |
|           |                                                                                  | | rdp(0x1B)                          |         |
|           |                                                                                  | | irtp(0x1C)                         |         |
|           |                                                                                  | | iso-tp4(0x1D)                      |         |
|           |                                                                                  | | netblt(0x1E)                       |         |
|           |                                                                                  | | mfe-nsp(0x1F)                      |         |
|           |                                                                                  | | merit-inp(0x20)                    |         |
|           |                                                                                  | | dccp(0x21)                         |         |
|           |                                                                                  | | 3pc(0x22)                          |         |
|           |                                                                                  | | idpr(0x23)                         |         |
|           |                                                                                  | | xtp(0x24)                          |         |
|           |                                                                                  | | ddp(0x25)                          |         |
|           |                                                                                  | | idpr-cmtp(0x26)                    |         |
|           |                                                                                  | | tp++(0x27)                         |         |
|           |                                                                                  | | il(0x28)                           |         |
|           |                                                                                  | | ipv6(0x29)                         |         |
|           |                                                                                  | | sdrp(0x2A)                         |         |
|           |                                                                                  | | ipv6-route(0x2B)                   |         |
|           |                                                                                  | | ipv6-frag(0x2C)                    |         |
|           |                                                                                  | | idrp(0x2D)                         |         |
|           |                                                                                  | | rsvp(0x2E)                         |         |
|           |                                                                                  | | gre(0x2F)                          |         |
|           |                                                                                  | | dsr(0x30)                          |         |
|           |                                                                                  | | bna(0x31)                          |         |
|           |                                                                                  | | esp(0x32)                          |         |
|           |                                                                                  | | ah(0x33)                           |         |
|           |                                                                                  | | i-nlsp(0x34)                       |         |
|           |                                                                                  | | swipe(0x35)                        |         |
|           |                                                                                  | | narp(0x36)                         |         |
|           |                                                                                  | | mobile(0x37)                       |         |
|           |                                                                                  | | tlsp(0x38)                         |         |
|           |                                                                                  | | skip(0x39)                         |         |
|           |                                                                                  | | ipv6-icmp(0x3A)                    |         |
|           |                                                                                  | | ipv6-nonxt(0x3B)                   |         |
|           |                                                                                  | | ipv6-opts(0x3C)                    |         |
|           |                                                                                  | | any-host(0x3D)                     |         |
|           |                                                                                  | | cftp(0x3E)                         |         |
|           |                                                                                  | | any-local-network(0x3F)            |         |
|           |                                                                                  | | sat-expak(0x40)                    |         |
|           |                                                                                  | | kryptolan(0x41)                    |         |
|           |                                                                                  | | rvd(0x42)                          |         |
|           |                                                                                  | | ippc(0x43)                         |         |
|           |                                                                                  | | any-dist-file-sys(0x44)            |         |
|           |                                                                                  | | sat-mon(0x45)                      |         |
|           |                                                                                  | | visa(0x46)                         |         |
|           |                                                                                  | | ipcu(0x47)                         |         |
|           |                                                                                  | | cpnx(0x48)                         |         |
|           |                                                                                  | | cphb(0x49)                         |         |
|           |                                                                                  | | wsn(0x4A)                          |         |
|           |                                                                                  | | pvp(0x4B)                          |         |
|           |                                                                                  | | br-sat-mon(0x4C)                   |         |
|           |                                                                                  | | sun-nd(0x4D)                       |         |
|           |                                                                                  | | wb-mon(0x4E)                       |         |
|           |                                                                                  | | wb-expak(0x4F)                     |         |
|           |                                                                                  | | iso-ip(0x50)                       |         |
|           |                                                                                  | | vmtp(0x51)                         |         |
|           |                                                                                  | | secure-vmtp(0x52)                  |         |
|           |                                                                                  | | vines(0x53)                        |         |
|           |                                                                                  | | ttp/iptm(0x54)                     |         |
|           |                                                                                  | | nsfnet-igp(0x55)                   |         |
|           |                                                                                  | | dgp(0x56)                          |         |
|           |                                                                                  | | tcf(0x57)                          |         |
|           |                                                                                  | | eigrp(0x58)                        |         |
|           |                                                                                  | | ospf(0x59)                         |         |
|           |                                                                                  | | sprite-rpc(0x5A)                   |         |
|           |                                                                                  | | larp(0x5B)                         |         |
|           |                                                                                  | | mtp(0x5C)                          |         |
|           |                                                                                  | | ax.25(0x5D)                        |         |
|           |                                                                                  | | os(0x5E)                           |         |
|           |                                                                                  | | micp(0x5F)                         |         |
|           |                                                                                  | | scc-sp(0x60)                       |         |
|           |                                                                                  | | etherip(0x61)                      |         |
|           |                                                                                  | | encap(0x62)                        |         |
|           |                                                                                  | | any-private-encrypt-scheme(0x63)   |         |
|           |                                                                                  | | gmtp(0x64)                         |         |
|           |                                                                                  | | ifmp(0x65)                         |         |
|           |                                                                                  | | pnni(0x66)                         |         |
|           |                                                                                  | | pim(0x67)                          |         |
|           |                                                                                  | | aris(0x68)                         |         |
|           |                                                                                  | | scps(0x69)                         |         |
|           |                                                                                  | | qnx(0x6A)                          |         |
|           |                                                                                  | | a/n(0x6B)                          |         |
|           |                                                                                  | | ipcomp(0x6C)                       |         |
|           |                                                                                  | | snp(0x6D)                          |         |
|           |                                                                                  | | compaq-peer(0x6E)                  |         |
|           |                                                                                  | | ipx-in-ip(0x6F)                    |         |
|           |                                                                                  | | vrrp(0x70)                         |         |
|           |                                                                                  | | pgm(0x71)                          |         |
|           |                                                                                  | | any-0-hop-protocol(0x72)           |         |
|           |                                                                                  | | l2tp(0x73)                         |         |
|           |                                                                                  | | ddx(0x74)                          |         |
|           |                                                                                  | | iatp(0x75)                         |         |
|           |                                                                                  | | stp(0x76)                          |         |
|           |                                                                                  | | srp(0x77)                          |         |
|           |                                                                                  | | uti(0x78)                          |         |
|           |                                                                                  | | smp(0x79)                          |         |
|           |                                                                                  | | sm(0x7A)                           |         |
|           |                                                                                  | | ptp(0x7B)                          |         |
|           |                                                                                  | | is-is-over-ipv4(0x7C)              |         |
|           |                                                                                  | | fire(0x7D)                         |         |
|           |                                                                                  | | crtp(0x7E)                         |         |
|           |                                                                                  | | crudp(0x7F)                        |         |
|           |                                                                                  | | sscopmce(0x80)                     |         |
|           |                                                                                  | | iplt(0x81)                         |         |
|           |                                                                                  | | sps(0x82)                          |         |
|           |                                                                                  | | pipe(0x83)                         |         |
|           |                                                                                  | | sctp(0x84)                         |         |
|           |                                                                                  | | fc(0x85)                           |         |
|           |                                                                                  | | rsvp-e2e-ignore(0x86)              |         |
|           |                                                                                  | | mobility-header(0x87)              |         |
|           |                                                                                  | | udplite(0x88)                      |         |
|           |                                                                                  | | mpls-in-ip(0x89)                   |         |
|           |                                                                                  | | manet(0x8A)                        |         |
|           |                                                                                  | | hip(0x8B)                          |         |
|           |                                                                                  | | shim6(0x8C)                        |         |
|           |                                                                                  | | wesp(0x8D)                         |         |
|           |                                                                                  | | rohc(0x8E)                         |         |
|           |                                                                                  | | 0x8F                               |         |
|           |                                                                                  | | 0x90                               |         |
|           |                                                                                  | | 0x91                               |         |
|           |                                                                                  | | 0x92                               |         |
|           |                                                                                  | | 0x93                               |         |
|           |                                                                                  | | 0x94                               |         |
|           |                                                                                  | | 0x95                               |         |
|           |                                                                                  | | 0x96                               |         |
|           |                                                                                  | | 0x97                               |         |
|           |                                                                                  | | 0x98                               |         |
|           |                                                                                  | | 0x99                               |         |
|           |                                                                                  | | 0xA0                               |         |
|           |                                                                                  | | 0xA1                               |         |
|           |                                                                                  | | 0xA2                               |         |
|           |                                                                                  | | 0xA3                               |         |
|           |                                                                                  | | 0xA4                               |         |
|           |                                                                                  | | 0xA5                               |         |
|           |                                                                                  | | 0xA6                               |         |
|           |                                                                                  | | 0xA7                               |         |
|           |                                                                                  | | 0xA8                               |         |
|           |                                                                                  | | 0xA9                               |         |
|           |                                                                                  | | 0xAA                               |         |
|           |                                                                                  | | 0xAB                               |         |
|           |                                                                                  | | 0xAC                               |         |
|           |                                                                                  | | 0xAD                               |         |
|           |                                                                                  | | 0xAE                               |         |
|           |                                                                                  | | 0xAF                               |         |
|           |                                                                                  | | 0xB0                               |         |
|           |                                                                                  | | 0xB1                               |         |
|           |                                                                                  | | 0xB2                               |         |
|           |                                                                                  | | 0xB3                               |         |
|           |                                                                                  | | 0xB4                               |         |
|           |                                                                                  | | 0xB5                               |         |
|           |                                                                                  | | 0xB6                               |         |
|           |                                                                                  | | 0xB7                               |         |
|           |                                                                                  | | 0xB8                               |         |
|           |                                                                                  | | 0xB9                               |         |
|           |                                                                                  | | 0xBA                               |         |
|           |                                                                                  | | 0xBB                               |         |
|           |                                                                                  | | 0xBC                               |         |
|           |                                                                                  | | 0xBE                               |         |
|           |                                                                                  | | 0xBF                               |         |
|           |                                                                                  | | 0xC0                               |         |
|           |                                                                                  | | 0xC1                               |         |
|           |                                                                                  | | 0xC2                               |         |
|           |                                                                                  | | 0xC3                               |         |
|           |                                                                                  | | 0xC4                               |         |
|           |                                                                                  | | 0xC5                               |         |
|           |                                                                                  | | 0xC6                               |         |
|           |                                                                                  | | 0xC7                               |         |
|           |                                                                                  | | 0xC8                               |         |
|           |                                                                                  | | 0xC9                               |         |
|           |                                                                                  | | 0xCA                               |         |
|           |                                                                                  | | 0xCB                               |         |
|           |                                                                                  | | 0xCC                               |         |
|           |                                                                                  | | 0xCD                               |         |
|           |                                                                                  | | 0xCE                               |         |
|           |                                                                                  | | 0xCF                               |         |
|           |                                                                                  | | 0xD0                               |         |
|           |                                                                                  | | 0xD1                               |         |
|           |                                                                                  | | 0xD2                               |         |
|           |                                                                                  | | 0xD3                               |         |
|           |                                                                                  | | 0xD4                               |         |
|           |                                                                                  | | 0xD5                               |         |
|           |                                                                                  | | 0xD6                               |         |
|           |                                                                                  | | 0xD7                               |         |
|           |                                                                                  | | 0xD8                               |         |
|           |                                                                                  | | 0xD9                               |         |
|           |                                                                                  | | 0xDA                               |         |
|           |                                                                                  | | 0xDB                               |         |
|           |                                                                                  | | 0xDC                               |         |
|           |                                                                                  | | 0xDD                               |         |
|           |                                                                                  | | 0xDE                               |         |
|           |                                                                                  | | 0xDF                               |         |
|           |                                                                                  | | 0xE0                               |         |
|           |                                                                                  | | 0xE1                               |         |
|           |                                                                                  | | 0xE2                               |         |
|           |                                                                                  | | 0xE3                               |         |
|           |                                                                                  | | 0xE4                               |         |
|           |                                                                                  | | 0xE5                               |         |
|           |                                                                                  | | 0xE6                               |         |
|           |                                                                                  | | 0xE7                               |         |
|           |                                                                                  | | 0xE8                               |         |
|           |                                                                                  | | 0xE9                               |         |
|           |                                                                                  | | 0xEA                               |         |
|           |                                                                                  | | 0xEB                               |         |
|           |                                                                                  | | 0xEC                               |         |
|           |                                                                                  | | 0xED                               |         |
|           |                                                                                  | | 0xEE                               |         |
|           |                                                                                  | | 0xEF                               |         |
|           |                                                                                  | | 0xF0                               |         |
|           |                                                                                  | | 0xF1                               |         |
|           |                                                                                  | | 0xF2                               |         |
|           |                                                                                  | | 0xF3                               |         |
|           |                                                                                  | | 0xF4                               |         |
|           |                                                                                  | | 0xF5                               |         |
|           |                                                                                  | | 0xF6                               |         |
|           |                                                                                  | | 0xF7                               |         |
|           |                                                                                  | | 0xF8                               |         |
|           |                                                                                  | | 0xF9                               |         |
|           |                                                                                  | | 0xFA                               |         |
|           |                                                                                  | | 0xFB                               |         |
|           |                                                                                  | | 0xFC                               |         |
|           |                                                                                  | | 0xFD                               |         |
|           |                                                                                  | | 0xFE                               |         |
|           |                                                                                  | | 0xFF                               |         |
|           |                                                                                  | | any                                |         |
+-----------+----------------------------------------------------------------------------------+--------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# match-class mc-1
    dnRouter(cfg-flp-ipv6-mc)# protocol tcp(0x06)
    dnRouter(cfg-flp-ipv6-mc)#


**Removing Configuration**

To remove the protocol from the match class:
::

    dnRouter(cfg-flp-ipv6-mc)# no protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
