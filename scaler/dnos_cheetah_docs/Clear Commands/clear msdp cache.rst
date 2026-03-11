clear msdp cache
----------------

**Minimum user role:** operator

You can use the command to clear externally learned MSDP Source-Active (SA) cached entries. You can use the group-address command to clear only those cached MSDP SA entries with a specific group address.

**Command syntax: clear msdp cache** group [group-address]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+------------------+------------------------------------------------------------+---------------------------+-------------+
|                  |                                                            |                           |             |
| Parameter        | Description                                                | Range                     | Default     |
+==================+============================================================+===========================+=============+
|                  |                                                            |                           |             |
| group-address    | To clear cached entries from the specific group address    | IPv4 Multicast address    | \-          |
+------------------+------------------------------------------------------------+---------------------------+-------------+


**Example**
::

  dnRouter# clear msdp cache
  dnRouter# clear msdp cache group 227.34.1.23

.. **Help line:** Clear MSDP SA cache

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 12.0        | Command introduced    |
+-------------+-----------------------+