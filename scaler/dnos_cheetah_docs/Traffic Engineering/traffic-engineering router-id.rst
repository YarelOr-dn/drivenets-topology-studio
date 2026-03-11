traffic-engineering router-id
-----------------------------

**Minimum user role:** operator

You can set a router ID for the OSPF process, or you can use the default router ID. The traffic-engineering router-id must be a re-routable IPv4 unicast address matching one of the DNOS router local addresses.

To set the router ID for traffic-engineering:


**Command syntax: router-id [router-id]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering

**Parameter table**

+---------------+------------------------------------------------------------------------------------------------------------------+------------+----------------------------------------------+
|               |                                                                                                                  |            |                                              |
| Parameter     | Description                                                                                                      | Range      | Value                                        |
+===============+==================================================================================================================+============+==============================================+
|               |                                                                                                                  |            |                                              |
| router-id     | Set the network unique traffic engineering router   ID. This command overrides the configured router identifier. | A.B.C.D    | routing-options router-id, if configured.    |
|               |                                                                                                                  |            |                                              |
|               | The router-id is identical in all IGP instances.                                                                 |            |                                              |
+---------------+------------------------------------------------------------------------------------------------------------------+------------+----------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# router-id 1.1.1.1

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-protocols-mpls-te)#  no router-id


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 9.0         | Command introduced    |
+-------------+-----------------------+