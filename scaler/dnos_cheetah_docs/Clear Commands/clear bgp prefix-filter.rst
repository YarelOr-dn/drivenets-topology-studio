clear bgp prefix-filter
-----------------------

**Minimum user role:** operator

To push out prefix-list ORF and do inbound soft reconfigure:

**Command syntax: clear bgp** instance vrf [vrf-name] **neighbor {  * \| external \| [neighbor-address] \| remote-as [as-number] \| group [group-name]}** [address-family] [sub-address-family] **in prefix-filter**

**Command mode:** operation

.. **Hierarchies**

**Note**

- Optional parameters must match the order in the command

- When stating a sub-address family, the address-family must be specified.


**Parameter table**

+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      |             |
| Parameter             | Description                                                                                                                                                            | Range                | Default     |
+=======================+========================================================================================================================================================================+======================+=============+
|                       |                                                                                                                                                                        |                      |             |
| vrf-name              | Clears only the specified VRF routes.                                                                                                                                  | 1..255 characters    | Disabled    |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      | \ -         |
| \*                    | Clears all neighbors                                                                                                                                                   | \ -                  |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      | \ -         |
| external              | Clears all eBGP neighbors                                                                                                                                              | \ -                  |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      | \ -         |
| neighbor-address      | Clears a specific neighbor                                                                                                                                             | A.B.C.D              |             |
|                       |                                                                                                                                                                        |                      |             |
|                       |                                                                                                                                                                        | xx:xx::xx:xx         |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      | \ -         |
| as-number             | Clears neighbors matching the specific AS number                                                                                                                       | 1..4294967295        |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      | \ -         |
| group-name            | Clears all neighbors from the specified neighbor group                                                                                                                 | 1..255 characters    |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      | \ -         |
| address-family        | Clears only the specific address-family routes                                                                                                                         | IPv4                 |             |
|                       |                                                                                                                                                                        |                      |             |
|                       |                                                                                                                                                                        | IPv6                 |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      | \ -         |
| sub-address-family    | Clears neighbors for the specified sub-address family indicator (SAFI). When stating the sub-address-family, address-family and update-direction must be specified.    | unicast              |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+



**Example**
::

	dnRouter# clear bgp neighbor * in prefix-filter
	dnRouter# clear bgp neighbor * ipv4 in prefix-filter
	dnRouter# clear bgp neighbor * ipv4 unicast in prefix-filter

	dnRouter# clear bgp neighbor external in prefix-filter
	dnRouter# clear bgp neighbor external ipv4 in prefix-filter
	dnRouter# clear bgp neighbor external ipv4 unicast in prefix-filter

	dnRouter# clear bgp neighbor 7.7.7.7 in prefix-filter
	dnRouter# clear bgp neighbor 7.7.7.7 ipv6 in prefix-filter
	dnRouter# clear bgp neighbor 7.7.7.7 ipv6 unicast in prefix-filter

	dnRouter# clear bgp neighbor remote-as 64999 in prefix-filter
	dnRouter# clear bgp neighbor remote-as 64999 ipv6 in prefix-filter
	dnRouter# clear bgp neighbor remote-as 64999 ipv6 unicast in prefix-filter

	dnRouter# clear bgp neighbor group BGP_GROUP in prefix-filter
	dnRouter# clear bgp neighbor group BGP_GROUP ipv4 in prefix-filter
	dnRouter# clear bgp neighbor group BGP_GROUP ipv4 unicast in prefix-filter
	dnRouter# clear bgp instance vrf A neighbor * in prefix-filter
	dnRouter# clear bgp instance vrf A neighbor 7.7.7.7 ipv6 in prefix-filter
	dnRouter# clear bgp instance vrf A neighbor remote-as 64999 ipv6 unicast in prefix-filter
	dnRouter# clear bgp instance vrf A neighbors group BGP_GROUP in prefix-filter

.. **Help line:**

**Command History**

+-----------+-------------------------------------------------+
| Release   | Modification                                    |
+===========+=================================================+
| 6.0       | Command introduced                              |
+-----------+-------------------------------------------------+