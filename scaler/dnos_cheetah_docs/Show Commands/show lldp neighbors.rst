show lldp neighbors
-------------------

**Minimum user role:** viewer

To display the configuration and operational values of LLDP neighbors:



**Command syntax: show lldp neighbors** [interface-name]

**Command mode:** operational



.. **Note**

	- NeighborChassis IDtaken from received TLV type 1 - "Chassis ID"

	- Neighborinterface taken from received TLV type 2 - "Port ID"

	- NeighborTTL taken from received TLV type 3 - "Time To Live"

	- Neighbor interface description taken from received TLV type 4 - "Port description"

	- Neighbor System Name taken from received TLV type 5 - "System Name"

	- Neighbor SystemDescriptiontaken from received TLV type 6 - "SystemDescription"

	- NeighborSystem Capabilitiestaken from received TLV type 7 - "System Capabilities"

	- Neighbor uptime is the time the local interface received lldp packets duringhold-timetime window

	- If optional parameters are not received, then N/A shall be displayed instead

	- If the advertisement of an optional TLV is disabled, then the relevant paramter shall be noted as not advertised

	- If the advertisement of an optional TLV is enabled, then the information should be updated as asoon as commit passes and sent in subsequent updates

**Parameter table**

+----------------+------------------------------------------------------------------+---------------------+
| Parameter      | Description                                                      | Range               |
+================+==================================================================+=====================+
| interface-name | Filters the information to display only the specified interface. | Physical interfaces |
+----------------+------------------------------------------------------------------+---------------------+

The following information is displayed:

+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Parameter                      | Description                                                                                                     | Range               | Default     |
+================================+=================================================================================================================+=====================+=============+
| Interface                      | The list of local interfaces for which neighbor information is available.                                       | Physical interfaces | \-          |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Neighbor System Name           | The configured name of the neighbor system. See system name.                                                    | 1..255 characters   | \-          |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Neighbor Interface             | The name of the neighbor LLDP enabled interface.                                                                | Physical interfaces | \-          |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Neighbor Interface Description | Taken from received TLV type 4 - “Port description”.                                                            | String              |             |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Neighbor TTL                   | Number of seconds for which the displayed information is valid.                                                 | Integer             | \-          |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Chassis ID                     | The unique identifier of the chassis. Displayed when the interface option is used.                              | 1..255 characters   | \-          |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Chassis ID Type                | The type of ID used for the chassis. Displayed when the interface option is used.                               | MAC Address         | MAC Address |
|                                |                                                                                                                 | IfAlias             |             |
|                                |                                                                                                                 | entPhysicalAlias    |             |
|                                |                                                                                                                 | Mgmt Address        |             |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| System Name                    | The name of the local system or neighbor system. Displayed when the interface option is used.                   | 1..255 characters   | \-          |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| System Description             | The description configured for the system. See system info description.                                         | 1..255 characters   | \-          |
|                                | Displayed when the interface option is used.                                                                    |                     |             |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Transmit                       | Displays the configured admin-state of the LLDP message transmission capability of the LLDP enabled interfaces. | Enabled             | Enabled     |
|                                | Displayed when the interface option is used.                                                                    | Disabled            |             |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Receive                        | Displays the configured admin-state of the LLDP message receipt capability of the LLDP enabled interfaces.      | Enabled             | Enabled     |
|                                | Displayed when the interface option is used.                                                                    | Disabled            |             |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| System Capabilities            | The information regarding the neighbor's capabilities.                                                          | Bridge              | \-          |
|                                |                                                                                                                 | Router              |             |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+
| Management Address             | The management address as advertised by the neighbor.                                                           | IPv4/IPv6 Address   | \-          |
+--------------------------------+-----------------------------------------------------------------------------------------------------------------+---------------------+-------------+

**Example**
::

	dnRouter# show lldp neighbors

	| Interface    | Neighbor System Name | Neighbor interface    | Neighbor TTL|
	|--------------+----------------------+-----------------------+-------------|
	| ge100-1/1/1  | dn10-systemR1-fe2    | ge100-2/3/1           | 120         |
	| ge100-1/2/1  | dn10-systemR1-fe2    | ge100-2/3/2           | 120         |
	| ge100-4/2/1  | dn11-systemR1-fe1    | ge100-1/1/2           | 120         |
	| ge100-4/2/2  | dn11-systemR1-fe4    | ge100-4/1/1           | 120         |

	dnRouter# show lldp neighbors ge100-1/1/1

	interface ge100-1/1/1
	 Local Parameters:
	    Chassis ID: aa:bb:cc:dd:ee:01 (Type: MAC Address)
	    System Name: dn1-Local-Router, System Description: DRIVENETS LTD. Virtual Router, DNOS [10.0.0.1]
		Management Address: 1.1.1.1 (not-advertised)
		System Capabilities: Bridge, Router
		Interface Description: ###TO_R30_Core###
	    Transmit: enabled, Receive: enabled
	 Neighbor Parameters:
	    Uptime: 10 Days, 00:01:30
	    Chassis ID: 7c:fe:90:57:73:10 (Type: MAC Address)
	    System Name: dn10-systemR1-fe2, System Description: DRIVENETS LTD. Virtual Router, DNOS [10.0.0.1]
		Management Address: N/A
	    System Capabilities: Bridge, Router
	    Interface Name: ge100-2/3/1
	    Interface Description: user_desc_of_ge100-2/3/1


.. **Help line:** show lldp neighbor list

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 7.0     | Command introduced                        |
+---------+-------------------------------------------+
| 9.0     | Not supported in this version             |
+---------+-------------------------------------------+
| 10.0    | Command supported                         |
+---------+-------------------------------------------+
| 11.0    | Added interface description to the output |
+---------+-------------------------------------------+
| 16.1    | Added optional TLVs information           |
+---------+-------------------------------------------+
