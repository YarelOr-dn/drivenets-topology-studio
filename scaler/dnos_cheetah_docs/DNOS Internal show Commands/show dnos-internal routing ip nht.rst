show dnos-internal routing ip nht
----------------------------------

**Minimum user role:** viewer

To display RIB Nexthop Tracking Information:

**Command syntax:show dnos-internal routing ip nht** 

**Command mode:** operation

**Example**
::

	dnRouter# show dnos-internal routing ip nht

	1.1.1.1/32
	 (Normal)
	 resolved via 1.1.1.1/32 (rsvp), metric: 10
	 via to-R1
	 Last update: 06-Feb-2023 14:17:06 UTC
	 Client list: bgp(fd 125, bgp, register time: 06-Feb-2023 14:16:59 UTC)
	1.1.1.1/32
	 (Multicast-Intact)
	 resolved via 1.1.1.1/32 (isis), metric: 10
	 10.0.13.1, via bundle-13
	 Last update: 06-Feb-2023 14:17:11 UTC
	 MULTICAST-INTACT reference count: 1
	 Client list: bgp(local, mc_intact, register time: 06-Feb-2023 14:17:11 UTC)
	2.2.2.2/32
	 (Normal)
	 resolved via 2.2.2.2/32 (rsvp), metric: 20
	 via to-R2
	 Last update: 06-Feb-2023 14:17:13 UTC
	 Client list: bgp(fd 125, bgp, register time: 06-Feb-2023 14:16:59 UTC)
	2.2.2.2/32
	 (Multicast-Intact)
	 resolved via 2.2.2.2/32 (isis), metric: 20
	 10.0.13.1, via bundle-13
	 Last update: 06-Feb-2023 14:17:13 UTC
	 MULTICAST-INTACT reference count: 2
	 Client list: bgp(local, mc_intact, register time: 06-Feb-2023 14:17:11 UTC)

.. **Help line:** Displays RIB Nexthop Tracking Information

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.1        | Command introduced    |
+-------------+-----------------------+
