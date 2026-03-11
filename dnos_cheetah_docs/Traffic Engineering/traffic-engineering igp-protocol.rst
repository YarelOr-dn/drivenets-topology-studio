traffic-engineering igp-protocol
--------------------------------

**Minimum user role:** operator

You can use the following to configure the default IGP protocol to be used for CSPF path calculations in RSVP-TE tunnels.

To set the IGP protocol to be used for path calculations:


**Command syntax: igp-protocol [igp-protocol]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Note**

- When configured it will affect newly configured RSVP-TE tunnels only.

**Parameter table**

+-----------------+----------------------------------------------------------------+-----------+-------------+
|                 |                                                                |           |             |
| Parameter       | Description                                                    | Range     | Default     |
+=================+================================================================+===========+=============+
|                 |                                                                |           |             |
| igp-protocol    | The type of IGP protocol to be used for path   calculations    | ISIS      | ISIS        |
|                 |                                                                |           |             |
|                 |                                                                | OSPF      |             |
+-----------------+----------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering
	dnRouter(cfg-protocols-mpls-te)# igp-protocol ospf

	dnRouter(cfg-protocols-mpls-te)# igp-protocol isis


**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-protocols-mpls-te)# no igp-protocol


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.1        | Command introduced    |
+-------------+-----------------------+