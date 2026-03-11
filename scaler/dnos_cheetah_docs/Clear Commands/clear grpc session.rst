clear grpc session
------------------

**Minimum user role:** operator

To kill gRPC sessions:

**Command syntax: clear grpc session** [session-id]

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


	dnRouter# clear grpc session
	dnRouter# clear grpc session 776


.. **Help line:** kill specific active or all active grpc sessions.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+