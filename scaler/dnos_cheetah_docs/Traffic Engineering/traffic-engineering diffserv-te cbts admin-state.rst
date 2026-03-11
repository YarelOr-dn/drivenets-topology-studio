traffic-engineering diffserv-te cbts admin-state
------------------------------------------------

**Minimum user role:** operator

When enabled with diffserv-te enabled, traffic is forwarded to tunnels according to class of service-to-tunnel mapping. See "mpls traffic-engineering diffserv-te cbts".

To enable CBTS forwarding:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering diffserv-te cbts

**Parameter table**

+----------------+--------------------------------------------------+-------------+-------------+
|                |                                                  |             |             |
| Parameter      | Description                                      | Range       | Default     |
+================+==================================================+=============+=============+
|                |                                                  |             |             |
| admin-state    | The administrative state of the CBTS feature.    | Enabled     | Disabled    |
|                |                                                  |             |             |
|                |                                                  | Disabled    |             |
+----------------+--------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# diffserv-te
	dnRouter(cfg-mpls-te-diffserv)# cbts
	dnRouter(cfg-te-diffserv-cbts)# admin-state enabled

**Removing Configuration**

To revert to the default state:
::

	dnRouter(cfg-te-diffserv-cbts)# no admin-state 


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+