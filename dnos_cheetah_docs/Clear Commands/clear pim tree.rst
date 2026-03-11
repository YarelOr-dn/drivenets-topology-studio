clear pim tree
--------------

**Minimum user role:** operator

You can use the command to clear all dynamically-signaled or data-driven PIM tree entries.
When group-address command is indicated, all the PIM tree entries with the related group address will be cleared.
The command clears all the PIM tree dynamic or data driven tree states (statically created entries or PIM SM static entries are not cleared unless the related static RP range or IGMP Join are deleted).

**Command syntax: clear pim tree** group [group-address] source [source-address]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+----------------+----------------------------------------------------------------------------+-------------+---------+
| Parameter      | Description                                                                | Range       | Default |
+================+============================================================================+=============+=========+
| group-address  | Clears PIM tree entries for the specified group address or prefix          | A.B.C.D     | \-      |
|                |                                                                            | A.B.C.D/M   |         |
+----------------+----------------------------------------------------------------------------+-------------+---------+
| source-address | Clears PIM tree entries for the specified source address                   | A.B.C.D     | \-      |
+----------------+----------------------------------------------------------------------------+-------------+---------+


**Example**
::

  dnRouter# clear pim tree
  dnRouter# clear pim tree 227.1.1.1


.. **Help line:** Clear PIM dynamic Tree entries

**Command History**

+-------------+--------------------------------+
| Release     | Modification                   |
+=============+================================+
| 12.0        | Command introduced             |
+-------------+--------------------------------+
| 16.2        | Added source-address parameter |
+-------------+--------------------------------+
