traffic-engineering diffserv-te admin-state
-------------------------------------------

**Minimum user role:** operator

You can enable or disable DiffServ-te on the system. When disabled, any DiffServ-te configuration will not apply and no DiffServ-te tunnel (whether head, tail, or transit) will be established. When enabled, you can set different levels of service and bandwidth to different class types. Non DiffServ-te path requests will be regarded as class 0.

To enable/disable diffserve-te:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering diffserv-te

**Note**

- Changing the admin-state will reset all tunnels (head, tail, and transit) in a break before make fashion.

**Parameter table**

+----------------+-----------------------------------------------------------+-------------+-------------+
|                |                                                           |             |             |
| Parameter      | Description                                               | Range       | Default     |
+================+===========================================================+=============+=============+
|                |                                                           |             |             |
| admin-state    | The administrative state of diffserv-te in the system.    | Enabled     | Disabled    |
|                |                                                           |             |             |
|                |                                                           | Disabled    |             |
+----------------+-----------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# diffserv-te
	dnRouter(cfg-mpls-te-diffserv)# admin-state enabled

**Removing Configuration**

To revert to the default state:
::

	dnRouter(cfg-mpls-te-diffserv)# no admin-state


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+