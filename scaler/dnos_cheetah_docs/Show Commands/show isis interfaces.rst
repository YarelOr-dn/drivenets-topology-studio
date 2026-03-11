show isis interfaces
--------------------

**Minimum user role:** viewer



The show isis interfaces command displays concentric information on the IS-IS process on all IS-IS-enabled interfaces, if an interface name is not specified. If specified, then the IS-ISconfiguration for the requested interface is displayed.

**Command syntax: show isis** instance [isis-instance-name] **interfaces** {[interface-name] \| detail}

**Command mode:** operational



**Note**

- The command is applicable to the following interface types:

	- Physical

	- Physical vlan

	- Bundle

	- Bundle vlan

	- gre-tunnel

..
	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances

	- set [interface-name] to display detailed information for a specific interface

**Parameter table**

+--------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                                                               | Range                                                                                                                        |
+====================+===========================================================================================================================================================+==============================================================================================================================+
| No argument        | Displays concentric information relating to the IS-IS-enabled interfaces.                                                                                 | \-                                                                                                                           |
+--------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| isis-instance-name | Displays interface information for a specific IS-IS instance. If you do not specify an instance, information for all instances will be displayed (string) | 1..255                                                                                                                       |
+--------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| interface-name     | Displays detailed information on the specified interface.                                                                                                 | An IS-IS-enabled interface name. ge{/10/25/40/100}-X/Y/Z bundle-<bundle-id> bundle-<bundle-id.sub-bundle-id> gre-tunnel-<id> |
+--------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+
| detail             | Displays detailed information on all IS-IS enabled interfaces.                                                                                            | \-                                                                                                                           |
+--------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show isis interfaces
	Instance ISIS_A:
	  Interface    State    Type           Level
	  lo1          Up       loopback       L2
	  bundle-1     Up       point-to-point L2
	  bundle-3     Up       point-to-point L2
	  gre-tunnel-3 Up       point-to-point L2
	  tunnel_A     Down     point-to-point L2
	Instance ISIS_B:
	  Interface    State    Type           Level
	  bundle-4     Up       point-to-point L2
	  bundle-5     Up       point-to-point L2
	  tunnel_B     One-Way  point-to-point L2

	dnRouter# show isis instance ISIS_A interfaces bundle-1
	Instance ISIS_A:
	  Interface: bundle-1, State: Up, Active, Circuit Id: 0x96
	    Type: point-to-point, Level: L2
	    Circuit-ID: 0x96
	    Extended circuit-id: 0x96
	    Level-2 Information:
			IPv4 Unicast topology:
	      		LDP sync is disabled
	      		Metric: 10, Active neighbors: 1
	      Hello interval: 3, Holddown count: 10 (pad)
	      CNSP interval: 10, PSNP interval: 2
	    LDP status down
	    IP Prefix(es):
	      12.0.0.10/24
	    IPv6 Link-Locals:
	      fe80::42:cff:fe00:a/64
	    IPv6 Prefixes:
	      1200::10/120

	dnRouter# show isis instance ISIS_B interfaces forwarding-adjacency tunnel_B
	Instance ISIS_B:
	  Interface: tunnel_B, State: One-Way, Active
	    Type: point-to-point, Level: L2
	    Level-2 Information:
	      Ipv4 Metric: 10
	    Remote System: NEIGH_1 1111.1111.1111



	dnRouter# show isis interfaces bundle-1117
	Instance Devtest_AP:
	Instance Level: L2
	Interface: bundle-1117, State: Up, Active
		Type: point-to-point, Level: L2
		Extended Circuit Id: 0x3406
		Level-2 Information:
		IPv4 Unicast topology:
			LDP sync is disabled
			Metric: 1
			TE-Metric: 1
			frr backup-candidate: enabled
		IPv6 Unicast topology:
			Metric: 1
			frr backup-candidate: enabled
		Active neighbors: 1
		Hello interval: 10, Holddown: 30 (pad)
		LDP status down
		BFD IPv4: Disabled
		BFD IPv6: Disabled
		IP Prefix(es):
		1.11.17.1/31
		IPv6 Link-Locals:
		fe80::8640:76ff:febc:37e5/64
		IPv6 Prefixes:
		2001:11:17::1/127


	dnRouter# show isis instance one interfaces detail

	Instance one:
	Instance Level: L2
	Interface: lo0, State: Up, Passive
		Type: loopback, Level: L2
		Extended Circuit Id: 0x3
		Level-2 Information:
		IPv4 Unicast topology: Enabled
			LDP sync is Disabled
			Metric: 0
			FRR backup-candidate: Enabled
		IPv4 Unicast address-family:
			Tag: 0
		IPv6 Unicast topology: Enabled
			Metric: 0
			FRR backup-candidate: Enabled
		IPv6 Unicast address-family:
			Tag: 0
		IPv4 Multicast topology: Enabled
			Metric: 0
			FRR backup-candidate: Enabled
		IPv4 Multicast address-family:
			Tag: 0

		LDP status down
		BFD IPv4: Disabled
		BFD IPv6: Disabled
		Measured Delay:           Min: N/A Avg: N/A Max: N/A usec
		Delay Normalization:      Interval: N/A Offset: N/A
		Normalized Delay:         Min: N/A Avg: N/A Max: N/A usec
		IP Prefix(es):
		1.1.1.1/32
		IPv6 Link-Locals:
		fe80::4856:58ff:fe10:3525/64

	Interface: bundle-3, State: Up, Active
		Type: point-to-point, Level: L2
		Extended Circuit Id: 0x7
		Level-2 Information:
		IPv4 Unicast topology: Enabled
			LDP sync is Disabled
			Metric: 10
			TE-Metric: 10
			FRR backup-candidate: Enabled
		IPv4 Unicast address-family:
			Tag: 0
		IPv6 Unicast topology: Enabled
			Metric: 10
			FRR backup-candidate: Enabled
		IPv6 Unicast address-family:
			Tag: 0
		IPv4 Multicast topology: Enabled
			Metric: 10
			FRR backup-candidate: Enabled
		IPv4 Multicast address-family:
			Tag: 0
		Active neighbors: 1
		Hello interval: 10, Holddown: 30 (pad)
		LDP status down
		BFD IPv4: Disabled
		BFD IPv6: Disabled
		Measured Delay:           Min: 19 Avg: 29 Max: 49 usec
		Delay Normalization:      Interval: 10 Offset: 3
		Normalized Delay:         Min: 23 Avg: 33 Max: 53 usec
		IP Prefix(es):
		13.1.1.1/24
		IPv6 Link-Locals:
		fe80::4c9a:51ff:fe5d:268f/64


**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 6.0     | Command introduced                               |
+---------+--------------------------------------------------+
| 11.4    | Added support for GRE tunnels                    |
+---------+--------------------------------------------------+
| 12.0    | Added support for BFD for IS-IS                  |
+---------+--------------------------------------------------+
| 15.0    | Added the status of the mesh-group configuration |
+---------+--------------------------------------------------+
| 18.0    | Added normalized delay information               |
+---------+--------------------------------------------------+
