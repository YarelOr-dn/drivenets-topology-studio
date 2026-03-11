show dnos-internal routing fib-manager database
-----------------------------------------------

**Minimum user role:** viewer

To display fib-manager forwarding data distribution information:

**Command syntax: show dnos-internal routing fib-manager database** {egress \| egress nh-address [ip-address] \| egress tunnel-oid [tunnel-oid] \| egress-request \| neighbor \| neighbor address [ip-address] \| nexthop \| nexthop oid [nh-oid] \| route \| route \| route [ip-prefix] \| route [address-family] \| route mpls-label [label] \| route summary \| tunnel \| tunnel name [tunnel-name] \| tunnel oid [tunnel-oid] \| summary \| bfd}

**Command mode:** operation

**Parameter table**

+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| Parameter         | Description                                                                                                                                                   |
+===================+===============================================================================================================================================================+
|                   |                                                                                                                                                               |
| egress            | Displays egress object (encapsulation) information. You can filter   the displayed information by nexthop address, tunnel object.                             |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| egress-request    | Displays which NCP request to create an egress object                                                                                                         |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| neighbor          | Displays neighbor ARP or NDP information. You can filter the displayed   information by neighbor address.                                                     |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| nexthop           | Displays the nexthop information. You can filter the information   by nexthop ID.                                                                             |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| route             | Displays routes information. You can filter the information by   prefix, address-family, or MPLS label. You can also display the summary for   all routes.    |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| tunnel            | Displays the tunnels information. You can filter the information   by tunnel ID or tunnel name.                                                               |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| summary           | Displays the database summary information (except route   information).                                                                                       |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                   |                                                                                                                                                               |
| bfd               | Displays BFD information.                                                                                                                                     |
+-------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show dnos-internal routing fib-manager database summary
	Object Type               Amount
	-----------------------------------
	Neighbors                 1
	Tunnels                   1
	Nexthops                  7
	Egress Objects            2 (2 installed)
	Egress Object Requests    10 (requested by 5 clients)
	---------------------------------

	dnRouter# show dnos-internal routing fib-manager database route summary
	Object Type               Amount
	-----------------------------------
	Neighbors                 1
	Tunnels                   1
	Nexthops                  7
	Egress Objects            2 (2 installed)
	Egress Object Requests    10 (requested by 5 clients)
	---------------------------------


	a80da8804f09# show fib-manager database route summary
	Route Type                Amount
	-----------------------------------
	VRF 0
	-----------------------------------
	IPv4                      8
	IPv6                      2
	MPLS                      0
	Total                     10
	---------------------------------

	Overall
	Overall IPv4              8
	Overall IPv6              2
	Overall MPLS              0
	Overall Total             10
	---------------------------------

	dnRouter# show dnos-internal routing fib-manager database route ipv4
	VRFs [size: 1]
	------------------------------------------------------------
	IPv4 Routes [size: 8]
	------------------------------------------------------------
	1.0.0.0/24: Type: normal, Protocol: connected, Metric: 0, Priority: high,
	1 Nexthop(s) :
	1. OID 3

	2.0.0.0/24: Type: normal, Protocol: static, Metric: 0, Priority: high,
	1 Nexthop(s) :
	1. OID 5

	3.0.0.0/24: Type: normal, Protocol: connected, Metric: 0, Priority: high,
	1 Nexthop(s) :
	1. OID 4

	10.10.10.10/32: Type: normal, Protocol: connected, Metric: 0, Priority: high,
	1 Nexthop(s) :
	1. OID 2

	13.13.12.12/32: Type: normal, Protocol: static, Metric: 0, Priority: high,
	1 Nexthop(s) :
	1. OID 6

	20.20.20.20/32: Type: normal, Protocol: static, Metric: 0, Priority: high,
	1 Nexthop(s) :
	1. OID 5

	30.30.30.30/32: Type: normal, Protocol: static, Metric: 0, Priority: high,
	1 Nexthop(s) :
	1. OID 5

	127.0.0.0/8: Type: normal, Protocol: connected, Metric: 0, Priority: high,
	1 Nexthop(s) :
	1. OID 1

	------------------------------------------------------------
	------------------------------------------------------------

	dnRouter# show dnos-internal routing fib-manager database egress-request
	Datapaths [size: 5]
	------------------------------------------------------------
	EgressObjectsRequests Datapath: 0 [size: 2]
	------------------------------------------------------------
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: None  tunnelOid: 0 indexPoolId: 223
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: 70001  tunnelOid: 2 indexPoolId: 2097375
	------------------------------------------------------------
	EgressObjectsRequests Datapath: 1 [size: 2]
	------------------------------------------------------------
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: None  tunnelOid: 0 indexPoolId: 223
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: 70001  tunnelOid: 2 indexPoolId: 2097375
	------------------------------------------------------------
	EgressObjectsRequests Datapath: 2 [size: 2]
	------------------------------------------------------------
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: None  tunnelOid: 0 indexPoolId: 223
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: 70001  tunnelOid: 2 indexPoolId: 2097375
	------------------------------------------------------------
	EgressObjectsRequests Datapath: 3 [size: 2]
	------------------------------------------------------------
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: None  tunnelOid: 0 indexPoolId: 223
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: 70001  tunnelOid: 2 indexPoolId: 2097375
	------------------------------------------------------------
	EgressObjectsRequests Datapath: 4 [size: 2]
	------------------------------------------------------------
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: None  tunnelOid: 0 indexPoolId: 223
	ifindex: 223 dp_index: 8192 address: 1.0.0.20 labels: 70001  tunnelOid: 2 indexPoolId: 2097375
	------------------------------------------------------------
	------------------------------------------------------------

	dnRouter# show dnos-internal routing fib-manager database bfd
	BFD Sessions [size: 6]
	VrfId   Local Address                               Remote Address                              IfIndex  Discriminator   Status      Flags
	-------------------------------------------------------------------------------------------------------------------------------------------
	0       11.0.3.1                                    11.0.3.3                                    0        8012            Up          0x21
	0       1113::3311                                  1113::1133                                  0        8016            Up          0x21
	0       11.0.4.1                                    11.0.4.4                                    0        8020            Up          0x21
	0       1111::4411                                  1111::1144                                  0        8024            Up          0x21
	0       1112::2211                                  1112::1122                                  0        8028            Up          0x21
	0       11.0.2.1                                    11.0.2.2                                    0        8032            Up          0x21
	-------------------------------------------------------------------------------------------------------------------------------------------

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+
|             |                       |
| 11.5        | Added BFD option      |
+-------------+-----------------------+


