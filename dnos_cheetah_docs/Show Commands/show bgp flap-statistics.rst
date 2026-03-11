show bgp flap-statistics
------------------------

**Minimum user role:** viewer

This command displays paths that were suppressed due to BGP dampening. This only affects eBGP prefixes.

The following command displays flap statistics of routes:



**Command syntax: show bgp** instance vrf [vrf-name] [address-family] [sub-address-family] **flap-statistics** {ip-address [ip-address] \| ip-prefix [ip-prefix] \| cidr-only \| ipv4-prefix-list [prefix-list-name] \| ipv6-prefix-list [prefix-list-name] \| regex [regex] \| policy [policy-name]}

**Command mode:** operational


..
	**Internal Note**

	- use vrf to display information for a non-default vrf

	- for non-default instance vrf support only "unicast" sub-address-family

	- address-family sub-address-family are optional, if not specified display for all sub-address-families

	- ip-address - display route matching the ip address. must match the address-family when specified

	- cidr-only - display only routes with non-natural netmasks

	- ipv4|6-prefix-list - display only routes matching the prefix-list. must match the address-family when specified

	- regex - display only routes matching the regular expression

	- policy - display only routes matching the policy


**Parameter table**

+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| Parameter          | Description                                                                                                                                                                   | Range                                                                      |
+====================+===============================================================================================================================================================================+============================================================================+
| vrf-name           | Display routing information for a non-default VRF                                                                                                                             | 1..255 characters                                                          |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| address-family     | Display routing information for a specific address-family (AFI)                                                                                                               | IPv4 IPv6                                                                  |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| sub-address-family | Display routing information for a specific subsequent address-family (SAFI). Only unicast is supported with a non-default VRF.                                                | unicast vpn                                                                |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| ip-address         | IP address in IPv4 format or IPv6 format. Must match the AFI or SAFI when specified.                                                                                          | A.B.C.D xx:xx::xx:xx                                                       |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| ip-prefix          | IP-prefix in IPv4 format or IPv6 format. Must match the AFI or SAFI when specified.                                                                                           | A.B.C.D/x xx:xx::xx:xx/x                                                   |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| cidr-only          | Displays only the routes with non-natural subnet masks                                                                                                                        | \-                                                                         |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| ipv4-prefix-list   | Displays only the routes matching the prefix-list. They must match the address-family when specified                                                                          | \-                                                                         |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| ipv6-prefix-list   | Displays only the routes matching the prefix-list. They must match the address-family when specified                                                                          | \-                                                                         |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| regex              | A regular expression defining a search pattern                                                                                                                                | \-                                                                         |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+
| policy             | Displays only the routes matching the policy                                                                                                                                  |                                                                            |
+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------+

**Example**
::

	dnRouter# show bgp flap-statistics

	dnRouter# show bgp instance vrf A flap-statistics

	dnRouter# show bgp ipv4 flap-statistics ip-address 1.1.1.1

	dnRouter# show bgp ipv6 flap-statistics ip-prefix 2:2::2:/64

	dnRouter# show bgp ipv6 unicast flap-statistics ipv5-prefix-list PL_NAME

	dnRouter# show bgp flap-statistics regex 1.[0-9].1.1

	dnRouter# show bgp instance vrf A ipv6 flap-statistics policy POL_NAME


.. **Help line:** show bgp ipv4 flap-statistics

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 6.0     | Command introduced                 |
+---------+------------------------------------+
