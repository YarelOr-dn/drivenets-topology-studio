show dnos-internal routing ip color nht
----------------------------------------

**Minimum user role:** viewer

To display RIB Color Nexthop Tracking Information:

**Command syntax:show dnos-internal routing ip color nht** 

**Command mode:** operation

**Example**
::

	dnRouter# show dnos-internal routing ip color nht

	22.22.22.2/32 colors: 7 6 5 4 3 2 1 0
	 (Normal)
	 resolved via 22.22.22.2/32 <c> 6 (sr-te), metric: 10
	 via pol_22.22.22.2_7
	 Last update: 06-Feb-2023 14:05:02 UTC
	 Client list: bgp(fd 128, bgp, register time: 06-Feb-2023 14:05:02 UTC)
	22.22.22.3/32 colors: 7 6 5 4 3 2 1 0
	 (Normal)
	 resolved via 22.22.22.3/32 <c> 7 (sr-te), metric: 10
	 via pol_22.22.22.3_7
	 Last update: 06-Feb-2023 14:05:03 UTC
	 Client list: bgp(fd 128, bgp, register time: 06-Feb-2023 14:05:03 UTC)
	33.33.33.2/32 colors: 7 6 5 4 3 2 1 0
	 (Normal)
	 resolved via 33.33.33.2/32 <c> 7 (sr-te), metric: 10
	 via pol_33.33.33.2_7
	 Last update: 06-Feb-2023 14:05:03 UTC
	 Client list: bgp(fd 128, bgp, register time: 06-Feb-2023 14:05:03 UTC)

.. **Help line:** Displays RIB Color Nexthop Tracking Information

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.1        | Command introduced    |
+-------------+-----------------------+
