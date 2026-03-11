clear services flow-monitoring cache counters
---------------------------------------------

**Minimum user role:** operator

To clear the flow-monitoring cache counters:

**Command syntax: clear services flow-monitoring cache counters**  ncp [ncp-id]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - "clear services flow-monitoring counters" without parameter, clears counters on all NCPs.

**Parameter table:**

+-----------+-----------------------------------------------------------------------+--------+-------------+
| Parameter | Description                                                           | Range  |             |
|           |                                                                       |        | Default     |
+===========+=======================================================================+========+=============+
| ncp-id    | Clears the flow-monitoring cache counters from the specified NCP only | 0..255 | \-          |
+-----------+-----------------------------------------------------------------------+--------+-------------+


**Example**
::

	dnRouter# clear services flow-monitoring cache counters ncp 5


.. **Help line:** clear flow-monitoring counters.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.4        | Command introduced    |
+-------------+-----------------------+