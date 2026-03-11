show bgp prefix-list
--------------------

**Minimum user role:** viewer

To display routes according to prefix-list:

**Command syntax: show bgp** instance vrf [vrf-name] { [address-family] \| [address-family] [sub-address-family] } **ipv4-prefix-list \| ipv6-prefix-list [prefix-list-name]**

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- address-family sub-address-family are optional, if not specified display for all sub-address-families

	- ipv4|6-prefix-list - display only routes matching the prefix-list. must match the address-family when specified

  	- if no BGP prefixes match the request defined in the specified prefix-list, the command output will display: "Can't find specified prefix-list".


**Parameter table**

+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| Parameter          | Description                                                                                                                                                       | Range                       |
+====================+===================================================================================================================================================================+=============================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                                 | 1..255 characters           |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                                   | IPv4                        |
|                    |                                                                                                                                                                   | IPv6                        |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                                    | unicast                     |
|                    |                                                                                                                                                                   | vpn                         |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| ipv4-prefix-list   | Displays only the routes matching the prefix-list. They must match the address-family when specified                                                              | An existing prefix-list     |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+
| ipv6-prefix-list   | Displays only the routes matching the prefix-list. They must match the address-family when specified                                                              | An existing prefix-list     |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------+

**Example**
::

	dnRouter# show bgp ipv4-prefix-list PL_NAME

	dnRouter# show bgp instance vrf A ipv4-prefix-list PL_NAME

	dnRouter# show bgp instance vrf A ipv6 ipv6-prefix-list PL_NAME

	dnRouter# show bgp ipv6 unicast ipv6-prefix-list PL_NAME


.. **Help line:** show bgp ipv4 routes

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 6.0     | Command introduced                 |
+---------+------------------------------------+
