clear bgp dampening
-------------------

**Minimum user role:** operator

To clear route flap dampening information:

**Command syntax: clear bgp** instance vrf [vrf-name] **dampening** [address-family] [sub-address-family] {route [route] \| prefix [prefix] \| neighbor [neighbor-address] }

**Command mode:** operation

.. **Hierarchies**

**Note**

- The optional parameters must match the order in the command

- When stating a sub-address family, an address-family must be specified

- If an address-family is specified, the route or prefix must match the address-family

- When stating 'instance vrf' - support is for **'unicast'** sub-address-family only.

**Parameter table**

+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      |             |
| Parameter             | Description                                                                                                                                                            | Range                | Default     |
+=======================+========================================================================================================================================================================+======================+=============+
|                       |                                                                                                                                                                        |                      |             |
| vrf-name              | Clears only the specified VRF routes                                                                                                                                   | 1..255 characters    | \ -         |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      |             |
| neighbor-address      | Clears a specific neighbor                                                                                                                                             | A.B.C.D              | \ -         |
|                       |                                                                                                                                                                        |                      |             |
|                       |                                                                                                                                                                        | xx:xx::xx:xx         |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      |             |
| address-family        | Clears only the specific address-family routes                                                                                                                         | IPv4                 | \ -         |
|                       |                                                                                                                                                                        |                      |             |
|                       |                                                                                                                                                                        | IPv6                 |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      |             |
| sub-address-family    | Clears neighbors for the specified sub-address family indicator (SAFI). When stating the sub-address-family, address-family and update-direction must be specified.    | unicast              | \ -         |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      |             |
| route                 | The route for which to clear dampening information. The route address must match the address-family                                                                    | A.B.C.D              | \ -         |
|                       |                                                                                                                                                                        |                      |             |
|                       |                                                                                                                                                                        | xx:xx::xx:xx         |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                       |                                                                                                                                                                        |                      |             |
| prefix                | The prefix for which to clear dampening   information. The prefix address must match the address-family                                                                | A.B.C.D/x            | \ -         |
|                       |                                                                                                                                                                        |                      |             |
|                       |                                                                                                                                                                        | xx:xx::xx:xx/x       |             |
+-----------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# clear bgp dampening

	dnRouter# clear bgp dampening ipv4
	dnRouter# clear bgp dampening ipv4 unicast
	dnRouter# clear bgp dampening ipv4 unicast route 1.1.1.1
	dnRouter# clear bgp dampening ipv4 prefix 1.2.0.0/16
	dnRouter# clear bgp dampening ipv4 vpn neighbor 2.2.2.2

	dnRouter# clear bgp dampening ipv6 unicast route 2:2::2:2
	dnRouter# clear bgp dampening ipv6 prefix 2:2::2:0/32
	dnRouter# clear bgp dampening ipv6 vpn neighbor 2.2.2.2

	dnRouter# clear bgp dampening route 1.1.1.1
	dnRouter# clear bgp dampening prefix 1.2.0.0/16
	dnRouter# clear bgp dampening neighbor 2.2.2.2

	dnRouter# clear bgp instance vrf A dampening
	dnRouter# clear bgp instance vrf A dampening ipv4
	dnRouter# clear bgp instance vrf A dampening ipv4 unicast
	dnRouter# clear bgp instance vrf A dampening ipv4 unicast route 1.1.1.1
	dnRouter# clear bgp instance vrf A dampening ipv4 prefix 1.2.0.0/16



.. **Help line:**


**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 6.0       | Command introduced    |
+-----------+-----------------------+