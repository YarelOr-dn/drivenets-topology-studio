show interfaces control
-----------------------

**Minimum user role:** viewer

To display a list of control interfaces:



**Command syntax: show interfaces control** [interface-name]

**Command mode:** operational



**Note**

- The uptime on control interfaces is with a "watch" interval of 1 sec.

- The uptime for control interface types is displayed when the interface's operational state is "up". The uptime will return to 0 if the operational state is not "up".

- The operational-state for control interfaces relates to link-state (laser state)

**Parameter table**

+----------------+----------------------------------------------------------------------+--------------+---------+
| Parameter      | Description                                                          | Range        | Default |
+================+======================================================================+==============+=========+
| interface-name | Optionally filter the displayed information to a specific interface. | ctrl-ncp-x/y | \-      |
|                |                                                                      | ctrl-ncf-x/y |         |
|                |                                                                      | ctrl-ncc-x/y |         |
|                |                                                                      | ctrl-ncm-x/y |         |
|                |                                                                      | iceX         |         |
+----------------+----------------------------------------------------------------------+--------------+---------+

The following information is displayed per interface:

+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Field               | Description                                                                                                                                                                                                                                                                                                                     | Options             |
+=====================+=================================================================================================================================================================================================================================================================================================================================+=====================+
| Interface           | The name of the interface                                                                                                                                                                                                                                                                                                       | String              |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Admin               | The administrative status, indicates whether or not the interface is currently enabled. System-down means that the port was shut down by the system (and not by a user).                                                                                                                                                        | Enabled Disabled    |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Operational         | The operational state of the interface, indicates whether the link is currently up or down. For physical interfaces, the operational state relates to the link-state (lasar state) Not-present: the port was pre-provisioned (the NCP is configured but not yet connected to the NCC), or the port was removed due to breakout. | Up Down Not-present |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Uptime              | The amount of time that the interface is up consecutively, with a polling time every 1 second. Uptime resets to zero if the interface is down.                                                                                                                                                                                  | D days, HH:MM:SS    |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Description         | The description provided for the interface.                                                                                                                                                                                                                                                                                     | String              |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| MAC Address         | The MAC Address of the interface. The MAC address is for physical interfaces only.                                                                                                                                                                                                                                              | MAC address format  |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Speed               | The interface's speed                                                                                                                                                                                                                                                                                                           | \-                  |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+
| Duplex              | The directionality of data transmission                                                                                                                                                                                                                                                                                         | Full Half           |
+---------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------+


**Example**
::

	dnRouter# show interfaces control

	| Interface         | Admin    | Operational   | IPv4 Address   | IPv6 Address                   | MTU  |
	+-------------------+----------+---------------+----------------+--------------------------------+------|
	| ctrl-ncc-0/0      | enabled  | up            |                |                                | 9198 |
	| ctrl-ncf-0/0      | enabled  | up            |                |                                | 9198 |
	| ctrl-ncp-1/0      | disabled | down          |                |                                | 9198 |
	| ctrl-ncp-1/1      | enabled  | up            |                |                                | 9198 |
	| ctrl-ncp-2/0      | enabled  | up            |                |                                | 9198 |
	| ctrl-ncp-3/0      |          | not-exist     |                |                                | 9198 |
	| ctrl-ncm-A0/0     | enabled  | up            |                |                                | 9198 |
	| ctrl-ncm-A0/1     | enabled  | up            |                |                                | 9198 |
	| ctrl-ncm-A0/2     | enabled  | up            |                |                                | 9198 |
	| ctrl-ncm-A0/3     | enabled  | up            |                |                                | 9198 |
	| ctrl-ncm-B0/0     | enabled  | up            |                |                                | 9198 |
	| ctrl-ncm-B0/1     | enabled  | up            |                |                                | 9198 |
	| ctrl-ncm-B0/2     | enabled  | up            |                |                                | 9198 |
	| ctrl-ncm-B0/3     | enabled  | up            |                |                                | 9198 |
	| ice0              | enabled  | up            | 192.168.0.1/16 |                                | 9300 |


	dnRouter# show interfaces control ctrl-ncp-0/0

	Interface ctrl-ncp-0/0
	  SNMP ifindex: 1234
	  Admin state: enabled, Operational state: up, Uptime: 0 days, 00:01:30
	  Description: internal control.
	  MAC Address: 7c:fe:90:57:73:10
	  Speed: 10Gbps, Duplex: full
	  L2 MTU: 9198
	  Encapsulation: Ethernet


	dnRouter# show interfaces control ctrl-ncc-0/0

	Interface ctrl-ncc-0/0
	  SNMP ifindex: 54529
	  Admin state: disabled, Operational state: down, Uptime: 0 days, 0:00:00
	  Description:
	  MAC Address: 02:ea:88:44:e4:53
	  Speed: N/A, Duplex: N/A
	  L2 MTU: 9198
	  Encapsulation: Ethernet


	dnRouter# show interfaces control ctrl-ncf-0/0

	Interface ctrl-ncf-0/0
	  SNMP ifindex: 54529
	  Admin state: enabled, Operational state: up, Uptime: 0 days, 21:14:19
	  Description:
	  MAC Address: 02:f1:f4:8b:c1:58
	  Speed: 10Gbps, Duplex: FULL
	  L2 MTU: 9198
	  Encapsulation: Ethernet


	dnRouter# show interfaces control ctrl-ncm-A0/0

	Interface ctrl-ncm-A0/0
	  SNMP ifindex: 1234
	  Admin state: enabled, Operational state: up, Uptime: 0 days, 00:01:30
	  Description: internal control.
	  MAC Address: 7c:fe:90:57:73:10
	  Speed: 10Gbps, Duplex: full
	  L2 MTU: 1548
	  Encapsulation: Ethernet


	dnRouter# show interfaces control ice0

	Interface ice0
	  SNMP ifindex: 1234
	  Admin state: enabled, Operational state: up, Uptime: 0 days, 00:01:30
	  State transitions: 0, Last cleared: 0 days, 00:01:30
	  Description: intra cluster exchange
	  Speed: 100Gbps, Duplex: full
	  L2 MTU: 9300
	  IPv4 Address: 192.168.0.1/16
	  Encapsulation: Ethernet


.. **Help line:** Displays control interface information

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 11.0    | Command introduced               |
+---------+----------------------------------+
| 19.10   | Added support for ICE interfaces |
+---------+----------------------------------+
