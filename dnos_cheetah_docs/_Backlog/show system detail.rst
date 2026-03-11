show system detail
------------------

**Command syntax: show system** { detail | { ncc [ncc-id] | ncp [ncp-id] | ncf [ncf-id] | ncm [ncm-id] } container [container-name] process [process-name] state [state] }

**Description:** show system information

System displays information regarding all nodes in cluster: NCC, NCP, NCF and NCM

There are maximum of 2 NCC per cluster. One is active, the other one is standby

First NCC configured is NCC-0, the second is NCC-1

For configured NCP, NCP-Type column shows the configured type.

For unconfigured NCP (discovered), NCP-Type column shows the actual type received by the NCP (valid only for cluster type).

Detail - display detailed information of software state in every DNOS cluster entity

ncc [ncc-id] container [container-name] process [process-name] - filter to display a specific DNOS cluster entity. Can use any combination of the filters

state [state] - Display entity matching the specified state

**CLI example:**
::

	### Standalone system type ###
	dnRouter# show system detail
	System Name: dnRouter, System-Id: 122f258df84d6fc11f7dfd5ac88c61ab
	System Type: SA-4, Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	Uptime: 1 days, 10:52:00
	Version: DNOS [10.0.0.0], Copyright 2019 DRIVENETS LTD
	


	System Name: dnRouter, System-Id: 417c0643-236b-4013-9752-54d606f1ea6f
	System Type: SA-40C, Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	Uptime: 0 days, 1:01:18
	Version: DNOS [11.5.0.1], Copyright 2019 DRIVENETS LTD.
	Environment:
		Location: IL
		Floor: 1
		Rack: 1
	Contact: support@drivenets.com
	Fabric Minimum Links: N/A
	Fabric Minimum NCF: N/A
	NCC switchovers: 0
	Last NCC switchover: N/A

	Node type: NCC
	Node ID: 0
		Operational: active-up
		Model: NCP-40C
		Uptime: 0 days, 1:00:44
		Description: dn-ncc-0
		Serial Number:
		High-Availability Failures: N/A

	Container: HA-PRV-134_management-engine.1.94irbaakk7iz00tuzy3wxg64s
		State: running
		Start time: 31-Oct-2019 08:49:47
		Uptime: 0 days, 1:03:23
		Restart: 0
		High-Availability Failures: N/A

	| Process Name             | State   |   PID | Uptime          |   Restart |
	|--------------------------+---------+-------+-----------------+-----------|
	| cluster_manager          | running |   832 | 0 days, 1:00:59 |         0 |
	| core:cluster_agent       | running |   805 | 0 days, 1:01:01 |         0 |
	| core:transaction_manager | running |   785 | 0 days, 1:01:01 |         0 |
	| ctrl_bond_ntpd           | running |   281 | 0 days, 1:01:37 |         0 |
	| deployment_agent         | running |   274 | 0 days, 1:01:37 |         0 |
	| docker_expose            | running |   291 | 0 days, 1:01:36 |         0 |
	| docker_manager           | running |   273 | 0 days, 1:01:37 |         0 |
	| event_manager            | running |   290 | 0 days, 1:01:36 |         0 |
	| fluentd                  | running |   277 | 0 days, 1:01:37 |         0 |
	| infra:log_manager        | running |   282 | 0 days, 1:01:36 |         0 |
	| infra:sshd               | running |   283 | 0 days, 1:01:36 |         0 |
	| ka_mesh                  | running |   280 | 0 days, 1:01:37 |         0 |
	| memmon                   | running |   272 | 0 days, 1:01:37 |         0 |
	| ntpd                     | running |   292 | 0 days, 1:01:36 |         0 |
	| oper_manager             | running |   286 | 0 days, 1:01:36 |         0 |
	| re_bridge                | running |   791 | 0 days, 1:01:00 |         0 |
	| yacron                   | running |   278 | 0 days, 1:01:37 |         0 |

	Container: HA-PRV-134_ncc-conductor.1.kgpq71amnbod9ovy0mjor3k1u
	        State: running
	        Start time: 31-Oct-2019 08:49:53
	        Uptime: 0 days, 1:03:18
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name        | State   |   PID | Uptime          |   Restart |
	|---------------------+---------+-------+-----------------+-----------|
	| cluster_rebalance   | running |   380 | 0 days, 1:01:53 |         0 |
	| deployment_agent    | running |   377 | 0 days, 1:01:53 |         0 |
	| deployment_api      | running |   392 | 0 days, 1:01:54 |         0 |
	| deployment_server   | running |   375 | 0 days, 1:01:53 |         0 |
	| dhcpd               | running |   378 | 0 days, 1:01:53 |         0 |
	| dhcpd_monitor       | running |   376 | 0 days, 1:01:53 |         0 |
	| discovery_broadcast | running |   387 | 0 days, 1:01:54 |         0 |
	| infra:log_manager   | running |   384 | 0 days, 1:01:54 |         0 |
	| infra:sshd          | running |   385 | 0 days, 1:01:54 |         0 |
	| ka_mesh             | running |   382 | 0 days, 1:01:54 |         0 |
	| memmon              | running |   374 | 0 days, 1:01:53 |         0 |
	| nginx               | running |   394 | 0 days, 1:01:54 |         0 |
	| yacron              | running |   381 | 0 days, 1:01:54 |         0 |

	Container: HA-PRV-134_node-manager.xw0b8gwrx51lq10pvn7yea9hj.qvpginzfgs0ez
	        State: running
	        Start time: 31-Oct-2019 08:49:48
	        Uptime: 0 days, 1:03:23
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name           | State   |   PID | Uptime          |   Restart |
	|------------------------+---------+-------+-----------------+-----------|
	| deployment_agent       | running |   789 | 0 days, 1:01:20 |         0 |
	| docker_expose          | running |   803 | 0 days, 1:01:21 |         0 |
	| docker_stats           | running |   788 | 0 days, 1:01:20 |         0 |
	| fluentbit_agent        | running |   806 | 0 days, 1:01:21 |         0 |
	| infra:log_manager      | running |   795 | 0 days, 1:01:20 |         0 |
	| infra:sshd             | running |   796 | 0 days, 1:01:20 |         0 |
	| ka_mesh                | running |   794 | 0 days, 1:01:20 |         0 |
	| management_agent       | running |  1289 | 0 days, 1:01:05 |         1 |
	| memmon                 | running |   783 | 0 days, 1:01:20 |         0 |
	| mgmt_interface_manager | running |  1290 | 0 days, 1:01:05 |         1 |
	| monit                  | running |   811 | 0 days, 1:01:21 |         0 |
	| ntpd                   | running |   791 | 0 days, 1:01:20 |         0 |
	| re_bridge              | running |   801 | 0 days, 1:01:21 |         0 |
	| yacron                 | running |   785 | 0 days, 1:01:20 |         0 |

	Container: HA-PRV-134_routing-engine.xw0b8gwrx51lq10pvn7yea9hj.m3m73zwbgjg
	        State: running
	        Start time: 31-Oct-2019 08:49:48
	        Uptime: 0 days, 1:03:23
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name               | State        |   PID | Uptime          |   Restart |
	|----------------------------+--------------+-------+-----------------+-----------|
	| bgpd_authentication_logger | running      |   479 | 0 days, 1:02:00 |         0 |
	| core:re_interfaces_agent   | running (up) |  2068 | 0 days, 1:01:00 |         0 |
	| core:routing_manager       | running      |   470 | 0 days, 1:02:00 |         0 |
	| core:rsyncd                | running      |   471 | 0 days, 1:02:00 |         0 |
	| deployment_agent           | running      |   467 | 0 days, 1:02:00 |         0 |
	| gnmi                       | running      |   440 | 0 days, 1:02:00 |         0 |
	| infra:log_manager          | running      |   474 | 0 days, 1:02:00 |         0 |
	| infra:sshd                 | running      |   477 | 0 days, 1:02:00 |         0 |
	| ka_mesh                    | running      |   473 | 0 days, 1:02:00 |         0 |
	| memmon                     | running      |   439 | 0 days, 1:02:00 |         0 |
	| monit                      | running      |   483 | 0 days, 1:02:00 |         0 |
	| netconf_sshd_oob           | running      |   449 | 0 days, 1:02:00 |         0 |
	| netconf_sshd_inband        | running      |   447 | 0 days, 1:02:00 |         0 |
	| netconf_sshd_ndvrf         | running      |   448 | 0 days, 1:02:00 |         0 |
	| notification_manager       | running      |   478 | 0 days, 1:02:00 |         0 |
	| nscd                       | running      |   451 | 0 days, 1:02:00 |         0 |
	| ntp_manager                | running      |   465 | 0 days, 1:02:00 |         0 |
	| ntpd_external              | running      |  2567 | 0 days, 1:00:53 |         1 |
	| re_interface_manager       | running (up) |  2190 | 0 days, 1:00:59 |         0 |
	| routing:bgpd               | running      |  2304 | 0 days, 1:00:55 |         0 |
	| routing:fibmgrd            | running      |  2325 | 0 days, 1:00:54 |         0 |
	| routing:isisd              | running      |  2516 | 0 days, 1:00:53 |         0 |
	| routing:ldpd               | running      |  2401 | 0 days, 1:00:54 |         0 |
	| routing:oam                | running      |  2481 | 0 days, 1:00:53 |         0 |
	| routing:ospfd              | running      |  2505 | 0 days, 1:00:53 |         0 |
	| routing:rib_manager        | running      |  2113 | 0 days, 1:01:00 |         0 |
	| routing:rsvpd              | running      |  2403 | 0 days, 1:00:54 |         0 |
	| routing:tunnel_dispatcher  | running      |  2556 | 0 days, 1:00:53 |         0 |
	| rsyslog                    | running      |  2511 | 0 days, 1:00:53 |         1 |
	| servers_manager            | running      |   446 | 0 days, 1:02:00 |         0 |
	| snmp_manager               | running      |   443 | 0 days, 1:02:00 |         0 |
	| snmp_northbound            | running      |   442 | 0 days, 1:02:00 |         0 |
	| snmp_trap_agent            | running      |   456 | 0 days, 1:02:00 |         0 |
	| snmpd                      | running      |   455 | 0 days, 1:02:00 |         0 |
	| snmptrap_managerd          | running      |   444 | 0 days, 1:02:00 |         0 |
	| ssh_manager                | running      |   482 | 0 days, 1:02:00 |         0 |
	| sshd_inband                | running      |   450 | 0 days, 1:02:00 |         0 |
	| syslog_relay               | running      |   452 | 0 days, 1:02:00 |         0 |
	| techsupport_manager        | running      |   445 | 0 days, 1:02:00 |         0 |
	| twamp_agent                | running      |  2050 | 0 days, 1:01:01 |         0 |
	| twampd                     | running      |  2178 | 0 days, 1:00:59 |         0 |
	| udev_monitor               | running      |   468 | 0 days, 1:02:00 |         0 |
	| users_manager              | running      |   441 | 0 days, 1:02:00 |         0 |
	| yacron                     | running      |   454 | 0 days, 1:02:00 |         0 |

	Node type: NCP
	Node ID: 0
	        Operational: up
	        Model: NCP-40C
	        Uptime: 0 days, 0:59:37
	        Description: dn-ncp-0
	        Serial Number: WDY1957L0005B
	        High-Availability Failures: N/A

	Container: datapath
	        State: running
	        Start time: 31-Oct-2019 08:53:39
	        Uptime: 0 days, 0:59:32
	        Restart: 0
	        High-Availability Failures: N/A

	| Process Name      | State        |   PID | Uptime          |   Restart |
	|-------------------+--------------+-------+-----------------+-----------|
	| deployment_agent  | running      |   788 | 0 days, 1:01:44 |         0 |
	| infra:log_manager | running      |   792 | 0 days, 1:01:44 |         0 |
	| infra:sshd        | running      |   793 | 0 days, 1:01:44 |         0 |
	| ka_mesh           | running      |   797 | 0 days, 1:01:45 |         0 |
	| memmon            | running      |   786 | 0 days, 1:01:44 |         0 |
	| wb_agent          | running (up) |   973 | 0 days, 1:01:41 |         0 |
	| wb_fe_agent       | running (up) |   839 | 0 days, 1:01:45 |         0 |

	dnRouter# show system ncp 0			
	Node: NCP
	Node ID: 0
		Admin: enabled
		Operational status: active-up
		Model: NCP-40C
		Uptime: 1 days, 10:52:00
		Description: dn-ncp-0
		Serial Number: WC81917180023
		High-Availability Failures:	N/A


	Container: forwarding-engine
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name        | State        |   PID | Uptime          | Restart   |
	+---------------------+--------------+-------+-----------------+-----------|
	| deployment-agent    | running      |   684 | 1 day, 23:11:43 |         0 |
	| hw_monitor_agent    | running      |   674 | 1 day, 23:11:43 |         0 |
	| log_manager         | running      |   678 | 1 day, 23:11:43 |         0 |
	| sshd                | running      |   679 | 1 day, 23:11:43 |         0 |
	| ka_mesh             | running      |   676 | 1 day, 23:11:43 |         0 |
	| memmon              | running      |   672 | 1 day, 23:11:43 |         0 |
	| process_event_agent | running      |   673 | 1 day, 23:11:43 |         0 |
	| recovery_poller     | running      |   677 | 1 day, 23:11:43 |         0 |
	| wb_agent            | running (up) |   680 | 1 day, 23:11:43 |         0 |
	| wb_fe_agent         | running (up) |   712 | 1 day, 23:11:43 |         0 |

	dnRouter# show system ncc 0 container ncc_conductor-master
	Node: NCC
	Node ID: 0
		Admin: enabled
		Operational status: active-up
		Model: NCP-40C
		Uptime: 1 days, 10:52:00
		Description: dn-ncc-0
		Serial Number:  resides on NCP 0
		High-Availability Failures:	N/A

	Container: ncc_conductor-master
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name        | State   |   PID | Uptime          | Restart   | 
	+---------------------+---------+-------+-----------------+-----------|-
	| cluster_rebalance   | running |   316 | 1 day, 23:18:39 |         0 | 
	| deployment-agent    | running |   328 | 1 day, 23:18:39 |         0 | 
	| deployment-api      | running |   322 | 1 day, 23:18:39 |         0 | 
	| deployment-server   | running |   314 | 1 day, 23:18:39 |         0 | 
	| dhcpd               | running |   327 | 1 day, 23:18:39 |         0 | 
	| dhcpd_monitor       | running |   326 | 1 day, 23:18:39 |         0 | 
	| discovery-broadcast | running |   318 | 1 day, 23:18:39 |         0 | 
	| log_manager         | running |   320 | 1 day, 23:18:39 |         0 | 
	| sshd                | running |   321 | 1 day, 23:18:39 |         0 | 
	| ka_mesh             | running |   315 | 1 day, 23:18:39 |         0 | 
	| memmon              | running |   312 | 1 day, 23:18:39 |         0 | 
	| nginx               | running |   323 | 1 day, 23:18:39 |         0 | 
	| process_event_agent | running |   313 | 1 day, 23:18:39 |         0 | 
	| recovery_poller     | running |   319 | 1 day, 23:18:39 |         0 | 

	dnRouter# show system process ka-mesh
	Node: NCC
	Node ID: 0
		Admin: enabled
		Operational status: active-up
		Model: NCP-40C
		Uptime: 1 days, 10:52:00
		Description: dn-ncc-0
		Serial Number:  resides on NCP 0
		High-Availability Failures:	N/A


	Container: routing-engine
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name        | State   |   PID | Uptime          | Restart   |
	+---------------------+---------+-------+-----------------+-----------|
	| ka_mesh             | running |   315 | 1 day, 23:18:39 |         0 |

	Container: management-engine
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name        | State   |   PID | Uptime          | Restart   |
	+---------------------+---------+-------+-----------------+-----------|
	| ka_mesh             | running |   315 | 1 day, 23:18:39 |         0 |

	Container: ncc_conductor-master
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name        | State   |   PID | Uptime          | Restart   |
	+---------------------+---------+-------+-----------------+-----------|
	| ka_mesh             | running |   315 | 1 day, 23:18:39 |         0 |

	Container: node-manager
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name        | State   |   PID | Uptime          | Restart   |
	+---------------------+---------+-------+-----------------+-----------|
	| ka_mesh             | running |   315 | 1 day, 23:18:39 |         0 |
			
	Node: NCP
	Node ID: 0
		Admin: enabled
		Operational status: active-up
		Model: NCP-40C
		Uptime: 1 days, 10:52:00
		Description: dn-ncp-0
		Serial Number: WC81917180023
		High-Availability Failures:	N/A


	Container: forwarding-engine
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name        | State   |   PID | Uptime          |
	+---------------------+---------+-------+-----------------+
	| ka_mesh             | running |   315 | 1 day, 23:18:39 |


	### Large Cluster system type ###
	dnRouter# show system detail
	System Name: R15_Large_Core, System-Id: 80dce006-1db3-4233-ac1f-ebbeb5efad97
	System Type: CL-192, Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	Uptime: 0 days, 5:36:37
	Version: DNOS [11.2.0.89_dev], Copyright 2019 DRIVENETS LTD.
	Environment:
		Location: N/A
		Floor: N/A
		Rack: N/A
	Contact: support@drivenets.com
	Fabric Minimum Links: 7
	Fabric Minimum NCF: 11
	NCC switchovers: 0
	Last NCC switchover: N/A
	Last switchover reason:	N/A
	
	Node: NCC
	Node ID: 0
		Admin: enabled
		Operational status: active-up
		Model: X86
		Uptime: 0 days, 5:36:3
		Description: dn-ncc-0
		Serial Number:  CZJ91903L3
		High-Availability Failures:	N/A


	Container: routing-engine
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name               | State        |   PID | Uptime           | Restart   |
	+----------------------------+--------------+-------+------------------+-----------+
	| bgpd_authentication_logger | running      |   403 | 1 day, 22:30:17  |         0 |
	| re_interfaces_agent        | running (up) |   394 | 1 day, 22:30:17  |         0 |
	| routing_manager            | running      |   393 | 1 day, 22:30:17  |         0 |
	| rsyncd                     | running      |   395 | 1 day, 22:30:17  |         0 |
	| deployment-agent           | running      |   392 | 1 day, 22:30:17  |         0 |
	| gnmi                       | running      |   371 | 1 day, 22:30:17  |         0 |
	| log_manager                | running      |   397 | 1 day, 22:30:17  |         0 |
	| sshd                       | running      |   399 | 1 day, 22:30:17  |         0 |
	| ka_mesh                    | running      |   396 | 1 day, 22:30:17  |         0 |
	| memmon                     | running      |   369 | 1 day, 22:30:17  |         0 |
	| monit                      | running      |   405 | 1 day, 22:30:17  |         0 |
	...

	Container: management-engine
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name        | State   |   PID | Uptime          | Restart   |
	+---------------------+---------+-------+-----------------+-----------|
	| cluster_manager     | running |   606 | 1 day, 22:52:46 |         0 |
	| cluster_agent       | running |   244 | 1 day, 22:52:50 |         0 |
	| transaction_manager | running |   245 | 1 day, 22:52:50 |         0 |
	| ctrl-bond-ntpd      | running |   252 | 1 day, 22:52:50 |         0 |
	| deployment-agent    | running |   261 | 1 day, 22:52:50 |         0 |
	| docker_expose       | running |   263 | 1 day, 22:52:50 |         0 |
	| docker_manager      | running |   243 | 1 day, 22:52:50 |         0 |
	| event_manager       | running |   262 | 1 day, 22:52:50 |         0 |
	| fluentd             | running |   249 | 1 day, 22:52:50 |         0 |
	| global_ha           | running |   250 | 1 day, 22:52:50 |         0 |
	| log_manager         | running |   254 | 1 day, 22:52:50 |         0 |
	| sshd                | running |   255 | 1 day, 22:52:50 |         0 |
	| ka_mesh             | running |   251 | 1 day, 22:52:50 |         0 |
	| ntpd                | running |   264 | 1 day, 22:52:50 |         0 |
	| oper_manager        | running |   259 | 1 day, 22:52:50 |         0 |
	| process_event_agent | running |   242 | 1 day, 22:52:50 |         0 |
	| recovery_poller     | running |   253 | 1 day, 22:52:50 |         0 |
	| yacron              | running |   258 | 1 day, 22:52:50 |         0 |

	Container: node-manager
		State: running
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A			

		...

	Container: ncc_conductor-master
	...

	Node: NCF
	Node ID: 0
		Admin: enabled
		Operational status: up
		Model: NCP-48CD
		Uptime: 0 days, 5:28:18
		Description: dn-ncf-0
		Serial Number: WEB1947800037
		High-Availability Failures:	N/A

	Container: fabric
		State: running
		Start time: 11-Sep-2019 11:54:32 	
		Uptime: 0 days, 5:40:42
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name              | State        |   PID | Uptime          | Restart   |
	+---------------------------+--------------+-------+-----------------+-----------|
	| deployment_agent          | running      |  1107 | 0 days, 5:40:42 |         0 |
	| fabric_agent              | running (up) |  1113 | 0 days, 5:40:42 |         0 |
	| fabric_manager            | running (up) |  1290 | 0 days, 5:40:41 |         0 |
	| hw_monitor_agent          | running      |  1106 | 0 days, 5:40:42 |         0 |
	| log_manager               | running      |  1111 | 0 days, 5:40:42 |         0 |
	| sshd                      | running      |  1112 | 0 days, 5:40:42 |         0 |
	| ka_mesh                   | running      |  1109 | 0 days, 5:40:42 |         0 |
	| memmon                    | running      |  1104 | 0 days, 5:40:42 |         0 |
	| process_event_agent       | running      |  1105 | 0 days, 5:40:42 |         0 |
	| recovery_poller           | running      |  1110 | 0 days, 5:40:42 |         0 |

		Container: node-manager
			State: running
			Start time: 11-Sep-2019 11:54:10 	
			Uptime: 0 days, 5:41:0
			Restart: 0
			High-Availability Failures:	N/A

			Process list:
			...

	Node: NCP
	...

	Node: NCM
	Node ID: A0
		Admin: enabled
		Operational status: up
		Model: NCM-48X-6C
		Uptime: 0 days, 9:37:30
		Description: dn-ncm-A0
		Serial Number: AAF1920AAAP
		High-Availability Failures:	N/A

	Node: NCM
	Node ID: B0
		Admin: enabled
		Operational status: up
		Model: NCM-48X-6C
		Uptime: 0 days, 9:37:30
		Description: dn-ncm-B0
		Serial Number: AAF1920AABZ
		High-Availability Failures:	N/A		
		
	...		

	dnRouter# show system ncc 0 container management-engine state down
	Node: NCC
	Node ID: 0
		Admin: enabled
		Operational status: active-up (partially) 
		Model: X86
		Uptime: 0 days, 5:36:3
		Description: dn-ncc-0
		Serial Number:  CZJ91903L3
		High-Availability Failures:	N/A


	Container: management-engine
		State: running (partially) 
		Start time: 2017-Jan-06 22:42:00 	
		Uptime: 1 days, 00:00:00
		Restart: 0
		High-Availability Failures:	N/A

	Process list:
	| Process Name        | State   |   PID | Uptime          | Restart   |
	+---------------------+---------+-------+-----------------+-----------|
	| log_manager         | down    |   606 | 1 day, 22:52:46 |         0 |

