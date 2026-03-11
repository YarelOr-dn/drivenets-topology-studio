show system details
-------------------

**Minimum user role:** viewer

The show system command displays information on the NCCs and NCPs. There are up to 2 NCCs per NCR, where one is active and the other is stand-by.

After configuring system information, it is recommended that you verify that your configuration and make changes as necessary.

**Command syntax: show system** { details | { { ncc [ncc-id] | ncp [ncp-id] | ncf [ncf-id] | ncm [ncm-id] } container [container-name] process [process-name] process-state [process-state] } | process [process-name]}

**Command mode:** operational



**Note**

- System active uptime denotes the time since the cluster has an active NCC and its state is "up".

- The serial number displayed per node, is the box's hardware S/N from the ODM.

- In a standalone system, the NCC is a virtual node and therefore no serial number is displayed. The box's serial number is reflected on the NCP node.

..
	**Internal Note**

	- Filter combination should only be allowed according for Cluster type. For example, in SA there shouldn't be ncm filter.

	- When there is also sub-status to the NCE, it will be displayed as "Operational status: <status> (<sub-status>)"

**Parameter table**

+----------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| Parameter      | Description                                                                                                                               | Range                                                                     |
+================+===========================================================================================================================================+===========================================================================+
| details        | Displays detailed system information. When combined with container or process, displays detailed information on the container or process. | \-                                                                        |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| ncc-id         | Filters the displayed information to the specified NCC.                                                                                   | 0..1                                                                      |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| ncp-id         | Filters the displayed information to the specified NCP.                                                                                   | 0..max number of NCP per cluster type -1                                  |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| ncf-id         | Filters the displayed information to the specified NCF.                                                                                   | 0..max number of NCF per cluster type -1                                  |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| ncm-id         | Filters the displayed information to the specified NCM.                                                                                   | a0, b0, a1, b1                                                            |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| container-name | Displays information on the specified container only.                                                                                     | A container from the process list that applies to the specified node name |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| process-name   | Displays information on the specified process only.                                                                                       | A process from the process list (see DNOS System Processes)               |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| process-state  | Displays information on entities matching the specified state.                                                                            | running                                                                   |
|                |                                                                                                                                           | down                                                                      |
|                |                                                                                                                                           | failed                                                                    |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+

The following information is displayed on the system:

+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Parameter            | Description                                                                                                                        | Default                                                |
+======================+====================================================================================================================================+========================================================+
| System Name          | The system name is given automatically during commissioning.                                                                       | dnRouter                                               |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| System-ID            | The system identification (a 16 bytes hex value) which is assigned by the system at creation.                                      | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| System Type          | The type of NCR.                                                                                                                   | - SA-40C                                               |
|                      |                                                                                                                                    | - SA-10CD                                              |
|                      |                                                                                                                                    | - CL-16                                                |
|                      |                                                                                                                                    | - CL-32                                                |
|                      |                                                                                                                                    | - CL-48                                                |
|                      |                                                                                                                                    | - CL-51                                                |
|                      |                                                                                                                                    | - CL-64                                                |
|                      |                                                                                                                                    | - CL-76                                                |
|                      |                                                                                                                                    | - CL-96                                                |
|                      |                                                                                                                                    | - CL-153                                               |
|                      |                                                                                                                                    | - CL-192                                               |
|                      |                                                                                                                                    | - CL-409                                               |
|                      |                                                                                                                                    | - CL-AI-8K-400G                                        |
|                      |                                                                                                                                    | - AI-256-400G-2                                        |
|                      |                                                                                                                                    | - AI-72-800G-2                                         |
|                      |                                                                                                                                    | - AI-8192-400G-2                                       |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Family               | The product family.                                                                                                                | NCR                                                    |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Enterprise-ID        | The enterprise identification.                                                                                                     | 49739                                                  |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Description          | Text field providing a general description of the system.                                                                          | DriveNets Network Cloud Router                         |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| System status        | The operational status of the system.                                                                                              | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| System Start Time    | The time stamp when the system came up.                                                                                            | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| System Uptime        | The total time that the system is running (days:hours:min:sec).                                                                    | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| System Boot Uptime   | The time since the last boot.                                                                                                      | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Version              | The software version.                                                                                                              | DNOS [x.x.x] build [x], Copyright © 2022 DriveNets Ltd |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Location             | Text field indicating the physical location of the router.                                                                         | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Floor                | Text field indicating the floor where the rack is located.                                                                         | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Rack                 | Text field indicating the name of the rack where the router is installed.                                                          | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Contact              | Text field specifying whom to contact about the system (name, email, telephone number).                                            | support@drivenets.com                                  |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Fabric Minimum Links | The number of links below which the NCP will become unavailable. Not applicable for standalone devices.                            | 1                                                      |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Fabric Minimum NCF   | The number of active NCF nodes below which the cluster NCPs will become unavailable. Not applicable for standalone devices.        | 1                                                      |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| NCC switchovers      | The number of times that a switchover to the redundant NCC occurred. The switchover counter resets when performing a system reset. | Integer                                                |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Last NCC switchover  | The date and time of the last NCC switchover.                                                                                      | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Max failover         | The maximum number of allowed failovers in a failover period.                                                                      | 2                                                      |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Failover period      | The time window in minutes, for which NCC failovers are counted for escalate-stop decision.                                        | 30                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| Recovery mode        | The state of the recovery mode function.                                                                                           | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+
| BGP NSR              | The state of the BGP NSR function.                                                                                                 | \-                                                     |
+----------------------+------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------+

