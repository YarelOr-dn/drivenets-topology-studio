show system
------------

**Minimum user role:** viewer

The show system command displays information on the NCCs and NCPs. There are up to 2 NCCs per NCR, where one is active and the other is stand-by.

After configuring system information, it is recommended that you verify that your configuration and make changes as necessary.

To check the system's configuration:

**Command syntax: show system**

**Command mode:** operational



**Note**

- Every node type includes information about all containers and the process running in them, such that each container includes a table detailing the processes running in that container: node 1 > container 1 > processes in container 1 > container 2 > processes running in container 2 > container 3... node 2 ...

- System active uptime denotes the time since the cluster has an active NCC and its state is "up".

- The serial number displayed per node, is the box's hardware S/N from the ODM.

- In a standalone system, the NCC is a virtual node and therefore no serial number is displayed. The box's serial number is reflected on the NCP node.

.. - Last NCC switchover uses system timestamp, not required to update timestamp if system time changes (due to NTP or user reconfig)

	- "Nodes in upgrade" table presents nodes that are currently in baseos/firmware upgrade state.

	- When node finish baseos/ugpgrade state successfully, it moves to the "System node" table and removed from "Nodes in upgrade" table.

	- "Nodes in upgrade" table is not presented when there are no nodes that are currently in upgrade state.

	- system-active-uptime - time since there is an Active NCC in the cluster and it's state is Up.

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
| process-state  | Displays information on entities matching the specified state.                                                                            | - running                                                                 |
|                |                                                                                                                                           | - down                                                                    |
|                |                                                                                                                                           | - failed                                                                  |
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

The following information is displayed on each component (NCC or NCP):