**Command mode:** operational

**TACACS role:** viewer

**Note:**
- Filter combanation should only be allowed according for Cluster type. For example, in SA there shouldn't be ncm filter.

- When there is also sub-status to the NCE, it will be displayed as "Operational status: <status> (<sub-status>)"

**Help line:** show system detailed information

**Parameter table:**

+----------------+--------------------------------------------------------------+---------------+
| Parameter      | Values                                                       | Default value |
+================+==============================================================+===============+
| Node-name      | ncp                                                          |               |
|                |                                                              |               |
|                | ncc                                                          |               |
|                |                                                              |               |
|                | ncf                                                          |               |
+----------------+--------------------------------------------------------------+---------------+
| ncc-id         | 0-1                                                          |               |
+----------------+--------------------------------------------------------------+---------------+
| ncp-id         | 0-(Cluster type max NCP number-1)                            |               |
+----------------+--------------------------------------------------------------+---------------+
| ncf-id         | 0-(Cluster type max NCF number-1)                            |               |
+----------------+--------------------------------------------------------------+---------------+
| Container-name | Any container from process list relative to the node name    |               |
+----------------+--------------------------------------------------------------+---------------+
| Process-name   | Any process from process list                                |               |
+----------------+--------------------------------------------------------------+---------------+
| state          | up, initializing, down, failed, active-up, standby-up,       |               |
|                | standby-not-ready, disconnected, in-upgrade, upgrade-failure |               |
+----------------+--------------------------------------------------------------+---------------+
