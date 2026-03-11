system info
-----------

**Minimum user role:** operator

You can configure identifying information about the router by entering system info configuration mode:

**Command syntax: parameter [parameter-value]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- Notice the change in prompt from dnRouter(cfg-system)# to dnRouter(cfg-system-info)# (system info configuration mode).

.. - no command reverts the system info parameter to its default value

**Parameter table**

+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Parameter           | Description                                                                                                                        | Default                        |
+=====================+====================================================================================================================================+================================+
| Description         | Text field providing a general description of the system                                                                           | DriveNets Network Cloud Router |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Location            | Text field indicating the physical location of the router                                                                          | \-                             |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Floor               | Text field indicating the floor where the rack is located                                                                          | \-                             |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Rack                | Text field indicating the name of the rack where the router is installed                                                           | \-                             |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Contact             | Text field specifying whom to contact about the system (name, email, telephone number).                                            | support@drivenets.com          |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Fabric-min-links    | The number of links below which the NCP will become unavailable.                                                                   | 7                              |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| NCC switchovers     | The number of times that a switchover to the redundant NCC occurred. The switchover counter resets when performing a system reset. | Integer                        |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| Last NCC switchover | The reason for the last NCC switchover                                                                                             | \-                             |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+
| BGP NSR             | The state of the NSR function                                                                                                      | \-                             |
+---------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# info
	dnRouter(cfg-system-info)# description Drivenets virtual Router
	dnRouter(cfg-system-info)# location Israel
	dnRouter(cfg-system-info)# floor FirstFloor
	dnRouter(cfg-system-info)# rack A01
	dnRouter(cfg-system-info)# contact support@drivenets.com





**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-system)# no info
	dnRouter(cfg-system-info)# no description
	dnRouter(cfg-system-info)# no location
	dnRouter(cfg-system-info)# no floor
	dnRouter(cfg-system-info)# no rack
	dnRouter(cfg-system-info)# no contact

.. **Help line:** Configure system general information

**Command History**

+---------+--------------------------------------+
| Release | Modification                         |
+=========+======================================+
| 6.0     | Command introduced for new hierarchy |
+---------+--------------------------------------+
