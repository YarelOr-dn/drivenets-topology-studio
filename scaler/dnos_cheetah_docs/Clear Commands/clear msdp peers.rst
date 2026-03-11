clear msdp peers
----------------

**Minimum user role:** operator

You can use the [peers-address] command to clear a specific peer TCP connection. 

**Command syntax: clear msdp peers** [peer-address]

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

  dnRouter# clear msdp peers
  dnRouter# clear msdp peers 3.3.3.3

.. **Help line:** Clear MSDP peers TCP connections

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 12.0        | Command introduced    |
+-------------+-----------------------+