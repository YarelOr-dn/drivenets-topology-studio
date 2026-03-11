show dnos-internal routing ipv6 color nht
------------------------------------------

**Minimum user role:** viewer

To display RIB IPv6 Color Nexthop Tracking Information:

**Command syntax:show dnos-internal routing ipv6 color nht** 

**Command mode:** operation

**Example**
::

	dnRouter# show dnos-internal routing ipv6 color nht

	4444::4444/128 colors: 3
	 (Normal)
	 resolved via 4444::4444/128 <c> 3 (isis-sr), metric: 20
	 fe80::7054:69ff:fe94:5f2d, label 18304, via bundle-12
	 Last update: 23-Feb-2023 08:27:14 UTC
	 Client list: bgp(fd 89, bgp, register time: 23-Feb-2023 08:27:14 UTC)
	5555::5555/128 colors: 6 4
	 (Normal)
	 resolved via 5555::5555/128 <c> 4 (isis-sr), metric: 20
	 fe80::64d6:beff:fe88:7fe5, label 18405, via bundle-13
	 Last update: 23-Feb-2023 08:27:15 UTC
	 Client list: bgp(fd 89, bgp, register time: 23-Feb-2023 08:27:15 UTC)
	8888::8888/128 colors: 4 3
	 (Normal)
	 resolved via 8888::8888/128 <c> 4 (isis-sr), metric: 30
	 fe80::48ad:4aff:fe9a:be0a, label 18408, via bundle-13
	 Last update: 23-Feb-2023 08:27:16 UTC
	 Client list: bgp(fd 89, bgp, register time: 23-Feb-2023 08:27:16 UTC)

.. **Help line:** Displays RIB IPv6 Color Nexthop Tracking Information

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.1        | Command introduced    |
+-------------+-----------------------+
