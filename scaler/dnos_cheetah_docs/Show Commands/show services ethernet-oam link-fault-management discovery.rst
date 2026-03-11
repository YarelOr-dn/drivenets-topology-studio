show services ethernet-oam link-fault-management discovery
----------------------------------------------------------

**Minimum user role:** viewer

To display ethernet OAM link fault management sessions:


**Command syntax: show services ethernet-oam link-fault-management discovery** [interface-name]

**Command mode:** operational

..
	**Internal Note**

	-

**Parameter table**

The following information is displayed for each interface in the concentrated table:

+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Parameter             | Description                                                                                                             | Range                                  | Default  |
+=======================+=========================================================================================================================+========================================+==========+
| Interface             | The name of the interface                                                                                               | ge<interface speed>-<A>/<B>/<C>        | \-       |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Admin State           | The administrative status, indicates whether or not the ethernet OAM LFM protocol is currently enabled on the interface | Enabled                                | Disabled |
|                       |                                                                                                                         | Disabled                               |          |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Session State         | The state of the ethernet OAM LFM protocol for the session with the peer                                                | INACTIVE                               | \-       |
|                       |                                                                                                                         | FAULT                                  |          |
|                       |                                                                                                                         | ACTIVE_SEND_LOCAL                      |          |
|                       |                                                                                                                         | PASSIVE_WAIT                           |          |
|                       |                                                                                                                         | SEND_LOCAL_REMOTE                      |          |
|                       |                                                                                                                         | SEND_LOCAL_REMOTE_OK                   |          |
|                       |                                                                                                                         | SEND_ANY                               |          |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Remote MAC Address    | The MAC address of the peer                                                                                             | xx:xx:xx:xx:xx:xx (mac-address format) | \-       |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Remote Vendor         | The Organizationally Unique Identifier of the peer                                                                      | String                                 | \-       |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Local Mode            | The mode of the local ethernet OAM LFM client                                                                           | Active                                 | Active   |
|                       |                                                                                                                         | Passive                                |          |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Remote Mode           | The mode of the remote ethernet OAM LFM client                                                                          | Active                                 | Active   |
|                       |                                                                                                                         | Passive                                |          |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Local Capabilities    | The ethernet OAM LFM capabilities supported by the local device                                                         | Link Events                            | \-       |
|                       |                                                                                                                         | Remote Loopback                        |          |
|                       |                                                                                                                         | Unidirectional Link-fault Detection    |          |
|                       |                                                                                                                         | MIB Variable Retrieval                 |          |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Remote Capabilities   | The ethernet OAM LFM capabilities supported by the peer                                                                 | Link Events                            | \-       |
|                       |                                                                                                                         | Remote Loopback                        |          |
|                       |                                                                                                                         | Unidirectional Link-fault Detection    |          |
|                       |                                                                                                                         | MIB Variable Retrieval                 |          |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Uptime/Downtime       | The amount of time that the ethernet OAM LFM session on the interface is up consecutively                               | D days, HH:MM:SS                       | \-       |
+-----------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+

The following information is displayed for each named interface:

+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Parameter                               | Description                                                                                                             | Range                                  | Default  |
+=========================================+=========================================================================================================================+========================================+==========+
| Interface                               | The name of the interface                                                                                               | ge<interface speed>-<A>/<B>/<C>        | \-       |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Interface operational state             | The operarional status of the interface                                                                                 | Up                                     | \-       |
|                                         |                                                                                                                         | Down                                   |          |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Admin State                             | The administrative status, indicates whether or not the ethernet OAM LFM protocol is currently enabled on the interface | Enabled                                | Disabled |
|                                         |                                                                                                                         | Disabled                               |          |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Uptime/Downtime                         | The amount of time that the ethernet OAM LFM session on the interface is up consecutively                               | D days, HH:MM:SS                       | \-       |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Mode                                    | The mode of the ethernet OAM LFM client                                                                                 | Active                                 | Active   |
|                                         |                                                                                                                         | Passive                                |          |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Session State                           | The state of the ethernet OAM LFM protocol for the session with the peer                                                | INACTIVE                               | \-       |
|                                         |                                                                                                                         | FAULT                                  |          |
|                                         |                                                                                                                         | ACTIVE_SEND_LOCAL                      |          |
|                                         |                                                                                                                         | PASSIVE_WAIT                           |          |
|                                         |                                                                                                                         | SEND_LOCAL_REMOTE                      |          |
|                                         |                                                                                                                         | SEND_LOCAL_REMOTE_OK                   |          |
|                                         |                                                                                                                         | SEND_ANY                               |          |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Status                                  | The operational status of the session                                                                                   | N/A                                    | \-       |
|                                         |                                                                                                                         | Up                                     |          |
|                                         |                                                                                                                         | Down                                   |          |
|                                         |                                                                                                                         | If-down                                |          |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| PDU Revision                            | The current revision of the Information TLV                                                                             | Integer                                | \-       |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| OAM Version                             | The ethernet OAM LFM protocol version supported by the DTE                                                              | Integer                                | \-       |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Maximum OAMPDU Size                     | The largest OAMPDU size, in octets, supported by the DTE                                                                | Integer                                | \-       |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| PDU Interval                            | The time interval between hello packets for an ethernet OAM LFM session                                                 | 100..1000 (in skips of 100ms)          | 1000     |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Connection Timeout                      | The timeout value for an ethernet OAM LFM session                                                                       | 3-10 (seconds)                         | 5        |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Remote MAC Address                      | The MAC address of the peer                                                                                             | xx:xx:xx:xx:xx:xx (mac-address format) | \-       |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Remote Vendor                           | The Organizationally Unique Identifier of the peer                                                                      | String                                 | \-       |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Capabilities                            | The supported ethernet OAM LFM capabilities                                                                             | Link Events                            | \-       |
|                                         |                                                                                                                         | Remote Loopback                        |          |
|                                         |                                                                                                                         | Unidirectional Link-fault Detection    |          |
|                                         |                                                                                                                         | MIB Variable Retrieval                 |          |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Errored Symbol Period Event threshold   | Indicates the threshold for the event to be generated                                                                   | 1..100                                 | 1        |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Errored frame event threshold           | Indicates the threshold for the event to be generated                                                                   | 1..100                                 | 1        |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Errored frame period event threshold    | Indicates the threshold for the event to be generated                                                                   | 1..100                                 | 1        |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+
| Errored frame seconds summary threshold | Indicates the threshold for the event to be generated                                                                   | 1..100                                 | 1        |
+-----------------------------------------+-------------------------------------------------------------------------------------------------------------------------+----------------------------------------+----------+

**Example**
::

	dnRouter# show services ethernet-oam link-fault-management discovery

	Ethernet OAM Link Fault Management sessions:

	Legend: L - Link Events capability, R - Remote Loopback capability, U - Unidirectional Link-fault Detection capability, M - MIB Variable Retrieval capability

	+---------------------+-------------+----------------------+--------------------+---------------------+---------------------+-----------------------------+--------------------+
	| Local Interface     | Admin State | Session State        | Remote MAC Address | Remote Vendor       | Local / Remote Mode | Local / Remote Capabilities | Uptime / Downtime  |
	+=====================+=============+======================+====================+=====================+=====================+=============================+====================+
	| ge100-0/0/0         | enabled     | SEND_LOCAL_REMOTE_OK | 00:01:02:03:04:05  | 00000A (Juniper)    | active / active     | L / L R M                   |                    |
	| ge100-0/0/6         | enabled     | PASSIVE_WAIT         |                    |                     | passive /           | L /                         |                    |
	| ge100-0/0/19        | enabled     | SEND_ANY             | 02:03:04:05:06:07  | 00000B (DriveNets)  | active / passive    | L / L                       | 0 days, 00:12:23   |
	| ge100-0/0/24        | enabled     | SEND_ANY             | 03:04:05:06:07:08  | 00000C (Cisco)      | active / passive    | L / L R U                   | 0 days, 04:34:57   |
	| ge100-0/0/28        | disabled    | INACTIVE             |                    |                     | active /            | L /                         |                    |
	+---------------------+-------------+----------------------+--------------------+---------------------+---------------------+-----------------------------+--------------------+


	dnRouter# show services ethernet-oam link-fault-management discovery ge100-0/0/24

	Interface: ge100-0/0/24
		Interface operational state: up
		Local client:
			Admin state: enabled, Uptime/Downtime: 0 days, 00:12:23
			Mode: active, Session state: SEND_ANY, Status: up
			PDU Revision: 4, OAM Version: 1
			Maximum OAMPDU size: 1500
			PDU interval: 1000 milliseconds, PDU threshold: 3 / Connection timeout: 5 seconds
			Capabilities supported:
				Link Events
					Configured thresholds:
						Errored symbol period event threshold:       1
						Errored frame event threshold:               1
						Errored frame period event threshold:      100
						Errored frame seconds summary threshold:   100

		Remote client:
			MAC Address: 02:03:04:05:06:07
			Vendor (OUI): 00000C (Cisco)
			Mode: passive
			PDU Revision: 2, OAM Version: 1
			Maximum OAMPDU size: 1496
			Capabilities supported:
				Link Events
				Remote Loopback
				Unidirectional Link-fault Detection



.. **Help line:** Display 802.3ah link-OAM sessions

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
