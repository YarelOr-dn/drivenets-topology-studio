show mpls traffic-engineering admin-group
-----------------------------------------

**Minimum user role:** viewer

To display admin-group values n MPLS traffic-engineering interfaces:



**Command syntax: show mpls traffic-engineering admin-group**

**Command mode:** operational



**Example**
::

	dnRouter# show mpls traffic-engineering admin-group
	
	+-------------+--------------+-----------------------+
	| Interface   | Mask value   | Admin-groups          |
	+-------------+--------------+-----------------------+
	| bundle-1    | 0x1          | RED                   |
	| bundle-2    | 0x2          | GREEN                 |
	| bundle-3    | 0x3          | RED, GREEN            |
	| ge100-1/1/1 | 0x4          | BLUE                  |
	| ge100-2/1/1 | 0x6          | GREEN, BLUE           |
	
	

.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


