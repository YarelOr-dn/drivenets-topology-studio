show flowspec
-------------

**Minimum user role:** viewer

To display the FlowSpec rules installed in the data plane:



**Command syntax: show flowspec** instance vrf [vrf-name] {[address-family] | [address-family] destination [dest-prefix] source [src-prfix] | [address-family] nlri [nlri]}

**Command mode:** operational



**Note**

- Source and destination filtering will match FlowSpec rules by exact match. For example, if the source is 50.0.0.0/8 a search for 50.1.2.3/8 will not result in a match. If source is 'any', search for 1.1.1.1/32 will not result in a match either.

- For dest-prefix and src-prefix, M is the prefix mask length, O is the IPv6 offset. You can enter both prefix offset and mask. If no offset is set, an offset of 0 is assumed

..
	**Internal Note**

	- if source is 50.0.0.0/8, search of 50.1.2.3/8 will not result in match.

	- if source is 'any', search of 1.1.1.1/32 will not result in match

	- When setting source or destination (or both), address-family must be set. Address-family must match the requested prefix type

	- When setting nlri, address-family must be set.

	- nlri - require to use apostrophes when entering the nlri string

	- When setting IPv6 prefix, user can enter both prefix offset and mask. Filter by exact match, if no offset is set, assume offset = 0

**Parameter table**

+----------------+-------------------------------------------------------------------------------------------------+------------------+-----------+
| Parameter      | Description                                                                                     | Range            | Default   |
+================+=================================================================================================+==================+===========+
| vrf-name       | Display the flowspec rule from a given vrf.                                                     | 0..255           | \-        |
+----------------+-------------------------------------------------------------------------------------------------+------------------+-----------+
| address-family | Filters the displayed routing information for a specific address-family.                        | IPv4             | both      |
|                |                                                                                                 | IPv6             |           |
+----------------+-------------------------------------------------------------------------------------------------+------------------+-----------+
| nlri           | Filters the displayed information for a specific Network Layer Reachability Information (NLRI). | FlowSpec NLRI    | \-        |
|                | The address-family must be set and must match the requested prefix type.                        |                  |           |
+----------------+-------------------------------------------------------------------------------------------------+------------------+-----------+
| dest-prefix    | Filters the displayed information for all rules matching the specified destination prefix       | A.B.C.D/M        | Offset: 0 |
|                |                                                                                                 | xx:xx::xx:xx/O-M |           |
+----------------+-------------------------------------------------------------------------------------------------+------------------+-----------+
| src-prefix     | Display information for all rules matching the specified source prefix                          | A.B.C.D/M        | Offset: 0 |
|                |                                                                                                 | xx:xx::xx:xx/O-M |           |
+----------------+-------------------------------------------------------------------------------------------------+------------------+-----------+

The displayed rules are ordered according to the priority defined by the RFC precedence algorithm. For each rule installed, the following information is displayed:

+----------------------+----------------------------------------------+--------------------------+
| Parameter            | Description                                  | Range                    |
+======================+==============================================+==========================+
| Address-family       | The address-family for the                   | IPv4                     |
|                      |                                              | IPv6                     |
+----------------------+----------------------------------------------+--------------------------+
| Flow                 | The FlowSpec rule installed                  | \-                       |
+----------------------+----------------------------------------------+--------------------------+
| Actions              | The action to take on the flow               | Traffic-rate: 0 (= drop) |
|                      |                                              | Else, allow              |
+----------------------+----------------------------------------------+--------------------------+
| Match packet counter | The number of packets that matched the rule. | Integer                  |
+----------------------+----------------------------------------------+--------------------------+


**Example**
::

	dnRouter# show flowspec

	Address-family: IPv4
		Flow: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Match packet counter:  1
		Flow: DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784
			Actions: Traffic-rate: 0 bps
			Match packet counter:  1

	Address-family: IPv6
		Flow: DstPrefix:=2011:11:100:1::/64,SrcPrefix:=1500:1550:5::1/128,NextHeader:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Match packet counter:  0

	dnRouter# show flowspec ipv4

	Address-family: IPv4
		Flow: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Match octets counter:  564
			Match packet counter:  1
		Flow: DstPrefix:=52.0.0.0/8,SrcPrefix:=51.1.2.3/32,Protocol:=17,DstPort:3784
			Actions: Traffic-rate: 0 bps
			Match packet counter:  1

	dnRouter# show flowspec ipv4 nlri "DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5"

	Address-family: IPv4
		Flow: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=5,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Match packet counter:  1

	dnRouter# show flowspec ipv4 destination 50.0.0.0/8

	Address-family: IPv4
		Flow: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Match packet counter:  1

	dnRouter# show flowspec ipv4 source 50.1.2.3/24

	Address-family: IPv4
		Flow: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/24,Protocol:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Match packet counter:  1

	dnRouter# show flowspec ipv4 destination 50.0.0.0/8 source 50.1.2.3/32

	Address-family: IPv4
		Flow: DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Match packet counter:  1

	dnRouter# show flowspec ipv6 destination 11:11:100:1::/8-64

	Address-family: IPv6
		Flow: DstPrefix:=11:11:100:1::/8-64,SrcPrefix:=1500:1550:5::1/128,NextHeader:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5
			Actions: Traffic-rate: 0 bps
			Match packet counter:  0

.. **Help line:** show flowspec rules and counters

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
