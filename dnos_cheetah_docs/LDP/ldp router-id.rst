ldp router-id
-------------

**Minimum user role:** operator

To configure the LDP router ID:

**Command syntax: router-id [ipv4-address]**

**Command mode:** config

**Hierarchies**

- protocols LDP

**Note**

- To configure LDP a router-id must be configured. If one is not configured, the default router-id is the router-options router-id. If the router-options router-id is not configured, the highest IPv4 address of any loopback interface will be used.

**Parameter table**

+-----------------+-----------------------------------------------+------------+-------------+
|                 |                                               |            |             |
| Parameter       | Description                                   | Range      | Default     |
+=================+===============================================+============+=============+
|                 |                                               |            |             |
| ipv4-address    | The network ipv4 address of the LDP router    | A.B.C.D    | \-          |
+-----------------+-----------------------------------------------+------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# router-id 100.70.1.45

.. **Help line:** Sets the LDP router-id.

**Command History**

+-------------+------------------------------------------------------------+
|             |                                                            |
| Release     | Modification                                               |
+=============+============================================================+
|             |                                                            |
| 6.0         | Command introduced                                         |
+-------------+------------------------------------------------------------+
|             |                                                            |
| 13.0        | Command syntax   changed from router-id to ipv4-address    |
+-------------+------------------------------------------------------------+