**Example**
::

	dnRouter# show system details

	System Name: sysp19, System-Id: ce74ac93-5524-4008-975e-2f885416ddba
	System Type: CL-16, Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	System status: running
	System Start Time: 19-May-2020 11:39:15 UTC
	System Uptime: 1 day, 18:44:47
	System Boot Uptime: 1 day, 18:45:41
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.
	Environment:
		Location: rackxxx
		Floor: -1
		Rack: 111
	Contact: support@drivenets.com
	Fabric Minimum Links: 10
	Fabric Minimum NCF: 1
	NCC switchovers: 2
	Last NCC switchover: 28-Sep-2022 06:10:13 UTC
	Escalation-stop-failovers
		Max-failover(remaining): 2(2)
		Failover-period(remaining): 30min(0 days, 0:30:00)
	Recovery-mode: supported
	BGP NSR: ready

	Node type: NCC
	Node ID: 0
		Operational: active-up
		Model: X86
		Uptime: 1 day, 18:44:47
		Description: dn-ncc-0
		Serial Number: CZ291902HR
		High-Availability Failures: N/A

	Container: management-engine
		State: running
		Start time: 19-May-2020 11:35:46
		Uptime: 1 day, 18:48:16
		Restart: 0
		High-Availability Failures: N/A

	| Process Name             | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|--------------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| cluster_manager          | running | 401   | 1 day, 18:46:43 | 0         | 1.3    | 0.26      | 998.7M       |
	| core:cluster_agent       | running | 434   | 1 day, 18:45:34 | 0         | 0.3    | 0.09      | 344.2M       |
	| core:transaction_manager | running | 1095  | 1 day, 18:45:32 | 0         | 0.3    | 0.18      | 711.0M       |
	| ctrl_bond_ntpd           | running | 452   | 1 day, 18:45:34 | 0         | 0.0    | 0.0       | 5.0M         |
	| deployment_agent         | running | 893   | 1 day, 18:45:32 | 0         | 0.0    | 0.02      | 59.4M        |
	| docker_expose            | running | 718   | 1 day, 18:45:33 | 0         | 0.0    | 0.01      | 35.1M        |
	| event_manager            | running | 622   | 1 day, 18:45:35 | 0         | 0.6    | 0.13      | 485.0M       |
	| infra:log_manager        | running | 924   | 1 day, 18:45:32 | 0         | 0.0    | 0.13      | 488.4M       |
	| infra:sshd               | running | 317   | 1 day, 18:47:10 | 0         | 0.0    | 0.0       | 7.0M         |
	| ncm_agent                | running | 1998  | 1 day, 18:44:44 | 1         | 0.9    | 0.16      | 613.5M       |
	| ntpd                     | running | 1123  | 1 day, 18:45:31 | 0         | 0.0    | 0.0       | 5.8M         |
	| oper_manager             | running | 931   | 1 day, 18:45:32 | 0         | 0.3    | 0.13      | 486.5M       |
	| rsyncd                   | running | 318   | 1 day, 18:47:10 | 0         | 0.0    | 0.0       | 4.2M         |
	| transaction_agent        | running | 443   | 1 day, 18:45:34 | 0         | 0.3    | 0.14      | 553.4M       |
	| yacron                   | running | 935   | 1 day, 18:45:32 | 0         | 0.3    | 0.01      | 38.3M        |

	Container: ncc-conductor
	        State: running
	        Start time: 19-May-2020 11:35:47
	        Uptime: 1 day, 18:48:15
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name        | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|---------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent    | running | 490   | 1 day, 18:45:34 | 0         | 0.0    | 0.01      | 57.1M        |
	| deployment_api      | running | 471   | 1 day, 18:45:34 | 0         | 0.0    | 0.02      | 79.5M        |
	| deployment_server   | running | 472   | 1 day, 18:45:34 | 0         | 0.0    | 0.02      | 82.0M        |
	| dhcpd               | running | 620   | 1 day, 18:45:33 | 0         | 0.0    | 0.0       | 3.6M         |
	| dhcpd_monitor       | running | 633   | 1 day, 18:45:32 | 0         | 0.0    | 0.02      | 59.3M        |
	| dhcpd_vxlan         | running | 459   | 1 day, 18:45:39 | 0         | 0.0    | 0.0       | 16.7M        |
	| discovery_broadcast | running | 602   | 1 day, 18:45:33 | 0         | 0.0    | 0.02      | 67.5M        |
	| infra:log_manager   | running | 882   | 1 day, 18:45:32 | 0         | 0.3    | 0.13      | 488.3M       |
	| infra:sshd          | running | 367   | 1 day, 18:47:04 | 0         | 0.0    | 0.0       | 6.9M         |
	| nginx               | running | 746   | 1 day, 18:45:32 | 0         | 0.0    | 0.0       | 7.5M         |
	| yacron_conductor    | running | 608   | 1 day, 18:45:33 | 0         | 0.3    | 0.01      | 37.9M        |

	Container: node-manager
	        State: running
	        Start time: 19-May-2020 11:35:49
	        Uptime: 1 day, 18:48:13
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| auth_logger            | running      | 3881  | 1 day, 18:45:36 | 0         | 0.0    | 0.01      | 34.0M        |
	| deployment_agent       | running      | 3701  | 1 day, 18:45:36 | 0         | 0.0    | 0.02      | 58.8M        |
	| disk_usage_manager     | running (up) | 3832  | 1 day, 18:45:35 | 0         | 0.0    | 0.02      | 80.0M        |
	| docker_expose          | running      | 3718  | 1 day, 18:45:36 | 0         | 0.0    | 0.01      | 35.2M        |
	| inotify_rsync          | down         | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| infra:log_manager      | running      | 3763  | 1 day, 18:45:36 | 0         | 0.0    | 0.13      | 491.0M       |
	| infra:sshd             | running      | 2899  | 1 day, 18:46:53 | 0         | 0.0    | 0.0       | 7.0M         |
	| lldpd                  | running      | 2895  | 1 day, 18:46:53 | 0         | 0.0    | 0.0       | 6.0M         |
	| management_agent       | running (up) | 3663  | 1 day, 18:45:36 | 0         | 3.5    | 0.14      | 540.6M       |
	| mgmt_interface_manager | running      | 3686  | 1 day, 18:45:36 | 0         | 0.6    | 0.09      | 338.6M       |
	| ntpd                   | running      | 2898  | 1 day, 18:46:53 | 0         | 0.0    | 0.0       | 5.9M         |
	| rsyncd                 | running      | 2900  | 1 day, 18:46:53 | 0         | 0.0    | 0.0       | 5.0M         |
	| sys_info               | running      | 3624  | 1 day, 18:45:36 | 0         | 0.0    | 0.0       | 3.5M         |
	| yacron                 | running      | 3810  | 1 day, 18:45:36 | 0         | 0.6    | 0.01      | 38.2M        |

	Container: routing-engine
	        State: running
	        Start time: 19-May-2020 11:35:46
	        Uptime: 1 day, 18:48:17
	        Restart: 0
	        High-Availability Failures:
			2020-05-21 06:19:45 process routing:pimd was restarted by system
			2020-05-21 06:19:43 process routing:pimd mitigation started
			2020-05-21 04:20:38 process routing:pimd was restarted by system
			2020-05-21 04:20:35 process routing:pimd mitigation started
			2020-05-21 01:59:40 process routing:pimd was restarted by system
			2020-05-21 01:59:38 process routing:pimd mitigation started
			2020-05-21 01:43:55 process routing:pimd was restarted by system
			2020-05-21 01:43:52 process routing:pimd mitigation started
			2020-05-21 01:16:42 process routing:pimd was restarted by system
			2020-05-21 01:16:39 process routing:pimd mitigation started


	| Process Name                | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-----------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| bgpd_authentication_logger  | running      | 848   | 1 day, 18:45:36 | 0         | 0.0    | 0.01      | 33.3M        |
	| console_ttyS0               | running      | 854   | 1 day, 18:45:36 | 0         | 0.0    | 0.0       | 4.6M         |
	| core:re_interfaces_agent    | running (up) | 1131  | 1 day, 18:45:34 | 0         | 0.0    | 0.09      | 354.9M       |
	| core:routing_manager        | running (up) | 881   | 1 day, 18:45:35 | 0         | 8.0    | 0.13      | 504.4M       |
	| core:rsyncd                 | running      | 552   | 1 day, 18:47:04 | 0         | 0.0    | 0.0       | 2.2M         |
	| deployment_agent            | running      | 2160  | 1 day, 18:45:30 | 0         | 0.0    | 0.02      | 58.5M        |
	| gnmi_agent                  | running      | 1165  | 1 day, 18:45:34 | 0         | 0.2    | 0.13      | 492.4M       |
	| gnmi_server                 | running      | 1059  | 1 day, 18:45:35 | 0         | 0.0    | 0.01      | 33.5M        |
	| infra:log_manager           | running      | 1901  | 1 day, 18:45:31 | 0         | 0.0    | 0.13      | 493.5M       |
	| infra:sshd                  | running      | 553   | 1 day, 18:47:04 | 0         | 0.0    | 0.0       | 7.4M         |
	| netconf_sshd_oob            | running      | 965   | 1 day, 18:45:35 | 0         | 0.0    | 0.01      | 33.9M        |
	| netconf_sshd_ndvrf          | running      | 967   | 1 day, 18:45:35 | 0         | 0.0    | 0.01      | 33.9M        |
	| netconf_sshd_inband         | running      | 1505  | 1 day, 18:45:33 | 0         | 0.0    | 0.01      | 33.8M        |
	| ntp_manager                 | running      | 892   | 1 day, 18:45:35 | 0         | 0.0    | 0.09      | 346.3M       |
	| ntpd_external               | running      | 3225  | 1 day, 18:45:20 | 1         | 0.0    | 0.0       | 7.3M         |
	| re_interface_manager        | running (up) | 1132  | 1 day, 18:45:35 | 0         | 0.8    | 0.32      | 1.2G         |
	| routing:bgpd                | running      | 2511  | 1 day, 18:45:28 | 0         | 1.2    | 4.27      | 16.1G        |
	| routing:fibmgrd             | running      | 2704  | 1 day, 18:45:27 | 0         | 54.3   | 2.31      | 8.7G         |
	| routing:isisd               | running      | 1336  | 1 day, 18:45:34 | 0         | 4.8    | 0.03      | 106.4M       |
	| routing:ldpd                | running      | 2649  | 1 day, 18:45:27 | 0         | 0.0    | 0.02      | 63.5M        |
	| routing:oam                 | running      | 2601  | 1 day, 18:45:28 | 0         | 0.2    | 0.01      | 23.6M        |
	| routing:ospfd               | running      | 2634  | 1 day, 18:45:28 | 0         | 0.0    | 0.01      | 21.5M        |
	| routing:pimd                | running      | 65959 | 0 days, 0:04:19 | 8         | 3.2    | 0.13      | 511.4M       |
	| routing:rib_manager         | running      | 1037  | 1 day, 18:45:35 | 0         | 0.2    | 16.8      | 63.3G        |
	| routing:rsvpd               | running      | 2725  | 1 day, 18:45:27 | 0         | 0.0    | 0.01      | 31.9M        |
	| routing:tunnel_dispatcher   | running      | 2670  | 1 day, 18:45:27 | 0         | 0.0    | 0.0       | 15.6M        |
	| rsyslog                     | running      | 11235 | 1 day, 18:29:23 | 3         | 0.0    | 0.0       | 5.9M         |
	| servers_manager             | running      | 1250  | 1 day, 18:45:34 | 0         | 0.2    | 0.13      | 483.1M       |
	| session_monitor             | running      | 1816  | 1 day, 18:45:31 | 0         | 0.2    | 0.02      | 69.6M        |
	| snmp_manager                | running      | 1414  | 1 day, 18:45:34 | 0         | 0.2    | 0.09      | 332.1M       |
	| snmp_probe_agent_if_mib     | running      | 870   | 1 day, 18:45:36 | 0         | 93.0   | 0.85      | 3.2G         |
	| snmp_probe_agent_ip_mib     | running      | 2184  | 1 day, 18:45:30 | 0         | 0.2    | 0.78      | 2.9G         |
	| snmp_probe_agent_system_mib | running      | 1162  | 1 day, 18:45:34 | 0         | 0.4    | 0.3       | 1.1G         |
	| snmp_trap_agent             | running      | 1724  | 1 day, 18:45:32 | 0         | 0.0    | 0.13      | 489.6M       |
	| snmpd                       | running      | 1602  | 1 day, 18:45:33 | 0         | 0.0    | 0.0       | 13.8M        |
	| snmptrap_managerd           | running      | 1694  | 1 day, 18:45:32 | 0         | 0.2    | 0.02      | 95.6M        |
	| snmptrapd                   | running      | 2313  | 1 day, 18:45:29 | 0         | 0.0    | 0.0       | 8.5M         |
	| ssh_manager                 | running      | 1594  | 1 day, 18:45:33 | 0         | 0.0    | 0.09      | 351.5M       |
	| sshd_inband                 | running      | 1996  | 1 day, 18:45:31 | 0         | 0.0    | 0.01      | 33.8M        |
	| sshd_outband                | running      | 2197  | 1 day, 18:45:30 | 0         | 0.0    | 0.01      | 34.8M        |
	| syslog_relay                | running      | 2172  | 1 day, 18:45:30 | 0         | 0.0    | 0.01      | 32.0M        |
	| techsupport_manager         | running      | 1921  | 1 day, 18:45:31 | 0         | 0.2    | 0.12      | 451.4M       |
	| twamp_agent                 | running      | 2214  | 1 day, 18:45:30 | 0         | 0.2    | 0.13      | 491.2M       |
	| twampd                      | running      | 2081  | 1 day, 18:45:31 | 0         | 0.2    | 0.01      | 29.7M        |
	| udev_monitor                | running      | 2397  | 1 day, 18:45:29 | 0         | 0.0    | 0.0       | 4.6M         |
	| users_manager               | running      | 1615  | 1 day, 18:45:32 | 0         | 0.0    | 0.13      | 484.6M       |
	| yacron                      | running      | 1713  | 1 day, 18:45:32 | 0         | 0.0    | 0.01      | 38.0M        |

	Node type: NCC
	Node ID: 1
	        Operational: standby-up
	        Model: X86
	        Uptime: 1 day, 18:44:48
	        Description: dn-ncc-1
	        Serial Number: CZ291902HT
	        High-Availability Failures: N/A

	Container: management-engine
	        State: running
	        Start time: 19-May-2020 11:35:44
	        Uptime: 1 day, 18:48:19
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name             | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|--------------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| cluster_manager          | running | 401   | 1 day, 18:46:45 | 0         | 1.0    | 0.16      | 616.7M       |
	| core:cluster_agent       | down    | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| core:transaction_manager | down    | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| ctrl_bond_ntpd           | running | 434   | 1 day, 18:45:36 | 0         | 0.0    | 0.0       | 4.8M         |
	...

	Container: ncc-conductor
	        State: running
	        Start time: 19-May-2020 11:35:45
	        Uptime: 1 day, 18:48:18
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name        | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|---------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent    | running | 493   | 1 day, 18:45:36 | 0         | 0.0    | 0.02      | 59.5M        |
	| deployment_api      | down    | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| deployment_server   | down    | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| dhcpd               | down    | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	...

	Container: node-manager
	        State: running
	        Start time: 19-May-2020 11:35:44
	        Uptime: 1 day, 18:48:20
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| auth_logger            | running      | 3884  | 1 day, 18:45:36 | 0         | 0.0    | 0.01      | 34.0M        |
	| deployment_agent       | running      | 3730  | 1 day, 18:45:36 | 0         | 0.0    | 0.02      | 58.8M        |
	| disk_usage_manager     | running (up) | 3873  | 1 day, 18:45:35 | 0         | 0.0    | 0.02      | 79.4M        |
	| docker_expose          | running      | 3700  | 1 day, 18:45:36 | 0         | 0.3    | 0.01      | 35.1M        |
	...

	Container: routing-engine
	        State: running
	        Start time: 19-May-2020 11:35:47
	        Uptime: 1 day, 18:48:17
	        Restart: 0
	        High-Availability Failures: N/A
	...


	Node type: NCF
	Node ID: 0
	        Operational: up
	        Model: NCF-48CD
	        Uptime: 1 day, 18:35:53
	        Description: dn-ncf-0
	        Serial Number: WEB194790002A
	        High-Availability Failures: N/A
	        Fabric-mode: single-stage

	Container: fabric
	        State: running
	        Start time: 19-May-2020 11:42:50
	        Uptime: 1 day, 18:41:14
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent  | running      | 1590  | 1 day, 18:39:30 | 0         | 0.0    | 0.09      | 58.6M        |
	| fabric_agent      | running (up) | 1447  | 1 day, 18:39:31 | 0         | 0.0    | 0.54      | 341.9M       |
	| fabric_manager    | running (up) | 1453  | 1 day, 18:39:31 | 0         | 40.1   | 1.38      | 879.8M       |
	| hw_monitor_agent  | running      | 1532  | 1 day, 18:39:32 | 0         | 1.0    | 0.03      | 17.1M        |
	| infra:log_manager | running      | 1554  | 1 day, 18:39:30 | 0         | 0.0    | 0.76      | 483.6M       |
	| infra:sshd        | running      | 1407  | 1 day, 18:39:59 | 0         | 0.0    | 0.01      | 7.3M         |

	Container: node-manager
	        State: running
	        Start time: 19-May-2020 11:42:30
	        Uptime: 1 day, 18:41:34
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| auth_logger            | running      | 2865  | 1 day, 18:40:33 | 0         | 0.0    | 0.05      | 33.9M        |
	| deployment_agent       | running      | 2876  | 1 day, 18:40:33 | 0         | 0.0    | 0.09      | 58.8M        |
	| disk_usage_manager     | running      | 2846  | 1 day, 18:40:33 | 0         | 0.3    | 0.12      | 77.8M        |
	| inotify_rsync          | running      | 2856  | 1 day, 18:40:33 | 0         | 0.0    | 0.05      | 29.5M        |
	| infra:log_manager      | running      | 2884  | 1 day, 18:40:33 | 0         | 0.0    | 0.77      | 490.3M       |
	| infra:sshd             | running      | 2686  | 1 day, 18:40:39 | 0         | 0.0    | 0.01      | 6.9M         |
	| lldpd                  | running      | 2683  | 1 day, 18:40:39 | 0         | 0.0    | 0.01      | 5.9M         |
	| management_agent       | running (up) | 2850  | 1 day, 18:40:33 | 0         | 2.6    | 0.79      | 501.7M       |
	| mgmt_interface_manager | running      | 2859  | 1 day, 18:40:33 | 0         | 1.6    | 0.47      | 302.8M       |
	| ntpd                   | running      | 2685  | 1 day, 18:40:39 | 0         | 0.0    | 0.01      | 5.8M         |
	| rsyncd                 | running      | 2687  | 1 day, 18:40:39 | 0         | 0.0    | 0.01      | 4.9M         |
	| sys_info               | running      | 2866  | 1 day, 18:40:33 | 0         | 0.0    | 0.01      | 3.5M         |
	| yacron                 | running      | 2864  | 1 day, 18:40:33 | 0         | 0.0    | 0.06      | 38.2M        |

	Node type: NCP
	Node ID: 0
	        Operational: up
	        Model: NCP-10CD
	        Hardware Model: S9700-23D (configured: S9700-23D)
	        Uptime: 1 day, 18:27:01
	        Description: dn-ncp-0
	        Serial Number: WDV1957D0000C
	        High-Availability Failures: N/A

	Container: datapath
	        State: running
	        Start time: 19-May-2020 11:45:22
	        Uptime: 1 day, 18:38:42
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent  | running      | 983   | 1 day, 18:37:05 | 0         | 0.0    | 0.09      | 58.4M        |
	| hw_monitor_agent  | running      | 1039  | 1 day, 18:37:05 | 0         | 0.6    | 0.03      | 16.7M        |
	| infra:log_manager | running      | 1141  | 1 day, 18:37:04 | 0         | 0.0    | 0.76      | 482.4M       |
	| infra:sshd        | running      | 903   | 1 day, 18:37:20 | 0         | 0.0    | 0.01      | 7.3M         |
	| udev_monitor      | running      | 1105  | 1 day, 18:37:04 | 0         | 0.0    | 0.01      | 4.8M         |
	| wb_agent          | running (up) | 965   | 1 day, 18:37:06 | 0         | 333.8  | 15.92     | 9.9G         |
	| wb_fe_agent       | running (up) | 959   | 1 day, 18:37:05 | 0         | 1.6    | 0.56      | 355.9M       |

	Container: node-manager
	        State: running
	        Start time: 19-May-2020 11:45:21
	        Uptime: 1 day, 18:38:43
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| auth_logger            | running      | 2805  | 1 day, 18:37:37 | 0         | 0.3    | 0.05      | 33.5M        |
	| deployment_agent       | running      | 2811  | 1 day, 18:37:37 | 0         | 0.0    | 0.09      | 58.4M        |
	| disk_usage_manager     | running      | 2800  | 1 day, 18:37:37 | 0         | 0.3    | 0.12      | 76.9M        |
	| inotify_rsync          | running      | 2787  | 1 day, 18:37:37 | 0         | 0.0    | 0.05      | 29.3M        |
	| infra:log_manager      | running      | 2809  | 1 day, 18:37:37 | 0         | 0.0    | 0.52      | 331.3M       |
	| infra:sshd             | running      | 2627  | 1 day, 18:37:44 | 0         | 0.0    | 0.01      | 6.8M         |
	| lldpd                  | running      | 2624  | 1 day, 18:37:44 | 0         | 0.0    | 0.01      | 5.9M         |
	| management_agent       | running (up) | 2789  | 1 day, 18:37:38 | 0         | 1.9    | 0.53      | 341.1M       |
	| mgmt_interface_manager | running      | 2793  | 1 day, 18:37:37 | 0         | 0.6    | 0.47      | 302.3M       |
	| ntpd                   | running      | 2626  | 1 day, 18:37:44 | 0         | 0.0    | 0.01      | 5.6M         |
	| rsyncd                 | running      | 2628  | 1 day, 18:37:44 | 0         | 0.0    | 0.01      | 4.8M         |
	| sys_info               | running      | 2806  | 1 day, 18:37:37 | 0         | 0.0    | 0.01      | 3.3M         |
	| yacron                 | running      | 2799  | 1 day, 18:37:37 | 0         | 0.6    | 0.06      | 38.3M        |

	Node type: NCP
	Node ID: 1
	        Operational: up
	        Model: NCP-10CD
	        Hardware Model: S9700-23D (configured: S9700-23D)
	        Uptime: 1 day, 18:27:01
	        Description: dn-ncp-1
	        Serial Number: WDV1957F0000E
	        High-Availability Failures: N/A

	Container: datapath
	        State: running
	        Start time: 19-May-2020 11:45:05
	        Uptime: 1 day, 18:38:59
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent  | running      | 1080  | 1 day, 18:37:18 | 0         | 0.0    | 0.09      | 58.5M        |
	| hw_monitor_agent  | running      | 969   | 1 day, 18:37:20 | 0         | 0.0    | 0.03      | 17.4M        |
	| infra:log_manager | running      | 961   | 1 day, 18:37:20 | 0         | 0.0    | 0.77      | 488.6M       |
	| infra:sshd        | running      | 915   | 1 day, 18:37:29 | 0         | 0.0    | 0.01      | 7.0M         |
	| udev_monitor      | running      | 1003  | 1 day, 18:37:19 | 0         | 0.0    | 0.01      | 4.7M         |
	| wb_agent          | running (up) | 982   | 1 day, 18:37:20 | 0         | 366.8  | 16.22     | 10.1G        |
	| wb_fe_agent       | running (up) | 955   | 1 day, 18:37:20 | 0         | 1.9    | 0.56      | 354.3M       |

	Container: node-manager
	        State: running
	        Start time: 19-May-2020 11:45:06
	        Uptime: 1 day, 18:38:58
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| auth_logger            | running      | 2824  | 1 day, 18:37:52 | 0         | 0.0    | 0.05      | 33.6M        |
	| deployment_agent       | running      | 3920  | 1 day, 18:33:10 | 1         | 0.0    | 0.09      | 56.0M        |
	| disk_usage_manager     | running      | 2812  | 1 day, 18:37:52 | 0         | 0.0    | 0.12      | 77.3M        |
	| inotify_rsync          | running      | 2804  | 1 day, 18:37:52 | 0         | 0.0    | 0.05      | 29.4M        |
	| infra:log_manager      | running      | 2838  | 1 day, 18:37:52 | 0         | 0.0    | 0.76      | 483.3M       |
	| infra:sshd             | running      | 2645  | 1 day, 18:37:58 | 0         | 0.0    | 0.01      | 6.9M         |
	| lldpd                  | running      | 2642  | 1 day, 18:37:58 | 0         | 0.0    | 0.01      | 5.9M         |
	| management_agent       | running (up) | 2810  | 1 day, 18:37:51 | 0         | 0.6    | 0.53      | 341.3M       |
	| mgmt_interface_manager | running      | 2805  | 1 day, 18:37:52 | 0         | 3.2    | 0.47      | 302.6M       |
	| ntpd                   | running      | 2644  | 1 day, 18:37:58 | 0         | 0.0    | 0.01      | 5.6M         |
	| rsyncd                 | running      | 2646  | 1 day, 18:37:58 | 0         | 0.0    | 0.01      | 4.9M         |
	| sys_info               | running      | 2828  | 1 day, 18:37:52 | 0         | 0.0    | 0.01      | 3.4M         |
	| yacron                 | running      | 2811  | 1 day, 18:37:52 | 0         | 0.6    | 0.06      | 37.9M        |


	dnRouter# show system ncc 0 container ncc-conductor

	Node type: NCC
	Node ID: 0
		Operational: active-up
		Model: X86
		Uptime: 1 day, 18:50:53
		Description: dn-ncc-0
		Serial Number: CZ291902HR
		High-Availability Failures: N/A

	Container: ncc-conductor
		State: running
		Start time: 19-May-2020 11:35:46
		Uptime: 1 day, 18:54:21
		Restart: 0
		High-Availability Failures: N/A

	| Process Name        | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|---------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent    | running | 490   | 1 day, 18:51:40 | 0         | 0.0    | 0.01      | 57.1M        |
	| deployment_api      | running | 471   | 1 day, 18:51:40 | 0         | 0.0    | 0.02      | 79.5M        |
	| deployment_server   | running | 472   | 1 day, 18:51:40 | 0         | 0.0    | 0.02      | 82.0M        |
	| dhcpd               | running | 620   | 1 day, 18:51:39 | 0         | 0.0    | 0.0       | 3.6M         |
	| dhcpd_monitor       | running | 633   | 1 day, 18:51:38 | 0         | 0.0    | 0.02      | 59.3M        |
	| dhcpd_vxlan         | running | 459   | 1 day, 18:51:45 | 0         | 0.0    | 0.0       | 16.7M        |
	| discovery_broadcast | running | 602   | 1 day, 18:51:39 | 0         | 0.0    | 0.02      | 67.5M        |
	| infra:log_manager   | running | 882   | 1 day, 18:51:38 | 0         | 0.0    | 0.13      | 488.3M       |
	| infra:sshd          | running | 367   | 1 day, 18:53:10 | 0         | 0.0    | 0.0       | 6.9M         |
	| nginx               | running | 746   | 1 day, 18:51:38 | 0         | 0.0    | 0.0       | 7.5M         |
	| yacron_conductor    | running | 608   | 1 day, 18:51:39 | 0         | 0.0    | 0.01      | 37.9M        |


	dnRouter# show system ncp 0 container datapath process wb_agent

	Node type: NCP
	Node ID: 0
		Operational: up
		Model: NCP-10CD
		Hardware Model: S9700-23D (configured: S9700-23D)
		Uptime: 1 day, 18:33:48
		Description: dn-ncp-0
		Serial Number: WDV1957D0000C
		High-Availability Failures: N/A

	Container: datapath
		State: running
		Start time: 19-May-2020 11:45:22
		Uptime: 1 day, 18:45:29
		Restart: 0
		High-Availability Failures: N/A

	| Process Name   | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|----------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| wb_agent       | running (up) | 965   | 1 day, 18:43:53 | 0         | 366.6  | 15.92     | 9.9G         |


	dnRouter# show system ncc 1 container routing-engine process-state down

	Node type: NCC
	Node ID: 1
		Operational: standby-up
		Model: X86
		Uptime: 1 day, 18:52:17
		Description: dn-ncc-1
		Serial Number: CZ291902HT
		High-Availability Failures: N/A

	Container: routing-engine
		State: running
		Start time: 19-May-2020 11:35:45
		Uptime: 1 day, 18:55:46
		Restart: 0
		High-Availability Failures: N/A

	| Process Name                | State               | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-----------------------------+---------------------+-------+-----------------+-----------+--------+-----------+--------------|
	| core:routing_manager        | down (disconnected) | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| gnmi_agent                  | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| gnmi_server                 | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| ntp_manager                 | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| ntpd_external               | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:bgpd                | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:fibmgrd             | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:isisd               | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:ldpd                | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:oam                 | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:ospfd               | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:pimd                | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:rib_manager         | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:rsvpd               | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| routing:tunnel_dispatcher   | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| session_monitor             | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| snmp_manager                | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| snmp_probe_agent_if_mib     | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| snmp_probe_agent_ip_mib     | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| snmp_probe_agent_system_mib | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| snmp_trap_agent             | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| snmpd                       | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| snmptrap_managerd           | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| snmptrapd                   | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| twamp_agent                 | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |
	| twampd                      | down                | 0     | 0 days, 0:00:00 | 0         |        |           |              |


	dnRouter# show system process cluster_manager

	System Name: sysp19, System-Id: ce74ac93-5524-4008-975e-2f885416ddba
	System Type: CL-16, Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	System status: running
	System Start Time: 19-May-2020 11:39:14 UTC
	System Uptime: 1 day, 18:53:09
	System Boot Uptime: 1 day, 18:54:03
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.
	Environment:
		Location: rackxxx
		Floor: -1
		Rack: 111
	Contact: support@drivenets.com
	Fabric Minimum Links: 10
	Fabric Minimum NCF: 1
	NCC switchovers: 0
	Last NCC switchover: N/A
	Escalation-stop-failovers
		Max-failover(remaining): 2(2)
		Failover-period(remaining): 30min(0 days, 0:30:00)
	Recovery-mode: supported
	BGP NSR: ready

	Node type: NCC
	Node ID: 0
		Operational: active-up
		Model: X86
		Uptime: 1 day, 18:53:09
		Description: dn-ncc-0
		Serial Number: CZ291902HR
		High-Availability Failures: N/A

	Container: management-engine
		State: running
		Start time: 19-May-2020 11:35:45
		Uptime: 1 day, 18:56:38
		Restart: 0
		High-Availability Failures: N/A

	| Process Name    | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-----------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| cluster_manager | running | 401   | 1 day, 18:55:05 | 0         | 0.9    | 0.26      | 999.8M       |

	Node type: NCC
	Node ID: 1
		Operational: standby-up
		Model: X86
	        Uptime: 1 day, 18:53:09
	        Description: dn-ncc-1
	        Serial Number: CZ291902HT
	        High-Availability Failures: N/A

	Container: management-engine
	        State: running
	        Start time: 19-May-2020 11:35:44
	        Uptime: 1 day, 18:56:40
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name    | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-----------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| cluster_manager | running | 401   | 1 day, 18:55:06 | 0         | 1.0    | 0.16      | 616.7M       |



	### Standalone system type ###
	dnRouter# show system details

	System Name: sysp204, System-Id: 5dd3ea41-e5ef-4b46-9345-47cda7c28368
	System Type: SA-40C, Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	System status: running
	System Start Time: 15-Jun-2020 12:15:39 UTC
	System Uptime: 0 days, 4:13:25
	System Boot Uptime: 0 days, 4:14:27
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.
	Environment:
		Location: N/A
		Floor: N/A
		Rack: N/A
	Contact: support@drivenets.com
	Fabric Minimum Links: N/A
	Fabric Minimum NCF: N/A
	NCC switchovers: 0
	Last NCC switchover: N/A
	Escalation-stop-failovers
		Max-failover(remaining): 2(2)
		Failover-period(remaining): 30min(0 days, 0:30:00)
	Recovery-mode: supported
	BGP NSR: N/A

	Node type: NCC
	Node ID: 0
		Operational: active-up
		Model: NCP-40C
		Uptime: 0 days, 4:13:25
		Description: dn-ncc-0
		Serial Number:
		High-Availability Failures: N/A

	Container: management-engine
		State: running
		Start time: 15-Jun-2020 12:13:06
		Uptime: 0 days, 4:15:58
		Restart: 0
		High-Availability Failures: N/A

	| Process Name             | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|--------------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| cluster_manager          | running | 700   | 0 days, 4:14:32 | 0         | 1.3    | 1.09      | 694.4M       |
	| core:cluster_agent       | running | 728   | 0 days, 4:14:21 | 0         | 0.0    | 0.61      | 389.2M       |
	| core:transaction_manager | running | 741   | 0 days, 4:14:21 | 0         | 0.0    | 0.92      | 588.2M       |
	| ctrl_bond_ntpd           | running | 800   | 0 days, 4:14:19 | 0         | 0.0    | 0.01      | 5.0M         |
	| deployment_agent         | running | 743   | 0 days, 4:14:21 | 0         | 0.0    | 0.09      | 59.3M        |
	| docker_expose            | running | 924   | 0 days, 4:14:15 | 0         | 0.0    | 0.06      | 35.6M        |
	| event_manager            | running | 923   | 0 days, 4:14:15 | 0         | 0.3    | 0.62      | 397.1M       |
	| infra:log_manager        | running | 870   | 0 days, 4:14:18 | 0         | 0.0    | 0.63      | 405.0M       |
	| infra:sshd               | running | 664   | 0 days, 4:14:50 | 0         | 0.0    | 0.01      | 7.2M         |
	| ntpd                     | running | 949   | 0 days, 4:14:15 | 0         | 0.0    | 0.01      | 5.9M         |
	| oper_manager             | running | 878   | 0 days, 4:14:16 | 0         | 0.0    | 0.61      | 387.8M       |
	| rsyncd                   | running | 665   | 0 days, 4:14:50 | 0         | 0.0    | 0.0       | 2.2M         |
	| transaction_agent        | running | 777   | 0 days, 4:14:19 | 0         | 0.0    | 0.82      | 520.2M       |
	| yacron                   | running | 1039  | 0 days, 4:14:13 | 0         | 0.3    | 0.06      | 37.3M        |

	Container: ncc-conductor
	        State: running
	        Start time: 15-Jun-2020 12:13:09
	        Uptime: 0 days, 4:15:56
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent  | running | 780   | 0 days, 4:14:20 | 0         | 0.0    | 0.09      | 57.6M        |
	| deployment_api    | running | 767   | 0 days, 4:14:20 | 0         | 0.0    | 0.12      | 79.5M        |
	| deployment_server | running | 854   | 0 days, 4:14:17 | 0         | 0.3    | 0.13      | 82.7M        |
	| infra:log_manager | running | 790   | 0 days, 4:14:19 | 0         | 0.0    | 0.64      | 406.4M       |
	| infra:sshd        | running | 724   | 0 days, 4:14:42 | 0         | 0.0    | 0.01      | 7.1M         |
	| nginx             | running | 800   | 0 days, 4:14:20 | 0         | 0.0    | 0.01      | 7.4M         |
	| yacron_conductor  | running | 890   | 0 days, 4:14:16 | 0         | 0.3    | 0.06      | 37.8M        |

	Container: node-manager
	        State: running
	        Start time: 15-Jun-2020 12:13:07
	        Uptime: 0 days, 4:15:58
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| auth_logger            | running      | 4030  | 0 days, 4:14:23 | 0         | 0.6    | 0.05      | 33.9M        |
	| deployment_agent       | running      | 3964  | 0 days, 4:14:22 | 0         | 0.0    | 0.09      | 58.8M        |
	| disk_usage_manager     | running      | 3957  | 0 days, 4:14:22 | 0         | 0.0    | 0.12      | 77.4M        |
	| docker_expose          | running      | 3948  | 0 days, 4:14:22 | 0         | 0.3    | 0.05      | 35.0M        |
	| infra:log_manager      | running      | 3970  | 0 days, 4:14:23 | 0         | 0.0    | 0.61      | 386.4M       |
	| infra:sshd             | running      | 3477  | 0 days, 4:15:13 | 0         | 0.0    | 0.01      | 7.4M         |
	| ipmi_watchdog_logger   | running      | 3930  | 0 days, 4:14:22 | 0         | 0.0    | 0.02      | 12.0M        |
	| management_agent       | running (up) | 3937  | 0 days, 4:14:22 | 0         | 2.9    | 0.63      | 402.2M       |
	| mgmt_interface_manager | running      | 3952  | 0 days, 4:14:22 | 0         | 0.6    | 0.49      | 314.7M       |
	| ntpd                   | running      | 3476  | 0 days, 4:15:13 | 0         | 0.0    | 0.01      | 5.8M         |
	| rsyncd                 | running      | 3478  | 0 days, 4:15:13 | 0         | 0.0    | 0.01      | 5.0M         |
	| sys_info               | running      | 3958  | 0 days, 4:14:22 | 0         | 0.0    | 0.01      | 3.4M         |
	| yacron                 | running      | 3998  | 0 days, 4:14:23 | 0         | 0.0    | 0.06      | 38.1M        |

	Container: routing-engine
	        State: running
	        Start time: 15-Jun-2020 12:13:10
	        Uptime: 0 days, 4:15:55
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name                | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-----------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| bgpd_authentication_logger  | running      | 1011  | 0 days, 4:14:22 | 0         | 0.0    | 0.05      | 33.4M        |
	| console_ttyS0               | running      | 1192  | 0 days, 4:14:18 | 0         | 0.0    | 0.01      | 4.7M         |
	| core:re_interfaces_agent    | running (up) | 1241  | 0 days, 4:14:17 | 0         | 0.0    | 0.6       | 384.8M       |
	| core:routing_manager        | running (up) | 1330  | 0 days, 4:14:16 | 0         | 1.4    | 0.64      | 407.4M       |
	| core:rsyncd                 | running      | 964   | 0 days, 4:14:40 | 0         | 0.0    | 0.0       | 2.2M         |
	| deployment_agent            | running      | 1908  | 0 days, 4:14:03 | 0         | 0.0    | 0.09      | 58.5M        |
	| gnmi_agent                  | running      | 1361  | 0 days, 4:14:14 | 0         | 0.0    | 0.83      | 529.6M       |
	| gnmi_server                 | running      | 1134  | 0 days, 4:14:20 | 0         | 0.3    | 0.05      | 30.5M        |
	| infra:log_manager           | running      | 1960  | 0 days, 4:14:02 | 0         | 0.0    | 0.61      | 391.1M       |
	| infra:sshd                  | running      | 965   | 0 days, 4:14:40 | 0         | 0.0    | 0.01      | 7.1M         |
	| netconf_sshd_oob            | running      | 1029  | 0 days, 4:14:21 | 0         | 0.0    | 0.05      | 33.9M        |
	| netconf_sshd_ndvrf          | running      | 1039  | 0 days, 4:14:21 | 0         | 0.0    | 0.05      | 33.9M        |
	| netconf_sshd_inband         | running      | 1159  | 0 days, 4:14:20 | 0         | 0.0    | 0.05      | 33.9M        |
	| ntp_manager                 | running      | 1179  | 0 days, 4:14:20 | 0         | 0.0    | 0.61      | 387.5M       |
	| ntpd_external               | running      | 8561  | 0 days, 3:42:27 | 2         | 0.0    | 0.01      | 5.8M         |
	| re_interface_manager        | running (up) | 1209  | 0 days, 4:14:18 | 0         | 1.7    | 1.68      | 1.0G         |
	| routing:bgpd                | running      | 1018  | 0 days, 4:14:21 | 0         | 108.1  | 12.27     | 7.6G         |
	| routing:fibmgrd             | running      | 2092  | 0 days, 4:13:59 | 0         | 86.6   | 8.76      | 5.5G         |
	| routing:isisd               | running      | 1281  | 0 days, 4:14:16 | 0         | 0.3    | 0.04      | 24.1M        |
	| routing:ldpd                | running      | 1991  | 0 days, 4:14:01 | 0         | 0.0    | 0.02      | 13.4M        |
	| routing:oam                 | running      | 2286  | 0 days, 4:13:57 | 0         | 0.3    | 0.03      | 20.3M        |
	| routing:ospfd               | running      | 1566  | 0 days, 4:14:10 | 0         | 0.0    | 0.03      | 17.8M        |
	| routing:pimd                | running      | 2038  | 0 days, 4:14:01 | 0         | 31.1   | 0.07      | 43.1M        |
	| routing:rib_manager         | running      | 1092  | 0 days, 4:14:20 | 0         | 57.7   | 2.59      | 1.6G         |
	| routing:rsvpd               | running      | 1867  | 0 days, 4:14:04 | 0         | 0.0    | 0.04      | 28.4M        |
	| routing:tunnel_dispatcher   | running      | 1041  | 0 days, 4:14:20 | 0         | 0.0    | 0.02      | 12.2M        |
	| rsyslog                     | running      | 8634  | 0 days, 3:42:22 | 3         | 0.0    | 0.01      | 4.5M         |
	| servers_manager             | running (up) | 1300  | 0 days, 4:14:15 | 0         | 0.0    | 0.61      | 390.2M       |
	| session_monitor             | running      | 1733  | 0 days, 4:14:07 | 0         | 0.8    | 0.11      | 69.0M        |
	| snmp_manager                | running      | 1275  | 0 days, 4:14:16 | 0         | 0.0    | 0.47      | 302.4M       |
	| snmp_probe_agent_if_mib     | running      | 1807  | 0 days, 4:14:06 | 0         | 0.0    | 0.69      | 441.5M       |
	| snmp_probe_agent_ip_mib     | running      | 1421  | 0 days, 4:14:13 | 0         | 0.0    | 0.68      | 433.7M       |
	| snmp_probe_agent_system_mib | running      | 1463  | 0 days, 4:14:12 | 0         | 0.3    | 0.63      | 403.8M       |
	| snmp_trap_agent             | running      | 1752  | 0 days, 4:14:06 | 0         | 0.3    | 0.47      | 301.0M       |
	| snmpd                       | running      | 1930  | 0 days, 4:14:03 | 0         | 0.6    | 0.02      | 11.4M        |
	| snmptrap_managerd           | running      | 1634  | 0 days, 4:14:08 | 0         | 0.0    | 0.02      | 13.8M        |
	| snmptrapd                   | running      | 1464  | 0 days, 4:14:12 | 0         | 0.0    | 0.01      | 8.3M         |
	| ssh_manager                 | running (up) | 2209  | 0 days, 4:13:57 | 0         | 0.0    | 0.6       | 384.6M       |
	| sshd_inband                 | running      | 1942  | 0 days, 4:14:03 | 0         | 0.0    | 0.05      | 34.0M        |
	| sshd_outband                | running      | 1851  | 0 days, 4:14:06 | 0         | 0.0    | 0.05      | 34.1M        |
	| syslog_relay                | running      | 1483  | 0 days, 4:14:11 | 0         | 0.0    | 0.05      | 32.2M        |
	| techsupport_manager         | running      | 1554  | 0 days, 4:14:10 | 0         | 0.3    | 0.78      | 497.9M       |
	| twamp_agent                 | running      | 2117  | 0 days, 4:13:59 | 0         | 0.0    | 0.6       | 383.7M       |
	| twampd                      | running      | 1505  | 0 days, 4:14:11 | 0         | 0.3    | 0.03      | 21.3M        |
	| udev_monitor                | running      | 1392  | 0 days, 4:14:13 | 0         | 0.0    | 0.01      | 4.7M         |
	| users_manager               | running (up) | 1769  | 0 days, 4:14:06 | 0         | 0.0    | 0.6       | 383.4M       |
	| yacron                      | running      | 1695  | 0 days, 4:14:07 | 0         | 0.0    | 0.06      | 38.1M        |

	Node type: NCP
	Node ID: 0
	        Operational: up
	        Model: NCP-40C
	        Hardware Model: S9700-53DX (configured: S9700-53DX)
	        Uptime: 0 days, 4:13:03
	        Description: dn-ncp-0
	        Serial Number: WDY19C7N00014-P3
	        High-Availability Failures: N/A

	Container: datapath
	        State: running
	        Start time: 15-Jun-2020 12:14:37
	        Uptime: 0 days, 4:14:28
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent  | running      | 2568  | 0 days, 4:14:18 | 0         | 0.0    | 0.09      | 58.6M        |
	| hw_monitor_agent  | running      | 2567  | 0 days, 4:14:18 | 0         | 0.0    | 0.03      | 16.9M        |
	| infra:log_manager | running      | 2563  | 0 days, 4:14:18 | 0         | 0.0    | 0.61      | 386.0M       |
	| infra:sshd        | running      | 1421  | 0 days, 4:15:28 | 0         | 0.0    | 0.01      | 7.3M         |
	| udev_monitor      | running      | 2569  | 0 days, 4:14:18 | 0         | 0.0    | 0.01      | 4.9M         |
	| wb_agent          | running (up) | 1581  | 0 days, 4:15:21 | 0         | 247.9  | 14.41     | 9.0G         |
	| wb_fe_agent       | running (up) | 2570  | 0 days, 4:14:18 | 0         | 1.2    | 0.63      | 403.8M       |

	### NC-AI Cluster system type ###
	dnRouter# show system details

	System Name: sysp204, System-Id: 5dd3ea41-e5ef-4b46-9345-47cda7c28368
	System Type: CL-AI-8K-400G ((SA-36CD-S-NCP), Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	System status: running
	System Start Time: 25-Jun-2023 12:15:39 UTC
	System Uptime: 0 days, 4:13:25
	System Boot Uptime: 0 days, 4:14:27
	Version: DNOS [19.0.0] build [411], Copyright 2022 DRIVENETS LTD.
	Environment:
		Location: N/A
		Floor: N/A
		Rack: N/A
	Contact: support@drivenets.com
	Fabric Minimum Links: 1
	Fabric Minimum NCF: 1
	NCC switchovers: 0
	Last NCC switchover: N/A
	Escalation-stop-failovers
		Max-failover(remaining): 2(2)
		Failover-period(remaining): 30min(0 days, 0:30:00)
	Recovery-mode: supported
	BGP NSR: N/A

	Node type: NCC
	Node ID: 0
		Operational: active-up
		Model: NCP-36CD-S
		Uptime: 0 days, 4:13:25
		Description: dn-ncc-0
		Serial Number:
		High-Availability Failures: N/A

	Container: management-engine
		State: running
		Start time: 15-Jun-2023 12:13:06
		Uptime: 0 days, 4:15:58
		Restart: 0
		High-Availability Failures: N/A

	| Process Name             | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|--------------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| cluster_manager          | running | 700   | 0 days, 4:14:32 | 0         | 1.3    | 1.09      | 694.4M       |
	| core:cluster_agent       | running | 728   | 0 days, 4:14:21 | 0         | 0.0    | 0.61      | 389.2M       |
	| core:transaction_manager | running | 741   | 0 days, 4:14:21 | 0         | 0.0    | 0.92      | 588.2M       |
	| ctrl_bond_ntpd           | running | 800   | 0 days, 4:14:19 | 0         | 0.0    | 0.01      | 5.0M         |
	| deployment_agent         | running | 743   | 0 days, 4:14:21 | 0         | 0.0    | 0.09      | 59.3M        |
	| docker_expose            | running | 924   | 0 days, 4:14:15 | 0         | 0.0    | 0.06      | 35.6M        |
	| event_manager            | running | 923   | 0 days, 4:14:15 | 0         | 0.3    | 0.62      | 397.1M       |
	| infra:log_manager        | running | 870   | 0 days, 4:14:18 | 0         | 0.0    | 0.63      | 405.0M       |
	| infra:sshd               | running | 664   | 0 days, 4:14:50 | 0         | 0.0    | 0.01      | 7.2M         |
	| ntpd                     | running | 949   | 0 days, 4:14:15 | 0         | 0.0    | 0.01      | 5.9M         |
	| oper_manager             | running | 878   | 0 days, 4:14:16 | 0         | 0.0    | 0.61      | 387.8M       |
	| rsyncd                   | running | 665   | 0 days, 4:14:50 | 0         | 0.0    | 0.0       | 2.2M         |
	| transaction_agent        | running | 777   | 0 days, 4:14:19 | 0         | 0.0    | 0.82      | 520.2M       |
	| yacron                   | running | 1039  | 0 days, 4:14:13 | 0         | 0.3    | 0.06      | 37.3M        |

	Container: ncc-conductor
	        State: running
	        Start time: 15-Jun-2023 12:13:09
	        Uptime: 0 days, 4:15:56
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent  | running | 780   | 0 days, 4:14:20 | 0         | 0.0    | 0.09      | 57.6M        |
	| deployment_api    | running | 767   | 0 days, 4:14:20 | 0         | 0.0    | 0.12      | 79.5M        |
	| deployment_server | running | 854   | 0 days, 4:14:17 | 0         | 0.3    | 0.13      | 82.7M        |
	| infra:log_manager | running | 790   | 0 days, 4:14:19 | 0         | 0.0    | 0.64      | 406.4M       |
	| infra:sshd        | running | 724   | 0 days, 4:14:42 | 0         | 0.0    | 0.01      | 7.1M         |
	| nginx             | running | 800   | 0 days, 4:14:20 | 0         | 0.0    | 0.01      | 7.4M         |
	| yacron_conductor  | running | 890   | 0 days, 4:14:16 | 0         | 0.3    | 0.06      | 37.8M        |

	Container: node-manager
	        State: running
	        Start time: 15-Jun-2023 12:13:07
	        Uptime: 0 days, 4:15:58
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| auth_logger            | running      | 4030  | 0 days, 4:14:23 | 0         | 0.6    | 0.05      | 33.9M        |
	| deployment_agent       | running      | 3964  | 0 days, 4:14:22 | 0         | 0.0    | 0.09      | 58.8M        |
	| disk_usage_manager     | running      | 3957  | 0 days, 4:14:22 | 0         | 0.0    | 0.12      | 77.4M        |
	| docker_expose          | running      | 3948  | 0 days, 4:14:22 | 0         | 0.3    | 0.05      | 35.0M        |
	| infra:log_manager      | running      | 3970  | 0 days, 4:14:23 | 0         | 0.0    | 0.61      | 386.4M       |
	| infra:sshd             | running      | 3477  | 0 days, 4:15:13 | 0         | 0.0    | 0.01      | 7.4M         |
	| ipmi_watchdog_logger   | running      | 3930  | 0 days, 4:14:22 | 0         | 0.0    | 0.02      | 12.0M        |
	| management_agent       | running (up) | 3937  | 0 days, 4:14:22 | 0         | 2.9    | 0.63      | 402.2M       |
	| mgmt_interface_manager | running      | 3952  | 0 days, 4:14:22 | 0         | 0.6    | 0.49      | 314.7M       |
	| ntpd                   | running      | 3476  | 0 days, 4:15:13 | 0         | 0.0    | 0.01      | 5.8M         |
	| rsyncd                 | running      | 3478  | 0 days, 4:15:13 | 0         | 0.0    | 0.01      | 5.0M         |
	| sys_info               | running      | 3958  | 0 days, 4:14:22 | 0         | 0.0    | 0.01      | 3.4M         |
	| yacron                 | running      | 3998  | 0 days, 4:14:23 | 0         | 0.0    | 0.06      | 38.1M        |

	Container: routing-engine
	        State: running
	        Start time: 15-Jun-2023 12:13:10
	        Uptime: 0 days, 4:15:55
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name                | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-----------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| bgpd_authentication_logger  | running      | 1011  | 0 days, 4:14:22 | 0         | 0.0    | 0.05      | 33.4M        |
	| console_ttyS0               | running      | 1192  | 0 days, 4:14:18 | 0         | 0.0    | 0.01      | 4.7M         |
	| core:re_interfaces_agent    | running (up) | 1241  | 0 days, 4:14:17 | 0         | 0.0    | 0.6       | 384.8M       |
	| core:routing_manager        | running (up) | 1330  | 0 days, 4:14:16 | 0         | 1.4    | 0.64      | 407.4M       |
	| core:rsyncd                 | running      | 964   | 0 days, 4:14:40 | 0         | 0.0    | 0.0       | 2.2M         |
	| deployment_agent            | running      | 1908  | 0 days, 4:14:03 | 0         | 0.0    | 0.09      | 58.5M        |
	| gnmi_agent                  | running      | 1361  | 0 days, 4:14:14 | 0         | 0.0    | 0.83      | 529.6M       |
	| gnmi_server                 | running      | 1134  | 0 days, 4:14:20 | 0         | 0.3    | 0.05      | 30.5M        |
	| infra:log_manager           | running      | 1960  | 0 days, 4:14:02 | 0         | 0.0    | 0.61      | 391.1M       |
	| infra:sshd                  | running      | 965   | 0 days, 4:14:40 | 0         | 0.0    | 0.01      | 7.1M         |
	| netconf_sshd_oob            | running      | 1029  | 0 days, 4:14:21 | 0         | 0.0    | 0.05      | 33.9M        |
	| netconf_sshd_ndvrf          | running      | 1039  | 0 days, 4:14:21 | 0         | 0.0    | 0.05      | 33.9M        |
	| netconf_sshd_inband         | running      | 1159  | 0 days, 4:14:20 | 0         | 0.0    | 0.05      | 33.9M        |
	| ntp_manager                 | running      | 1179  | 0 days, 4:14:20 | 0         | 0.0    | 0.61      | 387.5M       |
	| ntpd_external               | running      | 8561  | 0 days, 3:42:27 | 2         | 0.0    | 0.01      | 5.8M         |
	| re_interface_manager        | running (up) | 1209  | 0 days, 4:14:18 | 0         | 1.7    | 1.68      | 1.0G         |
	| routing:bgpd                | running      | 1018  | 0 days, 4:14:21 | 0         | 108.1  | 12.27     | 7.6G         |
	| routing:fibmgrd             | running      | 2092  | 0 days, 4:13:59 | 0         | 86.6   | 8.76      | 5.5G         |
	| routing:isisd               | running      | 1281  | 0 days, 4:14:16 | 0         | 0.3    | 0.04      | 24.1M        |
	| routing:ldpd                | running      | 1991  | 0 days, 4:14:01 | 0         | 0.0    | 0.02      | 13.4M        |
	| routing:oam                 | running      | 2286  | 0 days, 4:13:57 | 0         | 0.3    | 0.03      | 20.3M        |
	| routing:ospfd               | running      | 1566  | 0 days, 4:14:10 | 0         | 0.0    | 0.03      | 17.8M        |
	| routing:pimd                | running      | 2038  | 0 days, 4:14:01 | 0         | 31.1   | 0.07      | 43.1M        |
	| routing:rib_manager         | running      | 1092  | 0 days, 4:14:20 | 0         | 57.7   | 2.59      | 1.6G         |
	| routing:rsvpd               | running      | 1867  | 0 days, 4:14:04 | 0         | 0.0    | 0.04      | 28.4M        |
	| routing:tunnel_dispatcher   | running      | 1041  | 0 days, 4:14:20 | 0         | 0.0    | 0.02      | 12.2M        |
	| rsyslog                     | running      | 8634  | 0 days, 3:42:22 | 3         | 0.0    | 0.01      | 4.5M         |
	| servers_manager             | running (up) | 1300  | 0 days, 4:14:15 | 0         | 0.0    | 0.61      | 390.2M       |
	| session_monitor             | running      | 1733  | 0 days, 4:14:07 | 0         | 0.8    | 0.11      | 69.0M        |
	| snmp_manager                | running      | 1275  | 0 days, 4:14:16 | 0         | 0.0    | 0.47      | 302.4M       |
	| snmp_probe_agent_if_mib     | running      | 1807  | 0 days, 4:14:06 | 0         | 0.0    | 0.69      | 441.5M       |
	| snmp_probe_agent_ip_mib     | running      | 1421  | 0 days, 4:14:13 | 0         | 0.0    | 0.68      | 433.7M       |
	| snmp_probe_agent_system_mib | running      | 1463  | 0 days, 4:14:12 | 0         | 0.3    | 0.63      | 403.8M       |
	| snmp_trap_agent             | running      | 1752  | 0 days, 4:14:06 | 0         | 0.3    | 0.47      | 301.0M       |
	| snmpd                       | running      | 1930  | 0 days, 4:14:03 | 0         | 0.6    | 0.02      | 11.4M        |
	| snmptrap_managerd           | running      | 1634  | 0 days, 4:14:08 | 0         | 0.0    | 0.02      | 13.8M        |
	| snmptrapd                   | running      | 1464  | 0 days, 4:14:12 | 0         | 0.0    | 0.01      | 8.3M         |
	| ssh_manager                 | running (up) | 2209  | 0 days, 4:13:57 | 0         | 0.0    | 0.6       | 384.6M       |
	| sshd_inband                 | running      | 1942  | 0 days, 4:14:03 | 0         | 0.0    | 0.05      | 34.0M        |
	| sshd_outband                | running      | 1851  | 0 days, 4:14:06 | 0         | 0.0    | 0.05      | 34.1M        |
	| syslog_relay                | running      | 1483  | 0 days, 4:14:11 | 0         | 0.0    | 0.05      | 32.2M        |
	| techsupport_manager         | running      | 1554  | 0 days, 4:14:10 | 0         | 0.3    | 0.78      | 497.9M       |
	| twamp_agent                 | running      | 2117  | 0 days, 4:13:59 | 0         | 0.0    | 0.6       | 383.7M       |
	| twampd                      | running      | 1505  | 0 days, 4:14:11 | 0         | 0.3    | 0.03      | 21.3M        |
	| udev_monitor                | running      | 1392  | 0 days, 4:14:13 | 0         | 0.0    | 0.01      | 4.7M         |
	| users_manager               | running (up) | 1769  | 0 days, 4:14:06 | 0         | 0.0    | 0.6       | 383.4M       |
	| yacron                      | running      | 1695  | 0 days, 4:14:07 | 0         | 0.0    | 0.06      | 38.1M        |

	Node type: NCP
	Node ID: 151
	        Operational: up
	        Model: NCP-36CD-S
	        Hardware Model: S9710-76D (configured: S9710-76D)
	        Uptime: 0 days, 4:13:03
	        Description: dn-ncp-151
	        Serial Number: WDY19C7N00014-P3
	        High-Availability Failures: N/A
	        Local-cluster ID: 6

	Container: datapath
	        State: running
	        Start time: 15-Jun-2023 12:14:37
	        Uptime: 0 days, 4:14:28
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent  | running      | 2568  | 0 days, 4:14:18 | 0         | 0.0    | 0.09      | 58.6M        |
	| hw_monitor_agent  | running      | 2567  | 0 days, 4:14:18 | 0         | 0.0    | 0.03      | 16.9M        |
	| infra:log_manager | running      | 2563  | 0 days, 4:14:18 | 0         | 0.0    | 0.61      | 386.0M       |
	| infra:sshd        | running      | 1421  | 0 days, 4:15:28 | 0         | 0.0    | 0.01      | 7.3M         |
	| udev_monitor      | running      | 2569  | 0 days, 4:14:18 | 0         | 0.0    | 0.01      | 4.9M         |
	| wb_agent          | running (up) | 1581  | 0 days, 4:15:21 | 0         | 247.9  | 14.41     | 9.0G         |
	| wb_fe_agent       | running (up) | 2570  | 0 days, 4:14:18 | 0         | 1.2

	### NC-AI Cluster system type ###
	dnRouter# show system details

	System Name: sysp204, System-Id: 5dd3ea41-e5ef-4b46-9345-47cda7c28368
	System Type: CL-AI-8K-400G ((SA-48CD-NCF), Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	System status: running
	System Start Time: 25-Jun-2023 12:15:39 UTC
	System Uptime: 0 days, 4:13:25
	System Boot Uptime: 0 days, 4:14:27
	Version: DNOS [19.0.0] build [411], Copyright 2022 DRIVENETS LTD.
	Environment:
		Location: N/A
		Floor: N/A
		Rack: N/A
	Contact: support@drivenets.com
	Fabric Minimum Links: N/A
	Fabric Minimum NCF: N/A
	NCC switchovers: 0
	Last NCC switchover: N/A
	Escalation-stop-failovers
		Max-failover(remaining): 2(2)
		Failover-period(remaining): 30min(0 days, 0:30:00)
	Recovery-mode: supported
	BGP NSR: N/A

	Node type: NCC
	Node ID: 0
		Operational: active-up
		Model: NCF-48CD
		Uptime: 0 days, 4:13:25
		Description: dn-ncc-0
		Serial Number:
		High-Availability Failures: N/A

	Container: management-engine
		State: running
		Start time: 15-Jun-2023 12:13:06
		Uptime: 0 days, 4:15:58
		Restart: 0
		High-Availability Failures: N/A

	| Process Name             | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|--------------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| cluster_manager          | running | 700   | 0 days, 4:14:32 | 0         | 1.3    | 1.09      | 694.4M       |
	| core:cluster_agent       | running | 728   | 0 days, 4:14:21 | 0         | 0.0    | 0.61      | 389.2M       |
	| core:transaction_manager | running | 741   | 0 days, 4:14:21 | 0         | 0.0    | 0.92      | 588.2M       |
	| ctrl_bond_ntpd           | running | 800   | 0 days, 4:14:19 | 0         | 0.0    | 0.01      | 5.0M         |
	| deployment_agent         | running | 743   | 0 days, 4:14:21 | 0         | 0.0    | 0.09      | 59.3M        |
	| docker_expose            | running | 924   | 0 days, 4:14:15 | 0         | 0.0    | 0.06      | 35.6M        |
	| event_manager            | running | 923   | 0 days, 4:14:15 | 0         | 0.3    | 0.62      | 397.1M       |
	| infra:log_manager        | running | 870   | 0 days, 4:14:18 | 0         | 0.0    | 0.63      | 405.0M       |
	| infra:sshd               | running | 664   | 0 days, 4:14:50 | 0         | 0.0    | 0.01      | 7.2M         |
	| ntpd                     | running | 949   | 0 days, 4:14:15 | 0         | 0.0    | 0.01      | 5.9M         |
	| oper_manager             | running | 878   | 0 days, 4:14:16 | 0         | 0.0    | 0.61      | 387.8M       |
	| rsyncd                   | running | 665   | 0 days, 4:14:50 | 0         | 0.0    | 0.0       | 2.2M         |
	| transaction_agent        | running | 777   | 0 days, 4:14:19 | 0         | 0.0    | 0.82      | 520.2M       |
	| yacron                   | running | 1039  | 0 days, 4:14:13 | 0         | 0.3    | 0.06      | 37.3M        |

	Container: ncc-conductor
	        State: running
	        Start time: 15-Jun-2023 12:13:09
	        Uptime: 0 days, 4:15:56
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State   | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-------------------+---------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent  | running | 780   | 0 days, 4:14:20 | 0         | 0.0    | 0.09      | 57.6M        |
	| deployment_api    | running | 767   | 0 days, 4:14:20 | 0         | 0.0    | 0.12      | 79.5M        |
	| deployment_server | running | 854   | 0 days, 4:14:17 | 0         | 0.3    | 0.13      | 82.7M        |
	| infra:log_manager | running | 790   | 0 days, 4:14:19 | 0         | 0.0    | 0.64      | 406.4M       |
	| infra:sshd        | running | 724   | 0 days, 4:14:42 | 0         | 0.0    | 0.01      | 7.1M         |
	| nginx             | running | 800   | 0 days, 4:14:20 | 0         | 0.0    | 0.01      | 7.4M         |
	| yacron_conductor  | running | 890   | 0 days, 4:14:16 | 0         | 0.3    | 0.06      | 37.8M        |

	Container: node-manager
	        State: running
	        Start time: 15-Jun-2023 12:13:07
	        Uptime: 0 days, 4:15:58
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| auth_logger            | running      | 4030  | 0 days, 4:14:23 | 0         | 0.6    | 0.05      | 33.9M        |
	| deployment_agent       | running      | 3964  | 0 days, 4:14:22 | 0         | 0.0    | 0.09      | 58.8M        |
	| disk_usage_manager     | running      | 3957  | 0 days, 4:14:22 | 0         | 0.0    | 0.12      | 77.4M        |
	| docker_expose          | running      | 3948  | 0 days, 4:14:22 | 0         | 0.3    | 0.05      | 35.0M        |
	| infra:log_manager      | running      | 3970  | 0 days, 4:14:23 | 0         | 0.0    | 0.61      | 386.4M       |
	| infra:sshd             | running      | 3477  | 0 days, 4:15:13 | 0         | 0.0    | 0.01      | 7.4M         |
	| ipmi_watchdog_logger   | running      | 3930  | 0 days, 4:14:22 | 0         | 0.0    | 0.02      | 12.0M        |
	| management_agent       | running (up) | 3937  | 0 days, 4:14:22 | 0         | 2.9    | 0.63      | 402.2M       |
	| mgmt_interface_manager | running      | 3952  | 0 days, 4:14:22 | 0         | 0.6    | 0.49      | 314.7M       |
	| ntpd                   | running      | 3476  | 0 days, 4:15:13 | 0         | 0.0    | 0.01      | 5.8M         |
	| rsyncd                 | running      | 3478  | 0 days, 4:15:13 | 0         | 0.0    | 0.01      | 5.0M         |
	| sys_info               | running      | 3958  | 0 days, 4:14:22 | 0         | 0.0    | 0.01      | 3.4M         |
	| yacron                 | running      | 3998  | 0 days, 4:14:23 | 0         | 0.0    | 0.06      | 38.1M        |

	Container: routing-engine
	        State: running
	        Start time: 15-Jun-2023 12:13:10
	        Uptime: 0 days, 4:15:55
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name                | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-----------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| bgpd_authentication_logger  | running      | 1011  | 0 days, 4:14:22 | 0         | 0.0    | 0.05      | 33.4M        |
	| console_ttyS0               | running      | 1192  | 0 days, 4:14:18 | 0         | 0.0    | 0.01      | 4.7M         |
	| core:re_interfaces_agent    | running (up) | 1241  | 0 days, 4:14:17 | 0         | 0.0    | 0.6       | 384.8M       |
	| core:routing_manager        | running (up) | 1330  | 0 days, 4:14:16 | 0         | 1.4    | 0.64      | 407.4M       |
	| core:rsyncd                 | running      | 964   | 0 days, 4:14:40 | 0         | 0.0    | 0.0       | 2.2M         |
	| deployment_agent            | running      | 1908  | 0 days, 4:14:03 | 0         | 0.0    | 0.09      | 58.5M        |
	| gnmi_agent                  | running      | 1361  | 0 days, 4:14:14 | 0         | 0.0    | 0.83      | 529.6M       |
	| gnmi_server                 | running      | 1134  | 0 days, 4:14:20 | 0         | 0.3    | 0.05      | 30.5M        |
	| infra:log_manager           | running      | 1960  | 0 days, 4:14:02 | 0         | 0.0    | 0.61      | 391.1M       |
	| infra:sshd                  | running      | 965   | 0 days, 4:14:40 | 0         | 0.0    | 0.01      | 7.1M         |
	| netconf_sshd_oob            | running      | 1029  | 0 days, 4:14:21 | 0         | 0.0    | 0.05      | 33.9M        |
	| netconf_sshd_ndvrf          | running      | 1039  | 0 days, 4:14:21 | 0         | 0.0    | 0.05      | 33.9M        |
	| netconf_sshd_inband         | running      | 1159  | 0 days, 4:14:20 | 0         | 0.0    | 0.05      | 33.9M        |
	| ntp_manager                 | running      | 1179  | 0 days, 4:14:20 | 0         | 0.0    | 0.61      | 387.5M       |
	| ntpd_external               | running      | 8561  | 0 days, 3:42:27 | 2         | 0.0    | 0.01      | 5.8M         |
	| re_interface_manager        | running (up) | 1209  | 0 days, 4:14:18 | 0         | 1.7    | 1.68      | 1.0G         |
	| routing:bgpd                | running      | 1018  | 0 days, 4:14:21 | 0         | 108.1  | 12.27     | 7.6G         |
	| routing:fibmgrd             | running      | 2092  | 0 days, 4:13:59 | 0         | 86.6   | 8.76      | 5.5G         |
	| routing:isisd               | running      | 1281  | 0 days, 4:14:16 | 0         | 0.3    | 0.04      | 24.1M        |
	| routing:ldpd                | running      | 1991  | 0 days, 4:14:01 | 0         | 0.0    | 0.02      | 13.4M        |
	| routing:oam                 | running      | 2286  | 0 days, 4:13:57 | 0         | 0.3    | 0.03      | 20.3M        |
	| routing:ospfd               | running      | 1566  | 0 days, 4:14:10 | 0         | 0.0    | 0.03      | 17.8M        |
	| routing:pimd                | running      | 2038  | 0 days, 4:14:01 | 0         | 31.1   | 0.07      | 43.1M        |
	| routing:rib_manager         | running      | 1092  | 0 days, 4:14:20 | 0         | 57.7   | 2.59      | 1.6G         |
	| routing:rsvpd               | running      | 1867  | 0 days, 4:14:04 | 0         | 0.0    | 0.04      | 28.4M        |
	| routing:tunnel_dispatcher   | running      | 1041  | 0 days, 4:14:20 | 0         | 0.0    | 0.02      | 12.2M        |
	| rsyslog                     | running      | 8634  | 0 days, 3:42:22 | 3         | 0.0    | 0.01      | 4.5M         |
	| servers_manager             | running (up) | 1300  | 0 days, 4:14:15 | 0         | 0.0    | 0.61      | 390.2M       |
	| session_monitor             | running      | 1733  | 0 days, 4:14:07 | 0         | 0.8    | 0.11      | 69.0M        |
	| snmp_manager                | running      | 1275  | 0 days, 4:14:16 | 0         | 0.0    | 0.47      | 302.4M       |
	| snmp_probe_agent_if_mib     | running      | 1807  | 0 days, 4:14:06 | 0         | 0.0    | 0.69      | 441.5M       |
	| snmp_probe_agent_ip_mib     | running      | 1421  | 0 days, 4:14:13 | 0         | 0.0    | 0.68      | 433.7M       |
	| snmp_probe_agent_system_mib | running      | 1463  | 0 days, 4:14:12 | 0         | 0.3    | 0.63      | 403.8M       |
	| snmp_trap_agent             | running      | 1752  | 0 days, 4:14:06 | 0         | 0.3    | 0.47      | 301.0M       |
	| snmpd                       | running      | 1930  | 0 days, 4:14:03 | 0         | 0.6    | 0.02      | 11.4M        |
	| snmptrap_managerd           | running      | 1634  | 0 days, 4:14:08 | 0         | 0.0    | 0.02      | 13.8M        |
	| snmptrapd                   | running      | 1464  | 0 days, 4:14:12 | 0         | 0.0    | 0.01      | 8.3M         |
	| ssh_manager                 | running (up) | 2209  | 0 days, 4:13:57 | 0         | 0.0    | 0.6       | 384.6M       |
	| sshd_inband                 | running      | 1942  | 0 days, 4:14:03 | 0         | 0.0    | 0.05      | 34.0M        |
	| sshd_outband                | running      | 1851  | 0 days, 4:14:06 | 0         | 0.0    | 0.05      | 34.1M        |
	| syslog_relay                | running      | 1483  | 0 days, 4:14:11 | 0         | 0.0    | 0.05      | 32.2M        |
	| techsupport_manager         | running      | 1554  | 0 days, 4:14:10 | 0         | 0.3    | 0.78      | 497.9M       |
	| twamp_agent                 | running      | 2117  | 0 days, 4:13:59 | 0         | 0.0    | 0.6       | 383.7M       |
	| twampd                      | running      | 1505  | 0 days, 4:14:11 | 0         | 0.3    | 0.03      | 21.3M        |
	| udev_monitor                | running      | 1392  | 0 days, 4:14:13 | 0         | 0.0    | 0.01      | 4.7M         |
	| users_manager               | running (up) | 1769  | 0 days, 4:14:06 | 0         | 0.0    | 0.6       | 383.4M       |
	| yacron                      | running      | 1695  | 0 days, 4:14:07 | 0         | 0.0    | 0.06      | 38.1M        |

	Node type: NCF
	Node ID: 412
	        Operational: up
	        Model: NCF-48CD
	        Hardware Model: S9705-48D (configured: S9705-48D)
	        Uptime: 0 days, 4:13:03
	        Description: dn-ncf-412
	        Serial Number: WDY19C7N00014-P3
	        High-Availability Failures: N/A
	        Fabric-mode: three-stage-spine
	        vNCF ID: 16

	Container: fabric
	        State: running
	        Start time: 19-Jun-2023 11:42:50
	        Uptime: 1 day, 18:41:14
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|-------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| deployment_agent  | running      | 1590  | 1 day, 18:39:30 | 0         | 0.0    | 0.09      | 58.6M        |
	| fabric_agent      | running (up) | 1447  | 1 day, 18:39:31 | 0         | 0.0    | 0.54      | 341.9M       |
	| fabric_manager    | running (up) | 1453  | 1 day, 18:39:31 | 0         | 40.1   | 1.38      | 879.8M       |
	| hw_monitor_agent  | running      | 1532  | 1 day, 18:39:32 | 0         | 1.0    | 0.03      | 17.1M        |
	| infra:log_manager | running      | 1554  | 1 day, 18:39:30 | 0         | 0.0    | 0.76      | 483.6M       |
	| infra:sshd        | running      | 1407  | 1 day, 18:39:59 | 0         | 0.0    | 0.01      | 7.3M         |

	Container: node-manager
	        State: running
	        Start time: 15-Jun-2023 11:42:30
	        Uptime: 1 day, 18:41:34
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State        | PID   | Uptime          | Restart   | CPU%   | Memory%   | PHY-Memory   |
	|------------------------+--------------+-------+-----------------+-----------+--------+-----------+--------------|
	| auth_logger            | running      | 2865  | 1 day, 18:40:33 | 0         | 0.0    | 0.05      | 33.9M        |
	| deployment_agent       | running      | 2876  | 1 day, 18:40:33 | 0         | 0.0    | 0.09      | 58.8M        |
	| disk_usage_manager     | running      | 2846  | 1 day, 18:40:33 | 0         | 0.3    | 0.12      | 77.8M        |
	| inotify_rsync          | running      | 2856  | 1 day, 18:40:33 | 0         | 0.0    | 0.05      | 29.5M        |
	| infra:log_manager      | running      | 2884  | 1 day, 18:40:33 | 0         | 0.0    | 0.77      | 490.3M       |
	| infra:sshd             | running      | 2686  | 1 day, 18:40:39 | 0         | 0.0    | 0.01      | 6.9M         |
	| lldpd                  | running      | 2683  | 1 day, 18:40:39 | 0         | 0.0    | 0.01      | 5.9M         |
	| management_agent       | running (up) | 2850  | 1 day, 18:40:33 | 0         | 2.6    | 0.79      | 501.7M       |
	| mgmt_interface_manager | running      | 2859  | 1 day, 18:40:33 | 0         | 1.6    | 0.47      | 302.8M       |
	| ntpd                   | running      | 2685  | 1 day, 18:40:39 | 0         | 0.0    | 0.01      | 5.8M         |
	| rsyncd                 | running      | 2687  | 1 day, 18:40:39 | 0         | 0.0    | 0.01      | 4.9M         |
	| sys_info               | running      | 2866  | 1 day, 18:40:33 | 0         | 0.0    | 0.01      | 3.5M         |
	| yacron                 | running      | 2864  | 1 day, 18:40:33 | 0         | 0.0    | 0.06      | 38.2M        |

.. **Help line:** show system detailed information

**Command History**

+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                                                                 |
+=========+==============================================================================================================================================================+
| 5.1.0   | Command introduced                                                                                                                                           |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 6.0     | Removed system-id from the information is displayed on the system                                                                                            |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 10.0    | Updated to new NCR architecture                                                                                                                              |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 11.0    | Added fabric-min-links and serial number to the output                                                                                                       |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 11.5    | Switchover time and reason added to the output.                                                                                                              |
|         | Added option to display detailed system information and to filter per node, container, and process. This command replaces the show system processes command. |
|         | Added uptime shows (boot uptime, start time, system active uptime).                                                                                          |
|         | Added table displaying nodes that are being upgraded.                                                                                                        |
|         | Corrected operational states                                                                                                                                 |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 13.0    | Added process state filter to display processes matching a specific state.                                                                                   |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 13.3    | Added BGP NSR state to the detailed output                                                                                                                   |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 15.1    | Added support for new cluster types                                                                                                                          |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 17.2    | Split the build number from the DNOS version                                                                                                                 |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 19.10   | Added NC-AI Cluster type support                                                                                                                             |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
