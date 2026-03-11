show route forwarding-table
---------------------------

**Minimum user role:** viewer

To display the forwarding table, use the following command:

**Command syntax: show route forwarding-table** {vrf [vrf-name] | all} {ipv4 \| ipv6 \| ipv4 [ipv4-prefix] \| ipv6 [ipv6-prefix]} ncp [ncp-id]

**Command mode:** operational

..
	**Internal Note**

	- By default, the command output includes ipv4 & ipv6 forwarding-table.

	- By default, the information will be sent from the active NCP with the lowest ID.

	- Brief view display is order by prefix numeric value from lowest to highest

	- MPLS Colum display the pushed mpls label for the route.

	- Support up to 7 mpls labels.

	- First label to the left is the outermost (top) label on the label stack the information will be sent from the first configured active forwarder id.

	- Technical limitations:

	- On large scale routing tables, the table might not be presented ordered

	- When there are routing table updates while presenting the table, the table might contain duplicate entries and might not contain all entries.

**Parameter table**

+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|  Parameter  |                                                                                  Description                                                                                 |
+=============+==============================================================================================================================================================================+
| ipv4        | Displays only IPv4 forwarding table                                                                                                                                          |
+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ipv6        | Displays only IPv6 forwarding table                                                                                                                                          |
+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ipv4-prefix | Displays the forwarding table for the specified IPv4 prefix (displays IPv4 route table)                                                                                      |
+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ipv6-prefix | Displays the forwarding table for the specified IPv6 prefix (displays IPv6 route table)                                                                                      |
+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| vrf-name    | Displays the forwarding table for the specified VRF. If not specified, the global VRF forwarding table is displayed. If All is specified, all configured VRFs are displayed  |
+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ncp-id      | Displays information from a specific NCP. By default, information is sent from the active NCP with the lowest ID                                                             |
+-------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

The following information is displayed on each route:

