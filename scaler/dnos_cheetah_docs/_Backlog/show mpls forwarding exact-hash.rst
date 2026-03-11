show mpls forwarding exact-hash - supported in v11.1
----------------------------------------------------

**Command syntax: show mpls forwarding exact-hash** ingress-if [interface-name] **{labels [label]**, [label], .  **}** exp [exp] **payload [ipv4 \| ipv6] src-ip [ip-address] dest-ip [ip-address]** dscp [dscp] **ip-proto [{udp \| tcp} {src-port [port] dest-port [port]} \| host-any]** ncp [ncp-id] detail

**Description:** show mpls load-balancing hash result for an incoming packet flow with specified attributes.

Information about up to two ECMP levels, Class Based Tunnel Selection (CBTS), and Link Aggregation (LAG) is displayed in detail view. The command does not consider ACL filtering, RPF filtering and similar.

ingress-if - ingress interface.

labels - list of all (terminated and non-terminated labels) incoming labels. First label to the left is the outermost (top) label on the label stack.

exp - value of the MPLS EXP bits. The same value is used across the label stack.

payload - mpls payload.

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

	
	dnRouter# show mpls forwarding exact-hash labels 6612, 433 exp 3 payload ipv4 src-ip 10.1.1.123 dest-ip 10.1.2.133 dscp 3 ip-proto udp src-port 2040 dest-port 808 detail 
	
	NCP-ID: 3
	Hash information:
	next-hop: 2.2.2.2 (1 of 2)
	mpls labels: 1001
	tunnel: tunnel_1
	hash: 0xDF34
	   te-class 5 carries cos 3 (1 of 2)
	      next-hop: 13.0.1.1 (1 of 4)
	      mpls labels: 100
	      interface: bundle-3
	      hash: 0x6672
	         interface:  ge100-2/0/3 (1 of 4)
	         hash: 0x0672D
	
	
	dnRouter# show mpls forwarding exact-hash labels 6612, 433 exp 3 payload ipv4 src-address 10.1.1.123 dest-ip 10.1.2.133 dscp 3 ip-proto udp src-port 2040 dest-port 808  
	
	interface: ge100-2/0/3 (1 of 4 in bundle-3)
	next-hop: 13.0.1.1
	mpls labels: 100, 1001
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

-  Support 3-tuple IP flows over host-any(61) ip protocol and 5-tuple IP flows over udp or tcp.

-  Support up to 7 mpls labels.

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
| label          | 0..1048575                         |                        |
+----------------+------------------------------------+------------------------+
| exp            | 0..7                               | 0                      |
+----------------+------------------------------------+------------------------+
| Ip-address     | IPv4/IPv6 address format           |                        |
+----------------+------------------------------------+------------------------+
| dscp           | 0..63                              | 0                      |
+----------------+------------------------------------+------------------------+
| ncp-id         | 0..255                             | NCP with the lowest ID |
+----------------+------------------------------------+------------------------+
