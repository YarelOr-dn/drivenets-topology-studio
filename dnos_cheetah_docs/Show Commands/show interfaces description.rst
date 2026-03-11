show interfaces description
---------------------------

**Minimum user role:** viewer

This command is applicable to the following interfaces:

physical interfaces logical interfaces (sub-interfaces) bundle interfaces bundle sub-interfaces loopback interfaces GRE tunnel interfaces

The show interfaces description command displays the description configured for all the interfaces. If you specify an interface name, the output result is filtered to show only the information for the requested interface.

**Command syntax: show interfaces description** [interface-name]

**Command mode:** operational

**Note**

- Specifying an interface filters the displayed information to that interface.


The following information is displayed per interface:

+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+
| Field                      | Description                                                                                                                                                                        | Options     |
+============================+====================================================================================================================================================================================+=============+
| Interface                  | The name of the interface                                                                                                                                                          | String      |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+
| Admin                      | The administrative status, indicates whether or not the interface is currently enabled.                                                                                            | Enabled     |
|                            | System-down means that the port was shut down by the system (and not by a user).                                                                                                   | Disabled    |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+
| Operational                | The operational state of the interface, indicates whether the link is currently up or down. For physical interfaces, the operational state relates to the link-state (lasar state) | Up          |
|                            | Not-present: the port was pre-provisioned (the NCP is configured but not yet connected to the NCC), or the port was removed due to breakout.                                       | Down        |
|                            |                                                                                                                                                                                    | Not-present |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+
| Description                | The description provided for the interface.                                                                                                                                        | String      |
+----------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+


**Example**
::

	dnRouter# show interfaces description

	| Interface       | Admin    | Operational | Description                         |
	+-----------------+----------+-------------+-------------------------------------+
	| bundle-3        | enabled  | up          | 1234567890123456789012345678901234  |
	| ge100-2/1/1     | enabled  | up          | My First 100G Interface             |
	| ge100-2/1/1.100 | disabled | down        | VLAN 100 to Customer                |
	| ge100-3/1/1     | enabled  | up          | First port in lag for customer      |
	| lo1             | disabled | down        | Router-id                           |
	| gre-tunnel-3    | enabled  | up          | GRE_interface_for_ISIS              |
	| irb1            | enabled  | up          | My First IRB Interface              |


	dnRouter# show interfaces description ge100-2/1/1

	| Interface       | Admin    | Operational | Description                         |
	+-----------------+----------+-------------+-------------------------------------+
	| ge100-2/1/1     | enabled  | up          | My First 100G Interface             |


.. **Help line:** Displays configured interface description

**Command History**

+---------+-----------------------------------------------------------------------------------+
| Release | Modification                                                                      |
+=========+===================================================================================+
| 5.1.0   | Command introduced                                                                |
+---------+-----------------------------------------------------------------------------------+
| 6.0     | removed eth0 from the example                                                     |
+---------+-----------------------------------------------------------------------------------+
| 10.0    | Added show parameters (arp-timeout, VID, port-priority, min-links, min-bandwidth) |
+---------+-----------------------------------------------------------------------------------+
| 11.4    | Added support for GRE tunnel                                                      |
+---------+-----------------------------------------------------------------------------------+
| 16.2    | Management bond interface removed                                                 |
+---------+-----------------------------------------------------------------------------------+
| 18.0    | Added support for IRB interfaces                                                  |
+---------+-----------------------------------------------------------------------------------+