+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter     | Description                                                                                                                                                                                  |
+===============+==============================================================================================================================================================================================+
| Type          | Indicates whether the NCR component is an NCC, NCP, NCF, or NCM.                                                                                                                             |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ID            | The ID of the Network Cloud Element:                                                                                                                                                         |
|               | - For NCC, the ID can be 0 or 1 (there can be up to 2 NCCs per NCR. The ID is automatically given to the first NCC that is configured, regardless of whether it is active or not.            |
|               | - For NCP, the ID can be 0..249. ID 0 indicates a standalone NCR.                                                                                                                            |
|               | - For NCF, the ID can be 0..611                                                                                                                                                              |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Admin         | The administrative state of the machine: enabled or disabled.                                                                                                                                |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Operational   | The operational state of the machine:                                                                                                                                                        |
|               |                                                                                                                                                                                              |
|               | NCC:                                                                                                                                                                                         |
|               |                                                                                                                                                                                              |
|               | - active-up - for NCC only - the machine is up and so is the active NCC                                                                                                                      |
|               | - standby-up - for NCC only - the machine is up and so is the standby NCC                                                                                                                    |
|               | - standby-not-ready - for NCC only - the standby machine is ready for switchover                                                                                                             |
|               | - initializing - the machine is in the initialization phase                                                                                                                                  |
|               | - failed - the machine has failed                                                                                                                                                            |
|               | - disconnected - the NCC is disconnected                                                                                                                                                     |
|               | - firmware-upgrade (in-progress)                                                                                                                                                             |
|               | - firmware-upgrade (failed)                                                                                                                                                                  |
|               | - baseos-upgrade (in-progress)                                                                                                                                                               |
|               | - baseos-upgrade (failed)                                                                                                                                                                    |
|               |                                                                                                                                                                                              |
|               | NCP:                                                                                                                                                                                         |
|               | - disconnected - the NCP is disconnected                                                                                                                                                     |
|               | - initializing (config-not-ready)                                                                                                                                                            |
|               | - initializing (config-sync) - the NCP is in the process of initialization (synchronizing its configuration)                                                                                 |
|               | - initializing (fib-sync) - the NCP is in the process of initialization (receiving the FIB updates from the NCC)                                                                             |
|               | - up - the machine is up and running                                                                                                                                                         |
|               | - admin-down - the machine is down (because its administrative state is disabled)                                                                                                            |
|               | - discovered - the machine has not been configured                                                                                                                                           |
|               | - failed (internal-error) - e.g. FIB sync has failed                                                                                                                                         |
|               | - failed (misconfig)                                                                                                                                                                         |
|               | - system-down - The NCP is connected to the DNOS cluster, but its network interfaces are down due to cluster constraints (i.e. the min-fabric-links or min-fabric-ncfs constraint violation) |
|               | - baseos-upgrade (in-progress:starting)                                                                                                                                                      |
|               | - baseos-upgrade (in-progress:download-image-start)                                                                                                                                          |
|               | - baseos-upgrade (in-progress:download-image-finished)                                                                                                                                       |
|               | - baseos-upgrade (in-progress:rebooting-to-installer)                                                                                                                                        |
|               | - baseos-upgrade (in-progress:disk-setup)                                                                                                                                                    |
|               | - baseos-upgrade (in-progress:pre-install-cleanup)                                                                                                                                           |
|               | - baseos-upgrade (in-progress:verify-checksum)                                                                                                                                               |
|               | - baseos-upgrade (in-progress:remove-existing-os)                                                                                                                                            |
|               | - baseos-upgrade (in-progress:extract-os)                                                                                                                                                    |
|               | - baseos-upgrade (in-progress:mount-volumes)                                                                                                                                                 |
|               | - baseos-upgrade (in-progress:setup-hostname)                                                                                                                                                |
|               | - baseos-upgrade (in-progress:write-system-info)                                                                                                                                             |
|               | - baseos-upgrade (in-progress:install-bootloader)                                                                                                                                            |
|               | - baseos-upgrade (failed)                                                                                                                                                                    |
|               | - firmware-upgrade (in-progress)                                                                                                                                                             |
|               | - firmware-upgrade (failed)                                                                                                                                                                  |
|               |                                                                                                                                                                                              |
|               | NCF                                                                                                                                                                                          |
|               | -  disconnected                                                                                                                                                                              |
|               | -  initializing (config-not-ready)                                                                                                                                                           |
|               | -  initializing (config-sync)                                                                                                                                                                |
|               | -  up                                                                                                                                                                                        |
|               | -  admin-down                                                                                                                                                                                |
|               | -  discovered                                                                                                                                                                                |
|               | -  failed (internal-error)                                                                                                                                                                   |
|               | -  failed (misconfig)                                                                                                                                                                        |
|               | -  baseos-upgrade (in-progress:starting)                                                                                                                                                     |
|               | -  baseos-upgrade (in-progress:download-image-start)                                                                                                                                         |
|               | -  baseos-upgrade (in-progress:download-image-finished)                                                                                                                                      |
|               | -  baseos-upgrade (in-progress:rebooting-to-installer)                                                                                                                                       |
|               | -  baseos-upgrade (in-progress:disk-setup)                                                                                                                                                   |
|               | -  baseos-upgrade (in-progress:pre-install-cleanup)                                                                                                                                          |
|               | -  baseos-upgrade (in-progress:verify-checksum)                                                                                                                                              |
|               | -  baseos-upgrade (in-progress:remove-existing-os)                                                                                                                                           |
|               | -  baseos-upgrade (in-progress:extract-os)                                                                                                                                                   |
|               | -  baseos-upgrade (in-progress:mount-volumes)                                                                                                                                                |
|               | -  baseos-upgrade (in-progress:setup-hostname)                                                                                                                                               |
|               | -  baseos-upgrade (in-progress:write-system-info)                                                                                                                                            |
|               | -  baseos-upgrade (in-progress:install-bootloader)                                                                                                                                           |
|               | -  baseos-upgrade (failed)                                                                                                                                                                   |
|               | -  firmware-upgrade (in-progress)                                                                                                                                                            |
|               | -  firmware-upgrade (failed)                                                                                                                                                                 |
|               |                                                                                                                                                                                              |
|               | NCM:                                                                                                                                                                                         |
|               | - up                                                                                                                                                                                         |
|               | - initializing                                                                                                                                                                               |
|               | - failed                                                                                                                                                                                     |
|               | - disconnected                                                                                                                                                                               |
|               | - firmware-upgrade (in-progress)                                                                                                                                                             |
|               | - firmware-upgrade (failed)                                                                                                                                                                  |
|               | - nos-upgrade (in-progress)                                                                                                                                                                  |
|               | - nos-upgrade (failed)                                                                                                                                                                       |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Model         | Indicates the model name of the component:                                                                                                                                                   |
|               |                                                                                                                                                                                              |
|               | NCC:                                                                                                                                                                                         |
|               | - NCP-40C                                                                                                                                                                                    |
|               | - X86                                                                                                                                                                                        |
|               |                                                                                                                                                                                              |
|               | NCP:                                                                                                                                                                                         |
|               | - NCP-40C                                                                                                                                                                                    |
|               | - NCP-10CD                                                                                                                                                                                   |
|               | - NCP-36CD-S                                                                                                                                                                                 |
|               | - NCP-64X12C-S                                                                                                                                                                               |
|               |                                                                                                                                                                                              |
|               | NCF:                                                                                                                                                                                         |
|               | - NCF-48CD                                                                                                                                                                                   |
|               |                                                                                                                                                                                              |
|               | NCM:                                                                                                                                                                                         |
|               | - NCM-48X-6C                                                                                                                                                                                 |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Uptime        | The total time that the machine has been running (days, hours:min:sec).                                                                                                                      |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Description   | The configured description for the system. See system info description.                                                                                                                      |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Serial Number | The serial number of the physical machine.                                                                                                                                                   |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	### Standalone system type ###
	dnRouter# show system

	System Name: dnRouter, System-Id: 122f258df84d6fc11f7dfd5ac88c61ab
	System Type: SA-40C, Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	System status: running
	System Start Time: 03-Mar-2020 17:56:48 UTC
	System Uptime: 1 days, 10:52:00
	System Boot Uptime: 1 days, 10:53:43
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.
	Environment:
		Location: SiteA
		Floor: 19
		Rack: R01
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

	| Node | ID   | Admin    | Operational     | Model          | Uptime           | Description      | Serial Number |
	|------+------+----------+-----------------+----------------+------------------+------------------+---------------|
	| NCC  | 0    |          | active-up       | NCP-40C        | 1 days, 10:52:00 | dn-ncc-0         | ABCDEF        |
	| NCP  | 0    | enabled  | up              | NCP-40C        | 1 days, 10:52:00 | dn-ncp-0         | XYZDEF        |


	### Cluster system type ###
	dnRouter# show system

	System Name: dnRouter, System-Id: 122f258df84d6fc11f7dfd5ac88c61ab
	System Type: CL-96, Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	System status: Upgrade (in-progress)
	System Start Time: 03-Mar-2020 17:56:48 UTC
	System Uptime: 1 days, 10:52:00
	System Boot Uptime: 1 days, 10:53:43
	Version: DNOS [17.2.0] build [411], Copyright 2022 DRIVENETS LTD.
	Environment:
		Location: SiteA
		Floor: 19
		Rack: R01
	Contact: support@drivenets.com
	Fabric Minimum Links: 7
	Fabric Minimum NCF: 6
	NCC switchovers: 2
	Last NCC switchover: 28-Sep-2022 06:10:13 UTC
	Escalation-stop-failovers
		Max-failover(remaining): 2(2)
		Failover-period(remaining): 30min(0 days, 0:30:00)
	Recovery-mode: supported
	BGP NSR: ready

	| Type | ID   | Admin   | Operational                     | Model          | Uptime           | Description      | Serial Number |
	|------+------+---------+---------------------------------+----------------+------------------+------------------+---------------|
	| NCC  | 0    |         | active-up                       | X86            |0 days, 00:10:15  | dn-ncc-0         | ABCDEF        |
	| NCC  | 1    |         | standby-up                      | X86            |                  | dn-ncc-1         | 123DEF        |
	| NCP  | 0    | enabled | up                              | NCP-40C        |1 days, 10:52:00  | dn-ncp-0         | XYZDEF        |
	| NCP  | 1    | enabled | failed (internal-error)         | NCP-40C        |0 days, 00:00:00  | dn-ncp-1         | 234DEF        |
	| NCP  | 2    | enabled | baseos-upgrade (in-progress)    | NCP-40C        |0 days, 00:00:00  | dn-ncp-2         | 234DEE        |
	| NCP  | 3    | enabled | firmware-upgrade (failed)       | NCP-40C        |0 days, 00:00:00  | dn-ncp-3         | 234DEJ        |
	| NCF  | 0    | enabled | up                              | NCF-48CD       |1 days, 10:52:00  | dn-ncf-0         | 345DEF        |
	| NCM  | A0   |         | up                              | NCM-48X-6C     |1 days, 10:52:00  | dn-ncm-A0        | 456DEF        |
	| NCM  | A1   |         | firmware-upgrade (in-progress)  | NCM-48X-6C     |1 days, 10:52:00  | dn-ncm-A1        | 456DFF        |
	| NCM  | B0   |         | up (pending-upgrade)            | NCM-48X-6C     |1 days, 10:52:00  | dn-ncm-B0        | 456DCF        |
	| NCM  | B1   |         | up (pending-upgrade)            | NCM-48X-6C     |1 days, 10:52:00  | dn-ncm-B1        | 456DDF        |

**Example**
::

	### AI Cluster system type ###
	dnRouter# show system

	System Name: dnRouter, System-Id: 122f258df84d6fc11f7dfd5ac88c61ab
	System Type: CL-AI-8K-400G (SA-36CD-S-NCP), Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	System status: running
	System Start Time: 03-Mar-2023 17:56:48 UTC
	System Uptime: 1 days, 10:52:00
	System Boot Uptime: 1 days, 10:53:43
	Version: DNOS [19.0.0] build [411], Copyright 2022 DRIVENETS LTD.
	Environment:
		Location: SiteA
		Floor: 19
		Rack: R01
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

	| Node | ID   | Admin    | Operational     | Model          | Uptime           | Description      | Serial Number |
	|------+------+----------+-----------------+----------------+------------------+------------------+---------------|
	| NCC  | 0    |          | active-up       | NCP-36CD-S     | 1 days, 10:52:00 | dn-ncc-0         | ABCDEF        |
	| NCP  | 150  | enabled  | up              | NCP-36CD-S     | 1 days, 10:52:00 | dn-ncp-150       | XYZDEF        |

**Example**
::

	### AI Cluster system type ###
	dnRouter# show system

	System Name: dnRouter, System-Id: 122f258df84d6fc11f7dfd5ac88c61ab
	System Type: CL-AI-8K-400G (SA-48CD-NCF), Family: NCR
	Enterprise-Id: 49739
	Description: DRIVENETS Network Cloud Router
	System status: running
	System Start Time: 03-Mar-2023 17:56:48 UTC
	System Uptime: 1 days, 10:52:00
	System Boot Uptime: 1 days, 10:53:43
	Version: DNOS [19.0.0] build [411], Copyright 2022 DRIVENETS LTD.
	Environment:
		Location: SiteA
		Floor: 19
		Rack: R01
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

	| Node | ID   | Admin    | Operational     | Model          | Uptime           | Description      | Serial Number |
	|------+------+----------+-----------------+----------------+------------------+------------------+---------------|
	| NCC  | 0    |          | active-up       | NCF-48CD       | 1 days, 10:52:00 | dn-ncc-0         | ABCDEF        |
	| NCF  | 411  | enabled  | up              | NCF-48CD       | 1 days, 10:52:00 | dn-ncf-411       | XYZDEF        |

.. **Help line:** show system information

**TACACS role:** viewer

**Note:**
- Last NCC switchover uses system timestamp, not required to update timestamp if system time changes (due to NTP or user reconfig)

- system-active-uptime - time since there is an Active NCC in the cluster and it's state is Up


**Help line:** show system information

**Command History**

+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                                                                   |
+=========+================================================================================================================================================================+
| 5.1.0   | Command introduced                                                                                                                                             |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 6.0     | Removed system-id from the information is displayed on the system                                                                                              |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 10.0    | Updated to new NCR architecture                                                                                                                                |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 11.0    | Added fabric-min-links and serial number to the output                                                                                                         |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 11.5    | - Switchover time and reason added to the output.                                                                                                              |
|         | - Added option to display detailed system information and to filter per node, container, and process. This command replaces the show system processes command. |
|         | - Added uptime shows (boot uptime, start time, system active uptime).                                                                                          |
|         | - Added table displaying nodes that are being upgraded.                                                                                                        |
|         | - Corrected operational states                                                                                                                                 |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 13.0    | Added process state filter to display processes matching a specific state.                                                                                     |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 13.3    | Added BGP NSR state to the detailed output                                                                                                                     |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 15.1    | Added support for new cluster types                                                                                                                            |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 16.1    | Added support for CL-51 and CL-76 cluster-type, and NCP-36CD-S NCP model                                                                                       |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 17.1    | Modified table width to support hardware model name                                                                                                            |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 17.2    | - Split the build number from the DNOS version                                                                                                                 |
|         | - Added support for NCP-64X12C-S NCP (lite) model                                                                                                              |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 18.0    | - Added support for static hybrid cluster types CL-49 and CL-86                                                                                                |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 18.1    | Added support for CL-153 cluster-type                                                                                                                          |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 18.2    | Removed "fabric type" lines                                                                                                                                    |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 19.10   | Added NC-AI Cluster type support                                                                                                                               |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
