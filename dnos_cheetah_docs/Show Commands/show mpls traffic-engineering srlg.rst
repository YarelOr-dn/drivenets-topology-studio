show mpls traffic-engineering srlg
----------------------------------

**Minimum user role:** viewer

To displays mpls te interfaces by shared risk link group (SRLG):

**Command syntax: show mpls traffic-engineering srlg**

**Command mode:** operational



**Note**

- See mpls traffic-engineering interface srlg-group for information on SRLG.



**Example**
::

	dnRouter# show mpls traffic-engineering srlg
	
	Insatnace 1:
	+-------------+------+
	| Interface   | srlg |
	+-------------+------+
	| bundle-1    | 1    |
	| bundle-2    |      |
	| bundle-3    | 1, 2 |
	| ge100-1/1/1 | 3    |
	| ge100-2/1/1 | 1    |
	

.. **Help line:**

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+

