show isis traffic-engineering topology
--------------------------------------

**Minimum user role:** viewer

The IS-IS traffic-engineering topology displays for each node its adjacent neighbors and the link's admin-group.

To display the IS-IS traffic-engineering connectivity topology:

**Command syntax: show isis** instance [isis-instance-name] **traffic-engineering topology** level [level]

**Command mode:** operational



.. **Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when not specified, display information from all isis instances

**Parameter table**

+--------------------+--------------------------------------------------------------------+
| Parameter          | Description                                                        |
+====================+====================================================================+
| No filter          | Displays the entire traffic-engineering topology.                  |
+--------------------+--------------------------------------------------------------------+
| isis-instance-name | Filters the displayed information for the specified IS-IS instance |
+--------------------+--------------------------------------------------------------------+
| level              | selected isis level, level-1 or level-2 to display                 |
+--------------------+--------------------------------------------------------------------+



**Example**
::

	dnRouter# show isis traffic-engineering topology
	level-1:
	level-2:
	1.1.1.1:
	-- { 12.3.0.10/0 -> 12.3.0.2/0 } -- 2.2.2.2, 	Admin-groups: 0x0001
	-- { 12.3.0.10/0 -> 12.3.0.3/0 } -- 3.3.3.3, 	Admin-groups: 0x0002
	-- { 13.0.0.10/0 -> 13.0.0.3/0 } -- 3.3.3.3

	2.2.2.2:
	-- { 12.3.0.2/0 -> 12.3.0.10/0 } -- 1.1.1.1, 	Admin-groups: 0x0001
	-- { 12.3.0.2/0 -> 12.3.0.3/0 } -- 3.3.3.3
	-- { 24.5.0.2/0 -> 24.5.0.5/0 } -- 5.5.5.5
	-- { 24.5.0.2/0 -> 24.5.0.4/0 } -- 4.4.4.4

	3.3.3.3:
	-- { 12.3.0.3/0 -> 12.3.0.10/0 } -- 1.1.1.1, 	Admin-groups: 0x0002
	-- { 12.3.0.3/0 -> 12.3.0.2/0 } -- 2.2.2.2
	-- { 13.0.0.3/0 -> 13.0.0.10/0 } -- 1.1.1.1
	-- { 35.0.0.3/0 -> 35.0.0.5/0 } -- 5.5.5.5

	4.4.4.4:
	-- { 24.5.0.4/0 -> 24.5.0.5/0 } -- 5.5.5.5, 	Admin-groups: 0x000C
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

	dnRouter# show isis instance CORE traffic-engineering topology

	dnRouter# show isis traffic-engineering topology level level-1

.. **Help line:**

**Command History**

+---------+-------------------------------------------+
| Release | Modification                              |
+=========+===========================================+
| 9.0     | Command introduced                        |
+---------+-------------------------------------------+
| 10.0    | Changed syntax from "graph" to "topology" |
+---------+-------------------------------------------+
| 16.2    | Added level filter option                 |
+---------+-------------------------------------------+
