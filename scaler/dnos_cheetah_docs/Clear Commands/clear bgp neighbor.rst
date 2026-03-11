clear bgp neighbor
------------------

**Minimum user role:** operator

To clear BGP neighbors:

**Command syntax: clear bgp** instance vrf [vrf-name] **neighbor {  * \| external \| [neighbor-address] \| remote-as [as-number] \| group [group-name]}** [address-family] [sub-address-family] soft [update-direction]

**Command mode:** operation

.. **Hierarchies**

**Note**

-  Optional parameters must match the order in the command

-  When performing a hard clear for a bgp neighbor with a specific address-family, for example clear bgp neighbor group BGP_GROUP ipv4, the bgp session will tear affecting all address families

-  When stating a sub-address family, the address-family and update direction must be specified

-  Address-family and sub-address-family are used to clear a specific address-family or sub-address-family

-  Use soft to apply soft reconfig

-  When stating 'instance vrf' support is for **'unicast'** sub-address-family only

-  When no update-direction is specified, perform a hard clear.

**Parameter table**

+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| Parameter             | Description                                                                                                                                                            | Range                                                          | Default     |
+=======================+========================================================================================================================================================================+================================================================+=============+
| vrf-name              | Clears only the specified VRF routes. When VRF is specified, only unicast sub-address-family is supported                                                              | 1..255 characters                                              | \ -         |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| \*                    | Clears all neighbors                                                                                                                                                   | \-                                                             | \ -         |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| external              | Clears all eBGP neighbors                                                                                                                                              | \-                                                             |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| neighbor-address      | Clears a specific neighbor                                                                                                                                             | A.B.C.D                                                        |             |
|                       |                                                                                                                                                                        | xx:xx::xx:xx                                                   |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| as-number             | Clears neighbors matching the specific AS number                                                                                                                       | 1..4294967295                                                  |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| group-name            | Clears all neighbors from the specified neighbor group                                                                                                                 | 1..255 characters                                              |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| address-family        | Clears only the specific address-family routes                                                                                                                         | IPv4                                                           |             |
|                       |                                                                                                                                                                        | IPv6                                                           |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| sub-address-family    | Clears neighbors for the specified sub-address family indicator (SAFI). When stating the sub-address-family, address-family and update-direction must be specified.    | unicast                                                        |             |
|                       |                                                                                                                                                                        | vpn                                                            |             |
|                       |                                                                                                                                                                        | flowspec                                                       |             |
|                       |                                                                                                                                                                        | multicast                                                      |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| soft                  | Allows routing tables to be reconfigured and activated without clearing the BGP session.                                                                               | \-                                                             |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+
| update-direction      | Clears neighbors in the specified direction. When not specified, hard clear is performed                                                                               | in - Triggers inbound soft reconfiguration                     |             |
|                       |                                                                                                                                                                        | out - Triggers inbound soft reconfiguration                    |             |
|                       |                                                                                                                                                                        | both - Triggers inbound and outbound soft   reconfiguration    |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------------------+-------------+

**Example**
::

	dnRouter# clear bgp neighbor *
	dnRouter# clear bgp neighbor * ipv4
	dnRouter# clear bgp neighbor * ipv4 unicast out
	dnRouter# clear bgp neighbor * soft
	dnRouter# clear bgp neighbor * soft out

	dnRouter# clear bgp neighbor external
	dnRouter# clear bgp neighbor external ipv4
	dnRouter# clear bgp neighbor external ipv4 unicast out
	dnRouter# clear bgp neighbor external soft
	dnRouter# clear bgp neighbor external ipv6 soft in

	dnRouter# clear bgp neighbor 7.7.7.7
	dnRouter# clear bgp neighbor 7.7.7.7 ipv6
	dnRouter# clear bgp neighbor 7.7.7.7 ipv6 vpn in
	dnRouter# clear bgp neighbor 7.7.7.7 out
	dnRouter# clear bgp neighbor 7.7.7.7 soft out
	dnRouter# clear bgp neighbor 7.7.7.7 ipv6 unicast out

	dnRouter# clear bgp neighbor remote-as 64999
	dnRouter# clear bgp neighbor remote-as 64999 ipv6
	dnRouter# clear bgp neighbor remote-as 64999 ipv6 vpn in
	dnRouter# clear bgp neighbor remote-as 64999 out
	dnRouter# clear bgp neighbor remote-as 64999 ipv6 vpn soft

	dnRouter# clear bgp neighbor group BGP_GROUP
	dnRouter# clear bgp neighbor group BGP_GROUP ipv4
	dnRouter# clear bgp neighbor group BGP_GROUP ipv4 unicast out
	dnRouter# clear bgp neighbor group BGP_GROUP soft
	dnRouter# clear bgp neighbor group BGP_GROUP soft in


	dnRouter# clear bgp instance vrf A neighbor *
	dnRouter# clear bgp instance vrf A neighbor 7.7.7.7 ipv6
	dnRouter# clear bgp instance vrf A neighbor remote-as 64999 ipv6 unicast in
	dnRouter# clear bgp instance vrf A neighbor group BGP_GROUP soft in



.. **Help line:**

**Command History**

+-----------+-------------------------------------------------+
| Release   | Modification                                    |
+===========+=================================================+
| 6.0       | Command introduced                              |
+-----------+-------------------------------------------------+
| 13.0      | Added support for sub-address family flowspec   |
+-----------+-------------------------------------------------+
| 16.1      | Added support for sub-address family multicast  |
+-----------+-------------------------------------------------+