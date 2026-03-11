show ospf traffic-engineering topology
--------------------------------------

**Minimum user role:** viewer

DIsplays the OSPF traffic-engineering connectivity topology for the router. TE connectivity topology includes the router adjacent neighbors and per-like admin-groups.



**Command syntax: show ospf traffic-engineering topology**

**Command mode:** operational



**Example**
::

	dnRouter# show ospf traffic-engineering topology

	Area 0.0.0.0:

	1.1.1.1:
	-- { 12.3.0.10/0 -> 12.3.0.2/0 } -- 2.2.2.2,     Admin-groups: 0x00000401,     Extended Admin-groups: 0x00000401
	-- { 12.3.0.10/0 -> 12.3.0.3/0 } -- 3.3.3.3,     Admin-groups: 0x00000032,     Extended Admin-groups: 0x00000032
	-- { 13.0.0.10/0 -> 13.0.0.3/0 } -- 3.3.3.3,	 Admin-groups: 0x00000000,     Extended Admin-groups: 0x00000000 0x00000302

	2.2.2.2:
	-- { 12.3.0.2/0 -> 12.3.0.10/0 } -- 1.1.1.1,     Admin-groups: 0x00000001,     Extended Admin-groups: 0x00000001
	-- { 12.3.0.2/0 -> 12.3.0.3/0 } -- 3.3.3.3,     Admin-groups: 0x00000002,     Extended Admin-groups: 0x00000002 0x00FF0A1C 0x00000000 0x00000000 0x01000000
	-- { 24.5.0.2/0 -> 24.5.0.5/0 } -- 5.5.5.5
	-- { 24.5.0.2/0 -> 24.5.0.4/0 } -- 4.4.4.4

	3.3.3.3:
	-- { 12.3.0.3/0 -> 12.3.0.10/0 } -- 1.1.1.1,     Admin-groups: 0x00000002
	-- { 12.3.0.3/0 -> 12.3.0.2/0 } -- 2.2.2.2
	-- { 13.0.0.3/0 -> 13.0.0.10/0 } -- 1.1.1.1
	-- { 35.0.0.3/0 -> 35.0.0.5/0 } -- 5.5.5.5

	4.4.4.4:
	-- { 24.5.0.4/0 -> 24.5.0.5/0 } -- 5.5.5.5,     Admin-groups: 0x0000000C
	-- { 24.5.0.4/0 -> 24.5.0.2/0 } -- 2.2.2.2
	-- { 46.0.0.4/0 -> 46.0.0.6/0 } -- 6.6.6.6

	5.5.5.5:
	-- { 24.5.0.5/0 -> 24.5.0.2/0 } -- 2.2.2.2
	-- { 24.5.0.5/0 -> 24.5.0.4/0 } -- 4.4.4.4,
	-- { 35.0.0.5/0 -> 35.0.0.3/0 } -- 3.3.3.3
	-- { 56.0.0.5/0 -> 56.0.0.6/0 } -- 6.6.6.6

	6.6.6.6:
	-- { 46.0.0.6/0 -> 46.0.0.4/0 } -- 4.4.4.4
	-- { 56.0.0.6/0 -> 56.0.0.5/0 } -- 5.5.5.5

.. **Help line:** Displays ospf traffic-engineering connectivity topology for the router.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 13.1    | Command introduced                  |
+---------+-------------------------------------+
| 19.1    | Extended Admin Groups support added |
+---------+-------------------------------------+
