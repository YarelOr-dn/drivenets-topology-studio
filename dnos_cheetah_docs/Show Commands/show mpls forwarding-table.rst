show mpls forwarding-table
--------------------------

**Minimum user role:** viewer

Use the following command to display data-path forwarding information base (FIB) MPLS label entries. You can filter the information by label, to show the routes for a specific label only or NCP. By default, the information is sent from the active NCP with the lowest ID.



**Command syntax: show mpls forwarding-table** table [table] label [mpls-label] ncp [ncp-id]

**Command mode:** operational



.. **Note**

	- By default, the information will be sent from the active NCP with the lowest ID.

	- For explicit-null in label (label 0 or 2) action in always pop and forwarding is deceided per next header information.

	- Use ncp [ncp-id] to display information from a specific ncp

	- Action - pop, swap, swap-push

	- Up to 7 out labels supported

	- Interface will show applicable egress forwarding (out interface, policy, etc)

**Parameter table**

+------------+------------------------------------------------------------------------------------+------------+
| Parameter  | Description                                                                        | Range      |
+============+====================================================================================+============+
| table      | Optionally filters the display to a specific table                                 | ipv4 p2mp  |
+------------+------------------------------------------------------------------------------------+------------+
| mpls-label | Optionally filters the display to a matching ingress label (shows a detailed view) | 0..1048575 |
+------------+------------------------------------------------------------------------------------+------------+
| ncp-id     | Optionally filters the display to a specific NCP                                   | 0..255     |
+------------+------------------------------------------------------------------------------------+------------+

