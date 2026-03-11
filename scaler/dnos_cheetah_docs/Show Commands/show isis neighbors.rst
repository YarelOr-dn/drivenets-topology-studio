show isis neighbors
-------------------

**Minimum user role:** viewer

The show isis neighbors command displays information on all IS-IS neighbors. You can display details on the neighbors and you can filter by system-id.

To display neighbor information, use the following command:

**Command syntax: show isis** instance [isis-instance-name] **neighbors** {system-id [system-id] \| hostname [hostname] \| detail}

**Command mode:** operational


..
	**Internal Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances

	- set [system-id] to display detailed information for a specific neighbor

	- set [interface-name] to display detailed information for a specific interface

	- set detail to display detailed information for all IS-IS neighbors

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                                          |
+====================+======================================================================================================================================+
| No parameter       | Displays concentric information on all the IS-IS neighbors                                                                           |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------+
| isis-instance-name | Displays neighbors for a specific IS-IS instance. If you do not specify an instance, neighbors from all instances will be displayed. |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------+
| system-id          | Filters the displayed information for a specified neighbor                                                                           |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------+
| hostname           | Filters the displayed information for a specific hostname                                                                            |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------+
| detail             | Displays details on each IS-IS neighbor                                                                                              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show isis neighbors
	Area area1:
	  System Id           Interface   L  State       Last State Change   Holdtime  SNPA
	  q2                  bundle-1    2  Up          14m40s              28        p2p
	  q3                  bundle-2    2  Up          14m40s              28        p2p
	Area area2:
	  System Id           Interface   L  State       Last State Change   Holdtime  SNPA
	  q5                  bundle-4    2  Up          14m40s              29        p2p
	  q6                  bundle-6    2  Up          14m40s              28        p2p
	
	dnRouter# show isis neighbors system-id 4444.4444.4444
	Area area1:
	  q2                  
	    Interface: bundle-1, Level: 2, State: Up, Expires in 29s
	    Last state change: 19h49m27s ago
		Speaks: IPv4, IPv6
	    BFD IPv4 status = Disabled
	    BFD IPv6 status = Disabled
	    Circuit type: L2, Speaks: IPv4, IPv6
	    Topologies:
	      ipv4-unicast
	      ipv6-unicast
	    SNPA: p2p
	    Area Address(es):
	      47.0001
	    IPv4 Address(es):
	      12.0.0.2
	    IPv6 Address(es):
	      fe80::42:cff:fe00:2
	
	
	
	dnRouter# show isis neighbors detail

	Instance INST_1:
	  core1
	    Interface: ge100-0/0/0.3912, Level: 2, State: Up, Expires in 23s
	    Last state change: 47m40s ago
	    System-id: 1111.1111.1140
	    Speaks: IPv4, IPv6
	    BFD IPv4 status = Disabled
	    BFD IPv6 status = Disabled
	    Topologies:
	      ipv4-unicast
	      ipv6-unicast
	    SNPA: point-to-point
	    Area Address(es):
	      46.0040
	    IPv4 Address(es):
	      12.12.0.2
	    IPv6 Address(es):
	      fe80::206:aff:fe0e:3106

	  core2
	    Interface: ge100-0/0/0.3913, Level: 2, State: Up, Expires in 24s
	    Last state change: 47m39s ago
	    System-id: 1111.1111.1140
	    Speaks: IPv4, IPv6
	    BFD IPv4 status = Disabled
	    BFD IPv6 status = Disabled
	    Topologies:
	      ipv4-unicast
	      ipv6-unicast
	    SNPA: point-to-point
	    Area Address(es):
	      46.0040
	    IPv4 Address(es):
	      12.13.0.2
	    IPv6 Address(es):
	      fe80::206:aff:fe0e:3107


**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 6.0     | Command introduced                        |
+---------+-------------------------------------------+
| 12.0    | Added support for BFD for IS-IS           |
+---------+-------------------------------------------+
| 15.0    | Added support for displaying by System Id |
+---------+-------------------------------------------+
| 17.0    | Added 'Last State Change' to brief        |
+---------+-------------------------------------------+


