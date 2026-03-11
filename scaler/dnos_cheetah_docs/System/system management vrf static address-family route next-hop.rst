system management static address-family route next-hop
------------------------------------------------------

**Minimum user role:** operator

Configure a static route for the mgmt0 interface. mgmt0 is the out-of-band management interface and is not part of any traffic forwarding VRF.

To configure a static route for the OOB management interface (mgmt0):

**Command syntax: route [ip-prefix] next-hop [gateway]**

**Command mode:** config

**Hierarchies**

- system management static address-family


**Note**

- Static routes to mgmt0 VRF ignores admin-distance values and all routes will be installed.

.. -  [ip-prefix] & [gateway] address type must match the route ip address

	-  "no [ip-prefix]" removes all static routes with [prefix] destination.

	-  "no [ip-prefix] next-hop [gateway]" removes the specific prefix&gateway entry.

	-  Static route to mgmt0 VRF ignores admin-distance value. All routes will be installed

**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| Parameter   | Description                                                                                                                                                                                                                                        | Range             | Default |
+=============+====================================================================================================================================================================================================================================================+===================+=========+
| ip-prefix   | The destination IPv4 or IPv6 prefix.                                                                                                                                                                                                               | A.B.C.D/x         | \-      |
|             | In IPv4-unicast configuration mode you can only set IPv4 destination prefixes and in IPv6-unicast configuration mode you can only set IPv6 destination prefixes.                                                                                   | x:x::x:x/x        |         |
|             | When setting a non /32 prefix, the route installed is the matching subnet network address. For example, for route 192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be 192.168.1.192/26. The same applies for IPv6 prefixes. |                   |         |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| description | Provide a description for the route.                                                                                                                                                                                                               | 1..255 characters | \-      |
|             | Enter free-text description with spaces in between quotation marks. If you do not use quotation marks, do not use spaces. For example:                                                                                                             |                   |         |
|             | ... description "My long description"                                                                                                                                                                                                              |                   |         |
|             | ... description My_long_description                                                                                                                                                                                                                |                   |         |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| next-hop    | The gateway IPv4 or IPv6 address for the prefix.                                                                                                                                                                                                   | A.B.C.D           | \-      |
|             | In IPv4-unicast configuration mode you can only set IPv4 next hops and in IPv6-unicast configuration mode you can only set IPv6 next hops.                                                                                                         | x:x::x:x          |         |
|             | You can set multiple IP next hops for the same route.                                                                                                                                                                                              |                   |         |
|             | The next-hop address must be different from the route address.                                                                                                                                                                                     |                   |         |
+-------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static
	dnRouter(cfg-mgmt-vrf-static)# address-family ipv4
	dnRouter(cfg-vrf-static-ipv4)# route 10.0.0.0/24 next-hop 192.168.0.1
	dnRouter(cfg-vrf-static-ipv4)# route 10.0.0.0/24 next-hop 192.150.1.4

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# management
	dnRouter(cfg-system-mgmt)# vrf mgmt0
	dnRouter(cfg-system-mgmt-vrf)# static
	dnRouter(cfg-mgmt-vrf-static)# address-family ipv6
	dnRouter(cfg-vrf-static-ipv6)# route 2001:1111::0/124 next-hop abde::1
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-vrf-static-ipv4)# no route 10.0.0.0/24 next-hop 192.150.1.4
	dnRouter(cfg-vrf-static-ipv4)# no route 10.0.0.0/24


**Command History**

+---------+------------------------+
| Release | Modification           |
+=========+========================+
| 10.0    | Command introduced     |
+---------+------------------------+
| 13.0    | Command syntax updated |
+---------+------------------------+


