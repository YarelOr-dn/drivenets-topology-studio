static address-family route description
---------------------------------------

**Minimum user role:** operator

To enter a description for the static route:

**Command syntax: route [ip-prefix] description [description]**

**Command mode:** config

**Hierarchies**

- protocols static address-family

**Parameter table**

+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                |                                                                                                                                                                                                                                                             |                      |             |
| Parameter      | Description                                                                                                                                                                                                                                                 | Range                | Default     |
+================+=============================================================================================================================================================================================================================================================+======================+=============+
|                |                                                                                                                                                                                                                                                             |                      |             |
| ip-prefix      | The destination IPv4 or IPv6 prefix.                                                                                                                                                                                                                        | A.B.C.D/x            | \-          |
|                |                                                                                                                                                                                                                                                             |                      |             |
|                | In IPv4-unicast configuration mode you can only   set IPv4 destination prefixes and in IPv6-unicast configuration mode you can   only set IPv6 destination prefixes.                                                                                        | x:x::x:x/x           |             |
|                |                                                                                                                                                                                                                                                             |                      |             |
|                | When setting a non /32 prefix, the route   installed is the matching subnet network address. For example, for route   192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be   192.168.1.192/26. The same applies for IPv6 prefixes.    |                      |             |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+
|                |                                                                                                                                                                                                                                                             |                      |             |
| description    | Provide a description for the route.                                                                                                                                                                                                                        | 1..255 characters    | \-          |
|                |                                                                                                                                                                                                                                                             |                      |             |
|                | Enter free-text description with spaces in   between quotation marks. If you do not use quotation marks, do not use   spaces. For example:                                                                                                                  |                      |             |
|                |                                                                                                                                                                                                                                                             |                      |             |
|                | ... description "My long   description"                                                                                                                                                                                                                     |                      |             |
|                |                                                                                                                                                                                                                                                             |                      |             |
|                | ... description   My_long_description                                                                                                                                                                                                                       |                      |             |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv4-unicast
	dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.0/24 description route to cluster 1
	
	
	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# static
	dnRouter(cfg-protocols-static)# address-family ipv6-unicast
	dnRouter(cfg-protocols-static-ipv6)# route 232:16::8:0/96 description MY_DESCRIPTION

**Removing Configuration**

To remove the description for the route:
::

	dnRouter(cfg-protocols-static-ipv4)# no route 172.16.172.0/24 description


.. **Help line:** static route configuration

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+