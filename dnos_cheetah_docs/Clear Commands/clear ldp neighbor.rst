clear ldp neighbor
------------------

**Minimum user role:** operator

To restart the LDP sessions (restart TCP sessions only):

**Command syntax: clear ldp neighbor** [neighbor-address]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - clear ldp neighbor - restart all ldp TCP sessions only

 - clear ldp neighbor [neighbor-address] - restart ldp TCP session to a specific ldp neighbor


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

	dnRouter# clear ldp neighbor
	dnRouter# clear ldp neighbor 7.7.7.7

.. **Help line:** Restart ldp session

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+