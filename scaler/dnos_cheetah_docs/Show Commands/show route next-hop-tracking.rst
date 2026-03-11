show route next-hop-tracking
-----------------------------

**Minimum user role:** viewer

To display routing table next hop tracking summary, use the following command:



**Command syntax: show route next-hop-tracking** color **[address-family]** instance vrf [vrf-name]

**Command mode:** operational



.. **Note**

	- use vrf to display routing information for a non-default vrf

**Parameter table**

+----------------+--------------------------------------------------------------------------------------------------------------------+--------+
| Parameter      | Description                                                                                                        | Range  |
+================+====================================================================================================================+========+
| color          | Displays color next-hop-tracking information.                                                                      | \-     |
+----------------+--------------------------------------------------------------------------------------------------------------------+--------+
| address-family | Filter the displayed information to the specified address-family.                                                  | IPv4   |
|                |                                                                                                                    | IPv6   |
+----------------+--------------------------------------------------------------------------------------------------------------------+--------+
| vrf-name       | Filter the displayed information to the specified VRF. If not specified, routes for the default VRF are displayed. | String |
+----------------+--------------------------------------------------------------------------------------------------------------------+--------+


There can be several types of nexthop tracking (type of the nexthop resolution):

- Normal

- Exact match

- Multicast intact

- Multicast

- Tunnel

- Protocol

There can be several types of protocols referencing the next-hop:

- Value

- RSVP

- Static

- Multicast intact



**Example**
::

	dnRouter# show route next-hop-tracking ipv4

	10.0.2.3/32
		(Normal)
		resolved via 10.0.2.0/24 (connected), metric: 0
		is directly connected, b-1.2300
		Last update: Mon Sep 21 14:34:45 2020
		STATIC reference count: 1
		Client list: static(local, register time: Mon Sep 21 14:34:45 2020) bgp(fd 102, register time: Mon Sep 21 14:34:50)
	19.0.0.4/32
		(Normal)
		unresolved
		Last update: Mon Sep 14 23:16:45 2020
		Client list: external(external, register time: Mon Sep 21 14:34:38 2020)


	dnRouter# show route next-hop-tracking ipv4 instance vrf C

	10.0.3.5/32
		(Normal)
		resolved via 10.0.3.0/24 (connected), metric: 0
		is directly connected, b-1.2300
		Last update: Mon Sep 21 14:34:45 2020
		Client list: bgp(fd 94, register time: Mon Sep 21 12:11:00)


	dnRouter# show route next-hop-tracking ipv6

	3450::11/128
		(Normal)
		resolved via 3450::/120 (connected), metric: 0
		is directly connected, b-1.2300
		Last update: Mon Sep 21 14:34:52 2020
		Client list: bgp(fd 102, register time: Mon Sep 21 14:34:52 2020)


	dnRouter# show route next-hop-tracking color ipv4

	2.3.0.1/32 colors: 2300
		(Normal)
		resolved via 2.3.0.1/32 <c> 2300 (sr-te), metric: 20
		via IXIA_DN1_LU
		Last update: 20-Apr-2023 07:30:47 UTC
		Client list: bgp(fd 21, bgp, register time: 20-Apr-2023 07:15:24 UTC)


	dnRouter# show route next-hop-tracking color ipv6

	8888::8888/128 colors: 4 3
		(Normal)
		resolved via 8888::8888/128 <c> 4 (isis-sr), metric: 30
		fe80::48ad:4aff:fe9a:be0a, label 18408, via vdev_13
		Last update: 23-Feb-2023 08:27:16 UTC
		Client list: bgp(fd 132, bgp, register time: 23-Feb-2023 08:27:16 UTC)

.. **Help line:** Displays NHT information


**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 6.0     | Command introduced                                |
+---------+---------------------------------------------------+
| 18.2    | Added color knob to display color NHT information |
+---------+---------------------------------------------------+
