clear msdp statistics
---------------------

**Minimum user role:** operator

You can use the command to clear MSDP peer statistics. You can use the peer-address command to clear the statistics from a specific peer address.

**Command syntax: clear msdp statistics** peer [peer-address]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+-----------------+---------------------------+------------+-------------+
|                 |                           |            |             |
| Parameter       | Description               | Range      | Default     |
+=================+===========================+============+=============+
|                 |                           |            |             |
| peer-address    | IPv4 Multicast address    | A.B.C.D    | \-          |
+-----------------+---------------------------+------------+-------------+

**Example**
::

  dnRouter# clear msdp statistics


.. *Help line:** Clear MSDP statistics

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 12.0        | Command introduced    |
+-------------+-----------------------+