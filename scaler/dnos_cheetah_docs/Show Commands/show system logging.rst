show system logging
-------------------

**Minimum user role:** viewer

The show system logging command displays the configuration of all log files as well as a list of all the configured remote syslog servers (if any). You can filter the information by event, or by syslog servers.

**Command syntax: show system logging** syslog-server \| system-events [event-name]

**Command mode:** operational



.. **Internal Note**

	- if no keywords are specified, both logging files parameters and logging syslog server parameters are presented

	- syslog-server keyword presents list of the configured syslog servers.

	- system-event keyword presents information per system-events

	- for system-event option, if no event-name is specified, all system events are presented

	- for system-event option, if event-name is specified, only specific system-event is presented

	- vrf "default" represents in-band syslog server

	- vrf "mgmt0" represents out-of-band syslog server.

**Parameter table**

The following are the parameters that you can use to filter the output results:

+---------------+-----------------------------------------------------------------------------------------------------+
| Parameter     | Description                                                                                         |
+===============+=====================================================================================================+
| syslog-server | Displays a list of all configured remote syslog servers and their configuration.                    |
+---------------+-----------------------------------------------------------------------------------------------------+
| system-events | Displays information on the specific event or for all events belonging to the specific event-group. |
+---------------+-----------------------------------------------------------------------------------------------------+

If you specify system-events, but do not specify an event-name, then all the events in all the event groups will be displayed.

The following information is displayed on each log server:

+------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter        | Description                                                                                                     | Range                                                                                                                                                                              |
+==================+=================================================================================================================+====================================================================================================================================================================================+
| VRF              | The syslog server management type.                                                                              | default - in-band                                                                                                                                                                  |
|                  |                                                                                                                 | non-default-vrf - out-of-band                                                                                                                                                      |
|                  |                                                                                                                 | mgmt0 - out-of-band                                                                                                                                                                |
+------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Server           | The IPv4/IPv6 address of the syslog-server. See system logging syslog server.                                   | A.B.C.D                                                                                                                                                                            |
|                  |                                                                                                                 | xx:xx::xx:xx                                                                                                                                                                       |
+------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Port             | The port on which the syslog server listens to requests from clients. See system logging syslog server port.    | 1..65535                                                                                                                                                                           |
+------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Protocol         | The protocol based on which system messages are logged. See system logging syslog server protocol.              | TCP                                                                                                                                                                                |
|                  |                                                                                                                 | UDP                                                                                                                                                                                |
+------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Admin-state      | The administrative state of the remote syslog server. See system logging syslog server admin-state              | Enabled                                                                                                                                                                            |
|                  |                                                                                                                 | Disabled                                                                                                                                                                           |
+------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Severity         | The severity to which the system log message belongs. See system logging syslog severity.                       | emergency, alert, critical, error, warning, notice, info, debug, none                                                                                                              |
+------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Facility         | The facility to which the system log message belongs. See system logging syslog facility.                       | kern, user, mail, daemon, auth, syslog, lpr, news, uucp, cron, authpriv, ftp, ntp, security, console, solaris-cron, local0, local1, local2, local3, local4, local5, local6, local7 |
+------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Source-interface | The interface whose IP address will be used as the source IP address for messages sent to remote syslog server. | interface name                                                                                                                                                                     |
+------------------+-----------------------------------------------------------------------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

The following information is displayed on each system-event:

+-------------+----------------------------------------------+
| Parameter   | Description                                  |
+=============+==============================================+
| Name        | The name of the event                        |
+-------------+----------------------------------------------+
| Message     | The exact message displayed for the event    |
+-------------+----------------------------------------------+
| Severity    | The severity of the event:                   |
|             | Emergency (0)                                |
|             | Alert (1)                                    |
|             | Critical (2)                                 |
|             | Error (3)                                    |
|             | Warning (4)                                  |
|             | Notice (5)                                   |
|             | Info (6)                                     |
|             | Debug (7)                                    |
|             | None                                         |
+-------------+----------------------------------------------+
| Event-group | The group with which the event is associated |
+-------------+----------------------------------------------+

The following information is displayed for each log file:

