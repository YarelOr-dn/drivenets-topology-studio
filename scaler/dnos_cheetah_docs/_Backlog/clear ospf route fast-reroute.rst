clear ospf route fast-reroute
-----------------------------

**Minimum user role:** operator

The following command clears and re-installs OPSF routes to RIB (for OSPF only - unless fast-reroute is indicated, in order to clear only the LFA routes):

**Command syntax: clear ospf route fast-reroute**

**Command mode:** operation

.. **Hierarchies**

**Note**

- use "fast-reroute" option to clean only LFS routes.

.. **Parameter table:**

**Example**
::

	dnRouter# clear ospf routes fast-reroute

.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.6        | Command introduced    |
+-------------+-----------------------+