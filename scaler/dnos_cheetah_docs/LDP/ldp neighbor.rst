ldp neighbor
------------

**Minimum user role:** operator

Set an LDP neighbor IP address to enter LDP neighbor configuration hierarchy:

**Command syntax: neighbor [ipv4-address]**

**Command mode:** config

**Hierarchies**

- protocols ldp

.. **Note:**

.. - Applies for both connected and targeted neighbors

**Parameter table**

+-----------------+-------------------------------------+------------+-------------+
|                 |                                     |            |             |
| Parameter       | Description                         | Range      | Default     |
+=================+=====================================+============+=============+
|                 |                                     |            |             |
| ipv4-address    | The IPv4 address of the neighbor    | A.B.C.D    | \-          |
+-----------------+-------------------------------------+------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# neighbor 21.1.34.1
	dnRouter(cfg-protocols-ldp-neighbor)#

**Removing Configuration**

To delete the configuration for the specified neighbor:
::

	dnRouter(cfg-protocols-ldp)# no neighbor 21.1.34.1

.. **Help line:** Enters per neighbor configuration hierarchy.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 13.0      | Command introduced    |
+-----------+-----------------------+