+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter         | Description                                                                                                                                                                        |
+===================+====================================================================================================================================================================================+
| Rotate-files      | The maximum number of log files that the system will create. When the number is reached and the last file is full, the oldest file will be deleted. See system logging file files. |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| File size         | The maximum size of the file. When the size is reached, new logs will be saved in a new file. See system logging file size.                                                        |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Syslog parameters | Displays the configured parameters for the syslog:                                                                                                                                 |
|                   | Facility - see system logging syslog facility                                                                                                                                      |
|                   | Class-of-service - see system logging syslog class-of-service                                                                                                                      |
|                   | Source-interface - see system logging syslog source-interface                                                                                                                      |
|                   | Suppress-list - see system logging syslog suppress-event-list                                                                                                                      |
|                   | Timestamp-format utc-normalize - see system logging syslog timestamp-format utc-normalize                                                                                          |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Event groups      | The event groups that are saved to the log file. See system logging event-group severity.                                                                                          |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show system logging
	
	Logging Files Parameters:
	
	System-event.log
	Rotate-files: 5
	File size: 10 [MB]
	
	Accounting.log
	Rotate-files: 5
	File size: 10 [MB]
	
	
	
	Syslog Parameters:
	Facility: Local7
	Class-of-service: 16
	Source-interface: -
	Suppress-list:
	BGP_NEIGHBOR_ADJACENCY_UP
	BGP_NEIGHBOR_ADJACENCY_DOWN
	Chronological-ordering reorder: disabled
	Chronological-ordering max-delay: 5
	Timestamp-format utc-normalize: enabled
	
	Exported event-groups:
	| Event-groups  | Exported Severity |
	|---------------+-------------------|
	|  bgp          |  warning          |
	|  isis         |  notice           |
	|  rsvp         |  info             |
	|  tcp          |  info             |
	|  bfd          |  info             |
	|  lacp         |  info             |
	|  system       |  critical         |
	

	
	Syslog Server List:

	| VRF        | Server           | Port  | Protocol | Admin-state | Severity | Facility | Source-interface |
	|------------+------------------+-------+----------+-------------+----------|----------|------------------|
	| default    | 1.2.3.4          | 514   | UDP      | Enabled     | warning  | local7   | lo0              |
	| mgmt0      | 192.168.1.2      | 4     | UDP      | Disabled    | info     | local7   | mgmt0            |
	| mgmt0      | 2001:ab12::1     | 500   | UDP      | Disabled    | notice   | local7   | mgmt0            |
	| my_vrf     | 2.3.4.5          | 514   | UDP      | Disabled    | info     | local7   | lo1              |
	
	
	
	dnRouter# show system logging syslog-server
	Syslog Server List:

	| VRF        | Server           | Port  | Protocol | Admin-state | Severity | Facility | Source-interface |
	|------------+------------------+-------+----------+-------------+----------|----------|------------------|
	| default    | 1.2.3.4          | 514   | UDP      | Enabled     | warning  | local7   | lo0              |
	| mgmt0      | 192.168.1.2      | 4     | UDP      | Disabled    | info     | local7   | mgmt0            |
	| mgmt0      | 2001:ab12::1     | 500   | UDP      | Disabled    | notice   | local7   | mgmt0            |
	| my_vrf     | 2.3.4.5          | 514   | UDP      | Disabled    | info     | local7   | lo1              |
	
	
	dnRouter# show system logging system-events SSH_SESSION_TERMINATED
	
	Name: SSH_SESSION_TERMINATED
	Message: SSH session {session_id} (remote host {remote_host}) terminated by user {user_name}
	Severity: NOTICE (5)
	Event-group: Management

	dnRouter# show system logging system-events BGP_IPV4_NEIGHBOR_ADJACENCY_DOWN

	Name: BGP_IPV4_NEIGHBOR_ADJACENCY_DOWN
	Message: For instance {vrf} BGP {as_number}: Neighbor {neighbor_address} adjacency is {bgp_peer_state}, due to {reason}
	Severity: WARNING (4)
	Event-group: BGP
	Presents all supported system event from bgp event-group



	dnRouter# show system logging system-events
	
	Presents all supported system events
	
	
	

.. **Help line:** show system logging


**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 5.1.0   | Command introduced                                         |
+---------+------------------------------------------------------------+
| 6.0     | Updated filter examples                                    |
+---------+------------------------------------------------------------+
| 10.0    | Syntax changed and displayed information                   |
+---------+------------------------------------------------------------+
| 11.5    | Removed event-group from the syntax                        |
+---------+------------------------------------------------------------+
| 13.1    | Added in-band/out-of-band information (via VRF) per server |
+---------+------------------------------------------------------------+
| 15.1    | Added support for IPv6 address family                      |
+---------+------------------------------------------------------------+
| 19.1    | Display per-server source-interface                        |
+---------+------------------------------------------------------------+
