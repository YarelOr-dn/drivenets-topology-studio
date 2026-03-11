system ncf admin-state
----------------------

**Minimum user role:** operator

To change the admin-state of an NCF:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system ncf


**Note**

- When the NCF is disabled, all the Fabric interfaces go down. Mgmt, IPMI and Ctrl interfaces remain unaffected.

.. - no command set the admin-state to its default value

**Parameter table**

+-------------+--------------------------------------+----------+---------+
| Parameter   | Description                          | Range    | Default |
+=============+======================================+==========+=========+
| admin-state | The administrative state of the NCF. | Enabled  | Enabled |
|             |                                      | Disabled |         |
+-------------+--------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncf 0
	dnRouter(cfg-system-ncf-0)# admin-state disabled  
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system-ncf-0)# no admin-state

.. **Help line:** set the ncf admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


