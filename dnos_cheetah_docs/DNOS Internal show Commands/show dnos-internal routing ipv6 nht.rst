show dnos-internal routing ipv6 nht
-----------------------------------

**Minimum user role:** viewer

To display RIB Nexthop-OID for IPv6 next-hops:

**Command syntax:show dnos-internal routing ipv6 nht** 

**Command mode:** operation

**Example**
::

	dnRouter# show dnos-internal routing ipv6 nht
	2001:5:3:64::1/128
	 resolved via connected
	 is directly connected, bundle-2.2000
	 Last update: Mon Sep  9 23:50:22 2019
	 Client list: bgp(fd 79, register time: Mon Sep  9 23:50:22 2019)
	2001:5:3:64::3/128
	 resolved via connected
	 is directly connected, bundle-2.2001
	 Last update: Mon Sep  9 23:50:21 2019
	 Client list: bgp(fd 79, register time: Mon Sep  9 23:50:21 2019)
	2001:5:3:65::1/128
	 resolved via connected
	 is directly connected, bundle-2.2002
	 Last update: Mon Sep  9 23:50:19 2019
	 Client list: bgp(fd 79, register time: Mon Sep  9 23:50:19 2019)
	2001:5:3:65::3/128
	 resolved via connected
	 is directly connected, bundle-2.2003
	 Last update: Mon Sep  9 23:50:18 2019
	 Client list: bgp(fd 79, register time: Mon Sep  9 23:50:18 2019)

.. **Help line:** Displays RIB Nexthop-OID

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+


