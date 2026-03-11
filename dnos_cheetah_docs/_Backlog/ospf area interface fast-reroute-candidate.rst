ospf area interface fast-reroute-candidate 
-------------------------------------------

**Minimum user role:** operator

To set the interface as a valid candidate for loop-free alternate (LFA) calculation:

**Command syntax: fast-reroute-candidate [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf area interface

**Note**

By default, all ospf enabled interfaces are valid candidates for OSPF LFA.

.. - no command returns fast-reroute-candidate to default enabled state

**Parameter table**

+----------------+------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                |                                                                                                                                    |             |             |
| Parameter      | Description                                                                                                                        | Range       | Default     |
+================+====================================================================================================================================+=============+=============+
|                |                                                                                                                                    |             |             |
| admin-state    | Enable/Disable the fast reroute candidate interface. By default, all OSPF enabled interfaces are valid candidates for OSPF LFA.    | Enabled     | Enabled     |
|                |                                                                                                                                    |             |             |
|                |                                                                                                                                    | Disabled    |             |
+----------------+------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ospf
	dnRouter(cfg-protocols-ospf)# area 0
	dnRouter(cfg-protocols-ospf-area)# interface ge100-1/2/1
	dnRouter(cfg-ospf-area-if)#  fast-reroute-candidate enabled
	
	dnRouter(cfg-protocols-ospf-area)# interface bundle-2.1012
	dnRouter(cfg-ospf-area-if)#  fast-reroute-candidate disabled


**Removing Configuration**

To return fast-reroute-candidate to the default value: 
::

	dnRouter(cfg-ospf-area-if)#  no fast-reroute-candidate

.. **Help line:** Set the interface as a candidate for loop-free alternative calculation

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 11.6      | Command introduced    |
+-----------+-----------------------+