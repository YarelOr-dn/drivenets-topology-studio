traffic-engineering pcep admin-state
------------------------------------

**Minimum user role:** operator

To enable or disable the global PCEP administrative state.

Note: Any PCE admin-state configuration will override this value.


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep

**Parameter table**

+----------------+---------------------------------------------------+-------------+-------------+
|                |                                                   |             |             |
| Parameter      | Description                                       | Range       | Default     |
+================+===================================================+=============+=============+
|                |                                                   |             |             |
| admin-state    | The administrative state of the PCEP protocol.    | Enabled     | Disabled    |
|                |                                                   |             |             |
|                |                                                   | Disabled    |             |
+----------------+---------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# admin-state enabled

**Removing Configuration**

To revert to the default state:
::

	dnRouter(cfg-protocols-mpls-te)# no admin-state


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+