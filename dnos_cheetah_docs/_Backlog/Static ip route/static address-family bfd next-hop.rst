static address-family bfd next-hop
----------------------------------

**Minimum user role:** operator

You can enable BFD for next-hop protection of a single hop static route. Static route will be valid for FIB installation only when BFD is UP.

Once next-hop is used in any of the static routes, a BFD session will be formed to that address in order to protect the next-hop reachability. You can configure multiple BFD next-hops, each with it's own bfd session parameters:

-	type - the next-hop type to define the required BFD session type. A single-hop type is for a directly-connected next-hop.

-	admin-state - enable a BFD session. When admin-state is disabled, the bfd session is removed (not kept in admin-down).

-	min-tx - sets the bfd minimum transmit interval

-	min-rx - sets the bfd minimum receive interval

-	multiplier - sets the bfd multiplier.

To configure BFD for next-hop protection:

**Command syntax: next-hop [ip-address] [type]** admin-state [admin-state] min-rx [min-rx] min-tx [min-tx] multiplier [multiplier]

**Command mode:** config

**Hierarchies**

- protocols static address-family bfd

**Parameter table**

+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------+-------------+
|                |                                                                                                                                                                                                |                                                |             |
| Parameter      | Description                                                                                                                                                                                    | Values                                         | Default     |
+================+================================================================================================================================================================================================+================================================+=============+
|                |                                                                                                                                                                                                |                                                |             |
| ip address     | The IP address of the next-hop                                                                                                                                                                 | A.B.C.D                                        | \-          |
|                |                                                                                                                                                                                                |    xx:xx::xx:xx                                |             |
|                |                                                                                                                                                                                                |    Must comply with relative address-family    |             |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------+-------------+
|                |                                                                                                                                                                                                |                                                |             |
| type           | The type of static route                                                                                                                                                                       | single-hop                                     | \-          |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------+-------------+
|                |                                                                                                                                                                                                |                                                |             |
| admin-state    | Enable a BFD session                                                                                                                                                                           | Enabled                                        |             |
|                |                                                                                                                                                                                                |                                                |             |
|                |                                                                                                                                                                                                | disabled                                       |             |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------+-------------+
|                |                                                                                                                                                                                                |                                                |             |
| min-tx         | The interval (in msec) in which a BFD packet is   expected to be transmitted.                                                                                                                  | 5..1700 milliseconds                           | 300         |
|                |                                                                                                                                                                                                |                                                |             |
|                | Due to hardware limitation, the maximum   supported transmit rate is 1700 msec. A negotiated transmit interval higher   than 1700 msec will result in an actual transmit rate of 1700 msec.    |                                                |             |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------+-------------+
|                |                                                                                                                                                                                                |                                                |             |
| min-rx         | The interval (in msec) in which a BFD packet is   expected to be received.                                                                                                                     | 5..1700 milliseconds                           | 300         |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------+-------------+
|                |                                                                                                                                                                                                |                                                |             |
| multiplier     | The number of min-rx intervals in which no BFD   packet is received as expected (or the number of missing BFD packets) before   the BFD session goes down.                                     | 2..16                                          | 3           |
+----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)# bfd
	dnRouter(cfg-static-ipv4-bfd)# next-hop 10.173.2.65 single-hop admin-state enabled min-rx 100 min-tx 100 multiplier 5
	dnRouter(cfg-static-ipv4-bfd)# next-hop 10.1.3.1 single-hop admin-state enabled min-rx 50 min-tx 50 multiplier 5


	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-protocols-static-ipv6)# bfd
	dnRouter(cfg-static-ipv6-bfd)# next-hop 2001:3::65 single-hop admin-state enabled
	dnRouter(cfg-static-ipv6-bfd)# next-hop 2001:4::13 single-hop admin-state enabled min-rx 50 min-tx 50 multiplier 5

**Removing Configuration**

To remove BFD protection for the static route:
::

	dnRouter(cfg-static-ipv4-bfd)# no next-hop 10.1.3.1 single-hop
	dnRouter(cfg-static-ipv6-bfd)# no next-hop 2001:3::65 single-hop

To revert a parameter to its default value:
::

	dnRouter(cfg-static-ipv4-bfd)# no next-hop 10.1.3.1 single-hop admin-state enabled min-rx 50


.. **Help line:** static route bfd next-hop configuration

**Command History**

+-------------+--------------------------------------+
|             |                                      |
| Release     | Modification                         |
+=============+======================================+
|             |                                      |
| 12.0        | Command introduced                   |
+-------------+--------------------------------------+
|             |                                      |
| 15.1        | Added support for 5 msec interval    |
+-------------+--------------------------------------+