interfaces ipmi-ncf admin-state
-------------------------------

**Minimum user role:** operator

To configure the ipmi-ncf-0/0 interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the ipmi-ncf interface.


**Parameter table**

+----------------+---------------------------------------------------+-------------+-------------+
|                |                                                   |             |             |
| Parameter      | Description                                       | Range       | Default     |
+================+===================================================+=============+=============+
|                |                                                   |             |             |
| admin-state    | Set the administrative state of the interface.    | Enabled     | Enabled     |
|                |                                                   |             |             |
|                |                                                   | Disabled    |             |
+----------------+---------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# ipmi-ncf-0/0 
	dnRouter(cfg-if-ipmi-ncf-0/0)# admin-state disabled


**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-if)# no ipmi-ncf-0/0 


.. **Help line:** Configure ipmi-ncf-0/0 interface

**Command History**

+-------------+---------------------------------------------+
|             |                                             |
| Release     | Modification                                |
+=============+=============================================+
|             |                                             |
| 11.0        | Command introduced                          |
+-------------+---------------------------------------------+
