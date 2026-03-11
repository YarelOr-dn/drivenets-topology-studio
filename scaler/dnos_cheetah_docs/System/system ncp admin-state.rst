system ncp admin-state
----------------------

**Minimum user role:** operator

To change the admin-state of an NCP:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ncp

**Note**

- When the NCP is disabled, all the datapath interfaces go down and there are no FIBs in the NCP. Mgmt, IPMI and Ctrl interfaces remain unaffected.

.. - no command set the admin-state to its default value

**Parameter table**

+-------------+--------------------------------------+----------+----------+
| Parameter   | Description                          | Range    | Default  |
+=============+======================================+==========+==========+
| admin-state | The administrative state of the NCP. | Enabled  | Disabled |
|             |                                      | Disabled |          |
+-------------+--------------------------------------+----------+----------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncp 0
	dnRouter(cfg-system-ncp-0)# admin-state disabled  
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ncp-0)# no admin-state

.. **Help line:** set the ncp admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


