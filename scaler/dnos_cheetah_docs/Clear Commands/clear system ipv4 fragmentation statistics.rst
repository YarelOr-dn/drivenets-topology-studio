clear system ipv4 fragmentation statistics
------------------------------------------

**Minimum user role:** operator

Clears all IPv4 fragmentation statistics displayed by the **show system ipv4 fragmentation statistics** command.

To clear ipv4 fragmentation statistics counters:


**Command syntax: clear system ipv4 fragmentation statistics** ncp [ncp-id]

**Command mode:** operation

.. **Hierarchies**

**Note**

When no NCP-id is provided the IPv4 fragmentation statistics of all NCPs are cleared.

**Parameter table**

+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|               |                                                                                                                                                      |           |             |
| Parameter     | Description                                                                                                                                          | Range     | Default     |
+===============+======================================================================================================================================================+===========+=============+
|               |                                                                                                                                                      |           |             |
| ncp-id        | Clears the fragmentation statistics counters for the specified NCP only. If you do not specify an NCP, the counters for all NCPs will be cleared.    | 0..191    | \-          |
+---------------+------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+


**Example**
::

	dnRouter# clear system ipv4 fragmentation statistics ncp 5
	dnRouter# clear system ipv4 fragmentation statistics


.. **Help line:** Clears ipv4 fragmentation statistics displayed by show system ipv4 fragmentation statistics.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.1        | Command introduced    |
+-------------+-----------------------+