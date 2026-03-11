clear ldp neighbor statistics
-----------------------------

**Minimum user role:** operator

To clear the LDP neighbor statistics:

**Command syntax: clear ldp neighbor** [neighbor-address] **statistics**

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+---------------------+--------------------------------------------------------+------------+-------------+
|                     |                                                        |            |             |
| Parameter           | Description                                            | Range      | Default     |
+=====================+========================================================+============+=============+
|                     |                                                        |            |             |
| neighbor-address    | Restarts LDP TCP session to a specific LDP neighbor    | A.B.C.D    | \-          |
+---------------------+--------------------------------------------------------+------------+-------------+
|                     |                                                        |            |             |
| statistics          | Clears all LDP neighbor statistics                     | \-         | \-          |
+---------------------+--------------------------------------------------------+------------+-------------+

**Example**
::

	dnRouter# clear ldp neighbor statistics
	dnRouter# clear ldp neighbor 7.7.7.7 statistics


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+