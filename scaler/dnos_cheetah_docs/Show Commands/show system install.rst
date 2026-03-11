show system install
--------------------

**Minimum user role:** viewer

To display information regarding ongoing system-wide installation or revert processes:

**Command syntax: show system install**

**Command mode:** operational

**Example**
::

	dnRouter# show system install

	Task ID: 43124
	Installation type: upgrade
	Task status: in-progress
	Task start time: 11-Dec-2019 13:58:14 UTC
	Task elapsed time: 00:16:37

	Installed Packages:

	  | Type       | Version | Name                                     | HW Model      | HW Revision   |
	  |------------+---------+------------------------------------------+---------------+---------------|
	  | DNOS       | 16.1    | drivenets_dnos_v16.1.tar                 |               |               |
	  | BaseOS     | 1.601   | drivenets_baseos_1.602.tar               |               |               |
	  | NCM-NOS    | 1.2.0   | drivenets_stratax_1.1.0.tar              |               |               |
	  | Firmware   | 5.2     | ufi-wbx-fw-5.2                           | S9700-53DX    | 2, Build: 4   |
	  | Firmware   | 5.3     | ufi-wbx-fw-5.3                           | S9700-53DX    | 4, Build: 3   |
	  | ONIE       | 2021-03 | drivenets_onie_2019-06.0_s9700_53dx      | S9700-53DX    | default       |


	Running tasks:

	  | Node Type | Node ID | Serial Number | Package Type | Start time               | Elapsed time | Estimated Completion Time | Source Version               | Target Version              |
	  |-----------+---------+---------------+--------------+--------------------------+--------------|---------------------------|------------------------------|-----------------------------|
	  | NCP       | 2       | 234DEE        | DNOS         | 11-Dec-2019 13:58:14 UTC | 00:04:20     | 11-Dec-2019 14:03:14      |	drivenets_dnos_v16.1.tar    | drivenets_dnos_v16.2.tar    |
	  | NCP       | 3       | 2343EJ        | Firmware     | 11-Dec-2019 13:58:14 UTC | 00:04:05     | 11-Dec-2019 14:03:14      |	ufi-wbx-fw-5.2              | ufi-wbx-fw-5.3              |
	  | NCM       | A1      | 2344EJ        | NCM-NOS      | 11-Dec-2019 13:58:14 UTC | 00:03:15     | 11-Dec-2019 14:03:14      |	drivenets_stratax_1.1.0.tar | drivenets_stratax_1.1.1.tar |


	Finished tasks:

	  | Node Type | Node ID | Serial Number | Package Type | Task status   | Start time               | Finish time              | Elapsed time | Source Version                       |  Target Version                     |
	  |-----------+---------+---------------+--------------+---------------+--------------------------+--------------------------+--------------|--------------------------------------|-------------------------------------|
	  | NCC       | 1       | 234DEJ        | BaseOS        | completed    | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:02:14 UTC | 00:04:00     | drivenets_baseos_1.602.tar           | drivenets_baseos_1.602.tar          |
	  | NCC       | 1       | 234DEJ        | DNOS          | completed    | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:13:14 UTC | 00:15:00     | drivenets_dnos_v16.1.tar             | drivenets_dnos_v16.2.tar            |
	  | NCP       | 1       | 534DEF        | ONIE          | completed    | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:01:29 UTC | 00:03:15     | drivenets_onie_2019-06.0_s9700_53dx  | drivenets_onie_2019-06.0_s9700_53dx |
	  | NCP       | 1       | 534DEF        | Firmware      | completed    | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:02:16 UTC | 00:04:02     | ufi-wbx-fw-5.2                       | ufi-wbx-fw-5.3                      |
	  | NCP       | 1       | 534DEE        | BaseOS        | completed    | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 13:59:59 UTC | 00:01:45     | drivenets_baseos_1.601.tar           | drivenets_baseos_1.602.tar          |
	  | NCP       | 1       | 534DEF        | DNOS          | failed       | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:13:14 UTC | 00:15:00     | drivenets_dnos_v16.1.tar             | drivenets_dnos_v16.2.tar            |
	  | NCP       | 2       | 234DEF        | BaseOS        | completed    | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 13:59:44 UTC | 00:01:30     | drivenets_baseos_1.601.tar           | drivenets_baseos_1.602.tar          |
	  | NCP       | 2       | 234DEE        | Firmware      | completed    | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:01:36 UTC | 00:03:22     | ufi-wbx-fw-5.2                       | ufi-wbx-fw-5.3                      |
	  | NCP       | 3       | 2343EJ        | Firmware      | failed       | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 13:58:14 UTC | 00:00:00     | ufi-wbx-fw-5.2                       | ufi-wbx-fw-5.3                      |
	  | NCM       | A0      | 2344EJ        | NCM-NOS       | completed    | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:00:41 UTC | 00:02:17     | drivenets_stratax_1.1.0.tar          | drivenets_stratax_1.1.1.tar         |



	dnRouter# show system install

	No installation task to show.


	dnRouter# show system install

	Task ID: 43126
	Installation type: revert
	Task status: in-progress
	Task start time: 11-Dec-2019 13:58:14 UTC
	Task elapsed time: 00:03:37

	Reverted Packages:

	  | Type       | Version | Name                                     |
	  |------------+---------+------------------------------------------+
	  | BaseOS     | 1.586   | drivenets_baseos_1.501.tar               |
	  | NCM-NOS    | 1.1.0   | drivenets_stratax_1.1.0.tar              |


	Running tasks:

	  | Node Type | Node ID | Serial Number | Package Type | Start time               | Elapsed time | Estimated Completion Time | Source Version               | Target Version              |
	  |-----------+---------+---------------+--------------+--------------------------+--------------|---------------------------|------------------------------|-----------------------------|
	  | NCM       | A1      | 2344EJ        | NCM-NOS      | 11-Dec-2019 13:58:14 UTC | 00:03:15     | 11-Dec-2019 14:03:14      |  drivenets_stratax_1.1.1.tar | drivenets_stratax_1.1.0.tar |


	Finished tasks:

	  | Node Type | Node ID | Serial Number | Package Type | Task status | Start time               | Finish time              | Elapsed time | Source Version              | Target Version               |
	  |-----------+---------+---------------+--------------+-------------+--------------------------+--------------------------+--------------|-----------------------------|------------------------------|
	  | NCC       | 0       | 234DEF        | BaseOS       | completed   | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 13:59:50 UTC | 00:01:36     | drivenets_baseos_1.502.tar  |  drivenets_baseos_1.501.tar  |
	  | NCC       | 1       | 234DEJ        | BaseOS       | completed   | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 13:59:46 UTC | 00:01:32     | drivenets_baseos_1.502.tar  |  drivenets_baseos_1.501.tar  |
	  | NCP       | 1       | 534DEE        | BaseOS       | completed   | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:00:04 UTC | 00:01:50     | drivenets_baseos_1.502.tar  |  drivenets_baseos_1.501.tar  | 
	  | NCP       | 2       | 234DEF        | BaseOS       | completed   | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:00:14 UTC | 00:02:00     | drivenets_baseos_1.502.tar  |  drivenets_baseos_1.501.tar  |
	  | NCM       | A0      | 2344EJ        | NCM-NOS      | completed   | 11-Dec-2019 13:58:14 UTC | 11-Dec-2019 14:01:25 UTC | 00:03:11     | drivenets_stratax_1.1.1.tar |  drivenets_stratax_1.1.0.tar |



.. **Help line:** show system install

.. **Parameter table:**


**Command History**

+---------+---------------------------------+
| Release | Modification                    |
+=========+=================================+
| 16.1    | Command introduced              |
+---------+---------------------------------+
| 18.2.1  | Added estimated completion time |
+---------+---------------------------------+
