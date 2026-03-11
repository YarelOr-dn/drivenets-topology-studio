show services l2-cross-connect
------------------------------

**Minimum user role:** viewer

To display information on L2-cross-connect services:



**Command syntax: show services l2-cross-connect** [xc-name]

**Command mode:** operational



.. 
	**Internal Note**

	- The cross connect oper-state is derived from the service admin-state and both interfaces oper state Service oper state is up IFF ((admin-state == enabled) and (first-interface-oper = up ) and (second-interface-oper = up )) else it is down.

	- When the cross connect oper-state is up the service uptime equals the uptime of the interface with the shorter uptime.

**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------+
| Parameter | Description                                                                                                                               | Range                             |
+===========+===========================================================================================================================================+===================================+
| xc-name   | Displays detailed information on the specific xConnect service. When not specified, a concentrate table of all the services is displayed. | An existing xConnect service name |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------+

For each xConnect service, the following information is displayed:

+-------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Parameter                     | Description                                                                                                                                                                                                                                       | Range              |
+===============================+===================================================================================================================================================================================================================================================+====================+
| L2 cross connect service name | The name of the configured xConnect service                                                                                                                                                                                                       | String             |
+-------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Service admin-state           | The admin-state of the xConnect service                                                                                                                                                                                                           | Enabled            |
|                               |                                                                                                                                                                                                                                                   | Disabled           |
+-------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Service oper-state            | The operational state of the service. The service operation is considered as "up" if the service admin-state is "enabled" and the operational state of both interfaces is "up". Otherwise, the service operational state is considered as "down". | Up                 |
|                               |                                                                                                                                                                                                                                                   | Down               |
+-------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Service interfaces            | The name of the interface associated with the specific xConnect service                                                                                                                                                                           | Existing interface |
+-------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Interface oper-state          | The operational state of the interface associated with the xConnect service                                                                                                                                                                       | Up                 |
|                               |                                                                                                                                                                                                                                                   | Down               |
+-------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Service uptime                | The amount of time that the service has been running. This uptime reflects the most recent uptime of the two interfaces for a service with operational state "up".                                                                                | days, hh:mm:ss     |
+-------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

**Example**
::

	dnRouter# show services l2-cross-connect XC-To-Boston-CRS

	L2 Cross Connect Service: XC-To-Boston-CRS
		Service admin-state: Enabled
		Service oper-state: up
		Service uptime: 0 days, 01:09:57
		Interfaces:
			bundle-100.2      Oper-state: up, uptime: 0 days, 01:09:57
			bundle-200.3      Oper-state: up, uptime: 0 days, 01:23:43


	dnRouter# show services l2-cross-connect

	| L2 Cross connect service name | Service admin-state  | Service Oper-state  | Service interfaces       | Interface Oper-state |
	|-------------------------------+----------------------+---------------------+--------------------------+----------------------+
	|  XC-To-Boston-CRS             | enabled              | down                | bundle-100.2             | up                   |
	|                               |                      |                     | bundle-200.2             | down                 |
	|  XC-To-NewYork-CRS            | enabled              | up                  | ge100-0/0/2.123          | up                   |
	|                               |                      |                     | ge100-0/0/23.3           | up                   |
	|  XC-To-Dallas                 | disabled             | down                | ge100-0/0/13.87          | up                   |
	|                               |                      |                     | bundle-400.21            | up                   |

.. **Help line:** Show l2 cross connect services

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.1    | Command introduced |
+---------+--------------------+


