clear bfd statistics
--------------------

**Minimum user role:** operator

To clear BFD session statistics, which resets the BFD session counters:

- clear bfd statistics - clears all BFD sessions.

- vrf - clears BFD session statistics running in the specified VRF. When not specified, it assumes the default VRF sessions.

- discriminator - clears BFD sessions matching the local discriminator.

- tunnel - clears BFD sessions protecting an RSVP tunnel matching the tunnel-name.

- local-address - clears BFD sessions matching the local address.

To restart BFD sessions:

**Command syntax: clear bfd statistics** discriminator [discriminator] | tunnel [tunnel-name] | { vrf [vrf-name] local-address [ip-address] neighbor [neighbor-address] interface [interface-name] client [client] }

**Command mode:** operation

.. **Hierarchies**

**Note**

- When both BFD address-family match the clear request, reset both address-family sessions


**Parameter table**

+------------------+-------------------------------------------------------------------------------------+--------------------+-------------------------------------------------------------------------------+
| Parameter        | Values                                                                              | Default value      | notes                                                                         |
+==================+=====================================================================================+====================+===============================================================================+
| vrf-name         | Any configured vrf name                                                             | default            |                                                                               |
|                  |                                                                                     |                    |                                                                               |
|                  | The following vrfs exist by default:  default, mgmt0, mgmt-ncc-0, mgmt-ncc-1        |                    |                                                                               |
|                  |                                                                                     |                    |                                                                               |
|                  | Use 'all' to clear statistics form all vrfs                                         |                    |                                                                               |
+------------------+-------------------------------------------------------------------------------------+--------------------+-------------------------------------------------------------------------------+
| discriminator    | 0-4294967295                                                                        |                    |                                                                               |
+------------------+-------------------------------------------------------------------------------------+--------------------+-------------------------------------------------------------------------------+
| tunnel-name      | string length 1..255                                                                |                    |  Head tunnel name                                                             |
+------------------+-------------------------------------------------------------------------------------+--------------------+-------------------------------------------------------------------------------+
| local-address    | A.B.C.D                                                                             |                    | when neighbor-address is used, must match neighbor-address address-family     |
|                  |                                                                                     |                    |                                                                               |
|                  | {ipv6 address format}                                                               |                    |                                                                               |
+------------------+-------------------------------------------------------------------------------------+--------------------+-------------------------------------------------------------------------------+
| neighbor-address | A.B.C.D                                                                             |                    | when local-address is used, must match local -address address-family          |
|                  |                                                                                     |                    |                                                                               |
|                  | {ipv6 address format}                                                               |                    |                                                                               |
+------------------+-------------------------------------------------------------------------------------+--------------------+-------------------------------------------------------------------------------+
| interface-name   | bundle-<bundle id>                                                                  |                    |                                                                               |
|                  |                                                                                     |                    |                                                                               |
|                  | bundle-<bundle id>.<sub-interface-id>                                               |                    |                                                                               |
|                  |                                                                                     |                    |                                                                               |
|                  | ge<interface speed>-<A>/<B>/<C>                                                     |                    |                                                                               |
+------------------+-------------------------------------------------------------------------------------+--------------------+-------------------------------------------------------------------------------+
| client           | [bundle interface name], bgp, static, rsvp                                          |                    |                                                                               |
|                  | ospf, ospfv3                                                                        |                    |                                                                               |
+------------------+-------------------------------------------------------------------------------------+--------------------+-------------------------------------------------------------------------------+

**Example**
::

	dnRouter# clear bfd statistics
	dnRouter# clear bfd statistics discriminator 100
	dnRouter# clear bfd statistics tunnel TUNNEL_1
	dnRouter# clear bfd statistics neighbor 1.2.3.4
	dnRouter# clear bfd statistics local-address 1.2.3.3 neighbor 1.2.3.4
	dnRouter# clear bfd statistics local-address 2001:ab12::2
	dnRouter# clear bfd statistics interface ge10-2/1/1
	dnRouter# clear bfd statistics local-address 4.4.4.4 client rsvp
	dnRouter# clear bfd statistics client rsvp neighbor 5.5.5.5
	dnRouter# clear bfd statistics client bundle-3
	dnRouter# clear bfd statistics vrf CLIENT_A


.. **Help line:** Clear bfd statistics


**Command History**

+-------------+------------------------------------+
|             |                                    |
| Release     | Modification                       |
+=============+====================================+
|             |                                    |
| 11.2        | Command introduced                 |
+-------------+------------------------------------+
|             |                                    |
| 12.0        | Added support for BFD for IS-IS    |
+-------------+------------------------------------+
| 16.1        | Support was added for VRFs         |
+-------------+------------------------------------+
