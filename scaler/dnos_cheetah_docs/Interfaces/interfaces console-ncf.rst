interfaces console-ncf
----------------------

**Minimum user role:** operator

To configure the NCP's console serial interface, enter its configuration hierarchy:

**Command syntax: console-ncf-<node-id>/0**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the console interface.

**Parameter table**

+---------------+------------------------------------------------+-----------+-------------+
|               |                                                |           |             |
| Parameter     | Description                                    | Range     | Default     |
+===============+================================================+===========+=============+
|               |                                                |           |             |
| node-id       | The ID o fthe node that you want to configure. | 0..12     | \-          |
+---------------+------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# console-ncf-0/0 


**Removing Configuration**

To revert the interface configuration to the default values:
::

	dnRouter(cfg-if)# no console-ncf-0/0 


.. **Help line:** configure console-ncf-<node-id>/0 serial interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+
