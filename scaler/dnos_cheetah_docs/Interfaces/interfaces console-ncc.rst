interfaces console-ncc
----------------------

**Minimum user role:** operator

To configure the NCC's console serial interface, enter its configuration hierarchy:

**Command syntax: console-ncc-<node-id>/0**

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
| node-id       | The ID o fthe node that you want to configure. | 0, 1      | \-          |
+---------------+------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# console-ncc-0/0 


**Removing Configuration**

To revert the interface configuration to the default values:
::

	dnRouter(cfg-if)# no console-ncc-0/0 


.. **Help line:** configure console-ncc-0/0 serial interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+
