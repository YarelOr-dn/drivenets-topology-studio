clear netconf counters
----------------------

**Minimum user role:** operator

To clear active netconf sessions:

**Command syntax: clear netconf counters** [session-id]

**Command mode:** operation

.. **Hierarchies**

**Note**

- A Command without a specific session-id clears counters per system. With sessions-id clears counters per active session. 

**Parameter table:**

+---------------+------------------------------------------+-------------+-------------+
|               |                                          |             |             |
| Parameter     | Description                              | Range       | Default     |
+===============+==========================================+=============+=============+
|               |                                          | 1 - 2^32 -1 |             |
| session-id    | Enter a specific session ID to clear     |             | \-          |
+---------------+------------------------------------------+-------------+-------------+


**Example**
::

	dnRouter# clear netconf counters
	dnRouter# clear netconf counters 776


.. **Help line:** clear netconf counters per specific session and/or per system.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.2        | Command introduced    |
+-------------+-----------------------+