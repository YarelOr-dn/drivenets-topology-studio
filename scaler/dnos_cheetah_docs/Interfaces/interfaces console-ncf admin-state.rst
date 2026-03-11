interfaces console-ncf admin-state
----------------------------------

**Minimum user role:** operator

To enable/disable the NCF's console interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the console interface.

**Parameter table**

+----------------+--------------------------------------------------------+-------------+-------------+
|                |                                                        |             |             |
| Parameter      | Description                                            | Range       | Default     |
+================+========================================================+=============+=============+
|                |                                                        |             |             |
| admin-state    | The   administrative state of the console interface    | Enabled     | Enabled     |
|                |                                                        |             |             |
|                |                                                        | Disabled    |             |
+----------------+--------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# console-ncf-0/0 
	dnRouter(cfg-if-console-ncf-0/0)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

	dnRouter(cfg-if-console-ncf-0/0)# no admin-state


.. **Help line:** Configure console-ncf-<node-id>/0 serial interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+
