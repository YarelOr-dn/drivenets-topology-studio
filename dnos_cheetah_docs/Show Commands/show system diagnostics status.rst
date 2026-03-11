show system diagnostics status
------------------------------

**Minimum user role:** viewer

To display a list of all configured diagnostics tests and their status:



**Command syntax: show system diagnostics status** test [test-type]

**Command mode:** operational



.. 
	**Internal Note**

	- State column shows the operations state of the test.

	- Interval - the configured test interval value per node-type and node-id.

	- Threshold - the configured consecutive failures threshold value per node-type and node-id.

	- State - the state of the test.

	- Running - the test is up and running.

	- Failed - the test is up but currently it fails.

	- number of consecutive diag failed packets reached above the threshold.

	- Upon acceptance of successful (test passed) diag packet, the test will update to Running state.

	-  Not-Running - the test is configured on a missing component.

	-  Disabled - the test is disabled by user configuration.

	- Packets Sent - the number of generated diagnostics packets (accumulative).

	- Packets Lost - the number of lost packets (accumulative) which were generated but not received.

	- Last Fail Time - the period of time that passed from the last time the test went into Failed state.

	- Last Uptime - the period of time that passed from the last time the test went into a Running state.

	- Test Uptime - the period of time that passed from the beginning of the test execution.

	- Test Fails - the number of times the sent lost packets consecutively reached the configured 'Threshold'.

	- The user should be able to filter by test name.

**Parameter table**

+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter      | Description                                                                            | Range                                                                                                                                                    |
+================+========================================================================================+==========================================================================================================================================================+
| Component      | The component on which the test is configured                                          | Node type: NCC/NCF/NCP                                                                                                                                   |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| ID             | The ID of the component                                                                | NCP ID: 0..191                                                                                                                                           |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Interval       | The configured test interval value per node-type and node-id                           | 1..3600                                                                                                                                                  |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Fail threshold | The configured consecutive failures threshold                                          | 1..10                                                                                                                                                    |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| State          | The current state of the test                                                          | Running - the test is up and running                                                                                                                     |
|                |                                                                                        | Failed - the test is up but has failed (has reached the fail threshold). When a diagnostics packet is received, the test state will change to "running". |
|                |                                                                                        | Down - the test is configured on a missing component                                                                                                     |
|                |                                                                                        | Disabled - the admin-state of the test is "disabled"                                                                                                     |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Packets Sent   | The number of generated diagnostics packets                                            | 64-bit counter                                                                                                                                           |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Packets Lost   | The number of lost packets                                                             | 64-bit counter                                                                                                                                           |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Last Fail Time | The period of time that passed from the last time the test went into Failed state      | D days, HH:MM:SS                                                                                                                                         |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Last Uptime    | The period of time that passed from the last time the test went into a Running state   | D days, HH:MM:SS                                                                                                                                         |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Test Uptime    | The period of time that passed from the beginning of the test execution                | D days, HH:MM:SS                                                                                                                                         |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Test Fails     | The number of consecutive times the sent lost packets reached the configured threshold | 64-bit counter                                                                                                                                           |
+----------------+----------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show system diagnostics status
	
	Punt Datapath Test Status:
	
	| Component | ID  | Interval | Threshold | State  | Packets Sent  | Packets Lost | Last Fail Time   | Last Uptime      | Test Uptime      | Test Fails |
	|-----------+-----+----------+-----------+--------+---------------+--------------+------------------+------------------+------------------+------------+
	|  NCP      |  0  | 3600     | 3         | Running| 226           | 6            | 5 day, 19:01:05  | 4 day, 01:01:05  | 9 day, 10:01:05  | 2          |
	|  NCP      |  1  | 3600     | 6         | Failed | 121           | 19           | 0 days, 19:01:05 | 5 days, 01:01:05 | 5 days, 01:01:05 | 3          |


	dnRouter# show system diagnostics status test punt-datapath

	Punt Datapath Test Status:

	| Component | ID  | Interval | Threshold | State  | Packets Sent  | Packets Lost | Last Fail Time   | Last Uptime      | Test Uptime      | Test Fails |
	|-----------------+----------+-----------+--------+---------------+--------------+------------------+------------------+------------------+------------+
	|  NCP      |  0  | 3600     | 3         | Running| 226           | 6            | 5 day, 19:01:05  | 4 day, 01:01:05  | 9 day, 10:01:05  | 2          |
	|  NCP      |  1  | 3600     | 6         | Failed | 121           | 19           | 0 days, 19:01:05 | 5 days, 01:01:05 | 5 days, 01:01:05 | 3          |

	

.. **Help line:** show system diagnostics tests status.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


