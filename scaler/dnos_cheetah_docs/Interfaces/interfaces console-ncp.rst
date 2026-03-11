interfaces console-ncp
----------------------

**Minimum user role:** operator

To configure the NCP's console serial interface, enter its configuration hierarchy:

**Command syntax: console-ncp-<node-id>/0**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the console interface.

**Parameter table**

+--------------+-----------------------------------------------------+------------------------------+------------+
|              |                                                     |                              |            |
| Parameter    | Description                                         | Range                        | Default    |
+==============+=====================================================+==============================+============+
|              |                                                     |                              |            |
| Node-id      | The ID of the node that you want   to configure.    | 0..47 (per cluster size)     | \-         |
+--------------+-----------------------------------------------------+------------------------------+------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# console-ncp-0/0 


**Removing Configuration**

To revert the interface configuration to the default values:
::

	dnRouter(cfg-if)# no console-ncp-0/0 


.. **Help line:** configure console-ncp-<node-id>/0 serial interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+
