ldp administrative-distance
---------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance. To configure the administrative-distance for LDP:

**Command syntax: administrative-distance [admin-distance]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

-  When reconfiguring the administrative-distance, run clear ldp neighbor.

**Parameter table**

+-------------------+-------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|                   |                                                                                                                               |           |             |
| Parameter         | Description                                                                                                                   | Range     | Default     |
+===================+===============================================================================================================================+===========+=============+
|                   |                                                                                                                               |           |             |
| admin-distance    | Sets the administrative distance for LDP. A value of 255 will cause the router to remove the route from the forwarding table. | 1..255    | 105         |
+-------------------+-------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# administrative-distance 130

**Removing Configuration**

To revert to the default value:
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# no administrative-distance

.. **Help line:** Sets the LDP administrative-distance.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 14.0      | Command introduced    |
+-----------+-----------------------+