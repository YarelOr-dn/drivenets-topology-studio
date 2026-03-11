interfaces console-ncp admin-state
----------------------------------

**Minimum user role:** operator

To enable/disable the NCP's console interface:


**Command mode:** config

**Hierarchies**

- interfaces

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
	dnRouter(cfg-if)# console-ncp-0/0 
	dnRouter(cfg-if-console-ncp-0/0)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

	dnRouter(cfg-if-console-ncp-0/0)# no admin-state


.. **Help line:** Configure console-ncp-<node-id>/0 serial interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+
