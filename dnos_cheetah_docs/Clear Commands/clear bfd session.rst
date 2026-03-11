clear bfd session
-----------------

**Minimum user role:** operator

Restarting a BFD session will not affect protected protocols. These parameters have the following impact:

- clear bfd - restarts all BFD sessions.

- vrf - clears the BFD sessions running in the specified VRF. When not specified, it effects the default VRF sessions.

- discriminator - clears a BFD session matching the local discriminator.

To restart BFD sessions:

**Command syntax: clear bfd session** tunnel [tunnel-name] | {vrf [vrf-name] discriminator [discriminator] local-address [ip-address] neighbor [neighbor-address] interface [interface-name] client [client] }

**Command mode:** operation

.. **Hierarchies**

**Note**

- When both BFD address-family match the clear request, reset both address-family sessions

.. -Restarting the BFD sessions will also clear the BFD session counters.


**Parameter table:**

+------------------+-------------------------------------------------------------------------------------+--------------------+-------------------------------------------------------------------------------+
| Parameter        | Values                                                                              | Default value      | notes                                                                         |
+==================+=====================================================================================+====================+===============================================================================+
| vrf-name         | Any configured vrf name                                                             | default            |                                                                               |
|                  |                                                                                     |                    |                                                                               |
|                  | The following vrfs exist by default:  default, mgmt0, mgmt-ncc-0, mgmt-ncc-1        |                    |                                                                               |
|                  |                                                                                     |                    |                                                                               |
|                  | Use 'all' to clear sessions from all vrfs                                           |                    |                                                                               |
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

	dnRouter# clear bfd session
	dnRouter# clear bfd session discriminator 100
	dnRouter# clear bfd session tunnel TUNNEL_1
	dnRouter# clear bfd session neighbor 1.2.3.4
	dnRouter# clear bfd session local-address 1.2.3.3 neighbor 1.2.3.4
	dnRouter# clear bfd session local-address 2001:ab12::2
	dnRouter# clear bfd session interface ge10-2/1/1
	dnRouter# clear bfd session local-address 4.4.4.4 client rsvp
	dnRouter# clear bfd session client rsvp neighbor 5.5.5.5
	dnRouter# clear bfd session client bundle-3
	dnRouter# clear bfd session discriminator 8 interface ge100-0/0/1
	dnRouter# clear bfd session vrf CLIENT_A
	dnRouter# clear bfd session vrf CLIENT_A neighbor 1.2.3.4

.. **Help line:** Clear bfd sessions

**Command History**

+-------------+-----------------------------------------+
|             |                                         |
| Release     | Modification                            |
+=============+=========================================+
| 6.0         | Command introduced                      |
+-------------+-----------------------------------------+
| 9.0         | Command not supported                   |
+-------------+-----------------------------------------+
| 11.2        | Command reintroduced with new syntax    |
+-------------+-----------------------------------------+
| 12.0        | Added support for BFD for IS-IS         |
+-------------+-----------------------------------------+
| 16.1        | Support was added for VRFs              |
+-------------+-----------------------------------------+
