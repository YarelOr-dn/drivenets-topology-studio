clear system icmp unreachable statistics
-----------------------------------------

**Minimum user role:** operator

Clears all ICMP unreachable statistics counters (these are presented by the show system unreachable statistics command. See "show system icmp unreachable statistics".

To clear icmp unreachable statistics counters:

**Command syntax: clear system icmp unreachable statistics** ncp [ncp-id]

**Command mode:** operation

.. **Hierarchies**

.. **Note**


**Parameter table**

+-----------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter | Description                                                                                                                                    |
+===========+================================================================================================================================================+
| ncp-id    | Clear the unreachable statistics counters for the specified NCP only. If you do not specify an NCP, the counters for all NCPs will be cleared. |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# clear system icmp unreachable statistics ncp 5

	dnRouter# clear system icmp unreachable statistics


.. **Help line:** Clears all icmp unreachable statistics counters (presented by show system icmp unreachable statisitics CLI command).


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+