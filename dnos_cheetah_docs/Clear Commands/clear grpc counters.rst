clear grpc counters
-------------------

**Minimum user role:** operator

To clear grpc counters per specific session and/or per system:

**Command syntax: clear grpc counters** [session-id]

**Command mode:** operation

.. **Hierarchies**

**Note**

- A command without a specific session-id clears counters per all active sessions and per system.


**Parameter table:**

+------------+--------------------------------+---------------+--------------+
| Parameter  |        Description             |   Range       |Default value |
+============+================================+===============+==============+
| session-id | The id of the specific session | 1..65535      | \-           |
+------------+--------------------------------+---------------+--------------+

**Example**
::

	dnRouter# clear grpc counters
	dnRouter# clear grpc counters 776

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+