+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------+
| Attribute | Description                                                                                                                                           |
+===========+=======================================================================================================================================================+
| Type      | The type of route:                                                                                                                                    |
|           | Connected - connected routes                                                                                                                          |
|           | Local - routes designated to NCC (punted)                                                                                                             |
|           | Discard - discarded routes due to NCC ruling                                                                                                          |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------+
| IP-prefix | The prefix of the route                                                                                                                               |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------+
| Next Hop  | The next hop (IP or tunnel)                                                                                                                           |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------+
| Interface | The interface of the route                                                                                                                            |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------+
| MPLS      | The pushed MPLS label for the route. Up to 7 MPLS labels are supported. The leftmost label displayed is the outermost (top) label on the label stack. |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show route forwarding-table

	Legend: * - Active, A - Alternate path, B - Bypass, S - Secondary, EA - Enhanced-Alternate
	labels are arranged from top (left) to BoS (right), E - Entropy Label

	VRF: default
	NCP-ID: 0
	IPv4 Forwarding Table:
	| IP Prefix           | Next Hop  | Interface        | MPLS                    | RSVP Tunnel name |
	+---------------------+-----------+------------------+-------------------------+------------------+
	| (*)1.1.3.0/31       | 1.3.16.0  | bundle-100.1004  |                         |                  |
	| (*)1.1.6.0/31       | 1.6.16.0  | bundle-1002      |                         |                  |
	| (*)1.1.17.0/31      | 1.16.17.1 | bundle-1550.3856 |                         |                  |
	| (*)1.1.210.0/31     | 1.3.16.0  | bundle-100.1004  |                         |                  |
	| (*)1.6.16.1/31      | connected | bundle-1002      |                         |                  |
	| (*)1.6.16.0/32      | connected | bundle-1002      |                         |                  |
	| (*)1.6.16.1/32      | local     |                  |                         |                  |
	| (*)1.8.16.1/31      | connected | bundle-2002      |                         |                  |
	| (*)1.8.16.0/32      | connected | bundle-2002      |                         |                  |
	| (*)1.8.16.1/32      | local     |                  |                         |                  |
	| (*)1.16.209.0/24    | 1.3.16.0  | bundle-100.1004  |                         |                  |
	| (*)101.10.1.100/32  | 1.3.16.0  | bundle-100.1004  | 77402                   |                  |
	| (*)                 | 1.3.16.0  | bundle-100.1004  | 77363                   |                  |
	| (A)                 | 1.4.64.1  | bundle-200       | 3,377,555               | Tunnel_A         |
	| (*)101.10.1.103/32  | 1.3.16.0  | bundle-100.1004  | 77361                   | Tunnel_1         |
	| (*)                 | 1.3.16.0  | bundle-100.1004  | 77375                   | Tunnel_2         |
	| (*)                 | 1.3.16.0  | bundle-100.1004  | 77333                   | Tunnel_3         |
	|   (B)               | 1.4.64.1  | bundle-200       | 7,733,371,348           | Tunnel_bypass    |
	| (*)101.10.1.104/32  | 1.3.16.0  | bundle-100.1004  | 77461                   | Tunnel_4         |
	|  (S)                | 1.4.64.1  | bundle-200       | 7,733,371,348           | Tunnel_4         |
	| (*)99.99.99.99/32   | discard   | Null0            |                         |                  |

	IPv6 Forwarding Table:
	| IP Prefix            | Next Hop     | Interface | MPLS                       | RSVP Tunnel name |
	+----------------------+--------------+-----------+----------------------------+------------------+
	| (*)2001:1235::0/122  | 2001:1235::1 | bundle-3  | 100                        |                  |
	| (*)                  | 2001:1111::2 | bundle-3  | 300                        |                  |
	| (*)2001:1111::1/128  | local        |           |                            |                  |
	| (*)2001:4444::0/128  | discard      | Null0     |                            |                  |
	| (*)2003:3221::0/122  | 2003:3221::1 | bundle-5  |                            |                  |



	dnRouter# show route forwarding-table ipv6 ncp 2

	Legend: * - Active, A - Alternate path, B - Bypass, S - Secondary, EA - Enhanced-Alternate
	labels are arranged from top (left) to BoS (right), E - Entropy Label

	VRF: default
	NCP-ID: 2
	IPv6 Forwarding Table:
	| IP Prefix             | Next Hop     | Interface | MPLS                       | RSVP Tunnel name |
	+-----------------------+--------------+-----------+----------------------------+------------------+
	| (*)2001:1235::0/122   | 2001:1235::1 | bundle-3  | 100                        |                  |
	| (*)                   | 2001:1111::2 | bundle-3  | 300                        |                  |
	| (*)2001:1111::1/128   | local        |           |                            |                  |
	| (*)2003:3221::0/122   | 2003:3221::1 | bundle-5  |                            |                  |


	dnRouter# show route forwarding-table ipv4
	dnRouter# show route forwarding-table vrf default ipv4
	dnRouter# show route forwarding-table ipv6

	dnRouter# show route forwarding-table vrf MyVrf_1 ipv4 1.6.16.1/31
	VRF: MyVrf_1
	IPv4 Forwarding Table:
	Destination: 90.1.1.0/24
	    next-hop: connected
	    Interface: bundle-1002

	dnRouter# show route forwarding-table ipv4 90.1.1.0/24
	VRF: default
	IPv4 Forwarding Table:
	Destination: 90.1.1.0/24
	    next-hop(1): 2.2.2.2, Active
	    Interface: bundle-2
	    next-hop(2): 4.4.4.4, Active
	    interface: bundle-4
	    Alternate-path:
	      next-hop: 3.3.3.3 Recursive
	        next-hop(3,1): 13.0.1.1
	        mpls labels: 8156(top)
	        interface: bundle-3
	        via tunnel_1
	        Bypass:
	          next-hop: 13.0.2.1
	          mpls labels: 74413(top),8245
	          Interface: bundle-2
	          via bypass_1
	      next-hop(3,2): 13.0.1.1
	      mpls labels: 87441
	      interface: bundle-3
	      via tunnel_2
	      Bypass:
			next-hop: 13.0.2.1
			mpls labels: 74414(top),8247
			interface: bundle-2
			via bypass_1



	dnRouter# show route forwarding-table ipv4 91.1.0.0/24
	VRF: default
	IPv4 Forwarding Table:
	Destination: 90.1.0.0/24
	    next-hop(1): 2.2.2.2 Recursive, Active
	    mpls labels: 1001(top)
	      next-hop(1,1): 13.0.1.1 Active
	      mpls labels: 100
	      interface: bundle-3
	      via tunnel_1
	      Bypass:
	        next-hop: 13.0.2.1
	        mpls labels: 101(top), 100
	        Interface: bundle-2
	        via bypass_1
	      next-hop(1,2): 13.0.1.1 Active
	      mpls labels: 102(top)
	      interface: bundle-3
	      via tunnel_2
	      Secondary:
	        next-hop: 13.0.2.1
	        mpls labels: 103
	        Interface: bundle-2
	        via tunnel_2
	    next-hop(2): 8.8.8.8 Recursive, Active
	    mpls labels: 2542(top)
	      next-hop(2,1): 14.0.1.1 Active
	      mpls labels: 103(top)
	      Interface: bundle-4
	      via tunnel_4
	      next-hop(2,2): 14.0.1.1 Active
	      mpls labels: 104(top)
	      interface: bundle-3
	      via tunnel_5


.. **Help line:** show route forwarding-table

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 5.1.0   | Command introduced |
+---------+--------------------+
| 11.0    | Added NCP filter   |
+---------+--------------------+
| 16.1    | Added All filter   |
+---------+--------------------+