The following information is displayed on each route:

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------+
| Attribute | Description                                                                                                                             |
+===========+=========================================================================================================================================+
| In Label  | The incoming label                                                                                                                      |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------+
| Action    | The action performed by the router on the label: swap, pop, swap-push                                                                   |
|           | For explicit-null in label (label 0 or 2), the action is always pop and forwarding is decided according to the next header information. |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------+
| Next Hop  | The next hop                                                                                                                            |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------+
| Interface | The interface of the route. The interface will show the applicable egress forwarding (out interface, policy, etc.)                      |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------+
| Out Label | The outgoing label (up to 7 labels)                                                                                                     |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::


	dnRouter# show mpls forwarding-table
	Legend: * - Active, A - Alternate path, B - Bypass, S - Secondary, EA - Enhanced-Alternate
	labels are arranged from top (left) to BoS (right), E - Entropy Label

	NCP-ID: 0
	IPv4 MPLS Forwarding Table:
	| In Label  | Action    | Next Hop     | Interface     | Out Labels           |
	+-----------+-----------+--------------+---------------+----------------------+
	| (*)20001  | swap      | 30.1.1.2     | bundle-1      | 12345                |
	| (*)       | swap      | 30.2.2.2     | bundle-2      | 10002                |
	| (A)       | swap      | 30.2.2.3     | bundle-3      | 13460                |
	| (*)20002  | pop       | 30.1.1.2     | bundle-1      |                      |
	| (*)0      | pop       | local        |               |                      |
	| (*)2003   | swap-push | 30.1.1.2     | bundle-1      | 10000, 12345         |
	| (*)77534  | swap-push | 30.1.1.2     | bundle-1      | 1234, 6000           |
	| (*)66411  | swap      | 20.2.2.3     | policy-4      | 34197, 34199         |
	| (*B)77117 | swap-push | 30.1.1.2     | bundle-2      | 63276, 1212          |


	dnRouter# show mpls forwarding-table
	Legend: * - Active, A - Alternate path, B - Bypass, S - Secondary, EA - Enhanced-Alternate
	labels are arranged from top (left) to BoS (right), E - Entropy Label

	NCP-ID: 0
	IPv4 MPLS Forwarding Table:
	| In Label  | Action    | Next Hop     | Interface     | Out Labels           |
	+-----------+-----------+--------------+---------------+----------------------+
	| 77530     | pop       | VPWS_1       | bundle-1      |                      |


	dnRouter# show mpls forwarding-table table p2mp

	NCP-ID: 0
	P2MP MPLS Forwarding Table:
	| In Label  | Action    | Next Hop     | Interface     | Out Labels           |
	+-----------+-----------+--------------+---------------+----------------------+
	| (*)26001  | swap      | 10.0.3.10    | ge100-1/0/1   | 40310                |
	| (*)       | swap      | 10.0.4.10    | ge100-1/0/2   | 40320                |
	| (*)26002  | swap      | 10.0.7.10    | ge100-1/0/7   | 40350                |


	dnRouter# show mpls forwarding-table label 20001
	VRF: default
	NCP-ID: 0
	IPv4 MPLS Forwarding Table:
	In label: 20001
	    next-hop(1): 30.1.1.2, Active
	    mpls label 12345
	    interface: bundle-1
	    next-hop(2): 30.2.2.2, Active
	    mpls label 10002
	    interface: bundle-1
	    Alternate Path:
	      next-hop(3): 30.2.2.3, Standby
	      mpls label 13460
	      interface: bundle-2


	dnRouter# show mpls forwarding-table label 0
	label: 0 (ipv4 explicit-null)
	Action: pop
	Nexthop: ipv4-prefix

	dnRouter# show mpls forwarding-table label 1
	label: 1 (router alert)
	Action: punt
	Nexthop: local processing

	dnRouter# show mpls forwarding-table label 2
	label: 2 (ipv6 explicit-null)
	Action: pop
	Nexthop: ipv6-prefix

	dnRouter# show mpls forwarding-table label 3
	label: 3 (implicit null)
	Action: pop
	Nexthop: ipv6-prefix

	dnRouter# show mpls forwarding-table label 4
	label: 4 (unassigned)

	dnRouter# show mpls forwarding-table label 5
	label: 5 (unassigned)

	dnRouter# show mpls forwarding-table label 6
	label: 6 (unassigned)

	dnRouter# show mpls forwarding-table label 7
	label: 7 (entropy label indicator)
	Action: address next label as the entropy label

	dnRouter# show mpls forwarding-table label 8
	label: 8 (unassigned)

	dnRouter# show mpls forwarding-table label 9
	label: 9 (unassigned)

	dnRouter# show mpls forwarding-table label 10
	label: 10 (unassigned)

	dnRouter# show mpls forwarding-table label 11
	label: 11 (unassigned)

	dnRouter# show mpls forwarding-table label 12
	label: 12 (unassigned)

	dnRouter# show mpls forwarding-table label 13
	label: 13 (GAL)
	Action: pop
	Nexthop: associated channel header

	dnRouter# show mpls forwarding-table label 14
	label: 14 (OAM alert)
	Action: pop
	Nexthop: Y.1711

	dnRouter# show mpls forwarding-table label 15
	label: 15 (extension)
	Action: pop
	Nexthop: per extension application


	dnRouter# show mpls forwarding-table label 77530

	VRF: default
	NCP-ID: 0
	IPv4 MPLS Forwarding Table:
	In label: 77530
	    pop & forward to vpws AC
	    interface: bundle-1

	FAT Label Negotiation: none


.. **Help line:** show mpls forwarding table

**Command History**

+---------+------------------------------------------------------------------+
| Release | Modification                                                     |
+=========+==================================================================+
| 5.1.0   | Command introduced                                               |
+---------+------------------------------------------------------------------+
| 10.0    | Removed packets switched and bytes switched columns              |
+---------+------------------------------------------------------------------+
| 11.0    | Added ncp-id filter, updated the number of supported labels to 7 |
+---------+------------------------------------------------------------------+
| 16.1    | Added local Pseudowire label                                     |
+---------+------------------------------------------------------------------+
| 17.1    | Added support for mLDP                                           |
+---------+------------------------------------------------------------------+
