clear isis routes
-----------------

**Minimum user role:** operator

To clear IS-IS routes:

**Command syntax: clear isis** instance [isis-instance-name] **routes** address-family [address-family]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - use "instance [isis-instance-name]" to clear from a specific ISIS instance

 - use "address-family [address-family]" to clear specific address family routes


**Parameter table:**

+-----------------------+-------------------------------------------------------------+---------------------+-------------+
|                       |                                                             |                     |             |
| Parameter             | Description                                                 | Range               | Default     |
+=======================+=============================================================+=====================+=============+
|                       |                                                             |                     |             |
| no parameter          | Clear all IS-IS routes                                      | \-                  | \-          |
+-----------------------+-------------------------------------------------------------+---------------------+-------------+
|                       |                                                             |                     | \-          |
| isis-instance-name    | Clear IS-IS routes from the specified IS-IS instance        | 1..255 characters   |             |
+-----------------------+-------------------------------------------------------------+---------------------+-------------+
|                       |                                                             |                     | \-          |
| address-family        | Clear IS-IS routes for the specified address-family only    | IPv4                |             |
|                       |                                                             |                     |             |
|                       |                                                             | IPv6                |             |
+-----------------------+-------------------------------------------------------------+---------------------+-------------+


**Example**
::

	dnRouter# clear isis routes
	dnRouter# clear isis instance INST_A routes
	dnRouter# clear isis instance INST_A routes addres-family ipv4
	dnRouter# clear isis routes addres-family ipv6


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+
