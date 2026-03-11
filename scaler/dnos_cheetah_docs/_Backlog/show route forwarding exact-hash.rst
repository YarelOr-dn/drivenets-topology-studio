show route forwarding exact-hash - supported in v11.1
-----------------------------------------------------

**Command syntax: show route forwarding exact-hash** ingress-if [interface-name] vrf [vrf-name] **[ipv4 \| ipv6] src-ip [ip-address] dest-ip [ip-address]** dscp [dscp] **ip-proto [{udp \| tcp} {src-port [port] dest-port [port]} \| host-any]** ncp [ncp-id] detail

**Description:** show route load-balancing hash result for an incoming packet flow with specified attributes.

Information about up to two ECMP levels, Class Based Tunnel Selection (CBTS), and Link Aggregation (LAG) is displayed in detail view. The command does not consider ACL filtering, RPF filtering and similar.

ingress-if - ingress interface.

vrf - virtul routing and forwarding instance name.

src-ip - source ip address.

dest-ip - destination ip address.

dscp - ip dscp value.

ip-proto - ip protocol.

src-port - udp/tcp source port number.

dest-port - udp/tcp destination port number.

ncp - display information from a specific ncp.

detail - display detailed hashing information.

next hop type:

connected - directly connected next hop.

local - routes designated to NCC (punted).

discard - discarded routes due to NCC ruling.

**CLI example:**
::

	
	dnRouter#show route forwarding exact-hash ipv4 src-ip 1.1.1.1 dest-ip 2.2.2.2  ip-proto any-host 
	
	interface: ge100-2/0/3 (1 of 4 in bundle-1)
	next-hop: connected
	mpls labels: N/A
	
	
	dnRouter#show route forwarding exact-hash vrf customer1 ipv4 src-ip 10.1.1.1 dest-ip 10.2.2.2 ip-proto any-host detail
	
	NCP-ID: 1
	next-hop: 4.4.4.4 (1 of 2)
	mpls labels: 1001
	tunnel: tunnel_8
	hash: 0xDF34
	   next-hop: 3.3.3.3 (1 of 2)
	   mpls labels:  8156, 4332
	   tunnel_18 via bypass_18  
	   hash: 0x3221
	     next-hop: 40.0.0.1 (1 of 2)
	     interface: bundle-3
	     interface: ge100-2/0/3 (1 of 4)
	     hash: 0x7358
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

-  Support 3-tuple IP flows over host-any(61) ip protocol and 5-tuple IP flows over udp or tcp.

-  Support unicast flows only. No support for hash resolution of multicast flows.

-  By default, if a physical ingress interface is specified, the ncp with this interface is queried. If a bundle ingress interface is specified, the ncp with the first physical interface is selected, otherwise, the active ncp with the lowest ID is queried.

**Help line:** show mpls load-balancing hash result

**Parameter table:**

+----------------+------------------------------------+------------------------+
| Parameter      | Values                             | Default value          |
+================+====================================+========================+
| Interface-name | configured interface name.         |                        |
|                |                                    |                        |
|                | ge{/10/25/40/100}-X/Y/Z            |                        |
|                |                                    |                        |
|                | geX-<f>/<n>/<p>.<sub-interface id> |                        |
|                |                                    |                        |
|                | bundle-<bundle-id>                 |                        |
|                |                                    |                        |
|                | bundle-<bundle-id.sub-bundle-id>   |                        |
+----------------+------------------------------------+------------------------+
| vrf-name       | string                             | Default                |
+----------------+------------------------------------+------------------------+
| Ip-address     | IPv4/IPv6 address format           |                        |
+----------------+------------------------------------+------------------------+
| dscp           | 0..63                              | 0                      |
+----------------+------------------------------------+------------------------+
| ncp-id         | 0..255                             | NCP with the lowest ID |
+----------------+------------------------------------+------------------------+
