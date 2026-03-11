traffic-engineering pcep pce admin-state
----------------------------------------

**Minimum user role:** operator

If the PCC connection fails, the PCC will try to reconnect to the PCE after the retry-interval. The retry-interval is an exponentially increasing timer between 1 second and 64 seconds. After the first failure, the PCC will attempt to reconnect after 1 second. Each connection after that increases the timer by 2 seconds.

To set the availability of the PCE server for delegation:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep pce

**Parameter table**

+----------------+-----------------------------------------------------------------------------------------------------+-------------+--------------------------------------+
|                |                                                                                                     |             |                                      |
| Parameter      | Description                                                                                         | Range       | Default                              |
+================+=====================================================================================================+=============+======================================+
|                |                                                                                                     |             |                                      |
| admin-state    | The administrative state of the PCE server. When   enabled, the PCE is available for delegation.    | Enabled     | traffic-engineering pcep admin-state |
|                |                                                                                                     |             |                                      |
|                |                                                                                                     | Disabled    |                                      |
+----------------+-----------------------------------------------------------------------------------------------------+-------------+--------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# pce priority 3 address 1.1.1.1
	dnRouter(cfg-te-pcep-pce)# admin-state enabled

**Removing Configuration**

To revert to the default state:
::

	dnRouter(cfg-te-pcep-pce)# no admin-state


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+