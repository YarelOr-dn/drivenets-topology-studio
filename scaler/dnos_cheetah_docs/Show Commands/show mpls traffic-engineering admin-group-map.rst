show mpls traffic-engineering admin-group-map
---------------------------------------------

**Minimum user role:** viewer

To display the mapping of admin-groups to bit-position:



**Command syntax: show mpls traffic-engineering admin-group-map**

**Command mode:** operational



**Note**

- See mpls traffic-engineering admin-group-map for information on admin-group-maps.



**Example**
::

	dnRouter# show mpls traffic-engineering admin-group-map
	
	+------------------+--------------+-------------------+
	| Admin-group name | Bit-position | Admin-group value |
	+------------------+--------------+-------------------+
	| RED              | 0            | 0x1               |
	| GREEN            | 1            | 0x2               |
	| BLUE             | 2            | 0x4               |
	| BLACK            | 31           | 0x80000000        |

.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+

